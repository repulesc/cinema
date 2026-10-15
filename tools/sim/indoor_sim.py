# Faithful port of the INSIDE logic of hud/src/cinema_scenery.lsl (context, floorOK, localShot, safeShot and the
# inside part of nextShot), run against test builds. It replaces room_sim.py (the old wall-counting design).
#
# What makes it faithful:
#   - llCastRay returns what Second Life returns: a flat list [key, position, key, position, ..., count], the count
#     is < 0 when the region refuses the ray, the land reports NULL_KEY, one hit per object, sorted by distance.
#     The port reads it with llList2Key / llList2Vector / llList2Integer exactly like the script, so an indexing
#     mistake (like the 3-per-hit stride bug of 4.3.1) shows up here.
#   - Rays only see PHYSICS: parts built without physics (glass, ceilings, decor) are invisible to rays but still
#     part of the build, so the containment checks use the real geometry.
#   - Busy regions: a world can refuse a share of the rays (RCERR_CAST_TIME_EXCEEDED).
#
# Checked for every inside shot: the camera is inside the build's interior (not outside, not in another storey),
# not inside any solid part, and the classification (inside / outdoors) is the expected one for each place.
import math, random

NULL_KEY = "00000000-0000-0000-0000-000000000000"
ZERO_VECTOR = (0.0, 0.0, 0.0)
TWO_PI, PI = 2 * math.pi, math.pi

# ---- LSL list semantics ------------------------------------------------------------------------------------------
def _get(l, i):
    if i < 0: i += len(l)
    return l[i] if 0 <= i < len(l) else None
def llList2Integer(l, i):
    v = _get(l, i)
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0
def llList2Float(l, i):
    v = _get(l, i)
    return float(v) if isinstance(v, (int, float)) else 0.0
def llList2Vector(l, i):
    v = _get(l, i)
    return v if isinstance(v, tuple) and len(v) == 3 else ZERO_VECTOR
def llList2Key(l, i):
    v = _get(l, i)
    return v if isinstance(v, str) else ""

# ---- vectors -----------------------------------------------------------------------------------------------------
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def mag(a): return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
def norm(a): m = mag(a); return (a[0] / m, a[1] / m, a[2] / m) if m > 1e-9 else ZERO_VECTOR
def dist(a, b): return mag(sub(a, b))
def dirOf(a): return (math.cos(a), math.sin(a), 0.0)
def clampf(v, lo, hi): return lo if v < lo else hi if v > hi else v

# ---- the world ---------------------------------------------------------------------------------------------------
class Box:
    def __init__(s, b, obj, phys=True): s.b, s.obj, s.phys = b, obj, phys
    def inside(s, p, m=0.0): b = s.b; return b[0] + m < p[0] < b[3] - m and b[1] + m < p[1] < b[4] - m and b[2] + m < p[2] < b[5] - m

class World:
    def __init__(s, ground, boxes, err_p=0.0, rnd=None):
        s.ground, s.boxes, s.err_p, s.rnd = ground, boxes, err_p, rnd or random.Random(1)
    def llCastRay(s, a, b, max_hits):
        if s.err_p and s.rnd.random() < s.err_p: return [-3]               # RCERR_CAST_TIME_EXCEEDED
        d = sub(b, a); L = mag(d); hits = {}
        for bx in s.boxes:
            if not bx.phys or bx.inside(a): continue                       # no physics, or the ray starts inside it
            t0, t1, ok = 0.0, 1.0, True
            for i in range(3):
                lo, hi = bx.b[i], bx.b[i + 3]
                if abs(d[i]) < 1e-12:
                    if not (lo <= a[i] <= hi): ok = False; break
                else:
                    u, v = (lo - a[i]) / d[i], (hi - a[i]) / d[i]
                    if u > v: u, v = v, u
                    t0, t1 = max(t0, u), min(t1, v)
                    if t0 > t1: ok = False; break
            if ok and t0 > 1e-9 and (bx.obj not in hits or t0 < hits[bx.obj]): hits[bx.obj] = t0   # one hit per object
        out = [(t, "obj-%d" % o) for o, t in hits.items()]
        if a[2] > s.ground >= b[2]:
            out.append(((a[2] - s.ground) / (a[2] - b[2]), NULL_KEY))            # the land
        out.sort()
        out = out[:max_hits]
        flat = []
        for t, k in out: flat += [k, add(a, mul(d, t))]
        return flat + [len(out)]

# ---- the port (same names and order as cinema_scenery.lsl) ------------------------------------------------------
UP_DIRS = [(0.0, 0.0, 1.0), (0.423, 0.0, 0.906), (-0.423, 0.0, 0.906), (0.0, 0.423, 0.906), (0.0, -0.423, 0.906)]
N_LOCAL = 8
FLOOR_STEPS = [1.5, 3.0, 5.0, 8.0, 12.0, 20.0]

class Scenery:
    def __init__(s, W, OP, indoors, rnd, yaw=0.0):
        s.W, s.gOP, s.gIndoors, s.rnd, s.yaw = W, OP, indoors, rnd, yaw
        s.gLocal = False; s.gLocalAt = ZERO_VECTOR
        s.gErr = False; s.gCtxOK = False; s.gLastAz = []; s.gLastType = -1; s.gRetry = 0; s.gRayErr = 0
    def llFrand(s, x): return s.rnd.random() * x
    def ray(s, a, b):
        r = s.W.llCastRay(a, b, 1)
        st = llList2Integer(r, -1)
        if st < 0: s.gErr = True; s.gRayErr += 1; return [st, 0.0]
        if st == 0: return [0, dist(a, b)]
        return [1, dist(a, llList2Vector(r, 1))]
    def novelty(s, az):
        if not s.gLastAz: return 1.0
        m = PI
        for l in s.gLastAz:
            d = (az - l + PI) % TWO_PI - PI; m = min(m, abs(d))
        return clampf(m / (PI / 2), 0.0, 1.0)
    def context(s):
        s.gCtxOK = False; s.gRayErr = 0; op = s.gOP
        bd = s.W.llCastRay((op[0], op[1], op[2] + 0.3), (op[0], op[1], op[2] - 100.0), 4)
        nb = llList2Integer(bd, -1)
        if nb < 0: s.gErr = True; return
        s.gPrimFloor = False; s.gSky = True; s.gFloorZ = op[2] - 1.0
        if nb > 0:
            fh = llList2Vector(bd, 1); s.gFloorZ = fh[2]
            s.gPrimFloor = llList2Key(bd, 0) != NULL_KEY
        for i in range(nb):
            if llList2Key(bd, i * 2) == NULL_KEY: s.gSky = False
        U = (op[0], op[1], s.gFloorZ + 1.8); s.gRoofs = 0; ceil = 1.0e6
        for i in range(5):
            u = s.ray(U, add(U, mul(UP_DIRS[i], 40.0)))
            if llList2Integer(u, 0) == 1:
                s.gRoofs += 1; hz = U[2] + llList2Float(u, 1) * UP_DIRS[i][2]
                ceil = min(ceil, hz)
        E = (op[0], op[1], s.gFloorZ + 1.6); s.gWallD = []; nh = 0
        for i in range(8):
            r = s.ray(E, add(E, mul(dirOf(i * 0.785398), 60.0)))
            wd = llList2Float(r, 1)
            if llList2Integer(r, 0) == 1: nh += 1
            if llList2Integer(r, 0) < 0: wd = 4.0
            s.gWallD.append(wd)
        s.gFloorD = []
        for i in range(8):
            fd = 0.0
            for sd in FLOOR_STEPS:
                s.gErr = False
                if sd > s.gWallD[i]: break
                elif s.floorOK(add((op[0], op[1], s.gFloorZ + 1.0), mul(dirOf(i * 0.785398), sd))): fd = sd
                elif s.gErr: s.gRayErr += 1
                else: break
            s.gFloorD.append(fd)
        s.gErr = False
        nhit = nh
        built = s.gPrimFloor or s.gRoofs > 0
        if s.gIndoors == "inside": raw = True
        else: raw = s.gPrimFloor and (s.gSky or s.gRoofs >= 3 or (s.gRoofs >= 1 and nhit >= 5))
        if not raw and s.gLocal and s.gIndoors != "outside" and (built or nhit >= 5) and dist(s.gOP, s.gLocalAt) < 30.0: raw = True
        if s.gIndoors == "outside": raw = False
        s.gLocal = raw
        if raw: s.gLocalAt = s.gOP
        s.gCapZ = s.gFloorZ + 3.4
        if s.gRoofs > 0: s.gCapZ = clampf(ceil - 0.4, s.gFloorZ + 1.6, s.gFloorZ + 6.0)
        opn = sum(1 for w in s.gWallD if w >= 25.0)
        s.gDmax = 20.0 if opn >= 5 else 12.0
        s.gCtxOK = s.gRayErr <= 3
    def floorOK(s, c):
        r = s.W.llCastRay(c, (c[0], c[1], s.gFloorZ - 1.0), 1)
        st = llList2Integer(r, -1)
        if st < 0: s.gErr = True; return False
        if st == 0: return False
        if llList2Key(r, 0) == NULL_KEY and s.gPrimFloor: return False
        h = llList2Vector(r, 1)
        return s.gFloorZ - 1.0 <= h[2] <= s.gFloorZ + 1.5
    def edge(s, i):
        i = i % 8
        return min(s.gWallD[i] - 0.8, s.gFloorD[i] - 0.5)
    def localShot(s, dmax, relaxed):
        best, bestS, found = [], -1000.0, 0
        E = (s.gOP[0], s.gOP[1], s.gFloorZ + 1.6); O = (s.gOP[0], s.gOP[1], s.gFloorZ + 1.0)
        s.gRayErr = 0
        base = s.llFrand(TWO_PI); k = 0
        while k < N_LOCAL and found < 3 and s.gRayErr < 6:
            az = base + k * 0.785398 + s.llFrand(0.4) - 0.2
            wi = int(az / 0.785398)                                        # (integer) truncates toward zero, like LSL
            lim = min(s.edge(wi), s.edge(wi + 1))
            if lim > dmax: lim = dmax
            nov = s.novelty(az)
            if lim >= 2.5 and (relaxed or nov >= 0.3):
                roll = s.llFrand(1.0); typ = 11
                if not relaxed and roll < 0.4: typ = 10
                elif not relaxed and roll >= 0.75 and lim >= 5.0: typ = 12
                d = 2.5 + s.llFrand(lim - 2.5); z = s.gFloorZ + 1.5 + s.llFrand(0.4)
                if typ == 10:
                    d = lim * (0.6 + 0.4 * s.llFrand(1.0)); z = s.gCapZ - 0.2
                    if z < s.gFloorZ + 2.2: typ = 11
                elif typ == 12:
                    d = lim * (0.75 + 0.25 * s.llFrand(1.0)); z = s.gFloorZ + 1.8 + s.llFrand(0.6)
                if z > s.gCapZ: z = s.gCapZ
                c = add((s.gOP[0], s.gOP[1], z), mul(dirOf(az), d))
                if typ == 10:
                    T = add(O, (s.llFrand(4.0) - 2.0, s.llFrand(4.0) - 2.0, -0.2))
                    hv = sub(T, c); hv = (hv[0], hv[1], 0.0)
                    pitch = clampf(math.atan2(c[2] - T[2], mag(hv)), 0.21, 0.61)
                    foc = add(c, mul(norm(hv), 10.0)); foc = (foc[0], foc[1], c[2] - 10.0 * math.tan(pitch))
                elif typ == 12: foc = add(O, (0.0, 0.0, 0.2))
                else:
                    foc = add(c, mul(dirOf(az + PI + (s.llFrand(1.4) - 0.7)), 10.0)); foc = (foc[0], foc[1], c[2] - 0.5)
                need = min(d + 1.0, 6.0)
                if typ == 12: need = dist(c, foc) - 1.0
                if 1.0 < c[0] < 255.0 and 1.0 < c[1] < 255.0:
                    dEc = dist(E, c)
                    r = s.ray(E, add(E, mul(norm(sub(c, E)), dEc + 0.6)))
                    if llList2Integer(r, 0) == 0 or (llList2Integer(r, 0) == 1 and llList2Float(r, 1) >= dEc + 0.5):
                        if s.floorOK(c) and s.floorOK(add(c, mul(dirOf(az), 0.6))):
                            room = True
                            if not relaxed:
                                r = s.ray(c, add(c, (0.0, 0.0, 0.5))); room = llList2Integer(r, 0) == 0
                            if room:
                                r = s.ray(c, add(c, mul(norm(sub(foc, c)), 30.0))); clear = llList2Float(r, 1)
                                if llList2Integer(r, 0) >= 0 and clear >= need:
                                    found += 1
                                    sc = 2.0 * clear / 30.0 + 2.0 * nov + s.llFrand(0.5) + (1.0 if typ != s.gLastType else 0.0)
                                    if sc > bestS: bestS, best = sc, [c, foc, typ, az]
            k += 1
        return best
    def safeShot(s):
        F = (math.cos(s.yaw), math.sin(s.yaw), 0.0)
        E = (s.gOP[0], s.gOP[1], s.gFloorZ + 1.6); fa = math.atan2(F[1], F[0])
        bestD, B = 0.8, mul(F, -1.0)
        for i in range(3):
            b = dirOf(fa + PI + (i - 1) * 0.785398)
            r = s.ray(E, add(E, mul(b, 2.5))); dd = 2.2
            if llList2Integer(r, 0) == 1: dd = llList2Float(r, 1) - 0.3
            elif llList2Integer(r, 0) < 0: dd = 0.8
            dd = min(dd, 2.2)
            if dd > bestD + 0.1: bestD, B = dd, b
        c = add(add(E, mul(B, bestD)), (0.0, 0.0, 0.3))
        return [c, sub(add(c, mul(F, 10.0)), (0.0, 0.0, 0.6)), 13, math.atan2(B[1], B[0])]
    def nextShot(s):
        """the inside part of nextShot: returns ('shot', s) | ('retry', None) | ('noshot', None) | ('outdoor', None)"""
        s.gErr = False
        if not s.gCtxOK: s.context()
        sh = []
        if not sh and not s.gErr and s.gLocal:
            sh = s.localShot(s.gDmax, False)
            if not sh: sh = s.localShot(6.0, True)
            if not sh: sh = s.safeShot()
        if not s.gErr and s.gCtxOK and not s.gLocal: return ("outdoor", None)
        if sh: s.gErr = False
        if not sh:
            if s.gErr and s.gRetry < 2: s.gRetry += 1; return ("retry", None)
            s.gRetry = 0; s.gLastAz = []; return ("noshot", None)
        s.gRetry = 0; s.gLastAz = [sh[3]] + s.gLastAz[:1]; s.gLastType = sh[2]
        return ("shot", sh)

# ---- builds ------------------------------------------------------------------------------------------------------
_ids = [0]
def nid(): _ids[0] += 1; return _ids[0]
def room(x0, y0, z0, x1, y1, h, t=0.3, walls=True, wall_phys=(True, True, True, True), ceil=True, ceil_phys=True, obj=None):
    """one build (one object, like a skybox linkset): floor (top at z0), optional ceiling and walls -x +x -y +y"""
    o = obj or nid(); B = [Box((x0 - t, y0 - t, z0 - t, x1 + t, y1 + t, z0), o)]
    if ceil: B.append(Box((x0 - t, y0 - t, z0 + h, x1 + t, y1 + t, z0 + h + t), o, ceil_phys))
    if walls:
        W = [(x0 - t, y0 - t, z0, x0, y1 + t, z0 + h), (x1, y0 - t, z0, x1 + t, y1 + t, z0 + h),
             (x0, y0 - t, z0, x1, y0, z0 + h), (x0, y1, z0, x1, y1 + t, z0 + h)]
        for w, p in zip(W, wall_phys): B.append(Box(w, o, p))
    return B
def furniture(items, z0):
    return [Box((x0, y0, z0, x1, y1, z0 + hh), nid()) for (x0, y0, x1, y1, hh) in items]

def worlds():
    rnd = random.Random(5)
    L = []
    def add_(name, ground, boxes, op, air, expect, indoors="auto", err_p=0.0, yaw=0.0):
        L.append(dict(name=name, W=World(ground, boxes, err_p, random.Random(9)), op=op, air=air, expect=expect, indoors=indoors, yaw=yaw))
    sky = (110, 110, 3000, 130, 130, 3005)                                  # interior air of the standard skybox
    add_("skybox 20x20x5", 20.0, room(110, 110, 3000, 130, 130, 5), (120, 120, 3001.0), [sky], True)
    add_("skybox, ceiling without physics", 20.0, room(110, 110, 3000, 130, 130, 5, ceil_phys=False), (120, 120, 3001.0), [sky], True)
    add_("skybox, two glass walls (no physics)", 20.0, room(110, 110, 3000, 130, 130, 5, wall_phys=(True, False, True, False)), (120, 120, 3001.0), [sky], True)
    add_("skybox, only the floor has physics", 20.0, room(110, 110, 3000, 130, 130, 5, wall_phys=(False,) * 4, ceil_phys=False), (120, 120, 3001.0), [sky], True)
    add_("furnished skybox", 20.0, room(110, 110, 3000, 130, 130, 5) + furniture(
        [(112, 114, 116, 117, 0.9), (118, 117, 121, 118.5, 0.8), (110.3, 122, 111, 129, 2.2), (124, 110.3, 129, 111.2, 2.4),
         (123, 123, 127, 126, 0.7), (115, 125, 115.6, 125.6, 1.8), (127, 114, 128, 115, 1.5), (112, 127, 113, 128, 0.4)], 3000),
         (120, 120, 3001.0), [sky], True)
    stalls = [(x, y, x + rnd.uniform(2, 4), y + rnd.uniform(2, 4), rnd.uniform(2.5, 4.0)) for x in range(72, 180, 12) for y in range(72, 180, 12)
              if not (120 <= x <= 132 or 120 <= y <= 132)]                   # shops in a grid, two aisles through the middle
    add_("sky mall 120x120x10 with 64 shops", 20.0, room(66, 66, 2000, 186, 186, 10) + furniture(stalls, 2000), (126, 126, 2001.0), [(66, 66, 2000, 186, 186, 2010)], True)
    two = room(110, 110, 3000, 130, 130, 9) + [Box((110, 110, 3004.7, 130, 130, 3005.0), nid())]   # a second floor at 3005
    add_("two-storey skybox, you upstairs", 20.0, two, (120, 120, 3006.0), [(110, 110, 3005, 130, 130, 3009)], True)
    add_("tiny skybox 4x4x3", 20.0, room(126, 126, 1500, 130, 130, 3), (128, 128, 1501.0), [(126, 126, 1500, 130, 130, 1503)], True)
    add_("open sky deck (no walls, no roof)", 20.0, room(100, 100, 2000, 130, 130, 5, walls=False, ceil=False), (115, 115, 2001.0), [(100, 100, 2000, 130, 130, 2003.6)], True)
    add_("L-shaped skybox", 20.0, room(100, 100, 2500, 130, 112, 5, obj=900) + room(100, 100, 2500, 112, 130, 5, obj=900), (105, 105, 2501.0),
         [(100, 100, 2500, 130, 112, 2505), (100, 100, 2500, 112, 130, 2505)], True)
    add_("busy region: 25% of rays refused", 20.0, room(110, 110, 3000, 130, 130, 5), (120, 120, 3001.0), [sky], True, err_p=0.25)
    house = room(120, 120, 20.3, 136, 136, 7)
    add_("house on the ground, Auto", 20.0, house, (128, 128, 21.3), [(120, 120, 20.3, 136, 136, 27.3)], True)
    add_("plaza on the ground (floor, no roof), Auto", 20.0, room(100, 100, 20.3, 130, 130, 5, walls=False, ceil=False), (115, 115, 21.3), [], False)
    add_("ground mall, ceiling and walls without physics: Auto", 20.0, room(66, 66, 20.3, 186, 186, 10, wall_phys=(False,) * 4, ceil_phys=False), (126, 126, 21.3), [], False)
    add_("ground mall, ceiling and walls without physics: Inside", 20.0, room(66, 66, 20.3, 186, 186, 10, wall_phys=(False,) * 4, ceil_phys=False), (126, 126, 21.3), [(66, 66, 20.3, 186, 186, 30.3)], True, indoors="inside")
    add_("house on the ground, Indoors=Inside", 20.0, house, (128, 128, 21.3), [(120, 120, 20.3, 136, 136, 27.3)], True, indoors="inside")
    add_("trailer on the ground, Auto", 20.0, room(120, 120, 20.4, 126, 134, 3.2), (123, 127, 21.4), [(120, 120, 20.4, 126, 134, 23.6)], True)
    add_("trailer on the ground, Indoors=Inside", 20.0, room(120, 120, 20.4, 126, 134, 3.2), (123, 127, 21.4), [(120, 120, 20.4, 126, 134, 23.6)], True, indoors="inside")
    add_("skybox, Indoors=Outside", 20.0, room(110, 110, 3000, 130, 130, 5), (120, 120, 3001.0), [], False, indoors="outside")
    add_("open field, Auto", 20.0, [], (128, 128, 21.0), [], False)
    add_("open field, Indoors=Inside (override)", 20.0, [], (128, 128, 21.0), [(0, 0, 20.0, 256, 256, 40.0)], True, indoors="inside")
    return L

def main():
    ok = True
    for w in worlds():
        S = Scenery(w["W"], w["op"], w["indoors"], random.Random(3), w["yaw"])
        kinds, bad, outdoor, noshot, retries = {}, [], 0, 0, 0
        for cut in range(60):
            res, sh = S.nextShot()
            while res == "retry": retries += 1; res, sh = S.nextShot()
            if res == "outdoor": outdoor += 1; continue
            if res == "noshot": noshot += 1; continue
            c = sh[0]; kinds[sh[2]] = kinds.get(sh[2], 0) + 1
            if not any(a[0] - 0.05 <= c[0] <= a[3] + 0.05 and a[1] - 0.05 <= c[1] <= a[4] + 0.05 and a[2] + 0.3 <= c[2] <= a[5] - 0.1 for a in w["air"]):
                bad.append(("outside the interior", tuple(round(x, 1) for x in c), sh[2]))
            elif any(b.inside(c) for b in w["W"].boxes):
                bad.append(("inside a solid part", tuple(round(x, 1) for x in c), sh[2]))
        local = outdoor == 0 and (kinds or noshot)
        shots = sum(kinds.values())
        line = f"{w['name']:40s} " + ("inside " if local else "outdoor") + f"  shots {shots:2d}"
        if kinds: line += "  (" + ", ".join(f"{ {10: 'high', 11: 'eye', 12: 'small', 13: 'close'}[k]} {v}" for k, v in sorted(kinds.items())) + ")"
        if noshot: line += f"  no-shot {noshot}"
        if retries: line += f"  retries {retries}"
        print(line)
        if bool(local) != w["expect"]: ok = False; print(f"   FAIL expected {'inside' if w['expect'] else 'outdoor'}")
        if w["expect"] and outdoor: ok = False; print(f"   FAIL {outdoor} outdoor views while inside")
        for b in bad[:3]: print("   FAIL", *b)
        if bad: ok = False
        # quality: in a normal room most cuts must be real inside views, not the close fallback
        if w["expect"] and w["name"] in ("skybox 20x20x5", "furnished skybox", "sky mall 120x120x10 with 64 shops", "L-shaped skybox",
                                          "skybox, only the floor has physics", "two-storey skybox, you upstairs") and kinds.get(13, 0) > 6:
            ok = False; print(f"   FAIL too many close fallback shots ({kinds.get(13, 0)}/60)")
    # stress: 4 standing spots (two corners, beside a wall, the middle) x 4 facings per inside place, 20 cuts each.
    # Never a bad camera; and in ordinary rooms the close fallback stays rare.
    print("stress: 16 standing spots and facings per inside place, 20 cuts each")
    limits = {"tiny skybox 4x4x3": 1.0, "busy region: 25% of rays refused": 0.6}
    for w in worlds():
        if not w["expect"]: continue
        a = w["air"][0]; tot = close = 0; bad = []
        for (x, y) in ((a[0] + 1.2, a[1] + 1.2), (a[3] - 1.2, a[4] - 1.2), (a[0] + 1.2, (a[1] + a[4]) / 2), ((a[0] + a[3]) / 2, (a[1] + a[4]) / 2)):
            for yaw in (0.0, PI / 2, PI, -PI / 2):
                S = Scenery(w["W"], (x, y, w["op"][2]), w["indoors"], random.Random(int(x * 7 + y * 3 + yaw * 11)), yaw)
                for cut in range(20):
                    res, sh = S.nextShot()
                    while res == "retry": res, sh = S.nextShot()
                    if res == "outdoor": bad.append(("outdoor view", (x, y))); continue
                    if res != "shot": continue
                    c = sh[0]; tot += 1; close += sh[2] == 13
                    if not any(b[0] - 0.05 <= c[0] <= b[3] + 0.05 and b[1] - 0.05 <= c[1] <= b[4] + 0.05 and b[2] + 0.3 <= c[2] <= b[5] - 0.1 for b in w["air"]) \
                       or any(bx.inside(c) for bx in w["W"].boxes):
                        bad.append(("bad camera", tuple(round(v, 1) for v in c)))
        share = close / max(tot, 1); lim = limits.get(w["name"], 0.15)
        print(f"   {w['name']:40s} {tot:3d} shots, close fallback {100 * share:3.0f}% (limit {100 * lim:.0f}%), bad {len(bad)}")
        if bad: ok = False; print("   FAIL", *bad[:2])
        if share > lim: ok = False; print("   FAIL too many close fallback shots")
    # no flipping: walk through a trailer (door at the +y end, 3 m of porch), measuring after each step like the script does
    # on a 10 m move or a refused-ray re-measure; Auto must stay inside all the way to the porch, and go outdoors on open land
    tr = room(120, 120, 20.4, 126, 134, 3.2, walls=True, wall_phys=(True, True, True, False))   # the +y wall is the door side: open
    porch = [Box((120, 134, 20.0, 126, 137, 20.4), nid())]                                        # the porch floor (a prim, no roof)
    W = World(20.0, tr + porch)
    S = Scenery(W, (123, 127, 21.4), "auto", random.Random(2), 0.0)
    path = [(123, 127), (123, 131), (123, 133.5), (123, 135.5), (123, 136.6), (123, 140.0), (123, 150.0), (123, 170.0)]
    seq = []
    for (x, y) in path:
        S.gOP = (x, y, 21.4 if y < 137 else 21.4); S.gCtxOK = False; S.context(); seq.append(S.gLocal)
    print("walk out of a trailer (Auto):", " ".join("in " if v else "out" for v in seq), "  <- inside on the trailer and porch, outdoors once 30 m of open land away")
    if not (all(seq[:5]) and not seq[-1]): ok = False; print("   FAIL the decision flipped or never left")
    changes = sum(1 for i in range(1, len(seq)) if seq[i] != seq[i - 1])
    if changes > 1: ok = False; print(f"   FAIL it flipped {changes} times (more than the one exit)")
    # the bug this file exists to catch: reading Second Life's [key, position] pairs with the wrong stride
    W = World(20.0, room(110, 110, 3000, 130, 130, 5))
    bd = W.llCastRay((120, 120, 3001.3), (120, 120, 2901.0), 4)
    wrong = any(llList2Key(bd, i * 3) == NULL_KEY or llList2Vector(bd, i * 3 + 2)[2] < 3000 - 2.0 for i in range(llList2Integer(bd, -1)))
    print("stride check: reading 3 per hit (the 4.3.1 bug) says", "'not in the sky'" if wrong else "'in the sky'", "for a skybox; 2 per hit says 'in the sky'")
    if not wrong: ok = False; print("   FAIL the stride check no longer reproduces the old bug")
    print("indoor checks:", "ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
