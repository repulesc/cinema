#!/usr/bin/env python3
"""Take 12: the box's three textures (8.2.0). Cinema black, as the boards: the board on the front (and back), the name
on the sides, the [12] on the lid. hud/box/unpack.lsl puts them on a 0.45 x 0.25 x 0.45 m box by itself.

    python3 tools/art/make_box.py      -> hud/box/take12_box_front.png (1024), _side (512 x 1024), _top (1024 x 512)
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_strip as MS
import make_adboard as AB
from make_strip import font, spaced, spaced_w

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hud", "box")
BLACK = AB.BLACK


def side():
    """the spine: TAKE 12 upright, letter-spaced, and the line small under it"""
    t = Image.new("RGBA", (1024, 512), BLACK + (255,))
    d = ImageDraw.Draw(t)
    f = font("InterDisplay-SemiBold.otf", 96)
    w = spaced_w(AB.NAME, f, 0.3)
    spaced(d, 512 - w / 2, 230, AB.NAME, f, AB.a(0.95), 0.3)
    fl = font("Inter-Medium.otf", 26)
    line = "A CINEMATIC CAMERA FOR SECOND LIFE"
    spaced(d, 512 - spaced_w(line, fl, 0.2) / 2, 330, line, fl, AB.a(0.45), 0.2)
    return t.rotate(90, expand=True).convert("RGB")


def top():
    """the lid: the [12], alone"""
    t = Image.new("RGBA", (1024, 512), BLACK + (255,))
    disc = MS.disc((255, 255, 255)).resize((220, 220), Image.LANCZOS)
    t.alpha_composite(disc, (402, 146))
    return t.convert("RGB")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    AB.board(1024, 1024, "full").save(os.path.join(OUT, "take12_box_front.png"))
    side().save(os.path.join(OUT, "take12_box_side.png"))
    top().save(os.path.join(OUT, "take12_box_top.png"))
    print("wrote", os.path.normpath(OUT))
