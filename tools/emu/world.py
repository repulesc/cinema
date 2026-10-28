"""The world the Take 12 scripts run in (8.0): a region, avatars, worn HUDs, furniture, builds, virtual time
(tools/emu/lsl_emu.py runs the scripts). What it models, and how:
  - events: one queue in time order; each script runs one event at a time to its end, as in Second Life
  - link messages go to every script of the object (the sender too); region chat reaches every listening object
    but the speaker's own (llRegionSay / llRegionSayTo to an avatar reaches all its attachments; 0.05 s later; a
    message can be dropped on purpose)
  - controls: one request per script (a second llTakeControls replaces that script's first); a key reaches every
    script that accepts it, and moves the avatar unless some script holds it without passing it on
  - the camera: per avatar, from the worn object that set it last (locked spot, the follow camera, a locked corner
    looking at you) or the avatar's own; Alt-orbit shows your own camera over any script's
  - permissions: an attachment's requests to its owner are granted at once (run_time_permissions)
  - prims: every part's name, description, text, position, rotation, size, colour, alpha, texture, glow (getters
    and setters walk PRIM_LINK_TARGET lists like the server); touches on any part reach the root's scripts
  - rays: llCastRay against boxes (only physical ones; the land; one hit per object; RC_MAX_HITS; refusals on request)
  - furniture to sit on (OBJECT_ROOT, NAME, CREATOR, POS, ROT), ground sits, flying, mouselook, away, typing,
    teleports and region crossings (CHANGED_TELEPORT / CHANGED_REGION), parcels (PARCEL_DETAILS_ID)
  - several objects worn by one avatar; a rezzed object (the builder) with llRezObject, object_rez, llCreateLink
  - protected Linkset Data per object, llDialog (kept for the test to click), llOwnerSay (kept as the avatar's chat log)

    w = World(); ana = w.avatar("Ana", (128, 128, 21)); ana.wear(HUD_SCRIPTS); w.run(5)
"""
import heapq, itertools, math, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lsl_emu import compile_file, Script, Key, Vector, Quaternion, CONST, B, LSLError

C = CONST
NULL = C["NULL_KEY"]
ZV = Vector((0.0, 0.0, 0.0))
ZR = Quaternion((0.0, 0.0, 0.0, 1.0))
CTL_MOVE = C["CONTROL_FWD"] | C["CONTROL_BACK"] | C["CONTROL_LEFT"] | C["CONTROL_RIGHT"]
_keys = itertools.count(1)
_gens = itertools.count(1)
def new_key(): return Key("%08x-0000-4000-8000-%012x" % (0x7ac0012, next(_keys)))
def vec(*a): return Vector(tuple(float(x) for x in a))
def yaw_rot(deg):
    h = math.radians(deg) / 2
    return Quaternion((0.0, 0.0, math.sin(h), math.cos(h)))
def rot_yaw(q):
    f = B.llRot2Fwd(q)
    return math.degrees(math.atan2(f[1], f[0]))

# the parts of the 8.0 HUD (hud/build/builder.lsl makes them)
PARTS = ["t12 ring", "t12 dot", "t12 band", "t12 s0", "t12 s1", "t12 s2", "t12 s3", "t12 box", "t12 halo",
         "t12 o0", "t12 o1", "t12 o2", "t12 o3", "t12 o4", "t12 o5", "t12 sep", "t12 u0", "t12 u1", "t12 u2",
         "t12 shape", "t12 link", "t12 note", "t12 bar0", "t12 bar1", "t12 bar2", "t12 bar3", "t12 shut", "t12 auto"]


# ---- builds the rays see -----------------------------------------------------------------------------------------
class Box:
    def __init__(s, b, obj, phys=True): s.b, s.obj, s.phys = tuple(float(x) for x in b), obj, phys
    def inside(s, p, m=0.0):
        b = s.b
        return b[0] + m < p[0] < b[3] - m and b[1] + m < p[1] < b[4] - m and b[2] + m < p[2] < b[5] - m

def room(x0, y0, z0, x1, y1, h, t=0.3, walls=True, ceil=True, obj=None, door=None):
    """one build (one object): floor (top at z0), ceiling, walls -x +x -y +y; door: a gap in the -x wall (y0, y1)"""
    o = obj or new_key()
    L = [Box((x0 - t, y0 - t, z0 - t, x1 + t, y1 + t, z0), o)]
    if ceil: L.append(Box((x0 - t, y0 - t, z0 + h, x1 + t, y1 + t, z0 + h + t), o))
    if walls:
        if door:
            L += [Box((x0 - t, y0 - t, z0, x0, door[0], z0 + h), o), Box((x0 - t, door[1], z0, x0, y1 + t, z0 + h), o)]
        else:
            L.append(Box((x0 - t, y0 - t, z0, x0, y1 + t, z0 + h), o))
        L += [Box((x1, y0 - t, z0, x1 + t, y1 + t, z0 + h), o), Box((x0, y0 - t, z0, x1, y0, z0 + h), o),
              Box((x0, y1, z0, x1, y1 + t, z0 + h), o)]
    return L


class World:
    def __init__(s, seed=1, region="Take 12 Lab", ground=20.0, water=19.0, boxes=(), parcels=None):
        s.t = 0.0
        s.q = []
        s.seq = itertools.count()
        s.avatars = {}                                 # key -> Avatar
        s.objects = {}                                 # key -> Obj (worn or rezzed)
        s.things = {}                                  # key -> Furniture
        s.region = region
        s.ground, s.water = ground, water
        s.boxes = list(boxes)
        s.parcels = parcels or [((0, 0, 256, 256), new_key())]
        s.rng = random.Random(seed)
        s.drop = 0.0                                   # chance that a region chat message is lost
        s.refuse = 0.0                                 # chance that a ray is refused (a busy region)
        s.errors = []                                  # script errors (Math Error, a bad cast, a missing stub)
        s.emails = []                                  # llEmail: (time, script, to, subject, body)
        s.given = []                                   # llGiveInventoryList: (to, folder, items)
        s.chatlog = []                                 # (t, from, to, message) on the Connect channel
        s.base_unix = 1_800_000_000

    def avatar(s, name, pos, **kw):
        a = Avatar(s, name, pos, **kw)
        s.avatars[a.key] = a
        return a

    def furniture(s, name, pos, yaw=0.0, creator=None, size=(1.0, 2.0, 0.5)):
        f = Furniture(s, name, pos, yaw, creator, size)
        s.things[f.key] = f
        return f

    def post(s, dt, fn, *args):
        heapq.heappush(s.q, (s.t + dt, next(s.seq), fn, args))

    def run(s, seconds):
        end = s.t + seconds
        while s.q and s.q[0][0] <= end:
            t, _, fn, args = heapq.heappop(s.q)
            s.t = max(s.t, t)
            fn(*args)
        s.t = end

    def parcel(s, p):
        for (x0, y0, x1, y1), k in s.parcels:
            if x0 <= p[0] < x1 and y0 <= p[1] < y1: return k
        return s.parcels[0][1]

    # ---- rays ------------------------------------------------------------------------------------------------------
    def cast(s, a, b, max_hits=1, agents=False):
        if s.refuse and s.rng.random() < s.refuse: return [-3]          # RCERR_CAST_TIME_EXCEEDED
        d = B.sub(b, a)
        hits = {}
        for bx in s.boxes:
            if not bx.phys or bx.inside(a): continue                    # no physics, or the ray starts inside it
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
            if ok and t0 > 1e-9 and (bx.obj not in hits or t0 < hits[bx.obj]): hits[bx.obj] = t0
        out = [(t, k) for k, t in hits.items()]
        if a[2] > s.ground >= b[2]: out.append(((a[2] - s.ground) / (a[2] - b[2]), NULL))   # the land
        if agents:
            for av in s.avatars.values():
                if not av.in_region: continue
                c = B.add(av.pos, vec(0, 0, 0))
                t = _seg_sphere(a, d, c, 0.4)
                if t is not None and t > 1e-6: out.append((t, av.key))
        out.sort()
        flat = []
        for t, k in out[:max_hits]: flat += [Key(k), B.add(a, B.mul(d, t))]
        return flat + [len(out[:max_hits])]

    # ---- chat --------------------------------------------------------------------------------------------------------
    def chat(s, speaker, channel, msg, to=None, name=""):
        """speaker: an Obj or an Avatar; to: an avatar or object key (llRegionSayTo), None = the whole region"""
        if channel == -7712120: s.chatlog.append((round(s.t, 2), getattr(speaker, "owner_name", name), to, msg))
        if s.drop and channel != 0 and s.rng.random() < s.drop: return
        for o in list(s.objects.values()):
            if o is speaker or not (o.worn or o.rezzed): continue
            if to is not None and to != o.key and to != o.owner.key: continue
            for sc in o.live():
                for h, (ch, nm, idk, m) in list(sc.listens.items()):
                    if ch != channel: continue
                    if nm and nm != name: continue
                    if idk and idk != getattr(speaker, "key", None): continue
                    if m and m != msg: continue
                    s.post(0.05, o.event, sc, "listen", (channel, name, Key(speaker.key), msg))


def _seg_sphere(a, d, c, r):
    f = B.sub(a, c)
    A = d[0] ** 2 + d[1] ** 2 + d[2] ** 2
    if A < 1e-12: return None
    Bq = 2 * (f[0] * d[0] + f[1] * d[1] + f[2] * d[2])
    Cq = f[0] ** 2 + f[1] ** 2 + f[2] ** 2 - r * r
    disc = Bq * Bq - 4 * A * Cq
    if disc < 0: return None
    t = (-Bq - math.sqrt(disc)) / (2 * A)
    return t if 0 <= t <= 1 else None


class Furniture:
    def __init__(s, w, name, pos, yaw, creator, size):
        s.w, s.name, s.key = w, name, new_key()
        s.pos, s.rot = vec(*pos), yaw_rot(yaw)
        s.creator = creator or new_key()
        s.size = size


class Avatar:
    def __init__(s, w, name, pos, sitting=False, flying=False):
        s.w, s.name, s.key = w, name, new_key()
        s.pos, s.rot, s.vel = vec(*pos), ZR, ZV
        s.seat = None                                  # a Furniture, "ground", or None
        s.flying, s.typing, s.away, s.mouselook, s.in_region = flying, False, False, False, True
        s.region = w.region
        s.size = vec(0.45, 0.6, 1.8)
        s.fov, s.aspect = 1.047198, 1.778
        s.held = 0                                     # control bits held now
        s.own_cam = None                               # Alt-orbit: where you put your own camera (None: behind you)
        s.orbit = False
        s.huds = []                                    # worn objects, in the order worn
        s.chat = []                                    # what the scripts said to this avatar (llOwnerSay), with time
        s.texts = []                                   # every floating text put on a worn part: (t, part, text)
        s.sounds = []
        s.dialog = None                                # the last llDialog: (object, text, buttons, channel)
        s._walk = 0
        if sitting: s.seat = "ground"

    def __repr__(s): return "<%s>" % s.name

    @property
    def hud(s): return s.huds[-1] if s.huds else None
    @property
    def sitting(s): return s.seat is not None

    def wear(s, paths, point="ATTACH_HUD_TOP_CENTER", parts=PARTS, lsd=None, desc=""):
        o = Obj(s.w, s, paths, children=parts, point=C[point], desc=desc)
        if lsd: o.lsd.update(lsd)
        s.w.objects[o.key] = o
        s.huds.append(o)
        o.attach()
        return o

    def take_off(s, o=None):
        o = o or s.hud
        if o:
            o.detach()
            if o in s.huds: s.huds.remove(o)

    # ---- the camera this avatar sees ---------------------------------------------------------------------------------
    def camera(s):
        """(pos, focus, scripted?) of what the viewer shows"""
        if s.orbit and s.own_cam: return s.own_cam[0], s.own_cam[1], False
        cams = [o.cam for o in s.huds if o.worn and o.cam.get("active")]
        if cams:
            c = max(cams, key=lambda c: c.get("t", 0))
            if c.get("plock") and "pos" in c:
                if c.get("flock", True) and "focus" in c: return c["pos"], c["focus"], True
                return c["pos"], B.add(s.pos, B.mul(c.get("offset", ZV), 1.0)), True
            if "distance" in c:
                foc = B.add(s.pos, _rotv(c.get("offset", ZV), s.rot))
                p = math.radians(c.get("pitch", 0.0))
                if "freeaz" in c:
                    a = c["freeaz"]
                    return B.add(foc, vec(math.cos(a) * math.cos(p) * c["distance"], math.sin(a) * math.cos(p) * c["distance"], math.sin(p) * c["distance"])), foc, True
                back = _rotv(vec(-math.cos(p) * c["distance"], 0.0, math.sin(p) * c["distance"]), s.rot)
                return B.add(foc, back), foc, True
        if s.own_cam: return s.own_cam[0], s.own_cam[1], False
        behind = _rotv(vec(-3.0, 0.0, 1.0), s.rot)
        return B.add(s.pos, behind), B.add(s.pos, vec(0, 0, 0.5)), False

    # ---- moving --------------------------------------------------------------------------------------------------------
    def face(s, deg): s.rot = yaw_rot(deg)

    def walk(s, to, speed=1.5):
        """walk in a straight line to a point (facing it), then stand still"""
        to = vec(*to)
        s._walk += 1
        d = B.sub(to, s.pos)
        L = math.hypot(d[0], d[1])
        if L < 0.01: return
        s.face(math.degrees(math.atan2(d[1], d[0])))
        s.vel = vec(d[0] / L * speed, d[1] / L * speed, 0.0)
        s._step(s._walk, to, speed)

    def _step(s, gen, to, speed):
        if gen != s._walk: return
        d = B.sub(to, s.pos)
        L = math.hypot(d[0], d[1])
        step = speed * 0.1
        if L <= step:
            s.pos = vec(to[0], to[1], s.pos[2])
            s.vel = ZV
            return
        s.pos = vec(s.pos[0] + d[0] / L * step, s.pos[1] + d[1] / L * step, s.pos[2])
        s.w.post(0.1, s._step, gen, to, speed)

    def sit_on(s, f, at=(0.0, 0.0, 0.6), yaw=0.0):
        s._walk += 1
        s.seat = f
        s.pos = B.add(f.pos, _rotv(vec(*at), f.rot))
        s.rot = yaw_rot(rot_yaw(f.rot) + yaw)
        s.vel = ZV

    def sit_ground(s):
        s._walk += 1
        s.seat = "ground"
        s.vel = ZV

    def stand(s):
        s.seat = None

    def teleport(s, pos, region=None):
        s._walk += 1
        s.vel = ZV
        s.seat = None
        cross = region is not None and region != s.region
        if region: s.region = region
        s.pos = vec(*pos)
        what = C["CHANGED_TELEPORT"] | (C["CHANGED_REGION"] if cross else 0)
        for o in s.huds:
            if o.worn: o._changed(what)

    # ---- input ---------------------------------------------------------------------------------------------------------
    def keys(s, bits, hold=0.3):
        """press and hold movement keys for a while, then let go"""
        s._keys(bits)
        s.w.post(hold, s._keys, 0)

    def _keys(s, held):
        old, s.held = s.held, held
        edge = old ^ held
        blocked = 0
        for o in s.huds:
            if not o.worn: continue
            for sc in o.live():
                mask, accept, passon = sc.ctl
                if accept and (mask & (held | edge)) and sc.has("control"):
                    o.event(sc, "control", (Key(s.key), held & mask, edge & mask))
                if not passon: blocked |= mask
        moving = held & CTL_MOVE & ~blocked
        if moving and not s.sitting:
            f = 0.8 if moving & 1 else (-0.8 if moving & 2 else 0)
            s.pos = B.add(s.pos, _rotv(vec(f, 0.0, 0.0), s.rot))
            if f:                                      # walking with the keys moves you, as in-world (8.4.0: it had no speed)
                s.vel = _rotv(vec(f * 5.0, 0.0, 0.0), s.rot)
                s._kvel = True
        elif getattr(s, "_kvel", False):
            s.vel, s._kvel = ZV, False
        if held: s.w.post(0.2, s._repeat, held)

    def _repeat(s, held):
        if s.held == held and held: s._keys(held)

    def touch(s, link=1, hold=0.1, o=None, uv=(0.5, 0.5)):
        o = o or s.hud
        if isinstance(link, str): link = o.link(link)
        det = [{"key": Key(s.key), "link": link, "st": vec(uv[0], uv[1], 0), "uv": vec(uv[0], uv[1], 0)}]
        for sc in o.live():
            if sc.has("touch_start"): o.event(sc, "touch_start", (1,), det)
        def end():
            for sc in o.live():
                if sc.has("touch_end"): o.event(sc, "touch_end", (1,), det)
        s.w.post(hold, end)

    def alt_orbit(s, to=None, focus=None):
        p = s.camera()[0]
        s.own_cam = (vec(*to) if to else B.add(p, vec(0.0, 2.5, 1.0)), vec(*focus) if focus else s.pos)
        s.orbit = True

    def esc(s):
        s.orbit = False
        s.own_cam = None

    def tap(s): s.touch()
    def double_tap(s):
        s.touch()
        s.w.post(0.2, s.touch)
    def long_press(s): s.touch(hold=1.2)

    def click(s, label):
        """press a button of the dialog on screen"""
        if not s.dialog: raise AssertionError("%s: no dialog open (wanted %r)" % (s.name, label))
        o, text, buttons, ch = s.dialog
        if label not in buttons:
            raise AssertionError("%s: %r is not on the dialog %r" % (s.name, label, [b for b in buttons if b.strip()]))
        s.dialog = None
        s.say(ch, label)

    def say(s, channel, msg):
        s.w.chat(s, channel, msg, name=s.name)

    def type(s, text):
        """write in the text box on screen and press Submit"""
        if not s.dialog or s.dialog[2] != ["<text>"]: raise AssertionError("%s: no text box open" % s.name)
        ch = s.dialog[3]
        s.dialog = None
        s.say(ch, text)

    def labels(s): return [b for b in (s.dialog[2] if s.dialog else []) if b.strip()]

    def notes(s, since=0.0):
        return [t for (tm, part, t) in s.texts if tm >= since and t]


def _rotv(v, q):
    return B.mul(v, q)


def _prim(name, desc=""):
    return {"key": new_key(), "name": name, "desc": desc, "text": "", "pos": ZV, "rot": ZR, "size": vec(0.01, 0.01, 0.01),
            "color": vec(1, 1, 1), "alpha": 1.0, "tex": (Key(C["TEXTURE_BLANK"]), vec(1, 1, 0), ZV, 0.0), "glow": 0.0,
            "full": 0, "slice": vec(0, 1, 0)}


class Obj:
    """a worn HUD (or a rezzed object): the root prim (all scripts) and its parts"""
    def __init__(s, w, owner, paths, children=PARTS, point=0, textures=(), notecards=(), desc="", rezzed=False):
        s.w, s.owner, s.key = w, owner, new_key()
        s.owner_name = owner.name
        s.name = "Take 12"
        s.point = point
        s.prims = [_prim("Take 12", desc)] + [_prim(n) for n in children]
        s.prims[0]["key"] = s.key
        s.inventory = {t: ("texture", new_key(), True) for t in textures}
        s.inventory.update({n: ("notecard", new_key(), True) for n in notecards})
        s.lsd = {}
        s.cam = {}
        s.worn = False
        s.rezzed = rezzed
        s.pos = ZV
        s.scripts = [Script(compile_file(p), s) for p in paths]
        for sc in s.scripts: s._init(sc)

    def live(s): return [sc for sc in s.scripts if not getattr(sc, "dead", False)]

    def link(s, name):
        for i, p in enumerate(s.prims):
            if p["name"] == name: return i + 1
        raise KeyError(name)

    def part(s, name): return s.prims[s.link(name) - 1]

    def _init(s, sc):
        sc.listens, sc.nl = {}, 1
        sc.timer, sc.timer_gen = 0.0, next(_gens)
        sc.perms, sc.perm_key = 0, Key("")
        sc.ctl = (0, False, True)
        sc.t0 = s.w.t

    def attach(s):
        s.worn = True
        for sc in s.live(): s.reset(sc)                 # on_rez resets every script (they all call llResetScript)
        for sc in s.live():
            if sc.has("attach"): s.event(sc, "attach", (Key(s.owner.key),))

    def rez(s):
        s.rezzed = True
        for sc in s.live(): s.reset(sc)

    def detach(s):
        for sc in s.live():
            if sc.has("attach"): s._run(sc, "attach", (Key(NULL),), None, sc.timer_gen)
        s.worn = False
        s.cam = {}

    def reset(s, sc):
        s._init(sc)
        sc.reset_vars()
        sc.queue = []
        if sc.has("state_entry"): s.event(sc, "state_entry", ())

    def event(s, sc, name, args, detected=None, dt=0.0):
        s.w.post(dt, s._run, sc, name, args, detected, sc.timer_gen)

    def _run(s, sc, name, args, detected, gen):
        if gen != sc.timer_gen or getattr(sc, "dead", False) or getattr(sc, "stopped", False): return
        if not (s.worn or s.rezzed) and name != "attach": return
        try:
            sc.run(name, args, detected)
        except _Reset:
            s.reset(sc)
        except LSLError as e:
            s.w.errors.append((round(s.w.t, 2), s.owner.name, sc.name, name, str(e)))
        except NotImplementedError as e:
            s.w.errors.append((round(s.w.t, 2), s.owner.name, sc.name, name, "not emulated: " + str(e)))

    def _changed(s, what):
        for sc in s.live():
            if sc.has("changed"): s.event(sc, "changed", (what,))

    def send(s, num, msg, k=""):
        """a link message into the object, as if one of its scripts sent it"""
        for sc in s.live():
            if sc.has("link_message"): s.event(sc, "link_message", (1, num, msg, Key(k)))

    def drop(s, name, kind="texture", full=True):
        """you drop an item into the contents (full: you have full permissions on it)"""
        s.inventory[name] = (kind, new_key(), full)
        s._changed(C["CHANGED_INVENTORY"])

    # ---- the built-ins that touch the world (called as world.llName(script, *args)) ----------------------------------
    # time
    def llGetUnixTime(s, sc): return int(s.w.base_unix + s.w.t)
    def llGetDate(s, sc):
        import time as _t
        return _t.strftime("%Y-%m-%d", _t.gmtime(int(s.w.base_unix + s.w.t)))
    def llGetTime(s, sc): return B.F32(s.w.t - sc.t0)
    def llSetTimerEvent(s, sc, t):
        sc.timer = t
        sc.tgen = getattr(sc, "tgen", 0) + 1
        if t > 0: s.w.post(t, s._timer, sc, sc.tgen, sc.timer_gen)
    def _timer(s, sc, tg, gen):
        if tg != sc.tgen or gen != sc.timer_gen or sc.timer <= 0 or not (s.worn or s.rezzed): return
        s._run(sc, "timer", (), None, gen)
        if tg == sc.tgen and sc.timer > 0: s.w.post(sc.timer, s._timer, sc, tg, gen)
    def llResetScript(s, sc): raise _Reset()
    def llFrand(s, sc, m): return B.F32(s.w.rng.random() * m)
    def llGetFreeMemory(s, sc):
        """64 KB less the static estimate (tools/lslmem.py), the globals, and the biggest list built (twice: += copies)"""
        return int(LIMIT - static(sc.prog.path) - sc.globals_bytes() - 2 * sc.peak)
    # sensors: avatars around the wearer (not the wearer), nearest first, at most 16
    def llSensor(s, sc, name, k, kind, rng, arc): s._sense(sc, rng, getattr(sc, "sgen", 0))
    def llSensorRepeat(s, sc, name, k, kind, rng, arc, rate):
        sc.sgen = getattr(sc, "sgen", 0) + 1
        sc.srate, sc.srange = rate, rng
        s.w.post(rate, s._sweep, sc, sc.sgen, sc.timer_gen)
    def llSensorRemove(s, sc): sc.sgen = getattr(sc, "sgen", 0) + 1
    def _sweep(s, sc, g, gen):
        if g != getattr(sc, "sgen", 0) or gen != sc.timer_gen or not (s.worn or s.rezzed): return
        s._sense(sc, sc.srange, g)
        s.w.post(sc.srate, s._sweep, sc, g, gen)
    def _sense(s, sc, rng, g):
        me = s.owner
        L = sorted(((B.llVecDist(a.pos, me.pos), a) for a in s.w.avatars.values()
                    if a is not me and s._here(a) and B.llVecDist(a.pos, me.pos) <= rng), key=lambda x: x[0])[:16]
        det = [{"key": Key(a.key), "pos": a.pos, "name": a.name + " Resident", "link": 0} for d, a in L]
        if det:
            if sc.has("sensor"): s.event(sc, "sensor", (len(det),), det)
        elif sc.has("no_sensor"): s.event(sc, "no_sensor", ())
    def llGetScriptName(s, sc): return sc.name
    def llSleep(s, sc, t): pass
    # messages
    def llMessageLinked(s, sc, link, num, msg, k):
        for o in s.live():
            if o.has("link_message"): s.event(o, "link_message", (1, num, msg, Key(k)))
    def llListen(s, sc, ch, name, k, msg):
        h = sc.nl; sc.nl += 1
        sc.listens[h] = (ch, name, k if k and k != NULL else "", msg)
        return h
    def llListenRemove(s, sc, h): sc.listens.pop(h, None)
    def llRegionSay(s, sc, ch, msg): s.w.chat(s, ch, msg, name=s.name)
    def llRegionSayTo(s, sc, to, ch, msg): s.w.chat(s, ch, msg, to=to, name=s.name)
    def llOwnerSay(s, sc, msg): s.owner.chat.append((round(s.w.t, 2), sc.name, msg))
    def llDialog(s, sc, av, text, buttons, ch):
        if av == s.owner.key: s.owner.dialog = (s, text, list(buttons), ch)
    def llTextBox(s, sc, av, text, ch):
        if av == s.owner.key: s.owner.dialog = (s, text, ["<text>"], ch)     # Avatar.type() answers it
    def llEmail(s, sc, to, subject, body):
        s.w.emails.append((round(s.w.t, 2), sc.name, to, subject, body))   # (the script's 20 s pause is not emulated)
    def llLoadURL(s, sc, av, msg, url): s.owner.chat.append((round(s.w.t, 2), sc.name, "[url] " + url))
    def llGiveInventory(s, sc, k, name): pass
    def llGiveInventoryList(s, sc, k, folder, items):
        s.w.given.append((str(k), folder, list(items)))                    # (to, folder, the items)
    def llPlaySound(s, sc, snd, vol): s.owner.sounds.append((round(s.w.t, 2), snd))
    # permissions, controls, the camera
    def llRequestPermissions(s, sc, k, perms):
        if k == s.owner.key and (s.worn or s.rezzed):
            sc.perms, sc.perm_key = perms, Key(k)
            if sc.has("run_time_permissions"): s.event(sc, "run_time_permissions", (perms,))
    def llGetPermissions(s, sc): return sc.perms
    def llGetPermissionsKey(s, sc): return sc.perm_key
    def llTakeControls(s, sc, mask, accept, passon):
        if not sc.perms & C["PERMISSION_TAKE_CONTROLS"]: return
        sc.ctl = (mask, bool(accept), bool(passon))
    def llReleaseControls(s, sc):
        sc.ctl = (0, False, True)
        sc.perms &= ~C["PERMISSION_TAKE_CONTROLS"]
    _CAM = {"CAMERA_ACTIVE": "active", "CAMERA_POSITION": "pos", "CAMERA_FOCUS": "focus", "CAMERA_POSITION_LOCKED": "plock",
            "CAMERA_FOCUS_LOCKED": "flock", "CAMERA_DISTANCE": "distance", "CAMERA_PITCH": "pitch",
            "CAMERA_FOCUS_OFFSET": "offset", "CAMERA_POSITION_LAG": "plag", "CAMERA_FOCUS_LAG": "flag",
            "CAMERA_BEHINDNESS_LAG": "blag", "CAMERA_BEHINDNESS_ANGLE": "bangle"}
    def llSetCameraParams(s, sc, rules):
        if not sc.perms & C["PERMISSION_CONTROL_CAMERA"]: return
        names = {C[k]: v for k, v in s._CAM.items()}
        prev = s.owner.camera()[0]
        for i in range(0, len(rules) - 1, 2):
            if rules[i] in names: s.cam[names[rules[i]]] = rules[i + 1]
        if s.cam.get("bangle", 0) >= 90 and not s.cam.get("plock") and "freeaz" not in s.cam:
            d = B.sub(prev, s.owner.pos)                          # behindness 180: it stays on the side it is on
            s.cam["freeaz"] = math.atan2(d[1], d[0])
        if s.cam.get("bangle", 0) < 90: s.cam.pop("freeaz", None)
        s.cam["by"] = sc.name
        s.cam["t"] = s.w.t
        s.cam.setdefault("log", []).append((round(s.w.t, 2), sc.name, s.cam.get("pos"), s.cam.get("focus")))
    def llClearCameraParams(s, sc):
        if sc.perms & C["PERMISSION_CONTROL_CAMERA"]: s.cam = {"cleared_by": sc.name, "t": s.w.t, "log": s.cam.get("log", [])}
    def llGetCameraPos(s, sc): return s.owner.camera()[0] if sc.perms & C["PERMISSION_TRACK_CAMERA"] else ZV
    def llGetCameraRot(s, sc):
        if not sc.perms & C["PERMISSION_TRACK_CAMERA"]: return ZR
        p, f, _ = s.owner.camera()
        d = B.sub(f, p)
        if B.llVecMag(d) < 0.001: return ZR
        yaw = math.atan2(d[1], d[0])
        pitch = -math.atan2(d[2], math.hypot(d[0], d[1]))
        return B.mul(Quaternion((0.0, math.sin(pitch / 2), 0.0, math.cos(pitch / 2))), Quaternion((0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2))))
    # as in Second Life, 0 without PERMISSION_TRACK_CAMERA (8.0.5: portrait never asked, read 0, and framed for 60°)
    def llGetCameraFOV(s, sc): return B.F32(s.owner.fov) if sc.perms & C["PERMISSION_TRACK_CAMERA"] else 0.0
    def llGetCameraAspect(s, sc): return B.F32(s.owner.aspect) if sc.perms & C["PERMISSION_TRACK_CAMERA"] else 0.0
    # the object
    def llGetOwner(s, sc): return Key(s.owner.key)
    def llGetKey(s, sc): return Key(s.key)
    def llGetAttached(s, sc): return s.point if s.worn else 0
    def llGetObjectDesc(s, sc): return s.prims[0]["desc"]
    def llSetObjectDesc(s, sc, d): s.prims[0]["desc"] = d[:127]      # (a description holds 127 characters)
    def llDetachFromAvatar(s, sc):
        """back to the inventory (8.4.0, the box you wear): only worn, only with PERMISSION_ATTACH; after this event"""
        if s.worn and sc.perms & C["PERMISSION_ATTACH"]:
            s.w.post(0.0, lambda: s.owner.take_off(s))
    def llGetNumberOfPrims(s, sc): return len(s.prims)
    def llGetLinkName(s, sc, link):
        if link == C["LINK_ROOT"]: link = 1
        return s.prims[link - 1]["name"] if 1 <= link <= len(s.prims) else ""
    def llGetLinkKey(s, sc, link): return s.prims[link - 1]["key"] if 1 <= link <= len(s.prims) else Key(NULL)
    def llGetNumberOfSides(s, sc): return 6
    def llGetPos(s, sc): return s.owner.pos if s.worn else s.pos
    def llGetRot(s, sc): return s.owner.rot if s.worn else ZR
    def llGetLocalPos(s, sc): return s.prims[0]["pos"]
    def llGetLocalRot(s, sc): return s.prims[0]["rot"]
    def llGetScale(s, sc): return s.prims[0]["size"]
    def llSetText(s, sc, text, color, alpha): s._text(1, text)
    def _text(s, link, text):
        s.prims[link - 1]["text"] = text[:254]
        s.owner.texts.append((round(s.w.t, 2), s.prims[link - 1]["name"], text[:254]))
    def llGetPrimitiveParams(s, sc, rules): return s._params(1, rules)
    def llGetLinkPrimitiveParams(s, sc, link, rules): return s._params(link, rules)
    def _params(s, link, rules):
        if link == C["LINK_ROOT"]: link = 1
        p = s.prims[link - 1] if 1 <= link <= len(s.prims) else _prim("")
        out, i = [], 0
        while i < len(rules):
            r = rules[i]
            if r == C["PRIM_TEXT"]: out += [p["text"], vec(1, 1, 1), 1.0]
            elif r == C["PRIM_NAME"]: out += [p["name"]]
            elif r == C["PRIM_DESC"]: out += [p["desc"]]
            elif r == C["PRIM_POS_LOCAL"]: out += [p["pos"]]
            elif r == C["PRIM_ROT_LOCAL"]: out += [p["rot"]]
            elif r == C["PRIM_SIZE"]: out += [p["size"]]
            elif r == C["PRIM_COLOR"]: out += [p["color"], p["alpha"]]; i += 1
            elif r == C["PRIM_TEXTURE"]: out += list(p["tex"]); i += 1
            elif r == C["PRIM_GLOW"]: out += [p["glow"]]; i += 1
            elif r == C["PRIM_SLICE"]: out += [p["slice"]]
            i += 1
        return out
    def llSetPrimitiveParams(s, sc, rules): s._apply(1, rules)
    def llSetLinkPrimitiveParams(s, sc, link, rules): s._apply(link, rules)
    def llSetLinkPrimitiveParamsFast(s, sc, link, rules): s._apply(link, rules)
    def _apply(s, link, rules):
        i, cur = 0, link
        while i < len(rules):
            r = rules[i]
            if r == C["PRIM_LINK_TARGET"]:
                cur = rules[i + 1]; i += 2; continue
            targets = [cur]
            if cur in (C["LINK_ROOT"], C["LINK_THIS"]): targets = [1]          # (scripts sit in the root here)
            elif cur == C["LINK_SET"]: targets = list(range(1, len(s.prims) + 1))
            elif cur == C["LINK_ALL_CHILDREN"]: targets = list(range(2, len(s.prims) + 1))
            if r == C["PRIM_TYPE"]:
                n = {C["PRIM_TYPE_BOX"]: 6, C["PRIM_TYPE_CYLINDER"]: 6, C["PRIM_TYPE_PRISM"]: 6}.get(rules[i + 1], 6)
                i += 2 + n; continue
            n = _NARGS.get(r, 1)
            a = rules[i + 1:i + 1 + n]
            for t in targets:
                if not 1 <= t <= len(s.prims): continue
                p = s.prims[t - 1]
                if r == C["PRIM_NAME"]: p["name"] = a[0]
                elif r == C["PRIM_DESC"]: p["desc"] = a[0][:127]          # (127 characters, as llSetObjectDesc)
                elif r == C["PRIM_TEXT"]: s._text(t, a[0])
                elif r in (C["PRIM_POS_LOCAL"], C["PRIM_POSITION"]): p["pos"] = a[0]
                elif r in (C["PRIM_ROT_LOCAL"], C["PRIM_ROTATION"]): p["rot"] = a[0]
                elif r == C["PRIM_SIZE"]: p["size"] = a[0]
                elif r == C["PRIM_COLOR"]: p["color"], p["alpha"] = a[1], a[2]
                elif r == C["PRIM_TEXTURE"]: p["tex"] = (a[1], a[2], a[3], a[4])
                elif r == C["PRIM_GLOW"]: p["glow"] = a[1]
                elif r == C["PRIM_FULLBRIGHT"]: p["full"] = a[1]
                elif r == C["PRIM_SLICE"]: p["slice"] = a[0]
            i += 1 + n
    # the builder: rezzing and linking
    def llRezObject(s, sc, name, pos, vel, rot, param):
        if s.inventory.get(name, ("",))[0] != "object": return
        o = Obj(s.w, s.owner, [], children=(), rezzed=True)
        o.name = name
        o.prims[0]["name"] = name
        o.pos = pos
        s.w.objects[o.key] = o
        for x in s.live():
            if x.has("object_rez"): s.event(x, "object_rez", (Key(o.key),), dt=0.1)
    def llCreateLink(s, sc, target, parent):
        o = s.w.objects.get(target)
        if not o or not sc.perms & C["PERMISSION_CHANGE_LINKS"]: return
        del s.w.objects[target]
        s.prims[1:1] = o.prims                          # the new part is link 2
        s._changed(C["CHANGED_LINK"])
    def llRemoveInventory(s, sc, name):
        if s.inventory.pop(name, None): s._changed(C["CHANGED_INVENTORY"])
        else:
            for x in s.scripts:
                if x.name == name: x.dead = True
    # inventory and Linkset Data
    def llGetInventoryType(s, sc, name):
        if name in s.inventory: return C["INVENTORY_" + s.inventory[name][0].upper()]
        if any(x.name == name and not getattr(x, "dead", False) for x in s.scripts): return C["INVENTORY_SCRIPT"]
        return C["INVENTORY_NONE"]
    def _names(s, t):
        L = [n for n, v in s.inventory.items() if C["INVENTORY_" + v[0].upper()] == t or t == C["INVENTORY_ALL"]]
        if t in (C["INVENTORY_SCRIPT"], C["INVENTORY_ALL"]): L += [x.name for x in s.scripts if not getattr(x, "dead", False)]
        return sorted(L)
    def llGetInventoryNumber(s, sc, t): return len(s._names(t))
    def llGetInventoryName(s, sc, t, i):
        L = s._names(t)
        return L[i] if 0 <= i < len(L) else ""
    # a script's running state (8.5.0, carry's watchdog): a run-time error stops a script, as in-world (crash())
    def _script(s, name):
        for x in s.scripts:
            if x.name == name and not getattr(x, "dead", False): return x
    def crash(s, name):
        """the script stops, as after "Stack-Heap Collision": no more events until it is started again"""
        s._script(name).stopped = True
    def llGetScriptState(s, sc, name):
        x = s._script(name)
        return int(bool(x) and not getattr(x, "stopped", False))
    def llResetOtherScript(s, sc, name):
        x = s._script(name)
        if not x: return
        if getattr(x, "stopped", False):
            s._init(x); x.reset_vars(); x.queue = []; x.timer_gen = next(_gens); x.fresh = True   # runs when started
        else: s.reset(x)
    def llSetScriptState(s, sc, name, run):
        x = s._script(name)
        if not x: return
        was = getattr(x, "stopped", False)
        x.stopped = not run
        if run and was and getattr(x, "fresh", False):
            x.fresh = False
            if x.has("state_entry"): s.event(x, "state_entry", ())
    def llGetInventoryKey(s, sc, name):
        v = s.inventory.get(name)
        return v[1] if v and v[2] else Key(NULL)
    def llLinksetDataReadProtected(s, sc, k, pw):
        v = s.lsd.get(k)
        return v[0] if v and v[1] == pw else ""
    def llLinksetDataWriteProtected(s, sc, k, v, pw):
        if v == "": return s.llLinksetDataDeleteProtected(sc, k, pw)
        if s.lsd.get(k) == (v, pw): return C["LINKSETDATA_NOUPDATE"]
        s.lsd[k] = (v, pw)
        s._lsd_event(C["LINKSETDATA_UPDATE"], k, v)
        return 0
    def llLinksetDataDeleteProtected(s, sc, k, pw):
        if s.lsd.pop(k, None): s._lsd_event(C["LINKSETDATA_DELETE"], k, "")
        return 0
    def llLinksetDataReset(s, sc):
        s.lsd = {}
        s._lsd_event(C["LINKSETDATA_RESET"], "", "")
    def _lsd_event(s, action, k, v):
        """linkset_data in every script of the object that has it (8.4.2: screen keeps the textures through a reset)"""
        for x in s.live():
            if x.has("linkset_data"): s.event(x, "linkset_data", (action, k, v))
    def llLinksetDataListKeys(s, sc, first, count):
        L = sorted(s.lsd)
        return L[first:] if count < 1 else L[first:first + count]
    def llLinksetDataFindKeys(s, sc, pattern, first, count):
        import re as _re
        L = [k for k in sorted(s.lsd) if _re.search(pattern, k)]
        return L[first:] if count < 1 else L[first:first + count]
    def llLinksetDataAvailable(s, sc): return 131072 - sum(len(k) + len(v[0]) + len(v[1]) + 32 for k, v in s.lsd.items())
    def llLinksetDataCountKeys(s, sc): return len(s.lsd)
    # touches
    def llDetectedKey(s, sc, i): return sc.detected[i]["key"] if i < len(sc.detected) else Key(NULL)
    def llDetectedLinkNumber(s, sc, i): return sc.detected[i]["link"] if i < len(sc.detected) else 0
    def llDetectedPos(s, sc, i): return sc.detected[i].get("pos", ZV) if i < len(sc.detected) else ZV
    def llDetectedName(s, sc, i): return sc.detected[i].get("name", "") if i < len(sc.detected) else ""
    def llDetectedTouchST(s, sc, i): return sc.detected[i]["st"] if i < len(sc.detected) else vec(-1, -1, 0)
    def llDetectedTouchUV(s, sc, i): return sc.detected[i]["uv"] if i < len(sc.detected) else vec(-1, -1, 0)
    def llDetectedTouchFace(s, sc, i): return 4
    # avatars, things and the region
    def _av(s, k): return s.w.avatars.get(k)
    def llGetAgentSize(s, sc, k):
        a = s._av(k)
        return a.size if a and a.in_region and a.region == s.owner.region else ZV
    def llGetAgentInfo(s, sc, k):
        a = s._av(k)
        if not a or not a.in_region: return 0
        f = 0
        if a.sitting: f |= C["AGENT_SITTING"]
        if isinstance(a.seat, Furniture): f |= C["AGENT_ON_OBJECT"]
        if a.flying: f |= C["AGENT_FLYING"]
        if a.typing: f |= C["AGENT_TYPING"]
        if a.away: f |= C["AGENT_AWAY"]
        if a.mouselook: f |= C["AGENT_MOUSELOOK"]
        if a.huds: f |= C["AGENT_ATTACHMENTS"] | C["AGENT_SCRIPTED"]
        return f
    def _here(s, a): return a.in_region and a.region == s.owner.region
    def llGetAgentList(s, sc, scope, opts): return [Key(a.key) for a in s.w.avatars.values() if s._here(a)]
    def llKey2Name(s, sc, k):
        a = s._av(k)
        if a: return a.name + " Resident" if s._here(a) else ""
        o = s.w.objects.get(k) or s.w.things.get(k)
        return o.name if o else ""
    def llGetUsername(s, sc, k):
        a = s._av(k)
        return a.name.lower() if a and s._here(a) else ""
    def llGetOwnerKey(s, sc, k):
        o = s.w.objects.get(k)
        return Key(o.owner.key) if o else Key(k)
    def llGetObjectDetails(s, sc, k, params):
        a = s._av(k)
        o = s.w.objects.get(k)
        f = s.w.things.get(k)
        if a and not s._here(a): return []
        if not a and not o and not f: return []
        out = []
        for p in params:
            if p == C["OBJECT_POS"]: out.append(a.pos if a else (f.pos if f else o.owner.pos))
            elif p == C["OBJECT_ROT"]: out.append(a.rot if a else (f.rot if f else ZR))
            elif p == C["OBJECT_VELOCITY"]: out.append(a.vel if a else ZV)
            elif p == C["OBJECT_ROOT"]:
                out.append(Key(a.seat.key) if a and isinstance(a.seat, Furniture) else Key(k))
            elif p == C["OBJECT_NAME"]: out.append(a.name if a else (f.name if f else o.name))
            elif p == C["OBJECT_CREATOR"]: out.append(Key(f.creator) if f else Key(NULL))
            elif p == C["OBJECT_OWNER"]: out.append(Key(a.key if a else (o.owner.key if o else NULL)))
            else: out.append(0)
        return out
    def llCastRay(s, sc, a, b, opts):
        hits, agents = 1, True
        for i in range(0, len(opts) - 1, 2):
            if opts[i] == C["RC_MAX_HITS"]: hits = opts[i + 1]
            if opts[i] == C["RC_REJECT_TYPES"] and opts[i + 1] & C["RC_REJECT_AGENTS"]: agents = False
        return s.w.cast(a, b, hits, agents)
    def llGetRegionName(s, sc): return s.owner.region
    def llWater(s, sc, off): return B.F32(s.w.water)
    def llGround(s, sc, off): return B.F32(s.w.ground)
    def llGetParcelDetails(s, sc, pos, params):
        return [Key(s.w.parcel(pos)) if p == C["PARCEL_DETAILS_ID"] else "" for p in params]


class _Reset(Exception): pass


from lslmem import static_used, LIMIT                 # tools/lslmem.py (8.0.1)
_STATIC = {}
def static(path):
    if path not in _STATIC: _STATIC[path] = static_used(path)[0]
    return _STATIC[path]

# how many values each PRIM_* rule takes (enough to walk the lists the scripts build)
_NARGS = {C["PRIM_POS_LOCAL"]: 1, C["PRIM_POSITION"]: 1, C["PRIM_ROT_LOCAL"]: 1, C["PRIM_ROTATION"]: 1, C["PRIM_SIZE"]: 1,
          C["PRIM_COLOR"]: 3, C["PRIM_TEXTURE"]: 5, C["PRIM_FULLBRIGHT"]: 2, C["PRIM_GLOW"]: 2, C["PRIM_NAME"]: 1,
          C["PRIM_DESC"]: 1, C["PRIM_TEXT"]: 3, C["PRIM_SLICE"]: 1}

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
NAMES = ("core", "ui", "text", "screen", "strip", "bars", "tracking", "portrait", "fixed", "scenic", "sync", "carry")
HUD_SCRIPTS = [os.path.join(ROOT, "hud", "src", n + ".lsl") for n in NAMES]
FREE_SCRIPTS = [os.path.join(ROOT, "scenery", "src", n + ".lsl") for n in ("core", "ui", "text", "screen", "strip", "bars", "scenic", "sync", "carry")]
BUILDER = os.path.join(ROOT, "hud", "build", "builder.lsl")
PASS = "cinema-1.0-build1"


def lsd(o, k):
    """a protected Linkset Data value of a HUD ("" if none)"""
    v = o.lsd.get("cin." + k)
    return v[0] if v else ""


def ready(av, first_run_done=True):
    """settings as after the first run (lens, eye line, size): the shots run without the setup"""
    d = {"cin.owner": (str(av.key), PASS), "cin.ver": ("8.0.1", PASS)}
    if first_run_done: d["cin.firstrun"] = ("done", PASS)
    d["cin.open"] = ("0", PASS)          # the strip as left closed: the tests open it themselves (8.0.5 restores it on wear)
    return d
