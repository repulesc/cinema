#!/usr/bin/env python3
"""Take 12 icon: a deliberately pixel-art clapperboard with "12" on the slate, 16x16, two frames.

  frame 1 (left half)  = open   (idle look)
  frame 2 (right half) = clapped (shown for 0.3 s when the camera starts)

Writes hud/art/take12_icon_sheet_512x256.png (upload this one: ALL looks, switchable from the
menu), hud/art/variants/<look>_256x128.png (single-look, two frames), hud/art/preview.png, and the free
Take 12 Watch HUD's icon, watch/art/take12_watch_icon_128.png (the clapper with an eye instead of "12").
Pixels are scaled x8 with nearest-neighbour; the background is transparent.
Edit the palette or the drawing below, re-run, re-upload.

    python3 tools/art/make_icon.py
"""
import os, sys
from PIL import Image, ImageDraw

DEFAULT = "rec"            # chosen on the design board
N, SCALE = 16, 7          # 16 px sprite x7 = 112 px, centred in a 128x128 frame (8 px clear margin all round)
FRAME, PAD = 128, 8

PAL = {
    "K": (16, 16, 20, 255),      # outline
    "D": (46, 49, 64, 255),      # slate
    "W": (244, 241, 232, 255),   # chalk white
    "H": (138, 144, 166, 255),   # chalk lines
    "C": (255, 90, 95, 255),     # coral accent
    "B": (110, 214, 246, 255),   # cyan (viewfinder variant)
}

def blank():
    return [["." for _ in range(N)] for _ in range(N)]

def stripe(a, b, i):
    return a if (i // 2) % 2 == 0 else b

def draw(open_, v):
    g = blank()
    s1, s2 = ("W", "C") if v == "rec" else ("W", "D")
    # slate body rows 10..15, band rows 7..10 (outlines shared)
    for y in range(7, 16):
        for x in range(1, 15):
            edge = y in (7, 10, 15) or x in (1, 14)
            if edge:
                g[y][x] = "K"
            elif y in (8, 9):                       # fixed striped band
                g[y][x] = stripe(s2, s1, x + (y - 8))
            else:
                g[y][x] = "D"
    # "12" chalked on the slate (rows 11..14, 3x4 pixel digits)
    D1 = [".#.", "##.", ".#.", ".#."]
    D2 = ["##.", "..#", ".#.", "###"]
    x0 = 4 if v == "viewfinder" else 3   # viewfinder: digits centred
    for r in range(4):
        for c in range(3):
            ink = "B" if v == "viewfinder" else "W"
            if D1[r][c] == "#": g[11 + r][x0 + c] = ink
            if D2[r][c] == "#": g[11 + r][x0 + 4 + c] = ink
    if v == "rec":
        for (x, y) in [(11, 12), (12, 12), (11, 13), (12, 13)]:
            g[y][x] = "C"
    elif v == "classic":
        for x in range(11, 13):
            g[13][x] = "H"
    # hinged stick: 4 rows thick (outline, 2 fill, outline), hinge at x=1, bottom row 7
    rise = 4 if open_ else 0
    for x in range(1, 15):
        yb = 7 - round((x - 1) * rise / 13)
        for j in range(4):
            y = yb - j
            if 0 <= y < N:
                g[y][x] = "K" if j in (0, 3) or x in (1, 14) else stripe(s1, s2, x + j)
    return g

def frame_img(g):
    # transparent pixels carry the OUTLINE colour (alpha 0), so smoothing/mip-mapping in the viewer never
    # blends in black or white fringes. No halo. The sprite sits inside a clear margin so the frame edges
    # (and the neighbouring frame) never bleed in.
    im = Image.new("RGBA", (N, N), PAL["K"][:3] + (0,))
    for y in range(N):
        for x in range(N):
            if g[y][x] != ".":
                im.putpixel((x, y), PAL[g[y][x]])
    return im.resize((N * SCALE, N * SCALE), Image.NEAREST)

def sheet(v):
    s = Image.new("RGBA", (2 * FRAME, FRAME), PAL["K"][:3] + (0,))
    for i, o in enumerate((True, False)):
        s.paste(frame_img(draw(o, v)), (i * FRAME + PAD, PAD))
    return s

def preview(variants, out):
    # each variant: 40 px (as on screen) over sky and over a dark room, frames x4, faded at 15 %
    rows = []
    for v in variants:
        sh = sheet(v)
        f1 = sh.crop((0, 0, 128, 128)); f2 = sh.crop((128, 0, 256, 128))
        row = Image.new("RGBA", (560, 150), (255, 255, 255, 255))
        d = ImageDraw.Draw(row)
        for i in range(150):                     # sky gradient
            d.line([(0, i), (180, i)], fill=(110 + i // 3, 160 + i // 4, 225, 255))
        d.rectangle([180, 0, 360, 150], fill=(28, 26, 34, 255))
        for x0 in (20, 200):
            for k, f in enumerate((f1, f2)):
                small = f.resize((40, 40), Image.LANCZOS)
                row.alpha_composite(small, (x0 + k * 50, 20))
            faded = f1.resize((40, 40), Image.LANCZOS)
            faded.putalpha(faded.getchannel("A").point(lambda a: int(a * 0.15)))
            row.alpha_composite(faded, (x0 + 110, 20))
        row.alpha_composite(f1.resize((64, 64), Image.NEAREST), (380, 10))
        row.alpha_composite(f2.resize((64, 64), Image.NEAREST), (460, 10))
        d.text((20, 120), v, fill=(255, 255, 255, 255))
        rows.append(row)
    img = Image.new("RGBA", (560, 150 * len(rows)), (255, 255, 255, 255))
    for i, r in enumerate(rows):
        img.paste(r, (0, 150 * i))
    img.save(out)

def draw_watch():
    """Take 12 Watch (the free viewer HUD): the same open clapper, rec look, with a quiet pixel eye in place of
    the "12": chalk almond, coral pupil. One frame, it never changes."""
    g = draw(True, DEFAULT)
    for y in range(11, 15):
        for x in range(2, 14):
            g[y][x] = "D"
    E = [".#....#.", "#..CC..#", ".#....#.", "..####.."]
    for r, row in enumerate(E):
        for c, ch in enumerate(row):
            if ch == "#": g[11 + r][4 + c] = "W"
            if ch == "C": g[11 + r][4 + c] = "C"
    return g

def watch_icon():
    """128x128, transparent, the sprite centred like the Take 12 frames"""
    s = Image.new("RGBA", (FRAME, FRAME), PAL["K"][:3] + (0,))
    s.paste(frame_img(draw_watch()), (PAD, PAD))
    return s

LOOKS = ["classic", "rec", "viewfinder"]       # look number 0, 1, 2 (menu: Options > Look); 3 is spare
SHEET_COLS, SHEET_ROWS = 4, 2

def look_sheet():
    """ONE 512x256 texture with every look: 4 columns x 2 rows of 128x128 frames.
    Frame k sits at column k % 4, row k // 4 (row 0 = top). Look n uses frame 2n (open) and
    2n + 1 (clapped); frames 6 and 7 are spare for a fourth look.
    The script shows frame k with repeats <0.25, 0.5> and offset
    <(k % 4 + 0.5) / 4 - 0.5, +0.25 for the top row / -0.25 for the bottom row>."""
    s = Image.new("RGBA", (SHEET_COLS * FRAME, SHEET_ROWS * FRAME), PAL["K"][:3] + (0,))
    for n, v in enumerate(LOOKS):
        for j, o in enumerate((True, False)):
            k = 2 * n + j
            s.paste(frame_img(draw(o, v)), ((k % SHEET_COLS) * FRAME + PAD, (k // SHEET_COLS) * FRAME + PAD))
    return s

if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hud", "art")
    os.makedirs(os.path.join(root, "variants"), exist_ok=True)
    for v in LOOKS:                                 # single-look sheets (2 frames), if you want only one look
        sheet(v).save(os.path.join(root, "variants", v + "_256x128.png"))
    look_sheet().save(os.path.join(root, "take12_icon_sheet_512x256.png"))
    preview(LOOKS, os.path.join(root, "preview.png"))
    wroot = os.path.join(root, "..", "..", "watch", "art")
    os.makedirs(wroot, exist_ok=True)
    watch_icon().save(os.path.join(wroot, "take12_watch_icon_128.png"))
    print("wrote", os.path.normpath(os.path.join(root, "take12_icon_sheet_512x256.png")))
