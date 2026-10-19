"""Render a close-up grid of selected glyph strings for every weight."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
strings = sys.argv[2:] or ["a e g s", "y M 4 1", "k K R &"]
out = sys.argv[1]
size = 150
weights = ["Hairline", "Light", "Regular", "Bold", "Poster"]
W = 2200
H = len(weights) * len(strings) * int(size * 1.35) + 40
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
y = 20
for st in weights:
    f = ImageFont.truetype(str(ROOT / "fonts" / f"Mirrorball-{st}.ttf"), size)
    for s in strings:
        d.text((20, y), s, font=f, fill="black")
        y += int(size * 1.35)
img.save(out)
