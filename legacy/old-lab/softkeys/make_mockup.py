#!/usr/bin/env python3
"""Soft keys, a concept (not in the HUD): draws legacy/old-lab/softkeys/softkeys_mockup.png.

The clapper alone at rest; in a few busy moments, up to five quiet keys beside it. Thin 1 px line icons in chalk on a
near-black key, a small-caps label in the HUD's pixel font, the key in use marked by a coral underline.

    python3 legacy/old-lab/softkeys/make_mockup.py
"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                                              # make_icon.py (the 7.x clapper) lives here now
import make_icon as icon
import make_adboard as ab

KEY, LINE, CHALK, DIM, CORAL = (20, 21, 26), (52, 55, 68), (236, 233, 224), (150, 154, 170), (255, 90, 95)
PX = 4                      # one icon pixel = 4 screen pixels in the mockup (the key is about 40 px on a HUD)

# 11 x 11 line icons: '#' a 1 px line, nothing filled, no figures
ICONS = {
    "NEXT":   ["...........", "...........", "..#...#....", "...#...#...", "....#...#..", ".....#...#.", "....#...#..", "...#...#...", "..#...#....", "...........", "..........."],
    "INVITE": ["...........", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".#########.", ".....#.....", ".....#.....", ".....#.....", ".....#.....", "..........."],
    "END":    ["...........", ".#########.", ".#.......#.", ".#.......#.", ".#.......#.", ".#.......#.", ".#.......#.", ".#.......#.", ".#.......#.", ".#########.", "..........."],
    "SAVE":   ["...........", ".....#.....", ".....#.....", ".....#.....", "...#.#.#...", "....###....", ".....#.....", ".#.......#.", ".#.......#.", ".#########.", "..........."],
    "A":      [".#########.", ".#.......#.", ".#...#...#.", ".#..#.#..#.", ".#.#...#.#.", ".#.#####.#.", ".#.#...#.#.", ".#.#...#.#.", ".#.......#.", ".#########.", "..........."],
    "B":      [".#########.", ".#.......#.", ".#.####..#.", ".#.#...#.#.", ".#.####..#.", ".#.#...#.#.", ".#.#...#.#.", ".#.####..#.", ".#.......#.", ".#########.", "..........."],
    "STOP":   ["...........", "...........", "..#######..", "..#.....#..", "..#.....#..", "..#.....#..", "..#.....#..", "..#.....#..", "..#######..", "...........", "..........."],
    # Still: the frame edge, and how much of a standing subject (a line, its head a point) it takes in
    "FULL":   ["##.......##", "#....#....#", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".....#.....", ".....#.....", "#....#....#", "##.......##"],
    "HALF":   ["##.......##", "#.........#", ".....#.....", "....###....", "....#.#....", ".....#.....", ".....#.....", ".....#.....", ".....#.....", "#....#....#", "##...#...##"],
    "CLOSE":  ["##.......##", "#...###...#", "...#...#...", "...#...#...", "...#...#...", "....###....", ".....#.....", "..#######..", ".#.......#.", "#.........#", "##.......##"],
}
LABELS = {"A": "VIEW A", "B": "VIEW B"}

def key(name, on=False):
    w, h = 15, 19
    k = Image.new("RGBA", (w * PX, h * PX), KEY + (238,))
    d = ImageDraw.Draw(k)
    d.rectangle([0, 0, w * PX - 1, h * PX - 1], outline=LINE, width=1)
    for y, row in enumerate(ICONS[name]):
        for x, c in enumerate(row):
            if c == "#":
                X, Y = (2 + x) * PX, (2 + y) * PX
                d.rectangle([X, Y, X + PX - 1, Y + PX - 1], fill=CHALK if on else (206, 203, 194))
    label = LABELS.get(name, name)
    ab.ptext(k, ((w * PX - ab.pwidth(label, 1)) // 2, 14 * PX + 2), label, 1, CHALK if on else DIM)
    if on: d.rectangle([3 * PX, h * PX - 5, (w - 3) * PX, h * PX - 3], fill=CORAL)
    return k

def row(names, on=None, title=""):
    gap, kw, bw = 5, 15 * PX, 18 * PX
    w = len(names) * (kw + gap) + bw + 24
    im = Image.new("RGBA", (w, 19 * PX + 34), (0, 0, 0, 0))
    x = 8
    for n in names:
        im.alpha_composite(key(n, n == on), (x, 28)); x += kw + gap
    im.alpha_composite(icon.frame_img(icon.draw(True, "rec")).resize((bw, bw), Image.NEAREST), (x + 6, 28))
    if title: ImageDraw.Draw(im).text((w - 6, 13), title, font=ab.font(13), fill=CHALK, anchor="rm")
    return im

def main():
    rows = [(row([]), "At rest: the clapper alone, as now"),
            (row(["NEXT", "INVITE", "END"], title="● LIVE · 3 watching"), "Live, as the director: no dialog over the shot"),
            (row(["SAVE", "A", "B", "STOP"], on="A", title="✥ Freehand · held · 85 mm"), "Freehand: the tripod loop, one click each"),
            (row(["FULL", "HALF", "CLOSE"], on="HALF", title="□ Still · Half length · 85 mm ✓"), "Still: which framing is on, and the others")]
    W = max(max(r[0].width for r in rows) + 40, 480)
    H = len(rows) * 150 + 10
    bg = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(bg)
    for y in range(H): d.line([(0, y), (W, y)], fill=(64 + y // 14, 100 + y // 16, 150 + y // 22, 255))
    y = 10
    for im, t in rows:
        d.text((18, y), t, font=ab.font(15), fill=(255, 255, 255, 255))
        bg.alpha_composite(im, (W - im.width - 10, y + 22)); y += 150
    out = os.path.join(HERE, "softkeys_mockup.png")
    bg.convert("RGB").save(out)
    print("wrote", os.path.relpath(out))

if __name__ == "__main__":
    main()
