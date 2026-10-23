# Follow my lead (5.1): you frame a Friends view with Second Life's own camera; core sends LEAD once it is still,
# lens.lsl keeps how close, how high, from where and aimed at what, and friends.lsl plans every next
# shot from it. A port of that chain: your view must come back exactly as the next planned shot, move with the group,
# scale with its distance, and the scripts must carry the same maths and wiring. (7.1: seated W/S no longer step closer
# or wider; seated the keys adjust the shot, fit_sim.)
import math, os, random

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
src = lambda n: open(os.path.join(R, "hud", "src", n)).read()
lens, friends, core, ui = src("lens.lsl"), src("friends.lsl"), src("core.lsl"), src("ui.lsl")
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

# ---- wiring ------------------------------------------------------------------------------------------------------
for w in ('integer LEAD       = 7324;', 'llMessageLinked(LINK_SET, LEAD, (string)cp + "|" + (string)f, "");',
          'else if (gPeekOn || gMode == "friends" || gMode == "free")', 'else if (llGetTime() - gLeadT > 1.5 - 0.5 * (gMode == "free"))', "float t = (f0 - cp) * u;"):
    check(w in core, f"core: missing {w}")
# 5.1 gave standing E/C back to your avatar; 6.7 keeps them only for Fit (fit_sim), and never while you fly
check(core.count("llTakeControls(") == 1 and "(info & AGENT_FLYING)) return FALSE;" in core,
      "core: one control request (7.1.1); E/C kept back only for Fit (fit.lsl) and Adjust, never while you fly")
check("llTakeControls(3, TRUE, FALSE);" not in core and "NUDGE" not in lens and "gS * 0.8" not in lens, "7.1: no seated W/S closer / wider in Friends (the keys adjust)")
check('integer own = (gMode == "friends" || gMode == "free");' in core and 'if (own && (llVecDist(cp, gShotPos) > 0.3 || llRot2Fwd(cr) * llVecNorm(gShotFoc - gShotPos) < 0.985)) dev = TRUE;' in core,
      "core: Friends does not notice a small move or a turn of your camera")
check("gShotFoc = f;" in core[core.index("place(vector p, vector f)"):] and "place(gp, gf);" in core and "place(p, f);" in core, "core: the shot's focus is not kept")
for w in ('integer LEAD       = 7324;', "gAim += q - gSubj;", "gS = llVecDist(c, q);",
          "gEl = llAtan2(h.z, llVecMag(<h.x, h.y, 0.0>));", "gAz = llAtan2(h.y, h.x);",
          'automatic(TRUE); }', "gSubj += f - gFoc;", "if (llVecDist(c, gLC) < 0.05) return;"):
    check(w in lens, f"lens: missing {w}")
for w in ('+ "|" + (string)gPFp, "");', "if (gLed > 0.0) gPAz = gLedAz;", "gVNeed = gLed;", "gPLo = gLed;", "gMeas = [];",
          "if ((gOSit || gLed > 0.0) && gSeatEl > 0.0) z = eyeRef + d * llTan(gSeatEl);",
          "if ((!gOSit && gLed == 0.0) || gSeatEl <= 0.0) return S;", "llAtan2(tanV * 0.236, 1.0) * (gLed == 0.0)",
          "gPEye = C.z + (gOE - gOP.z) + gAim.z;", "gPFp = <C.x + gAim.x, C.y + gAim.y, gPEye>;",
          'llMessageLinked(LINK_SET, CMD, "autoq", "");', "if (gPType == 3 && gUsedN > 0 && gLed == 0.0)"):
    check(w in friends, f"friends: missing {w}")
check('if (gUiMode == "friends") b += ["flist", "release"];' in ui and 'llMessageLinked(LINK_SET, CMD, "auto", "")' in ui and "tune" not in ui,
      "ui: the live menu should offer Release (back to automatic), not Tune")

# ---- the chain, ported -------------------------------------------------------------------------------------------
add = lambda a, b: tuple(x + y for x, y in zip(a, b))
sub = lambda a, b: tuple(x - y for x, y in zip(a, b))
mul = lambda a, k: tuple(x * k for x in a)
dot = lambda a, b: sum(x * y for x, y in zip(a, b))
mag = lambda a: math.sqrt(dot(a, a))
def norm(a): return mul(a, 1.0 / mag(a))

def core_lead(cp, u, f0):                              # core: the point your view looks at, nearest the old subject
    t = max(dot(sub(f0, cp), u), 0.5)
    return add(cp, mul(u, t))
def lens_lead(c, q):                                   # lens: how far, how high, from where
    h = sub(c, q)
    return mag(h), math.atan2(h[2], math.hypot(h[0], h[1])), math.atan2(h[1], h[0])
def friends_plan(base, aim, S, el, az, tanV=math.tan(math.radians(30))):
    # planF: subject = group base + aim; sweep picks off = 0 in the open; seatD: horizontal = S cos(el);
    # camZ: eye + d tan(el); tryCand: looks down by the same angle (no thirds offset when led)
    P = add(base, aim)
    d = S * math.cos(el) if el > 0 else S
    cam = (P[0] + math.cos(az) * d, P[1] + math.sin(az) * d, P[2] + d * math.tan(el) if el > 0 else P[2])
    r = cam[2] - P[2]
    pitch = math.atan2(r, d) if r > d * 0.176 else 0.0
    V = (-math.cos(az), -math.sin(az))
    foc = (cam[0] + V[0] * d, cam[1] + V[1] * d, cam[2] - d * math.tan(pitch))
    return cam, foc

rng = random.Random(9)
worst_pos = worst_dir = worst_move = worst_scale = 0.0
n = 0
for t in range(400):
    base = (rng.uniform(20, 200), rng.uniform(20, 200), rng.uniform(21, 40))        # the planned subject
    # you orbit: a camera 0.8 to 6 m from your faces, 12 to 70 degrees down, from anywhere; the faces are up to
    # 0.9 m from the planned subject (a lying avatar's head)
    faces = add(base, (rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), rng.uniform(-0.4, 0.2)))
    S0, el0, az0 = rng.uniform(0.8, 6.0), math.radians(rng.uniform(12, 70)), rng.uniform(-math.pi, math.pi)
    cp = add(faces, (math.cos(az0) * S0 * math.cos(el0), math.sin(az0) * S0 * math.cos(el0), S0 * math.sin(el0)))
    u = norm(sub(faces, cp))
    q = core_lead(cp, u, base)
    aim = sub(q, base)                                                              # lens: aim += q - subject (aim was 0)
    S, el, az = lens_lead(cp, q)
    cam, foc = friends_plan(base, aim, S, el, az)
    worst_pos = max(worst_pos, mag(sub(cam, cp)))
    worst_dir = max(worst_dir, math.degrees(math.acos(max(-1.0, min(1.0, dot(norm(sub(foc, cam)), u))))))
    # the group shifts by up to 1.5 m: the camera shifts with it, nothing else changes
    mv = (rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), 0.0)
    cam2, _ = friends_plan(add(base, mv), aim, S, el, az)
    worst_move = max(worst_move, mag(sub(sub(cam2, cam), mv)))
    # W: 20 % closer along the same line
    cam3, _ = friends_plan(base, aim, S * 0.8, el, az)
    worst_scale = max(worst_scale, abs(mag(sub(cam3, q)) - 0.8 * S))
    n += 1
check(worst_pos < 1e-6, f"your view comes back {worst_pos:.2e} m off")
check(worst_dir < 1e-4, f"your view comes back turned by {worst_dir:.2e} degrees")
check(worst_move < 1e-6, f"a moved group moves the camera wrongly by {worst_move:.2e} m")
check(worst_scale < 1e-6, f"the distance does not scale ({worst_scale:.2e} m off)")
# the core's focus: when you look at your faces, the point kept is on your line of sight nearest the old subject
check(abs(dot(sub(core_lead((0, 0, 0), (1, 0, 0), (3, 0.4, 0)), (3, 0, 0)), (1, 1, 1))) < 1e-9, "core lead point")
check(core_lead((0, 0, 0), (1, 0, 0), (-2, 0, 0)) == (0.5, 0.0, 0.0), "a subject behind the camera must not flip the view")
print(f"follow my lead: {n} orbited views come back exactly (worst {worst_pos:.0e} m, {worst_dir:.0e} deg), "
      f"follow the group and scale with the distance")
print("lens checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
