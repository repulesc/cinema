#!/usr/bin/env python3
"""Take 12 marketing graphics (Second Life Marketplace + in-world vendor board).

Also writes the Lite versions (a LITE ribbon, Room and Friends dimmed as full-version features) to
hud-lite/marketing/*_lite.png.
Formats: square 1:1 (1024), portrait 3:4 (768 x 1024), landscape 4:3 (1024 x 768), wide (1024 x 512), vendor (1024 and 512).
Also the free Take 12 Watch board (watch/marketing/adboard_watch_1024.png).
Writes hud/marketing/adboard_square_1024.png (Marketplace main image),
hud/marketing/adboard_wide_1024x512.png (in-world vendor board / banner) and
hud/marketing/adboard_vendor_1024.png + adboard_vendor_512.png (a bolder, simpler square for
in-world vendor displays such as Caspervend, where the picture is small).

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
TAGLINE = "Your idle time, framed."
HOWTO = "Double-tap to start. Any key brings you back."
NEW = "NEW: SHARE THE VIEW"                                  # the banner/stamp for the 5.5+ feature (Share the view)
SMALL = "ONE TINY BUTTON  -  NO SETUP  -  SHARE WITH FRIENDS"
CHIPS = ["Drone views", "Skybox rooms", "Share the view", "Photo hold"]
BG, PANEL, INK, CHALK, CORAL = (22, 24, 32), (36, 39, 52), (16, 16, 20), (244, 241, 232), (255, 90, 95)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LITE = False                      # main() runs the boards twice; True draws the Take 12 Lite versions
FULL_ONLY = ("ROOM", "SHARE")   # the views Lite does not have

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

TAG = True          # the "LIVE" tag on the share view (the wide strip puts a label there instead)

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
    if TAG:                                                                                  # the HUD's own text: "● LIVE"
        d.rectangle([2, 2, 2 + 4 + 2 + 23 + 3, 2 + 9], fill=INK)
        d.rectangle([4, 5, 6, 7], fill=CORAL)
        ptext(im, (9, 3), "LIVE", 1, CHALK)
    return im

SCENES = [("DRONE", scene_drone), ("WIDE", scene_wide), ("ROOM", scene_room), ("SHARE", scene_friends)]

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

def ribbon(base, box):
    """the coral LITE ribbon"""
    d = ImageDraw.Draw(base); x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=CORAL, outline=INK, width=4)
    sc = max(2, (y1 - y0 - 24) // 7); ptext(base, ((x0 + x1 - pwidth("LITE", sc)) // 2, (y0 + y1 - 7 * sc) // 2), "LITE", sc, INK)

def banner(base, x, y, w, text, scale):
    """a coral band across the top of a view (the new feature)"""
    d = ImageDraw.Draw(base); h = 7 * scale + 16
    d.rectangle([x - 4, y - 4, x + w + 3, y + h - 1], fill=CORAL, outline=INK, width=4)
    ptext(base, (x + (w - pwidth(text, scale)) // 2, y + 6), text, scale, INK)

def newlabel(base, x, y, w, h, scale, text, border=4):
    """the label strip under a framed view (see paste_framed), in coral: the new feature"""
    d = ImageDraw.Draw(base); y0 = y + h + border
    d.rectangle([x - border, y0, x + w + border - 1, y0 + 6 * scale + 12], fill=CORAL)
    ptext(base, (x + 8, y0 + 6), text, scale, INK)

def stamp(base, box, lines):
    """a coral stamp, lines = [(text, scale), ...] centred"""
    d = ImageDraw.Draw(base); x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=CORAL, outline=INK, width=4)
    total = sum(7 * sc for _, sc in lines) + 8 * (len(lines) - 1); y = (y0 + y1 - total) // 2
    for text, sc in lines:
        ptext(base, ((x0 + x1 - pwidth(text, sc)) // 2, y), text, sc, INK); y += 7 * sc + 8

def scene_img(lab, fn, gw, gh, sc, seed):
    """one view; in Lite the views the Lite version does not have are dimmed and marked"""
    im = view(fn, gw, gh, sc, seed)
    if LITE and lab in FULL_ONLY:
        im = Image.blend(im, Image.new("RGB", im.size, BG), 0.72)
        t = 3 if im.width > 300 else 2
        ptext(im, ((im.width - pwidth("FULL VERSION", t)) // 2, im.height // 2 - 7 * t // 2), "FULL VERSION", t, CHALK)
    return im

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
    d.text((248, 214), HOWTO, font=font(24), fill=(170, 176, 200))
    if LITE:
        ribbon(im, (664, 30, 984, 122)); ptext(im, (664, 138), "SCENERY CAMERA + PHOTO HOLD", 2, (170, 176, 200))
    else:
        looks(im, 664, 30, 96, 14)
        ptext(im, (664, 138), "CHOOSE YOUR CLAPPER", 2, (170, 176, 200))
    gw, gh, sc = 64, 40, 7; px, py = 48, 262
    for i, (lab, fn) in enumerate(SCENES):
        x = px + (i % 2) * (gw * sc + 40); y = py + (i // 2) * (gh * sc + 62)
        paste_framed(im, scene_img(lab, fn, gw, gh, sc, 11 + i), (x, y), label=lab + ("  -  FULL" if LITE and lab in FULL_ONLY else ""))
    chips(im, 936, ["Drone views", "Wide views", "AFK start", "Photo hold"] if LITE else CHIPS, 24, 40, S - 40)
    d.text((S // 2, 996), "THE EASY WAY IN  -  ONE TINY BUTTON  -  NO SETUP" if LITE else SMALL, font=font(16), fill=(120, 126, 150), anchor="mm")
    if not LITE: newlabel(im, 48 + 64 * 7 + 40, 262 + 40 * 7 + 62, 64 * 7, 40 * 7, 3, NEW)   # the share view's label, in coral
    return im

def wide():
    W, H = 1024, 512; im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for yy in range(0, H, 4): d.line([(0, yy), (W, yy)], fill=(26, 28, 38) if (yy // 4) % 2 else BG)
    im.paste(clapper(128), (40, 30), clapper(128))
    ptext(im, (192, 34), NAME, 7, CHALK, shadow=CORAL)
    ptext(im, (196, 92), DESCRIPTOR, 2, CORAL)
    d.text((196, 120), TAGLINE, font=font(32), fill=(255, 196, 120))
    if LITE:
        ribbon(im, (716, 26, 980, 100)); ptext(im, (716, 114), "SCENERY + PHOTO HOLD", 2, (170, 176, 200))
    else:
        looks(im, 716, 26, 80, 12)
        ptext(im, (716, 114), "3 CLAPPER LOOKS", 2, (170, 176, 200))
    d.text((44, 196), "Drone and wide views, AFK start, Photo hold." if LITE else "Drone views, skyboxes, share with friends.", font=font(22), fill=(170, 176, 200))
    # film strip along the bottom
    sy, sh = 262, 232; d.rectangle([0, sy, W, sy + sh], fill=INK)
    for x in range(10, W, 36):
        d.rounded_rectangle([x, sy + 8, x + 18, sy + 22], radius=3, fill=BG); d.rounded_rectangle([x, sy + sh - 22, x + 18, sy + sh - 8], radius=3, fill=BG)
    gw, gh, sc = 56, 36, 4
    global TAG
    TAG = False                                                  # the strip puts the view's name there instead
    for i, (lab, fn) in enumerate(SCENES):
        x = 26 + i * (gw * sc + 24); y = sy + 36
        im.paste(scene_img(lab, fn, gw, gh, sc, 21 + i), (x, y)); d.rectangle([x - 2, y - 2, x + gw * sc + 1, y + gh * sc + 1], outline=(70, 74, 92), width=2)
        ptext(im, (x + 8, y + 8), lab, 2, CHALK, shadow=INK)
        if lab == "SHARE" and not LITE: banner(im, x, y + gh * sc + 10, gw * sc, "NEW: SHARE", 2)
    TAG = True
    d.text((W - 36, 150), "TAP  menu\nDOUBLE-TAP  go\nHOLD  share", font=font(22), fill=CHALK, anchor="ra", spacing=8)
    return im

def vendor():
    """bold, simple square for vendor displays: one big on-screen picture with the button in the corner"""
    S = 1024; im = Image.new("RGB", (S, S), BG); d = ImageDraw.Draw(im)
    for yy in range(0, S, 4): d.line([(0, yy), (S, yy)], fill=(26, 28, 38) if (yy // 4) % 2 else BG)
    im.paste(clapper(150), (48, 34), clapper(150))
    ptext(im, (232, 40), NAME, 11, CHALK, shadow=CORAL)
    ptext(im, (236, 128), DESCRIPTOR, 3, CORAL)
    d.text((236, 168), TAGLINE, font=font(38), fill=(255, 196, 120))
    gw, gh, sc = 96, 56, 9                      # the hero: what you see on screen, with the HUD button top right
    hero = view(scene_wide, gw, gh, sc, 31)
    hx, hy = 80, 236
    paste_framed(im, hero, (hx, hy), border=6)
    btn = clapper(72); im.paste(btn, (hx + gw * sc - 72 - 22, hy + 18), btn)
    ptext(im, (hx + gw * sc - 190, hy + 98), "DOUBLE-TAP", 2, CHALK, shadow=INK)
    if LITE:
        ribbon(im, (80, 784, 380, 884)); ptext(im, (80, 894), "THE EASY WAY IN", 2, (170, 176, 200))
        chips(im, 790, ["Drone", "Wide"], 30, 420, S - 60); chips(im, 870, ["AFK start", "Photo hold"], 30, 420, S - 60)
    else:
        looks(im, 80, 784, 96, 14)
        ptext(im, (80, 894), "3 CLAPPER LOOKS", 2, (170, 176, 200))
        chips(im, 790, ["Drone", "Skybox"], 30, 420, S - 60)
        chips(im, 870, ["Share live", "Photo hold"], 30, 420, S - 60)
        stamp(im, (730, 44, 976, 126), [("NEW", 3), ("SHARE THE VIEW", 2)])
    d.text((S // 2, 990), "ONE TINY BUTTON  -  SHARE WITH FRIENDS" if not LITE else "ONE TINY BUTTON  -  STILL, CONTEMPLATIVE CUTS", font=font(20), fill=(120, 126, 150), anchor="mm")
    return im

def watch():
    """the free Take 12 Watch: one big view, as the Watch shows it (the HUD's own text above the icon)"""
    S = 1024; im = Image.new("RGB", (S, S), BG); d = ImageDraw.Draw(im)
    for yy in range(0, S, 4): d.line([(0, yy), (S, yy)], fill=(26, 28, 38) if (yy // 4) % 2 else BG)
    w = icon.watch_icon().resize((176, 176), Image.NEAREST); im.paste(w, (40, 26), w)
    ptext(im, (236, 40), "TAKE 12 WATCH", 7, CHALK, shadow=CORAL)
    ptext(im, (240, 112), "FOR FRIENDS OF TAKE 12", 3, CORAL)
    d.text((240, 156), "See your friend's view.", font=font(38), fill=(255, 196, 120))
    d.text((240, 206), "Wear it. Nothing to click.", font=font(22), fill=(170, 176, 200))
    stamp(im, (820, 40, 980, 124), [("FREE", 5)])
    gw, gh, sc = 96, 56, 9
    hero = scene_wide(gw, gh, random.Random(31)).resize((gw * sc, gh * sc), Image.NEAREST)   # their camera, with the Watch's own text
    t = "WATCHING PANO"; ImageDraw.Draw(hero).rectangle([20, 20, 20 + pwidth(t, 3) + 24, 20 + 7 * 3 + 20], fill=INK)
    ptext(hero, (32, 30), t, 3, CHALK); hx, hy = 80, 246
    paste_framed(im, hero, (hx, hy), border=6)
    btn = icon.watch_icon().resize((72, 72), Image.NEAREST); im.paste(btn, (hx + gw * sc - 72 - 22, hy + 18), btn)
    ptext(im, (hx + gw * sc - 112, hy + 98), "WEAR IT", 2, CHALK, shadow=INK)
    chips(im, 800, ["Nothing to click", "Follows their cuts"], 30, 80, S - 80)
    chips(im, 880, ["Tap: your camera", "Double-tap: next"], 30, 80, S - 80)
    d.text((S // 2, 990), "ONE TINY BUTTON  -  NO TAKE 12 NEEDED", font=font(20), fill=(120, 126, 150), anchor="mm")
    return im

def _base(W, H):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for yy in range(0, H, 4): d.line([(0, yy), (W, yy)], fill=(26, 28, 38) if (yy // 4) % 2 else BG)
    return im, d

def _chip_list():
    return ["Drone views", "Wide views", "AFK start", "Photo hold"] if LITE else CHIPS

def portrait():
    """3:4 portrait (768 x 1024): header, one big view, three small views, chips"""
    W, H = 768, 1024; im, d = _base(W, H)
    im.paste(clapper(150), (40, 30), clapper(150))
    ptext(im, (216, 38), NAME, 9, CHALK, shadow=CORAL)
    ptext(im, (220, 112), DESCRIPTOR, 3, CORAL)
    d.text((220, 150), TAGLINE, font=font(34), fill=(255, 196, 120))
    d.text((220, 200), HOWTO, font=font(20), fill=(170, 176, 200))
    gw, gh, sc = 96, 56, 7; hx, hy = 48, 250                       # the hero view, 672 x 392
    paste_framed(im, scene_img("WIDE", scene_wide, gw, gh, sc, 41), (hx, hy), border=5, label="WIDE")
    small = [("DRONE", scene_drone), ("ROOM", scene_room), ("FRIENDS", scene_friends)]; gw2, gh2, sc2 = 52, 32, 4; y2 = 722
    for i, (lab, fn) in enumerate(small):
        x = 48 + i * (gw2 * sc2 + 24)
        paste_framed(im, scene_img(lab, fn, gw2, gh2, sc2, 51 + i), (x, y2), border=4, label=lab + ("  FULL" if LITE and lab in FULL_ONLY else ""), lab_scale=2)
    if LITE:
        ribbon(im, (48, 884, 200, 930)); ptext(im, (216, 898), "SCENERY + PHOTO HOLD", 2, (170, 176, 200))
    else:
        looks(im, 48, 876, 54, 10); ptext(im, (232, 898), "CHOOSE YOUR CLAPPER", 2, (170, 176, 200))
    chips(im, 944, _chip_list(), 20, 30, W - 30, gap=10)
    d.text((W // 2, 1004), ("THE EASY WAY IN  -  ONE TINY BUTTON" if LITE else SMALL), font=font(14), fill=(120, 126, 150), anchor="mm")
    if not LITE: stamp(im, (612, 36, 736, 120), [("NEW", 4), ("SHARE", 2)])
    return im

def landscape43():
    """4:3 landscape (1024 x 768): header row and four views"""
    W, H = 1024, 768; im, d = _base(W, H)
    im.paste(clapper(110), (40, 22), clapper(110))
    ptext(im, (178, 26), NAME, 8, CHALK, shadow=CORAL)
    ptext(im, (182, 90), DESCRIPTOR, 2, CORAL)
    d.text((182, 112), TAGLINE, font=font(28), fill=(255, 196, 120))
    d.text((182, 148), HOWTO, font=font(18), fill=(170, 176, 200))
    if LITE: ribbon(im, (760, 26, 984, 96))
    else:
        looks(im, 700, 20, 82, 12)
        ptext(im, (700, 108), "CHOOSE YOUR CLAPPER", 2, (170, 176, 200))
    gw, gh, sc = 56, 34, 6; px, py = 156, 186
    for i, (lab, fn) in enumerate(SCENES):
        x = px + (i % 2) * (gw * sc + 40); y = py + (i // 2) * (gh * sc + 48)
        paste_framed(im, scene_img(lab, fn, gw, gh, sc, 61 + i), (x, y), border=4, label=lab + ("  -  FULL" if LITE and lab in FULL_ONLY else ""), lab_scale=2)
    chips(im, 690, _chip_list(), 20, 30, W - 30, gap=12)
    d.text((W // 2, 748), ("THE EASY WAY IN  -  ONE TINY BUTTON" if LITE else SMALL), font=font(14), fill=(120, 126, 150), anchor="mm")
    if not LITE: newlabel(im, 156 + 56 * 6 + 40, 186 + 34 * 6 + 48, 56 * 6, 34 * 6, 2, NEW)
    return im

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    builds = [(False, os.path.join(base, "hud", "marketing"), "")]
    if "--lite" in sys.argv:                     # Lite is paused (frozen at 4.4.5): its boards are only rebuilt on request
        builds.append((True, os.path.join(base, "hud-lite", "marketing"), "_lite"))
    for lite, out, suf in builds:
        LITE = lite; os.makedirs(out, exist_ok=True)
        square().save(os.path.join(out, f"adboard_square_1024{suf}.png")); wide().save(os.path.join(out, f"adboard_wide_1024x512{suf}.png"))
        portrait().save(os.path.join(out, f"adboard_portrait_3x4_768x1024{suf}.png")); landscape43().save(os.path.join(out, f"adboard_landscape_4x3_1024x768{suf}.png"))
        v = vendor(); v.save(os.path.join(out, f"adboard_vendor_1024{suf}.png")); v.resize((512, 512), Image.LANCZOS).save(os.path.join(out, f"adboard_vendor_512{suf}.png"))
        print("wrote", os.path.normpath(out))
        if not lite:
            wo = os.path.join(base, "watch", "marketing"); os.makedirs(wo, exist_ok=True)
            watch().save(os.path.join(wo, "adboard_watch_1024.png")); print("wrote", os.path.normpath(wo))
