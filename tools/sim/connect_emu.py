# Connect on the REAL scripts (7.1.3): two and three avatars wear the full Take 12 HUD (all fifteen hud/src scripts, run by
# tools/emu), or the Watch, in one region. First fixed scenarios, then a fuzzer: random taps, double-taps, holds, menu
# and panel choices, movement keys, Alt-orbits, Esc, waits, taking the HUD off, a lost chat message, a fresh reset.
# After every settled step it checks what both sides believe:
#   - nobody holds a connection and follows someone at the same time
#   - whoever is in your list follows you; whoever follows you is in your list
#   - a viewer whose director films sees that camera (not their own), unless it is their own moment, they look around
#     or they are taking the camera
#   - no script error, no state left past its time-out
# A failure prints the seed and the steps that led to it.   python3 tools/sim/connect_emu.py [runs] [seed]
import os, sys, random, traceback
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "emu"))
from world import World, HUD_SCRIPTS, WATCH_SCRIPTS, Key

NK = "00000000-0000-0000-0000-000000000000"
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

def g(a, name="sync"):
    return next(s for s in a.hud.scripts if s.name == name).g
def key_ok(k): return bool(k) and k != NK
def T(a): return a.kind == "T"

def host(a):
    k = g(a, "sync" if T(a) else "take12_watch")["gHost"]
    return a.w.avatars.get(k) if key_ok(k) else None

def describe(w, a):
    if not a.hud or not a.hud.worn: return "%s: (HUD off)" % a.name
    p, f, scr = a.camera()
    if not T(a):
        h = host(a)
        return "%s [Watch]: host=%s cam=%s" % (a.name, h.name if h else "-", "script" if scr else "own")
    s, c = g(a), g(a, "core")
    nm = lambda k: w.avatars[k].name if k in w.avatars else "?"
    h = host(a)
    return ("%s: hub=%d host=%s list=%s away=%s camOn=%d ask=%d held=%d own=%d lookaround=%d core=%d/%s cam=%s text=%r"
            % (a.name, s["gSharing"], h.name if h else "-", [nm(k) for k in s["gWatchers"]], [nm(k) for k in s["gAway"]],
               s["gCamOn"], s["gAskT"], s["gHeld"], s["gOwnT"] > 0, s["gIsAway"], c["gState"], c["gMode"],
               ("script:" + a.hud.cam.get("by", "?")) if scr else "own", a.hud.prims[0]["text"]))

def setup(kinds=("T", "T"), seed=1):
    w = World(seed=seed)
    names = ["Ana", "Ben", "Cy"]
    avs = []
    for i, k in enumerate(kinds):
        a = w.avatar(names[i], (128 + 2 * i, 128, 22))
        a.kind = k
        a.wear(HUD_SCRIPTS if k == "T" else WATCH_SCRIPTS)
        avs.append(a)
    w.run(5)
    return w, avs

# ---- the invariants -------------------------------------------------------------------------------------------------
def invariants(w, avs, quiet_for):
    """quiet_for: seconds since the last action (some checks need the messages to have arrived)"""
    bad = []
    for e in w.errors: bad.append("script error %s" % (e,))
    on = [a for a in avs if a.hud and a.hud.worn]
    for a in on:
        if not T(a): continue
        s = g(a)
        if s["gSharing"] and host(a): bad.append("%s holds a connection and follows %s at once" % (a.name, host(a).name))
        if quiet_for >= 3:
            for k in s["gWatchers"]:
                b = w.avatars.get(k)
                if b and b.hud and b.hud.worn and host(b) is not a:
                    bad.append("%s lists %s as connected, but %s follows %s" % (a.name, b.name, b.name, host(b).name if host(b) else "nobody"))
        if s["gAskT"] and int(w.base_unix + w.t) - s["gAskT"] > 25: bad.append("%s: the hand-over ask is stuck" % a.name)
    for b in on:
        h = host(b)
        if not h or not h.hud or not h.hud.worn or not T(h): continue
        hs = g(h)
        if quiet_for >= 3 and not hs["gSharing"] and not host(h):
            bad.append("%s follows %s, who holds no connection" % (b.name, h.name))
        if quiet_for >= 3 and hs["gSharing"] and Key(b.key) not in hs["gWatchers"]:
            bad.append("%s follows %s, who does not list them" % (b.name, h.name))
        if T(b):
            s = g(b)
            moment = s["gOwnT"] > 0 or s["gIsAway"] or s["gAskT"] or s["gHeld"] or b.orbit
        else:
            s = g(b, "take12_watch")
            moment = s["gOwnT"] > 0 or s["gIsAway"] or s["gHeld"] or b.orbit
        if quiet_for >= 3 and hs["gSharing"] and hs["gCamOn"] and not moment and h.camera()[2]:
            if not b.camera()[2]: bad.append("%s should see %s's camera, but has their own" % (b.name, h.name))
    return bad

# ---- the actions ----------------------------------------------------------------------------------------------------
def act(w, a, rng, avs):
    """one random thing a person does; returns its description"""
    if not a.hud or not a.hud.worn:
        if rng.random() < 0.3:
            a.wear(HUD_SCRIPTS if a.kind == "T" else WATCH_SCRIPTS); return "wears the HUD again"
        return "waits (HUD off)"
    r = rng.random()
    if not T(a):
        if r < 0.3: a.keys(1, hold=rng.choice([0.2, 1.0])); return "walks"
        if r < 0.4: a.alt_orbit(); return "Alt-orbits"
        if r < 0.5: a.esc(); return "Esc"
        if r < 0.55: a.take_off(); return "takes the Watch off"
        return "waits"
    if a.dialog and r < 0.55:
        b = rng.choice(a.labels()); a.click(b); return "clicks %r" % b
    if r < 0.2: a.tap(); return "taps"
    if r < 0.3: a.double_tap(); return "double-taps"
    if r < 0.42: a.long_press(); return "holds the button (Connect)"
    if r < 0.55: bits = rng.choice([1, 2, 256, 16]); a.keys(bits, hold=rng.choice([0.2, 1.5])); return "presses keys %d" % bits
    if r < 0.6: a.alt_orbit(); return "Alt-orbits"
    if r < 0.66: a.esc(); return "Esc"
    if r < 0.68: a.take_off(); return "takes the HUD off"
    if r < 0.69: a.hud.attach(); return "resets the HUD (re-wears it)"
    return "waits"

def fuzz(runs, seed0, kinds=("T", "T"), steps=30, drop=0.0, verbose=False):
    found = 0
    for r in range(runs):
        seed = seed0 + r
        rng = random.Random(seed)
        w, avs = setup(kinds, seed)
        w.drop = drop
        trace = []
        for i in range(steps):
            a = rng.choice(avs)
            try:
                what = act(w, a, rng, avs)
            except AssertionError as e:
                what = "(%s)" % e
            trace.append("%6.1f %s %s" % (w.t, a.name, what))
            wait = rng.choice([0.3, 1, 2, 4, 8, 15])
            w.run(wait)
            bad = invariants(w, avs, wait)
            if bad:
                found += 1
                print("---- seed %d (%s, drop %.2f): after step %d" % (seed, "+".join(kinds), drop, i + 1))
                for b in bad: print("  !", b)
                for t in trace[-12:]: print("    ", t)
                for a2 in avs: print("    =", describe(w, a2))
                break
    return found

# ---- fixed scenarios -------------------------------------------------------------------------------------------------
def connect(w, ana, ben):
    ana.long_press(); w.run(3); ana.click("+ " + ben.name); w.run(2)
    if T(ben): ben.double_tap(); w.run(2)

def film(w, a, item="○ Framing"):
    a.tap(); w.run(1)
    if item in a.labels(): a.click(item)
    else: a.click("× Close")                                            # a camera runs already
    w.run(3)

def scenarios():
    w, (ana, ben) = setup()
    connect(w, ana, ben)
    check(g(ana)["gSharing"] and host(ben) is ana, "connect: Ben follows Ana: " + describe(w, ben))
    check(not ben.camera()[2] and g(ben)["gHeld"], "connected, nobody films: Ben has his own camera")
    film(w, ana)
    check(ben.camera()[2] and ben.hud.cam.get("by") == "sync", "Ana films: Ben sees it: " + describe(w, ben))
    ben.keys(1, hold=1.0); w.run(1.5)
    check(not ben.camera()[2] and g(ana)["gAway"], "a key while watching: Ben's own camera for a moment, Ana sees it")
    w.run(6)
    check(ben.camera()[2] and not g(ana)["gAway"], "still for 4 s: Ben is back on Ana's camera")
    film(w, ben)
    check(host(ana) is ben and g(ben)["gSharing"] and ana.camera()[2], "Ben films: the lead passes, Ana sees Ben's camera: " + describe(w, ana))
    w.run(40)
    check(host(ana) is ben and Key(ana.key) in g(ben)["gWatchers"], "40 s later both still agree: " + describe(w, ana) + " / " + describe(w, ben))
    ben.tap(); w.run(1)
    check("■ Stop" in ben.labels(), "Ben's live menu has Stop: %s" % ben.labels())
    ben.click("■ Stop"); w.run(2)
    check(not ana.camera()[2] and g(ana)["gHeld"] and host(ana) is ben, "Ben stops: nobody films, Ana has her own camera, still connected")
    ana.double_tap(); w.run(4)
    check(host(ben) is ana and ben.camera()[2], "Ana double-taps: she films, Ben follows: " + describe(w, ben))
    # Disconnect from the viewer's side
    ben.long_press(); w.run(1)
    check("Disconnect" in ben.labels(), "Ben's panel has Disconnect: %s" % ben.labels())
    ben.click("Disconnect"); w.run(2)
    check(not host(ben) and Key(ben.key) not in g(ana)["gWatchers"] and not ben.camera()[2], "Ben disconnects: both know, Ben's own camera")
    check(not w.errors, "no script errors: %s" % w.errors)
    # 7.1.3: one role at a time; a restarted HUD lets its people go at once; /77 debug
    w4, (a4, b4, c4) = setup(("T", "T", "T"))
    b4.long_press(); w4.run(3)                                          # Ben's panel is open ...
    a4.long_press(); w4.run(3); a4.click("+ Ben"); w4.run(2)            # ... Ana asks Ben ...
    b4.click("+ Cy"); w4.run(2)                                         # ... Ben connects Cy from the panel still open ...
    b4.double_tap(); w4.run(3)                                          # ... then says yes to Ana
    check(not (g(b4)["gSharing"] and host(b4)), "never a hub and a viewer at once: " + describe(w4, b4))
    ana.long_press(); w.run(1); ana.click("Disconnect"); w.run(3)       # Ana still held it (alone): she ends it
    check(not g(ana)["gSharing"], "Ana disconnects, alone: " + describe(w, ana))
    connect(w, ana, ben); film(w, ana)
    check(host(ben) is ana, "connected again: " + describe(w, ben))
    ana.hud.attach(); w.run(1)                                          # Ana's scripts restart (Reset Scripts, a re-wear)
    check(not host(ben) and not ben.camera()[2], "Ana's HUD restarted: Ben lets go at once, his own camera: " + describe(w, ben))
    ben.say(77, "debug on"); w.run(1)
    connect(w, ana, ben)
    log = " ".join(x[2] for x in ben.chat)
    check("Connect debug on" in log and "[T12 sync" in log and "← Ana: invite" in log and "→ Ana: join" in log, "/77 debug shows the messages: " + log[-300:])
    # a fresh HUD says nothing about a disconnect (7.1.2)
    w2, (c,) = setup(("T",))
    film(w2, c); w2.run(30)
    check("disconnected" not in " ".join(x[2] for x in c.chat) and "disconnected" not in c.hud.prims[0]["text"], "a fresh HUD: no disconnect notice")
    # the Watch
    w3, (ana3, ben3) = setup(("T", "W"))
    connect(w3, ana3, ben3); film(w3, ana3)
    check(host(ben3) is ana3 and ben3.camera()[2], "a Watch follows Ana's camera: " + describe(w3, ben3))

if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    scenarios()
    n = 0
    n += fuzz(runs, seed, ("T", "T"))
    n += fuzz(runs // 2, seed + 5000, ("T", "T", "T"))
    n += fuzz(runs // 2, seed + 9000, ("T", "T", "W"))
    n += fuzz(runs // 2, seed + 13000, ("T", "T"), drop=0.05)
    check(n == 0, "%d fuzz runs broke an invariant" % n)
    print("connect (real scripts): scenarios, then %d fuzz runs on 2 and 3 HUDs (and a Watch, and lost messages)" % (runs * 5 // 2))
    print("connect_emu checks:", "ALL PASS" if ok else "FAILURES")
    raise SystemExit(0 if ok else 1)
