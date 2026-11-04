#!/usr/bin/env python3
"""Render the journal's two Play Store graphics from its own launcher icon.

Play asks for a 512x512 icon and a 1024x500 feature graphic. The launcher mark is a vector drawable
on a 108-unit viewport, so the same shapes are redrawn here at store size with the same colours the
app ships. Pillow is the only dependency:

    python3 dev/play-art.py

writes `play/icon-512.png` and `play/feature-graphic.png`. Point FONTS somewhere with DejaVu if the
path below is not on this machine.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ICON_BG, CARD, LINES = "#E6D5BC", "#C8AD8D", "#FBF6EC"
BG, INK, MUTE = "#F4EBDD", "#4A3F35", "#9C8B77"
FONTS = "/usr/share/fonts/truetype/dejavu"


def icon(size=512):
    """The launcher icon: a card of paper with three lines of writing."""
    s = size / 108.0
    im = Image.new("RGB", (size, size), ICON_BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([30 * s, 26 * s, 76 * s, 82 * s], radius=6 * s, fill=CARD)
    for x0, y0, x1, y1 in ((36, 40, 64, 44), (36, 52, 64, 56), (36, 64, 54, 68)):
        d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=LINES)
    return im


def feature(mark, out):
    im = Image.new("RGB", (1024, 500), BG)
    tile = mark.resize((230, 230), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", tile.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 229, 229], radius=52, fill=255)
    im.paste(tile, (78, 135), mask)
    d = ImageDraw.Draw(im)
    d.text((350, 152), "UJournal", fill=INK,
           font=ImageFont.truetype(os.path.join(FONTS, "DejaVuSerif-Bold.ttf"), 76))
    d.text((352, 254), "A quiet journal, one entry a day", fill=MUTE,
           font=ImageFont.truetype(os.path.join(FONTS, "DejaVuSans.ttf"), 27))
    im.save(out, "PNG", optimize=True)


if __name__ == "__main__":
    os.makedirs("play", exist_ok=True)
    mark = icon()
    mark.save("play/icon-512.png", "PNG", optimize=True)
    feature(mark, "play/feature-graphic.png")
    print("wrote play/icon-512.png and play/feature-graphic.png")
