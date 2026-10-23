#!/usr/bin/env python3
"""Take 12 marketing graphics (7.0.1: minimal) for the Second Life Marketplace and in-world vendors.

One idea per picture: a single quiet frame fills the board, golden-line ticks barely visible at its edges, the small
clapper in a corner, the name and one line. Nothing else (the product is one button; the boards say so).
  Take 12          the dusk horizon     "A camera for Second Life."
  Take 12 Scenery  the drone view       "Free. The place, while you are away."
  Take 12 Watch    friends at dusk      "Free. See your friend's camera."
Formats: square 1:1 (1024), portrait 3:4 (768 x 1024), landscape 4:3 (1024 x 768), wide (1024 x 512), vendor
(1024 and 512: the same frame, bigger type). The views are pixel-art drawn here, not screenshots.

    python3 tools/art/make_adboard.py
"""
import os, sys, random
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_icon as icon

NAME = "TAKE 12"
TAGLINE = "A camera for Second Life."
FREE_NAME, FREE_LINE = "TAKE 12 SCENERY", "Free. The place, while you are away."
WATCH_NAME, WATCH_LINE = "TAKE 12 WATCH", "Free. See your friend's camera."
BG, PANEL, INK, CHALK, CORAL = (22, 24, 32), (36, 39, 52), (16, 16, 20), (244, 241, 232), (255, 90, 95)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FREE = False                      # main() runs the boards twice; True draws the free Take 12 Scenery versions

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

LENS_TAG = False    # (7.0.1: the frames carry no HUD text)

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
    if LENS_TAG and not FREE:                                                                # "85 mm": your lens
        d.rectangle([2, 2, 2 + 29 + 3, 2 + 9], fill=INK)
        ptext(im, (4, 3), "85 MM", 1, CHALK)
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

TAG = False         # (7.0.1: the frames carry no HUD text)

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
        if TAG: d.line([(ax, ay), (ax + 6 * sx_, ay)], fill=CHALK); d.line([(ax, ay), (ax, ay + 6 * sy_)], fill=CHALK)
    if TAG:                                                                                  # the HUD's own text: "● LIVE"
        d.rectangle([2, 2, 2 + 4 + 2 + 23 + 3, 2 + 9], fill=INK)
        d.rectangle([4, 5, 6, 7], fill=CORAL)
        ptext(im, (9, 3), "LIVE", 1, CHALK)
    return im

def font(sz, bold=True): return ImageFont.truetype(BOLD if bold else REG, sz)

def clapper(px, kind="full"):
    g = {"full": lambda: icon.draw(True, icon.DEFAULT), "free": lambda: icon.draw_scenery(True)}.get(kind)
    im = icon.watch_icon() if kind == "watch" else icon.frame_img(g())
    return im.resize((px, px), Image.NEAREST)

def board(W, H, scene, seed, name, line, kind, big=1.0):
    """one frame: the scene fills the board; a soft dark foot for the type; golden-line ticks; clapper, name, line"""
    px = 8
    im = scene(-(-W // px), -(-H // px), random.Random(seed)).resize((-(-W // px) * px, -(-H // px) * px), Image.NEAREST).crop((0, 0, W, H)).convert("RGBA")
    foot = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(foot)
    y0 = int(H * 0.62)
    for y in range(y0, H):                                    # the foot: transparent to 78 % black
        fd.line([(0, y), (W, y)], fill=(10, 10, 14, int(200 * ((y - y0) / (H - y0)) ** 1.4)))
    im = Image.alpha_composite(im, foot)
    d = ImageDraw.Draw(im, "RGBA")
    m, t, tick = int(min(W, H) * 0.035), 2, int(min(W, H) * 0.022)      # golden-line ticks (38.2 % from each side)
    for f in (0.382, 0.618):
        x, y = int(W * f), int(H * f)
        d.rectangle([x - 1, m, x, m + tick], fill=CHALK + (110,))                  # (none at the foot: the type is there)
        d.rectangle([m, y - 1, m + tick, y], fill=CHALK + (110,)); d.rectangle([W - m - tick, y - 1, W - m, y], fill=CHALK + (110,))
    u = int((W * H) ** 0.5)                                 # the type follows the board's area (a wide strip too)
    ic = int(u * 0.085 * big)
    pad = int(u * 0.06)
    c = clapper(ic, kind)
    im.paste(c, (pad, H - pad - ic), c)
    sc = max(2, int(u * 0.0068 * big))
    tx = pad + ic + int(u * 0.03)
    ptext(im, (tx, H - pad - ic + int(ic * 0.08)), name, sc, CHALK)
    d.text((tx, H - pad - ic + int(ic * 0.08) + 7 * sc + int(u * 0.018)), line, font=font(max(14, int(u * 0.03 * big)), False), fill=(226, 222, 214))
    return im.convert("RGB")

def the(kind):
    """the frame, the name and the line of each product"""
    if kind == "watch": return scene_friends, 31, WATCH_NAME, WATCH_LINE
    if kind == "free": return scene_drone, 23, FREE_NAME, FREE_LINE
    return scene_wide, 41, NAME, TAGLINE

def square(kind="full"):   f, sd, n, l = the(kind); return board(1024, 1024, f, sd, n, l, kind)
def wide(kind="full"):     f, sd, n, l = the(kind); return board(1024, 512, f, sd, n, l, kind)
def portrait(kind="full"): f, sd, n, l = the(kind); return board(768, 1024, f, sd, n, l, kind)
def landscape43(kind="full"): f, sd, n, l = the(kind); return board(1024, 768, f, sd, n, l, kind)
def vendor(kind="full"):   f, sd, n, l = the(kind); return board(1024, 1024, f, sd, n, l, kind, big=1.45)   # read from across a store
def watch():               return square("watch")

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    builds = [("full", os.path.join(base, "hud", "marketing"), ""), ("free", os.path.join(base, "scenery", "marketing"), "_scenery")]
    for kind, out, suf in builds:
        FREE = (kind == "free"); os.makedirs(out, exist_ok=True)
        square(kind).save(os.path.join(out, f"adboard_square_1024{suf}.png")); wide(kind).save(os.path.join(out, f"adboard_wide_1024x512{suf}.png"))
        portrait(kind).save(os.path.join(out, f"adboard_portrait_3x4_768x1024{suf}.png")); landscape43(kind).save(os.path.join(out, f"adboard_landscape_4x3_1024x768{suf}.png"))
        v = vendor(kind); v.save(os.path.join(out, f"adboard_vendor_1024{suf}.png")); v.resize((512, 512), Image.LANCZOS).save(os.path.join(out, f"adboard_vendor_512{suf}.png"))
        print("wrote", os.path.normpath(out))
    wo = os.path.join(base, "watch", "marketing"); os.makedirs(wo, exist_ok=True)
    watch().save(os.path.join(wo, "adboard_watch_1024.png")); print("wrote", os.path.normpath(wo))
