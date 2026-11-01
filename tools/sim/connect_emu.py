"""Connect on the REAL scripts (8.0): two equal cameras. Two and three avatars wear the full Take 12 (the twelve
hud/src scripts, run by tools/emu), or the free Take 12 Scenery. Scenarios, then a fuzzer: random Connect taps, shots,
Alt-clicks, walking away and back, taking the HUD off and on, holds, Leave, lost chat messages. After every settled step
it checks what everyone believes:
  - whoever you watch is connected with you, films, and knows you watch
  - nobody watches someone who watches them (one director per pair)
  - connections are mutual (once the messages have arrived)
  - nothing goes out while you are not filming (your own camera, Alt-click, off)
  - no script error
A failure prints the seed and the steps.     python3 tools/sim/connect_emu.py [runs] [seed]"""
import os, sys, random
from emu_util import *

CH = -7712120
NK = C["NULL_KEY"]
HUD = HUD_SCRIPTS                               # the Take 12 the tests wear (review(): the lab's too)
HP = PARTS

def S(a, n="sync"): return var(a.hud, n, "__all__") if False else next(s for s in a.hud.scripts if s.name == n).g
def peers(a): return [a.w.avatars[k].name for k in S(a)["gP"] if k in a.w.avatars]
def host(a):
    k = S(a)["gHost"]
    return a.w.avatars.get(k) if k and k != NK else None
def linkst(a): return var(a.hud, "strip", "gLinkSt")
def notes(a, since): return a.notes(since)

def setup(names=("Ana", "Ben"), seed=1, free=()):
    w = World(seed=seed)
    avs = []
    for i, n in enumerate(names):
        av = w.avatar(n, (128 + 2 * i, 128, 21))
        av.fov = 0.6125
        av.wear(FREE_SCRIPTS if n in free else HUD, parts=HP, lsd=ready(av))
        avs.append(av)
    w.run(0.5)
    for av in avs: manual(av.hud)                       # the shots by hand (Auto: auto_emu.py)
    w.run(4.5)
    for av in avs:
        av.double_tap()
    w.run(1)
    return w, avs

def ask(w, a, b, yes=True):
    a.say(12, "connect"); w.run(4)                       # the scan: asked twice, listed after 2.5 s (8.0.6)
    if "Invite" in a.labels():
        a.click("Invite"); w.run(4)
    nm = [x for x in a.labels() if x.lstrip("★ ").startswith(b.name)]
    check(nm, "%s's nearby list has %s: %r" % (a.name, b.name, a.labels()))
    if not nm: return
    a.click(nm[0]); w.run(1)
    if b.dialog and "share films" in b.dialog[1]:
        b.click("Yes" if yes else "No"); w.run(1.5)

def shot(w, a, n):
    g = next(x for x in a.hud.scripts if x.name == "strip").g
    if g.get("gQuiet"): a.touch("t12 fold"); w.run(0.5)              # the new design's Quiet page: Direct first, as you would
    a.touch("t12 s%d" % ["tracking", "portrait", "fixed", "scenic"].index(n)); w.run(3)

def link(w, a):
    a.touch("t12 link"); w.run(2)

# ---- scenarios ------------------------------------------------------------------------------------------------------------
def scenarios():
    w, (ana, ben) = setup()
    ana.hud.drop("chime", kind="sound")
    t = w.t
    ask(w, ana, ben)
    check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "Ana asks, Ben says yes: connected (%r, %r)" % (peers(ana), peers(ben)))
    check("Ben is asked." in notes(ana, t) and any(n.startswith("Ben is with you.") for n in notes(ana, t)) and any(n.startswith("Ana is with you.") for n in notes(ben, t)), "the notes say it (%r / %r)" % (notes(ana, t), notes(ben, t)))
    check(ana.sounds and not ben.sounds, "the chime plays (Ana has a sound in her HUD, Ben has none)")
    check(linkst(ana) == "on" and linkst(ben) == "on", "connected: the key lights, even before a shot (your own camera can be watched too, 8.0.7) (%s %s)" % (linkst(ana), linkst(ben)))
    check(rect(ana.hud, ana, "t12 dot")[4] > 0.5, "the [12]'s dot: white while connected")
    ana.hud.lsd["cin.shape"] = ("1.85", PASS); ana.hud.send(7330, "shape")   # Ana's film frame, not Ben's 2.39
    shot(w, ana, "portrait")
    w.run(2)
    check(linkst(ben) == "on", "Ana films: Ben's key lights (%s)" % linkst(ben))
    t = w.t
    link(w, ben)
    check(host(ben) is ana and var(ben.hud, "core", "gState") == "watch", "Ben taps Connect: he watches Ana's film")
    check(B.llVecDist(ben.camera()[0], ana.camera()[0]) < 0.05 and ben.hud.cam.get("by") == "core", "Ben sees Ana's camera")
    check(linkst(ana) == "shared" and linkst(ben) == "theirs", "SHARING / THEIR FILM (%s, %s)" % (linkst(ana), linkst(ben)))
    check(var(ben.hud, "bars", "gFollow") == "1.85", "Ben's bars show Ana's shape (%r)" % var(ben.hud, "bars", "gFollow"))
    check("You're watching Ana's film." in notes(ben, t) and "Ben is watching your film." in notes(ana, t), "the notes")
    check(ana.hud.part("t12 dot")["glow"] > 0, "Ana's dot glows softly while shared")
    shot(w, ana, "portrait")                                          # her lit tap: the other side
    check(B.llVecDist(ben.camera()[0], ana.camera()[0]) < 0.05, "Ana's new angle reaches Ben")
    # 8.0.6: Ben sees exactly what Ana sees, her own Alt-click framing too (only mouselook is never sent)
    ana.alt_orbit(); w.run(3)
    check(host(ben) is ana and B.llVecDist(ben.camera()[0], ana.camera()[0]) < 0.3, "Ana frames with Alt-click: Ben sees her framing")
    ana.esc(); shot(w, ana, "portrait"); w.run(2)
    check(host(ben) is ana and B.llVecDist(ben.camera()[0], ana.camera()[0]) < 0.05, "her shot again: Ben still with her")
    # one director per pair: Ana can't watch Ben while he watches her
    t = w.t
    link(w, ana)
    check(host(ana) is None and "Ben is watching your film." in notes(ana, t), "Ana taps Connect while Ben watches her: Ben is watching your film (8.9.0: it said he wasn't filming)")
    shot(w, ben, "tracking")                                          # Ben picks a shot: his own film again
    check(host(ben) is None and var(ben.hud, "bars", "gFollow") == "", "Ben picks Tracking: his own film, his own bars")
    w.run(2)
    link(w, ana)
    check(host(ana) is ben and host(ben) is None, "now Ana watches Ben")
    link(w, ana)
    check(host(ana) is None and var(ana.hud, "core", "gState") == "film", "a second tap: Ana's own film again")
    # rest beyond 20 m, back by itself
    link(w, ben); w.run(1)
    t = w.t
    ben.walk((128, 160, 21), speed=4); w.run(10)
    check(host(ben) is None and "Ana is out of reach." in notes(ben, t) and "Ben is out of reach." in notes(ana, t), "25 m apart: it rests, Ben back to his film")
    check(linkst(ana) == "dim", "resting: Ana's key dims (%s)" % linkst(ana))
    t = w.t
    ben.walk((130, 128, 21), speed=4); w.run(10)
    check("Ana is back." in notes(ben, t) and peers(ben) == ["Ana"] and linkst(ana) in ("on", "dim"), "back near: it rejoins by itself")
    # host gone: 3 s without a word
    link(w, ben)
    check(host(ben) is ana, "Ben watches Ana")
    t = w.t
    kept = dict(ana.hud.lsd)
    ana.take_off(); w.run(8)
    check(host(ben) is None and "Ana left." in notes(ben, t), "Ana's HUD gone: after 6 s Ben's own film, Ana left.")
    ana.wear(HUD, parts=HP, lsd=kept)
    w.run(0.5); manual(ana.hud); w.run(7.5)
    check(peers(ana) == ["Ben"] and "Ana" in peers(ben), "Ana wears it again within 30 min: they rejoin (%r %r)" % (peers(ana), peers(ben)))
    # Leave
    ben.say(12, "connect"); w.run(2)
    check("Leave" in ben.labels(), "Dialog › Connect, connected: names, Invite, Leave (%r)" % ben.labels())
    ben.click("Leave"); w.run(2)
    check(peers(ben) == [] and peers(ana) == [] and linkst(ana) == "alone", "Leave: both alone")
    # a No is quiet; a friend joins without the question
    t = w.t
    ask(w, ana, ben, yes=False)
    check(peers(ana) == [] and "Ben didn't answer." in notes(ana, t), "a No: \"didn't answer\", never a rejection")
    ben.hud.lsd["cin.friends"] = (str(ana.key) + ",Ana Resident", PASS)
    t = w.t
    ana.say(12, "connect"); w.run(0.5); ana.click("Invite"); w.run(4); ana.click("Ben"); w.run(2)   # alone: the Connect page first (8.6.0)
    check(peers(ben) == ["Ana"] and not (ben.dialog and "share films" in ben.dialog[1]), "Ben has Ana in Friends: she joins without the question")
    # hold: everything off leaves too
    ana.long_press(); w.run(2)
    check(peers(ana) == [] and peers(ben) == [], "Ana holds: everything off, the connection ends")
    no_errors(w, "two")

    # ---- three: one group; the Connect key opens the names ----------------------------------------------------------------
    w, (ana, ben, cy) = setup(("Ana", "Ben", "Cy"))
    ask(w, ana, ben); ask(w, ana, cy)
    w.run(2)
    check(sorted(peers(ana)) == ["Ben", "Cy"] and sorted(peers(ben)) == ["Ana", "Cy"] and sorted(peers(cy)) == ["Ana", "Ben"], "three: one group (%r %r %r)" % (peers(ana), peers(ben), peers(cy)))
    shot(w, ben, "portrait"); shot(w, cy, "scenic"); w.run(2)
    link(w, ana)
    check(ana.dialog and set(["Ben", "Cy", "Leave"]) <= set(ana.labels()), "three: the Connect key opens the names (%r)" % ana.labels())
    ana.click("Cy"); w.run(1)
    check(ana.dialog and "Watch" in ana.labels() and "Show my film" in ana.labels(), "a name: Watch, or Show my film (%r)" % ana.labels())
    ana.click("Watch"); w.run(2)
    check(host(ana) is cy, "Ana watches Cy")
    no_errors(w, "three")

    # ---- an older and a newer Take 12 -------------------------------------------------------------------------------------------
    w, (ana,) = setup(("Ana",))
    olga = w.avatar("Olga", (130, 129, 21))
    o = Obj(w, olga, [], children=()); o.worn = True; w.objects[o.key] = o
    ana.say(12, "connect"); w.run(0.2); ana.click("Invite"); w.run(0.1)
    w.chat(o, CH, "T12|here|T|idle|", to=ana.key)
    w.run(4)
    check("Olga (old)" in ana.labels(), "a 7.x Take 12: listed as (old) (%r)" % ana.labels())
    t = w.t
    ana.click("Olga (old)"); w.run(1)
    check("Olga's Take 12 is older. A new copy fixes it." in notes(ana, t), "tapping it explains")
    nina = w.avatar("Nina", (127, 129, 21))
    o2 = Obj(w, nina, [], children=()); o2.worn = True; w.objects[o2.key] = o2
    t = w.t
    w.chat(o2, CH, "T12|8|here|8.99.0|0", to=ana.key); w.run(1)
    w.chat(o2, CH, "T12|8|here|8.99.0|0", to=ana.key); w.run(1)
    nn = [n for n in notes(ana, t) if "newer" in n]
    check(len(nn) == 1, "a newer Take 12 met: told once (%r)" % nn)
    no_errors(w, "versions")

    # ---- the free Take 12 Scenery watches, never films for others ---------------------------------------------------------------
    w, (ana, fay) = setup(("Ana", "Fay"), free=("Fay",))
    ask(w, fay, ana)
    check(peers(fay) == ["Ana"], "the free build connects")
    shot(w, ana, "portrait"); shot(w, fay, "scenic"); w.run(2)
    link(w, fay)
    check(host(fay) is ana and B.llVecDist(fay.camera()[0], ana.camera()[0]) < 0.05, "the free build watches Ana's film")
    link(w, fay)
    t = w.t
    link(w, ana)
    check(host(ana) is None and "Fay isn't filming." in notes(ana, t), "Fay's free build never films for others")
    no_errors(w, "free")

# ---- the fuzzer -------------------------------------------------------------------------------------------------------------------
def invariants(w, avs):
    bad = ["script error %s" % (e,) for e in w.errors]
    on = [a for a in avs if a.hud and a.hud.worn]
    for a in on:
        h = host(a)
        if h is not None:
            if h not in on: bad.append("%s watches %s whose HUD is off" % (a.name, h.name))
            else:
                if a.name not in peers(h): bad.append("%s watches %s, not connected on %s's side" % (a.name, h.name, h.name))
                if host(h) is a: bad.append("%s and %s watch each other" % (a.name, h.name))
                if not S(h)["gFilm"]: bad.append("%s watches %s, who isn't filming" % (a.name, h.name))
                if a.key not in S(h)["gW"]: bad.append("%s watches %s, who doesn't know" % (a.name, h.name))
        for i, p in enumerate(peers(a)):
            b = next(x for x in avs if x.name == p)
            near = S(a)["gPR"][i]                                      # a resting connection may be one-sided
            if near and b in on and a.name not in peers(b): bad.append("%s has %s, not the other way" % (a.name, b.name))
    return bad

def fuzz(runs, seed, names, drop=0.0, mates=False):
    broken = 0
    for r in range(runs):
        rng = random.Random(seed + r)
        w, avs = setup(names, seed=seed + r)
        if mates: friends(*avs)                                        # 8.9.0: everyone each other's friend (they join by themselves)
        steps = []
        if not mates and rng.random() < 0.7:                           # most runs start connected (friends connect themselves)
            for b in avs[1:]: ask(w, avs[0], b)
            FAILS[:] = [f for f in FAILS if "nearby list" not in f]
        w.drop = drop
        for i in range(25):
            a = rng.choice(avs)
            act = rng.choice(["ask"] * 2 + ["link"] * 3 + ["watch"] * 3 + ["shot"] * 3 + ["alt", "esc", "walk", "back", "back", "off", "rewear", "leave", "wait"])
            steps.append("%s %s" % (a.name, act))
            if not (a.hud and a.hud.worn) and act != "rewear": continue
            if act == "ask":
                b = rng.choice([x for x in avs if x is not a])
                a.dialog = None
                a.say(12, "connect"); w.run(2.5)
                if "Invite" in a.labels() and not any(x.lstrip("★ ").startswith(b.name) for x in a.labels()):
                    a.click("Invite"); w.run(2.5)
                nm = [x for x in a.labels() if x.lstrip("★ ").startswith(b.name)]
                if nm:
                    a.click(nm[0]); w.run(1)
                    if b.dialog and "share films" in b.dialog[1]: b.click(rng.choice(["Yes", "Yes", "No"]))
            elif act == "link":
                if not peers(a): continue
                a.dialog = None
                link(w, a)
                if a.dialog and a.labels():
                    a.click(rng.choice(a.labels()))
            elif act == "shot": shot(w, a, rng.choice(["tracking", "portrait", "fixed", "scenic"]))
            elif act == "watch":                                       # someone films, a watches them
                if not peers(a): continue
                pick = rng.choice(peers(a))
                b = next(x for x in avs if x.name == pick)
                if b.hud and b.hud.worn: shot(w, b, rng.choice(["tracking", "portrait", "scenic"]))
                a.dialog = None
                link(w, a)
                if a.dialog and b.name in a.labels():
                    a.click(b.name); w.run(1)                          # 8.2.0: a name, then Watch
                    if a.dialog and "Watch" in a.labels(): a.click("Watch")
            elif act == "alt": a.alt_orbit()
            elif act == "esc": a.esc(); a.keys(C["CONTROL_FWD"], hold=0.2)
            elif act == "walk": a.walk((128 + rng.uniform(-30, 30), 128 + rng.uniform(-30, 30), 21), speed=4)
            elif act == "back": a.walk((128 + rng.uniform(-3, 3), 128 + rng.uniform(-3, 3), 21), speed=4)
            elif act == "off": a.long_press()
            elif act == "rewear":
                if a.hud and a.hud.worn: a.take_off()
                else:
                    a.wear(HUD, parts=HP, lsd=ready(a))
                    if mates: friends(*[x for x in avs if x.hud])
                    w.run(5); a.double_tap()
            elif act == "leave":
                a.dialog = None
                a.say(12, "connect"); w.run(2.5)
                if "Leave" in a.labels(): a.click("Leave")
            w.run(rng.uniform(1, 6))
            w.run(12)                                                  # settle: messages, the 3 s and 10 s clocks
            bad = invariants(w, avs)
            if bad:
                broken += 1
                print("FUZZ seed %d (%s, drop %.2f): %s\n  steps: %s" % (seed + r, ",".join(names), drop, bad[:3], "; ".join(steps[-8:])))
                break
    return broken

# ---- 8.0.7: a just-worn friend can be watched; her moving camera reaches you; a stray update is ignored -----------------
def streaming():
    w, (ana, ben) = setup()
    ask(w, ana, ben); w.run(2)
    link(w, ben)
    check(host(ben) is ana, "a friend who has not picked a shot can be watched (her own camera)")
    check(B.llVecDist(ben.camera()[0], ana.camera()[0]) < 0.3, "... and you see it")
    link(w, ben); w.run(1)                                              # back to his own film
    shot(w, ana, "tracking"); w.run(2)
    link(w, ben); w.run(1)
    ana.walk((140, 128, 21), speed=1.5)
    far = 0.0
    for i in range(16):
        w.run(0.25)
        far = max(far, B.llVecDist(ben.camera()[0], ana.camera()[0]))
    check(far < 1.0, "Ana walks in Tracking: Ben's view keeps up within a step (%.2f m)" % far)
    n = len([1 for c in w.chatlog if c[1] == "Ana" and "|cam|" in c[3] and c[0] > w.t - 4])
    check(20 <= n <= 36, "her camera goes out about 7 times a second (%d in 4 s)" % n)
    link(w, ben); w.run(0.5)
    mine = ben.camera()[0]
    w.chat(ana.hud, CH, "T12|8|cam|<1,1,30>|<2,2,30>|0|1.0|0", to=ben.key); w.run(0.5)
    check(B.llVecDist(ben.camera()[0], mine) < 0.5, "a late update after he stopped watching is ignored")
    no_errors(w, "streaming")

# ---- 8.2.0: who is near is known; friends connect by themselves; show my film; a smooth view ------------------------------
def rework():
    w, (ana, ben) = setup()
    w.run(12)                                                          # their "here" every 10 s
    ana.dialog = None
    ana.say(12, "connect"); w.run(0.2); ana.click("Invite"); w.run(0.4)
    check(any(x.startswith("Ben") for x in ana.labels()), "the nearby list at once, no waiting (%r)" % ana.labels())
    ana.click(next(x for x in ana.labels() if x.startswith("Ben"))); w.run(1)
    ben.click("Yes"); w.run(1.5)
    check(peers(ana) == ["Ben"], "connected")
    t = w.t
    ana.dialog = None
    ana.hud.send(7371, "connect|friends"); w.run(0.5); ana.click("Add"); w.run(0.5)
    check(any(x.startswith("Ben") for x in ana.labels()) and not any("Nobody" in n for n in notes(ana, t)),
          "Connect › Friends › Add lists Ben, connected already (8.1: 'Nobody near you'; 8.6.0: anyone near) (%r)" % ana.labels())
    ana.click(next(x for x in ana.labels() if x.startswith("Ben"))); w.run(0.5)
    shot(w, ana, "tracking"); w.run(2)
    ana.dialog = None
    ana.say(12, "connect"); w.run(0.5)                                  # (with one person the rings flip; the dialog lists names)
    check(ana.dialog and "Ben · " in ana.dialog[1], "the list says where each one is (%r)" % (ana.dialog and ana.dialog[1]))
    if "Ben" in ana.labels(): ana.click("Ben"); w.run(0.5)
    check("Show my film" in ana.labels(), "a name: Show my film (%r)" % ana.labels())
    ana.click("Show my film"); w.run(1)
    check(ben.dialog and "shows you their film" in ben.dialog[1], "Ben (not Ana's friend in his list) is asked (%r)" % (ben.dialog and ben.dialog[1]))
    ben.click("Watch"); w.run(1)
    check(host(ben) is ana, "Ben watches Ana's film")
    # smooth: Ana walks in Tracking, Ben's view eases 20 times a second, never a big step
    ana.walk((150, 128, 21), speed=1.5)
    P = []
    for i in range(80):
        w.run(0.05)
        P.append(ben.camera()[0])
    jump = max(B.llVecDist(P[i], P[i + 1]) for i in range(len(P) - 1))
    moved = B.llVecDist(P[0], P[-1])
    check(moved > 3.0 and jump < 0.2, "Ben's view moves smoothly with Ana (%.1f m in 4 s, biggest step %.2f m)" % (moved, jump))
    no_errors(w, "rework")

    # two friends near each other connect by themselves
    w, (ana, ben) = setup()
    ana.hud.lsd["cin.friends"] = ("%s,Ben Resident" % ben.key, PASS)
    ben.hud.lsd["cin.friends"] = ("%s,Ana Resident" % ana.key, PASS)
    t = w.t
    w.run(25)
    check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "two friends near: connected by themselves (%r %r)" % (peers(ana), peers(ben)))
    check(any("is with you" in n for n in notes(ana, t)), "... and told so")
    # only one of them a friend: nothing happens by itself
    w, (ana, ben) = setup()
    ana.hud.lsd["cin.friends"] = ("%s,Ben Resident" % ben.key, PASS)
    w.run(25)
    check(peers(ana) == [] and peers(ben) == [] and not ben.dialog, "a friend one way only: nothing by itself, no question popping up")
    no_errors(w, "friends near")


# ---- the lens (8.7.0): a watcher whose zoom differs sees you the same size. Their HUD moves along the view round the
# director's aim; for Tracking that aim was a point 3 m ahead of the camera, not you, and the size came out 16-25 % off
def lens_match():
    import math
    for look in (None, "SHOULDER", "CLASSIC"):
        w, (ana, ben) = setup()
        ana.fov = 0.6125; ben.fov = 1.047                                  # Ana zoomed in (38 mm), Ben the viewer's wide view
        ask(w, ana, ben); shot(w, ana, "tracking"); w.run(2)
        if look: ana.touch(opt_part(ana.hud, look)); w.run(2)
        link(w, ben); w.run(3)
        head = B.add(ana.pos, vec(0, 0, 0.6))
        sd, sw = B.llVecDist(head, ana.camera()[0]), B.llVecDist(head, ben.camera()[0])
        want = sd * math.tan(0.6125 / 2) / math.tan(1.047 / 2)
        check(abs(sw - want) / want < 0.06, "%s, another lens: Ben sees Ana the same size (%.2f m, %.2f for the same size)" % (look or "FILM", sw, want))
        no_errors(w, "lens")

# ---- 8.9.0: the Connect review. Each case was found by reading the scripts end to end; each failed on 8.8.2 -------------
def friends(*avs):
    for a in avs:
        a.hud.lsd["cin.friends"] = (";".join("%s,%s Resident" % (b.key, b.name) for b in avs if b is not a), PASS)

def cams_from(w, name, since):
    return len([1 for c in w.chatlog if c[1] == name and "|cam|" in c[3] and c[0] >= since])

def review(scripts=HUD_SCRIPTS, parts=PARTS):
    global HUD, HP
    HUD, HP = scripts, parts
    # 1. Leave sticks between friends (8.8.2: they connected again by themselves within 10 s)
    w, (ana, ben) = setup()
    friends(ana, ben); w.run(25)
    check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "two friends: connected by themselves")
    ana.dialog = None; ana.say(12, "connect"); w.run(1); ana.click("Leave"); w.run(40)
    check(peers(ana) == [] and peers(ben) == [], "Ana leaves her friend: it stays that way (%r %r)" % (peers(ana), peers(ben)))
    ben.dialog = None; ben.say(12, "connect"); w.run(0.5); ben.click("Invite"); w.run(2)
    nm = [x for x in ben.labels() if x.lstrip("★ ") == "Ana"]
    if nm: ben.click(nm[0]); w.run(2)
    check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"] and not ana.dialog, "Ben asks her himself: his friend joins at once, as friends do")
    ana.dialog = None; ana.say(12, "connect"); w.run(1); ana.click("Leave"); w.run(25)
    check(peers(ana) == [] and peers(ben) == [], "she leaves again: it stays that way")
    ana.dialog = None; ana.say(12, "connect"); w.run(0.5); ana.click("Invite"); w.run(2)
    nm = [x for x in ana.labels() if x.lstrip("★ ") == "Ben"]
    if nm: ana.click(nm[0]); w.run(2)
    check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "she asks him herself: together again")
    # 2. a hold (everything off) is off for Connect too; a hold again brings friends back
    t = w.t
    ana.long_press(); w.run(30)
    check(peers(ana) == [] and peers(ben) == [], "Ana holds: everything off, friends stay apart (%r %r)" % (peers(ana), peers(ben)))
    check(not any(c[1] == "Ana" and "|here|" in c[3] and c[0] > t + 2 for c in w.chatlog), "off: Ana's HUD says nothing to the region")
    ben.dialog = None; ben.say(12, "connect"); w.run(0.5); ben.click("Invite"); w.run(4)
    check(not any(x.startswith("Ana") for x in ben.labels()), "off: Ana is not in Ben's list (%r)" % ben.labels())
    ana.long_press(); w.run(25)
    check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "a hold again: the friends connect by themselves again (%r %r)" % (peers(ana), peers(ben)))
    no_errors(w, "review: leave and off")

    # 3. a second copy worn: the older one steps aside and keeps out of Connect (8.8.2: it answered for Ana too)
    w, (ana, ben) = setup()
    friends(ana, ben); w.run(25)
    old = ana.hud
    ana.wear(HUD, parts=HP, lsd=dict(ready(ana), **{"cin.friends": old.lsd["cin.friends"]})); w.run(0.5); manual(ana.hud); w.run(4.5)
    check(var(old, "carry", "gAside"), "(the older copy stepped aside)")
    w.run(25)
    check(peers(ben) == ["Ana"], "Ben is with Ana's new copy (%r)" % peers(ben))
    shot(w, ana, "portrait"); w.run(2)
    link(w, ben); w.run(12)
    check(host(ben) is ana and B.llVecDist(ben.camera()[0], ana.camera()[0]) < 0.05, "Ben watches Ana: the older copy never says she stopped (host %r)" % host(ben))
    check(S(ana) is not None and not [k for k in next(s for s in old.scripts if s.name == "sync").g["gP"]], "the older copy is connected with nobody")
    no_errors(w, "review: two copies")

    # 4. a watcher who takes the HUD off (or logs off): no SHARING left, nothing sent on (8.8.2: for up to 30 min)
    w, (ana, ben) = setup()
    ask(w, ana, ben); shot(w, ana, "tracking"); w.run(2)
    link(w, ben); w.run(2)
    check(linkst(ana) == "shared", "Ben watches: SHARING")
    ben.take_off(); w.run(15)
    t = w.t; w.run(3)
    check(linkst(ana) != "shared" and not S(ana)["gW"], "Ben's HUD is off: Ana's SHARING goes (%s, %r)" % (linkst(ana), S(ana)["gW"]))
    check(cams_from(w, "Ana", t) == 0, "... and her camera goes to nobody (%d)" % cams_from(w, "Ana", t))
    no_errors(w, "review: a watcher gone")

    # 5. tapping the rings while someone asks you: their question again (8.8.2: the question could not be answered any more,
    #    and everyone else asking was "busy" until the HUD was worn again); 6. a Yes after 20 s still connects both
    w, (ana, ben, cy) = setup(("Ana", "Ben", "Cy"))
    ana.dialog = None; ana.say(12, "connect"); w.run(0.5); ana.click("Invite"); w.run(3); ana.click("Ben"); w.run(1)
    check(ben.dialog and "wants to share films" in ben.dialog[1], "Ben is asked")
    asked = ben.dialog
    link(w, ben)
    check(ben.dialog and "wants to share films" in ben.dialog[1], "Ben taps his rings: Ana's question again (%r)" % (ben.dialog and ben.dialog[1]))
    w.run(30)
    if ben.dialog and "Yes" in ben.labels(): ben.click("Yes")
    w.run(2)
    check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "Ben says yes after 30 s: both connected (%r %r)" % (peers(ana), peers(ben)))
    w2, (dee, eve) = setup(("Dee", "Eve"))
    dee.dialog = None; dee.say(12, "connect"); w2.run(0.5); dee.click("Invite"); w2.run(3); dee.click("Eve"); w2.run(1)
    q = eve.dialog
    eve.dialog = None; eve.hud.send(7371, "connect|friends"); w2.run(1)            # another of Connect's pages over the question
    eve.say(q[3], "Yes"); w2.run(80)                                                 # the old question's Yes: nobody listens now
    t = w2.t
    fay = w2.avatar("Fay", (130, 130, 21)); fay.fov = 0.6125
    fay.wear(HUD, parts=HP, lsd=ready(fay)); w2.run(0.5); manual(fay.hud); w2.run(5)
    fay.dialog = None; fay.say(12, "connect"); w2.run(0.5); fay.click("Invite"); w2.run(3)
    if "Eve" in fay.labels(): fay.click("Eve"); w2.run(1.5)
    check(not any("busy" in n for n in fay.notes(t)) and eve.dialog and "Fay wants" in eve.dialog[1], "a question nobody can answer any more ends: Eve is not busy for ever (%r)" % fay.notes(t))
    no_errors(w, "review: asked"); no_errors(w2, "review: asked 2")

    # 7. the frame of a still shot reaches the watcher when it changes; 8. a still shot stays still for the watcher
    w, (ana, ben) = setup()
    ask(w, ana, ben); shot(w, ana, "portrait"); w.run(2)
    link(w, ben); w.run(2)
    check(host(ben) is ana, "Ben watches Ana's Portrait")
    was = var(ben.hud, "bars", "gFollow")
    want = "1.66" if was != "1.66" else "2.00"
    ana.hud.lsd["cin.shape"] = (want, PASS); ana.hud.send(7330, "shape"); w.run(3)
    check(var(ben.hud, "bars", "gFollow") == want, "Ana's frame %s reaches Ben's bars (%r, was %r)" % (want, var(ben.hud, "bars", "gFollow"), was))
    cam = ana.camera()[0]
    ana.pos = B.add(ana.pos, vec(0.4, 0.3, 0)); w.run(0.6)
    check(B.llVecDist(ana.camera()[0], cam) < 0.01 and B.llVecDist(ben.camera()[0], cam) < 0.05,
          "Ana shifts a little in her still shot: Ben's view stays where hers is (%.2f m off)" % B.llVecDist(ben.camera()[0], ana.camera()[0]))
    no_errors(w, "review: still shots")

    # 9. a Watch from a dialog left open, on someone out of reach since: nothing (8.8.2: watched them for good)
    w, (ana, ben) = setup()
    ask(w, ana, ben); shot(w, ben, "tracking"); w.run(2)
    ana.dialog = None; ana.say(12, "connect"); w.run(0.5)
    if "Ben" in ana.labels(): ana.click("Ben"); w.run(0.5)
    stale = ana.dialog
    check(stale and "Watch" in ana.labels(), "a name: Watch (%r)" % ana.labels())
    ben.walk((128, 165, 21), speed=4); w.run(14)
    ana.dialog = stale; ana.click("Watch"); w.run(3)
    check(host(ana) is None and var(ana.hud, "core", "gState") != "watch", "Watch on someone out of reach: nothing")
    no_errors(w, "review: a stale Watch")

    # 10. sync started again while you watch: your own film, not a frozen view
    w, (ana, ben) = setup()
    ask(w, ana, ben); shot(w, ana, "tracking"); shot(w, ben, "portrait"); w.run(2)
    link(w, ben); w.run(2)
    check(host(ben) is ana, "Ben watches Ana")
    ben.hud.crash("sync"); w.run(9)
    check(var(ben.hud, "core", "gState") != "watch" or host(ben) is ana, "Ben's sync started again: he isn't left on a frozen view (core %s)" % var(ben.hud, "core", "gState"))
    no_errors(w, "review: sync again")

    # 11. the rings while your one friend watches you: "Ben is watching your film." (8.8.2: "Ben isn't filming.")
    w, (ana, ben) = setup()
    ask(w, ana, ben); shot(w, ana, "portrait"); w.run(2)
    link(w, ben); w.run(2)
    t = w.t
    link(w, ana)
    check("Ben is watching your film." in ana.notes(t) and not any("isn't filming" in n for n in ana.notes(t)), "Ana taps her rings: Ben is watching your film (%r)" % ana.notes(t))
    # 12. standing at 20 m: one "out of reach", not a note at every step
    link(w, ben); w.run(1)
    t = w.t
    for i in range(10):
        ben.walk((128, 128 + 19.6 + (i % 2) * 0.9, 21), speed=1); w.run(3)
    n = len([x for x in ana.notes(t) if "out of reach" in x or "is back" in x])
    check(n <= 2, "Ben steps back and forth across 20 m: at most one out of reach and one back (%d)" % n)
    no_errors(w, "review: notes")

    # 13. efficiency: a watched camera that stands still goes out once a second, not 7 times
    w, (ana, ben) = setup()
    ask(w, ana, ben); shot(w, ana, "tracking"); w.run(4)
    link(w, ben); w.run(3)
    t = w.t; w.run(5)
    n = cams_from(w, "Ana", t)
    check(n <= 7, "Ana stands still in Tracking, watched: her camera goes out about once a second (%d in 5 s)" % n)
    ana.walk((140, 128, 21), speed=1.5)
    t = w.t; w.run(4)
    n = cams_from(w, "Ana", t)
    check(n >= 20, "she walks: 7 a second again (%d in 4 s)" % n)
    no_errors(w, "review: still camera")

    # 14. worn again with every "back" lost (in-world, carry may still be starting when sync asks it): Ben, who kept the
    #     connection, sends his heartbeat, and that rejoins them
    w, (ana, ben) = setup()
    ask(w, ana, ben); w.run(2)
    kept = dict(ana.hud.lsd)
    ana.take_off(); w.run(3)
    say = w.chat
    w.chat = lambda sp, ch, msg, to=None, name="": None if "|back|" in msg else say(sp, ch, msg, to=to, name=name)
    ana.wear(HUD, parts=HP, lsd=kept); w.run(0.5); manual(ana.hud); w.run(3)
    w.chat = say
    check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "worn again, every 'back' lost: Ben's heartbeat rejoins them (%r %r)" % (peers(ana), peers(ben)))
    ana.dialog = None; ana.say(12, "connect"); w.run(1); ana.click("Leave"); w.run(3)
    check(peers(ana) == [] and peers(ben) == [], "... and a Leave still ends it")
    no_errors(w, "review: rejoin")

# ---- 8.9.0: an Alt-click close-up of a thing, watched through another lens. The watcher moved along the view round you,
# not round what the picture looks at, and could end up past it (in-world: "a wall camera" while a friend framed a toy)
def closeup(scripts=HUD_SCRIPTS, parts=PARTS):
    import math
    global HUD, HP
    HUD, HP = scripts, parts
    w, (ana, ben) = setup()
    ana.fov = 0.6125; ben.fov = 1.047
    ask(w, ana, ben); w.run(2)
    toy = (131.0, 126.0, 20.9)                                           # a small thing on the ground, 3.6 m from Ana
    w.boxes.append(Box((toy[0] - 0.1, toy[1] - 0.1, 20.0, toy[0] + 0.1, toy[1] + 0.1, toy[2]), "toy"))
    cam = (toy[0] - 0.7, toy[1] + 0.1, toy[2] + 0.25)
    ana.alt_orbit(to=cam, focus=(toy[0], toy[1], toy[2] - 0.05)); w.run(2)
    link(w, ben); w.run(3)
    check(host(ben) is ana, "Ben watches Ana's close-up")
    c = ben.camera()
    d0 = B.llVecDist(vec(*cam), vec(*toy))
    want = d0 * math.tan(0.6125 / 2) / math.tan(1.047 / 2)
    v = [c[1][i] - c[0][i] for i in range(3)]
    n = math.sqrt(sum(x * x for x in v))
    ahead = sum((toy[i] - c[0][i]) * v[i] / n for i in range(3))
    dist = B.llVecDist(c[0], vec(*toy))
    check(ahead > 0.1 and abs(dist - want) / want < 0.25, "the toy is in front of Ben's camera, the same size (%.2f m away, %.2f for the same size)" % (dist, want))
    no_errors(w, "close-up")

if __name__ == "__main__":
    if sys.argv[1:2] == ["review"]:
        closeup(); review(); review(LAB_SCRIPTS, LAB_PARTS); done("connect_emu review"); sys.exit()
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    scenarios()
    streaming()
    rework()
    lens_match()
    n = fuzz(runs, seed, ("Ana", "Ben"))
    n += fuzz(runs // 2, seed + 5000, ("Ana", "Ben", "Cy"))
    n += fuzz(runs // 2, seed + 9000, ("Ana", "Ben"), drop=0.05)
    n += fuzz(runs // 2, seed + 13000, ("Ana", "Ben", "Cy"), mates=True)
    review()
    review(LAB_SCRIPTS, LAB_PARTS)                                     # the new design (lab/) wears the same Connect
    closeup()
    check(n == 0, "%d fuzz runs broke an invariant" % n)
    print("connect (real scripts): scenarios, then %d fuzz runs on 2 and 3 HUDs (and lost messages)" % (runs * 2))
    done("connect_emu")
