# Your lens, everywhere (6.0.0): every camera keeps its picture when you zoom, and the lens shapes the shot mix.
# The rule: the lens changes the perspective, never the size of the picture. On FOVMSG, Me / Us (people.lsl) and
# Only friends (friends.lsl) dolly the camera along its line to the focus by k = tan(old/2) / tan(new/2); Follow my
# lead (lens.lsl) scales your distance by the same k; core reports the zoom in every camera and lets people glide.
# Checked here: the size and the angle down are kept at every lens pair, the fallback when there is no room, the
# close-view chance per lens, and that the scripts carry exactly this.
import math, os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda n: open(os.path.join(R, "hud", "src", n)).read()
core, people, friends, lens, frame = rd("core.lsl"), rd("people.lsl"), rd("friends.lsl"), rd("lens.lsl"), rd("frame.lsl")
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

fov_of = lambda mm: 2 * math.atan(12.0 / mm)                     # 35 mm equivalent, 24 mm frame height
mm_of = lambda fov: 12.0 / math.tan(fov / 2)
LENSES = (21, 24, 35, 50, 85, 105)

# ---- the dolly: same picture, new perspective --------------------------------------------------------------------
def dolly(cam, foc, f_old, f_new):
    k = math.tan(f_old / 2) / math.tan(f_new / 2)
    return tuple(f + (c - f) * k for c, f in zip(cam, foc))
def screen_h(cam, foc, h, fov):
    # a subject h tall standing at the focus, seen from cam: its height on screen (1 = the whole picture)
    d = math.dist(cam, foc)
    return (h / d) / (2 * math.tan(fov / 2))
def down(cam, foc):
    d = [f - c for c, f in zip(cam, foc)]
    return math.atan2(-d[2], math.hypot(d[0], d[1]))
for a in LENSES:
    for b in LENSES:
        cam, foc = (10.0, 4.0, 26.5), (14.0, 7.0, 25.2)
        c2 = dolly(cam, foc, fov_of(a), fov_of(b))
        check(abs(screen_h(cam, foc, 1.8, fov_of(a)) - screen_h(c2, foc, 1.8, fov_of(b))) < 1e-9, f"{a}->{b} mm: the size changed")
        check(abs(down(cam, foc) - down(c2, foc)) < 1e-9, f"{a}->{b} mm: the angle down changed")
        check(abs(math.dist(c2, foc) / math.dist(cam, foc) - mm_of(fov_of(b)) / mm_of(fov_of(a))) < 1e-9, f"{a}->{b} mm: the distance is not in proportion")
# from 21 to 105 mm the camera goes five times as far: Only friends then cuts when that is past its 25 m
cam, foc = (0.0, 0.0, 2.0), (6.0, 0.0, 1.6)
far = dolly(cam, foc, fov_of(21), fov_of(105))
check(math.dist(far, foc) > 25.0, "the test case should be past MAX_DIST")

# ---- the scripts carry exactly this -------------------------------------------------------------------------------
check('if (gMode == "frame")\n    {\n        float fv' not in core and "float fv = llGetCameraFOV();" in core, "core: the zoom must be reported in every camera")
check('if (gState == ST_ROLL && gMode != "scenery")' in core, "core: people must be allowed to glide (the dolly)")
for name, s, guard in (("people", people, 'if (llVecDist(nc, gOP) > 30.0 || llList2Integer(ray(gCurFoc, nc), 0)) nextShot();'),
                       ("friends", friends, 'if (llVecDist(nc, gCenter) > MAX_DIST || llList2Integer(ray(gCurFoc, nc), 0)) nextShot(1.0);')):
    for frag in ("integer FOVMSG     = 7318;", "else if (num == FOVMSG)", "float k = tanV;", "gFov = (float)str;", "loadCfg();",
                 "vector nc = gCurFoc + (gCurCam - gCurFoc) * (k / tanV);", guard,
                 'llMessageLinked(LINK_SET, GLIDE, (string)gCurCam + "|" + (string)gCurFoc + "|1.5", "");', "gCurFoc = foc;"):
        check(frag in s, f"{name}: missing {frag}")
    i = s.index("else if (num == FOVMSG)")
    check(s.index("float k = tanV;", i) < s.index("loadCfg();", i), f"{name}: k must be taken before loadCfg re-solves tanV")
check("gS = gS * llTan(gF * 0.5) / llTan(f * 0.5);" in lens and "if (gS > 25.0) gS = 25.0;" in lens and "send(FALSE);" in lens,
      "lens: Follow my lead must keep your framing through a zoom (scaled, capped, no cut)")
check("gF = (float)llList2String(S, 1);" in lens, "lens: the lens at the start")
check("num == FOVMSG" in frame, "frame keeps its own zoom handling")

# ---- the lens shapes the shot mix ---------------------------------------------------------------------------------
BIAS = "fclamp((12.0 / llTan(gFov * 0.5) - 35.0) / 120.0, -0.15, 0.3)"   # the real lens, not the Frame-scaled tanV
for name, s in (("people", people), ("friends", friends)):
    check("llFrand(1.0) >= 0.55 + 0.25 * gOSit + " + BIAS in s, f"{name}: the close-view chance must follow the lens")
def p_close(mm, seated=0):
    t = math.tan(fov_of(mm) / 2)
    return 0.55 + 0.25 * seated + max(-0.15, min(0.3, (12.0 / t - 35.0) / 120.0))
ps = [p_close(mm) for mm in LENSES]
check(all(b >= a for a, b in zip(ps, ps[1:])), f"a longer lens must never mean fewer close views: {ps}")
check(abs(p_close(21) - 0.433) < 0.01 and abs(p_close(50) - 0.675) < 0.01 and abs(p_close(85) - 0.85) < 0.001 and abs(p_close(200) - 0.85) < 1e-9,
      f"the close-view chance table: 21 {p_close(21):.3f}, 50 {p_close(50):.3f}, 85 {p_close(85):.3f}")

print(f"zoom: the dolly keeps size and angle for {len(LENSES)}x{len(LENSES)} lens pairs; close views {p_close(21):.0%} at 21 mm, "
      f"{p_close(50):.0%} at 50 mm, {p_close(85):.0%} from 85 mm")
print("zoom checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
