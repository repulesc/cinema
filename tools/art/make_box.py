#!/usr/bin/env python3
"""Take 12: the box's three textures (8.2.0; the mark, 8.4.1). Cinema black, as the boards: the board on the front
(and back, and the card on screen while the worn box unpacks), TAKE (12) up the sides, the [12] alone on the lid.
hud/box/unpack.lsl puts them on a 0.45 x 0.25 x 0.45 m box by itself.

    python3 tools/art/make_box.py      -> hud/box/take12_box_front.png (1024), _side (512 x 1024), _top (1024 x 512)
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_adboard as AB

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hud", "box")
BLACK = AB.BLACK


def side():
    """the spine: TAKE (12), upright"""
    t = Image.new("RGBA", (1024, 512), BLACK + (255,))
    L = AB.lockup(104)
    t.alpha_composite(L, ((1024 - L.width) // 2, (512 - L.height) // 2))
    return t.rotate(90, expand=True).convert("RGB")


def top():
    """the lid: the [12], alone"""
    t = Image.new("RGBA", (1024, 512), BLACK + (255,))
    m = AB.mark(200)
    t.alpha_composite(m, (512 - 100, 256 - 100))
    return t.convert("RGB")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    AB.board(1024, 1024, "full").save(os.path.join(OUT, "take12_box_front.png"))
    side().save(os.path.join(OUT, "take12_box_side.png"))
    top().save(os.path.join(OUT, "take12_box_top.png"))
    print("wrote", os.path.normpath(OUT))
