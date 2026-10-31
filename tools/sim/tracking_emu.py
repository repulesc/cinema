"""Tracking (8.0), on the REAL scripts: the viewer's own follow camera (FOLLOW), the three looks (Shoulder 1.6 m,
Film 3.5 m a little low, Classic 3 m above), L · R the side of the picture you walk on, a steadicam lag, running pulls
back 30 %, a wall behind you pulls the camera in (never through it), a small closed room gives its corner (panning
with you) and leaving it gives you the camera behind you again, standing still 5 s lights PORTRAIT once, the lit tap
goes back into the look, everything scales with your size."""
import math
from emu_util import *

w = World()
ana, h = hud(w)
h.lsd["cin.feel"] = ("smooth", PASS)                                 # the steadicam feel (Snappy is the default, 8.0.8)
ana.face(0)
ana.double_tap(); w.run(1)
ana.touch("t12 s0"); w.run(2)
c = h.cam
check(not c.get("plock") and abs(c["distance"] - 3.6) < 0.05 and abs(c["pitch"] - 6.0) < 0.01, "Film (8.7.0): 3.6 m, looking 6 deg down (%r, %r)" % (c.get("distance"), c.get("pitch")))
eye = ana.pos[2] + (0.935 - 0.5) * ana.size[2]
cp = ana.camera()[0]
check(cp[2] > eye, "... the camera above your eyes, no longer below your chest (camera %.2f, eyes %.2f)" % (cp[2], eye))
check(abs(c["offset"][0]) < 1e-6, "standing: no lead room (%r)" % (tuple(c["offset"]),))
check(c["blag"] > 0.4 and c["plag"] > 0.3, "a steadicam lag (behind %.2f s, position %.2f s)" % (c["blag"], c["plag"]))
p = project(ana, eyes(ana))
check(p and p[0] > 0.05, "R: you on the right of the picture (%.3f)" % (p[0] if p else -9))
ana.touch(opt_part(h, "L")); w.run(1)
p = project(ana, eyes(ana))
check(p and p[0] < -0.05, "L: you on the left (%.3f)" % (p[0] if p else 9))
ana.touch(opt_part(h, "SHOULDER")); w.run(1)
check(abs(h.cam["distance"] - 2.2) < 0.05 and abs(h.cam["pitch"] - 8.0) < 0.01, "Shoulder (8.7.0): 2.2 m, 8 deg down")
ana.touch(opt_part(h, "CLASSIC")); w.run(1)
check(abs(h.cam["distance"] - 4.2) < 0.05 and h.cam["pitch"] > 15 and abs(h.cam["offset"][1]) < 1e-6, "Classic (8.7.0): 4.2 m, from above, centred")
check(lsd(h, "trk") == "2|0", "kept: %r" % lsd(h, "trk"))
ana.touch(opt_part(h, "FILM")); w.run(1)
no_errors(w, "looks")

# ---- running pulls back ---------------------------------------------------------------------------------------------
ana.walk((200, 128, 21), speed=5.0); w.run(1.5)
check(abs(h.cam["distance"] - 3.6 * 1.3) < 0.1, "running: 30 %% further (%.2f)" % h.cam["distance"])
check(h.cam["offset"][0] > 0.3, "moving: lead room, the frame looks ahead of you (8.7.0; %r)" % (tuple(h.cam["offset"]),))
w.run(20)
check(abs(h.cam["distance"] - 3.5) < 0.1, "stopped: back in (%.2f)" % h.cam["distance"])
no_errors(w, "running")

# ---- a wall behind you: in, never through it ------------------------------------------------------------------------
ana.pos = vec(128, 128, 21); ana.face(0); w.run(1)
w.boxes.append(Box((126.3, 120, 15, 126.6, 136, 30), "wall"))       # 1.7 m behind you
ana.touch("t12 s0"); w.run(2)
check(h.cam["distance"] < 1.5, "a wall 1.7 m behind: the camera pulls in (%.2f)" % h.cam["distance"])
cam = ana.camera()[0]
check(cam[0] > 126.6, "never through the wall (camera at x %.2f)" % cam[0])
w.boxes.pop()
w.run(1); ana.touch("t12 s0"); w.run(2)
check(abs(h.cam["distance"] - 3.5) < 0.1, "the wall gone: 3.5 m again")
no_errors(w, "wall")

# ---- a small closed room: its corner, panning with you; out of it, behind you again ----------------------------------
w.boxes += room(140, 140, 20.0, 143.5, 143.5, 3.0, door=(141.2, 142.3))
ana.teleport((141.7, 141.7, 21.0)); w.run(5)
check(h.cam.get("plock") and not h.cam.get("flock", True), "a small room: a corner, the focus on you (%r)" % {k: h.cam.get(k) for k in ("plock", "flock")})
cp = h.cam.get("pos", vec(0, 0, 0))
check(140 < cp[0] < 143.5 and 140 < cp[1] < 143.5 and 20 < cp[2] < 23, "the corner is inside the room (%s)" % (cp,))
check(B.llVecDist(cp, ana.pos) > 1.2, "the corner is across the room from you")
ana.walk((135, 141.7, 21.0), speed=1.5); w.run(6)
check(not h.cam.get("plock") and h.cam.get("distance"), "out of the room: behind you again")
no_errors(w, "room")

# ---- standing still: PORTRAIT lights once; the lit tap; your size ---------------------------------------------------------
w.run(6)
check(var(h, "strip", "gHint") == "portrait" or var(h, "tracking", "gHinted") == 1, "standing 5 s: PORTRAIT lights")
w.run(6)
check(var(h, "strip", "gHint") == "", "... once")
n = len(h.cam["log"])
ana.touch("t12 s0"); w.run(1)
check(len(h.cam["log"]) > n and not h.cam.get("plock"), "the lit tap: back into the look behind you")
ana.size = vec(0.3, 0.4, 0.9); ana.touch("t12 s0"); w.run(1)
check(abs(h.cam["distance"] - 3.6 * 0.5) < 0.05, "a 0.9 m avatar: half the distance (%.2f)" % h.cam["distance"])
no_errors(w, "still")

# ---- a teleport (8.5.10, in-world: the camera drifted in from afar): the first frame there snaps, then eases again ------
ana.size = vec(0.45, 0.6, 1.9); ana.touch("t12 s0"); w.run(2)
ana.teleport((60, 60, 21)); w.run(2.2)
check(h.cam.get("plag") == 0.0 and h.cam.get("distance"), "after the teleport: the follow camera there at once (lag %r)" % h.cam.get("plag"))
w.run(1)
check(h.cam.get("plag", 0) > 0.0, "... then its easing again (lag %r)" % h.cam.get("plag"))
no_errors(w, "teleport")

# ---- your lens, always known (8.5.10): zooming shows it for a moment on the note plate, as a camera shows its focal length
t = w.t
ana.fov = 2 * math.atan(12.0 / 26.0); w.run(1.5)                     # Ctrl+8: the 26 mm stop
check(any(n == "Lens 26 mm" for n in ana.notes(t)), "zooming out: \"Lens 26 mm\" (%r)" % ana.notes(t)[-2:])
t = w.t
w.run(5)
check(not any("Lens" in n for n in ana.notes(t)), "... and nothing while it stays")
done("tracking_emu")
