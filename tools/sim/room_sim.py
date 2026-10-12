# Python port of the room classifier (context) and room shots (roomShot / roomClear) of
# hud/src/cinema_scenery.lsl, run in test rooms made of thin wall boxes. Checks:
#   - classification: skyboxes / sky malls are "inside"; a house on the ground and an open field are not
#   - every room shot is inside the room's air, in the same room as the owner, with a clear view,
#     and the corner / centre / you-small heights stay in range
import math, random

def ray(world, a, b):
    ground, boxes = world
    d = [b[i] - a[i] for i in range(3)]; L = math.sqrt(sum(x * x for x in d)); best = None
    if d[2] < 0 and a[2] > ground:
        t = (ground - a[2]) / d[2]
        if 0 <= t <= 1: best = t
    for bx in boxes:
        tmin, tmax, ok = 0.0, 1.0, True
        for i, (lo, hi) in enumerate([(bx[0], bx[3]), (bx[1], bx[4]), (bx[2], bx[5])]):
            if abs(d[i]) < 1e-9:
                if a[i] < lo or a[i] > hi: ok = False; break
            else:
                t1, t2 = (lo - a[i]) / d[i], (hi - a[i]) / d[i]
                if t1 > t2: t1, t2 = t2, t1
                tmin = max(tmin, t1); tmax = min(tmax, t2)
                if tmin > tmax: ok = False; break
        if ok and tmin > 0 and (best is None or tmin < best): best = tmin
    return (0, L) if best is None else (1, best * L)

def clampf(v, lo, hi): return max(lo, min(hi, v))
def dirOf(a): return (math.cos(a), math.sin(a))
def novelty(az, last):
    if not last: return 1.0
    m = math.pi
    for l in last: m = min(m, abs((az - l + math.pi) % (2 * math.pi) - math.pi))
    return clampf(m / (math.pi / 2), 0, 1)

def box(x0, y0, z0, x1, y1, z1): return (x0, y0, z0, x1, y1, z1)
def room(x0, y0, z0, x1, y1, h, t=0.3):
    # hollow room: floor, ceiling and four walls (x0..x1, y0..y1, floor top at z0, ceiling underside at z0+h)
    return [box(x0 - t, y0 - t, z0 - t, x1 + t, y1 + t, z0), box(x0 - t, y0 - t, z0 + h, x1 + t, y1 + t, z0 + h + t),
            box(x0 - t, y0 - t, z0, x0, y1 + t, z0 + h), box(x1, y0 - t, z0, x1 + t, y1 + t, z0 + h),
            box(x0, y0 - t, z0, x1, y0, z0 + h), box(x0, y1, z0, x1, y1 + t, z0 + h)]

class Ctx: pass

def context(world, OP, mode="auto"):
    c = Ctx(); ground = world[0]
    E = (OP[0], OP[1], OP[2] + 0.6)
    u = ray(world, (OP[0], OP[1], OP[2] + 1), (OP[0], OP[1], OP[2] + 41))
    c.covered = u[0] == 1; c.ceil = OP[2] + 1 + u[1]
    c.wd, c.wp, nhit = [], [], 0
    for i in range(8):
        dv = dirOf(i * 0.785398); st, d = ray(world, E, (E[0] + dv[0] * 60, E[1] + dv[1] * 60, E[2]))
        nhit += st == 1; c.wd.append(d); c.wp.append((E[0] + dv[0] * d, E[1] + dv[1] * d, E[2]))
    st, d = ray(world, (OP[0], OP[1], OP[2] + 0.3), (OP[0], OP[1], OP[2] - 30))
    floorless = st == 0
    c.floor = OP[2] - 1.0 if floorless else OP[2] + 0.3 - d
    c.enclosed = c.covered and nhit >= 6
    sky = floorless or OP[2] - ground > 50
    c.inside = c.enclosed and sky
    if mode == "inside": c.inside = c.enclosed
    elif mode == "outside": c.inside = False
    c.span = max(c.wd); c.cent = tuple(sum(p[k] for p in c.wp) / 8 for k in range(2))
    ordr = sorted(range(8), key=lambda i: -c.wd[i]); c.ord = ordr
    c.diag = [i for i in ordr if i % 2 == 1][:2]
    c.zc = clampf(c.ceil - 0.6, c.floor + 1.2, c.floor + 6.0)
    c.OP = OP
    return c

CLEAR = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1)]
def roomClear(world, c, cam, foc, need):
    OP = c.OP
    if not (1 <= cam[0] <= 255 and 1 <= cam[1] <= 255): return -1
    E = (OP[0], OP[1], OP[2] + 0.6)
    if math.dist(E, cam) < 0.5: return -1
    st, d = ray(world, E, cam)
    if st == 1 and d < math.dist(E, cam) - 0.2: return -1
    for dv in CLEAR:
        if ray(world, cam, tuple(cam[k] + dv[k] * 0.5 for k in range(3)))[0] != 0: return -1
    v = [foc[k] - cam[k] for k in range(3)]; vl = math.sqrt(sum(x * x for x in v))
    st, cl = ray(world, cam, tuple(cam[k] + v[k] / vl * 60 for k in range(3)))
    return -1 if cl < need else cl

def roomShot(world, c, last, lasttype, n_room=5):
    OP = c.OP; best = None; bs = -1e9
    for _ in range(n_room):
        r = random.random(); typ = 12 if r >= 0.75 else (10 if r < 0.45 else 11)
        cam = foc = None; need = max(3.0, c.span * 0.4)
        if typ == 10:
            di = c.diag[int(random.random() * 2)] if len(c.diag) == 2 else None
            if di is not None and c.wd[di] >= 3:
                d = c.wd[di]; dv = dirOf(di * 0.785398)
                cam = (OP[0] + dv[0] * (d - 0.8), OP[1] + dv[1] * (d - 0.8), c.zc)
                opp = c.wp[(di + 4) % 8]; T = tuple(opp[k] + ((OP[k] if k < 2 else c.floor) - opp[k]) / 3 for k in range(3))
                hv = (T[0] - cam[0], T[1] - cam[1]); hl = math.hypot(*hv)
                pitch = clampf(math.atan2(cam[2] - c.floor, hl), 0.2618, 0.7854)
                foc = (cam[0] + hv[0] / hl * 30, cam[1] + hv[1] / hl * 30, cam[2] - 30 * math.tan(pitch))
        elif typ == 11:
            cam = (c.cent[0], c.cent[1], c.floor + 1.7)
            w = c.wp[c.ord[int(random.random() * 3)]]; hv = (w[0] - cam[0], w[1] - cam[1]); hl = math.hypot(*hv)
            if hl < 1: a = random.uniform(0, 6.2832); hv = dirOf(a); hl = 1
            foc = (cam[0] + hv[0] / hl * 30, cam[1] + hv[1] / hl * 30, cam[2] - 30 * 0.0349)
        else:
            wi = c.ord[int(random.random() * 2)]; d = c.wd[wi]
            if d >= 6:
                dv = dirOf(wi * 0.785398); cam = (OP[0] + dv[0] * (d - 0.8), OP[1] + dv[1] * (d - 0.8), c.floor + 2.5)
                foc = OP; need = math.dist(cam, foc) - 1
        if cam is None: continue
        cl = roomClear(world, c, cam, foc, need)
        if cl >= 0:
            hv = (cam[0] - OP[0], cam[1] - OP[1]); az = math.atan2(hv[1], hv[0])
            nov = novelty(az, last) if math.hypot(*hv) >= 1 else 1.0
            s = 3 * cl / 60 + 2 * nov + random.uniform(0, 0.5) + (1 if typ != lasttype else 0)
            if s > bs: bs = s; best = (cam, foc, typ, az, cl, need)
    return best

random.seed(11)
# (name, world, owner, expect inside?, air boxes (x0,y0,z0,x1,y1,z1) the camera must stay in)
sky_box = room(110, 110, 3000, 130, 130, 5)
mall = room(60, 80, 2000, 120, 120, 8)
tiny = room(126, 126, 1500, 130, 130, 3)
house = room(120, 120, 20, 136, 136, 7)
L1 = room(100, 100, 2500, 130, 112, 5); L2 = room(100, 100, 2500, 112, 130, 5)  # overlapping arms of an L
worlds = [
    ("skybox 20x20x5 at 3000 m", (20.0, sky_box), (120, 120, 3001.0), True, [(110, 110, 3000, 130, 130, 3005)]),
    ("sky mall 60x40x8",         (20.0, mall),    (90, 100, 2001.0), True, [(60, 80, 2000, 120, 120, 2008)]),
    ("tiny sky room 4x4x3",      (20.0, tiny),    (128, 128, 1501.0), True, [(126, 126, 1500, 130, 130, 1503)]),
    ("house on the ground",      (20.0, house),   (128, 128, 21.0), False, []),
    ("open field",               (20.0, []),      (128, 128, 21.0), False, []),
    ("L-shaped sky room",        (20.0, L1 + L2), (105, 105, 2501.0), True, [(100, 100, 2500, 130, 112, 2505), (100, 100, 2500, 112, 130, 2505)]),
]
ok = True
for name, world, OP, want_inside, air in worlds:
    c = context(world, OP)
    if c.inside != want_inside: ok = False; print(f"FAIL {name}: inside={c.inside}, expected {want_inside}")
    shots = fails = 0; last = []; lt = -1
    if c.inside:
        for _ in range(40):
            s = roomShot(world, c, last, lt)
            if s is None: fails += 1; last = []; continue
            cam, foc, typ, az, cl, need = s; shots += 1; problems = []
            if not any(a[0] + 0.3 <= cam[0] <= a[3] - 0.3 and a[1] + 0.3 <= cam[1] <= a[4] - 0.3 and a[2] + 1.1 <= cam[2] <= a[5] - 0.3 for a in air): problems.append("camera not in the room's air")
            E = (OP[0], OP[1], OP[2] + 0.6); st, d = ray(world, E, cam)
            if st == 1 and d < math.dist(E, cam) - 0.25: problems.append("different room")
            if cl < need: problems.append("view blocked")
            if typ == 10 and not (c.floor + 1.2 - 1e-6 <= cam[2] <= c.floor + 6 + 1e-6): problems.append("corner height")
            if problems: ok = False; print(f"FAIL {name}: type {typ} {problems} {tuple(round(x, 1) for x in cam)}")
            last = [az] + last[:1]; lt = typ
    print(f"{name:26s} inside={c.inside!s:5s} enclosed={c.enclosed!s:5s} room shots {shots:2d}/40" + ("" if c.inside else "  (outdoor logic)"))
    if name.startswith(("skybox", "sky mall", "L-shaped")) and shots < 30: ok = False; print(f"FAIL {name}: too few room shots ({shots})")
print("room checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
