# Show me (7.2), on the REAL scripts (tools/emu): you lie on a bed, your face is far from where Second Life says you
# are (the avatar's root). You Alt-click your face and Alt-drag a little round it; fit.lsl finds the face where the two
# views meet, keeps it for this seat in your own frame, and Me (frame.lsl) and Us (people.lsl) frame that face.
# Checked: the measured face is within a few cm, a turn of the bed turns it with you, a view that does not aim at one
# point is not taken, Me's camera looks at the face from the side it faces, Us puts you where your face is, the camera
# comes back by itself, and /77 showme clear forgets it.
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "emu"))
from world import World, HUD_SCRIPTS, vec, B, Quaternion

ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)
def g(a, n): return next(s for s in a.hud.scripts if s.name == n).g
def add(a, b): return vec(a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return vec(a[0] - b[0], a[1] - b[1], a[2] - b[2])
def dist(a, b): return math.dist(a, b)
def zrot(deg): return B.llEuler2Rot(vec(0, 0, math.radians(deg)))

def lying(yaw=0.0):
    w = World(seed=7)
    a = w.avatar("Ana", (128, 128, 22.4), sitting=True)
    a.rot = zrot(yaw)
    a.wear(HUD_SCRIPTS)
    w.run(5)
    return w, a

def face_of(a, off=(0.55, 0.1, 0.05)):
    """where her face really is: lying, 55 cm along the bed from the avatar's root (the animation puts it there)"""
    return add(a.pos, B.mul(vec(*off), a.rot))

def show(w, a, face, side=(1.2, 0.0, 0.6), turn=25.0):
    """tap > Show me; Alt-click the face from one side, hold still; Alt-drag round it, hold still; Esc"""
    a.tap(); w.run(1); a.click("Show me"); w.run(1)
    c1 = add(face, B.mul(vec(*side), a.rot))
    a.own_cam = (c1, face); a.orbit = True; w.run(1.5)
    r = zrot(turn)
    c2 = add(face, B.mul(sub(c1, face), r))
    a.own_cam = (c2, face); w.run(1.5)
    a.esc(); w.run(3)

# ---- Me (Framing): measured, kept, framed ----------------------------------------------------------------------------
w, a = lying()
a.tap(); w.run(1); a.click("○ Framing"); w.run(3)
check(g(a, "core")["gMode"] == "frame" and a.camera()[2], "Framing › Me runs")
F = face_of(a)
show(w, a, F)
fc = g(a, "fit")
saved = [v for k, v in a.hud.lsd.items() if k.startswith("cin.facec.")]
check(len(saved) == 1 and a.hud.lsd.get("cin.face", ("",))[0] == saved[0][0], "the face is kept for this seat and in use: %s" % saved)
off = vec(*[float(x) for x in saved[0][0].split("|")[0].strip("<>").split(",")]) if saved else vec(0, 0, 0)
check(dist(add(a.pos, B.mul(off, a.rot)), F) < 0.05, "measured within 5 cm: %.3f m" % dist(add(a.pos, B.mul(off, a.rot)), F))
check(not fc["gCal"] and any("Got you" in t[2] for t in a.texts), "Show me ends by itself and says so")
check(g(a, "core")["gState"] == 2 and a.camera()[2], "the camera comes back by itself, framed again: state %d" % g(a, "core")["gState"])
p, foc, _ = a.camera()
check(dist(vec(foc[0], foc[1], 0), vec(F[0], F[1], 0)) < 1.0 and abs(foc[2] - F[2]) < 1.0, "Me looks at the face (focus %s, face %s)" % (foc, F))
facing = B.mul(vec(1.2, 0.0, 0.6), a.rot)
check(B.mul(sub(p, F), facing) > 0.0, "... from the side the face looks to")
check(any("Got you" in t[2] for t in a.texts) and g(a, "fit")["gFit"] == 0.0, "Fit starts level where you showed your face")

# ---- Us: you are where your face is ----------------------------------------------------------------------------------
a.tap(); w.run(1); a.click("◎ Us"); w.run(4)
pe = g(a, "people")
check(dist(vec(pe["gOP"][0], pe["gOP"][1], 0), vec(F[0], F[1], 0)) < 0.05 and abs(pe["gOE"] - F[2]) < 0.05,
      "Us: you are where your face is (%s, eyes %.2f; face %s)" % (pe["gOP"], pe["gOE"], F))

# ---- the bed turned: your face turns with you --------------------------------------------------------------------
w2, b = lying(yaw=90.0)
b.hud.lsd = dict(a.hud.lsd)                                 # the same seat, measured before, now turned
b.tap(); w2.run(1); b.click("○ Framing"); w2.run(4)
F2 = face_of(b)
c = b.hud.lsd.get("cin.face", ("",))[0].split("|")[0]
o2 = vec(*[float(x) for x in c.strip("<>").split(",")]) if c else vec(0, 0, 0)
check(dist(add(b.pos, B.mul(o2, b.rot)), F2) < 0.05, "a turned bed: the face turns with you")

# ---- views that do not aim at one point are not taken ----------------------------------------------------------------
w3, d = lying()
d.tap(); w3.run(1); d.click("○ Framing"); w3.run(3)
d.tap(); w3.run(1); d.click("Show me"); w3.run(1)
Fd = face_of(d)
d.own_cam = (add(Fd, vec(1.2, 0, 0.6)), Fd); d.orbit = True; w3.run(1.5)
d.own_cam = (add(Fd, vec(0.3, 1.2, 0.6)), add(Fd, vec(0, 0, 1.5))); w3.run(1.5)      # aims 1.5 m above: no
check(not any(k.startswith("cin.facec.") for k in d.hud.lsd) and g(d, "fit")["gCal"], "two views that miss each other are not taken")
d.say(77, "showme"); w3.run(1)
check(not g(d, "fit")["gCal"] and g(d, "core")["gState"] == 2, "Show me again stops it; the camera comes back")
# clear
a.say(77, "showme clear"); w.run(1)
check(a.hud.lsd.get("cin.face", ("",))[0] == "" and not any(k.startswith("cin.facec.") and a.hud.lsd[k][0] for k in a.hud.lsd), "/77 showme clear forgets it")
check(not w.errors and not w2.errors and not w3.errors, "no script errors: %s" % (w.errors + w2.errors + w3.errors))
print("show me (real scripts): measured to a few cm lying down, kept per seat and turned with it, Me and Us frame the face")
print("showme checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
