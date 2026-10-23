#!/usr/bin/env python3
"""Take 12 keys (6.5; 6.8: Connect; 7.1: Adjust): the texture of the soft-key strip, hud/art/take12_keys_1024.png.

One atlas, one row per key set, the keys in use marked by a coral underline. 7.1: 1024 x 1024, two columns of ten rows
(row r is in column r // 10, row r % 10), for the ADJUST key's on and off rows. keys.lsl shows a row on the strip prim
with repeats and offsets (it never needs a second texture), and reads which key you touched from the touch position.
The style is the lab concept's (lab/softkeys): thin 1-pixel line icons in chalk on a near-black key, a small-caps
label in the HUD's pixel font.

    python3 tools/art/make_keys.py
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_adboard as ab

W, H = 1024, 1024
COL = 512                     # two columns of rows
PER = 10                      # rows in a column
CW, CH = 76, 96               # one key cell; a row of up to 5 keys is 380 px wide
PX = 5                        # one icon pixel = 5 texture pixels: a key is 75 x 95
KEY, LINE, CHALK, DIM, CORAL = (20, 21, 26), (52, 55, 68), (236, 233, 224), (150, 154, 170), (255, 90, 95)

# keep in step with keys.lsl: the rows, top first, and their keys (the one in use after '*')
ROWS = [
    ("live",   ["NEXT", "INVITE", "OFF"], ()),
    ("watch",  ["NEXT", "TURN", "OFF"], ()),
]
FREE, STILL, GROUP = ["SAVE", "A", "B", "STOP", "ADJUST"], ["FULL", "HALF", "CLOSE", "ADJUST"], ["NEXT", "ADJUST"]
for adj in (False, True):                                  # Freehand: the view in use, ADJUST off / on
    for v, nm in ((None, "free"), ("A", "freeA"), ("B", "freeB")):
        ROWS.append((nm + "+" * adj, FREE, tuple(x for x in (v, "ADJUST" if adj else None) if x)))
for adj in (False, True):                                  # Me: the framing in use, ADJUST off / on
    for f in ("FULL", "HALF", "CLOSE"):
        ROWS.append((f.lower() + "+" * adj, STILL, tuple(x for x in (f, "ADJUST" if adj else None) if x)))
for adj in (False, True):                                  # Us, Friends
    ROWS.append(("group" + "+" * adj, GROUP, ("ADJUST",) if adj else ()))

# 11 x 11 line icons: '#' a 1 px line, nothing filled, no figures
ICONS = {
    "NEXT":   ["...........", "...........", "..#...#....", "...#...#...", "....#...#..", ".....#...#.", "....#...#..", "...#...#...", "..#...#....", "...........", "..........."],
    "HOLD":   ["...........", "..###.###..", "..#.#.#.#..", "..#.#.#.#..", "..#.#.#.#..", "..#.#.#.#..", "..#.#.#.#..", "..#.#.#.#..", "..#.#.#.#..", "..###.###..", "..........."],
    "INVITE": ["...........", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".#########.", ".....#.....", ".....#.....", ".....#.....", ".....#.....", "..........."],
    "TURN":   ["...........", "....###....", "..##...##..", "..#.....#..", ".#.......#.", ".#...#...#.", ".#.......#.", "..#.....#..", "..##...##..", "....###....", "..........."],
    "OFF":    ["...........", ".###.......", "#...#......", "#...#.#....", ".###...#...", "...........", "...#...###.", "....#.#...#", "......#...#", ".......###.", "..........."],
    "END":    ["...........", ".#########.", ".#.......#.", ".#.......#.", ".#.......#.", ".#.......#.", ".#.......#.", ".#.......#.", ".#.......#.", ".#########.", "..........."],
    "ASK":    ["...........", ".....#.....", "....###....", "...#.#.#...", "..#..#..#..", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".#########.", "..........."],
    "LEAVE":  ["#######....", "#.....#....", "#.....#..#.", "#.....#...#", "#..########", "#.....#...#", "#.....#..#.", "#.....#....", "#.....#....", "#######....", "..........."],
    "SAVE":   ["...........", ".....#.....", ".....#.....", ".....#.....", "...#.#.#...", "....###....", ".....#.....", ".#.......#.", ".#.......#.", ".#########.", "..........."],
    "A":      [".#########.", ".#.......#.", ".#...#...#.", ".#..#.#..#.", ".#.#...#.#.", ".#.#####.#.", ".#.#...#.#.", ".#.#...#.#.", ".#.......#.", ".#########.", "..........."],
    "B":      [".#########.", ".#.......#.", ".#.####..#.", ".#.#...#.#.", ".#.####..#.", ".#.#...#.#.", ".#.#...#.#.", ".#.####..#.", ".#.......#.", ".#########.", "..........."],
    "STOP":   ["...........", "...........", "..#######..", "..#.....#..", "..#.....#..", "..#.....#..", "..#.....#..", "..#.....#..", "..#######..", "...........", "..........."],
    "FULL":   ["##.......##", "#....#....#", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".....#.....", "#....#....#", "##.......##"],
    "HALF":   ["##.......##", "#.........#", ".....#.....", "....###....", "....#.#....", ".....#.....", ".....#.....", ".....#.....", ".....#.....", "#....#....#", "##...#...##"],
    "ADJUST": [".....#.....", "....###....", ".....#.....", ".....#.....", ".#...#...#.", "###########", ".#...#...#.", ".....#.....", ".....#.....", "....###....", ".....#....."],
    "CLOSE":  ["##.......##", "#...###...#", "...#...#...", "...#...#...", "...#...#...", "....###....", ".....#.....", "..#######..", ".#.......#.", "#.........#", "##.......##"],
}
LABELS = {"A": "VIEW A", "B": "VIEW B", "TURN": "MY TURN", "OFF": "DISCONNECT"}

def key(name, on=False):
    k = Image.new("RGBA", (15 * PX, 19 * PX), KEY + (240,))
    d = ImageDraw.Draw(k)
    d.rectangle([0, 0, 15 * PX - 1, 19 * PX - 1], outline=LINE, width=1)
    for y, row in enumerate(ICONS[name]):
        for x, c in enumerate(row):
            if c == "#":
                X, Y = (2 + x) * PX, (2 + y) * PX
                d.rectangle([X, Y, X + PX - 1, Y + PX - 1], fill=CHALK if on else (206, 203, 194))
    label = LABELS.get(name, name)
    ab.ptext(k, ((15 * PX - ab.pwidth(label, 1)) // 2, 14 * PX + 3), label, 1, CHALK if on else DIM)
    if on: d.rectangle([3 * PX, 19 * PX - 6, 12 * PX, 19 * PX - 4], fill=CORAL)
    return k

def atlas():
    im = Image.new("RGBA", (W, H), KEY + (0,))
    for r, (_, keys, on) in enumerate(ROWS):
        x0, y0 = (r // PER) * COL, (r % PER) * CH
        for i, n in enumerate(keys):
            k = key(n, n in on)
            im.paste(k, (x0 + i * CW + (CW - k.width) // 2, y0 + (CH - k.height) // 2))
    return im

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hud", "art", "take12_keys_1024.png")
    atlas().save(out)
    print("wrote", os.path.normpath(out))
