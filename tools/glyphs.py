"""Fizzpop glyph skeletons.

Every glyph is a function of a Ctx (which knows the half stroke width `h`
and the vertical metrics) and returns a list of primitives. Coordinates are
stroke *centre-lines*; the outline is `h` units either side. Radii are mostly
expressed as an outer radius minus `h`, so the silhouette stays the same
across weights while the counters shrink as the stroke grows.
"""
from __future__ import annotations

import math

from stroke import Arc, Dot, Line, skeleton_bounds

UPM = 1000
XH = 520          # x-height
CAP = 700         # cap height
ASC = 740         # ascender
DESC = -210       # descender
OVER = 12         # overshoot

# side bearings by side type
SB = {"s": 44, "r": 30, "d": 18, "o": 0}


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
        # lowercase bowl: outer radius XH/2 + overshoot
        self.rx = XH / 2 + OVER - h
        self.cyx = XH / 2            # centre y of lowercase bowl
        # lowercase arch (n, h, m, u)
        self.rn = self.R(238)
        # cap stadium (O, C, G, Q, U)
        self.rO = self.R(300)
        self.dot = h * 1.18          # dot radius

    def R(self, outer):
        """Centre-line radius for a given outer radius. At heavy weights the
        radius is clamped so a counter always survives; the silhouette then
        grows a little, which suits a chunky display face."""
        return max(outer - self.h, self.h + 10)


G = {}


def glyph(name, sides="ss", unicode=None):
    def deco(fn):
        G[name] = (fn, sides, unicode)
        return fn
    return deco


def L(x0, y0, x1, y1, hs=1.0):
    return Line(x0, y0, x1, y1, hs)


def A(cx, cy, r, a0, a1, hs=1.0):
    return Arc(cx, cy, r, a0, a1, hs)


def circle(cx, cy, r, hs=1.0):
    return Arc(cx, cy, r, 0, 360, hs)


def stadium(c, x, ytop, ybot, r):
    """Closed rounded-rectangle loop (centre-line) between ytop and ybot."""
    return [
        A(x + r, ytop - r, r, 0, 180),
        L(x, ytop - r, x, ybot + r),
        A(x + r, ybot + r, r, 180, 360),
        L(x + 2 * r, ybot + r, x + 2 * r, ytop - r),
    ]


# ---------------------------------------------------------------- lowercase
@glyph("a", "rs", 0x61)
def _(c):
    return [circle(c.rx, c.cyx, c.rx), L(2 * c.rx, c.yx, 2 * c.rx, c.yb)]


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
    # keep the bar no thicker than 40% of the counter so it never closes up
    counter = 2 * (c.rx - c.h)
    hs = min(1.0, 0.4 * counter / c.w)
    return [L(0, c.cyx, 2 * c.rx, c.cyx, hs), A(c.rx, c.cyx, c.rx, 0, 318)]


@glyph("f", "ss", 0x66)
def _(c):
    rf = c.R(170)
    return [
        L(0, c.yb, 0, c.ya - rf),
        A(rf, c.ya - rf, rf, 25, 180),
        L(-110, c.yx, 150, c.yx),
    ]


@glyph("g", "rs", 0x67)
def _(c):
    rg = c.R(200)
    return [
        circle(c.rx, c.cyx, c.rx),
        L(2 * c.rx, c.yx, 2 * c.rx, c.yd + rg),
        A(2 * c.rx - rg, c.yd + rg, rg, -190, 0),
    ]


@glyph("h", "ss", 0x68)
def _(c):
    rn = c.rn
    return [
        L(0, c.ya, 0, c.yb),
        A(rn, c.yx - rn, rn, 0, 180),
        L(2 * rn, c.yx - rn, 2 * rn, c.yb),
    ]


@glyph("i", "ss", 0x69)
def _(c):
    return [L(0, c.yx, 0, c.yb), Dot(0, XH + 60 + c.dot, c.dot)]


@glyph("j", "ds", 0x6A)
def _(c):
    rj = c.R(190)
    return [
        L(0, c.yx, 0, c.yd + rj),
        A(-rj, c.yd + rj, rj, -115, 0),
        Dot(0, XH + 60 + c.dot, c.dot),
    ]


@glyph("k", "sd", 0x6B)
def _(c):
    return [
        L(0, c.ya, 0, c.yb),
        L(0, 215, 255, c.yx),
        L(95, 300, 275, c.yb),
    ]


@glyph("l", "ss", 0x6C)
def _(c):
    rl = c.R(165)
    return [L(0, c.ya, 0, c.yb + rl), A(rl, c.yb + rl, rl, 180, 320)]


@glyph("m", "ss", 0x6D)
def _(c):
    rm = c.R(205)
    return [
        L(0, c.yx, 0, c.yb),
        A(rm, c.yx - rm, rm, 0, 180),
        L(2 * rm, c.yx - rm, 2 * rm, c.yb),
        A(3 * rm, c.yx - rm, rm, 0, 180),
        L(4 * rm, c.yx - rm, 4 * rm, c.yb),
    ]


@glyph("n", "ss", 0x6E)
def _(c):
    rn = c.rn
    return [
        L(0, c.yx, 0, c.yb),
        A(rn, c.yx - rn, rn, 0, 180),
        L(2 * rn, c.yx - rn, 2 * rn, c.yb),
    ]


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
    rr = c.R(200)
    return [L(0, c.yx, 0, c.yb), A(rr, c.yx - rr, rr, 20, 180)]


@glyph("s", "rr", 0x73)
def _(c):
    total = (c.yx - c.yb + 2 * c.o) / 2
    ru, rl = total * 0.47, total * 0.53
    cx = rl
    cyu = c.yx + c.o - ru
    cyl = c.yb - c.o + rl
    return [A(cx, cyu, ru, 30, 270), A(cx, cyl, rl, -150, 90)]


@glyph("t", "ss", 0x74)
def _(c):
    rt = c.R(165)
    return [
        L(0, c.ya - 60, 0, c.yb + rt),
        A(rt, c.yb + rt, rt, 180, 320),
        L(-120, c.yx, 150, c.yx),
    ]


@glyph("u", "ss", 0x75)
def _(c):
    rn = c.rn
    return [
        L(0, c.yx, 0, c.yb + rn),
        A(rn, c.yb + rn, rn, 180, 360),
        L(2 * rn, c.yx, 2 * rn, c.yb),
    ]


@glyph("v", "dd", 0x76)
def _(c):
    return [L(0, c.yx, 215, c.yb), L(215, c.yb, 430, c.yx)]


@glyph("w", "ss", 0x77)
def _(c):
    r = c.R(175)
    return [
        L(0, c.yx, 0, c.yb + r),
        A(r, c.yb + r, r, 180, 360),
        L(2 * r, c.yb + r, 2 * r, c.yx - 110),
        A(3 * r, c.yb + r, r, 180, 360),
        L(4 * r, c.yx, 4 * r, c.yb + r),
    ]


@glyph("x", "dd", 0x78)
def _(c):
    return [L(0, c.yx, 400, c.yb), L(0, c.yb, 400, c.yx)]


@glyph("y", "ds", 0x79)
def _(c):
    rn = c.rn
    rj = c.R(190)
    return [
        L(0, c.yx, 0, c.yb + rn),
        A(rn, c.yb + rn, rn, 180, 360),
        L(2 * rn, c.yx, 2 * rn, c.yd + rj),
        A(2 * rn - rj, c.yd + rj, rj, -115, 0),
    ]


@glyph("z", "ss", 0x7A)
def _(c):
    return [L(0, c.yx, 380, c.yx), L(380, c.yx, 0, c.yb), L(0, c.yb, 380, c.yb)]


# ---------------------------------------------------------------- uppercase
@glyph("A", "dd", 0x41)
def _(c):
    w = 580
    yl, yr = c.yb, c.yc
    t = (255 - yl) / (yr - yl)
    xl = t * (w / 2)
    return [
        L(0, c.yb, w / 2, c.yc),
        L(w / 2, c.yc, w, c.yb),
        L(xl, 255, w - xl, 255),
    ]


@glyph("B", "sr", 0x42)
def _(c):
    H2 = (c.yc - c.yb) / 2
    r1, r2 = H2 * 0.47, H2 * 0.53
    ym = c.yc - 2 * r1
    return [
        L(0, c.yc, 0, c.yb),
        L(0, c.yc, 70, c.yc), A(70, c.yc - r1, r1, -90, 90), L(70, ym, 0, ym),
        L(0, ym, 90, ym), A(90, ym - r2, r2, -90, 90), L(90, c.yb, 0, c.yb),
    ]


@glyph("C", "rr", 0x43)
def _(c):
    r = c.rO
    top = c.yc + c.o
    bot = c.yb - c.o
    return [
        A(r, top - r, r, 48, 180),
        L(0, top - r, 0, bot + r),
        A(r, bot + r, r, 180, 312),
    ]


@glyph("D", "sr", 0x44)
def _(c):
    r = (c.yc - c.yb) / 2 + c.o
    cy = (c.yc + c.yb) / 2
    xd = 90
    return [
        L(0, c.yc, 0, c.yb),
        L(0, cy + r, xd, cy + r),
        A(xd, cy, r, -90, 90),
        L(xd, cy - r, 0, cy - r),
    ]


@glyph("E", "ss", 0x45)
def _(c):
    ym = (c.yc + c.yb) / 2 + 12
    return [
        L(0, c.yc, 0, c.yb),
        L(0, c.yc, 370, c.yc),
        L(0, ym, 310, ym),
        L(0, c.yb, 370, c.yb),
    ]


@glyph("F", "ss", 0x46)
def _(c):
    ym = (c.yc + c.yb) / 2 + 12
    return [L(0, c.yc, 0, c.yb), L(0, c.yc, 370, c.yc), L(0, ym, 300, ym)]


@glyph("G", "rs", 0x47)
def _(c):
    r = c.rO
    top = c.yc + c.o
    bot = c.yb - c.o
    return [
        A(r, top - r, r, 48, 180),
        L(0, top - r, 0, bot + r),
        A(r, bot + r, r, 180, 360),
        L(2 * r, bot + r, 2 * r, 320),
        L(2 * r - 190, 320, 2 * r, 320),
    ]


@glyph("H", "ss", 0x48)
def _(c):
    ym = (c.yc + c.yb) / 2 + 12
    return [L(0, c.yc, 0, c.yb), L(480, c.yc, 480, c.yb), L(0, ym, 480, ym)]


@glyph("I", "ss", 0x49)
def _(c):
    return [L(0, c.yc, 0, c.yb)]


@glyph("J", "ds", 0x4A)
def _(c):
    rj = c.R(215)
    return [L(0, c.yc, 0, c.yb + rj), A(-rj, c.yb + rj, rj, -150, 0)]


@glyph("K", "sd", 0x4B)
def _(c):
    return [
        L(0, c.yc, 0, c.yb),
        L(0, 330, 360, c.yc),
        L(120, 430, 390, c.yb),
    ]


@glyph("L", "ss", 0x4C)
def _(c):
    return [L(0, c.yc, 0, c.yb), L(0, c.yb, 350, c.yb)]


@glyph("M", "ss", 0x4D)
def _(c):
    w = 620
    return [
        L(0, c.yc, 0, c.yb),
        L(0, c.yc, w / 2, 210),
        L(w / 2, 210, w, c.yc),
        L(w, c.yc, w, c.yb),
    ]


@glyph("N", "ss", 0x4E)
def _(c):
    w = 500
    return [L(0, c.yc, 0, c.yb), L(0, c.yc, w, c.yb), L(w, c.yc, w, c.yb)]


@glyph("O", "rr", 0x4F)
def _(c):
    return stadium(c, 0, c.yc + c.o, c.yb - c.o, c.rO)


@glyph("P", "sr", 0x50)
def _(c):
    rp = (c.yc - 310) / 2
    return [
        L(0, c.yc, 0, c.yb),
        L(0, c.yc, 80, c.yc),
        A(80, c.yc - rp, rp, -90, 90),
        L(80, c.yc - 2 * rp, 0, c.yc - 2 * rp),
    ]


@glyph("Q", "rr", 0x51)
def _(c):
    r = c.rO
    return stadium(c, 0, c.yc + c.o, c.yb - c.o, r) + [
        L(r + 40, c.yb + 110, r + 280, c.yb - 130)
    ]


@glyph("R", "sd", 0x52)
def _(c):
    rp = (c.yc - 310) / 2
    return [
        L(0, c.yc, 0, c.yb),
        L(0, c.yc, 80, c.yc),
        A(80, c.yc - rp, rp, -90, 90),
        L(80, c.yc - 2 * rp, 0, c.yc - 2 * rp),
        L(120, c.yc - 2 * rp, 420, c.yb),
    ]


@glyph("S", "rr", 0x53)
def _(c):
    total = (c.yc - c.yb + 2 * c.o) / 2
    ru, rl = total * 0.46, total * 0.54
    cx = rl
    cyu = c.yc + c.o - ru
    cyl = c.yb - c.o + rl
    return [A(cx, cyu, ru, 30, 270), A(cx, cyl, rl, -150, 90)]


@glyph("T", "ss", 0x54)
def _(c):
    return [L(0, c.yc, 520, c.yc), L(260, c.yc, 260, c.yb)]


@glyph("U", "ss", 0x55)
def _(c):
    r = c.rO
    bot = c.yb - c.o
    return [
        L(0, c.yc, 0, bot + r),
        A(r, bot + r, r, 180, 360),
        L(2 * r, c.yc, 2 * r, bot + r),
    ]


@glyph("V", "dd", 0x56)
def _(c):
    return [L(0, c.yc, 290, c.yb), L(290, c.yb, 580, c.yc)]


@glyph("W", "dd", 0x57)
def _(c):
    w = 860
    return [
        L(0, c.yc, w / 4, c.yb),
        L(w / 4, c.yb, w / 2, c.yc - 180),
        L(w / 2, c.yc - 180, 3 * w / 4, c.yb),
        L(3 * w / 4, c.yb, w, c.yc),
    ]


@glyph("X", "dd", 0x58)
def _(c):
    return [L(0, c.yc, 540, c.yb), L(0, c.yb, 540, c.yc)]


@glyph("Y", "dd", 0x59)
def _(c):
    return [L(0, c.yc, 270, 330), L(540, c.yc, 270, 330), L(270, 330, 270, c.yb)]


@glyph("Z", "ss", 0x5A)
def _(c):
    return [L(0, c.yc, 500, c.yc), L(500, c.yc, 0, c.yb), L(0, c.yb, 500, c.yb)]


# ------------------------------------------------------------------- digits
@glyph("zero", "rr", 0x30)
def _(c):
    return stadium(c, 0, c.yc + c.o, c.yb - c.o, c.R(265))


@glyph("one", "ds", 0x31)
def _(c):
    return [L(0, c.yc, 0, c.yb), L(0, c.yc, -150, c.yc - 150)]


@glyph("two", "rs", 0x32)
def _(c):
    r = c.R(260)
    ex = r + r * math.cos(math.radians(-45))
    ey = c.yc - r + r * math.sin(math.radians(-45))
    return [
        A(r, c.yc - r, r, -45, 180),
        L(ex, ey, 0, c.yb),
        L(0, c.yb, 2 * r + 10, c.yb),
    ]


@glyph("three", "rr", 0x33)
def _(c):
    H2 = (c.yc - c.yb + 2 * c.o) / 2
    r1, r2 = H2 * 0.47, H2 * 0.53
    cx = r2
    return [
        A(cx, c.yc + c.o - r1, r1, -90, 165),
        A(cx, c.yb - c.o + r2, r2, -165, 90),
    ]


@glyph("four", "ds", 0x34)
def _(c):
    xs = 340
    return [L(xs, c.yc, 0, 225), L(0, 225, xs + 110, 225), L(xs, c.yc, xs, c.yb)]


@glyph("five", "sr", 0x35)
def _(c):
    ytop = 405
    r5 = (ytop - c.yb + c.o) / 2
    cx = 130
    return [
        L(0, c.yc, 390, c.yc),
        L(0, c.yc, 0, ytop),
        L(0, ytop, cx, ytop),
        A(cx, ytop - r5, r5, -200, 90),
    ]


@glyph("six", "rr", 0x36)
def _(c):
    r6 = c.R(215)
    rt = c.R(265)
    return [
        circle(r6, c.yb - c.o + r6, r6),
        L(0, c.yb - c.o + r6, 0, c.yc + c.o - rt),
        A(rt, c.yc + c.o - rt, rt, 35, 180),
    ]


@glyph("seven", "sd", 0x37)
def _(c):
    return [L(0, c.yc, 460, c.yc), L(460, c.yc, 150, c.yb)]


@glyph("eight", "rr", 0x38)
def _(c):
    H2 = (c.yc - c.yb + 2 * c.o) / 2
    r1, r2 = H2 * 0.46, H2 * 0.54
    cx = r2
    return [circle(cx, c.yc + c.o - r1, r1), circle(cx, c.yb - c.o + r2, r2)]


@glyph("nine", "rr", 0x39)
def _(c):
    r9 = c.R(215)
    rt = c.R(265)
    return [
        circle(r9, c.yc + c.o - r9, r9),
        L(2 * r9, c.yc + c.o - r9, 2 * r9, c.yb - c.o + rt),
        A(2 * r9 - rt, c.yb - c.o + rt, rt, -145, 0),
    ]


# ------------------------------------------------------------- punctuation
@glyph("space", "oo", 0x20)
def _(c):
    return []


@glyph("period", "ss", 0x2E)
def _(c):
    return [Dot(0, c.dot, c.dot)]


@glyph("comma", "ss", 0x2C)
def _(c):
    return [Dot(0, c.dot, c.dot), L(0, c.dot, -45, -150)]


@glyph("colon", "ss", 0x3A)
def _(c):
    return [Dot(0, c.dot, c.dot), Dot(0, XH - c.dot, c.dot)]


@glyph("semicolon", "ss", 0x3B)
def _(c):
    return [Dot(0, c.dot, c.dot), L(0, c.dot, -45, -150), Dot(0, XH - c.dot, c.dot)]


@glyph("exclam", "ss", 0x21)
def _(c):
    return [L(0, c.yc, 0, 265), Dot(0, c.dot, c.dot)]


@glyph("question", "rs", 0x3F)
def _(c):
    r = c.R(240)
    ex = r + r * math.cos(math.radians(-60))
    ey = c.yc - r + r * math.sin(math.radians(-60))
    return [
        A(r, c.yc - r, r, -60, 180),
        L(ex, ey, r, 265),
        Dot(r, c.dot, c.dot),
    ]


@glyph("quotesingle", "ss", 0x27)
def _(c):
    return [L(0, c.yc, 0, c.yc - 180)]


@glyph("quotedbl", "ss", 0x22)
def _(c):
    return [L(0, c.yc, 0, c.yc - 180), L(190, c.yc, 190, c.yc - 180)]


@glyph("quoteright", "ss", 0x2019)
def _(c):
    return [Dot(0, c.yc - c.dot, c.dot), L(0, c.yc - c.dot, -45, c.yc - 230)]


@glyph("quoteleft", "ss", 0x2018)
def _(c):
    return [Dot(0, c.yc - 230 + c.dot, c.dot), L(0, c.yc - 230 + c.dot, 45, c.yc)]


@glyph("hyphen", "ss", 0x2D)
def _(c):
    return [L(0, 290, 210, 290)]


@glyph("endash", "ss", 0x2013)
def _(c):
    return [L(0, 290, 420, 290)]


@glyph("emdash", "ss", 0x2014)
def _(c):
    return [L(0, 290, 760, 290)]


@glyph("underscore", "ss", 0x5F)
def _(c):
    return [L(0, -120, 480, -120)]


@glyph("parenleft", "rr", 0x28)
def _(c):
    R = 560
    return [A(R, 260, R, 128, 232)]


@glyph("parenright", "rr", 0x29)
def _(c):
    R = 560
    return [A(-R + 0, 260, R, -52, 52)]


@glyph("bracketleft", "ss", 0x5B)
def _(c):
    return [L(0, c.ya, 0, -160), L(0, c.ya, 170, c.ya), L(0, -160, 170, -160)]


@glyph("bracketright", "ss", 0x5D)
def _(c):
    return [L(170, c.ya, 170, -160), L(0, c.ya, 170, c.ya), L(0, -160, 170, -160)]


@glyph("slash", "dd", 0x2F)
def _(c):
    return [L(0, -120, 340, c.yc + 20)]


@glyph("backslash", "dd", 0x5C)
def _(c):
    return [L(0, c.yc + 20, 340, -120)]


@glyph("plus", "ss", 0x2B)
def _(c):
    return [L(0, 290, 380, 290), L(190, 100, 190, 480)]


@glyph("minus", "ss", 0x2212)
def _(c):
    return [L(0, 290, 380, 290)]


@glyph("equal", "ss", 0x3D)
def _(c):
    return [L(0, 200, 380, 200), L(0, 380, 380, 380)]


@glyph("multiply", "dd", 0xD7)
def _(c):
    return [L(0, 110, 340, 470), L(0, 470, 340, 110)]


@glyph("asterisk", "dd", 0x2A)
def _(c):
    cx, cy, r = 0, c.yc - 150, 150
    out = []
    for i in range(3):
        a = math.radians(90 + i * 60)
        out.append(L(cx + r * math.cos(a), cy + r * math.sin(a),
                     cx - r * math.cos(a), cy - r * math.sin(a)))
    return out


@glyph("numbersign", "dd", 0x23)
def _(c):
    return [
        L(60, c.yb, 160, c.yc), L(300, c.yb, 400, c.yc),
        L(0, 230, 420, 230), L(50, 440, 470, 440),
    ]


@glyph("percent", "dd", 0x25)
def _(c):
    r = c.R(200)
    hs = min(1.0, 155 / c.w)   # keep the ring counters open at heavy weights
    return [
        circle(r, c.yc - r, r, hs),
        circle(620 - r, c.yb + r, r, hs),
        L(80, c.yb, 540, c.yc),
    ]


@glyph("ampersand", "rd", 0x26)
def _(c):
    ru = c.R(160)
    rl = c.R(235)
    cyl = c.yb - c.o + rl
    hs = min(1.0, 150 / c.w)
    return [
        circle(ru + 40, c.yc + c.o - ru, ru, hs),
        A(rl, cyl, rl, 20, 360),
        L(rl + rl * 0.6, cyl + rl * 0.8, 2 * rl + 110, c.yb),
        L(2 * rl + 110, c.yb, 2 * rl + 150, c.yb + 110),
    ]


@glyph("at", "rr", 0x40)
def _(c):
    ri = c.R(205)
    ro = c.R(380)
    cy = 240
    hs = min(1.0, 150 / c.w)   # keep the inner counter open at heavy weights
    return [
        circle(ro - ri + 20, cy, ri, hs),
        L(ro + 20, cy + 80, ro + 20, cy - ri, hs),
        A(ro, cy, ro, -40, 300, hs),
    ]


@glyph("dollar", "rr", 0x24)
def _(c):
    total = (c.yc - c.yb + 2 * c.o) / 2
    ru, rl = total * 0.46, total * 0.54
    cx = rl
    cyu = c.yc + c.o - ru
    cyl = c.yb - c.o + rl
    return [A(cx, cyu, ru, 30, 270), A(cx, cyl, rl, -150, 90),
            L(cx, c.yc + 90, cx, c.yb - 90)]


@glyph("exclamdown", "ss", 0xA1)
def _(c):
    return [L(0, c.yb - 160, 0, 260), Dot(0, XH - c.dot, c.dot)]


@glyph("questiondown", "sr", 0xBF)
def _(c):
    # a 180-degree turn of the question mark, dropped to the descender
    prims = G["question"][0](c)
    x0, y0, x1, y1 = skeleton_bounds(prims)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return [pr.transformed(180, cx, cy, 0, -200) for pr in prims]


# ------------------------------------------------------------------ bounce
# Deterministic per-glyph "sparkle": a small rotation (degrees) and a
# vertical shift. Keeps the hand-set, bouncy feel without hurting legibility.
BOUNCE_TABLE = [
    (1.8, 10), (-1.4, -8), (0.6, 16), (-2.2, 4), (1.2, -12),
    (-0.8, 12), (2.0, -4), (-1.6, 8), (0.0, -14), (1.4, 6),
]
NO_BOUNCE = {"space", "period", "comma", "colon", "semicolon", "hyphen",
             "endash", "emdash", "underscore", "minus", "plus", "equal",
             "multiply", "parenleft", "parenright", "bracketleft",
             "bracketright", "slash", "backslash", "quotesingle",
             "quotedbl", "quoteleft", "quoteright", "at", "numbersign",
             "asterisk"}


def bounce_for(name):
    if name in NO_BOUNCE:
        return 0.0, 0.0
    idx = sum((i + 1) * ord(ch) for i, ch in enumerate(name)) % len(BOUNCE_TABLE)
    return BOUNCE_TABLE[idx]
