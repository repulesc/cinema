#!/usr/bin/env python3
"""Take 12 marketing graphics (8.0.10) for the Second Life Marketplace and in-world vendors: cinema black.

No scene, no drawing: what a camera maker would print. A black board; a frame drawn the way a cinema monitor draws its
frame lines (hairline corners, a faint centre mark, the frame and the lens written small at its top edge, the shot at
its foot); under it the [12] (the HUD's own disc, from tools/art/make_strip.py), the name letter-spaced, one line, and a
quiet row of what is inside. Inter throughout, white at three strengths, nothing else.
  Take 12          a 2.39 frame   PORTRAIT · MEDIUM · ME     "A cinematic camera for Second Life."
  Take 12 Scenery  a 2.39 frame   SCENIC · DRIFT             "Free. The place, while you are away."
Formats: square 1:1 (1024), portrait 3:4 (768 x 1024), landscape 4:3 (1024 x 768), wide (1024 x 512), vendor
(1024 and 512: bigger type, no row, read from across a store).

    python3 tools/art/make_adboard.py
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_strip
from make_strip import font, spaced, spaced_w

NAME = "TAKE 12"
TAGLINE = "A cinematic camera for Second Life."
FREE_NAME, FREE_LINE = "TAKE 12 SCENERY", "Free. The place, while you are away."
BLACK = (9, 9, 10)
WHITE = make_strip.WHITE
K = 2                                   # drawn at twice the size, then reduced: hairlines stay crisp


def the(kind):
    """each product's name, line, the shot written at the frame's foot, and the row of what is inside"""
    if kind == "free":
        return FREE_NAME, FREE_LINE, "SCENIC  ·  DRIFT", "DRIFT  ·  NEAR  ·  ROOM  ·  FAR"
    return NAME, TAGLINE, "PORTRAIT  ·  MEDIUM  ·  ME", "TRACKING  ·  PORTRAIT  ·  FIXED  ·  SCENIC"


def a(v): return WHITE + (int(255 * v),)


def frame_lines(d, x0, y0, x1, y1, u, top_l, top_r, foot):
    """a monitor's frame lines: corners, a centre mark, small writing at the edges"""
    c = int(u * 0.045)                               # corner arm
    t = max(K, int(u * 0.0026))                      # hairline
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.rectangle([min(x, x + sx * c), y - (t if sy < 0 else 0), max(x, x + sx * c), y + (t if sy > 0 else 0)], fill=a(0.85))
        d.rectangle([x - (t if sx < 0 else 0), min(y, y + sy * c), x + (t if sx > 0 else 0), max(y, y + sy * c)], fill=a(0.85))
    d.rectangle([x0, y0, x1, y1], outline=a(0.14), width=max(1, t // 2))       # the frame itself, barely there
    mx, my, m = (x0 + x1) // 2, (y0 + y1) // 2, int(u * 0.012)
    d.rectangle([mx - m, my - t // 2, mx + m, my + t // 2], fill=a(0.35))
    d.rectangle([mx - t // 2, my - m, mx + t // 2, my + m], fill=a(0.35))
    f = font("Inter-Medium.otf", int(u * 0.019))
    g = int(u * 0.016)
    spaced(d, x0, y0 - g, top_l, f, a(0.6), 0.16)
    spaced(d, x1 - spaced_w(top_r, f, 0.16), y0 - g, top_r, f, a(0.6), 0.16)
    spaced(d, mx - spaced_w(foot, f, 0.16) / 2, y1 - g * 1.6, foot, f, a(0.75), 0.16)


def board(W, H, kind, big=1.0):
    w, h = W * K, H * K
    im = Image.new("RGBA", (w, h), BLACK + (255,))
    d = ImageDraw.Draw(im)
    name, line, foot, row = the(kind)
    u = (w * h) ** 0.5
    wide = w / h >= 1.6
    row_on = big == 1.0 and not wide                 # the row needs the room a wide board has not got
    ic = int(u * 0.075 * big)
    fn = font("InterDisplay-SemiBold.otf", int(u * 0.058 * big))
    fl = font("Inter-Regular.otf", int(u * 0.026 * big))
    # one block, centred: the 2.39 frame, the [12] with the name, the line (the row keeps to the foot)
    fw = w * (0.62 if wide else 0.80)
    fh = fw / 2.39
    g1, g2 = int(u * 0.11 * big), int(u * 0.045 * big)
    block = fh + g1 + ic + g2 + fl.size
    room = h - (int(u * 0.10) if row_on else 0)
    y0 = int((room - block) / 2 + u * 0.01)
    x0, x1 = int((w - fw) / 2), int((w + fw) / 2)
    y1 = int(y0 + fh)
    frame_lines(d, x0, y0, x1, y1, u, "2.39", "35 MM", foot)
    nw = spaced_w(name, fn, 0.22)
    gap = int(u * 0.028)
    x = (w - (ic + gap + nw)) / 2
    y = y1 + g1
    disc = make_strip.disc((255, 255, 255)).resize((ic, ic), Image.LANCZOS)
    im.alpha_composite(disc, (int(x), int(y)))
    spaced(d, x + ic + gap, y + ic / 2 + int(u * 0.002), name, fn, a(0.96), 0.22)
    ly = y + ic + g2
    d.text((w / 2, ly), line, font=fl, fill=a(0.62), anchor="mm")
    if row_on:                                       # the row of what is inside: the quietest thing on the board
        fr = font("Inter-Medium.otf", int(u * 0.017))
        rw = spaced_w(row, fr, 0.2)
        spaced(d, (w - rw) / 2, h - int(u * 0.06), row, fr, a(0.38), 0.2)
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
