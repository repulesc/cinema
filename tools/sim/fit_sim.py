# Adjust and Fit (fit.lsl; 6.7 Fit: Page Up / Page Down move the camera up or down, because no script can see where a
# seated, heeled or ground-sitting body really is; 7.1 Adjust: tilt, swing and slide too). Checked here: a tap and a hold
# move as said on all four axes and stop at their limits; the sign is right (Page Up: the camera goes UP); the shot on
# screen (core) and every next shot (people, friends, frame read cin.fitz) agree; it is kept per seat (the last 20, a
# seat used again moves to the end), for the ground and for standing; core's trim keeps the distance on a swing, moves
# only the focus on a tilt and both on a slide; seated the keys always adjust, standing only after ADJUST, never while
# you fly; Adjust is reset where it should be; and the tips say it.
import math, os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
fit, core, people, friends, frame, tips = (rd("hud", "src", n) for n in ("fit.lsl", "core.lsl", "people.lsl", "friends.lsl", "frame.lsl", "tips.lsl"))
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)
lst = lambda name, t=float: [t(x) for x in re.search(r"list\s+" + name + r"\s*=\s*\[([-\d., ]+)\];", fit).group(1).split(",")]
UPS, DOWNS = lst("UPS", int), lst("DOWNS", int)
STEPS, RATES, LIMITS = lst("STEPS"), lst("RATES"), lst("LIMITS")
num = lambda name: float(re.search(r"float\s+" + name + r"\s*=\s*([-\d.]+);", fit).group(1))
RAMP, FULL = num("RAMP"), num("FULL")
SEATS = int(re.search(r"integer SEATS = (\d+);", fit).group(1))
rad = math.radians
check(UPS == [16, 1, 256, 8] and DOWNS == [32, 2, 512, 4], f"the keys: height PgUp/PgDn, tilt W/S, swing A/D, slide Shift+D/A {UPS} {DOWNS}")
check(abs(STEPS[0] - 0.10) < 1e-9 and abs(STEPS[1] - rad(1)) < 1e-5 and abs(STEPS[2] - rad(3)) < 1e-5 and abs(STEPS[3] - 0.05) < 1e-9, f"a tap: {STEPS}")
check(abs(RATES[0] - 0.6) < 1e-9 and abs(RATES[1] - rad(15)) < 1e-4 and abs(RATES[2] - rad(45)) < 1e-4 and abs(RATES[3] - 0.5) < 1e-9, f"held: {RATES}")
check(abs(LIMITS[0] - 1.5) < 1e-9 and abs(LIMITS[1] - rad(25)) < 1e-4 and abs(LIMITS[2] - rad(75)) < 1e-4 and abs(LIMITS[3] - 1.5) < 1e-9, f"limits: {LIMITS}")
check((RAMP, FULL, SEATS) == (0.3, 1.0, 20), f"the ramp {RAMP} {FULL}, {SEATS} seats")

# ---- a port of fit.lsl's keys ---------------------------------------------------------------------------------------
class Fit:
    def __init__(s): s.v, s.keys, s.down, s.t, s.sent, s.trim = [0.0] * 4, 0, 0.0, 0.0, [], []
    def move(s, a, d):
        f = max(-LIMITS[a], min(LIMITS[a], s.v[a] + d))
        if f == s.v[a]: return
        if a == 0: s.sent.append(f - s.v[0])
        s.v[a] = f
        if a: s.trim.append(tuple(s.v[1:]))
    def key(s, k):                                       # FITKEY from core: what is held now
        for a in range(4):
            if k & ~s.keys & UPS[a]: s.move(a, STEPS[a])
            if k & ~s.keys & DOWNS[a]: s.move(a, -STEPS[a])
        if k and not s.keys: s.down = s.t
        s.keys = k
    def timer(s):                                        # every 0.1 s while held
        s.t += 0.1
        h = s.t - s.down
        if s.keys and h > RAMP + 1e-9:
            r = min(1.0, 0.2 + 0.8 * (h - RAMP) / (FULL - RAMP))
            for a in range(4):
                v = RATES[a] * 0.1 * r
                if s.keys & UPS[a]: s.move(a, v)
                if s.keys & DOWNS[a]: s.move(a, -v)
def held(k, sec, a):
    f = Fit(); f.key(k)
    for _ in range(round(sec * 10)): f.timer()
    f.key(0)
    return f.v[a]
for a, (up, dn) in enumerate(zip(UPS, DOWNS)):
    f = Fit(); f.key(up); f.key(0)
    check(abs(f.v[a] - STEPS[a]) < 1e-9, f"axis {a}: a tap is one step ({f.v[a]})")
    f = Fit(); f.key(dn); f.key(0)
    check(abs(f.v[a] + STEPS[a]) < 1e-9, f"axis {a}: a tap the other way")
    early = (held(up, 0.5, a) - held(up, 0.4, a)) / 0.1
    full = (held(up, 1.6, a) - held(up, 1.2, a)) / 0.4
    check(early < 0.5 * RATES[a] and abs(full - RATES[a]) < 1e-6 or held(up, 1.6, a) >= LIMITS[a] - 1e-9,
          f"axis {a}: slow at first ({early:.3f}/s), full speed after a second ({full:.3f}/s of {RATES[a]})")
    check(abs(held(dn, 30.0, a) + LIMITS[a]) < 1e-9, f"axis {a}: held, it stops at the limit")
check(abs((held(16, 2.0, 0) - held(16, 1.0, 0)) - 0.6) < 1e-6, "Page Up held: 60 cm a second at full speed (the big move: no script sees Shift)")
f = Fit(); f.key(32)
for _ in range(200): f.timer()
check(abs(sum(f.sent) + LIMITS[0]) < 1e-9, "the height's glides add up to where it stopped")
f = Fit(); f.key(1 | 256); f.key(0)
check(f.trim[-1] == (STEPS[1], STEPS[2], 0.0), "two keys at once: both axes move")
for frag in ("if (k & ~gKeys & llList2Integer(UPS, a)) move(a, llList2Float(STEPS, a));", "if (k & ~gKeys & llList2Integer(DOWNS, a)) move(a, -llList2Float(STEPS, a));",
             "if (k && !gKeys) gDownT = llGetTime();", "float r = 0.2 + 0.8 * (h - RAMP) / (FULL - RAMP);", "if (r > 1.0) r = 1.0;",
             "float v = llList2Float(RATES, a) * 0.1 * r;", "if (gKeys & llList2Integer(UPS, a)) move(a, v);", "if (gKeys & llList2Integer(DOWNS, a)) move(a, -v);",
             'llMessageLinked(LINK_SET, FIT, (string)(f - gFit), "");', 'if (!gFree) set("fitz", (string)gFit);', "integer k = (integer)str * gOn;",
             'llMessageLinked(LINK_SET, TRIM, (string)gT.x + "|" + (string)gT.y + "|" + (string)gT.z, "");', "if (gKeys && h > RAMP)"):
    check(frag in fit, f"fit.lsl: the port is stale: {frag}")
check('if (gTaps < 3 && !gKeys) s += "\\nhold: faster";' in fit, "fit: the first taps say that a hold is faster")
check('if (cfg("trace") == "1") llOwnerSay("[Take 12] keys " + str);' in fit, "fit: Chat text shows the keys the viewer sends (Shift + Page Down)")
check('show("Adjust · W/S tilt · A/D around · Shift+A/D side · PgUp/PgDn height");' in fit and 'show("Walk · the keys move you");' in fit,
      "fit: Adjust on / off is said above the button")
# 7.1.1: the help stays 6 s and comes back once (4 s) after 15 s unless a key was pressed
check("help(6.0);" in fit and "gHelpT = llGetTime();" in fit and "if (gHelpT > 0.0 && gAdj && llGetTime() - gHelpT > 15.0)" in fit
      and "help(4.0);" in fit and "if (k) gHelpT = 0.0;" in fit and "llGetTime() - gTextT > gTextFor" in fit and "gTextFor = 3.0;" in fit,
      "fit: the Adjust help stays 6 s, and comes back once for 4 s after 15 s until you press a key")

# ---- the sign, and the two paths agree --------------------------------------------------------------------------
# a level camera at height zc, D away: your eyes at y = (eye - zc) / (D tanV). Page Up (fit > 0): cin.fitz = +fit, so the
# camera scripts frame as if your eyes were higher: the camera rises (and you show lower). Core moves the shot on screen
# by the same dz (FIT "<f - gFit>"), so the shot on screen and the next one planned agree.
tanV = math.tan(math.radians(30))
camZ = lambda eye, d: eye - d * tanV * 0.236            # people / friends camZ (no floor in the way)
eye, D = 1.0, 3.0
y0 = (eye - camZ(eye, D)) / (D * tanV)
f = Fit(); f.key(16); f.key(0)
fitz = f.v[0]                                           # cin.fitz
y_next = (eye - camZ(eye + fitz, D)) / (D * tanV)       # the next shot, planned with the fit
y_now = (eye - (camZ(eye, D) + sum(f.sent))) / (D * tanV)   # the shot on screen, moved by core
cam_next, cam_now = camZ(eye + fitz, D), camZ(eye, D) + sum(f.sent)
check(cam_next > camZ(eye, D) and abs(cam_next - cam_now) < 1e-12 and y_next < y0 and abs(y_next - y_now) < 1e-12,
      f"Page Up must raise the camera, the same now and next: camera {camZ(eye, D):.3f} -> {cam_now:.3f} / {cam_next:.3f}")
for name, s in (("people", people), ("friends", friends)):
    check('gOE = gOP.z + (K_EYE_STAND + (K_EYE_SIT - K_EYE_STAND) * gOSit) * sz.z + (float)cfg("fitz", "0");' in s, f"{name}: the eyes must include Fit")
check('float fz = (float)llLinksetDataReadProtected("cin.fitz", PASS);' in frame and "float z0 = P.z - 0.5 * h + fz;" in frame
      and "E.z = P.z + 0.25 * h + fz;" in frame and "float z0 = p.z - 0.5 * h + ff * (i == 0);" in frame, "frame (Still): you, alone or in a group, where Fit says")
check("gNH" not in frame and "CONTROL_UP" not in frame, "frame: E/C no longer nudge the camera (they are Fit's)")

# ---- core: who gets the keys ---------------------------------------------------------------------------------------
fo = core[core.index("integer fitOK(integer info)"):core.index("// the movement keys")]
check("if (gState == ST_IDLE || (info & AGENT_FLYING)) return FALSE;" in fo and '["personal", "social", "friends", "frame"]' in fo
      and 'return (gMode == "free" && (gAdjOn || (info & AGENT_SITTING)));' in fo, "core: Fit for a people camera (Freehand: while adjusting), never while you fly")
tc = core[core.index("takeCtl(integer pass)"):core.index("// ---- lifecycle")]
check("gAdj = (gFitCtl && (gAdjOn || gSitCtl));" in tc and "llTakeControls(CTL, TRUE, pass && !gAdj);" in tc,
      "core: seated the keys always adjust, standing after ADJUST; then none of them reaches your avatar")
# 7.1.1: a script holds ONE set of controls (a second llTakeControls replaces the first): 7.0 / 7.1.0 took Page Up / Down
# last, so the movement keys were not taken (Adjust walked you, Me never heard you walk). Core: one request; fit keeps
# Page Up / Down from your avatar with its own.
check(tc.count("llTakeControls(") == 1 and core.count("llTakeControls(") == 1, "core: exactly one control request")
check('if (on) llTakeControls(48, TRUE, FALSE);' in fit and 'else llTakeControls(48, FALSE, TRUE);' in fit and fit.count("llTakeControls(") == 2
      and "gWant48 = (integer)llList2String(L, 5);" in fit and "hold(gWant48);" in fit and "control(key id, integer level, integer edge)" in fit
      and "llRequestPermissions(gOwner, PERMISSION_TAKE_CONTROLS);" in fit, "fit: keeps Page Up / Down from your avatar (no jump) while Fit is on, its own request")
check('+ "|" + (string)gAdj + "|" + (string)gFitCtl, "");' in core, "core: UI_STATE says when Fit is on (field 6)")
check('if ((was && !gFitCtl) || (adj && !gAdj)) llMessageLinked(LINK_SET, FITKEY, "0", "");' in tc, "core: taking off, stopping or walking again while a key is held lets go of it")
check('if ((adj != gAdj || was != gFitCtl) && gState != ST_IDLE) setUi(' in tc, "core: the keys strip, tips and fit hear when Adjust or Fit turn on or off")
check("if ((info & AGENT_SITTING) != gSitCtl || fitOK(info) != gFitCtl) takeCtl(TRUE);" in core, "core: sitting down, standing up, taking off, landing hand the keys over again")
ctl = core[core.index("control(key id, integer level, integer edge)"):core.index("timer()", core.index("control(key id"))]
check(ctl.index('bail("key");') < ctl.index("if (gAdj)") < ctl.index('if (gMode == "free") return;') < ctl.index("level = level & ~48;"),
      "core: Scenery keeps its keys; Adjust takes every key (Freehand too); otherwise Page Up / Down go to Fit and the rest walk you")
check('if (edge) llMessageLinked(LINK_SET, FITKEY, (string)(level & CTL), "");' in ctl, "core: Adjust hands over every key held")
check('else if (str == "adjust")' in core and "gAdjOn = !gAdjOn;" in core and core.count("gAdjOn = FALSE;") >= 3, "core: ADJUST toggles; a stop, a new camera and a teleport turn it off")
check("if (!gSitCtl) gAdjOn = !gAdjOn;" in core, "core: ADJUST tapped while seated (where the keys always adjust) is not left on for when you stand up")
check("llTakeControls(3, TRUE, FALSE);" not in core, "7.1: no seated W/S closer / wider in Friends (the keys adjust)")

# ---- core: the trim on every shot ---------------------------------------------------------------------------------
def V(*a): return list(a)
add = lambda a, b: [x + y for x, y in zip(a, b)]
sub = lambda a, b: [x - y for x, y in zip(a, b)]
mul = lambda a, k: [x * k for x in a]
mag = lambda a: math.sqrt(sum(x * x for x in a))
cross = lambda a, b: [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def rotz(v, ang):                                        # v * llAxisAngle2Rot(<0,0,1>, ang)
    c, s_ = math.cos(ang), math.sin(ang)
    return [v[0] * c - v[1] * s_, v[0] * s_ + v[1] * c, v[2]]
def place(p, f, tilt, swing, slide):                     # a port of core's place(), with no wall in the way
    d = rotz(sub(p, f), -swing)
    n = cross([0, 0, 1], d); f = add(f, mul(n, slide / mag(n)))
    p = add(f, d)
    f = add(f, [0, 0, mag(d[:2] + [0]) * math.tan(tilt)])
    return p, f
pl = core[core.index("place(vector p, vector f)"):core.index("untrim()")]
for frag in ("vector d = (p - f) * llAxisAngle2Rot(<0.0, 0.0, 1.0>, -gTrim.y);", "f += llVecNorm(<0.0, 0.0, 1.0> % d) * gTrim.z;", "p = f + d;",
             "f.z += llVecMag(<d.x, d.y, 0.0>) * llTan(gTrim.x);", "if (llList2Integer(h, -1) == 1) p = llList2Vector(h, 1) + llVecNorm(f - p) * 0.3;",
             "gBaseP = p;", "gShotPos = p;"):
    check(frag in pl, f"core place(): the port is stale: {frag}")
P, F = [3.0, 0.0, 1.6], [0.0, 0.0, 1.6]                   # a camera 3 m east of you, looking west at your eyes
p, f = place(P, F, 0, rad(20), 0)
check(abs(mag(sub(p, f)) - 3.0) < 1e-9 and f == F and abs(p[2] - P[2]) < 1e-12, "swing: around you, the same distance and height")
right = cross(sub(F, P), [0, 0, 1])                       # the camera's right: forward x up (Second Life: +Y is left)
check(sum(a * b for a, b in zip(sub(p, P), mul(right, -1))) > 0, "swing +: the camera goes to its left (A)")
p, f = place(P, F, rad(10), 0, 0)
check(p == P and abs(f[2] - (F[2] + 3.0 * math.tan(rad(10)))) < 1e-12 and f[:2] == F[:2], "tilt +: the camera stays, its aim goes up (W)")
p, f = place(P, F, 0, 0, 0.5)
check(abs(mag(sub(p, P)) - 0.5) < 1e-9 and abs(mag(sub(f, F)) - 0.5) < 1e-9 and sum(a * b for a, b in zip(sub(p, P), right)) > 0,
      "slide +: camera and aim move together, to the camera's right (Shift+D)")
check(place(P, F, 0, 0, 0) == (P, F), "no adjustment: the shot as planned")
check("place(p, f);" in core[core.index("setCam(vector p, vector f)"):core.index("applyShot(string s)")] and "place(gp, gf);" in core,
      "core: every cut and every glide goes through the trim")
check("glide(gBaseP + d, gBaseF + d, 0.2);" in core and "if (gState == ST_ROLL) glide(gBaseP, gBaseF, 0.15);" in core,
      "core: Fit and Adjust move the shot on screen from the planned one, at once")
check('vector d = <0.0, 0.0, gFitShift * (gMode != "frame")>;' in core and "gFitShift += d.z;" in core and "gFitShift = 0.0;" in core[core.index("applyShot(string s)"):],
      "core: a camera's later glides keep the Fit move until its next shot (Me re-solves itself)")
# ---- when Adjust starts clean, and the groups' held shot ------------------------------------------------------------
ut = core[core.index("untrim()"):core.index("setCam(vector p")]
check("gTrim = ZERO_VECTOR;" in ut and "gHeld = FALSE;" in ut and 'llMessageLinked(LINK_SET, FITKEY, "r", "");' in ut and 'gT = ZERO_VECTOR;' in fit,
      "core and fit start Adjust clean together")
check('if ((gMode == "social" || gMode == "friends") && s != gLast) untrim();' in core, "Us, Friends: each new cut its own picture (not after a pause)")
check('llGetSubString(str, 0, 7) == "framing|" || llGetSubString(str, 0, 4) == "view|") untrim();' in core and core.count("untrim();") >= 6,
      "Me keeps it until Full / Half / Close change; Next, a saved view, your own framing, a stop or a new camera start clean")
check("if (gHeld && !gAsking) return;" in core and "gHeld = TRUE;" in core and "&& !gHeld)" in core[core.index("// hold timer"):],
      "Us, Friends: adjusting holds the shot (no cut by time or by a speaker) until Next")
# ---- kept per seat ------------------------------------------------------------------------------------------------
def keep(lsd, ctx, val):
    lsd["fit." + ctx] = val
    if ctx in ("stand", "ground"): return
    L = [x for x in lsd.get("fitseats", "").split(",") if x]
    if ctx in L: L.remove(ctx)
    L.append(ctx)
    if len(L) > SEATS:
        lsd.pop("fit." + L[0], None); L = L[1:]
    lsd["fitseats"] = ",".join(L)
lsd = {}
for i in range(25): keep(lsd, f"seat{i}@0:1", 0.01 * i)
keep(lsd, "seat5@0:1", 0.3); keep(lsd, "stand", -0.05); keep(lsd, "ground", 0.2)
seats = lsd["fitseats"].split(",")
check(len(seats) == SEATS and seats[-1] == "seat5@0:1" and "seat0@0:1" not in seats and "fit.seat0@0:1" not in lsd, "the last 20 seats, a seat used again moves to the end")
check(lsd["fit.stand"] == -0.05 and lsd["fit.ground"] == 0.2 and "stand" not in seats, "standing and the ground are kept apart from the seats")
check('gFit = (float)cfg("fitc." + c);' in fit and 'set("fitc." + gCtx, (string)gFit);' in fit and '"fit.' not in fit,
      "6.7.1: the values are kept as fitc.* (6.7.0's had the other sign)")
for frag in ('if (!(i & AGENT_SITTING)) return "stand";', 'if (!(i & AGENT_ON_OBJECT)) return "ground";', "list d = llGetObjectDetails(gOwner, [OBJECT_ROOT, OBJECT_POS]);",
             'return (string)r + "@" + (string)llRound(v.x * 2.0) + ":" + (string)llRound(v.y * 2.0);',
             'llLinksetDataDeleteProtected("cin.fitc." + llList2String(L, 0), PASS);', "keep();                                     // let go: kept",
             "if (gFree) return;"):
    check(frag in fit, f"fit.lsl: {frag}")
# where on the seat: each side of a sofa (1 m apart) is its own, a shuffle of 10 cm is not
side = lambda x, y: (round(x * 2.0), round(y * 2.0))
check(side(0.0, -0.5) != side(0.0, 0.5) and side(0.62, 0.1) == side(0.7, 0.05), "seat sides: half a metre apart")

# ---- the tip ----------------------------------------------------------------------------------------------------------
check('"Sitting\\nsitting: W/S tilt · A/D around · PgUp/PgDn height",' in tips and "else if (!gSat && m >= 1 && m <= 4 && (llGetAgentInfo(gOwner) & AGENT_SITTING))" in tips,
      "tips: seated in any people camera, the tip says the keys adjust")
check('"Me\\nwalk: it follows · Adjust: the keys trim the shot",' in tips, "tips: Framing › Me's tip (7.1)")
print(f"adjust: taps {STEPS[0] * 100:.0f} cm / {math.degrees(STEPS[1]):.0f} deg tilt / {math.degrees(STEPS[2]):.0f} deg around / {STEPS[3] * 100:.0f} cm side, "
      f"full speed after {FULL:.0f} s; the trim keeps the distance, the aim, the pair; Page Up raises the camera, the same on screen and next; {SEATS} seats")
print("fit checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
