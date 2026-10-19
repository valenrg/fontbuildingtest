"""Build Mirrorball: generate UFO masters, compile OTF/TTF/WOFF2, render specimen.

Usage:  python tools/build.py [--weights Regular,Bold] [--no-compile]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import ufoLib2
from fontTools.ttLib import TTFont

import glyphs as gl
from stroke import draw_into_glyph, outline

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
MASTERS = BUILD / "masters"
FONTS = ROOT / "fonts"

FAMILY = "Mirrorball"
VERSION = (1, 0)

WEIGHTS = {
    # style name: (stroke width, OS/2 weight class)
    "Hairline": (20, 100),
    "Light": (60, 300),
    "Regular": (95, 400),
    "Bold": (150, 700),
    "Poster": (200, 900),
}

# Kerning for the diagonals and open shapes; values scale a little with weight.
KERN_PAIRS = {
    ("A", "V"): -60, ("A", "W"): -40, ("A", "Y"): -60, ("A", "T"): -60,
    ("V", "A"): -60, ("W", "A"): -40, ("Y", "A"): -60, ("T", "A"): -60,
    ("L", "T"): -50, ("L", "V"): -50, ("L", "Y"): -50, ("L", "W"): -30,
    ("P", "A"): -40, ("F", "A"): -30, ("A", "O"): -10, ("O", "A"): -10,
    ("T", "a"): -50, ("T", "e"): -50, ("T", "o"): -50, ("T", "r"): -35,
    ("T", "u"): -35, ("T", "y"): -35, ("T", "period"): -60, ("T", "comma"): -60,
    ("Y", "a"): -40, ("Y", "e"): -40, ("Y", "o"): -40, ("Y", "u"): -25,
    ("V", "a"): -35, ("V", "e"): -35, ("V", "o"): -35,
    ("r", "period"): -40, ("r", "comma"): -40, ("y", "period"): -40, ("y", "comma"): -40,
    ("v", "period"): -30, ("f", "f"): -10, ("r", "a"): -10,
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
    info.copyright = "Copyright 2026 The Mirrorball Project Authors"
    info.openTypeNameDesigner = "The Mirrorball Project Authors"
    info.openTypeNameDescription = (
        "Mirrorball is a tight geometric grotesque with a seventies disco "
        "flavour, from Hairline to Poster. Built from stroked skeletons; "
        "every weight shares one drawing.")
    info.openTypeOS2WeightClass = weight_class
    info.openTypeOS2WidthClass = 5
    info.openTypeOS2TypoAscender = 780
    info.openTypeOS2TypoDescender = -220
    info.openTypeOS2TypoLineGap = 0
    info.openTypeHheaAscender = 780
    info.openTypeHheaDescender = -220
    info.openTypeHheaLineGap = 0
    info.openTypeOS2WinAscent = 800
    info.openTypeOS2WinDescent = 240
    info.openTypeOS2Selection = [7]  # USE_TYPO_METRICS
    info.openTypeOS2Panose = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    info.openTypeOS2VendorID = "MIRR"
    info.postscriptUnderlinePosition = -130
    info.postscriptUnderlineThickness = int(stroke)
    info.styleMapFamilyName = FAMILY if style in ("Regular", "Bold") else f"{FAMILY} {style}"
    info.styleMapStyleName = "bold" if style == "Bold" else "regular"

    order = []
    for name, (fn, sides, uni) in gl.G.items():
        prims = fn(ctx)
        path = outline(prims, ctx.h)
        g = font.newGlyph(name)
        if uni is not None:
            g.unicodes = [uni]
        if name == "space":
            g.width = round(200 + stroke * 0.3)
        else:
            draw_into_glyph(path, g)
            bounds = g.getBounds(font)
            lsb = ctx.sb[sides[0]]
            rsb = ctx.sb[sides[1]]
            if bounds is None:
                g.width = 300
            else:
                g.move((lsb - bounds.xMin, 0))
                g.width = round(lsb + (bounds.xMax - bounds.xMin) + rsb)
        order.append(name)
    nd = font.newGlyph(".notdef")
    box = outline(gl.stadium(ctx.h + 30, gl.CAP, 0, ctx.R(120)), ctx.h)
    draw_into_glyph(box, nd)
    nd.width = round(ctx.R(120) * 2 + stroke + 60 + 60)
    font.glyphOrder = [".notdef"] + order

    scale = stroke / 95
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "",
             "feature kern {"]
    for (a, b), v in KERN_PAIRS.items():
        if a in font and b in font:
            lines.append(f"    pos {a} {b} {round(v * (0.7 + 0.3 * scale))};")
    lines.append("} kern;")
    font.features.text = "\n".join(lines) + "\n"
    return font


def compile_fonts(ufos: list[Path]):
    FONTS.mkdir(exist_ok=True)
    for old in FONTS.iterdir():
        old.unlink()
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
        ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 60),
        ("abcdefghijklmnopqrstuvwxyz", 60),
        ("0123456789 !?&@#%$ ()[] .,:; \"'‘’“” -–— +=×/", 52),
        ("Disco light array & neon pink synthesizer", 72),
        ("The quick brown fox jumps over the lazy dog.", 46),
    ]
    W = 1800
    rows = []
    for st in WEIGHTS:
        fp = FONTS / f"{FAMILY}-{st}.ttf"
        if not fp.exists():
            continue
        for text, size in lines:
            rows.append((ImageFont.truetype(str(fp), size), text, size))
        rows.append((None, "", 26))
    H = sum(int(size * 1.4) for _, _, size in rows) + 60
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    y = 30
    for fnt, text, size in rows:
        if fnt is not None:
            d.text((40, y), text, font=fnt, fill=(15, 15, 25))
        y += int(size * 1.4)
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
