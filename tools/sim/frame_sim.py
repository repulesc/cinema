# Frame: the framing maths of frame.lsl, checked. Three framings (Full length, Half length, Close) for you
# alone and for you with the people next to you (mixed heights), over avatar heights 1.55-2.35 m and viewer zooms
# from 21 mm (the default) to 105 mm. The script's tables must match the ones tested here.
# (The fuller 4.5.0 version and its sim live in lab/frame-full-4.5.0/.)
import math, os, random, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
LSL = open(os.path.join(R, "hud", "src", "frame.lsl")).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

FEAT = ["top", "eyes", "shoulders", "chest", "belt", "midthigh", "feet"]
BODY = dict(top=1.0, eyes=0.935, shoulders=0.82, chest=0.72, belt=0.56, midthigh=0.38, feet=0.0)
PHI_Y, DMIN, TOP_MAX, FIT, MARGIN = 0.236, 1.2, 0.9, 1.6, 1.3      # 6.6: the golden line (was the third)
NAMES = ["Full length", "Half length", "Close"]
# you: camera height, degrees round, across, (f1, y1), (f2, y2)
PORT = [(0.50, 15, 0.0, ("top", 0.80), ("feet", -0.84)),         # 6.6: 10 % air above the head, 8 % below the feet
        (0.935, 30, 0.236, ("eyes", PHI_Y), ("belt", -1.0)),        # eyes on the golden line, you on a golden line across
        (0.98, 25, 0.2, ("eyes", PHI_Y), ("chest", -1.0))]
GRP = [(0.60, ("top", 0.80), ("feet", -0.84)),
       (0.80, ("eyes", PHI_Y), ("midthigh", -1.0)),
       (0.935, ("eyes", PHI_Y), ("belt", -1.0))]
pct = lambda y: 100 * (1 - y) / 2                            # screen y (-1..1) as % from the top

def fov_of_mm(mm): return 2 * math.atan(12.0 / mm)
def solve(z1, y1, z2, y2, zc, fov):
    t = math.tan(fov / 2)
    want = math.atan(y1 * t) - math.atan(y2 * t)
    span = lambda D: math.atan((z1 - zc) / D) - math.atan((z2 - zc) / D)
    lo, hi = 0.05, 400.0
    if span(hi) > want: return None
    for _ in range(28):                                       # as many rounds as the script
        m = (lo + hi) / 2
        if span(m) > want: lo = m
        else: hi = m
    D = (lo + hi) / 2
    return D, math.atan(y1 * t) - math.atan((z1 - zc) / D)
def tilt_for(z, y, zc, D, fov): return math.atan(y * math.tan(fov / 2)) - math.atan((z - zc) / D)
def y_of(z, zc, D, phi, fov): return math.tan(math.atan((z - zc) / D) + phi) / math.tan(fov / 2)

# ---- the script must carry these tables and constants ----------------------------------------------------------
def lsl_list(name):
    body = re.search(r"list\s+" + name + r"\s*=\s*\[(.*?)\];", LSL, re.S).group(1)
    return [t.strip('"') if t.startswith('"') else float(t) for t in re.findall(r'"[^"]*"|-?\d+(?:\.\d+)?', re.sub(r"//[^\n]*", "", body))]
check([round(BODY[f], 4) for f in FEAT] == lsl_list("BODY"), "BODY differs from the script")
check(lsl_list("NAMES") == NAMES, "NAMES differ from the script")
port = lsl_list("PORT")
for i, (cam, side, x, (f1, y1), (f2, y2)) in enumerate(PORT):
    want = [cam, side, x, FEAT.index(f1), round(y1, 4), FEAT.index(f2), round(y2, 4)]
    check([round(v, 4) for v in port[i * 7:(i + 1) * 7]] == want, f"PORT row {i} differs from the script")
grp = lsl_list("GRP")
for i, (cam, (f1, y1), (f2, y2)) in enumerate(GRP):
    want = [cam, FEAT.index(f1), round(y1, 4), FEAT.index(f2), round(y2, 4)]
    check([round(v, 4) for v in grp[i * 5:(i + 1) * 5]] == want, f"GRP row {i} differs from the script")
for c, v in (("DMIN", DMIN), ("TOPMAX", TOP_MAX), ("FIT", FIT), ("MARGIN", MARGIN)):
    m = re.search(r"float\s+" + c + r"\s*=\s*([\d.]+);", LSL)
    check(m and abs(float(m.group(1)) - v) < 1e-9, f"{c} differs from the script")

# ---- you alone --------------------------------------------------------------------------------------------------
HEIGHTS = (1.55, 1.75, 1.95, 2.15, 2.35)
LENSES = (21, 24, 35, 50, 85, 105)
loose = 0
for i, (cam, side, x, (f1, y1), (f2, y2)) in enumerate(PORT):
    for h in HEIGHTS:
        for mm in LENSES:
            fov = fov_of_mm(mm)
            zc = cam * h
            s = solve(BODY[f1] * h, y1, BODY[f2] * h, y2, zc, fov)
            check(s is not None, f"{NAMES[i]}: no solution at {h} m, {mm} mm")
            D, phi = s
            if D < DMIN:                                     # the script: from DMIN, a little looser
                loose += 1
                D = DMIN
                phi = tilt_for(BODY["eyes"] * h, PHI_Y, zc, D, fov) if i else tilt_for(BODY[f1] * h, y1, zc, D, fov)
                check(mm < 85, f"{NAMES[i]}: looser at {mm} mm, which should be long enough")
            else:
                check(abs(y_of(BODY[f1] * h, zc, D, phi, fov) - y1) < 0.01, f"{NAMES[i]}: {f1} misplaced")
                check(abs(y_of(BODY[f2] * h, zc, D, phi, fov) - y2) < 0.01, f"{NAMES[i]}: {f2} misplaced")
            check(y_of(h, zc, D, phi, fov) <= 0.97, f"{NAMES[i]}: head cut at {h} m, {mm} mm")
            if i: check(abs(pct(y_of(BODY["eyes"] * h, zc, D, phi, fov)) - 38.2) < 1.0, f"{NAMES[i]}: eyes off the golden line")
            elif D > DMIN:                                    # full length: air above the head and below the feet
                check(abs(pct(y_of(h, zc, D, phi, fov)) - 10.0) < 1.0, f"Full length: {pct(y_of(h, zc, D, phi, fov)):.1f} % above the head at {h} m, {mm} mm")
                check(abs(100 - pct(y_of(0.0, zc, D, phi, fov)) - 8.0) < 1.0, f"Full length: the feet at {h} m, {mm} mm")
            check(abs(math.degrees(phi)) <= 25, f"{NAMES[i]}: tilt {math.degrees(phi):.0f} degrees")

# ---- you with the people next to you ----------------------------------------------------------------------------
rng = random.Random(5)
for i, (cam, (f1, y1), (f2, y2)) in enumerate(GRP):
    for trial in range(200):
        n = rng.randint(2, 6)
        hs = [rng.uniform(1.6, 2.4) for _ in range(n)]
        fov = fov_of_mm(rng.choice(LENSES))
        top = max(hs); eyes = sum(BODY["eyes"] * h for h in hs) / n
        z1 = top if f1 == "top" else eyes
        z2 = min(BODY[f2] * h for h in hs)
        zc = cam * sum(hs) / n
        s = solve(z1, y1, z2, y2, zc, fov)
        check(s is not None, f"group {NAMES[i]}: no solution")
        D, phi = s
        D = max(D, DMIN)
        if y_of(top, zc, D, phi, fov) > TOP_MAX: phi = tilt_for(top, TOP_MAX, zc, D, fov)
        for h in hs:
            check(y_of(h, zc, D, phi, fov) <= 0.97, f"group {NAMES[i]}: a head is cut")
            check(y_of(BODY["eyes"] * h, zc, D, phi, fov) > -0.6, f"group {NAMES[i]}: someone's eyes near the bottom")

# ---- 5.9: the lens guide and Shift + A/D ------------------------------------------------------------------------
REC = [50, 85, 105]                                           # the classic lens per framing (35 mm equivalent)
check([int(v) for v in lsl_list("LENSES")] == REC, f"LENSES differ: {lsl_list('LENSES')}")
mm_of = lambda fov: round(12.0 / math.tan(fov / 2))
check(mm_of(math.radians(60)) == 21 and all(mm_of(fov_of_mm(m)) == m for m in REC), "the mm <-> FOV conversion")
check("(string)llRound(12.0 / llTan(gFov * 0.5))" in LSL and 'llMessageLinked(LINK_SET, STILL, llList2String(NAMES, gIdx) + "|" + llList2String(LENSES, gIdx)' in LSL,
      "frame: STILL must carry the framing, its lens and yours")
check(re.search(r"num == FOVMSG\)\s*\{[^}]*lens\(\);", LSL) is not None, "frame: the readout must follow the zoom at once")
check("llSetText" not in LSL, "frame must not write text itself (the status line shows Still)")
# at the recommended lens every framing keeps its exact lines (never pushed back to DMIN, so never looser)
for i, (cam, side, x, (f1, y1), (f2, y2)) in enumerate(PORT):
    for h in HEIGHTS:
        zc = cam * h; sol = solve(BODY[f1] * h, y1, BODY[f2] * h, y2, zc, fov_of_mm(REC[i]))
        check(sol is not None and sol[0] >= DMIN, f"{NAMES[i]} at {REC[i]} mm, {h} m: closer than DMIN")
# Shift + A/D: Second Life sends Shift + A/D as strafe (CONTROL_LEFT/RIGHT); plain A/D (ROT) still walks round you
for frag in ("if (gKeys & CONTROL_ROT_LEFT) gNAz += 3.0;", "if (gKeys & CONTROL_ROT_RIGHT) gNAz -= 3.0;",
             "if (gKeys & CONTROL_LEFT) gNX -= 0.02;", "if (gKeys & CONTROL_RIGHT) gNX += 0.02;", "x += gNX;",
             "float SLIDE  = 0.6;", "gNX = 0.0;", "llAtan2(gNX * t * gAsp, 1.0)", "llAtan2(x * t * gAsp, 1.0)"):
    check(frag in LSL, f"frame: missing {frag}")
# the view turns by atan(x * t * aspect): you land at screen x (+ = right) of the picture's half-width; 6.6: the
# picture's real aspect (the Frame format, or your window), so Half length's 0.236 is exactly the golden line
def load(a, r):                                               # frame.lsl load(): (gAsp, gFit, gTS)
    asp, fit, ts = a, min(a, FIT), 1.0
    if r > 0: asp, fit = r, r; ts = a / r if r > a else 1.0
    return asp, fit, ts
for a, r in ((16 / 9, 0.0), (1.6, 0.0), (16 / 9, 0.8), (16 / 9, 1.0), (16 / 9, 2.39), (1.6, 1.5)):
    asp, fit, ts = load(a, r)
    for mm in (21, 50, 105):
        t = math.tan(fov_of_mm(mm) / 2) * ts
        for x in (-0.6, -0.236, 0.0, 0.2, 0.6):
            ang = math.atan(x * t * asp)                      # the view direction turns left (+) by ang
            fwd, right = (math.cos(ang), math.sin(ang)), (math.sin(ang), -math.cos(ang))
            sx = (10 * right[0]) / (10 * fwd[0]) / (t * asp)  # you, 10 m straight ahead of the unturned view
            check(abs(sx - x) < 1e-9, f"slide {x} at {mm} mm lands at {sx:.3f}")
    check(abs(pct(-PORT[1][2]) - 61.8) < 0.1, "Half length: you are not on the golden line across")
for frag in ("float t = llTan(gFov * 0.5) * gTS;", "if (r > a) gTS = a / r;", "gAsp = r;", "gFit = r;", "if (a > FIT) gFit = FIT;",
             "float kk = t * gFit / MARGIN;", 'num == CFG_CHANGED && (str == "crop" || str == "aspect" || str == "all")', "if (gActive) shoot(FALSE);"):
    check(frag in LSL, f"frame: composing inside the Frame format: missing {frag}")
# a wider format (2.39:1 on 16:9) is a shorter picture: the framings still keep their lines inside it
for mm in (50, 85, 105):
    asp, fit, ts = load(16 / 9, 2.39)
    tp = math.tan(fov_of_mm(mm) / 2) * ts
    fovp = 2 * math.atan(tp)                                  # the picture as a lens
    for i, (cam, side, x, (f1, y1), (f2, y2)) in enumerate(PORT):
        h = 1.9; zc = cam * h
        sl = solve(BODY[f1] * h, y1, BODY[f2] * h, y2, zc, fovp)
        check(sl is not None, f"2.39:1 {NAMES[i]} at {mm} mm: no solution")
        if sl and sl[0] >= DMIN:
            check(abs(y_of(BODY[f1] * h, zc, sl[0], sl[1], fovp) - y1) < 0.01, f"2.39:1 {NAMES[i]} at {mm} mm: {f1} off its line")

print(f"Frame: 3 framings x {len(HEIGHTS)} heights x {len(LENSES)} zooms, and 600 mixed groups; "
      f"{loose} cases framed a little looser at a wide zoom (as intended)")
print("frame checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
