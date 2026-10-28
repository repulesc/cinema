#!/usr/bin/env python3
"""Take 12 marketing graphics (8.4.1) for the Second Life Marketplace and in-world vendors: the mark, quiet.

The [12] is the 12 (2026-10, the owner's pick of four directions): the word TAKE and the HUD's own [12] (its disc and
its filming ring, from tools/art/make_strip.py) make one lockup, so the name is said once (the 8.2 boards set the [12]
beside TAKE 12: twelve, twice). A black board, the lockup centred, one line under it, nothing else. Inter, white at two
strengths.
  Take 12          TAKE (12)            "Your Second Life, filmed."
  Take 12 Scenery  TAKE (12) SCENERY    "Free. The place, while you are away."
Formats: square 1:1 (1024), portrait 3:4 (768 x 1024), landscape 4:3 (1024 x 768), wide (1024 x 512), vendor
(1024 and 512: bigger, read from across a store). tools/art/make_box.py dresses the box with the same lockup.

    python3 tools/art/make_adboard.py
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_strip
from make_strip import font, spaced, spaced_w

TAGLINE = "Your Second Life, filmed."
FREE_NAME, FREE_LINE = "SCENERY", "Free. The place, while you are away."
BLACK = (9, 9, 10)
WHITE = make_strip.WHITE
K = 2                                   # drawn at twice the size, then reduced: edges stay crisp


def a(v): return WHITE + (int(255 * v),)


def mark(px):
    """the [12] as on the HUD while it films: the disc, and its thin ring round it"""
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = int(px * 0.88)
    im.alpha_composite(make_strip.disc(WHITE).resize((d, d), Image.LANCZOS), ((px - d) // 2, (px - d) // 2))
    ring = make_strip.ring(1.0, track=False, width=5).resize((int(px * 64 / 60), int(px * 64 / 60)), Image.LANCZOS)
    o = (px - ring.width) // 2
    im.alpha_composite(ring.crop((-o, -o, -o + px, -o + px)) if o < 0 else ring, (max(o, 0), max(o, 0)))
    return im


def lockup(h):
    """TAKE, and the [12] as its second word: an image h px tall (the cap height), the mark 1.62 h"""
    f = font("InterDisplay-Bold.otf", int(h))
    tw = spaced_w("TAKE", f, 0.06)
    dp = int(h * 1.62)
    gap = int(h * 0.22)
    im = Image.new("RGBA", (int(tw + gap + dp + 4), dp + 4), (0, 0, 0, 0))
    spaced(ImageDraw.Draw(im), 0, dp / 2 + h * 0.02, "TAKE", f, a(0.97), 0.06)
    im.alpha_composite(mark(dp), (int(tw + gap), 0))
    return im


def board(W, H, kind, big=1.0):
    w, h = W * K, H * K
    im = Image.new("RGBA", (w, h), BLACK + (255,))
    d = ImageDraw.Draw(im)
    u = min(w, h)
    L = lockup(u * 0.105 * big)
    fl = font("Inter-Regular.otf", int(u * 0.03 * big))
    sub = font("Inter-Medium.otf", int(u * 0.026 * big))
    line = FREE_LINE if kind == "free" else TAGLINE
    g1, g2 = int(u * 0.075 * big), int(u * 0.05 * big)
    block = L.height + g1 + fl.size + ((sub.size + g2) if kind == "free" else 0)
    y = (h - block) / 2
    im.alpha_composite(L, (int((w - L.width) / 2), int(y)))
    y += L.height + g1
    if kind == "free":                               # the free build: SCENERY under the mark, then its line
        spaced(d, (w - spaced_w(FREE_NAME, sub, 0.42)) / 2, y + sub.size / 2, FREE_NAME, sub, a(0.85), 0.42)
        y += sub.size + g2
    d.text((w / 2, y + fl.size / 2), line, font=fl, fill=a(0.6), anchor="mm")
    return im.resize((W, H), Image.LANCZOS).convert("RGB")


def square(kind="full"): return board(1024, 1024, kind)
def wide(kind="full"): return board(1024, 512, kind)
def portrait(kind="full"): return board(768, 1024, kind)
def landscape43(kind="full"): return board(1024, 768, kind)
def vendor(kind="full"): return board(1024, 1024, kind, big=1.35)   # read from across a store


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    builds = [("full", os.path.join(base, "hud", "marketing"), ""), ("free", os.path.join(base, "scenery", "marketing"), "_scenery")]
    for kind, out, suf in builds:
        os.makedirs(out, exist_ok=True)
        square(kind).save(os.path.join(out, f"adboard_square_1024{suf}.png"))
        wide(kind).save(os.path.join(out, f"adboard_wide_1024x512{suf}.png"))
        portrait(kind).save(os.path.join(out, f"adboard_portrait_3x4_768x1024{suf}.png"))
        landscape43(kind).save(os.path.join(out, f"adboard_landscape_4x3_1024x768{suf}.png"))
        v = vendor(kind)
        v.save(os.path.join(out, f"adboard_vendor_1024{suf}.png"))
        v.resize((512, 512), Image.LANCZOS).save(os.path.join(out, f"adboard_vendor_512{suf}.png"))
        print("wrote", os.path.normpath(out))
