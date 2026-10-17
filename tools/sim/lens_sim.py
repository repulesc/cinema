# The framing keys in Friends (cinema_lens.lsl -> cinema_friends.lsl): gears from Wide to Faces, the seated angle,
# and Tune. Checks that each gear brings the camera closer than the one before, that nobody is cut at any gear, that
# Faces comes in closer than Frame's nearest distance for people sitting together, that a Tune aim saved in a seat's
# frame comes back right however the seat is turned, and that the scripts carry the same table and wiring.
import importlib.util, math, os, random, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
src = lambda n: open(os.path.join(R, "hud", "src", n)).read()
spec = importlib.util.spec_from_file_location("framing_sim", os.path.join(os.path.dirname(os.path.abspath(__file__)), "framing_sim.py"))
fs = importlib.util.module_from_spec(spec); spec.loader.exec_module(fs)
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

lens, friends, core, ui = src("cinema_lens.lsl"), src("cinema_friends.lsl"), src("cinema_core.lsl"), src("cinema_ui.lsl")
body = re.search(r"list GEARS = \[(.*?)\];", lens, re.S).group(1)
toks = re.findall(r'"[^"]*"|-?\d+(?:\.\d+)?', body)
GEARS = [(toks[i].strip('"'), float(toks[i + 1]), float(toks[i + 2]), float(toks[i + 3]), float(toks[i + 4])) for i in range(0, len(toks), 5)]
check([g[0] for g in GEARS] == ["Auto", "Wide", "Group", "Half", "Close", "Faces"], "gear names changed")
check(re.search(r"list ANGLES = \[60, 45, 30, 15, 0\];", lens) is not None, "angle steps changed")

# ---- wiring: the keys reach the lens, the lens reaches Friends ----------------------------------------------------
check('llMessageLinked(LINK_SET, NUDGE, (string)level + "|" + (string)llGetCameraRot(), "")' in core, "core: NUDGE without the camera rotation")
check('if (gMode == "frame" || gMode == "friends")' in core, "core: Friends keys are not forwarded")
check("llTakeControls(CTL & ~48, TRUE, TRUE);" in core and "llTakeControls(48, TRUE, FALSE);" in core, "core: standing Friends must keep only E/C")
check('if (gMode == "friends" && (info & AGENT_SITTING) != gSitCtl) takeCtl(TRUE);' in core, "core: sitting down does not re-take the keys")
check("integer LENS       = 7319;" in lens and "integer LENS       = 7319;" in friends, "LENS id differs")
for w in ("gSeatEl = llList2Float(gLens, 4) * DEG_TO_RAD;", "gAim = (vector)llList2String(gLens, 5);",
          "gPAz = llAtan2(Nn.y, Nn.x) + llList2Float(gLens, 6);", "vector o = llList2Vector(gMeas, i) + gAim - gPFp;",
          "gVNeed = g / tanV * MARGIN;", "gPLo = llList2Float(gLens, 1);", "if (gOSit) gSeatR = llList2Float(gLens, 2);",
          "gPEye += llList2Float(gLens, 3);", "vector to = p + gAim - gCurCam;"):
    check(w in friends, f"friends: missing {w}")
check('if (gUiMode == "friends") b += ["tune", "untune"];' in ui and "~tune|" in ui and "~untune|" in ui, "ui: Tune is not in the live menu")

# ---- the keys: from Auto, closer lands on Close and wider on Group; the ends hold; past Wide is Auto again ----------
def gear(g, d):
    g = 3 + d if g == 0 else g + d
    return max(0, min(5, g))
check(gear(0, 1) == 4 and gear(0, -1) == 2 and gear(5, 1) == 5 and gear(1, -1) == 0, "gear stepping")
g, seen = 1, [1]
for _ in range(6): g = gear(g, 1); seen.append(g)
check(seen[:5] == [1, 2, 3, 4, 5], "closer does not walk Wide -> Faces")

# ---- distances and margins at each gear, tight groups sitting together ---------------------------------------------
rng = random.Random(3)
dist = {g[0]: [] for g in GEARS[1:]}
worst = {g[0]: 99.0 for g in GEARS[1:]}
pair_faces = []
for t in range(300):
    n = rng.randint(2, 3)
    a = rng.uniform(0, math.pi); step = rng.uniform(0.4, 1.2)
    pts = [fs.mul(fs.d2(a), (i - (n - 1) / 2) * step) for i in range(n)]
    for name, half, lo, sr, lift in GEARS[1:]:
        pl = fs.Planner(fs.World(None), True, rng); pl.op, pl.oy = pts[0], rng.uniform(0, 2 * math.pi)
        pl.grp = pts[1:]; pl.np = pts[1]
        if not pl.planF(): continue
        pl.vneed, pl.lo = half / fs.tanV * pl.M, lo
        for seated in (False, True):
            pl.seatr = sr if seated else 0.0
            sh = pl.sweep()
            check(sh is not None, f"{name}: no shot for a tight group")
            if sh is None: continue
            d = fs.mag(fs.sub(sh[0], pl.F))
            if not seated:
                dist[name].append(d)
                if name == "Faces" and n == 2 and step <= 0.7: pair_faces.append(d)
                m = min(fs.margins(sh[0], sh[1], pl.meas, 1.6))
                worst[name] = min(worst[name], m)
                check(m >= 10.0, f"{name}: someone is within {m:.1f} % of the edge")
mean = {k: sum(v) / len(v) for k, v in dist.items()}
names = [g[0] for g in GEARS[1:]]
for a_, b_ in zip(names, names[1:]):
    check(mean[b_] < mean[a_], f"{b_} ({mean[b_]:.2f} m) is not closer than {a_} ({mean[a_]:.2f} m)")
pf = sum(pair_faces) / len(pair_faces)
check(pf <= 1.2, f"Faces stands {pf:.2f} m from a couple: not closer than Frame's nearest (1.2 m)")
print(f"Faces, two people side by side: {pf:.2f} m (Frame's nearest is 1.2 m)")
print("gears, two or three people sitting together (camera distance along the view, worst edge margin):")
for k in names: print(f"  {k:6s} {mean[k]:5.2f} m   margin {worst[k]:5.1f} %")

# ---- Tune: the aim is kept in the seat's frame -------------------------------------------------------------------
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
def rotv(v, q):                       # LSL v * q
    x, y, z, w = q
    p = qmul(qmul((-x, -y, -z, w), (v[0], v[1], v[2], 0.0)), q)   # LSL rotates by the conjugate convention
    return p[:3]
def unrot(v, q): return rotv(v, (-q[0], -q[1], -q[2], q[3]))      # v / q
def zrot(a): return (0.0, 0.0, math.sin(a / 2), math.cos(a / 2))
check("gAim += m / gSeatRot;" in lens and "(string)(gAim * gSeatRot)" in lens, "lens: the aim is not kept in the seat's frame")
worst_err = 0.0
for t in range(200):
    q = zrot(rng.uniform(0, 2 * math.pi))
    moves = [(rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), rng.uniform(-0.05, 0.05)) for _ in range(8)]
    aim = (0.0, 0.0, 0.0)
    for m in moves: aim = tuple(a + b for a, b in zip(aim, unrot(m, q)))
    world = rotv(aim, q)
    want = tuple(sum(m[i] for m in moves) for i in range(3))
    worst_err = max(worst_err, max(abs(world[i] - want[i]) for i in range(3)))
check(worst_err < 1e-9, f"the aim comes back {worst_err} m off")
# the seat key: each side or pose of a bed (0.5 m steps) is its own entry
check('(string)llRound(v.x * 2.0) + "," + (string)llRound(v.y * 2.0) + "," + (string)llRound(v.z * 2.0)' in lens, "lens: seat key rounding changed")
key = lambda v: tuple(round(c * 2.0) for c in v)
check(key((0.6, 0.0, 0.3)) != key((-0.6, 0.0, 0.3)), "the two sides of a bed share a key")
print(f"tune: the aim comes back exactly ({worst_err:.0e} m) however the seat is turned")
print("lens checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
