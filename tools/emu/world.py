"""The world the Take 12 scripts run in (7.1.3): a region, avatars, worn HUDs, virtual time (tools/emu/lsl_emu.py runs
the scripts). What it models, and how:
  - events: one queue in time order; each script runs one event at a time to its end, as in Second Life
  - link messages go to every script of the object (the sender too); region chat reaches every listening object
    but the speaker's own (llRegionSay / llRegionSayTo, 0.05 s later; a message can be dropped on purpose)
  - controls: one request per script (a second llTakeControls replaces that script's first); a key reaches every
    script that accepts it, and moves the avatar unless some script holds it without passing it on
  - the camera: per avatar, the worn object's scripted camera (any of its scripts) or the avatar's own
  - permissions: an attachment's requests to its owner are granted at once (run_time_permissions)
  - protected Linkset Data per object (llLinksetDataReset when the owner changes), prim names and descriptions,
    the text above the HUD, llDialog (kept for the test to click), llOwnerSay (kept as the avatar's chat log)

    w = World(); ana = w.avatar("Ana", (128, 128, 22)); ana.wear(HUD_SCRIPTS); w.run(5)
"""
import heapq, itertools, math, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lsl_emu import compile_file, Script, Key, Vector, Quaternion, CONST, B, LSLError

C = CONST
ZV = Vector((0.0, 0.0, 0.0))
ZR = Quaternion((0.0, 0.0, 0.0, 1.0))
CTL_MOVE = C["CONTROL_FWD"] | C["CONTROL_BACK"] | C["CONTROL_LEFT"] | C["CONTROL_RIGHT"]
_keys = itertools.count(1)
_gens = itertools.count(1)
def new_key(): return Key("%08x-0000-4000-8000-%012x" % (0x7ac0012, next(_keys)))
def vec(*a): return Vector(tuple(float(x) for x in a))


class World:
    def __init__(s, seed=1, region="Take 12 Lab"):
        s.t = 0.0
        s.q = []
        s.seq = itertools.count()
        s.avatars = {}                                 # key -> Avatar
        s.objects = {}                                 # key -> Obj
        s.region = region
        s.rng = random.Random(seed)
        s.drop = 0.0                                   # chance that a region chat message is lost
        s.errors = []                                  # script errors (Math Error, a bad cast, a missing stub)
        s.chatlog = []                                 # (t, from, to, channel, message) on the Connect channel
        s.base_unix = 1_800_000_000

    def avatar(s, name, pos, **kw):
        a = Avatar(s, name, pos, **kw)
        s.avatars[a.key] = a
        return a

    def post(s, dt, fn, *args):
        heapq.heappush(s.q, (s.t + dt, next(s.seq), fn, args))

    def run(s, seconds):
        end = s.t + seconds
        while s.q and s.q[0][0] <= end:
            t, _, fn, args = heapq.heappop(s.q)
            s.t = max(s.t, t)
            fn(*args)
        s.t = end

    # ---- chat ---------------------------------------------------------------------------------------------------------
    def chat(s, speaker, channel, msg, to=None, name=""):
        """speaker: an Obj or an Avatar; to: an avatar or object key (llRegionSayTo), None = the whole region"""
        if channel == -7712120: s.chatlog.append((round(s.t, 2), getattr(speaker, "owner_name", name), to, msg))
        if s.drop and channel != 0 and s.rng.random() < s.drop: return
        for o in list(s.objects.values()):
            if o is speaker or not o.worn: continue
            if to is not None and to != o.key and to != o.owner.key: continue
            for sc in o.scripts:
                for h, (ch, nm, idk, m) in list(sc.listens.items()):
                    if ch != channel: continue
                    if nm and nm != name: continue
                    if idk and idk != getattr(speaker, "key", None): continue
                    if m and m != msg: continue
                    s.post(0.05, o.event, sc, "listen", (channel, name, Key(speaker.key), msg))


class Avatar:
    def __init__(s, w, name, pos, sitting=False, flying=False):
        s.w, s.name, s.key = w, name, new_key()
        s.pos, s.rot, s.vel = vec(*pos), ZR, ZV
        s.sitting, s.flying, s.typing, s.away, s.in_region = sitting, flying, False, False, True
        s.size = vec(0.45, 0.6, 1.8)
        s.fov, s.aspect = 1.047198, 1.778
        s.held = 0                                     # control bits held now
        s.own_cam = None                               # Alt-orbit: where you put your own camera (None: behind you)
        s.orbit = False                                # Alt-orbiting: the viewer shows your own camera over any script's
        s.hud = None
        s.chat = []                                    # what the scripts said to this avatar (llOwnerSay), with time
        s.texts = []                                   # every text put above the HUD, with time and script
        s.dialog = None                                # the last llDialog: (object, text, buttons, channel)

    def __repr__(s): return "<%s>" % s.name

    def wear(s, paths, **kw):
        s.hud = Obj(s.w, s, paths, **kw)
        s.w.objects[s.hud.key] = s.hud
        s.hud.attach()
        return s.hud

    def take_off(s):
        if s.hud: s.hud.detach()

    # ---- the camera this avatar sees -------------------------------------------------------------------------------
    def camera(s):
        """(pos, focus, scripted?) of what the viewer shows"""
        c = s.hud.cam if s.hud and s.hud.worn else None
        if s.orbit and s.own_cam: return s.own_cam[0], s.own_cam[1], False
        if c and c.get("active"):
            return c.get("pos", s.pos), c.get("focus", s.pos), True
        if s.own_cam: return s.own_cam[0], s.own_cam[1], False
        return B.sub(s.pos, vec(3, 0, -1)), s.pos, False

    # ---- input ---------------------------------------------------------------------------------------------------------
    def keys(s, bits, hold=0.3):
        """press and hold movement keys for a while, then let go"""
        s._keys(bits)
        s.w.post(hold, s._keys, 0)

    def _keys(s, held):
        old, s.held = s.held, held
        edge = old ^ held
        if not s.hud or not s.hud.worn: return
        blocked = 0
        for sc in s.hud.scripts:
            mask, accept, passon = sc.ctl
            if accept and (mask & (held | edge)) and sc.has("control"):
                s.hud.event(sc, "control", (Key(s.key), held & mask, edge & mask))
            if not passon: blocked |= mask
        moving = held & CTL_MOVE & ~blocked
        if moving and not s.sitting:
            s.pos = B.add(s.pos, vec(0.8 if moving & 1 else (-0.8 if moving & 2 else 0), 0.0, 0.0))
        if held: s.w.post(0.2, s._repeat, held)

    def _repeat(s, held):
        if s.held == held and held: s._keys(held)      # held keys keep sending control events

    def touch(s, link=1, st=(0.5, 0.5, 0.0), hold=0.1):
        o = s.hud
        det = [{"key": Key(s.key), "link": link, "st": vec(*st)}]
        for sc in o.scripts:
            if sc.has("touch_start"): o.event(sc, "touch_start", (1,), det)
        def end():
            for sc in o.scripts:
                if sc.has("touch_end"): o.event(sc, "touch_end", (1,), det)
        s.w.post(hold, end)

    def alt_orbit(s):
        p = s.camera()[0]
        s.own_cam = (B.add(p, vec(0.0, 2.5, 1.0)), s.pos)
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

    def labels(s): return [b for b in (s.dialog[2] if s.dialog else []) if b.strip()]


class Obj:
    """a worn HUD: the root prim (all scripts) and its children (four Format bars, the keys strip)"""
    def __init__(s, w, owner, paths, children=("Object",) * 5, textures=("take12_keys",), notecards=("Take 12 - Read Me",)):
        s.w, s.owner, s.key = w, owner, new_key()
        s.owner_name = owner.name
        s.name = "Take 12"
        s.prims = [{"name": "Take 12", "desc": "", "text": ""}] + [{"name": n, "desc": "", "text": ""} for n in children]
        s.inventory = {t: ("texture", new_key(), True) for t in textures}
        s.inventory.update({n: ("notecard", new_key(), True) for n in notecards})
        s.lsd = {}
        s.cam = {}
        s.worn = False
        s.scripts = [Script(compile_file(p), s) for p in paths]
        for sc in s.scripts: s._init(sc)

    def _init(s, sc):
        sc.listens, sc.nl = {}, 1
        sc.timer, sc.timer_gen = 0.0, next(_gens)
        sc.perms, sc.perm_key = 0, Key("")
        sc.ctl = (0, False, True)
        sc.t0 = s.w.t

    def attach(s):
        s.worn = True
        for sc in s.scripts: s.reset(sc)
        for sc in s.scripts:
            if sc.has("attach"): s.event(sc, "attach", (Key(s.owner.key),))

    def detach(s):
        for sc in s.scripts:
            if sc.has("attach"): s._run(sc, "attach", (Key(C["NULL_KEY"]),), None, sc.timer_gen)
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
        if gen != sc.timer_gen or (not s.worn and name != "attach"): return   # reset since, or taken off
        try:
            st = sc.run(name, args, detected)
        except _Reset:
            s.reset(sc)
        except LSLError as e:
            s.w.errors.append((round(s.w.t, 2), s.owner.name, sc.name, name, str(e)))
        except NotImplementedError as e:
            s.w.errors.append((round(s.w.t, 2), s.owner.name, sc.name, name, "not emulated: " + str(e)))

    # ---- the built-ins that touch the world (called as world.llName(script, *args)) ----------------------------------
    # time
    def llGetUnixTime(s, sc): return int(s.w.base_unix + s.w.t)
    def llGetTime(s, sc): return B.F32(s.w.t - sc.t0)
    def llSetTimerEvent(s, sc, t):
        sc.timer_gen += 0                              # (kept: resets bump the generation, timers have their own)
        sc.timer = t
        sc.tgen = getattr(sc, "tgen", 0) + 1
        if t > 0: s.w.post(t, s._timer, sc, sc.tgen, sc.timer_gen)
    def _timer(s, sc, tg, gen):
        if tg != sc.tgen or gen != sc.timer_gen or sc.timer <= 0 or not s.worn: return
        s._run(sc, "timer", (), None, gen)
        if tg == sc.tgen and sc.timer > 0: s.w.post(sc.timer, s._timer, sc, tg, gen)
    def llResetScript(s, sc): raise _Reset()
    def llFrand(s, sc, m): return B.F32(s.w.rng.random() * m)
    def llGetFreeMemory(s, sc): return 30000
    # messages
    def llMessageLinked(s, sc, link, num, msg, k):
        for o in s.scripts:
            if o.has("link_message"): s.event(o, "link_message", (1, num, msg, Key(k)))
    def llListen(s, sc, ch, name, k, msg):
        h = sc.nl; sc.nl += 1
        sc.listens[h] = (ch, name, k if k and k != C["NULL_KEY"] else "", msg)
        return h
    def llListenRemove(s, sc, h): sc.listens.pop(h, None)
    def llRegionSay(s, sc, ch, msg): s.w.chat(s, ch, msg, name=s.name)
    def llRegionSayTo(s, sc, to, ch, msg): s.w.chat(s, ch, msg, to=to, name=s.name)
    def llOwnerSay(s, sc, msg): s.owner.chat.append((round(s.w.t, 2), sc.name, msg))
    def llDialog(s, sc, av, text, buttons, ch):
        if av == s.owner.key: s.owner.dialog = (s, text, list(buttons), ch)
    def llLoadURL(s, sc, av, msg, url): s.owner.chat.append((round(s.w.t, 2), sc.name, "[url] " + url))
    def llGiveInventory(s, sc, k, name): pass
    # permissions, controls, the camera
    def llRequestPermissions(s, sc, k, perms):
        if k == s.owner.key and s.worn:
            sc.perms, sc.perm_key = perms, Key(k)
            if sc.has("run_time_permissions"): s.event(sc, "run_time_permissions", (perms,))
    def llGetPermissions(s, sc): return sc.perms
    def llGetPermissionsKey(s, sc): return sc.perm_key
    def llTakeControls(s, sc, mask, accept, passon):
        if not sc.perms & C["PERMISSION_TAKE_CONTROLS"]: return
        sc.ctl = (mask, bool(accept), bool(passon))      # one set per script: this replaces the last
    def llReleaseControls(s, sc):
        sc.ctl = (0, False, True)
        sc.perms &= ~C["PERMISSION_TAKE_CONTROLS"]
    def llSetCameraParams(s, sc, rules):
        if not sc.perms & C["PERMISSION_CONTROL_CAMERA"]: return
        names = {C["CAMERA_ACTIVE"]: "active", C["CAMERA_POSITION"]: "pos", C["CAMERA_FOCUS"]: "focus"}
        for i in range(0, len(rules) - 1, 2):
            if rules[i] in names: s.cam[names[rules[i]]] = rules[i + 1]
        s.cam["by"] = sc.name
        s.cam["t"] = s.w.t
    def llClearCameraParams(s, sc):
        if sc.perms & C["PERMISSION_CONTROL_CAMERA"]: s.cam = {"cleared_by": sc.name, "t": s.w.t}
    def llGetCameraPos(s, sc): return s.owner.camera()[0] if sc.perms & C["PERMISSION_TRACK_CAMERA"] else ZV
    def llGetCameraRot(s, sc):
        if not sc.perms & C["PERMISSION_TRACK_CAMERA"]: return ZR
        p, f, _ = s.owner.camera()
        d = B.sub(f, p)
        return B.llRotBetween(vec(1, 0, 0), d) if B.llVecMag(d) > 0.001 else ZR
    def llGetCameraFOV(s, sc): return B.F32(s.owner.fov)
    def llGetCameraAspect(s, sc): return B.F32(s.owner.aspect)
    # the object
    def llGetOwner(s, sc): return Key(s.owner.key)
    def llGetAttached(s, sc): return C["ATTACH_HUD_TOP_RIGHT"] if s.worn else 0
    def llGetNumberOfPrims(s, sc): return len(s.prims)
    def llGetLinkName(s, sc, link): return s.prims[link - 1]["name"] if 1 <= link <= len(s.prims) else ""
    def llGetNumberOfSides(s, sc): return 6
    def llGetPos(s, sc): return s.owner.pos
    def llGetLocalPos(s, sc): return ZV
    def llGetLocalRot(s, sc): return ZR
    def llGetScale(s, sc): return vec(0.01, 0.06, 0.06)
    def llSetScale(s, sc, v): pass
    def llScaleTexture(s, sc, u, v, face): pass
    def llOffsetTexture(s, sc, u, v, face): pass
    def llSetText(s, sc, text, color, alpha):
        s.prims[0]["text"] = text[:254]
        s.owner.texts.append((round(s.w.t, 2), sc.name, text[:254]))
    def llGetPrimitiveParams(s, sc, rules): return s._params(1, rules)
    def llGetLinkPrimitiveParams(s, sc, link, rules): return s._params(link, rules)
    def _params(s, link, rules):
        p = s.prims[link - 1] if 1 <= link <= len(s.prims) else {"name": "", "desc": "", "text": ""}
        out = []
        for r in rules:
            if r == C["PRIM_TEXT"]: out += [p["text"], vec(1, 1, 1), 1.0]
            elif r == C["PRIM_NAME"]: out += [p["name"]]
            elif r == C["PRIM_DESC"]: out += [p["desc"]]
            elif r == C["PRIM_TEXTURE"]: out += [C["NULL_KEY"], vec(1, 1, 0), ZV, 0.0]
        return out
    def llSetLinkPrimitiveParamsFast(s, sc, link, rules):
        i, cur = 0, link
        while i < len(rules):
            r = rules[i]
            if r == C["PRIM_LINK_TARGET"]: cur = rules[i + 1]; i += 2; continue
            if r in (C["PRIM_NAME"], C["PRIM_DESC"]) and 1 <= cur <= len(s.prims):
                s.prims[cur - 1]["name" if r == C["PRIM_NAME"] else "desc"] = rules[i + 1]
            i += 1 + _NARGS.get(r, 1)
    # inventory and Linkset Data
    def llGetInventoryType(s, sc, name):
        if name in s.inventory: return C["INVENTORY_" + s.inventory[name][0].upper()]
        if any(x.name == name for x in s.scripts): return C["INVENTORY_SCRIPT"]
        return C["INVENTORY_NONE"]
    def llGetInventoryNumber(s, sc, t):
        return len([n for n, v in s.inventory.items() if C["INVENTORY_" + v[0].upper()] == t or t == C["INVENTORY_ALL"]])
    def llGetInventoryName(s, sc, t, i):
        L = sorted(n for n, v in s.inventory.items() if C["INVENTORY_" + v[0].upper()] == t or t == C["INVENTORY_ALL"])
        return L[i] if 0 <= i < len(L) else ""
    def llGetInventoryKey(s, sc, name):
        v = s.inventory.get(name)
        return v[1] if v and v[2] else Key(C["NULL_KEY"])
    def llLinksetDataReadProtected(s, sc, k, pw):
        v = s.lsd.get(k)
        return v[0] if v and v[1] == pw else ""
    def llLinksetDataWriteProtected(s, sc, k, v, pw):
        if v == "": s.lsd.pop(k, None)
        else: s.lsd[k] = (v, pw)
        return 0
    def llLinksetDataDeleteProtected(s, sc, k, pw): s.lsd.pop(k, None); return 0
    def llLinksetDataReset(s, sc): s.lsd = {}
    # touches
    def llDetectedKey(s, sc, i): return sc.detected[i]["key"] if i < len(sc.detected) else Key(C["NULL_KEY"])
    def llDetectedLinkNumber(s, sc, i): return sc.detected[i]["link"] if i < len(sc.detected) else 0
    def llDetectedTouchST(s, sc, i): return sc.detected[i]["st"] if i < len(sc.detected) else vec(-1, -1, 0)
    # avatars and the region
    def _av(s, k): return s.w.avatars.get(k)
    def llGetAgentSize(s, sc, k):
        a = s._av(k)
        return a.size if a and a.in_region else ZV
    def llGetAgentInfo(s, sc, k):
        a = s._av(k)
        if not a or not a.in_region: return 0
        f = 0
        if a.sitting: f |= C["AGENT_SITTING"] | C["AGENT_ON_OBJECT"]
        if a.flying: f |= C["AGENT_FLYING"]
        if a.typing: f |= C["AGENT_TYPING"]
        if a.away: f |= C["AGENT_AWAY"]
        if a.hud and a.hud.worn: f |= C["AGENT_ATTACHMENTS"] | C["AGENT_SCRIPTED"]
        return f
    def llGetAgentList(s, sc, scope, opts): return [Key(a.key) for a in s.w.avatars.values() if a.in_region]
    def llKey2Name(s, sc, k):
        a = s._av(k)
        return a.name + " Resident" if a and a.in_region else ""
    def llGetUsername(s, sc, k):
        a = s._av(k)
        return a.name.lower() if a and a.in_region else ""
    def llGetOwnerKey(s, sc, k):
        o = s.w.objects.get(k)
        return Key(o.owner.key) if o else Key(k)
    def llGetObjectDetails(s, sc, k, params):
        a = s._av(k)
        o = s.w.objects.get(k)
        if a and not a.in_region: return []
        if not a and not o: return []
        out = []
        for p in params:
            if p == C["OBJECT_POS"]: out.append(a.pos if a else o.owner.pos)
            elif p == C["OBJECT_ROT"]: out.append(a.rot if a else ZR)
            elif p == C["OBJECT_VELOCITY"]: out.append(a.vel if a else ZV)
            elif p == C["OBJECT_ROOT"]: out.append(Key(k))
            elif p == C["OBJECT_NAME"]: out.append(a.name if a else o.name)
            elif p == C["OBJECT_OWNER"]: out.append(Key(a.key if a else o.owner.key))
            else: out.append(0)
        return out
    def llCastRay(s, sc, a, b, opts): return [0]
    def llGetRegionName(s, sc): return s.w.region
    def llWater(s, sc, off): return 20.0


class _Reset(Exception): pass

# how many values each PRIM_* rule takes in llSetLinkPrimitiveParamsFast (enough to walk the lists the scripts build)
_NARGS = {C["PRIM_POS_LOCAL"]: 1, C["PRIM_ROT_LOCAL"]: 1, C["PRIM_SIZE"]: 1, C["PRIM_COLOR"]: 3, C["PRIM_TEXTURE"]: 5,
          C["PRIM_FULLBRIGHT"]: 2, C["PRIM_GLOW"]: 2, C["PRIM_NAME"]: 1, C["PRIM_DESC"]: 1, C["PRIM_TEXT"]: 3}

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
HUD_SCRIPTS = [os.path.join(ROOT, "hud", "src", n + ".lsl") for n in
               ("core", "ui", "scenery", "people", "friends", "picker", "frame", "free", "lens", "sync", "connect",
                "tips", "crop", "keys", "fit")]
WATCH_SCRIPTS = [os.path.join(ROOT, "watch", "take12_watch.lsl")]
