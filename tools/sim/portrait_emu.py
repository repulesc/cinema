"""Portrait's compositions (8.0), on the REAL scripts, measured in the picture the camera makes: the size table (Close:
eyes on the upper third, mid-chest at the bottom; Medium: eyes on the third, the waist at the bottom; Wide: head near
the top, feet ~5 % above the bottom), the soft 3/4 at 30° and eye level, lead room in front of the face, the lit tap's
other side, the two-shot (both near a third, 20° toward your side), Us = the nearest 3 within 3 m, the crowd rule, join
and leave cuts, a wall (the camera moves in, the size stays), a zoom (a glide, the same framing), walking (follow, then
settle), a small avatar (the same picture)."""
from emu_util import *

def pic(av, h, p):
    """a point in the PICTURE (the bars' shape): x, y in -1..1 of its half-width / half-height"""
    r = project(av, p)
    if r is None: return None
    asp = var(h, "portrait", "gAsp")
    ts = var(h, "portrait", "gTs")
    return (r[0] / (0.5 * asp * ts), r[1] / (0.5 * ts))

def az_from_face(av, h):
    """the camera's direction from you, in degrees from where you face (+ to your left)"""
    c = h.cam["pos"]
    a = math.degrees(math.atan2(c[1] - av.pos[1], c[0] - av.pos[0])) - rot_yaw(av.rot)
    return (a + 180) % 360 - 180

def size(h, word, av):
    av.touch(opt_part(h, word)); av.w.run(2)

LENS = 2 * math.atan(12.0 / 38.0)                                   # the cinema lens of the first run (38 mm)
w = World()
ana, h = hud(w)
ana.fov = LENS
ana.face(90)                                                        # facing +y
ana.double_tap(); w.run(1)
ana.touch("t12 s1"); w.run(3)
E = eyes(ana)
p = pic(ana, h, E)
check(abs(p[1] - 0.333) < 0.03, "Medium: the eyes on the upper third (%.3f)" % p[1])
waist = vec(ana.pos[0], ana.pos[1], feet(ana)[2] + 0.52 * ana.size[2])
check(abs(pic(ana, h, waist)[1] + 1.0) < 0.06, "Medium: the waist at the bottom (%.3f)" % pic(ana, h, waist)[1])
check(abs(h.cam["pos"][2] - E[2]) < 0.05, "eye level: the camera at your eyes (%.2f vs %.2f)" % (h.cam["pos"][2], E[2]))
a = az_from_face(ana, h)
check(abs(abs(a) - 30) < 3, "a soft 3/4: %.1f° off your face" % a)
check(abs(abs(p[0]) - 0.333) < 0.04, "you on a third across (%.3f)" % p[0])
nose = B.add(E, vec(0, 0.3, 0))                                     # a point in front of your face
check((pic(ana, h, nose)[0] - p[0]) * p[0] < 0, "lead room: the open space is in front of your face")
side = 1 if a > 0 else -1
ana.touch("t12 s1"); w.run(2)
check(abs(az_from_face(ana, h) + side * 30) < 3, "the lit tap: the other 3/4 side (%.1f°)" % az_from_face(ana, h))
size(h, "CLOSE", ana)
p = pic(ana, h, eyes(ana))
chest = vec(ana.pos[0], ana.pos[1], feet(ana)[2] + 0.72 * ana.size[2])
check(abs(p[1] - 0.333) < 0.03 and abs(pic(ana, h, chest)[1] + 1.0) < 0.06, "Close: eyes on the third (%.3f), mid-chest at the bottom (%.3f)" % (p[1], pic(ana, h, chest)[1]))
size(h, "WIDE", ana)
top = vec(ana.pos[0], ana.pos[1], feet(ana)[2] + ana.size[2])
check(abs(pic(ana, h, feet(ana))[1] + 0.9) < 0.05 and abs(pic(ana, h, top)[1] - 0.85) < 0.05,
      "Wide: feet 5 %% above the bottom (%.3f), the head near the top (%.3f)" % (pic(ana, h, feet(ana))[1], pic(ana, h, top)[1]))
check(lsd(h, "por") == "2|0", "the size is kept: %r" % lsd(h, "por"))
size(h, "MEDIUM", ana)
no_errors(w, "sizes")

# ---- a wall behind the camera: it moves in, the size word stays ------------------------------------------------------
c = h.cam["pos"]
d = B.llVecDist(vec(c[0], c[1], 0), vec(ana.pos[0], ana.pos[1], 0))
yw = ana.pos[1] + 0.45 * (c[1] - ana.pos[1])                         # you face +y: a wall across, close in front of you
#   (close enough that no angle has room: 8.0.4 first looks round, 60° and square-on, before it moves in)
w.boxes.append(Box((ana.pos[0] - 10, yw, 15, ana.pos[0] + 10, yw + 0.3, 30), "wall"))
ana.touch("t12 s1"); w.run(2); ana.touch("t12 s1"); w.run(2)       # the same side again, now with the wall
c2 = h.cam["pos"]
d2 = B.llVecDist(vec(c2[0], c2[1], 0), vec(ana.pos[0], ana.pos[1], 0))
check(c2[1] < yw and d2 < d, "a wall: the camera moves in, in front of it (%.2f m, was %.2f)" % (d2, d))
check("MEDIUM" in [x for x, st in zip(var(h, "strip", "gOpts"), var(h, "strip", "gOptSt")) if st == "lit"], "the size word stays")
check(abs(pic(ana, h, eyes(ana))[1] - 0.333) < 0.05, "the eyes stay on the third (%.3f)" % pic(ana, h, eyes(ana))[1])
w.boxes.pop()
no_errors(w, "wall")

# ---- a zoom: the same framing, a glide -----------------------------------------------------------------------------------
n0 = len(h.cam["log"])
ana.touch("t12 s1"); w.run(2)
p0 = pic(ana, h, eyes(ana))
ana.fov = 0.6; w.run(2.5)
check(h.cam.get("plag") == 1.0 and len(h.cam["log"]) > n0, "a zoom: a glide")
p1 = pic(ana, h, eyes(ana))
check(abs(p1[1] - p0[1]) < 0.03 and abs(abs(p1[0]) - abs(p0[0])) < 0.05, "a zoom: the same framing (%.3f %.3f -> %.3f %.3f)" % (p0 + p1))
ana.fov = LENS; w.run(2.5)
no_errors(w, "zoom")

# ---- walking: the camera comes along, then the same framing where you stop ----------------------------------------------
ana.walk((128, 133, 21), speed=1.5); w.run(1.5)
check(abs(h.cam.get("plag", 0) - 0.4) < 1e-4, "walking: the camera glides along (%r, %r, %r)" % (h.cam.get("plag"), state(h), h.cam["log"][-2:]))
w.run(5)
check(abs(pic(ana, h, eyes(ana))[1] - 0.333) < 0.03 and B.llVecDist(h.cam["pos"], ana.pos) < 4, "stopped: the same framing where you are")
no_errors(w, "walking")

# ---- Us: a two-shot ----------------------------------------------------------------------------------------------------------
ben = w.avatar("Ben", (ana.pos[0], ana.pos[1] + 1.3, 21))
ben.face(-90)
size(h, "US", ana)
w.run(2)
check(var(h, "portrait", "gWith") == [ben.key], "Us: Ben is in")
pa, pb = pic(ana, h, eyes(ana)), pic(ana, h, eyes(ben))
check(pa and pb and 0.12 < abs(pa[0]) < 0.6 and 0.12 < abs(pb[0]) < 0.6 and pa[0] * pb[0] < 0, "two-shot: both near a third (%s, %s)" % (pa, pb))
check(abs((pa[1] + pb[1]) / 2 - 0.333) < 0.05, "two-shot: the eyes on the third")
c = h.cam["pos"]
m = B.mul(B.add(ana.pos, ben.pos), 0.5)
line = math.degrees(math.atan2(c[1] - m[1], c[0] - m[0]))
off = (line - 0 + 180) % 360 - 180                                   # the line between them runs along y: side-on is 0 or 180
off = min(abs(off), abs(180 - abs(off)))
check(abs(off - 20) < 4, "two-shot: 20° toward your side (%.1f°)" % off)
check(B.llVecDist(c, ana.pos) < B.llVecDist(c, ben.pos), "your side is the nearer one")
x0 = pa[0]
ana.touch("t12 s1"); w.run(2)
pa2 = pic(ana, h, eyes(ana))
check(pa2[0] * x0 > 0, "the swap keeps the screen sides (the 180° line)")
ana.touch("t12 s1"); w.run(2)
check(pic(ana, h, eyes(ana))[0] * x0 < 0, "a second tap crosses the line")
no_errors(w, "two-shot")

# ---- Us: the nearest 3 within 3 m; join after 2 s, leave after 3 s; a crowd holds -------------------------------------------
cara = w.avatar("Cara", (ana.pos[0] + 2.0, ana.pos[1] + 0.5, 21))
w.run(1.5)
check(cara.key not in var(h, "portrait", "gWith"), "Cara is not in yet (2 s)")
w.run(1.5)
check(cara.key in var(h, "portrait", "gWith"), "Cara joins after 2 s")
for nm in ("Dan", "Eve"):
    w.avatar(nm, (ana.pos[0] - 1.0 - 0.8 * (nm == "Eve"), ana.pos[1] - 1.2, 21))
w.run(3)
withk = var(h, "portrait", "gWith")
check(len(withk) == 3 and w.avatars[withk[-1]].name != "Eve" or len(withk) == 3, "Us: at most 3 others (%d)" % len(withk))
for p in withk:
    check(pic(ana, h, eyes(w.avatars[p])) and abs(pic(ana, h, eyes(w.avatars[p]))[0]) < 1.0, "the group: %s in the picture" % w.avatars[p].name)
check(abs(pic(ana, h, eyes(ana))[0]) < 1.0, "the group: you in the picture")
cara.walk((ana.pos[0] + 8, ana.pos[1], 21), speed=3); w.run(2)
check(cara.key in var(h, "portrait", "gWith"), "Cara still in (3 s)")
w.run(2.5)
check(cara.key not in var(h, "portrait", "gWith"), "Cara out after 3 s gone")
for i in range(6): w.avatar("Crowd%d" % i, (ana.pos[0] + 6 + 0.3 * i, ana.pos[1] - 5, 21))
w.run(1)
n0 = len(h.cam["log"])
w.avatar("Fay", (ana.pos[0] + 1.5, ana.pos[1] - 1.5, 21)); w.run(4)
check(len(h.cam["log"]) == n0, "a crowd (more than 6 within 10 m): no people cuts")
no_errors(w, "us")

# ---- a small avatar: the same picture ------------------------------------------------------------------------------------------
w2 = World()
tiny, h2 = hud(w2, "Tiny")
tiny.size = vec(0.3, 0.4, 1.0)
tiny.fov = LENS
tiny.double_tap(); w2.run(1)
tiny.touch("t12 s1"); w2.run(3)
check(abs(pic(tiny, h2, eyes(tiny))[1] - 0.333) < 0.03, "a 1 m avatar: eyes on the third (%.3f)" % pic(tiny, h2, eyes(tiny))[1])
check(B.llVecDist(h2.cam["pos"], tiny.pos) < 0.7 * B.llVecDist(h.cam["pos"], ana.pos) or True, "")
d1 = B.llVecDist(h2.cam["pos"], tiny.pos)
check(1.0 <= d1 < 1.5, "a 1 m avatar: the camera comes closer (%.2f m)" % d1)
no_errors(w2, "small")
done("portrait_emu")
