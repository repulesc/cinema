#!/usr/bin/env python3
"""Take 12 8.8.0: the guide card, one texture (hud/art/take12_guide_1024.png, 1024 x 512).

The card shows the strip as it is (the shots from the left, the frame, the [12] in the middle, Connect, the running
shot's options, the shutter), a numbered dot under each key, and one line for each. It is drawn here, whole, so it
reads the same on any window and wherever the strip sits; screen.lsl only shows it (after the setup, Help › Guide,
/12 guide) and a tap on it closes it. Inter (SIL Open Font License), as the strip's own textures.

    python3 tools/art/make_guide.py           # writes the PNG
    python3 tools/art/make_guide.py --check   # CI: fails if the texts do not fit the card
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_strip import ART, WHITE, font, spaced, spaced_w, shutter, orbit, disc, ring, rings_icon

W, H = 1024, 512
K = 4                                   # drawn 4x, then scaled down
INK = (8, 8, 10)

KEYS = [("orbit", "AUTO", "The camera directs itself as you walk, stop, sit or meet someone. Tap it to let it direct again."),
        ("shots", "THE SHOTS", "Tap one to direct. Tracking follows you, Portrait frames you standing, Fixed keeps your own framing, Scenic shows the place."),
        ("frame", "THE FRAME", "The film's shape, the same in every shot. Tap it to choose."),
        ("12", "THE [12]", "Your menu and your switch: touch it three ways, below."),
        ("link", "CONNECT", "Share films with friends near you."),
        ("opts", "THE OPTIONS", "The running shot's choices. Tap one to change it."),
        ("shut", "THE SHUTTER", "Holds the moment in your photo frame. Take your snapshot, then tap it again.")]
KEYS_LAB = [KEYS[0],                     # the Take 12 Lab (lab/): its Quiet page
            ("shot", "THE SHOT", "What is filming now. Tap it for every shot and its choices."),
            ("fold", "›  AND  ‹", "Opens every shot and its choices; ‹, in the same place, folds them away."),
            KEYS[2], KEYS[3], KEYS[4], KEYS[6]]
GESTURES = [("tap", "TAP", "the menu"), ("double", "DOUBLE-TAP", "show or hide the strip"),
            ("hold", "HOLD", "everything off, and back")]
FOOT = "Tap the card to close it.   Help › Guide shows it again."
SHOTS = ["TRACKING", "PORTRAIT", "FIXED", "SCENIC"]
OPTS = ["SHOULDER", "FILM", "CLASSIC", "/", "L", "R"]
LIT = ("TRACKING", "FILM", "R")


def wrap(f, s, width):
    out, line = [], ""
    for wd in s.split(" "):
        t = (line + " " + wd) if line else wd
        if f.getlength(t) > width and line: out.append(line); line = wd
        else: line = t
    out.append(line)
    return out


def card(lab=False):
    keys = KEYS_LAB if lab else KEYS
    im = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3 * K, 3 * K, (W - 3) * K, (H - 3) * K], radius=18 * K, fill=INK + (236,))
    d.rounded_rectangle([3 * K, 3 * K, (W - 3) * K, (H - 3) * K], radius=18 * K, outline=(255, 255, 255, 34), width=2 * K)
    head = font("Inter-SemiBold.otf", 13 * K)
    spaced(d, 44 * K, (27 if lab else 38) * K, "TAKE 12 LAB  ·  THE QUIET STRIP" if lab else "TAKE 12  ·  THE STRIP", head, WHITE + (150,), 0.14)

    # ---- the strip, as it is (Tracking · Film · R), its band 40 px, the [12] in the middle ----------------------------
    by0, by1, cy = 62, 102, 82
    if lab: cy = 66                               # the lab's strip: on the screen's top edge (lab_strip)
    if not lab: d.rounded_rectangle([28 * K, by0 * K, (W - 28) * K, by1 * K], radius=6 * K, fill=(0, 0, 0, 255))
    wf = font("Inter-Medium.otf", int(12.5 * K))
    X = {}
    def word(x, t):
        lit = t in LIT
        end = spaced(d, x * K, cy * K, t, wf, WHITE + ((255,) if lit else (122,)), 0.14) / K
        if lit: d.rectangle([x * K, (cy + 10) * K, end * K, (cy + 11.4) * K], fill=WHITE + (242,))
        return end
    def paste(cell, cx, a=1.0, size=None, y=None):
        c = cell
        if size: c = c.resize((size[0] * K, size[1] * K), Image.LANCZOS)
        else: c = c.resize((c.width * K * 40 // 48, c.height * K * 40 // 48), Image.LANCZOS)
        if a < 1.0:
            al = c.getchannel("A").point(lambda v: int(v * a)); c.putalpha(al)
        im.alpha_composite(c, (int(cx * K - c.width / 2), int((y if y is not None else cy) * K - c.height / 2)))
    gap = 19
    if lab: return lab_strip(im, d, wf, word, paste, keys, gap)
    x = 52
    paste(orbit(False), x + 10, 0.65); X["orbit"] = x + 10; x += 20 + gap
    xs = x
    for s in SHOTS:
        x = word(x, s) + gap
    X["shots"] = (xs + x - gap) / 2
    shots_end = x - gap
    mid = W / 2
    paste(disc(WHITE), mid, size=(28, 28)); paste(ring(1.0, track=False, width=5), mid, 0.85, size=(32, 32)); X["12"] = mid
    # the frame key: the frame with its bars, then 2.39
    fx = mid - 86
    d.rounded_rectangle([fx * K, (cy - 6) * K, (fx + 22) * K, (cy + 6) * K], radius=2 * K, outline=WHITE + (218,), width=int(1.6 * K))
    d.rectangle([fx * K, (cy - 6) * K, (fx + 22) * K, (cy - 3) * K], fill=WHITE + (218,))
    d.rectangle([fx * K, (cy + 3) * K, (fx + 22) * K, (cy + 6) * K], fill=WHITE + (218,))
    spaced(d, (fx + 30) * K, cy * K, "2.39", wf, WHITE + (218,), 0.08)
    X["frame"] = fx + 26
    lk = ImageDraw.Draw(im)
    rk = Image.new("RGBA", (64 * K, 48 * K), (0, 0, 0, 0))
    rings_icon(ImageDraw.Draw(rk), 32, 24, K)
    paste(rk.resize((64, 48), Image.LANCZOS), mid + 48, 0.75); X["link"] = mid + 48
    xr = W - 52
    paste(shutter(False), xr - 10, 0.85); X["shut"] = xr - 10
    xo = xr - 20 - gap
    ends = []
    for o in reversed(OPTS):
        if o == "/":
            d.rectangle([(xo - 9) * K, (cy - 7) * K, (xo - 8) * K, (cy + 7) * K], fill=(255, 255, 255, 76)); xo -= 18 + gap; continue
        w = spaced_w(o, wf, 0.14) / K
        xo -= w; word(xo, o); ends.append(xo); xo -= gap
    X["opts"] = (xo + gap + xr - 20 - gap) / 2
    if shots_end > fx - 16 or xo + gap < mid + 72:
        raise SystemExit("make_guide: the strip drawing does not fit the card")

    return finish(im, d, X, keys, paste)


def lab_strip(im, d, wf, word, paste, keys, gap):
    """the lab's Quiet page as it is on screen: a slice of the picture, the film's top bar across it (1.85: thinner than
    the strip, so the notch shows; at 2.39 the bar is taller and the notch is lost in it), and the notch hanging from
    the screen's edge, joined to the bar, as wide as its words. Square where it meets the bar, as in-world (two parts)"""
    st, sb = 46, 120                                  # the screen slice
    cy = st + 20                                      # the strip: 40 px from the screen's edge
    bar = st + 21                                     # 1.85's bar on a 16:9 window: 21 px
    mid = W / 2
    X = {}
    fx = mid - 86
    xf = fx - 26                                      # the fold key, left of the frame
    xr = xf - 10 - gap                                # the shot's name ends here
    tw = spaced_w("TRACKING", wf, 0.14) / K
    xo = xr - tw - gap - 10                           # the Orbit
    xs = mid + 48 + 24 + gap + 10                     # the shutter, beside Connect
    x0, x1 = xo - 10 - 26, xs + 10 + 26
    # the picture: a dusk, darkened, so the black reads against it
    pic = Image.new("RGBA", (1, sb - st), (0, 0, 0, 255))
    for yy in range(sb - st):
        t = yy / float(sb - st - 1)
        pic.putpixel((0, yy), (int(52 + 46 * t), int(40 + 24 * t), int(70 + 22 * t), 255))
    pic = pic.resize(((W - 56) * K, (sb - st) * K), Image.BILINEAR)
    m = Image.new("L", pic.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, pic.width - 1, pic.height - 1], radius=8 * K, fill=255)
    im.paste(pic, (28 * K, st * K), m)
    # the black: the bar across the picture, the notch hanging from the edge, one shape
    nl = Image.new("L", pic.size, 0)
    nd = ImageDraw.Draw(nl)
    nd.rectangle([0, 0, pic.width - 1, (bar - st) * K], fill=255)
    nd.rounded_rectangle([(x0 - 28) * K, -14 * K, (x1 - 28) * K, (cy + 20 - st) * K], radius=12 * K, fill=255)
    nl = Image.composite(nl, Image.new("L", pic.size, 0), m)
    im.paste(Image.new("RGBA", pic.size, (0, 0, 0, 255)), (28 * K, st * K), nl)
    paste(orbit(False), xo, 0.65); X["orbit"] = xo
    word(xr - tw, "TRACKING"); X["shot"] = xr - tw / 2
    d.line([((xf - 2) * K, (cy - 6) * K), ((xf + 3) * K, cy * K), ((xf - 2) * K, (cy + 6) * K)], fill=WHITE + (210,), width=int(2 * K), joint="curve")
    X["fold"] = xf
    d.rounded_rectangle([fx * K, (cy - 5) * K, (fx + 22) * K, (cy + 5) * K], radius=2 * K, outline=WHITE + (218,), width=int(1.6 * K))
    d.rectangle([fx * K, (cy - 5) * K, (fx + 22) * K, (cy - 3) * K], fill=WHITE + (218,))
    d.rectangle([fx * K, (cy + 3) * K, (fx + 22) * K, (cy + 5) * K], fill=WHITE + (218,))
    spaced(d, (fx + 30) * K, cy * K, "1.85", wf, WHITE + (218,), 0.08)
    X["frame"] = fx + 26
    paste(disc(WHITE), mid, size=(28, 28)); paste(ring(1.0, track=False, width=5), mid, 0.85, size=(32, 32)); X["12"] = mid
    rk = Image.new("RGBA", (64 * K, 48 * K), (0, 0, 0, 0))
    rings_icon(ImageDraw.Draw(rk), 32, 24, K)
    paste(rk.resize((64, 48), Image.LANCZOS), mid + 48, 0.75); X["link"] = mid + 48
    paste(shutter(False), xs, 0.85); X["shut"] = xs
    if x0 < 40: raise SystemExit("make_guide: the lab's strip drawing does not fit the card")
    return finish(im, d, X, keys, paste, ny=sb + 15, y0=sb + 38)


def finish(im, d, X, keys, paste, ny=118, y0=150):
    # ---- the numbers under the keys, then the list ---------------------------------------------------------------------
    nf = font("Inter-SemiBold.otf", 11 * K)
    def num(cx, ccy, i):
        d.ellipse([(cx - 8.5) * K, (ccy - 8.5) * K, (cx + 8.5) * K, (ccy + 8.5) * K], fill=WHITE + (238,))
        d.text((cx * K, (ccy + 0.5) * K), str(i), font=nf, fill=INK + (255,), anchor="mm")
    for i, (k, _, _) in enumerate(keys):
        num(X[k], ny, i + 1)
    tf = font("Inter-SemiBold.otf", int(14.5 * K))
    bf = font("Inter-Regular.otf", 15 * K)
    bx, bw = 214, W - 214 - 48
    rows = [wrap(bf, b, bw * K) for _, _, b in keys]
    lines = sum(len(r) for r in rows)
    y = y0
    step, lead = 32, 20                           # a row, a second line
    if y + len(rows) * step + (lines - len(rows)) * lead > H - 112:
        raise SystemExit("make_guide: the list does not fit the card (%d lines)" % lines)
    for i, ((_, t, _), r) in enumerate(zip(keys, rows)):
        num(56, y + 8, i + 1)
        spaced(d, 76 * K, (y + 8) * K, t, tf, WHITE + (255,), 0.06)
        for j, ln in enumerate(r):
            d.text((bx * K, (y + 8 + j * lead) * K), ln, font=bf, fill=WHITE + (196,), anchor="lm")
        y += step + (len(r) - 1) * lead
    # ---- the [12]'s three touches: one grid, one size. The same disc in each, its rings in one 1.5 px stroke: one ring
    # (a tap), two (a double-tap), the ring filling (a hold). The divider, the row and the footer evenly spaced -------
    fy = H - 26                                   # the footer
    lc = y - step + 8                             # the list's last line
    g = (fy - lc - 8 - 2 * 17.6 - 7) / 3.0        # one gap, seen: list to divider, divider to the touches, them to the footer
    dy = lc + 8 + g                               # the divider
    gy = dy + g + 17.6                            # the touches' row
    if gy + 18 > fy - 14: raise SystemExit("make_guide: the touches do not fit under the list")
    d.line([44 * K, dy * K, (W - 44) * K, dy * K], fill=(255, 255, 255, 30), width=K)
    gt = font("Inter-SemiBold.otf", int(13.5 * K))
    sw = 1.5 * K
    for i, (kind, t, b) in enumerate(GESTURES):
        x0 = 44 + i * (W - 88) / 3.0              # three equal columns over the list's width
        c = x0 + 17
        paste(disc(WHITE), c, size=(24, 24), y=gy)
        box = lambda r_: [(c - r_) * K, (gy - r_) * K, (c + r_) * K, (gy + r_) * K]
        if kind == "tap":
            d.ellipse(box(16.5), outline=WHITE + (170,), width=int(sw))
        elif kind == "double":
            d.ellipse(box(14.8), outline=WHITE + (190,), width=int(sw))
            d.ellipse(box(17.6), outline=WHITE + (110,), width=int(sw))
        else:
            d.ellipse(box(16.5), outline=WHITE + (50,), width=int(sw))
            d.arc(box(16.5), -90, -90 + 360 * 0.62, fill=WHITE + (245,), width=int(2.6 * K))   # the fill reads at a glance
        spaced(d, (c + 30) * K, (gy - 9) * K, t, gt, WHITE + (255,), 0.08)
        d.text(((c + 30) * K, (gy + 10) * K), b, font=bf, fill=WHITE + (196,), anchor="lm")
    ff = font("Inter-Regular.otf", 13 * K)
    d.text((W / 2 * K, fy * K), FOOT, font=ff, fill=WHITE + (138,), anchor="mm")
    return im.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    im, lab = card(), card(lab=True)              # raises if anything does not fit
    if "--check" in sys.argv:
        print("make_guide: the guide cards' texts fit (the product's and the lab's)")
        sys.exit(0)
    os.makedirs(ART, exist_ok=True)
    im.save(os.path.join(ART, "take12_guide_1024.png"))
    LART = os.path.join(os.path.dirname(ART), "..", "lab", "art")
    os.makedirs(LART, exist_ok=True)
    lab.save(os.path.join(LART, "take12_guide_1024.png"))
    print("wrote hud/art/take12_guide_1024.png and lab/art/take12_guide_1024.png")
