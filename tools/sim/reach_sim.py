# Reach learning: a port of the scenery camera distance (scenery findShot / REACH_FAIL / regrowth), the
# core camera check after a cut (core activeTick) and the settings migration (ui checkOwner), run
# against simulated viewers. The new logic must learn a real viewer limit and ignore everything that only LOOKS like
# one (a stale or minimised viewer, mouselook, orbiting, Alt-cam, the viewer lifting the camera off the ground).
# The 4.4.4 logic is run too: it must reproduce the "reach fell to 20 m" report, so the sim proves it tests the bug.
import math, os, random, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
src = lambda n: open(os.path.join(R, "hud", "src", n)).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

# ---- the LSL this file ports (fails loudly if the scripts change under it) -------------------------------------
core, scen, ui = src("core.lsl"), src("scenery.lsl"), src("ui.lsl")
for s, what in ((core, "gCamBefore = llGetCameraPos();"), (core, "llVecDist(cp, gCamBefore) > 1.0"),
                (core, "got > 15.0 && got < 0.9 * want && llVecNorm(cp - op) * llVecNorm(gShotPos - op) > 0.99"),
                (core, "float PEEK_GRACE  = 2.5;"),
                (scen, "if (gCuts - gFailCut <= 10 && llFabs(got - gFailGot) < 0.1 * got)"), (scen, "gReach = clampf(0.9 * got, MIN_DIST, gReach);"),
                (scen, "if (gReachOk >= 20 && gReach < gReachSet)"), (scen, "gReach = clampf(gReach * 1.1, MIN_DIST, gReachSet);"),
                (scen, "if (gReach < gReachSet && llVecDist(c, gOP) > gReach) need = 999.0;"),
                (scen, 'cfg("reach_set", "100")'), (scen, 'cfg("reach", "100")'), (scen, "float   MIN_DIST   = 20.0;"),
                (ui, '~reach=100~'), (ui, '~reach_set=100~'), (ui, "if (v < 4)"), (ui, 'if (rr != "50" && rr != "200") rr = "100";'),
                (ui, 'if (id == "relearn") setReach(cfgGet("reach_set"));')):
    check(what in s, f"source changed, port is stale: {what}")

MIN_DIST, N_CAND = 20.0, 10
V = lambda x, y, z: (x, y, z)
sub = lambda a, b: (a[0] - b[0], a[1] - b[1], a[2] - b[2])
add = lambda a, b: (a[0] + b[0], a[1] + b[1], a[2] + b[2])
mul = lambda a, k: (a[0] * k, a[1] * k, a[2] * k)
mag = lambda a: math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
dist = lambda a, b: mag(sub(a, b))
dot = lambda a, b: a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def norm(a):
    m = mag(a)
    return (0.0, 0.0, 0.0) if m == 0 else mul(a, 1.0 / m)
clampf = lambda v, lo, hi: max(lo, min(hi, v))

class Scenery:
    """scenery: candidate distance, the learned-limit filter, REACH_FAIL (new or 4.4.4) and regrowth."""
    def __init__(s, rng, new, reach=100.0, reach_set=100.0):
        s.rng, s.new, s.reach, s.set = rng, new, reach, reach_set
        s.ok, s.cuts, s.fail_cut, s.fail_got = 0, 0, -99, 0.0
    def shot(s, op):
        r = s.rng
        for _ in range(N_CAND):
            az = r.uniform(0, 2 * math.pi)
            d = MIN_DIST + r.uniform(0, clampf(s.reach - MIN_DIST, 0.0, 200.0))
            c = [op[0] + math.cos(az) * d, op[1] + math.sin(az) * d, 0.0]
            c[0], c[1] = clampf(c[0], 3.0, 253.0), clampf(c[1], 3.0, 253.0)
            ground = op[2] - 1.0 + r.uniform(-6.0, 18.0)           # rolling land around you
            typ, h = (5, r.uniform(10.0, 30.0)) if r.random() < 0.6 else (6, r.uniform(2.5, 4.0))
            c[2] = ground + h
            c = tuple(c)
            if s.new and s.reach < s.set and dist(c, op) > s.reach: continue   # learned limit, straight-line
            return c, typ
        return None, 9                                                    # nothing: core's basic shot
    def after_cut(s, typ):
        s.cuts += 1
        if 5 <= typ <= 7:
            s.ok += 1
            if s.ok >= 20 and s.reach < s.set:
                s.reach = clampf(s.reach * 1.1, MIN_DIST, s.set); s.ok = 0
    def reach_fail(s, want, got):
        s.ok = 0
        if not s.new:
            s.reach = clampf(0.8 * want, MIN_DIST, s.reach); return True
        if s.cuts - s.fail_cut <= 10 and abs(got - s.fail_got) < 0.1 * got:
            got = max(got, s.fail_got)
            s.reach = clampf(0.9 * got, MIN_DIST, s.reach); s.fail_cut = -99; return True
        s.fail_cut, s.fail_got = s.cuts, got
        return False

def verify(new, typ, cp, shot, op, before):
    """core: the first camera check 2.5 s after a cut. Returns (want, got) for a REACH_FAIL, else None."""
    if typ not in (5, 6, 7): return None
    want, got = dist(shot, op), dist(cp, op)
    if not new:
        return (want, got) if dist(cp, shot) > 3.0 and got < 0.8 * want else None
    if (dist(cp, shot) > 3.0 and dist(cp, before) > 1.0 and 15.0 < got < 0.9 * want
            and dot(norm(sub(cp, op)), norm(sub(shot, op))) > 0.99):
        return (want, got)
    return None

# ---- viewers: where the camera really is 2.5 s after the script asked for `shot` --------------------------------
def clamp(L):
    return lambda r, before, shot, op, i: add(op, mul(norm(sub(shot, op)), min(dist(shot, op), L)))
def unlimited(r, before, shot, op, i): return shot
def stale(r, before, shot, op, i): return before                         # minimised / frozen viewer: no updates
def slow(r, before, shot, op, i): return before if r.random() < 0.5 else shot   # update arrives after the check
def mouselook(r, before, shot, op, i): return add(op, V(r.uniform(-.1, .1), r.uniform(-.1, .1), 0.7))
def orbit(p, base=unlimited):
    def f(r, before, shot, op, i):
        if r.random() < p:                                               # you orbit / zoom around yourself
            a, e = r.uniform(0, 2 * math.pi), r.uniform(-0.3, 1.2)
            return add(op, mul(V(math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)), r.uniform(2.0, 30.0)))
        return base(r, before, shot, op, i)
    return f
def altcam(r, before, shot, op, i):                                      # Alt-click on something, stays there a while
    rr = random.Random(i // 8)
    return add(op, V(rr.uniform(-35, 35), rr.uniform(-35, 35), rr.uniform(0, 15)))
def lift(r, before, shot, op, i):                                        # viewer keeps the camera above the land
    return add(shot, V(0, 0, r.uniform(0, 12))) if r.random() < 0.3 else shot

def run(viewer, new, cuts=600, seed=1, reach=100.0, reach_set=100.0):
    r = random.Random(seed)
    sc = Scenery(r, new, reach, reach_set)
    op = V(128.0, 128.0, 30.0)
    cam = add(op, V(-3.0, 0.0, 1.2))                                     # the viewer's camera before Scenery
    fails, shrinks, lo, i = 0, 0, sc.reach, 0
    late = []
    while sc.cuts < cuts:
        shot, typ = sc.shot(op)
        if shot is None: shot, typ = add(op, V(-4, 0, 2)), 9
        sc.after_cut(typ)
        before = cam
        cam = viewer(r, before, shot, op, i); i += 1
        f = verify(new, typ, cam, shot, op, before)
        late.append(1 if f else 0)
        if f:
            fails += 1
            if sc.reach_fail(*f): shrinks += 1
        lo = min(lo, sc.reach)
    return dict(reach=sc.reach, low=lo, fails=fails, shrinks=shrinks, late=sum(late[-300:]) / 300.0)

SEEDS = range(1, 9)
def multi(viewer, new=True, **kw):
    rs = [run(viewer, new, seed=s, **kw) for s in SEEDS]
    return dict(reach=(min(x["reach"] for x in rs), max(x["reach"] for x in rs)), low=min(x["low"] for x in rs),
                fails=max(x["fails"] for x in rs), shrinks=max(x["shrinks"] for x in rs), late=max(x["late"] for x in rs))

def show(name, m):
    print(f"  {name:34s} reach end {m['reach'][0]:5.1f}-{m['reach'][1]:5.1f} m, lowest {m['low']:5.1f}, "
          f"short views {m['fails']:3d}, shrinks {m['shrinks']:2d}, last 300 cuts {100 * m['late']:4.1f} % short")

print("reach sim: 600 cuts x 8 seeds per viewer, chosen reach 100 m")
# 1. viewers without a limit: the reach must stay 100 m whatever the viewer or you do
for name, v in (("unlimited", unlimited), ("minimised / stale camera", stale), ("slow viewer", slow),
                ("mouselook", mouselook), ("Alt-cam on things", altcam), ("camera lifted off the land", lift),
                ("you orbit on 20 % of cuts", orbit(0.2)), ("you orbit on 50 % of cuts", orbit(0.5))):
    m = multi(v); show(name, m)
    check(m["reach"][0] == 100.0, f"{name}: reach should stay 100 m, ended at {m['reach'][0]:.1f}")
    check(m["low"] >= 80.0 if "orbit" in name else m["low"] == 100.0, f"{name}: reach dipped to {m['low']:.1f} m")
# 2. a viewer that really holds the camera within L: learn about L, then (almost) no more short views
for L in (90.0, 64.0, 48.0, 32.0):
    for name, v in ((f"viewer limit {L:.0f} m", clamp(L)), (f"limit {L:.0f} m + you orbit 20 %", orbit(0.2, clamp(L)))):
        m = multi(v); show(name, m)
        # it settles near L (regrowth keeps testing up to ~1.3 L, where the camera is cut short by < 10 %)
        check(m["reach"][1] <= 1.35 * L, f"{name}: should settle near {L:.0f} m, ended at {m['reach'][1]:.1f}")
        check(m["low"] >= min(0.75 * L, MIN_DIST + 4.0), f"{name}: learned too short ({m['low']:.1f} m)")
        check(m["late"] <= 0.06, f"{name}: still {100 * m['late']:.1f} % short views after learning")
# 3. the 4.4.4 logic, to prove the sim catches the bug the user saw (reach at 20 m)
print("4.4.4 logic, same viewers:")
for name, v in (("minimised / stale camera", stale), ("mouselook", mouselook), ("you orbit on 20 % of cuts", orbit(0.2))):
    m = multi(v, new=False, reach=150.0, reach_set=150.0); show(name, m)
    check(m["low"] <= 25.0, f"old logic under '{name}' should collapse to ~20 m (the reported bug); lowest {m['low']:.1f}")
m = multi(unlimited, new=False, reach=150.0, reach_set=150.0)
check(m["shrinks"] == 0, "old logic: an unlimited viewer should not shrink either")

# 4. settings migration (ui checkOwner) on every rez
def boot_old(c):                                           # 4.4.4: the two string checks re-ran on every rez
    if c.get("cfgv") != "2": c["trace"] = "0"; c["cfgv"] = "2"
    if c.get("cfgv") != "3":
        rr = c.get("reach", "")
        if rr in ("", "100"): rr = "150"
        c["reach"] = c["reach_set"] = rr; c["cfgv"] = "3"
def boot_new(c):
    v = int(c.get("cfgv") or 0)
    if v < 2: c["trace"] = "0"
    if v < 4:
        rr = c.get("reach_set", "")
        if rr not in ("50", "200"): rr = "100"
        c["reach_set"] = c["reach"] = rr; c["reach_ok"] = "0"; c["cfgv"] = "4"
old = {"cfgv": "3", "reach": "150", "reach_set": "150", "trace": "1"}
old["reach"] = "24"                                        # a false alarm shrank it, then you re-logged twice
boot_old(old); boot_old(old)
check(old["reach_set"] == "24" and old["trace"] == "0", "4.4.4 migration bug not reproduced")
print(f"migration 4.4.4: after 2 re-logs the chosen reach became {old['reach_set']} m and Chat text was forced off")
for start, want in (({"cfgv": "3", "reach": "24", "reach_set": "24", "trace": "1"}, "100"),
                    ({"cfgv": "3", "reach": "150", "reach_set": "150"}, "100"),
                    ({"cfgv": "3", "reach": "60", "reach_set": "200"}, "200"),
                    ({}, "100")):
    c = dict(start); boot_new(c)
    check(c["reach_set"] == want and c["reach"] == want, f"migration from {start}: got {c.get('reach_set')}/{c.get('reach')}")
    c["reach"] = "57"; c["trace"] = "1"; c["reach_set"] = "100" if want == "100" else want
    for _ in range(3): boot_new(c)                         # later re-logs: nothing changes any more
    check(c["reach"] == "57" and c["trace"] == "1", f"migration re-ran after {start}")
print("migration 4.4.5: 150 / polluted -> 100 m once, 200 / 50 kept, later re-logs leave your settings alone")

print("reach checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
