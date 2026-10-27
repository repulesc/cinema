"""Fixed (8.0), on the REAL scripts: your own framing kept. Nothing kept: your camera and "Frame it", and a framing
held still 1 s is kept by itself; a kept view is never replaced silently (KEEP NEW for 5 s, a tap replaces it, ignored
it was just a look); View A / B per place (region + parcel); walking off it comes along and settles at the same angle on
you; a zoom dollies the camera; seats keep a view per furniture and spot (a new spot or another piece of furniture is a
new "Frame it"), the least used furniture is forgotten past 48; FORGET SEAT with UNDO for 3 s; ground sits per place
and spot; TAKE BACK; standing up returns to the shot you had before you sat."""
from emu_util import *

def frame_it(av, w, to, focus=None):
    """Alt-click to a framing and hold still: let go of Alt (Esc) once Take 12 locked it"""
    av.alt_orbit(to=to, focus=focus or B.add(av.pos, vec(0, 0, 0.6)))
    w.run(2.5)

def opts(h): return list(zip(var(h, "strip", "gOpts"), var(h, "strip", "gOptSt")))
def words(h): return [x for x, st in opts(h)]
def place_key(h):
    return [k for k in h.lsd if k.startswith("cin.view.")]

w = World(parcels=[((0, 0, 128, 256), "aaaaaaaa-0000-0000-0000-000000000001"), ((128, 0, 256, 256), "bbbbbbbb-0000-0000-0000-000000000002")])
ana, h = hud(w, pos=(140, 128, 21))
ana.face(0)
ana.double_tap(); w.run(1)

# ---- nothing kept: frame it ----------------------------------------------------------------------------------------------
ana.touch("t12 s2"); w.run(2.5)
check(var(h, "core", "gFree") == 1 and not h.cam.get("active"), "nothing kept: your own camera")
check(any(n.startswith("Frame it with Alt-click") for n in ana.notes()), "the note says so")
check(not place_key(h), "nothing kept until you frame it")
A = vec(143, 126, 22)
frame_it(ana, w, A)
check(len(place_key(h)) == 1 and var(h, "core", "gFree") == 0, "framed and still 1 s: kept (%r)" % place_key(h))
check(h.cam.get("active") and B.llVecDist(h.cam["pos"], A) < 0.05, "Take 12 holds it (%s)" % (h.cam.get("pos"),))
ana.esc(); w.run(1)
check(state(h)[0] == "film" and B.llVecDist(ana.camera()[0], A) < 0.05, "Esc: the kept view stays on screen")
no_errors(w, "frame it")

# ---- a kept view is never replaced silently -----------------------------------------------------------------------------
w.run(3)
B2 = vec(137, 130, 23)
frame_it(ana, w, B2); w.run(1)
check(state(h)[0] == "held", "Alt-click away from the kept view: held")
check(("KEEP NEW", "accent") in opts(h), "KEEP NEW lights (%r)" % opts(h))
w.run(5.5)
check("KEEP NEW" not in words(h), "ignored 5 s: it was just a look")
ana.touch("t12 s2"); w.run(0.5); ana.esc(); w.run(2)
check(state(h)[0] == "film" and B.llVecDist(h.cam["pos"], A) < 0.1, "the lit tap: the kept view back")
w.run(3)
frame_it(ana, w, B2); w.run(1)
ana.touch(opt_part(h, "KEEP NEW")); w.run(0.5); ana.esc(); w.run(2)
check(state(h)[0] == "film" and B.llVecDist(h.cam["pos"], B2) < 0.1, "KEEP NEW: the new framing is kept and held (%s)" % (h.cam.get("pos"),))
check("Kept." in ana.notes(), "Kept.")
no_errors(w, "keep new")

# ---- View B ----------------------------------------------------------------------------------------------------------------
ana.touch(opt_part(h, "VIEW B")); w.run(2.5)
check(var(h, "core", "gFree") == 1 and ("VIEW B", "lit") in opts(h), "View B, empty: frame it")
C3 = vec(140, 133, 21.8)
frame_it(ana, w, C3); ana.esc(); w.run(1)
ana.touch(opt_part(h, "VIEW A")); w.run(1)
check(B.llVecDist(h.cam["pos"], B2) < 0.1, "View A: a cut to it")
ana.touch(opt_part(h, "VIEW B")); w.run(1)
check(B.llVecDist(h.cam["pos"], C3) < 0.1, "View B: a cut to it")
ana.touch(opt_part(h, "VIEW A")); w.run(1)
no_errors(w, "view b")

# ---- walking off: it comes along, then the same angle on you -------------------------------------------------------------
rel = B.sub(h.cam["pos"], ana.pos)
ana.walk((140, 120, 21), speed=1.5); w.run(2)
check(abs(h.cam.get("plag", 0) - 0.4) < 1e-4, "walking: the camera comes along")
w.run(6)
r2 = B.sub(h.cam["pos"], ana.pos)
yaw = math.radians(rot_yaw(ana.rot))
rr = (rel[0] * math.cos(yaw) - rel[1] * math.sin(yaw), rel[0] * math.sin(yaw) + rel[1] * math.cos(yaw), rel[2])
check(B.llVecDist(r2, vec(*rr)) < 0.2, "stopped: the same angle on you, turned with you (%s vs %s)" % (r2, rr))
no_errors(w, "walking")

# ---- per place --------------------------------------------------------------------------------------------------------------
ana.teleport((100, 128, 21)); w.run(4)
check(var(h, "core", "gFree") == 1, "another parcel: nothing kept, frame it")
ana.teleport((140, 128, 21)); ana.face(0); w.run(4)
check(var(h, "core", "gFree") == 0 and h.cam.get("active"), "back: this place's View A")
no_errors(w, "places")

# ---- a zoom: the camera dollies, the picture stays ---------------------------------------------------------------------
w.run(3)
d0 = B.llVecDist(h.cam["pos"], h.cam["focus"])
ana.fov = 0.6; w.run(1)
check(abs(h.cam.get("plag", 0) - 1.5) < 1e-4 and B.llVecDist(h.cam["pos"], h.cam["focus"]) > d0 * 1.3, "a zoom: the camera dollies back")
ana.fov = 1.047198; w.run(2)
no_errors(w, "zoom")

# ---- seats: per furniture and spot ------------------------------------------------------------------------------------
sofa = w.furniture("Sofa", (145, 128, 20.5))
ana.sit_on(sofa, at=(0, -0.5, 0.6)); w.run(3)
check(var(h, "core", "gState") == "film" and var(h, "core", "gFree") == 1, "a new seat: frame it")
check(words(h) == ["FORGET SEAT", "LET GO"] and ("FORGET SEAT", "dim") in opts(h), "seated: FORGET SEAT (dim, nothing kept) · LET GO")
S1 = vec(147, 126, 22)
frame_it(ana, w, S1); ana.esc(); w.run(1)
check(("seat." + str(sofa.key)) and lsd(h, "seat." + str(sofa.key)) != "", "kept for this sofa")
check(("FORGET SEAT", "") in opts(h), "FORGET SEAT lights up")
ana.stand(); ana.pos = vec(140, 128, 21); w.run(3)
check(state(h) == ("film", "fixed") and var(h, "fixed", "gCtx") == "stand", "standing up from Fixed: this place's view")
sofa.pos = vec(150, 130, 20.5)                                       # the sofa moved: its view comes with it
ana.sit_on(sofa, at=(0, -0.5, 0.6)); w.run(3)
want = B.add(S1, vec(5, 2, 0))
check(B.llVecDist(h.cam["pos"], want) < 0.1, "the same spot: its view, moved with the sofa (%s, want %s)" % (h.cam.get("pos"), want))
ana.sit_on(sofa, at=(0, 0.6, 0.6)); w.run(3)
check(var(h, "core", "gFree") == 1, "another spot on it: frame it")
sofa2 = w.furniture("Sofa", (160, 128, 20.5), creator=sofa.creator)
ana.sit_on(sofa2, at=(0, -0.5, 0.6)); w.run(3)
check(var(h, "core", "gFree") == 1, "the same model elsewhere: frame it")
ana.sit_on(sofa, at=(0, -0.5, 0.6)); w.run(3)
ana.touch(opt_part(h, "FORGET SEAT")); w.run(1)
check(("UNDO", "accent") in opts(h) and var(h, "core", "gFree") == 1, "FORGET SEAT: forgotten, UNDO for 3 s")
ana.touch(opt_part(h, "UNDO")); w.run(1)
check(var(h, "core", "gFree") == 0 and B.llVecDist(h.cam["pos"], want) < 0.1, "UNDO: the view is back")
ana.touch(opt_part(h, "FORGET SEAT")); w.run(4)
check("UNDO" not in words(h) and ("FORGET SEAT", "dim") in opts(h), "3 s later: forgotten for good")
no_errors(w, "seats")

# ---- before you sat: standing up returns to it --------------------------------------------------------------------------
ana.stand(); ana.pos = vec(140, 128, 21); w.run(2)
ana.touch("t12 s1"); w.run(3)
ana.sit_on(sofa, at=(0, -0.5, 0.6)); w.run(2)
ana.touch("t12 s2"); w.run(3)
check(state(h) == ("film", "fixed"), "seated, Fixed tapped")
ana.stand(); ana.pos = vec(140, 128, 21); w.run(3)
check(state(h) == ("film", "portrait"), "standing up: back to Portrait (%r)" % (state(h),))
no_errors(w, "stand up")

# ---- ground sits: per place and spot --------------------------------------------------------------------------------------
ana.touch("t12 s2"); w.run(3)
ana.sit_ground(); w.run(3)
check(var(h, "core", "gFree") == 1 and words(h) == ["FORGET SEAT"], "a ground sit: frame it; FORGET SEAT only (%r)" % words(h))
G = vec(142, 131, 21.5)
frame_it(ana, w, G); ana.esc(); w.run(1)
ana.stand(); w.run(2)
ana.pos = vec(141, 128.5, 21); ana.sit_ground(); w.run(3)
check(var(h, "core", "gFree") == 0 and B.llVecDist(h.cam["pos"], G) < 0.1, "the same spot (1 m off): its view")
ana.stand(); ana.pos = vec(146, 128, 21); ana.sit_ground(); w.run(3)
check(var(h, "core", "gFree") == 1, "a spot 6 m away: frame it")
ana.stand(); ana.pos = vec(140, 128, 21); w.run(3)
no_errors(w, "ground")

# ---- the least used furniture is forgotten past 48 -------------------------------------------------------------------------
first = None
for i in range(50):
    f = w.furniture("Chair %d" % i, (100 + i, 60, 20.5))
    first = first or f
    ana.sit_on(f); w.run(3.5)
    frame_it(ana, w, B.add(f.pos, vec(2, 1, 1.5))); ana.esc(); w.run(0.5)
    ana.stand(); w.run(1.5)
seats = lsd(h, "seats").split(",")
check(len(seats) == 48 and str(first.key) not in seats and lsd(h, "seat." + str(first.key)) == "", "past 48: the least used is forgotten (%d kept)" % len(seats))
check(var(h, "fixed", "SEATS") == 48, "48 pieces of furniture")
no_errors(w, "eviction")
done("fixed_emu")
