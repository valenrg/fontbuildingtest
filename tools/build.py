"""Build Fizzpop: generate UFO masters, compile OTF/TTF/WOFF2, render specimen.

Usage:  python tools/build.py [--weights Regular,Bold] [--no-compile]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import ufoLib2
from fontTools.ttLib import TTFont

import glyphs as gl
from stroke import bounce, draw_into_glyph, outline

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
MASTERS = BUILD / "masters"
FONTS = ROOT / "fonts"

FAMILY = "Fizzpop"
VERSION = (1, 0)

WEIGHTS = {
    # style name: (stroke width, OS/2 weight class)
    "Light": (100, 300),
    "Regular": (140, 400),
    "Bold": (190, 700),
}

# A few obvious kerning pairs for the diagonals; values scale with weight.
KERN_PAIRS = {
    ("A", "V"): -70, ("A", "W"): -50, ("A", "Y"): -70, ("A", "T"): -70,
    ("V", "A"): -70, ("W", "A"): -50, ("Y", "A"): -70, ("T", "A"): -70,
    ("L", "T"): -60, ("L", "V"): -60, ("L", "Y"): -60,
    ("P", "A"): -40, ("F", "A"): -40,
    ("T", "a"): -60, ("T", "e"): -60, ("T", "o"): -60, ("T", "r"): -40,
    ("T", "u"): -40, ("T", "y"): -40, ("T", "period"): -60, ("T", "comma"): -60,
    ("Y", "a"): -50, ("Y", "e"): -50, ("Y", "o"): -50, ("Y", "u"): -30,
    ("V", "a"): -40, ("V", "e"): -40, ("V", "o"): -40,
    ("r", "period"): -50, ("r", "comma"): -50, ("y", "period"): -40,
    ("f", "f"): -30, ("v", "period"): -30,
}


def build_ufo(style: str, stroke: float, weight_class: int) -> ufoLib2.Font:
    ctx = gl.Ctx(stroke)
    font = ufoLib2.Font()
    info = font.info
    info.familyName = FAMILY
    info.styleName = style
    info.unitsPerEm = gl.UPM
    info.ascender = gl.ASC
    info.descender = gl.DESC
    info.xHeight = gl.XH
    info.capHeight = gl.CAP
    info.versionMajor, info.versionMinor = VERSION
    info.copyright = "Copyright 2026 The Fizzpop Project Authors"
    info.openTypeNameDesigner = "The Fizzpop Project Authors"
    info.openTypeNameDescription = (
        "Fizzpop is a bubbly rounded display typeface with a bouncy baseline. "
        "Built from stroked skeletons; every weight shares one drawing.")
    info.openTypeOS2WeightClass = weight_class
    info.openTypeOS2WidthClass = 5
    info.openTypeOS2TypoAscender = 800
    info.openTypeOS2TypoDescender = -250
    info.openTypeOS2TypoLineGap = 0
    info.openTypeHheaAscender = 800
    info.openTypeHheaDescender = -250
    info.openTypeHheaLineGap = 0
    info.openTypeOS2WinAscent = 820
    info.openTypeOS2WinDescent = 270
    info.openTypeOS2Selection = [7]  # USE_TYPO_METRICS
    info.openTypeOS2Panose = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    info.openTypeOS2VendorID = "FIZZ"
    info.postscriptUnderlinePosition = -150
    info.postscriptUnderlineThickness = int(stroke)
    info.styleMapFamilyName = FAMILY if style in ("Regular", "Bold") else f"{FAMILY} {style}"
    info.styleMapStyleName = "bold" if style == "Bold" else "regular"

    order = []
    for name, (fn, sides, uni) in gl.G.items():
        prims = fn(ctx)
        rot, dy = gl.bounce_for(name)
        if prims and (rot or dy):
            prims = bounce(prims, rot, dy)
        path = outline(prims, ctx.h)
        g = font.newGlyph(name)
        if uni is not None:
            g.unicodes = [uni]
        if name == "space":
            g.width = 260
        else:
            draw_into_glyph(path, g)
            bounds = g.getBounds(font)
            lsb = gl.SB[sides[0]]
            rsb = gl.SB[sides[1]]
            if bounds is None:
                g.width = 300
            else:
                g.move((lsb - bounds.xMin, 0))
                g.width = round(lsb + (bounds.xMax - bounds.xMin) + rsb)
        order.append(name)
    # .notdef: a simple rounded box
    nd = font.newGlyph(".notdef")
    box = outline(gl.stadium(ctx, ctx.h + 30, gl.CAP, 0, ctx.R(150)), ctx.h)
    draw_into_glyph(box, nd)
    nd.width = round(ctx.R(150) * 2 + stroke + 60 + 2 * 30)
    font.glyphOrder = [".notdef"] + order

    scale = stroke / 140
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "",
             "feature kern {"]
    for (a, b), v in KERN_PAIRS.items():
        if a in font and b in font:
            lines.append(f"    pos {a} {b} {round(v * (0.8 + 0.2 * scale))};")
    lines.append("} kern;")
    font.features.text = "\n".join(lines) + "\n"
    return font


def compile_fonts(ufos: list[Path]):
    FONTS.mkdir(exist_ok=True)
    for fmt in ("otf", "ttf"):
        cmd = [sys.executable, "-m", "fontmake", "-o", fmt,
               "--output-dir", str(FONTS), "--flatten-components",
               "-u", *[str(u) for u in ufos]]
        subprocess.run(cmd, check=True)
    for ttf in sorted(FONTS.glob("*.ttf")):
        f = TTFont(ttf)
        f.flavor = "woff2"
        f.save(ttf.with_suffix(".woff2"))


def render_specimen():
    from PIL import Image, ImageDraw, ImageFont

    out = ROOT / "specimen" / "specimen.png"
    lines = [
        ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 64),
        ("abcdefghijklmnopqrstuvwxyz", 64),
        ("0123456789 !?&@#%$ ()[] .,:; \"'‘’ -–— +=×/", 56),
        ("Sparkling fizzy lemonade & jumbo gumdrops!", 72),
        ("The quick brown fox jumps over the lazy dog.", 48),
        ("Pack my box with five dozen liquor jugs.", 48),
    ]
    W = 1800
    styles = ["Light", "Regular", "Bold"]
    rows = []
    for st in styles:
        fp = FONTS / f"{FAMILY}-{st}.ttf"
        if not fp.exists():
            continue
        for text, size in lines:
            rows.append((ImageFont.truetype(str(fp), size), text, size))
        rows.append((None, "", 30))
    H = sum(int(size * 1.45) for _, _, size in rows) + 80
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    y = 40
    for fnt, text, size in rows:
        if fnt is not None:
            d.text((40, y), text, font=fnt, fill=(20, 20, 40))
        y += int(size * 1.45)
    img.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=",".join(WEIGHTS))
    ap.add_argument("--no-compile", action="store_true")
    args = ap.parse_args()

    MASTERS.mkdir(parents=True, exist_ok=True)
    ufos = []
    for style in args.weights.split(","):
        stroke, wc = WEIGHTS[style]
        font = build_ufo(style, stroke, wc)
        path = MASTERS / f"{FAMILY}-{style}.ufo"
        font.save(path, overwrite=True)
        ufos.append(path)
        print(f"wrote {path} ({len(font)} glyphs)")
    if args.no_compile:
        return
    compile_fonts(ufos)
    print("fonts:", ", ".join(p.name for p in sorted(FONTS.iterdir())))
    print("specimen:", render_specimen())


if __name__ == "__main__":
    main()
