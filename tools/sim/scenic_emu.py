"""Scenic (8.0), on the REAL scripts: still frames with a clean cut about every 15 s (Near, Far), Drift moving
continuously and starting close, every camera within 60 m of you, inside the region, above the ground and the water,
never inside a build's walls; indoors every band stays in the room (FAR dim, Room views inside the walls), outdoors ROOM
is dim; Drift stays near (under about 8 m) while anyone is within 10 m; the lit tap gives the next view now."""
from emu_util import *

def cams(h, since):
    return [(t, p, f) for (t, by, p, f) in h.cam.get("log", []) if t >= since and p is not None]

def ok_cam(w, av, p, where, limit=60.0):
    check(B.llVecDist(vec(p[0], p[1], 0), vec(av.pos[0], av.pos[1], 0)) <= limit + 0.5, "%s: camera %.1f m from you" % (where, B.llVecDist(p, av.pos)))
    check(0 <= p[0] <= 256 and 0 <= p[1] <= 256, "%s: camera outside the region %s" % (where, p))
    check(p[2] > w.ground + 0.3 and p[2] > w.water, "%s: camera under the ground or water %s" % (where, p))
    check(not any(b.inside(p) for b in w.boxes), "%s: camera inside a wall %s" % (where, p))

# ---- outdoors: Far, still frames ---------------------------------------------------------------------------------------
w = World()
w.boxes += [Box((150, 120, 20, 160, 125, 30), "house"), Box((100, 140, 20, 104, 160, 26), "shed")]
ana, h = hud(w, pos=(128, 128, 21))
ana.double_tap(); w.run(1)
ana.touch("t12 s3"); w.run(2)
st = dict(zip(var(h, "screen", "gOpts"), var(h, "screen", "gOptSt")))
check(st.get("ROOM") == "dim" and st.get("FAR") == "", "outdoors: ROOM dim, FAR open (%r)" % st)
ana.touch(opt_part(h, "FAR")); w.run(1)
t0 = w.t
w.run(95)
C = cams(h, t0)
gaps = [b[0] - a[0] for a, b in zip(C, C[1:])]
check(len(C) >= 5 and all(10.0 <= g <= 20.0 for g in gaps), "Far: a cut about every 15 s (%s)" % [round(g, 1) for g in gaps])
for t, p, f in C: ok_cam(w, ana, p, "Far")
check(max(B.llVecDist(p, ana.pos) for t, p, f in C) > 15, "Far reaches out (furthest %.1f m)" % max(B.llVecDist(p, ana.pos) for t, p, f in C))
check(var(h, "scenic", "gLocal") == 0, "outdoors")
n = len(cams(h, 0))
ana.touch("t12 s3"); w.run(1)
check(len(cams(h, 0)) > n, "the lit tap: the next view now")
no_errors(w, "far")

# ---- Near ----------------------------------------------------------------------------------------------------------------
ana.touch(opt_part(h, "NEAR")); w.run(1)
t0 = w.t
w.run(50)
for t, p, f in cams(h, t0): ok_cam(w, ana, p, "Near", limit=8.0)
check(lsd(h, "scn") == "1", "Near is kept")
no_errors(w, "near")

# ---- Drift: it moves, starts close, stays near people --------------------------------------------------------------
ana.touch(opt_part(h, "DRIFT")); w.run(1.5)
first = cams(h, w.t - 1.5)[0][1]
check(B.llVecDist(first, ana.pos) < 7, "Drift starts close (%.1f m)" % B.llVecDist(first, ana.pos))
t0 = w.t
w.run(90)
C = cams(h, t0)
check(len(C) > 100, "Drift moves continuously (%d steps)" % len(C))
for t, p, f in C[::10]: ok_cam(w, ana, p, "Drift")
far = max(B.llVecDist(p, ana.pos) for t, p, f in C)
check(far > 12, "alone: Drift pulls out (%.1f m)" % far)
ben = w.avatar("Ben", (132, 130, 21))
w.run(20)
t0 = w.t
w.run(60)
far = max(B.llVecDist(vec(p[0], p[1], 0), vec(ana.pos[0], ana.pos[1], 0)) for t, p, f in cams(h, t0))
check(far <= 8.5, "someone within 10 m: Drift stays near (%.1f m)" % far)
no_errors(w, "drift")

# ---- the region's edge ----------------------------------------------------------------------------------------------------
ana.teleport((4, 4, 21)); ana.touch(opt_part(h, "FAR")); w.run(1)
t0 = w.t
w.run(60)
for t, p, f in cams(h, t0): ok_cam(w, ana, p, "edge")
no_errors(w, "edge")

# ---- indoors: the room -----------------------------------------------------------------------------------------------------
w2 = World()
w2.boxes += room(100, 100, 30.0, 112, 110, 4.0)                    # a 12 x 10 m room, its floor at 30 m
amy, h2 = hud(w2, "Amy", pos=(104, 104, 30.95))
amy.double_tap(); w2.run(1)
amy.touch("t12 s3"); w2.run(3)
st = dict(zip(var(h2, "screen", "gOpts"), var(h2, "screen", "gOptSt")))
check(var(h2, "scenic", "gLocal") == 1 and st.get("FAR") == "dim" and st.get("ROOM") == "", "indoors: FAR dim, ROOM open (%r)" % st)
inside = lambda p: 100 < p[0] < 112 and 100 < p[1] < 110 and 30 < p[2] < 34
for band in ("ROOM", "NEAR", "DRIFT", "FAR"):
    amy.touch(opt_part(h2, band)); w2.run(1)
    t0 = w2.t
    w2.run(40)
    C = cams(h2, t0)
    check(C and all(inside(p) for t, p, f in C), "indoors, %s: every camera inside the room (%s)" % (band, [tuple(round(x, 1) for x in p) for t, p, f in C if not inside(p)][:3]))
no_errors(w2, "room")
done("scenic_emu")
