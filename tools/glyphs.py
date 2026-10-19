"""Mirrorball glyph skeletons.

A tight geometric grotesque with a 70s disco flavour: flat and radially
cut terminals, big x-height, square dots, letters set close, and a weight
range from Hairline to Poster. Every glyph is a function of a Ctx (which
knows the half stroke width `h` and the metrics) and returns primitives.
Coordinates are stroke centre-lines. Radii are mostly "outer radius minus
h" so silhouettes hold across weights while counters shrink; heavy weights
also get a little extra width (`ex`) so counters survive.
"""
from __future__ import annotations

import math

from stroke import Arc, Cut, Dot, Line

UPM = 1000
XH = 520          # x-height
CAP = 700         # cap height
ASC = 720         # ascender
DESC = -190       # descender
OVER = 12         # overshoot
BIG = 4000        # "infinity" for clipping polygons


class Ctx:
    def __init__(self, stroke: float):
        self.w = stroke
        self.h = h = stroke / 2
        self.yb = h                  # baseline centre-line
        self.yx = XH - h             # x-height centre-line
        self.yc = CAP - h            # cap centre-line
        self.ya = ASC - h            # ascender centre-line
        self.yd = DESC + h           # descender centre-line
        self.o = OVER
        self.ex = max(0.0, stroke - 95) * 0.7    # extra width for heavy weights
        self.hv = max(0.0, (stroke - 95) / 105)   # 0 at Regular .. 1 at Poster
        # lowercase bowl (o, b, d, p, q, c, e): outer diameter XH + 2o + ex
        self.rx = (XH + 2 * OVER + self.ex) / 2 - h
        self.cyx = XH / 2
        # lowercase arch (n, h, m, u): outer width 470 + ex
        self.rn = (470 + self.ex - stroke) / 2
        # cap round (O, C, G, Q): outer width 600 + ex
        self.rO = (600 + self.ex - stroke) / 2
        # horizontals a touch thinner in the heavy weights
        self.hb = 1.0 - 0.2 * self.hv
        # square dot side
        self.dot = stroke * 1.0 + 14
        self.dgap = 70 - 28 * self.hv          # gap between x-height and the dot
        # side bearings get tighter as weight grows
        s = 40 - 0.15 * stroke
        self.sb = {"s": s, "r": s * 0.45, "d": 10, "o": 0}

    def R(self, outer):
        """Centre-line radius for a given outer radius, never collapsing."""
        return max(outer - self.h, self.h + 8)


G = {}


def glyph(name, sides="ss", unicode=None):
    def deco(fn):
        G[name] = (fn, sides, unicode)
        return fn
    return deco


def L(x0, y0, x1, y1, w=1.0):
    return Line(x0, y0, x1, y1, w, w)


def A(cx, cy, r, a0, a1, w=1.0):
    return Arc(cx, cy, r, a0, a1, w, w)


def circle(cx, cy, r, w=1.0):
    return Arc(cx, cy, r, 0, 360, w, w)


def ext(x0, y0, x1, y1, e0, e1, w=1.0):
    """Line extended by e0 before its start and e1 past its end."""
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    return Line(x0 - ux * e0, y0 - uy * e0, x1 + ux * e1, y1 + uy * e1, w, w)


def clip_above(y, x0=-BIG, x1=BIG):
    return Cut([(x0, y), (x1, y), (x1, BIG), (x0, BIG)])


def clip_below(y, x0=-BIG, x1=BIG):
    return Cut([(x0, -BIG), (x1, -BIG), (x1, y), (x0, y)])


def clip_left(x, y0=-BIG, y1=BIG):
    return Cut([(-BIG, y0), (x, y0), (x, y1), (-BIG, y1)])


def clip_right(x, y0=-BIG, y1=BIG):
    return Cut([(x, y0), (BIG, y0), (BIG, y1), (x, y1)])


def arch3(xl, xr, ytop, depth, r, w=1.0):
    """Three-centred (basket-handle) arch from (xl, ys) over (xm, ytop) to
    (xr, ys), ys = ytop - depth, with side radius r; flat-topped if the
    geometry does not allow a tangent big arc."""
    a = (xr - xl) / 2
    xm = (xl + xr) / 2
    ys = ytop - depth
    r = min(r, depth - 1, a - 1)
    if r < 4 or a <= depth:
        # semicircle-ish fallback: two quarter arcs with a flat top
        rr = min(a, depth)
        return [A(xr - rr, ytop - rr, rr, 0, 90, w), L(xr - rr, ytop, xl + rr, ytop, w),
                A(xl + rr, ytop - rr, rr, 90, 180, w)]
    k = ((a - r) ** 2 - (depth - r) ** 2) / (2 * (depth - r))
    R = depth + k
    phi = math.degrees(math.atan2(k, a - r))
    return [A(xr - r, ys, r, 0, phi, w), A(xm, ys - k, R, phi, 180 - phi, w),
            A(xl + r, ys, r, 180 - phi, 180, w)]


def stadium(x, ytop, ybot, r):
    """Closed rounded-rectangle loop (centre-line) between ytop and ybot."""
    return [
        A(x + r, ytop - r, r, 0, 180),
        L(x, ytop - r, x, ybot + r),
        A(x + r, ybot + r, r, 180, 360),
        L(x + 2 * r, ybot + r, x + 2 * r, ytop - r),
    ]


def sq(c, cx, ybot, side=None):
    """Square dot centred at cx with its bottom at ybot (a short fat line)."""
    side = side or c.dot
    return Line(cx, ybot, cx, ybot + side, side / c.w, side / c.w)


# ---------------------------------------------------------------- lowercase
@glyph("a", "rs", 0x61)
def _(c):
    Wa = 480 + c.ex                                  # outer width
    xa = Wa - c.w                                    # stem centre-line
    ab = 1.0 - 0.45 * c.hv                           # bowl loop stroke scale
    hb_ = c.h * ab
    top = 0.54 * XH + 0.95 * max(0, c.w - 95)        # bowl top (outer)
    xl = hb_                                         # bowl left centre-line
    ybot, ytop = hb_, top - hb_
    rb = max(min((ytop - ybot) / 2, (xa - xl) / 2.2), hb_ + 4)
    # arch: basket-handle from the stem over to a terminal on the left
    xt = xl + 0.3 * c.h                              # terminal centre-line
    aperture = 0.07 * XH + 0.3 * c.h
    depth = max(c.yx - (top + aperture) - c.h * 0.2, 0.3 * c.h + 40)
    depth = min(depth, (xa - xt) * 0.5)
    drop = max(0.0, (c.yx - depth) - (top + aperture) - c.h)
    drop = min(drop, 0.12 * XH)
    prims = [L(xa, c.yx - depth, xa, c.yb)]                       # stem
    aw = 1.0 - 0.2 * c.hv
    prims += arch3(xt, xa, c.yx, depth, 0.45 * depth, aw)
    prims += [
        L(xt, c.yx - depth, xt, c.yx - depth - drop, aw),   # terminal drop
        L(xl + rb, ytop, xa, ytop, ab),                     # bowl top
        A(xl + rb, ytop - rb, rb, 90, 180, ab),             # bowl top-left
        A(xl + rb, ybot + rb, rb, 180, 270, ab),            # bowl bottom-left
        L(xl + rb, ybot, xa, ybot, ab),                     # bowl bottom
    ]
    if ytop - rb > ybot + rb + 1:
        prims.append(L(xl, ybot + rb, xl, ytop - rb, ab))   # bowl left side
    return prims


@glyph("b", "sr", 0x62)
def _(c):
    return [L(0, c.ya, 0, c.yb), circle(c.rx, c.cyx, c.rx)]


@glyph("c", "rr", 0x63)
def _(c):
    return [A(c.rx, c.cyx, c.rx, 42, 318)]


@glyph("d", "rs", 0x64)
def _(c):
    return [circle(c.rx, c.cyx, c.rx), L(2 * c.rx, c.ya, 2 * c.rx, c.yb)]


@glyph("e", "rr", 0x65)
def _(c):
    counter = 2 * (c.rx - c.h)
    eb = min(c.hb, 0.5 * counter / c.w)
    gap = 0.12 * c.w + 10
    ybar = c.cyx - c.h * eb                       # bar underside
    return [A(c.rx, c.cyx, c.rx, 0, 325 - 10 * c.hv), L(0, c.cyx, 2 * c.rx, c.cyx, eb),
            Cut([(c.rx + c.h * 0.6, ybar - gap), (BIG, ybar - gap), (BIG, ybar), (c.rx + c.h * 0.6, ybar)])]


@glyph("f", "ss", 0x66)
def _(c):
    rf = c.R(165 + c.ex * 0.4)
    return [
        L(0, c.yb, 0, c.ya - rf),
        A(rf, c.ya - rf, rf, 68, 180),
        L(-105, c.yx, 140 + c.ex * 0.3, c.yx, c.hb),
    ]


@glyph("g", "rs", 0x67)
def _(c):
    gs = 1.0 - 0.3 * c.hv
    rg = max(200 + c.ex * 0.4 - c.h * gs, c.h * gs + 8)
    ydh = DESC + c.h * gs
    return [
        circle(c.rx, c.cyx, c.rx),
        L(2 * c.rx, c.yx, 2 * c.rx, ydh + rg),
        A(2 * c.rx - rg, ydh + rg, rg, -182 + 40 * c.hv, 0, gs),
    ]


@glyph("h", "ss", 0x68)
def _(c):
    rn = c.rn
    return [L(0, c.ya, 0, c.yb), A(rn, c.yx - rn, rn, 0, 180), L(2 * rn, c.yx - rn, 2 * rn, c.yb)]


@glyph("i", "ss", 0x69)
def _(c):
    return [L(0, c.yx, 0, c.yb), sq(c, 0, XH + c.dgap)]


@glyph("j", "ds", 0x6A)
def _(c):
    rj = c.R(175 + c.ex * 0.4)
    return [L(0, c.yx, 0, c.yd + rj), A(-rj, c.yd + rj, rj, -92, 0), sq(c, 0, XH + c.dgap)]


@glyph("k", "sd", 0x6B)
def _(c):
    kx = 250 + c.ex * 0.6
    return [
        L(0, c.ya, 0, c.yb),
        ext(0, 215, kx, c.yx, 0, c.h * 1.6),
        ext(90 + c.ex * 0.2, 310, kx + 15, c.yb, 0, c.h * 1.6),
        clip_above(XH, 60, BIG),
        clip_below(0, 60, BIG),
    ]


@glyph("l", "ss", 0x6C)
def _(c):
    return [L(0, c.ya, 0, c.yb)]


@glyph("m", "ss", 0x6D)
def _(c):
    rm = c.rn * 0.86
    return [
        L(0, c.yx, 0, c.yb),
        A(rm, c.yx - rm, rm, 0, 180), L(2 * rm, c.yx - rm, 2 * rm, c.yb),
        A(3 * rm, c.yx - rm, rm, 0, 180), L(4 * rm, c.yx - rm, 4 * rm, c.yb),
    ]


@glyph("n", "ss", 0x6E)
def _(c):
    rn = c.rn
    return [L(0, c.yx, 0, c.yb), A(rn, c.yx - rn, rn, 0, 180), L(2 * rn, c.yx - rn, 2 * rn, c.yb)]


@glyph("o", "rr", 0x6F)
def _(c):
    return [circle(c.rx, c.cyx, c.rx)]


@glyph("p", "sr", 0x70)
def _(c):
    return [L(0, c.yx, 0, c.yd), circle(c.rx, c.cyx, c.rx)]


@glyph("q", "rs", 0x71)
def _(c):
    return [circle(c.rx, c.cyx, c.rx), L(2 * c.rx, c.yx, 2 * c.rx, c.yd)]


@glyph("r", "sr", 0x72)
def _(c):
    rr = c.R(170 + c.ex * 0.4)
    return [L(0, c.yx, 0, c.yb), A(rr, c.yx - rr, rr, 18, 180)]


@glyph("s", "rr", 0x73)
def _(c):
    total = (c.yx - c.yb + 2 * c.o) / 2 + c.ex * 0.4
    ru, rl = total * 0.47, total * 0.53
    cx = rl
    cyu = c.yx + c.o - ru
    cyl = c.yb - c.o + rl
    op = 22 * c.hv
    return [A(cx, cyu, ru, 38 + op, 270), A(cx, cyl, rl, -142 - op, 90)]


@glyph("t", "ss", 0x74)
def _(c):
    return [L(0, c.yb, 0, 650 - c.h), L(-110, c.yx, 130 + c.ex * 0.3, c.yx, c.hb)]


@glyph("u", "ss", 0x75)
def _(c):
    rn = c.rn
    return [L(0, c.yx, 0, c.yb + rn), A(rn, c.yb + rn, rn, 180, 360), L(2 * rn, c.yx, 2 * rn, c.yb)]


@glyph("v", "dd", 0x76)
def _(c):
    vx = 215 + c.ex * 0.6
    e = c.h * 1.8
    return [ext(0, c.yx, vx, c.yb, e, e), ext(vx, c.yb, 2 * vx, c.yx, e, e),
            clip_above(XH), clip_below(0)]


@glyph("w", "dd", 0x77)
def _(c):
    a = 170 + c.ex * 0.55
    e = c.h * 1.8
    mid = c.yx - 40
    return [ext(0, c.yx, a, c.yb, e, e), ext(a, c.yb, 2 * a, mid, e, e),
            ext(2 * a, mid, 3 * a, c.yb, e, e), ext(3 * a, c.yb, 4 * a, c.yx, e, e),
            clip_above(XH), clip_below(0)]


@glyph("x", "dd", 0x78)
def _(c):
    xw = 400 + c.ex * 0.9
    e = c.h * 1.8
    return [ext(0, c.yx, xw, c.yb, e, e), ext(0, c.yb, xw, c.yx, e, e),
            clip_above(XH), clip_below(0)]


@glyph("y", "dd", 0x79)
def _(c):
    jx = 210 + c.ex * 0.6
    e = c.h * 1.8
    # right diagonal runs straight from the x-height through the join to the descender
    s = (c.yd - c.yx) / (c.yb - c.yx)
    xd = 2 * jx - s * jx
    return [ext(0, c.yx, jx, c.yb, e, e), ext(2 * jx, c.yx, xd, c.yd, e, e),
            clip_above(XH), clip_below(DESC)]


@glyph("z", "ss", 0x7A)
def _(c):
    zw = 380 + c.ex * 0.8
    e = c.h * 2
    return [L(0, c.yx, zw, c.yx, c.hb), ext(zw, c.yx, 0, c.yb, e, e), L(0, c.yb, zw, c.yb, c.hb),
            clip_above(XH), clip_below(0), clip_left(-c.h), clip_right(zw + c.h)]


# ---------------------------------------------------------------- uppercase
@glyph("A", "dd", 0x41)
def _(c):
    w = 600 + c.ex * 1.1
    e = c.h * 2
    t = (235 - c.yb) / (c.yc - c.yb)
    xl = t * (w / 2)
    return [ext(0, c.yb, w / 2, c.yc, e, e), ext(w / 2, c.yc, w, c.yb, e, e),
            L(xl, 235, w - xl, 235, c.hb), clip_above(CAP), clip_below(0)]


@glyph("B", "sr", 0x42)
def _(c):
    H2 = (c.yc - c.yb) / 2
    r1, r2 = H2 * 0.46 + c.ex * 0.15, H2 * 0.54 + c.ex * 0.15
    ym = c.yc - 2 * r1 + c.ex * 0.15
    return [
        L(0, c.yc, 0, c.yb),
        L(0, c.yc, 80, c.yc, c.hb), A(80, c.yc - r1, r1, -90, 90), L(80, ym, 0, ym, c.hb),
        L(0, ym, 100, ym, c.hb), A(100, ym - r2, r2, -90, 90), L(100, c.yb, 0, c.yb, c.hb),
    ]


@glyph("C", "rr", 0x43)
def _(c):
    r = c.rO
    top, bot = c.yc + c.o, c.yb - c.o
    return [A(r, top - r, r, 45, 180), L(0, top - r, 0, bot + r), A(r, bot + r, r, 180, 315)]


@glyph("D", "sr", 0x44)
def _(c):
    r = (c.yc - c.yb) / 2 + c.o
    cy = (c.yc + c.yb) / 2
    xd = 110 + c.ex * 0.5
    return [L(0, c.yc, 0, c.yb), L(0, cy + r, xd, cy + r, c.hb), A(xd, cy, r, -90, 90),
            L(xd, cy - r, 0, cy - r, c.hb)]


@glyph("E", "ss", 0x45)
def _(c):
    ym = (c.yc + c.yb) / 2 + 15
    ew = 390 + c.ex * 0.5
    return [L(0, c.yc, 0, c.yb), L(0, c.yc, ew, c.yc, c.hb), L(0, ym, ew - 50, ym, c.hb),
            L(0, c.yb, ew, c.yb, c.hb)]


@glyph("F", "ss", 0x46)
def _(c):
    ym = (c.yc + c.yb) / 2 + 15
    ew = 380 + c.ex * 0.5
    return [L(0, c.yc, 0, c.yb), L(0, c.yc, ew, c.yc, c.hb), L(0, ym, ew - 60, ym, c.hb)]


@glyph("G", "rs", 0x47)
def _(c):
    r = c.rO
    top, bot = c.yc + c.o, c.yb - c.o
    ybar = 330
    return [A(r, top - r, r, 45, 180), L(0, top - r, 0, bot + r), A(r, bot + r, r, 180, 360),
            L(2 * r, bot + r, 2 * r, ybar), L(2 * r - 230 - c.ex * 0.3, ybar, 2 * r, ybar, c.hb)]


@glyph("H", "ss", 0x48)
def _(c):
    ym = (c.yc + c.yb) / 2 + 15
    hw = 500 + c.ex
    return [L(0, c.yc, 0, c.yb), L(hw, c.yc, hw, c.yb), L(0, ym, hw, ym, c.hb)]


@glyph("I", "ss", 0x49)
def _(c):
    return [L(0, c.yc, 0, c.yb)]


@glyph("J", "rs", 0x4A)
def _(c):
    rj = c.R(220 + c.ex * 0.4)
    return [L(0, c.yc, 0, c.yb + rj), A(-rj, c.yb + rj, rj, -92, 0)]


@glyph("K", "sd", 0x4B)
def _(c):
    kx = 400 + c.ex * 0.8
    e = c.h * 1.8
    return [L(0, c.yc, 0, c.yb), ext(0, 300, kx, c.yc, 0, e),
            ext(130 + c.ex * 0.2, 415, kx + 30, c.yb, 0, e),
            clip_above(CAP, 80, BIG), clip_below(0, 80, BIG)]


@glyph("L", "ss", 0x4C)
def _(c):
    return [L(0, c.yc, 0, c.yb), L(0, c.yb, 360 + c.ex * 0.5, c.yb, c.hb)]


@glyph("M", "ss", 0x4D)
def _(c):
    w = 640 + c.ex * 1.2
    e = c.h * 2.2
    yv = 210
    return [L(0, c.yc, 0, c.yb), ext(0, c.yc, w / 2, yv, e, e), ext(w / 2, yv, w, c.yc, e, e),
            L(w, c.yc, w, c.yb), clip_above(CAP), clip_left(-c.h), clip_right(w + c.h),
            clip_below(yv - 0.9 * c.h, c.h, w - c.h)]


@glyph("N", "ss", 0x4E)
def _(c):
    w = 520 + c.ex
    e = c.h * 2.2
    return [L(0, c.yc, 0, c.yb), ext(0, c.yc, w, c.yb, e, e), L(w, c.yc, w, c.yb),
            clip_above(CAP), clip_below(0), clip_left(-c.h), clip_right(w + c.h)]


@glyph("O", "rr", 0x4F)
def _(c):
    return stadium(0, c.yc + c.o, c.yb - c.o, c.rO)


@glyph("P", "sr", 0x50)
def _(c):
    rp = (c.yc - 300) / 2 + c.ex * 0.2
    xp = 90 + c.ex * 0.4
    return [L(0, c.yc, 0, c.yb), L(0, c.yc, xp, c.yc, c.hb), A(xp, c.yc - rp, rp, -90, 90),
            L(xp, c.yc - 2 * rp, 0, c.yc - 2 * rp, c.hb)]


@glyph("Q", "rr", 0x51)
def _(c):
    r = c.rO
    e = c.h * 1.5
    return stadium(0, c.yc + c.o, c.yb - c.o, r) + [
        ext(r + 60, c.yb + 120, r + 300 + c.ex * 0.4, c.yb - 110, 0, e), clip_below(-150)]


@glyph("R", "sd", 0x52)
def _(c):
    rp = (c.yc - 300) / 2 + c.ex * 0.2
    xp = 90 + c.ex * 0.4
    e = c.h * 1.8
    return [L(0, c.yc, 0, c.yb), L(0, c.yc, xp, c.yc, c.hb), A(xp, c.yc - rp, rp, -90, 90),
            L(xp, c.yc - 2 * rp, 0, c.yc - 2 * rp, c.hb),
            ext(xp + 60, c.yc - 2 * rp, 450 + c.ex * 0.8, c.yb, 0, e), clip_below(0)]


@glyph("S", "rr", 0x53)
def _(c):
    total = (c.yc - c.yb + 2 * c.o) / 2 + c.ex * 0.4
    ru, rl = total * 0.46, total * 0.54
    cx = rl
    cyu = c.yc + c.o - ru
    cyl = c.yb - c.o + rl
    op = 20 * c.hv
    return [A(cx, cyu, ru, 38 + op, 270), A(cx, cyl, rl, -142 - op, 90)]


@glyph("T", "ss", 0x54)
def _(c):
    tw = 540 + c.ex * 0.8
    return [L(0, c.yc, tw, c.yc, c.hb), L(tw / 2, c.yc, tw / 2, c.yb)]


@glyph("U", "ss", 0x55)
def _(c):
    r = (560 + c.ex - c.w) / 2
    bot = c.yb - c.o
    return [L(0, c.yc, 0, bot + r), A(r, bot + r, r, 180, 360), L(2 * r, c.yc, 2 * r, bot + r)]


@glyph("V", "dd", 0x56)
def _(c):
    vx = 300 + c.ex * 0.6
    e = c.h * 2.2
    return [ext(0, c.yc, vx, c.yb, e, e), ext(vx, c.yb, 2 * vx, c.yc, e, e),
            clip_above(CAP), clip_below(0)]


@glyph("W", "dd", 0x57)
def _(c):
    a = 225 + c.ex * 0.55
    e = c.h * 2.2
    mid = c.yc - 30
    return [ext(0, c.yc, a, c.yb, e, e), ext(a, c.yb, 2 * a, mid, e, e),
            ext(2 * a, mid, 3 * a, c.yb, e, e), ext(3 * a, c.yb, 4 * a, c.yc, e, e),
            clip_above(CAP), clip_below(0)]


@glyph("X", "dd", 0x58)
def _(c):
    xw = 540 + c.ex
    e = c.h * 2.2
    return [ext(0, c.yc, xw, c.yb, e, e), ext(0, c.yb, xw, c.yc, e, e),
            clip_above(CAP), clip_below(0)]


@glyph("Y", "dd", 0x59)
def _(c):
    yw = 560 + c.ex
    e = c.h * 2.2
    return [ext(0, c.yc, yw / 2, 300, e, c.h), ext(yw, c.yc, yw / 2, 300, e, c.h),
            L(yw / 2, 300 + c.h, yw / 2, c.yb), clip_above(CAP)]


@glyph("Z", "ss", 0x5A)
def _(c):
    zw = 520 + c.ex
    e = c.h * 2.2
    return [L(0, c.yc, zw, c.yc, c.hb), ext(zw, c.yc, 0, c.yb, e, e), L(0, c.yb, zw, c.yb, c.hb),
            clip_above(CAP), clip_below(0), clip_left(-c.h), clip_right(zw + c.h)]


# ------------------------------------------------------------------- digits
@glyph("zero", "rr", 0x30)
def _(c):
    return stadium(0, c.yc + c.o, c.yb - c.o, (540 + c.ex - c.w) / 2)


@glyph("one", "ds", 0x31)
def _(c):
    e = c.h * 1.5
    return [L(0, c.yc, 0, c.yb), ext(0, c.yc, -170 - c.ex * 0.3, c.yc - 150, e, 0), clip_above(CAP)]


@glyph("two", "rs", 0x32)
def _(c):
    r = (540 + c.ex - c.w) / 2
    ang = -40
    ex_, ey = r + r * math.cos(math.radians(ang)), c.yc - r + r * math.sin(math.radians(ang))
    e = c.h * 2
    return [A(r, c.yc - r, r, ang, 180), ext(ex_, ey, 0, c.yb, 0, e),
            L(0, c.yb, 2 * r + 15, c.yb, c.hb), clip_below(0), clip_left(-c.h)]


@glyph("three", "rr", 0x33)
def _(c):
    H2 = (c.yc - c.yb + 2 * c.o) / 2 + c.ex * 0.2
    r1, r2 = H2 * 0.47, H2 * 0.53
    cx = r2
    return [A(cx, c.yc + c.o - r1, r1, -90, 162), A(cx, c.yb - c.o + r2, r2, -162, 90)]


@glyph("four", "ds", 0x34)
def _(c):
    xs = 350 + c.ex * 0.6
    e = c.h * 2
    return [ext(xs, c.yc, 0, 210, e, 0), L(0, 210, xs + 120, 210, c.hb), L(xs, c.yc, xs, c.yb),
            clip_above(CAP), clip_left(-c.h), clip_right(xs + 120 + c.h),
            Cut([(xs + c.h, 210 + c.h), (BIG, 210 + c.h), (BIG, BIG), (xs + c.h, BIG)])]


@glyph("five", "sr", 0x35)
def _(c):
    ytop = 410 + c.ex * 0.2
    r5 = (ytop - c.yb + c.o) / 2
    cx = 130 + c.ex * 0.3
    return [L(0, c.yc, 400 + c.ex * 0.5, c.yc, c.hb), L(0, c.yc, 0, ytop), L(0, ytop, cx, ytop, c.hb),
            A(cx, ytop - r5, r5, -150, 90)]


@glyph("six", "rr", 0x36)
def _(c):
    r6 = (440 + c.ex - c.w) / 2
    rt = (540 + c.ex - c.w) / 2
    return [circle(r6, c.yb - c.o + r6, r6), L(0, c.yb - c.o + r6, 0, c.yc + c.o - rt),
            A(rt, c.yc + c.o - rt, rt, 40, 180)]


@glyph("seven", "sd", 0x37)
def _(c):
    w7 = 480 + c.ex * 0.8
    e = c.h * 2
    return [L(0, c.yc, w7, c.yc, c.hb), ext(w7, c.yc, 150, c.yb, e, e),
            clip_above(CAP), clip_below(0), clip_right(w7 + c.h)]


@glyph("eight", "rr", 0x38)
def _(c):
    H2 = (c.yc - c.yb + 2 * c.o) / 2 + c.ex * 0.2
    r1, r2 = H2 * 0.46, H2 * 0.54
    cx = r2
    return [circle(cx, c.yc + c.o - r1, r1), circle(cx, c.yb - c.o + r2, r2)]


@glyph("nine", "rr", 0x39)
def _(c):
    r9 = (440 + c.ex - c.w) / 2
    rt = (540 + c.ex - c.w) / 2
    return [circle(r9, c.yc + c.o - r9, r9), L(2 * r9, c.yc + c.o - r9, 2 * r9, c.yb - c.o + rt),
            A(2 * r9 - rt, c.yb - c.o + rt, rt, -140, 0)]


# ------------------------------------------------------------- punctuation
@glyph("space", "oo", 0x20)
def _(c):
    return []


@glyph("period", "ss", 0x2E)
def _(c):
    return [sq(c, 0, 0)]


@glyph("comma", "ss", 0x2C)
def _(c):
    d = c.dot
    return [sq(c, 0, 0), ext(d * 0.25, d * 0.5, -d * 0.35, -d * 1.1, 0, 0, d / c.w * 0.55),
            clip_below(-d * 1.1)]


@glyph("colon", "ss", 0x3A)
def _(c):
    return [sq(c, 0, 0), sq(c, 0, XH - c.dot)]


@glyph("semicolon", "ss", 0x3B)
def _(c):
    d = c.dot
    return [sq(c, 0, 0), ext(d * 0.25, d * 0.5, -d * 0.35, -d * 1.1, 0, 0, d / c.w * 0.55),
            clip_below(-d * 1.1), sq(c, 0, XH - c.dot)]


@glyph("exclam", "ss", 0x21)
def _(c):
    return [L(0, c.yc, 0, c.dot + 90), sq(c, 0, 0)]


@glyph("question", "rs", 0x3F)
def _(c):
    r = (470 + c.ex - c.w) / 2
    return [A(r, c.yc - r, r, -90, 180), L(r, c.yc - 2 * r, r, c.dot + 90), sq(c, r, 0)]


@glyph("quotesingle", "ss", 0x27)
def _(c):
    return [L(0, c.yc, 0, c.yc - 170)]


@glyph("quotedbl", "ss", 0x22)
def _(c):
    return [L(0, c.yc, 0, c.yc - 170), L(c.w + 90, c.yc, c.w + 90, c.yc - 170)]


@glyph("quoteright", "ss", 0x2019)
def _(c):
    d = c.dot
    return [sq(c, 0, CAP - d), ext(d * 0.25, CAP - d * 0.5, -d * 0.35, CAP - d * 2.1, 0, 0, d / c.w * 0.55),
            clip_below(CAP - d * 2.1)]


@glyph("quoteleft", "ss", 0x2018)
def _(c):
    d = c.dot
    return [sq(c, 0, CAP - d * 2.1), ext(-d * 0.25, CAP - d * 1.6, d * 0.35, CAP, 0, 0, d / c.w * 0.55),
            clip_above(CAP)]


@glyph("quotedblright", "ss", 0x201D)
def _(c):
    base = G["quoteright"][0](c)
    return base + [p.transformed(0, 0, 0, c.dot + 70, 0) for p in base if not isinstance(p, Cut)]


@glyph("quotedblleft", "ss", 0x201C)
def _(c):
    base = G["quoteleft"][0](c)
    return base + [p.transformed(0, 0, 0, c.dot + 70, 0) for p in base if not isinstance(p, Cut)]


@glyph("hyphen", "ss", 0x2D)
def _(c):
    return [L(0, 280, 230 + c.ex * 0.4, 280, c.hb)]


@glyph("endash", "ss", 0x2013)
def _(c):
    return [L(0, 280, 460 + c.ex * 0.5, 280, c.hb)]


@glyph("emdash", "ss", 0x2014)
def _(c):
    return [L(0, 280, 820 + c.ex * 0.5, 280, c.hb)]


@glyph("underscore", "ss", 0x5F)
def _(c):
    return [L(0, -110, 500, -110, c.hb)]


@glyph("parenleft", "rr", 0x28)
def _(c):
    R = 600
    return [A(R, 250, R, 132, 228)]


@glyph("parenright", "rr", 0x29)
def _(c):
    R = 600
    return [A(-R, 250, R, -48, 48)]


@glyph("bracketleft", "ss", 0x5B)
def _(c):
    return [L(0, c.ya, 0, c.yd - 20), L(0, c.ya, 180, c.ya, c.hb), L(0, c.yd - 20, 180, c.yd - 20, c.hb)]


@glyph("bracketright", "ss", 0x5D)
def _(c):
    return [L(180, c.ya, 180, c.yd - 20), L(0, c.ya, 180, c.ya, c.hb), L(0, c.yd - 20, 180, c.yd - 20, c.hb)]


@glyph("slash", "dd", 0x2F)
def _(c):
    e = c.h * 2
    return [ext(0, -100, 330 + c.ex * 0.5, CAP + 20, e, e), clip_above(CAP + 20), clip_below(-100)]


@glyph("backslash", "dd", 0x5C)
def _(c):
    e = c.h * 2
    return [ext(0, CAP + 20, 330 + c.ex * 0.5, -100, e, e), clip_above(CAP + 20), clip_below(-100)]


@glyph("plus", "ss", 0x2B)
def _(c):
    s = 200 + c.ex * 0.3
    return [L(0, 280, 2 * s, 280, c.hb), L(s, 280 - s, s, 280 + s)]


@glyph("minus", "ss", 0x2212)
def _(c):
    s = 200 + c.ex * 0.3
    return [L(0, 280, 2 * s, 280, c.hb)]


@glyph("equal", "ss", 0x3D)
def _(c):
    s = 200 + c.ex * 0.3
    return [L(0, 190, 2 * s, 190, c.hb), L(0, 370, 2 * s, 370, c.hb)]


@glyph("multiply", "dd", 0xD7)
def _(c):
    s = 160 + c.ex * 0.3
    e = c.h * 1.5
    return [ext(0, 280 - s, 2 * s, 280 + s, e, e), ext(0, 280 + s, 2 * s, 280 - s, e, e),
            clip_above(280 + s + c.h), clip_below(280 - s - c.h), clip_left(-c.h), clip_right(2 * s + c.h)]


@glyph("asterisk", "dd", 0x2A)
def _(c):
    cx, cy, r = 0, c.yc - 150, 160 + c.ex * 0.3
    return [L(cx + r * math.cos(math.radians(90 + i * 60)), cy + r * math.sin(math.radians(90 + i * 60)),
              cx - r * math.cos(math.radians(90 + i * 60)), cy - r * math.sin(math.radians(90 + i * 60)))
            for i in range(3)]


@glyph("numbersign", "dd", 0x23)
def _(c):
    e = c.h * 1.5
    return [ext(60, c.yb, 160, c.yc, e, e), ext(300, c.yb, 400, c.yc, e, e),
            L(0, 220, 440 + c.ex * 0.4, 220, c.hb), L(40, 440, 480 + c.ex * 0.4, 440, c.hb),
            clip_above(CAP), clip_below(0)]


@glyph("percent", "dd", 0x25)
def _(c):
    r = (260 - c.w * 0.6) / 2
    rw = min(1.0, 0.6)
    e = c.h * 1.5
    return [circle(r, c.yc - r, r, rw), circle(600 + c.ex - r, c.yb + r, r, rw),
            ext(90, c.yb, 520 + c.ex, c.yc, e, e, 0.8), clip_above(CAP), clip_below(0)]


@glyph("ampersand", "rd", 0x26)
def _(c):
    ru = c.R(165 + c.ex * 0.3)
    rl = c.R(240 + c.ex * 0.4)
    cyl = c.yb - c.o + rl
    e = c.h * 1.5
    uw = 1.0 - 0.3 * c.hv
    return [
        circle(ru + 50, c.yc + c.o - ru, ru, uw),
        A(rl, cyl, rl, 25, 360),
        ext(rl + rl * 0.55, cyl + rl * 0.85, 2 * rl + 120 + c.ex * 0.4, c.yb, 0, e),
        L(2 * rl + 120 + c.ex * 0.4, c.yb, 2 * rl + 170 + c.ex * 0.4, c.yb + 120, 0.9),
        clip_below(0),
    ]


@glyph("at", "rr", 0x40)
def _(c):
    ws = min(1.0, 140 / c.w)
    ri = c.R(190 + c.ex * 0.3)
    ro = c.R(380 + c.ex * 0.5)
    cy = 240
    return [circle(ro - ri + 10, cy, ri, ws), L(ro + 10, cy + 60, ro + 10, cy - ri, ws),
            A(ro, cy, ro, -40, 300, ws)]


@glyph("dollar", "rr", 0x24)
def _(c):
    base = G["S"][0](c)
    cx = base[0].cx
    return base + [L(cx, CAP + 70, cx, -70, 0.85)]


@glyph("exclamdown", "ss", 0xA1)
def _(c):
    return [L(0, DESC + 30, 0, XH - c.dot - 90), sq(c, 0, XH - c.dot)]


@glyph("questiondown", "rs", 0xBF)
def _(c):
    r = (470 + c.ex - c.w) / 2
    base = [A(r, c.yc - r, r, -90, 180), L(r, c.yc - 2 * r, r, c.dot + 90), sq(c, r, 0)]
    cx, cy = r, CAP / 2
    return [p.transformed(180, cx, cy, 0, -180) for p in base]
