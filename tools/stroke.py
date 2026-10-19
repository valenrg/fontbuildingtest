"""Stroke engine: skeletons made of straight lines and circular arcs are
expanded into round-ended outlines and merged with boolean union.

Because every primitive is a line or a circular arc, the offset outline is
exact (parallel lines / concentric arcs) and rotation keeps circles circular,
so a glyph can be "bounced" (rotated + shifted) at the skeleton level.

Strokes are expanded without caps (rectangles and annular sectors); a single
round dot is then placed at every distinct endpoint. That way two strokes
meeting at a point never contribute two identical circles to the union, a
case in which Skia's boolean ops can silently return a wrong result.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pathops
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.roundingPen import RoundingPen

TAU = math.tau


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------
@dataclass
class Line:
    x0: float
    y0: float
    x1: float
    y1: float
    hs: float = 1.0  # stroke-width scale for this primitive

    def points(self):
        return [(self.x0, self.y0), (self.x1, self.y1)]

    def endpoints(self):
        return [(self.x0, self.y0), (self.x1, self.y1)]

    def probes(self):
        return [((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)] + self.endpoints()

    def transformed(self, rot, cx, cy, dx, dy):
        x0, y0 = _rot(self.x0, self.y0, rot, cx, cy)
        x1, y1 = _rot(self.x1, self.y1, rot, cx, cy)
        return Line(x0 + dx, y0 + dy, x1 + dx, y1 + dy, self.hs)


@dataclass
class Arc:
    """Circular arc, angles in degrees, counter-clockwise from a0 to a1."""
    cx: float
    cy: float
    r: float
    a0: float
    a1: float
    hs: float = 1.0  # stroke-width scale for this primitive

    def points(self):
        return [(self.cx - self.r, self.cy - self.r), (self.cx + self.r, self.cy + self.r)]

    def _at(self, deg):
        a = math.radians(deg)
        return (self.cx + self.r * math.cos(a), self.cy + self.r * math.sin(a))

    def endpoints(self):
        if abs(self.a1 - self.a0) >= 360 - 1e-9:
            return []
        return [self._at(self.a0), self._at(self.a1)]

    def probes(self):
        return [self._at((self.a0 + self.a1) / 2)] + self.endpoints()

    def transformed(self, rot, cx, cy, dx, dy):
        x, y = _rot(self.cx, self.cy, rot, cx, cy)
        return Arc(x + dx, y + dy, self.r, self.a0 + rot, self.a1 + rot, self.hs)


@dataclass
class Dot:
    """A filled circle (not stroked)."""
    cx: float
    cy: float
    r: float

    def points(self):
        return [(self.cx - self.r, self.cy - self.r), (self.cx + self.r, self.cy + self.r)]

    def endpoints(self):
        return []

    def probes(self):
        return [(self.cx, self.cy)]

    def transformed(self, rot, cx, cy, dx, dy):
        x, y = _rot(self.cx, self.cy, rot, cx, cy)
        return Dot(x + dx, y + dy, self.r)


def _rot(x, y, deg, cx, cy):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x -= cx
    y -= cy
    return cx + x * c - y * s, cy + x * s + y * c


# --------------------------------------------------------------------------
# Path construction helpers
# --------------------------------------------------------------------------
def _arc_segments(path: pathops.Path, cx, cy, r, a0, a1):
    """Append cubic segments approximating the arc from a0 to a1 (radians).
    The current point must already be at angle a0."""
    delta = a1 - a0
    n = max(1, int(math.ceil(abs(delta) / (math.pi / 2) - 1e-9)))
    step = delta / n
    k = 4.0 / 3.0 * math.tan(abs(step) / 4.0)
    sgn = 1 if step > 0 else -1
    for i in range(n):
        t0 = a0 + i * step
        t1 = t0 + step
        p0 = (cx + r * math.cos(t0), cy + r * math.sin(t0))
        p3 = (cx + r * math.cos(t1), cy + r * math.sin(t1))
        d0 = (-math.sin(t0) * sgn, math.cos(t0) * sgn)
        d3 = (-math.sin(t1) * sgn, math.cos(t1) * sgn)
        p1 = (p0[0] + k * r * d0[0], p0[1] + k * r * d0[1])
        p2 = (p3[0] - k * r * d3[0], p3[1] - k * r * d3[1])
        path.cubicTo(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])


def stroke_line(seg: Line, h: float) -> pathops.Path | None:
    """Rectangle of half-width h along the segment (no caps)."""
    dx, dy = seg.x1 - seg.x0, seg.y1 - seg.y0
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    nx, ny = -dy / length * h, dx / length * h
    p = pathops.Path()
    p.moveTo(seg.x0 + nx, seg.y0 + ny)
    p.lineTo(seg.x1 + nx, seg.y1 + ny)
    p.lineTo(seg.x1 - nx, seg.y1 - ny)
    p.lineTo(seg.x0 - nx, seg.y0 - ny)
    p.close()
    return p


def stroke_arc(seg: Arc, h: float) -> list[pathops.Path]:
    """Annular sector of half-width h along the arc (no caps)."""
    a0, a1 = math.radians(seg.a0), math.radians(seg.a1)
    if a1 < a0:
        a0, a1 = a1, a0
    full = (a1 - a0) >= TAU - 1e-9
    cx, cy = seg.cx, seg.cy
    if seg.r <= h + 2:
        # Inner offset would collapse: approximate with short segments plus
        # dots. The union of capsules along the arc is exactly the Minkowski
        # sum of the arc with the pen disk, so this is still exact.
        n = max(2, int(math.ceil((a1 - a0) / math.radians(12))))
        out = []
        for i in range(n):
            t0 = a0 + (a1 - a0) * i / n
            t1 = a0 + (a1 - a0) * (i + 1) / n
            x0, y0 = cx + seg.r * math.cos(t0), cy + seg.r * math.sin(t0)
            x1, y1 = cx + seg.r * math.cos(t1), cy + seg.r * math.sin(t1)
            out.append(stroke_line(Line(x0, y0, x1, y1), h))
            out.append(fill_dot(Dot(x1, y1, h)))
        return [o for o in out if o is not None]
    ro, ri = seg.r + h, seg.r - h
    if full:
        outer = pathops.Path()
        outer.moveTo(cx + ro, cy)
        _arc_segments(outer, cx, cy, ro, 0, TAU)
        outer.close()
        inner = pathops.Path()
        inner.moveTo(cx + ri, cy)
        _arc_segments(inner, cx, cy, ri, 0, TAU)
        inner.close()
        ring = pathops.Path()
        pathops.difference([outer], [inner], ring.getPen())
        return [ring]
    p = pathops.Path()
    p.moveTo(cx + ro * math.cos(a0), cy + ro * math.sin(a0))
    _arc_segments(p, cx, cy, ro, a0, a1)
    p.lineTo(cx + ri * math.cos(a1), cy + ri * math.sin(a1))
    _arc_segments(p, cx, cy, ri, a1, a0)
    p.close()
    return [p]


def fill_dot(d: Dot) -> pathops.Path:
    p = pathops.Path()
    p.moveTo(d.cx + d.r, d.cy)
    _arc_segments(p, d.cx, d.cy, d.r, 0, TAU)
    p.close()
    return p


# --------------------------------------------------------------------------
# Skeleton -> outline
# --------------------------------------------------------------------------
def _pieces(prims, h):
    pieces = []
    dots = {}
    for pr in prims:
        if isinstance(pr, Line):
            piece = stroke_line(pr, h * pr.hs)
            if piece is not None:
                pieces.append(piece)
        elif isinstance(pr, Arc):
            pieces.extend(stroke_arc(pr, h * pr.hs))
        elif isinstance(pr, Dot):
            pieces.append(fill_dot(pr))
            continue
        else:
            raise TypeError(pr)
        for x, y in pr.endpoints():
            key = (round(x, 2), round(y, 2), round(h * pr.hs, 2))
            dots[key] = Dot(x, y, h * pr.hs)
    pieces.extend(fill_dot(d) for d in dots.values())
    # Every piece must share one orientation, otherwise nonzero winding
    # cancels where a clockwise piece overlaps a counter-clockwise one.
    for piece in pieces:
        piece.fillType = pathops.FillType.WINDING
        if piece.clockwise:
            piece.reverse()
    return pieces


def _valid_union(result, pieces, prims):
    """A real union covers every piece's bounds, is no bigger than the sum of
    the pieces, and contains every skeleton probe point."""
    areas = [abs(p.area) for p in pieces]
    area = abs(result.area)
    if area < max(areas) * 0.999 or area > sum(areas) * 1.001:
        return False
    rb = result.bounds
    for p in pieces:
        b = p.bounds
        if b[0] < rb[0] - 0.5 or b[1] < rb[1] - 0.5 or b[2] > rb[2] + 0.5 or b[3] > rb[3] + 0.5:
            return False
    for pr in prims:
        for x, y in pr.probes():
            if not result.contains((x, y)):
                return False
    return True


def outline(prims, h: float) -> pathops.Path:
    if not prims:
        return pathops.Path()
    # If Skia still trips on some coincidence, retry with an invisible
    # sub-unit rotation/shift of the whole skeleton.
    for attempt in range(12):
        if attempt == 0:
            trial = prims
        else:
            rot = 0.017 * attempt * (1 if attempt % 2 else -1)
            trial = [pr.transformed(rot, 0, 0, 0.011 * attempt, 0.007 * attempt) for pr in prims]
        pieces = _pieces(trial, h)
        result = pathops.Path()
        try:
            pathops.union(pieces, result.getPen())
        except pathops.PathOpsError:
            continue
        if _valid_union(result, pieces, trial):
            return result
    raise RuntimeError("boolean union failed after retries")


def skeleton_bounds(prims):
    xs, ys = [], []
    for pr in prims:
        for x, y in pr.points():
            xs.append(x)
            ys.append(y)
    if not xs:
        return 0, 0, 0, 0
    return min(xs), min(ys), max(xs), max(ys)


def bounce(prims, rot_deg: float, dy: float):
    """Rotate the skeleton about its centre and shift it vertically."""
    x0, y0, x1, y1 = skeleton_bounds(prims)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return [pr.transformed(rot_deg, cx, cy, 0, dy) for pr in prims]


def draw_into_glyph(path: pathops.Path, glyph):
    """Draw a pathops path into a ufoLib2 glyph, rounded, with outer contours
    counter-clockwise (PostScript convention)."""
    rec = RecordingPen()
    path.draw(rec)
    area_pen = AreaPen()
    rec.replay(area_pen)
    pen = RoundingPen(glyph.getPen())
    if area_pen.value < 0:  # clockwise outer -> reverse everything
        pen = ReverseContourPen(pen)
    rec.replay(pen)
