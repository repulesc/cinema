# People framing: where do the people land on screen? A port of the shot planning in cinema_people.lsl (Social:
# group tableau planG, over-the-shoulder pair planA, portrait) and cinema_friends.lsl (planF), with their sweep() and
# tryCand(), run over pairs, lines, chat circles and loose clusters, in the open and in rooms whose walls block spots,
# on 16:9 and 16:10 windows. Every person who should be in the picture is projected at their real depth with a body
# half-width of 0.3 m; the result is their margin to the nearest screen edge in % of the screen width.
#   old = the 4.4.5 planning (fit straight-on only, depth ignored in Social, camera moved closer at walls)
#   new = 4.4.6 (fit for each candidate direction at its real depth, rejected if a wall is closer than that)
# The over-the-shoulder foreground person is left out on purpose (their shoulder at the edge is the composition).
import math, os, random, sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
src = lambda n: open(os.path.join(R, "hud", "src", n)).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

FOV = 1.047198                       # the default viewer camera: 60 degrees vertical
tanV = math.tan(FOV / 2)
BODY_R, STANDOFF, BODY_MEASURE = 0.35, 0.4, 0.30
OFFS = [0.0, 0.436332, -0.436332, 0.872665, -0.872665, 1.396263, -1.396263]
PHI = [45.0, -45.0, 135.0, -135.0, 180.0, 0.0]
NEW = dict(margin=1.3, fit_aspect=1.6)
OLD = dict(margin=1.15, fit_aspect=1.778)

d2 = lambda a: (math.cos(a), math.sin(a))
dot = lambda a, b: a[0] * b[0] + a[1] * b[1]
sub = lambda a, b: (a[0] - b[0], a[1] - b[1])
add = lambda a, b: (a[0] + b[0], a[1] + b[1])
mul = lambda a, k: (a[0] * k, a[1] * k)
mag = lambda a: math.hypot(a[0], a[1])
def norm(a):
    m = mag(a)
    return (1.0, 0.0) if m == 0 else (a[0] / m, a[1] / m)
def rot(v, a):                       # LSL v * llEuler2Rot(<0,0,a>): counter-clockwise by a
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)

class World:
    def __init__(s, box=None): s.box = box                          # (x0, y0, x1, y1) room walls, or None (open)
    def ray(s, a, b):                                               # (hit?, distance)
        L = mag(sub(b, a))
        if s.box is None or L == 0: return (0, L)
        d = norm(sub(b, a)); t = 1e9
        x0, y0, x1, y1 = s.box
        for i, (lo, hi) in enumerate(((x0, x1), (y0, y1))):
            if d[i] > 1e-9: t = min(t, (hi - a[i]) / d[i])
            elif d[i] < -1e-9: t = min(t, (lo - a[i]) / d[i])
        return (1, t) if t < L else (0, L)

class Planner:
    """One port for both scripts; `new` switches between the 4.4.5 and the 4.4.6 planning."""
    def __init__(s, world, new, rng):
        s.w, s.new, s.r = world, new, rng
        P = NEW if new else OLD
        s.M = P["margin"]; s.tanH = tanV * P["fit_aspect"]; s.alpha = math.atan2(tanV * 1.778 / 3.0, 1.0)
        s.side, s.rev, s.lastPhi = 1.0, False, 999.0
        s.close = False                                             # 4.9.0: a close, half-length group view
        s.skip_from = None                                          # "next": the camera on screen, to move away from
    # ---- shared: tryCand's view direction (rule of thirds for a non-centred shot) ----
    def view(s, az):
        V = mul(d2(az), -1.0)
        if not s.center:
            fs = dot(d2(s.oy), (V[1], -V[0]))
            sd = s.side
            if fs > 0.2: sd = 1.0
            elif fs < -0.2: sd = -1.0
            V = rot(V, -sd * s.alpha)
        return V
    def need_at(s, az):                                             # 4.4.6: distance that fits everyone measured
        u = d2(az); V = s.view(az); P = (-V[1], V[0])
        c, sn, k = -dot(u, V), dot(u, P), s.tanH / s.M
        need = s.vneed
        for p in s.meas:
            o = sub(p, s.F); a, b = dot(o, P), dot(o, V)
            need = max(need, (a + BODY_R - k * b) / (k * c + sn), (-a + BODY_R - k * b) / (k * c - sn))
        return need
    def fitDist(s, spread, halfH, lo, hi):
        return min(hi, max(lo, max((spread + BODY_R) / s.tanH, halfH / tanV) * s.M))
    # ---- plans ----
    def planA(s, pair):
        s.axis, s.center, s.type, s.F, s.dMin, s.meas = None, False, 0, s.op, 2.0, [s.op]
        s.vneed, s.lo, s.hi = 1.3 / tanV * s.M, 2.5, 3.5
        ax = sub(s.np, s.op) if s.np else (0, 0)
        if pair and s.np and mag(ax) >= 0.3:
            A = norm(ax)
            dc = mul((-A[1], A[0]), s.side * 0.819152)
            dc = add(dc, mul(A, 0.573576)) if s.rev else sub(dc, mul(A, 0.573576))
            s.meas = [s.op] if s.rev else [s.np]                   # the person who faces the camera
            s.rev = not s.rev
            dc = norm(dc)
            s.F = mul(add(mul(s.op, 1.5), s.np), 1 / 2.5)
            s.az, s.axis, s.dMin, s.type = math.atan2(dc[1], dc[0]), A, 2.5, 1
            s.vneed, s.lo, s.hi = 0.9 / tanV * s.M, 2.5, (6.5 if s.new else 5.0)
            s.d = s.fitDist(abs(dot(ax, (-dc[1], dc[0]))), 0.9, 2.5, 5.0)
            if s.new: s.d = min(s.hi, max(s.lo, s.need_at(s.az)))
            return
        i = s.r.randrange(6)
        if abs(PHI[i] - s.lastPhi) < 0.5: i = (i + 1) % 6
        s.lastPhi = PHI[i]
        s.az = s.oy + math.radians(PHI[i])
        s.d = s.fitDist(0.0, 1.3, 2.5, 3.5)
    def planG(s):                                                   # Social group tableau
        M = [s.op] + s.grp
        if len(M) < 3: return False
        C = mul((sum(p[0] for p in M), sum(p[1] for p in M)), 1 / len(M))
        best, A = 0.0, (1.0, 0.0)
        for i in range(len(M)):
            for j in range(i + 1, len(M)):
                dv = sub(M[j], M[i])
                if mag(dv) > best: best, A = mag(dv), norm(dv)
        Nn = (-A[1], A[0])
        if dot(d2(s.oy), Nn) < 0: Nn = mul(Nn, -1)
        spread = max(abs(dot(sub(p, C), A)) for p in M)
        s.F, s.az, s.dMin, s.axis, s.center, s.type, s.meas = C, math.atan2(Nn[1], Nn[0]), 3.0, None, True, 2, M
        s.vneed, s.lo, s.hi = 1.3 / tanV * s.M, 4.0, 12.0
        if s.close: s.vneed, s.lo = 0.9 / tanV * s.M, 2.0
        s.d = s.fitDist(spread, 1.3, 4.0, 12.0)
        if s.new: s.d = min(s.hi, max(s.lo, s.need_at(s.az)))
        return True
    def planF(s, maxd=25.0, cnt=None):                              # Friends group (depth-aware since 4.0)
        if cnt is None: cnt = len(s.grp)
        while cnt > 0:
            M = [s.op] + s.grp[:cnt]
            C = mul((sum(p[0] for p in M), sum(p[1] for p in M)), 1 / len(M))
            best, A = 0.0, (1.0, 0.0)
            for i in range(len(M)):
                for j in range(i + 1, len(M)):
                    dv = sub(M[j], M[i])
                    if mag(dv) > best: best, A = mag(dv), norm(dv)
            Nn = (-A[1], A[0])
            if dot(d2(s.oy), Nn) < 0: Nn = mul(Nn, -1)
            s.F, s.az, s.dMin, s.axis, s.center, s.type, s.meas = C, math.atan2(Nn[1], Nn[0]), 3.0, None, True, 3, M
            s.vneed, s.lo, s.hi = 1.3 / tanV * s.M, 3.0, maxd
            if s.close: s.vneed, s.lo = 0.9 / tanV * s.M, 2.0
            if s.new: need = s.need_at(s.az)
            else:
                need = 1.3 / tanV * s.M
                for p in M:
                    o = sub(p, C)
                    need = max(need, (abs(dot(o, A)) + BODY_R) * s.M / s.tanH + dot(o, Nn))
            if need <= maxd or cnt == 1:
                s.d = min(maxd, max(s.lo, need)); s.used = cnt
                return True
            cnt -= 1
        return False
    # ---- sweep + tryCand ----
    def tryCand(s, az, de):
        cam = add(s.F, mul(d2(az), de))
        hit, dist = s.w.ray(cam, s.F)
        if hit and dist < mag(sub(cam, s.F)) - 0.8: return None
        return cam, s.view(az)
    def sweep(s):
        C = []
        for off in OFFS:
            az = s.az + off
            if s.new:
                de = s.need_at(az)
                if de > s.hi: continue                              # cannot hold everyone from this side
                de = max(de, s.lo)
                hit, dist = s.w.ray(s.F, add(s.F, mul(d2(az), de)))
                if hit and dist - STANDOFF < de: continue           # a wall is closer than that: next side
                sc = 3.0 * min(1.0, s.d / de) + 2.0 * math.cos(off)
            else:
                hit, dist = s.w.ray(s.F, add(s.F, mul(d2(az), s.d)))
                de = s.d if not hit else min(s.d, dist - STANDOFF)
                if de < max(0.6 * s.dMin, 1.2): continue
                sc = 3.0 * de / s.d + 2.0 * math.cos(off)
            if s.axis:
                lat = dot(d2(az), (-s.axis[1], s.axis[0]))
                sc += 1.0 if lat * s.side > 0 else -2.0
            if s.new and s.skip_from is not None and mag(sub(add(s.F, mul(d2(az), de)), s.skip_from)) <= 1.5: continue
            C.append((sc, az, de))
        C.sort(key=lambda c: -c[0])
        for sc, az, de in C[:2]:
            v = s.tryCand(az, de)
            if v: return v
        return None

def margins(cam, V, people, aspect):
    """each person's margin to the nearest screen edge, % of the screen width (negative = cut / off screen)"""
    tanH = tanV * aspect
    P = (-V[1], V[0]); out = []
    for p in people:
        o = sub(p, cam); f, l = dot(o, V), abs(dot(o, P))
        if f < 0.3: out.append(-100.0); continue
        x = (l + BODY_MEASURE) / (f * tanH)                          # 1.0 = the body touches the edge
        out.append(50.0 * (1.0 - x))
    return out

# ---- groups of people --------------------------------------------------------------------------------------------
def spaced(r, n, gen, minsep=0.7):
    for _ in range(200):
        pts = gen()
        if all(mag(sub(pts[i], pts[j])) >= minsep for i in range(n) for j in range(i + 1, n)): return pts
    return pts
def scene(r, kind):
    if kind == "pair":
        a = r.uniform(0, 2 * math.pi); dd = r.uniform(0.8, 4.5)
        return [(0.0, 0.0), d2(a) and mul(d2(a), dd)]
    if kind == "line":
        n = r.randint(3, 6); a = r.uniform(0, math.pi); step = r.uniform(0.8, 1.5)
        pts = [mul(d2(a), (i - (n - 1) / 2) * step) for i in range(n)]
        k = r.randrange(n); pts[0], pts[k] = pts[k], pts[0]
        return pts
    if kind == "circle":
        n = r.randint(4, 6); rad = r.uniform(1.5, 3.5); a0 = r.uniform(0, 2 * math.pi)
        return [mul(d2(a0 + i * 2 * math.pi / n + r.uniform(-0.2, 0.2)), rad) for i in range(n)]
    n = r.randint(3, 6)
    return spaced(r, n, lambda: [(r.uniform(-3, 3), r.uniform(-3, 3)) for _ in range(n)])
ROOMS = {"open": None, "room 10x8": (-5.0, -4.0, 5.0, 4.0), "room 6x6": (-3.0, -3.0, 3.0, 3.0)}

def run(new, mode, kind, room, aspect, trials=400, seed=7):
    r = random.Random(seed)
    res = dict(n=0, edge5=0, edge10=0, cut=0, fallback=0, mins=[])
    for t in range(trials):
        pts = scene(r, kind)
        box = ROOMS[room]
        if box:                                                     # move the group into the room, clear of the walls
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if max(xs) - min(xs) > box[2] - box[0] - 1.0 or max(ys) - min(ys) > box[3] - box[1] - 1.0: continue
            dx = r.uniform(box[0] + 0.5 - min(xs), box[2] - 0.5 - max(xs))
            dy = r.uniform(box[1] + 0.5 - min(ys), box[3] - 0.5 - max(ys))
            pts = [(p[0] + dx, p[1] + dy) for p in pts]
        pl = Planner(World(box), new, r)
        pl.op, pl.oy = pts[0], r.uniform(0, 2 * math.pi)
        pl.side = r.choice((1.0, -1.0)); pl.rev = r.random() < 0.5
        others = sorted(pts[1:], key=lambda p: mag(sub(p, pts[0])))
        if mode == "social":
            pl.grp = [p for p in others if mag(sub(p, pl.op)) <= 8.0][:5]
            near = [p for p in others if mag(sub(p, pl.op)) <= 4.5]
            pl.np = near[0] if near else None
            shot = None
            if kind != "pair" and len(pl.grp) >= 2 and pl.planG(): shot = pl.sweep()
            if shot is None and pl.np:
                if kind != "pair": res["fallback"] += 1
                pl.planA(True); shot = pl.sweep()
        else:
            pl.grp = others; pl.np = others[0] if others else None
            shot = pl.sweep() if pl.planF() else None
            if new:                                                 # 4.4.6: a wall in the way? frame fewer friends
                tries = 0
                while shot is None and pl.used > 1 and tries < 3:
                    tries += 1; res["fewer"] = res.get("fewer", 0) + 1
                    shot = pl.sweep() if pl.planF(cnt=pl.used - 1) else None
        if shot is None:
            res["fallback"] += 1; continue                         # portrait of you: not a people framing
        m = min(margins(shot[0], shot[1], pl.meas, aspect))
        res["n"] += 1; res["mins"].append(m)
        res["edge5"] += m < 5.0; res["edge10"] += m < 10.0; res["cut"] += m < 0.0
    return res

def fmt(x):
    if x["n"] == 0: return "   (no shots)"
    mins = sorted(x["mins"]); med = mins[len(mins) // 2]
    return (f"{x['n']:4d} shots  cut {100 * x['cut'] / x['n']:5.1f} %  <5 % {100 * x['edge5'] / x['n']:5.1f} %  "
            f"<10 % {100 * x['edge10'] / x['n']:5.1f} %  median margin {med:5.1f} %  fallback {x['fallback']:3d}")

if __name__ == "__main__":
    people, friends = src("cinema_people.lsl"), src("cinema_friends.lsl")
    for s, name in ((people, "people"), (friends, "friends")):     # the port must match the scripts it claims to
        for what in ("float MARGIN      = 1.3;", "tanH = tanV * fmin(aspect, 1.6);", "gAlpha = llAtan2(tanV * aspect / 3.0, 1.0);",
                     "need = fmax(need, fmax((a + b) / (c + sn), (b - a) / (c - sn)));", "float b = BODY_R - k * (o * V);",
                     "float c = k * (ZERO_VECTOR - u) * V;", "if (de <= gPHi && (st == 0 || llList2Float(r, 1) - STANDOFF >= de))",
                     "float s = 3.0 * fmin(1.0, gPd / de) + 2.0 * llCos(off);", "gPHi = 6.5;", "gMeas = [gNPos];"):
            check(what in s, f"{name}: source changed, port is stale: {what}")
    check("gPLo = 4.0;\n    gPHi = 12.0;" in people, "people: planG limits changed")
    check("if (planF(mult, gUsedN - 1)) shot = sweep();" in friends and "t < 3" in friends, "friends: fewer-friends retry changed")
    quick = "--quick" in sys.argv
    T = 150 if quick else 400
    totals = {False: dict(n=0, cut=0, e10=0), True: dict(n=0, cut=0, e10=0)}
    for mode, kinds in (("social", ("pair", "line", "circle", "cluster")), ("friends", ("line", "circle", "cluster"))):
        for kind in kinds:
            for room in ROOMS:
                for aspect in (1.778, 1.6):
                    tag = f"{mode:7s} {kind:7s} {room:9s} {('16:9' if aspect > 1.7 else '16:10'):5s}"
                    for new in (False, True):
                        x = run(new, mode, kind, room, aspect, trials=T)
                        totals[new]["n"] += x["n"]; totals[new]["cut"] += x["cut"]; totals[new]["e10"] += x["edge10"]
                        if not quick or new: print(f"{tag} {'new' if new else 'old'}  {fmt(x)}")
                        if new:
                            check(x["cut"] == 0, f"{tag}: someone is cut ({x['cut']} shots)")
                            check(x["n"] == 0 or x["edge10"] <= 0.01 * x["n"], f"{tag}: {x['edge10']} of {x['n']} shots under a 10 % margin")
    for new in (False, True):
        t = totals[new]
        print(f"ALL {'new (4.4.6)' if new else 'old (4.4.5)'}: {t['n']} shots, cut {100 * t['cut'] / t['n']:.1f} %, "
              f"under 10 % margin {100 * t['e10'] / t['n']:.1f} %")
    check(totals[False]["e10"] > 0.05 * totals[False]["n"], "the old planning should show the reported edge problem")
    # "next" (double-tap): the group shot is planned from where people stand, so without the skip rule it comes out
    # identical; with it, the next camera must stand somewhere else (and still frame everyone)
    for s_, what in ((people, "people"), (friends, "friends")):
        check('if (!gSkip || llVecDist(<cc.x, cc.y, 0.0>, <gCurCam.x, gCurCam.y, 0.0>) > 1.5) C += [s, az, de];' in s_,
              f"{what}: the next-shot rule is missing")
    rng = random.Random(11); same = moved = 0
    for t in range(300):
        pts = scene(rng, rng.choice(("line", "circle", "cluster")))
        for use_skip in (False, True):
            pl = Planner(World(None), True, rng); pl.op, pl.oy = pts[0], rng.uniform(0, 2 * math.pi)
            pl.grp = sorted(pts[1:], key=lambda p: mag(sub(p, pts[0])))[:5]
            if len(pl.grp) < 2 or not pl.planG(): continue
            a = pl.sweep()
            if use_skip: pl.skip_from = a[0]
            b = pl.sweep()
            if a is None or b is None: continue
            if use_skip:
                moved += mag(sub(a[0], b[0])) > 1.5
                check(min(margins(b[0], b[1], pl.meas, 1.778)) >= 0, "next: the new shot cuts someone")
            else: same += mag(sub(a[0], b[0])) < 0.01
    print(f"next: without the rule {same} of 300 group shots repeat exactly; with it {moved} move to a new spot")
    check(moved >= 290, f"next: only {moved} of 300 group shots moved")
    # close views (4.9.0): people standing within 3.5 m of each other get, now and then, a half-length view from about
    # half the distance; they must fit as well as the wide ones, and the camera must come out closer
    for s_, what in ((people, "people"), (friends, "friends")):
        check("(best < 3.5 &&" in s_ and "gPLo = 2.0;" in s_ and "gVNeed = 0.9 / tanV * MARGIN;" in s_
              and "llFrand(1.0) < 0.55" in s_ and "!gLastClose" in s_, f"{what}: the close-view rule changed")
    rng = random.Random(21); wide_d = []; close_d = []; worst = 99.0; nclose = 0
    for t in range(600):
        pts = scene(rng, rng.choice(("pair", "line", "cluster")))
        for mode in ("social", "friends"):
            for use_close in (False, True):
                pl = Planner(World(None), True, rng); pl.op, pl.oy = pts[0], rng.uniform(0, 2 * math.pi)
                pl.close = use_close
                pl.grp = sorted(pts[1:], key=lambda p: mag(sub(p, pts[0])))[:5]
                pl.np = pl.grp[0] if pl.grp else None
                if mode == "social":
                    if len(pl.grp) < 2 or not pl.planG(): continue
                else:
                    if not pl.grp or not pl.planF(): continue
                spread = max(mag(sub(a, b)) for a in [pl.op] + pl.grp[:getattr(pl, "used", 9)] for b in [pl.op] + pl.grp[:getattr(pl, "used", 9)])
                if spread >= 3.5: continue
                sh = pl.sweep()
                if sh is None: continue
                (close_d if use_close else wide_d).append(pl.d)
                m = min(margins(sh[0], sh[1], pl.meas, 1.6))
                if use_close: worst = min(worst, m); nclose += 1
                check(m >= 10.0, f"close={use_close} {mode}: margin {m:.1f} % under 10 %")
    mean = lambda L: sum(L) / len(L)
    print(f"close views: {nclose} compact groups; mean camera distance wide {mean(wide_d):.1f} m, close {mean(close_d):.1f} m; worst margin {worst:.1f} %")
    check(nclose > 100 and mean(close_d) < 0.75 * mean(wide_d), "close views should be clearly closer than wide ones")
    print("framing checks:", "ALL PASS" if ok else "FAILURES")
    raise SystemExit(0 if ok else 1)
