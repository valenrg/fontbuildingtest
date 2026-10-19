"""Stroke engine: skeletons made of straight lines and circular arcs are
expanded into flat-ended (butt-capped) bands and merged with boolean union;
optional cut polygons are subtracted afterwards to clip apexes, corners and
terminals flat, or to carve ink-trap notches.

Line and arc offsets are exact (parallel lines / concentric arcs), so the
result is clean cubic geometry, not flattened polygons.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

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
    w0: float = 1.0  # stroke-width scale at the start
    w1: float = 1.0  # stroke-width scale at the end

    def points(self):
        return [(self.x0, self.y0), (self.x1, self.y1)]

    def probes(self):
        return [((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)]

    def transformed(self, rot, cx, cy, dx, dy):
        x0, y0 = _rot(self.x0, self.y0, rot, cx, cy)
        x1, y1 = _rot(self.x1, self.y1, rot, cx, cy)
        return Line(x0 + dx, y0 + dy, x1 + dx, y1 + dy, self.w0, self.w1)


@dataclass
class Arc:
    """Circular arc, angles in degrees, counter-clockwise from a0 to a1.
    Its ends are cut radially (perpendicular to the stroke)."""
    cx: float
    cy: float
    r: float
    a0: float
    a1: float
    w0: float = 1.0
    w1: float = 1.0

    def points(self):
        return [(self.cx - self.r, self.cy - self.r), (self.cx + self.r, self.cy + self.r)]

    def _at(self, deg):
        a = math.radians(deg)
        return (self.cx + self.r * math.cos(a), self.cy + self.r * math.sin(a))

    def probes(self):
        return [self._at((self.a0 + self.a1) / 2)]

    def transformed(self, rot, cx, cy, dx, dy):
        x, y = _rot(self.cx, self.cy, rot, cx, cy)
        return Arc(x + dx, y + dy, self.r, self.a0 + rot, self.a1 + rot, self.w0, self.w1)


@dataclass
class Dot:
    """A filled circle (not stroked)."""
    cx: float
    cy: float
    r: float

    def points(self):
        return [(self.cx - self.r, self.cy - self.r), (self.cx + self.r, self.cy + self.r)]

    def probes(self):
        return [(self.cx, self.cy)]

    def transformed(self, rot, cx, cy, dx, dy):
        x, y = _rot(self.cx, self.cy, rot, cx, cy)
        return Dot(x + dx, y + dy, self.r)


@dataclass
class Cut:
    """A polygon subtracted from the glyph after the strokes are merged."""
    pts: list = field(default_factory=list)

    def points(self):
        return []  # cuts do not count towards the skeleton bounds

    def probes(self):
        return []

    def transformed(self, rot, cx, cy, dx, dy):
        return Cut([(_rot(x, y, rot, cx, cy)[0] + dx, _rot(x, y, rot, cx, cy)[1] + dy)
                    for x, y in self.pts])


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


def _smooth(t):
    return t * t * (3 - 2 * t)


def _tangent_quad(x0, y0, r0, x1, y1, r1):
    """Quad bounded by the external tangents of discs (p0, r0) and (p1, r1)."""
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    if d < 1e-6 or abs(r0 - r1) >= d:
        return None
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    sin_phi = (r0 - r1) / d
    cos_phi = math.sqrt(1 - sin_phi * sin_phi)
    mpx, mpy = cos_phi * nx + sin_phi * ux, cos_phi * ny + sin_phi * uy
    mmx, mmy = -cos_phi * nx + sin_phi * ux, -cos_phi * ny + sin_phi * uy
    p = pathops.Path()
    p.moveTo(x0 + r0 * mpx, y0 + r0 * mpy)
    p.lineTo(x1 + r1 * mpx, y1 + r1 * mpy)
    p.lineTo(x1 + r1 * mmx, y1 + r1 * mmy)
    p.lineTo(x0 + r0 * mmx, y0 + r0 * mmy)
    p.close()
    return p


def stroke_line(seg: Line, h: float) -> pathops.Path | None:
    """Band of half-width h*w along the segment with flat ends."""
    r0, r1 = h * seg.w0, h * seg.w1
    if abs(r0 - r1) > 1e-6:
        return _tangent_quad(seg.x0, seg.y0, r0, seg.x1, seg.y1, r1)
    dx, dy = seg.x1 - seg.x0, seg.y1 - seg.y0
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    nx, ny = -dy / length * r0, dx / length * r0
    p = pathops.Path()
    p.moveTo(seg.x0 + nx, seg.y0 + ny)
    p.lineTo(seg.x1 + nx, seg.y1 + ny)
    p.lineTo(seg.x1 - nx, seg.y1 - ny)
    p.lineTo(seg.x0 - nx, seg.y0 - ny)
    p.close()
    return p


def stroke_arc(seg: Arc, hbase: float) -> list[pathops.Path]:
    """Annular sector of half-width h along the arc with radial flat ends."""
    a0, a1 = math.radians(seg.a0), math.radians(seg.a1)
    cx, cy = seg.cx, seg.cy
    if abs(seg.w0 - seg.w1) > 1e-6:
        n = max(2, int(math.ceil(abs(a1 - a0) / math.radians(7.5))))
        out = []
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            ang0 = a0 + (a1 - a0) * t0
            ang1 = a0 + (a1 - a0) * t1
            r0 = hbase * (seg.w0 + (seg.w1 - seg.w0) * _smooth(t0))
            r1 = hbase * (seg.w0 + (seg.w1 - seg.w0) * _smooth(t1))
            x0, y0 = cx + seg.r * math.cos(ang0), cy + seg.r * math.sin(ang0)
            x1, y1 = cx + seg.r * math.cos(ang1), cy + seg.r * math.sin(ang1)
            q = _tangent_quad(x0, y0, r0, x1, y1, r1)
            if q is not None:
                out.append(q)
            if i:
                out.append(fill_dot(Dot(x0, y0, r0)))
        return out
    h = hbase * seg.w0
    if a1 < a0:
        a0, a1 = a1, a0
    full = (a1 - a0) >= TAU - 1e-9
    ro, ri = seg.r + h, max(seg.r - h, 0.0)
    if full:
        outer = pathops.Path()
        outer.moveTo(cx + ro, cy)
        _arc_segments(outer, cx, cy, ro, 0, TAU)
        outer.close()
        if ri <= 0.5:
            return [outer]
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
    if ri <= 0.5:
        p.lineTo(cx, cy)
    else:
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


def polygon(pts) -> pathops.Path:
    p = pathops.Path()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    return p


# --------------------------------------------------------------------------
# Skeleton -> outline
# --------------------------------------------------------------------------
def _orient(pieces):
    for piece in pieces:
        piece.fillType = pathops.FillType.WINDING
        if piece.clockwise:
            piece.reverse()
    return pieces


def _pieces(prims, h):
    pieces, cuts = [], []
    for pr in prims:
        if isinstance(pr, Line):
            piece = stroke_line(pr, h)
            if piece is not None:
                pieces.append(piece)
        elif isinstance(pr, Arc):
            pieces.extend(stroke_arc(pr, h))
        elif isinstance(pr, Dot):
            pieces.append(fill_dot(pr))
        elif isinstance(pr, Cut):
            cuts.append(polygon(pr.pts))
        else:
            raise TypeError(pr)
    return _orient(pieces), _orient(cuts)


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
    # Retry with an invisible sub-unit rotation/shift of the whole skeleton
    # if Skia trips on coincident geometry.
    for attempt in range(12):
        if attempt == 0:
            trial = prims
        else:
            rot = 0.017 * attempt * (1 if attempt % 2 else -1)
            trial = [pr.transformed(rot, 0, 0, 0.011 * attempt, 0.007 * attempt) for pr in prims]
        pieces, cuts = _pieces(trial, h)
        if not pieces:
            return pathops.Path()
        result = pathops.Path()
        try:
            pathops.union(pieces, result.getPen())
        except pathops.PathOpsError:
            continue
        if not _valid_union(result, pieces, [p for p in trial if not isinstance(p, Cut)]):
            continue
        if cuts:
            clipped = pathops.Path()
            try:
                pathops.difference([result], cuts, clipped.getPen())
            except pathops.PathOpsError:
                continue
            result = clipped
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
