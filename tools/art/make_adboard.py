#!/usr/bin/env python3
"""Take 12 marketing graphics (Second Life Marketplace + in-world vendor board).

Writes hud/marketing/adboard_square_1024.png (Marketplace main image / square vendor)
and hud/marketing/adboard_wide_1024x512.png (in-world vendor board / banner).

The four small "views" are pixel-art illustrations drawn here, NOT screenshots. For the best
Marketplace images, swap them for real in-world snapshots (see hud/marketing/README.md).
Change the NAME / DESCRIPTOR / TAGLINE constants below and re-run to rename the product on the boards.

    python3 tools/art/make_adboard.py
"""
import os, sys, random
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_icon as icon

NAME = "TAKE 12"
DESCRIPTOR = "CINEMATIC CAMERA HUD"
TAGLINE = "Your idle time, on film."
BG, PANEL, INK, CHALK, CORAL = (22, 24, 32), (36, 39, 52), (16, 16, 20), (244, 241, 232), (255, 90, 95)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---- a tiny 5x7 pixel font (caps) ------------------------------------------------------------
ROWS = {
 "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
 "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
 "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
 "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
 "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
 "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
 "G": [".####", "#....", "#....", "#..##", "#...#", "#...#", ".###."],
 "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
 "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
 "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
 "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
 "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
 "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
 "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
 "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
 "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
 "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
 "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
 "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
 "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
 "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
 "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
 "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
 "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
 "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
 "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
 "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
 "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
 "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
 "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
 "4": ["#...#", "#...#", "#...#", "#####", "....#", "....#", "....#"],
 "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
 "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
 "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
 "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
 "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
 " ": ["....."] * 7,
 ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
 ",": [".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."],
 "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
 "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
 "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
 "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
 ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
 "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
 "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
}
G = {k: "".join(v) for k, v in ROWS.items()}
assert all(len(v) == 35 for v in G.values()), [k for k, v in G.items() if len(v) != 35]

def ptext(img, xy, text, scale, fill, shadow=None):
    d = ImageDraw.Draw(img); x, y = xy
    for ch in text.upper():
        g = G.get(ch, G[" "])
        for i, c in enumerate(g):
            if c == "#":
                px, py = x + (i % 5) * scale, y + (i // 5) * scale
                if shadow: d.rectangle([px + scale // 2, py + scale // 2, px + scale * 3 // 2 - 1, py + scale * 3 // 2 - 1], fill=shadow)
        x += 6 * scale
    x = xy[0]
    for ch in text.upper():
        g = G.get(ch, G[" "])
        for i, c in enumerate(g):
            if c == "#":
                px, py = x + (i % 5) * scale, y + (i // 5) * scale
                d.rectangle([px, py, px + scale - 1, py + scale - 1], fill=fill)
        x += 6 * scale
def pwidth(text, scale): return len(text) * 6 * scale - scale

def font(sz): return ImageFont.truetype(BOLD, sz)

# ---- the four pixel-art views ----------------------------------------------------------------
def bands(d, w, h, y1, cols):
    n = len(cols)
    for i, c in enumerate(cols):
        d.rectangle([0, int(i * y1 / n), w, int((i + 1) * y1 / n)], fill=c)

def scene_drone(w, h, r):
    im = Image.new("RGB", (w, h), (92, 150, 92)); d = ImageDraw.Draw(im)
    for _ in range(26):                              # field patches
        x, y = r.randrange(w), r.randrange(h); pw, ph = r.randrange(6, 16), r.randrange(4, 10)
        d.rectangle([x, y, x + pw, y + ph], fill=r.choice([(104, 164, 98), (84, 138, 86), (122, 170, 96), (98, 146, 84)]))
    d.polygon([(0, int(h * .62)), (int(w * .35), int(h * .5)), (int(w * .7), int(h * .72)), (w, int(h * .6)), (w, int(h * .72)), (int(w * .7), int(h * .84)), (int(w * .35), int(h * .62)), (0, int(h * .76))], fill=(70, 140, 196))
    for _ in range(40):                              # trees
        x, y = r.randrange(w - 2), r.randrange(h - 2)
        if abs(y - h * .66) > h * .16: d.rectangle([x, y, x + 1, y + 1], fill=(40, 98, 64))
    hx, hy = int(w * .62), int(h * .22)
    d.rectangle([hx, hy + 3, hx + 6, hy + 7], fill=(236, 228, 210)); d.polygon([(hx - 1, hy + 3), (hx + 3, hy - 1), (hx + 7, hy + 3)], fill=(196, 70, 64))
    d.rectangle([int(w * .3), int(h * .38), int(w * .3), int(h * .38)], fill=CORAL)      # you, tiny
    return im

def scene_wide(w, h, r):
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im); hz = int(h * .58)
    bands(d, w, hz, hz, [(255, 214, 140), (255, 182, 122), (246, 148, 114), (224, 120, 122), (170, 102, 150), (112, 92, 158)])
    sx, sy = int(w * .62), int(hz * .78)
    d.ellipse([sx - 6, sy - 6, sx + 6, sy + 6], fill=(255, 244, 200))
    d.polygon([(0, hz), (int(w * .12), hz - 6), (int(w * .26), hz - 2), (int(w * .38), hz)], fill=(78, 62, 112))
    d.polygon([(int(w * .78), hz), (int(w * .9), hz - 8), (w, hz - 3), (w, hz)], fill=(70, 56, 106))
    for yy in range(hz, h):
        t = (yy - hz) / (h - hz); base = (int(96 - 40 * t), int(110 - 36 * t), int(176 - 40 * t))
        d.line([(0, yy), (w, yy)], fill=base)
        if yy % 2 == 0: d.line([(sx - int(5 * (1 - t) + 2 + (yy % 4)), yy), (sx + int(5 * (1 - t) + 2 + (yy % 3)), yy)], fill=(255, 214, 150))
    d.polygon([(0, h), (0, int(h * .86)), (int(w * .14), int(h * .92)), (int(w * .3), h)], fill=(30, 28, 44))
    return im

def scene_room(w, h, r):
    im = Image.new("RGB", (w, h), (52, 48, 84)); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = int(w * .2), int(h * .22), int(w * .8), int(h * .66)
    d.polygon([(0, 0), (w, 0), (x1, y0), (x0, y0)], fill=(34, 32, 58))                       # ceiling
    d.polygon([(0, 0), (x0, y0), (x0, y1), (0, h)], fill=(64, 58, 100))                      # left wall
    d.polygon([(w, 0), (x1, y0), (x1, y1), (w, h)], fill=(58, 52, 94))                       # right wall
    d.rectangle([x0, y0, x1, y1], fill=(78, 72, 118))                                        # back wall
    d.polygon([(0, h), (x0, y1), (x1, y1), (w, h)], fill=(124, 92, 74))                      # floor
    wx0, wy0, wx1, wy1 = int(w * .36), int(h * .3), int(w * .64), int(h * .54)               # a window onto the night sky
    d.rectangle([wx0, wy0, wx1, wy1], fill=(20, 24, 56))
    for _ in range(12): d.point((r.randrange(wx0 + 1, wx1), r.randrange(wy0 + 1, wy1)), fill=CHALK)
    d.rectangle([wx0, wy0, wx1, wy1], outline=(200, 190, 170))
    d.line([((wx0 + wx1) // 2, wy0), ((wx0 + wx1) // 2, wy1)], fill=(200, 190, 170))
    cx, cy = int(w * .5), int(h * .72)
    d.rectangle([cx - 9, cy - 3, cx + 9, cy + 3], fill=(230, 84, 92)); d.rectangle([cx - 9, cy - 7, cx + 9, cy - 4], fill=(196, 62, 76))
    d.rectangle([int(w * .12), int(h * .5), int(w * .12) + 1, int(h * .74)], fill=(220, 190, 120)); d.ellipse([int(w * .12) - 3, int(h * .44), int(w * .12) + 4, int(h * .5)], fill=(255, 232, 160))
    d.point((int(w * .46), int(h * .8)), fill=CORAL); d.point((int(w * .46), int(h * .79)), fill=CORAL)      # you, small
    return im

def scene_friends(w, h, r):
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im); hz = int(h * .6)
    bands(d, w, hz, hz, [(44, 52, 112), (66, 70, 132), (104, 88, 150), (160, 110, 150), (222, 140, 130)])
    d.ellipse([int(w * .8) - 4, int(h * .12), int(w * .8) + 4, int(h * .12) + 8], fill=(255, 246, 214))
    for _ in range(14): d.point((r.randrange(w), r.randrange(int(hz * .5))), fill=(220, 220, 240))
    d.rectangle([0, hz, w, h], fill=(48, 92, 74))
    for i, col in enumerate([(255, 90, 95), (92, 190, 230), (255, 206, 90), (150, 220, 140)]):
        fx = int(w * (.22 + i * .17)); fy = int(h * (.74 + (i % 2) * .05))
        d.ellipse([fx - 2, fy - 12, fx + 2, fy - 8], fill=(246, 214, 186)); d.rectangle([fx - 2, fy - 7, fx + 2, fy], fill=col); d.rectangle([fx - 2, fy + 1, fx + 2, fy + 4], fill=(40, 40, 60))
    bx0, by0, bx1, by1 = int(w * .1), int(h * .36), int(w * .9), int(h * .94)               # the viewfinder brackets
    for (ax, ay, sx_, sy_) in ((bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
        d.line([(ax, ay), (ax + 6 * sx_, ay)], fill=CHALK); d.line([(ax, ay), (ax, ay + 6 * sy_)], fill=CHALK)
    return im

SCENES = [("DRONE", scene_drone), ("WIDE", scene_wide), ("ROOM", scene_room), ("FRIENDS", scene_friends)]

def view(fn, gw, gh, scale, seed):
    return fn(gw, gh, random.Random(seed)).resize((gw * scale, gh * scale), Image.NEAREST)

def clapper(px, v=icon.DEFAULT):
    im = icon.frame_img(icon.draw(True, v)).resize((px, px), Image.NEAREST)
    return im

def looks(base, x, y, px, gap):
    """the three clapper looks (classic, rec, viewfinder), open frame, left to right"""
    for i, v in enumerate(("classic", "rec", "viewfinder")):
        c = clapper(px, v); base.paste(c, (x + i * (px + gap), y), c)

def paste_framed(base, im, xy, border=4, label=None, lab_scale=3):
    d = ImageDraw.Draw(base); x, y = xy; w, h = im.size
    d.rectangle([x - border, y - border, x + w + border - 1, y + h + border - 1], fill=INK)
    base.paste(im, (x, y))
    if label:
        d.rectangle([x - border, y + h + border, x + w + border - 1, y + h + border + 6 * lab_scale + 12], fill=INK)
        ptext(base, (x + 8, y + h + border + 6), label, lab_scale, CHALK)

def chips(base, y, items, size, x_left, x_right, gap=14, fill=CORAL):
    d = ImageDraw.Draw(base); f = font(size); widths = [d.textlength(t, font=f) + 28 for t in items]
    total = sum(widths) + gap * (len(items) - 1); x = x_left + ((x_right - x_left) - total) / 2
    for t, wd in zip(items, widths):
        d.rounded_rectangle([x, y, x + wd, y + size + 20], radius=8, fill=PANEL, outline=fill, width=2)
        d.text((x + 14, y + 8), t, font=f, fill=CHALK); x += wd + gap

def square():
    S = 1024; im = Image.new("RGB", (S, S), BG); d = ImageDraw.Draw(im)
    for yy in range(0, S, 4): d.line([(0, yy), (S, yy)], fill=(26, 28, 38) if (yy // 4) % 2 else BG)   # faint scanlines
    im.paste(clapper(176), (44, 28), clapper(176))
    ptext(im, (244, 44), NAME, 9, CHALK, shadow=CORAL)
    ptext(im, (248, 118), DESCRIPTOR, 3, CORAL)
    d.text((248, 160), TAGLINE, font=font(40), fill=(255, 196, 120))
    d.text((248, 214), "Double-tap. Walk away. Watch the world.", font=font(24), fill=(170, 176, 200))
    looks(im, 664, 30, 96, 14)
    ptext(im, (664, 138), "CHOOSE YOUR CLAPPER", 2, (170, 176, 200))
    gw, gh, sc = 64, 40, 7; px, py = 48, 262
    for i, (lab, fn) in enumerate(SCENES):
        x = px + (i % 2) * (gw * sc + 40); y = py + (i // 2) * (gh * sc + 62)
        paste_framed(im, view(fn, gw, gh, sc, 11 + i), (x, y), label=lab)
    chips(im, 936, ["Drone views", "Skybox rooms", "Friends mode", "Photo hold"], 24, 40, S - 40)
    d.text((S // 2, 996), "ONE TINY BUTTON  -  NO SETUP  -  STILL, CONTEMPLATIVE CUTS", font=font(16), fill=(120, 126, 150), anchor="mm")
    return im

def wide():
    W, H = 1024, 512; im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for yy in range(0, H, 4): d.line([(0, yy), (W, yy)], fill=(26, 28, 38) if (yy // 4) % 2 else BG)
    im.paste(clapper(128), (40, 30), clapper(128))
    ptext(im, (192, 34), NAME, 7, CHALK, shadow=CORAL)
    ptext(im, (196, 92), DESCRIPTOR, 2, CORAL)
    d.text((196, 120), TAGLINE, font=font(32), fill=(255, 196, 120))
    steps = [("DOUBLE-TAP", "start the show"), ("TAP", "menu / stop"), ("HOLD", "photo, save, next")]
    for i, (a, b) in enumerate(steps):
        ptext(im, (44, 190 + i * 0), "", 1, CHALK)
    looks(im, 716, 26, 80, 12)
    ptext(im, (716, 114), "3 CLAPPER LOOKS", 2, (170, 176, 200))
    d.text((44, 196), "Drone views, skyboxes, your friends.", font=font(22), fill=(170, 176, 200))
    # film strip along the bottom
    sy, sh = 262, 232; d.rectangle([0, sy, W, sy + sh], fill=INK)
    for x in range(10, W, 36):
        d.rounded_rectangle([x, sy + 8, x + 18, sy + 22], radius=3, fill=BG); d.rounded_rectangle([x, sy + sh - 22, x + 18, sy + sh - 8], radius=3, fill=BG)
    gw, gh, sc = 56, 36, 4
    for i, (lab, fn) in enumerate(SCENES):
        x = 26 + i * (gw * sc + 24); y = sy + 36
        im.paste(view(fn, gw, gh, sc, 21 + i), (x, y)); d.rectangle([x - 2, y - 2, x + gw * sc + 1, y + gh * sc + 1], outline=(70, 74, 92), width=2)
        ptext(im, (x + 8, y + 8), lab, 2, CHALK, shadow=INK)
    d.text((W - 36, 150), "TAP  menu\nDOUBLE-TAP  go\nHOLD  live menu", font=font(22), fill=CHALK, anchor="ra", spacing=8)
    return im

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hud", "marketing"); os.makedirs(out, exist_ok=True)
    square().save(os.path.join(out, "adboard_square_1024.png")); wide().save(os.path.join(out, "adboard_wide_1024x512.png"))
    print("wrote", os.path.normpath(out))
