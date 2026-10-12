# Python port of the Friends mode loop in hud/src/cinema_friends.lsl (planF, inFrame, glideTick).
# Scripted walks: checks that a slow walk glides (no snaps, everyone stays in frame), that someone leaving
# the frame triggers a snap within 2 half-second ticks (1 s) to a wider shot that holds everyone, that the
# camera never ends further than 25 m, and that a glide into a wall becomes a cut.
import math
tanV = math.tan(1.047198 / 2); tanH = tanV * 1.778; halfH = math.atan2(tanH, 1.0)
BODY_R, MARGIN, MAXD = 0.35, 1.15, 25.0
def norm(v): m = math.hypot(*v); return (v[0] / m, v[1] / m)
def dot(a, b): return a[0] * b[0] + a[1] * b[1]

class Sim:
    def __init__(s, wall=None):
        s.cam = s.foc = s.V = s.center = None; s.used = 0; s.out = 0; s.glides = s.snaps = s.cuts = 0; s.wall = wall
    def plan(s, owner, friends, mult):
        # friends: positions nearest first; drop the farthest until it fits MAXD
        cnt = len(friends)
        while cnt > 0:
            M = [owner] + friends[:cnt]; n = len(M)
            C = tuple(sum(p[k] for p in M) / n for k in range(2))
            best, A = 0.0, (1.0, 0.0)
            for i in range(n):
                for j in range(i + 1, n):
                    dv = (M[j][0] - M[i][0], M[j][1] - M[i][1])
                    if math.hypot(*dv) > best: best = math.hypot(*dv); A = norm(dv)
            N = (-A[1], A[0]); face = (1.0, 0.0)             # owner faces +x
            if dot(face, N) < 0: N = (-N[0], -N[1])
            need = 1.3 / tanV * MARGIN
            for p in M:
                off = (p[0] - C[0], p[1] - C[1])
                need = max(need, (abs(dot(off, A)) + BODY_R) * MARGIN / tanH + dot(off, N))
            need *= mult
            if need <= MAXD or cnt == 1:
                d = min(max(need, 3.0), MAXD)
                s.cam = (C[0] + N[0] * d, C[1] + N[1] * d); s.V = (-N[0], -N[1]); s.foc = (s.cam[0] + s.V[0] * d, s.cam[1] + s.V[1] * d)
                s.used = cnt; s.center = C; s.out = 0; s.cuts += 1
                return d
            cnt -= 1
        return None
    def in_frame(s, p, k=0.97):
        to = (p[0] - s.cam[0], p[1] - s.cam[1])
        if math.hypot(*to) < 0.1: return True
        fwd = dot(to, s.V); lat = abs(to[0] * s.V[1] - to[1] * s.V[0])
        return fwd > 0.3 and lat <= k * tanH * fwd
    def tick(s, owner, friends, since=5):
        pts = [owner] + friends[:s.used]
        if not all(s.in_frame(p) for p in pts):
            s.out += 1
            if s.out >= 2 and since >= 1: s.snaps += 1; s.plan(owner, friends, 1.3); return "snap"
            return "out"
        s.out = 0
        n = len(pts); C = tuple(sum(p[k] for p in pts) / n for k in range(2))
        dl = (C[0] - s.center[0], C[1] - s.center[1])
        if math.hypot(*dl) <= 0.2: return "still"
        nc = (s.cam[0] + dl[0], s.cam[1] + dl[1])
        if s.wall and s.wall[0] <= nc[0] <= s.wall[2] and s.wall[1] <= nc[1] <= s.wall[3]:
            s.plan(owner, friends, 1.0); return "cut"
        s.cam, s.foc, s.center = nc, (s.foc[0] + dl[0], s.foc[1] + dl[1]), C; s.glides += 1
        return "glide"

ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

# 1) slow walk: owner and two friends walk 0.5 m/s along +x for 40 s -> glides, no snaps, all in frame
s = Sim(); me = [0.0, 0.0]; fr = [[3.0, 2.0], [-2.0, 3.0]]
s.plan(tuple(me), [tuple(f) for f in fr], 1.0)
for t in range(80):
    me[0] += 0.25; [f.__setitem__(0, f[0] + 0.25) for f in fr]
    r = s.tick(tuple(me), [tuple(f) for f in fr])
    check(all(s.in_frame(p) for p in [tuple(me)] + [tuple(f) for f in fr]), f"slow walk: someone out of frame at tick {t}")
check(s.snaps == 0 and s.glides >= 3, f"slow walk: glides {s.glides}, snaps {s.snaps}")
print(f"slow walk       glides {s.glides:3d}  snaps {s.snaps}")

# 2) a friend runs out of the frame: snap within 2 ticks, then everyone is in frame
s = Sim(); s.plan((0, 0), [(3.0, 2.0), (-2.0, 3.0)], 1.0)
fr = [(3.0, 2.0), (-2.0, 3.0)]; fr2 = [(3.0, 2.0), (-2.0, 14.0)]       # second friend 11 m sideways in one step
ticks = 0; res = ""
while res != "snap" and ticks < 6:
    res = s.tick((0, 0), fr2); ticks += 1
check(res == "snap" and ticks <= 2, f"snap took {ticks} ticks ({res})")
check(all(s.in_frame(p) for p in [(0, 0)] + fr2[:s.used]), "after the snap someone is still out of frame")
print(f"friend leaves   snap after {ticks} tick(s) = {ticks * 0.5:.1f} s, now framing {s.used + 1}")

# 3) very far friends: camera never beyond 25 m
s = Sim()
d = s.plan((0, 0), [(10.0, 0.0), (28.0, 0.0), (0.0, 29.0)], 1.0)
check(d is not None and d <= 25.0 + 1e-9, f"distance {d}")
print(f"far friends     camera {d:.1f} m, framing {s.used + 1} of 4")

# 4) a glide that would end inside a wall becomes a cut
s = Sim(wall=(-100, -100, 100, 100)); s.plan((0, 0), [(3.0, 2.0)], 1.0)
res = s.tick((0.5, 0), [(3.5, 2.0)])
check(res == "cut", f"wall: expected a cut, got {res}")
print(f"glide into wall -> {res}")
print("friends checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
