# Fit (6.7.0, fit.lsl; 6.7.1: Page Up raises the camera, a tap is 5 cm and a hold speeds up): Page Up / Page Down move
# the camera up or down, because no script can see where a seated (or heeled, or ground-sitting) body really is (nor
# Shift: the hold is the big move). Checked here: a tap and a hold move as said and stop at the limit; the sign is
# right (Page Up: the camera goes UP); the shot on screen (core) and every next shot (people, friends, frame read
# cin.fitz) agree; it is kept per seat (the last 20, a seat used again moves to the end), for the ground and for
# standing; core takes Page Up / Down only for a people camera and never while you fly; the other keys still reach
# the camera scripts; and the tip says it.
import math, os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
fit, core, people, friends, frame, tips = (rd("hud", "src", n) for n in ("fit.lsl", "core.lsl", "people.lsl", "friends.lsl", "frame.lsl", "tips.lsl"))
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)
num = lambda name: float(re.search(r"float\s+" + name + r"\s*=\s*([-\d.]+);", fit).group(1))
STEP, SLOW, GROW, FAST, LIMIT = (num(n) for n in ("STEP", "SLOW", "GROW", "FAST", "LIMIT"))
SEATS = int(re.search(r"integer SEATS = (\d+);", fit).group(1))
check((STEP, SLOW, GROW, FAST, LIMIT, SEATS) == (0.05, 0.01, 0.025, 0.05, 1.5, 20), f"fit: the steps changed: {STEP} {SLOW} {GROW} {FAST} {LIMIT} {SEATS}")

# ---- a port of fit.lsl's keys ---------------------------------------------------------------------------------------
class Fit:
    def __init__(s): s.fit, s.keys, s.down, s.t, s.sent, s.lsd = 0.0, 0, 0.0, 0.0, [], {}
    def move(s, d):
        f = max(-LIMIT, min(LIMIT, s.fit + d))
        if f == s.fit: return
        s.sent.append(f - s.fit); s.fit = f; s.lsd["fitz"] = f
    def key(s, k):                                       # FITKEY from core: what is held now
        if k & ~s.keys & 16: s.move(STEP)
        if k & ~s.keys & 32: s.move(-STEP)
        if k and not s.keys: s.down = s.t
        s.keys = k
    def timer(s):                                        # every 0.1 s while held
        s.t += 0.1
        h = s.t - s.down
        if s.keys and h > 0.4 + 1e-9:
            v = min(FAST, SLOW + GROW * (h - 0.4))
            s.move(v * bool(s.keys & 16) - v * bool(s.keys & 32))
f = Fit(); f.key(16); f.key(0)
check(abs(f.fit - 0.05) < 1e-9, f"a tap of Page Up: {f.fit}")
def held(sec):
    f = Fit(); f.key(16)
    for _ in range(round(sec * 10)): f.timer()
    f.key(0)
    return f.fit
h1, h2, h3 = held(1.0), held(2.0), held(3.0)
speed = lambda a, b, dt: (b - a) / dt
check(0.10 < h1 < 0.20, f"one second held: {h1:.3f} m (slow at first, for precision)")
check(speed(h2, h3, 1.0) > 0.45, f"after 2 s held it runs at {speed(h2, h3, 1.0):.2f} m/s (the big move, as Shift would have been)")
check(speed(held(0.6), held(0.8), 0.2) < 0.2, "the first moments of a hold are slow")
f = Fit(); f.key(32)
for _ in range(200): f.timer()
check(abs(f.fit + LIMIT) < 1e-9 and abs(sum(f.sent) + LIMIT) < 1e-9, "held down: it stops at the limit, and the glides add up to it")
for frag in ("if (k & ~gKeys & 16) move(STEP);", "if (k & ~gKeys & 32) move(-STEP);", "if (k && !gKeys) gDownT = llGetTime();",
             "float v = SLOW + GROW * (h - 0.4);", "if (v > FAST) v = FAST;", "move(v * ((gKeys & 16) > 0) - v * ((gKeys & 32) > 0));",
             'llMessageLinked(LINK_SET, FIT, (string)(f - gFit), "");', 'set("fitz", (string)gFit);', "integer k = (integer)str * gOn;"):
    check(frag in fit, f"fit.lsl: the port is stale: {frag}")

# ---- the sign, and the two paths agree --------------------------------------------------------------------------
# a level camera at height zc, D away: your eyes at y = (eye - zc) / (D tanV). Page Up (fit > 0): cin.fitz = +fit, so the
# camera scripts frame as if your eyes were higher: the camera rises (and you show lower). Core moves the shot on screen
# by the same dz (FIT "<f - gFit>"), so the shot on screen and the next one planned agree.
tanV = math.tan(math.radians(30))
camZ = lambda eye, d: eye - d * tanV * 0.236            # people / friends camZ (no floor in the way)
eye, D = 1.0, 3.0
y0 = (eye - camZ(eye, D)) / (D * tanV)
f = Fit(); f.key(16); f.key(0)
fitz = f.lsd["fitz"]
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

# ---- core: the keys and the shot ----------------------------------------------------------------------------------
check('return (gState != ST_IDLE && llListFindList(["personal", "social", "friends", "frame"], [gMode]) >= 0 && !(info & AGENT_FLYING));' in core,
      "core: Fit only for a people camera, never while you fly")
tc = core[core.index("takeCtl(integer pass)"):core.index("// ---- lifecycle")]
check("if (gFitCtl) llTakeControls(48, TRUE, FALSE);" in tc and tc.index("llTakeControls(48") > tc.rindex("llTakeControls(CTL"),
      "core: Page Up / Down kept back (no jump) while they are Fit's, after every other control request (seated friends passes the rest on)")
check('else if (was) llMessageLinked(LINK_SET, FITKEY, "0", "");' in tc, "core: taking off or stopping while a key is held lets go of it")
check("|| fitOK(info) != gFitCtl) takeCtl(TRUE);" in core, "core: taking off or landing hands the keys over again")
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
check('gFit = (float)cfg("fitc." + c);' in fit and 'set("fitc." + gCtx, (string)gFit);' in fit and '"fit.' not in fit,
      "6.7.1: the values are kept as fitc.* (6.7.0's had the other sign)")
for frag in ('if (!(i & AGENT_SITTING)) return "stand";', 'if (!(i & AGENT_ON_OBJECT)) return "ground";', "list d = llGetObjectDetails(gOwner, [OBJECT_ROOT, OBJECT_POS]);",
             'return (string)r + "@" + (string)llRound(v.x * 2.0) + ":" + (string)llRound(v.y * 2.0);',
             'llLinksetDataDeleteProtected("cin.fitc." + llList2String(L, 0), PASS);', "if (!k && gKeys) keep();"):
    check(frag in fit, f"fit.lsl: {frag}")
# where on the seat: each side of a sofa (1 m apart) is its own, a shuffle of 10 cm is not
side = lambda x, y: (round(x * 2.0), round(y * 2.0))
check(side(0.0, -0.5) != side(0.0, 0.5) and side(0.62, 0.1) == side(0.7, 0.05), "seat sides: half a metre apart")

# ---- the tip ----------------------------------------------------------------------------------------------------------
check('"Sitting\\nsitting: Page Up / Down move you in the picture",' in tips and "else if (!gSat && m >= 1 && m <= 4 && (llGetAgentInfo(gOwner) & AGENT_SITTING))" in tips,
      "tips: seated in any people camera, the tip says Page Up / Down")
check('"Me\\nwalk: it follows · stand: it holds the picture",' in tips, "tips: Framing › Me's tip (7.0)")
print(f"fit: a tap {STEP * 100:.0f} cm, held {SLOW * 1000:.0f} cm/s rising to {FAST * 1000:.0f} cm/s, up to {LIMIT:.1f} m; Page Up raises the camera, the same on screen and next; "
      f"{SEATS} seats, the ground, standing")
print("fit checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
