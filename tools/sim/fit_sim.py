# Fit (6.7.0, fit.lsl): Page Up / Page Down move you in the picture, because no script can see where a seated (or
# heeled, or ground-sitting) body really is. Checked here: a tap and a hold move as said and stop at the limit; the
# sign is right (Page Up: you go UP in the picture); the shot on screen (core) and every next shot (people, friends,
# frame read cin.fitz) agree; it is kept per seat (the last 20, a seat used again moves to the end), for the ground and
# for standing; core takes Page Up / Down only for a people camera and never while you fly; the other keys still
# reach the camera scripts; and the tip says it.
import math, os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
fit, core, people, friends, frame, tips = (rd("hud", "src", n) for n in ("fit.lsl", "core.lsl", "people.lsl", "friends.lsl", "frame.lsl", "tips.lsl"))
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)
num = lambda name: float(re.search(r"float\s+" + name + r"\s*=\s*([-\d.]+);", fit).group(1))
STEP, RUN, LIMIT = num("STEP"), num("RUN"), num("LIMIT")
SEATS = int(re.search(r"integer SEATS = (\d+);", fit).group(1))
check((STEP, RUN, LIMIT, SEATS) == (0.02, 0.025, 1.2, 20), f"fit: the steps changed: {STEP} {RUN} {LIMIT} {SEATS}")

# ---- a port of fit.lsl's keys ---------------------------------------------------------------------------------------
class Fit:
    def __init__(s): s.fit, s.keys, s.down, s.t, s.sent, s.lsd = 0.0, 0, 0.0, 0.0, [], {}
    def move(s, d):
        f = max(-LIMIT, min(LIMIT, s.fit + d))
        if f == s.fit: return
        s.sent.append(s.fit - f); s.fit = f; s.lsd["fitz"] = -f
    def key(s, k):                                       # FITKEY from core: what is held now
        if k & ~s.keys & 16: s.move(STEP)
        if k & ~s.keys & 32: s.move(-STEP)
        if k and not s.keys: s.down = s.t
        s.keys = k
    def timer(s):                                        # every 0.1 s while held
        s.t += 0.1
        if s.keys and s.t - s.down > 0.4 + 1e-9: s.move(RUN * bool(s.keys & 16) - RUN * bool(s.keys & 32))
f = Fit(); f.key(16); f.key(0)
check(abs(f.fit - 0.02) < 1e-9, f"a tap of Page Up: {f.fit}")
f = Fit(); f.key(16)
for _ in range(10): f.timer()
f.key(0)
check(abs(f.fit - (0.02 + 6 * 0.025)) < 1e-9, f"one second held: {f.fit:.3f} m (a tap, then 0.25 m/s after 0.4 s)")
f = Fit(); f.key(32)
for _ in range(200): f.timer()
check(abs(f.fit + LIMIT) < 1e-9 and abs(sum(f.sent) - LIMIT) < 1e-9, "held down: it stops at the limit, and the glides add up to it")
for frag in ("if (k & ~gKeys & 16) move(STEP);", "if (k & ~gKeys & 32) move(-STEP);", "if (k && !gKeys) gDownT = llGetTime();",
             "if (gKeys && llGetTime() - gDownT > 0.4) move(RUN * ((gKeys & 16) > 0) - RUN * ((gKeys & 32) > 0));",
             'llMessageLinked(LINK_SET, FIT, (string)(gFit - f), "");', 'set("fitz", (string)(-gFit));', "integer k = (integer)str * gOn;"):
    check(frag in fit, f"fit.lsl: the port is stale: {frag}")

# ---- the sign, and the two paths agree --------------------------------------------------------------------------
# a level camera at height zc, D away: your eyes at y = (eye - zc) / (D tanV). Page Up (fit > 0): cin.fitz = -fit, so the
# camera scripts think your eyes are lower, place the camera lower, and you show higher. Core moves the shot on screen
# by the same dz (FIT "<gFit - f>"), so the shot on screen and the next one planned agree.
tanV = math.tan(math.radians(30))
camZ = lambda eye, d: eye - d * tanV * 0.236            # people / friends camZ (no floor in the way)
eye, D = 1.0, 3.0
y0 = (eye - camZ(eye, D)) / (D * tanV)
f = Fit(); f.key(16); f.key(0)
fitz = f.lsd["fitz"]
y_next = (eye - camZ(eye + fitz, D)) / (D * tanV)       # the next shot, planned with the fit
y_now = (eye - (camZ(eye, D) + sum(f.sent))) / (D * tanV)   # the shot on screen, moved by core
check(y_next > y0 and abs(y_next - y_now) < 1e-12, f"Page Up must move you up in the picture, the same now and next: {y0:.3f} -> {y_now:.3f} / {y_next:.3f}")
for name, s in (("people", people), ("friends", friends)):
    check('gOE = gOP.z + (K_EYE_STAND + (K_EYE_SIT - K_EYE_STAND) * gOSit) * sz.z + (float)cfg("fitz", "0");' in s, f"{name}: the eyes must include Fit")
check('float fz = (float)llLinksetDataReadProtected("cin.fitz", PASS);' in frame and "float z0 = P.z - 0.5 * h + fz;" in frame
      and "E.z = P.z + 0.25 * h + fz;" in frame and "float z0 = p.z - 0.5 * h + ff * (i == 0);" in frame, "frame (Still): you, alone or in a group, where Fit says")
check("gNH" not in frame and "CONTROL_UP" not in frame, "frame: E/C no longer nudge the camera (they are Fit's)")

# ---- core: the keys and the shot ----------------------------------------------------------------------------------
check('return (gState != ST_IDLE && llListFindList(["personal", "social", "friends", "frame"], [gMode]) >= 0 && !(info & AGENT_FLYING));' in core,
      "core: Fit only for a people camera, never while you fly")
tc = core[core.index("takeCtl(integer pass)"):core.index("// ---- lifecycle")]
check("if (gFitCtl) llTakeControls(48, TRUE, FALSE);" in tc and tc.index("llTakeControls(48") > tc.rindex("llTakeControls(CTL"),
      "core: Page Up / Down kept back (no jump) while they are Fit's, after every other control request (seated friends passes the rest on)")
check('else if (was) llMessageLinked(LINK_SET, FITKEY, "0", "");' in tc, "core: taking off or stopping while a key is held lets go of it")
check("|| fitOK(info) != gFitCtl) takeCtl(gMode != \"frame\");" in core, "core: taking off or landing hands the keys over again")
ctl = core[core.index("control(key id, integer level, integer edge)"):core.index("timer()", core.index("control(key id"))]
check(ctl.index("FITKEY") < ctl.index("NUDGE") and "level = level & ~48;" in ctl and "edge = edge & ~48;" in ctl,
      "core: Page Up / Down go to Fit, the other keys still nudge or walk")
check(ctl.index('if (gMode == "free") return;') < ctl.index("FITKEY") and ctl.index("bail(\"key\");") < ctl.index("FITKEY"),
      "core: Freehand and Scenery keep their own keys")
check('vector d = <0.0, 0.0, gFitShift * (gMode != "frame")>;' in core and "gFitShift += d.z;" in core
      and "glide(gShotPos + d, gShotFoc + d, 0.2);" in core and "gFitShift = 0.0;" in core[core.index("applyShot(string s)"):],
      "core: the shot moves at once; a camera's later glides keep the move until its next shot (Still re-solves itself)")
check('if (gPermOK) takeCtl(TRUE);' in core[core.index("bail(string why)"):core.index("engage(string mode)")], "core: the keys go back when the camera stops")

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
for frag in ('if (!(i & AGENT_SITTING)) return "stand";', 'if (!(i & AGENT_ON_OBJECT)) return "ground";', "list d = llGetObjectDetails(gOwner, [OBJECT_ROOT, OBJECT_POS]);",
             'return (string)r + "@" + (string)llRound(v.x * 2.0) + ":" + (string)llRound(v.y * 2.0);',
             'llLinksetDataDeleteProtected("cin.fit." + llList2String(L, 0), PASS);', "if (!k && gKeys) keep();"):
    check(frag in fit, f"fit.lsl: {frag}")
# where on the seat: each side of a sofa (1 m apart) is its own, a shuffle of 10 cm is not
side = lambda x, y: (round(x * 2.0), round(y * 2.0))
check(side(0.0, -0.5) != side(0.0, 0.5) and side(0.62, 0.1) == side(0.7, 0.05), "seat sides: half a metre apart")

# ---- the tip ----------------------------------------------------------------------------------------------------------
check('"Sitting\\nsitting: Page Up / Down move you in the picture",' in tips and "else if (!gSat && m >= 1 && m <= 4 && (llGetAgentInfo(gOwner) & AGENT_SITTING))" in tips,
      "tips: seated in any people camera, the tip says Page Up / Down")
check('"Still\\nW/S A/D adjust · Page Up / Down: you up or down",' in tips, "tips: Still's tip")
print(f"fit: a tap {STEP * 100:.0f} cm, held {RUN * 10 * 100:.0f} cm/s after 0.4 s, up to {LIMIT:.1f} m; Page Up moves you up, the same on screen and next; "
      f"{SEATS} seats, the ground, standing")
print("fit checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
