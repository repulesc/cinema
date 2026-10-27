#!/usr/bin/env python3
"""Take 12 8.0: the two textures of the strip (the Monitor look) and the tables screen.lsl reads.

  hud/art/take12_words_1024.png  every word in small caps, white on transparent, one 512 x 48 cell each
  hud/art/take12_marks_1024.png  the [12] disc, its rings (filming, the hold fill, amber), the dot, the box, the halo,
                                 the underline, the divider, the band's fade, the shape cells and the Connect cells

The script tints the white words per state (lit, dim, ink on the white box). The cell tables (where each word is and
how wide it is) are written into hud/src/screen.lsl between the "// <CELLS>" and "// </CELLS>" lines, so the art and
the script never disagree. Inter (SIL Open Font License) is drawn into the textures.

    python3 tools/art/make_strip.py           # writes both PNGs and the tables
    python3 tools/art/make_strip.py --check   # CI: fails if the tables in screen.lsl are stale
"""
import math, os, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ART = os.path.join(ROOT, "hud", "art")
SCREEN = os.path.join(ROOT, "hud", "src", "screen.lsl")
STRIP = os.path.join(ROOT, "hud", "src", "strip.lsl")
FONT_DIRS = ["/usr/share/fonts/opentype/inter/", os.path.join(ROOT, "tools", "art", "fonts")]

W = 1024
CELL_W, CELL_H = 512, 48          # a word cell
PAD = 8                           # px of air left and right of a word, in the cell
SIZE = 23                         # px: small caps about 17 px tall in a 48 px cell (11.5 px on a 1080 px window at M)
TRACK = 0.14                      # letter spacing, em

WORDS = ["TRACKING", "PORTRAIT", "FIXED", "SCENIC",
         "CLOSE", "MEDIUM", "WIDE", "ME", "US",
         "SHOULDER", "FILM", "CLASSIC", "L", "R",
         "VIEW A", "VIEW B", "KEEP NEW", "FORGET SEAT", "UNDO", "LET GO", "TAKE BACK",
         "DRIFT", "NEAR", "ROOM", "FAR"]
SHAPES = ["1.66", "1.85", "2.00", "2.39", "FULL", "DIM"]
LINKS = ["ALONE"] + [str(i) for i in range(1, 10)] + ["SHARING", "THEIR FILM"]

GLASS = (17, 18, 22)
WHITE = (247, 246, 241)
AMBER = (255, 178, 52)


def font(name, px):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p): return ImageFont.truetype(p, px)
    raise SystemExit("font %s not found (Inter; on Debian: fonts-inter)" % name)


def spaced(draw, x, y, text, f, fill, track):
    """letter-spaced text from x, centred on y; returns its width"""
    sp = track * f.size
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill, anchor="lm")
        x += f.getlength(ch) + sp
    return x


def spaced_w(text, f, track):
    return sum(f.getlength(c) for c in text) + track * f.size * (len(text) - 1)


def ss(w, h, k=4):
    return Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)), k


def down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


# ---- words ------------------------------------------------------------------------------------------------------------
def words():
    sheet = Image.new("RGBA", (W, W), (255, 255, 255, 0))
    f = font("Inter-SemiBold.otf", SIZE * 4)
    table = []
    for i, w in enumerate(WORDS):
        cx, cy = (i % 2) * CELL_W, (i // 2) * CELL_H
        im, k = ss(CELL_W, CELL_H)
        d = ImageDraw.Draw(im)
        end = spaced(d, PAD * k, CELL_H * k / 2 + 1 * k, w, f, WHITE + (255,), TRACK)
        tw = int(math.ceil((end - PAD * k - TRACK * f.size) / k))
        sheet.alpha_composite(down(im, CELL_W, CELL_H), (cx, cy))
        table.append((w, cx, cy, tw + 2 * PAD))
    return sheet, table


# ---- marks ------------------------------------------------------------------------------------------------------------
def disc(numerals):
    im, k = ss(256, 256)
    d = ImageDraw.Draw(im)
    r = 124 * k
    c = 128 * k
    d.ellipse([c - r, c - r, c + r, c + r], fill=GLASS + (224,))
    d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255, 52), width=3 * k)
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - r * 0.8, c - r * 0.95, c + r * 0.8, c - r * 0.1], fill=(255, 255, 255, 9))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(12 * k)))
    f = font("InterDisplay-SemiBold.otf", 104 * k)
    d.text((c, c + 3 * k), "12", font=f, fill=numerals + (250,), anchor="mm")
    return down(im, 256, 256)


def ring(frac, colour=WHITE, track=True, width=7):
    im, k = ss(128, 128)
    d = ImageDraw.Draw(im)
    c, r = 64 * k, 60 * k
    box = [c - r, c - r, c + r, c + r]
    if track: d.arc(box, 0, 360, fill=(255, 255, 255, 50), width=width * k)
    if frac >= 1.0: d.ellipse(box, outline=colour + (245,), width=width * k)
    elif frac > 0: d.arc(box, -90, -90 + 360 * frac, fill=colour + (250,), width=width * k)
    return down(im, 128, 128)


def dot():
    im, k = ss(64, 64)
    d = ImageDraw.Draw(im)
    c = 32 * k
    d.ellipse([c - 26 * k, c - 26 * k, c + 26 * k, c + 26 * k], fill=GLASS + (255,))
    d.ellipse([c - 17 * k, c - 17 * k, c + 17 * k, c + 17 * k], fill=WHITE + (255,))
    return down(im, 64, 64)


def rrect(w, h, r, fill=None, outline=None, width=1):
    im, k = ss(w, h)
    ImageDraw.Draw(im).rounded_rectangle([2 * k, 2 * k, (w - 2) * k - 1, (h - 2) * k - 1], radius=r * k, fill=fill,
                                         outline=outline, width=width * k)
    return down(im, w, h)


def band(w, h, solid=0.41):
    im = Image.new("RGBA", (w, h), (4, 4, 6, 0))
    px = im.load()
    for y in range(h):
        t = y / (h - 1)
        a = 218 if t <= solid else int(218 * 0.55 * (1 - (t - solid) / (1 - solid)) ** 2)
        for x in range(w): px[x, y] = (4, 4, 6, a)
    return im


def rings_icon(d, x, y, k, fill=None):
    for dx in (-7.2, 7.2):
        b = [(x + dx - 11.2) * k, (y - 11.2) * k, (x + dx + 11.2) * k, (y + 11.2) * k]
        if fill: d.ellipse(b, fill=fill)
    for dx in (-7.2, 7.2):
        b = [(x + dx - 11.2) * k, (y - 11.2) * k, (x + dx + 11.2) * k, (y + 11.2) * k]
        d.ellipse(b, outline=WHITE + (255,), width=int(2.6 * k))


def cells(kind):
    """the shape or link cells (256 x 48): [(name, image, content width)]"""
    f = font("Inter-SemiBold.otf", SIZE * 4)
    out = []
    names = SHAPES if kind == "shape" else LINKS
    for n in names:
        im, k = ss(256, CELL_H)
        d = ImageDraw.Draw(im)
        if kind == "shape":
            x0, y0, x1, y1 = PAD, 15, PAD + 32, 33
            d.rounded_rectangle([x0 * k, y0 * k, x1 * k, y1 * k], radius=3 * k, outline=WHITE + (255,), width=int(2.4 * k))
            if n not in ("FULL", "DIM"):
                d.rounded_rectangle([x0 * k, y0 * k, x1 * k, (y0 + 5) * k], radius=2 * k, fill=WHITE + (255,))
                d.rounded_rectangle([x0 * k, (y1 - 5) * k, x1 * k, y1 * k], radius=2 * k, fill=WHITE + (255,))
            end = x1 + 2
            if n != "DIM": end = spaced(d, (x1 + 14) * k, CELL_H * k / 2 + k, n, f, WHITE + (255,), 0.08) / k
        else:
            rings_icon(d, PAD + 19, CELL_H / 2, k, fill=(WHITE + (110,)) if n == "SHARING" else None)
            end = PAD + 41
            if n != "ALONE": end = spaced(d, (PAD + 52) * k, CELL_H * k / 2 + k, n, f, WHITE + (255,), TRACK) / k
        out.append((n, down(im, 256, CELL_H), int(math.ceil(end)) + PAD))
    return out


def marks():
    sheet = Image.new("RGBA", (W, W), (255, 255, 255, 0))
    table = []
    def put(name, im, x, y, cw=None):
        sheet.alpha_composite(im, (x, y))
        table.append((name, x, y, im.width, im.height, cw if cw is not None else im.width))
    put("disc", disc(WHITE), 0, 0)
    put("discamber", disc(AMBER), 256, 0)
    put("dot", dot(), 512, 0)
    put("box", rrect(256, 64, 12, fill=WHITE + (255,)), 576, 0)
    put("halo", rrect(256, 64, 12, outline=WHITE + (255,), width=3), 576, 64)
    line = Image.new("RGBA", (192, 32), (255, 255, 255, 0))
    ImageDraw.Draw(line).rectangle([0, 13, 191, 18], fill=WHITE + (255,))
    put("under", line, 832, 0)
    sep = Image.new("RGBA", (32, 64), (255, 255, 255, 0))
    ImageDraw.Draw(sep).rectangle([14, 0, 17, 63], fill=(255, 255, 255, 230))
    put("sep", sep, 832, 32)
    put("band", band(64, 192), 896, 64)
    frames = [ring(1.0, track=False, width=5)] + [ring(i / 8.0) for i in range(1, 9)] + [ring(1.0, AMBER, track=False)]
    for i, im in enumerate(frames):
        put("ring%d" % i, im, (i % 8) * 128, 256 + (i // 8) * 128)
    for i, (n, im, cw) in enumerate(cells("shape")):
        put("shape" + n, im, (i % 4) * 256, 512 + (i // 4) * CELL_H, cw)
    for i, (n, im, cw) in enumerate(cells("link")):
        put("link" + n, im, (i % 4) * 256, 512 + 2 * CELL_H + (i // 4) * CELL_H, cw)
    return sheet, table


SCREEN_MARKS = ("disc", "discamber", "dot", "under") + tuple("ring%d" % i for i in range(10))   # the [12] (screen.lsl)


def lsl_tables(wt, mt):
    """the cell tables, as strings ("~name|x|y|...~": a string costs far less script memory than a list). strip.lsl
    gets every word and the marks the strip uses; screen.lsl only the [12]'s marks (8.0.2: each script carries only
    what it draws)"""
    w = "~" + "~".join("%s|%d|%d|%d" % r for r in wt) + "~"
    ms = "~" + "~".join("%s|%d|%d|%d|%d|%d" % r for r in mt if r[0] not in SCREEN_MARKS or r[0] == "under") + "~"
    mk = "~" + "~".join("%s|%d|%d|%d|%d|%d" % r for r in mt if r[0] in SCREEN_MARKS) + "~"
    strip = "\n".join(["// <CELLS> (generated by tools/art/make_strip.py: do not edit)",
                       "// WORDS: ~name|x|y|width px~ (cells 512 x 48 on take12_words); MARKS: ~name|x|y|w|h|content width~",
                       _split("string WORDS = ", w), _split("string MARKS = ", ms), "// </CELLS>"])
    screen = "\n".join(["// <MARKS> (generated by tools/art/make_strip.py: do not edit)",
                        "// MARKS: ~name|x|y|w|h|content width~ on take12_marks", _split("string MARKS = ", mk), "// </MARKS>"])
    return strip, screen


def _split(head, s):
    """one string constant (LSL allows no expression in a global's initialiser, so one long line)"""
    return head + '"' + s + '"' + ";"


def _wrap(line, n=118):
    """long LSL lines broken after commas, continued with 4 spaces"""
    if len(line) <= n: return line
    out, cur = [], ""
    for part in re.split(r"(?<=,) ", line):
        if len(cur) + len(part) + 1 > n and cur:
            out.append(cur)
            cur = "    " + part
        else:
            cur = (cur + " " + part) if cur else part
    out.append(cur)
    return "\n".join(out)


def splice(src, tables, tag="CELLS"):
    a = src.index("// <%s>" % tag)
    b = src.index("// </%s>" % tag) + len("// </%s>" % tag)
    return src[:a] + tables + src[b:]


if __name__ == "__main__":
    ws, wt = words()
    ms, mt = marks()
    strip_t, screen_t = lsl_tables(wt, mt)
    targets = [(STRIP, strip_t, "CELLS"), (SCREEN, screen_t, "MARKS")]
    stale = []
    for path, t, tag in targets:
        src = open(path, encoding="utf-8").read()
        new = splice(src, t, tag)
        if new != src:
            stale.append(os.path.basename(path))
            if "--check" not in sys.argv: open(path, "w", encoding="utf-8").write(new)
    if "--check" in sys.argv:
        if stale: raise SystemExit("make_strip: the tables in %s are stale; run python3 tools/art/make_strip.py" % ", ".join(stale))
        print("make_strip: the tables in strip.lsl and screen.lsl match the art")
        sys.exit(0)
    os.makedirs(ART, exist_ok=True)
    ws.save(os.path.join(ART, "take12_words_1024.png"))
    ms.save(os.path.join(ART, "take12_marks_1024.png"))
    print("wrote hud/art/take12_words_1024.png, hud/art/take12_marks_1024.png and the tables in strip.lsl and screen.lsl")
