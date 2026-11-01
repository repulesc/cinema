import math
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
st = dict(zip(var(h, "strip", "gOpts"), var(h, "strip", "gOptSt")))
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
# 8.7.0: the glide (the default): held close, then round you at the same distance and height. 8.8.1: on the viewer's own
# follow camera (eased every frame, as Tracking; 8.7.0's 20 locked steps a second were choppy in-world): its behindness
# angle narrows a little every half second, and the camera swings round you toward your back
t0 = w.t
G = []
for i in range(60):                                                    # the hold (4 s) and the swing (24 s), sampled
    w.run(0.5)
    G.append((w.t, ana.camera()[0]))
flat = lambda p: vec(p[0] - ana.pos[0], p[1] - ana.pos[1], 0)
S = [(t, p) for t, p in G if t >= t0 + 2.0]                            # once the follow camera has it
R = [B.llVecMag(flat(p)) for t, p in S]
check(h.cam.get("distance") and not h.cam.get("plock") and h.cam.get("bangle", 180) < 180, "the glide: the viewer's follow camera, not a locked one")
check(max(R) - min(R) < 0.05 and max(p[2] for t, p in S) - min(p[2] for t, p in S) < 0.05, "... at one distance and height (%.2f to %.2f m)" % (min(R), max(R)))
steps = [B.llVecDist(S[i][1], S[i + 1][1]) for i in range(len(S) - 1)]
check(max(steps) < 0.2, "... a little at a time, the viewer easing between (largest %.3f m a half second)" % max(steps))
az = lambda p: math.atan2(flat(p)[1], flat(p)[0])
a0, a1 = az(S[0][1]), az(S[-1][1])
arc = abs((a1 - a0 + math.pi) % (2 * math.pi) - math.pi)
check(0.5 < arc < 0.9, "... about 40 degrees round you (%.0f)" % math.degrees(arc))
bk = B.llRot2Fwd(ana.rot); ba = math.atan2(-bk[1], -bk[0])
off = lambda a: abs((a - ba + math.pi) % (2 * math.pi) - math.pi)
check(off(a1) < off(a0), "... toward your back (%.0f to %.0f degrees from behind you)" % (math.degrees(off(a0)), math.degrees(off(a1))))
for t, p in S[::6]: ok_cam(w, ana, p, "Glide")
# Settings › Motion › Reveal (8.1.0): rising and pulling back on the viewer's follow camera, on the side the first cut chose
h.lsd["cin.drift"] = ("reveal", PASS); h.send(7330, "drift")
ana.touch(opt_part(h, "DRIFT")); w.run(1.5)
C = []
for i in range(90):
    w.run(1)
    C.append(ana.camera()[0])
check(h.cam.get("distance") and h.cam.get("bangle") == 180 and not h.cam.get("plock"), "Reveal: the viewer's follow camera, free to stay on its side")
for p in C[::10]: ok_cam(w, ana, p, "Drift")
far = max(B.llVecDist(p, ana.pos) for p in C)
check(far > 12, "alone: the Reveal pulls out (%.1f m)" % far)
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
st = dict(zip(var(h2, "strip", "gOpts"), var(h2, "strip", "gOptSt")))
check(var(h2, "scenic", "gLocal") == 1 and st.get("FAR") == "dim" and st.get("ROOM") == "", "indoors: FAR dim, ROOM open (%r)" % st)
inside = lambda p: 100 < p[0] < 112 and 100 < p[1] < 110 and 30 < p[2] < 34
for band in ("ROOM", "NEAR", "DRIFT", "FAR"):
    amy.touch(opt_part(h2, band)); w2.run(1)
    t0 = w2.t
    w2.run(40)
    C = cams(h2, t0)
    check(C and all(inside(p) for t, p, f in C), "indoors, %s: every camera inside the room (%s)" % (band, [tuple(round(x, 1) for x in p) for t, p, f in C if not inside(p)][:3]))
no_errors(w2, "room")

# ---- a boat's cabin (8.5.10, in-world): a small closed space, 3 x 2.4 m, its roof 2.4 m over the deck, above the water.
# Drift pulled back out through the walls (its follow camera keeps 1.8 m at least: more than the cabin has)
w3 = World()
w3.boxes += room(150, 150, 30.0, 153, 152.4, 2.4)
bo, h3 = hud(w3, "Bo", pos=(151.5, 151.2, 30.95))
bo.double_tap(); w3.run(1)
bo.touch("t12 s3"); w3.run(3)
st = dict(zip(var(h3, "scenic", "gLocal") and var(h3, "strip", "gOpts") or [], var(h3, "strip", "gOptSt")))
check(var(h3, "scenic", "gLocal") == 1 and st.get("ROOM") == "" and st.get("FAR") == "dim", "the cabin is a room: ROOM open, FAR dim (%r)" % st)
check(var(h3, "scenic", "gTight") == 1, "a small closed space: Drift holds still views (no pulling back into the walls)")
cabin = lambda p: 150 < p[0] < 153 and 150 < p[1] < 152.4 and 30 < p[2] < 32.4
for band in ("DRIFT", "ROOM", "NEAR"):
    bo.touch(opt_part(h3, band)); w3.run(1)
    t0 = w3.t
    w3.run(40)
    C = cams(h3, t0)
    check(C and all(cabin(p) for t, p, f in C), "the cabin, %s: every camera inside it (%s)" % (band, [tuple(round(x, 1) for x in p) for t, p, f in C if not cabin(p)][:3]))
no_errors(w3, "cabin")

# ---- a dim option does nothing (8.5.10: ROOM, dim outdoors, still switched the view) -------------------------------------
w4 = World()
cy, h4 = hud(w4, "Cy")
cy.double_tap(); w4.run(1)
cy.touch("t12 s3"); w4.run(3)
b0 = var(h4, "scenic", "gBand")
cy.touch(opt_part(h4, "ROOM")); w4.run(2)
check(var(h4, "scenic", "gLocal") == 0 and var(h4, "scenic", "gBand") == b0, "outdoors, a tap on the dim ROOM: nothing (band %r, was %r)" % (var(h4, "scenic", "gBand"), b0))
no_errors(w4, "dim")
done("scenic_emu")
