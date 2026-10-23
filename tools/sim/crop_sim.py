# Frame (6.2.0, crop.lsl): four dimmed bars cut your screen down to a picture format. Ported here: for every format on
# every common window, the picture left between the bars has exactly the format's ratio, is centred and as large as the
# window allows, and the bars tile the rest of the screen with no gap and no overlap. Also: the screen centre seen from
# each HUD point, the menu fits a dialog, and ui / picker / the free build are wired as described.
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
crop, ui, picker, build = rd("hud", "src", "crop.lsl"), rd("hud", "src", "ui.lsl"), rd("hud", "src", "picker.lsl"), rd("tools", "build_scenery.py")
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

NAMES = re.findall(r'"([^"]+)"', re.search(r"list    NAMES  = \[(.*?)\];", crop).group(1))
RATIOS = [float(x) for x in re.search(r"list    RATIOS = \[(.*?)\];", crop).group(1).split(",")]
check(NAMES == ["3:2", "4:5", "1:1", "4:3", "2.39:1", "9:16"], f"formats: {NAMES}")
for n, r in zip(NAMES, RATIOS):
    a, b = (float(x) for x in n.split(":"))
    check(abs(a / b - r) < 1e-5, f"{n} is {r}")

# ---- the port of cut(): bars as (y, z, w, h) around the screen centre, +Y to the left ---------------------------
def cut(r, a):
    sw = th = 0.0
    if 0.0 < r < a: sw = (a - r) * 0.5
    elif r > a: th = (1.0 - a / r) * 0.5
    return [((r + sw) * 0.5, 0.0, sw, 1.0), (-(r + sw) * 0.5, 0.0, sw, 1.0), (0.0, 0.5 - th * 0.5, a, th), (0.0, th * 0.5 - 0.5, a, th)]
for line in ("if (r > 0.0 && r < a) sw = (a - r) * 0.5;", "else if (r > a) th = (1.0 - a / r) * 0.5;",
             "bar(llList2Integer(gBars, 0), (r + sw) * 0.5, 0.0, sw, 1.0);", "bar(llList2Integer(gBars, 1), -(r + sw) * 0.5, 0.0, sw, 1.0);",
             "bar(llList2Integer(gBars, 2), 0.0, 0.5 - th * 0.5, a, th);", "bar(llList2Integer(gBars, 3), 0.0, th * 0.5 - 0.5, a, th);"):
    check(line in crop, f"crop.lsl: cut() no longer reads '{line}'")

def rect(y, z, w, h): return (y - w / 2, y + w / 2, z - h / 2, z + h / 2)
def area(q): return max(0.0, q[1] - q[0]) * max(0.0, q[3] - q[2])
def inter(p, q): return area((max(p[0], q[0]), min(p[1], q[1]), max(p[2], q[2]), min(p[3], q[3])))
WINDOWS = {"16:9": 16 / 9, "16:10": 1.6, "21:9": 64 / 27, "4:3": 4 / 3, "5:4": 1.25}
E = 1e-9
for wn, a in WINDOWS.items():
    screen = (-a / 2, a / 2, -0.5, 0.5)
    for n, r in zip(NAMES, RATIOS):
        bars = [rect(*b) for b in cut(r, a) if b[2] > 0 and b[3] > 0]
        # the picture: the screen minus the bars
        side = [q for q in bars if q[3] - q[2] >= 1 - E]          # full-height bars: left (+Y) and right
        flat = [q for q in bars if q[1] - q[0] >= a - E]          # full-width bars: top and bottom
        pic = (max([q[1] for q in side if q[1] <= E] + [-a / 2]), min([q[0] for q in side if q[0] >= -E] + [a / 2]),
               max([q[3] for q in flat if q[3] <= E] + [-0.5]), min([q[2] for q in flat if q[2] >= -E] + [0.5]))
        w, h = pic[1] - pic[0], pic[3] - pic[2]
        check(abs(w / h - r) < 1e-6 or (abs(r - a) < 1e-6), f"{wn} {n}: the picture is {w / h:.4f}, not {r:.4f}")
        check(abs(pic[0] + pic[1]) < 1e-9 and abs(pic[2] + pic[3]) < 1e-9, f"{wn} {n}: the picture is not centred")
        check(abs(w - min(a, r)) < 1e-9 or abs(h - 1.0) < 1e-9, f"{wn} {n}: the picture is not as large as the window allows")
        check(abs(h - min(1.0, a / r)) < 1e-9, f"{wn} {n}: the picture height {h:.4f}")
        for q in bars:
            check(q[0] >= screen[0] - E and q[1] <= screen[1] + E and q[2] >= screen[2] - E and q[3] <= screen[3] + E, f"{wn} {n}: a bar leaves the screen")
            check(inter(q, pic) < 1e-12, f"{wn} {n}: a bar covers the picture")
        for i in range(len(bars)):
            for j in range(i + 1, len(bars)): check(inter(bars[i], bars[j]) < 1e-12, f"{wn} {n}: two bars overlap (double dark)")
        check(abs(sum(area(q) for q in bars) + area(pic) - area(screen)) < 1e-9, f"{wn} {n}: the bars and the picture do not tile the screen")
    # Off: no bar shows
    check(all(b[2] == 0 or b[3] == 0 for b in cut(0.0, a)), f"{wn}: Off still shows a bar")

# ---- the screen centre from each HUD point: origin + centre() lands on the middle of the screen --------------------
POINTS = ["ATTACH_HUD_TOP_RIGHT", "ATTACH_HUD_TOP_CENTER", "ATTACH_HUD_TOP_LEFT", "ATTACH_HUD_BOTTOM_LEFT", "ATTACH_HUD_BOTTOM", "ATTACH_HUD_BOTTOM_RIGHT"]
check(all(p in crop for p in POINTS), "crop.lsl: the HUD point table")
ys = [float(x) for x in re.search(r"llList2Float\(\[([-0-9., ]+)\], p\);\n    float z", crop).group(1).split(",")]
zs = [float(x) for x in re.search(r"float z = 0\.5 \* llList2Float\(\[([-0-9., ]+)\], p\);", crop).group(1).split(",")]
a = 16 / 9
ORIGIN = {"ATTACH_HUD_TOP_RIGHT": (-a / 2, 0.5), "ATTACH_HUD_TOP_CENTER": (0, 0.5), "ATTACH_HUD_TOP_LEFT": (a / 2, 0.5),
          "ATTACH_HUD_BOTTOM_LEFT": (a / 2, -0.5), "ATTACH_HUD_BOTTOM": (0, -0.5), "ATTACH_HUD_BOTTOM_RIGHT": (-a / 2, -0.5)}   # +Y left
for p, y, z in zip(POINTS, ys, zs):
    oy, oz = ORIGIN[p]
    check(abs(oy + a * 0.5 * y) < 1e-9 and abs(oz + 0.5 * z) < 1e-9, f"{p}: centre() misses the middle of the screen")
check("if (p < 0) return ZERO_VECTOR;" in crop, "Center and Center 2 are the screen centre itself")
check("(at - p) / r" in crop and "ZERO_ROTATION / r" in crop and "<p.x + gSX * DEPTH, y * gSY, z>" in crop,
      "bars must be placed through the root's own position and rotation, square to the screen, behind the button")
check('if ((m == "take 12 frame") == (n == 0) && llSubStringIndex(m, "keys") < 0)' in crop and "gBars += [i];" in crop,
      "the bars: the boxes named as bars first, then the lowest other children, never a keys strip (6.6)")
check("integer gSX = 1;" in crop, "the bars must sit behind the button: +X points into the screen (6.5.0 fix)")
check("llGetCameraAspect()" in crop and "PERMISSION_TRACK_CAMERA" in crop, "the window is measured")
check('set("aspect", (string)a);' in crop and 'llMessageLinked(LINK_SET, CFG_CHANGED, "aspect", "");' in crop, "the cameras get your window")

# ---- the menu fits a dialog; ui, picker and the free build ------------------------------------------------------
labels = ["Off", " ", "Back", "‹ Back", "↩ Back"] + ["✓ " + n for n in NAMES] + NAMES
check(all(len(l.encode()) <= 24 for l in labels) and 3 + len(NAMES) <= 12, "the Frame menu must fit llDialog")
check("llDetectedLinkNumber(0) > 1) return;" in ui[ui.index("touch_start"):ui.index("touch_end")] and
      "llDetectedLinkNumber(0) > 1) return;" in ui[ui.index("touch_end"):], "ui must ignore touches on the bars")
check('"crop"' in re.search(r'b = \["scenery".*?\];', ui).group(0) and '|| id == "crop")' in ui and "~crop|" in ui, "ui: Frame on the main page, routed to crop")
check('else if (c == "crop") llMessageLinked(LINK_SET, CMD, "crop|" + v, "");' in picker, "picker: /77 crop")
check('"frame", "free", "crop", "share"' in build and "crop.lsl is not part of it" in build, "the free build leaves Frame out")
print(f"frame: {len(NAMES)} formats x {len(WINDOWS)} windows, the picture exact and centred, bars tile the screen; {len(POINTS)} HUD points")
print("frame checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
