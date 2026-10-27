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

def S(a, n="sync"): return var(a.hud, n, "__all__") if False else next(s for s in a.hud.scripts if s.name == n).g
def peers(a): return [a.w.avatars[k].name for k in S(a)["gP"] if k in a.w.avatars]
def host(a):
    k = S(a)["gHost"]
    return a.w.avatars.get(k) if k and k != NK else None
def linkst(a): return var(a.hud, "screen", "gLinkSt")
def notes(a, since): return a.notes(since)

def setup(names=("Ana", "Ben"), seed=1, free=()):
    w = World(seed=seed)
    avs = []
    for i, n in enumerate(names):
        av = w.avatar(n, (128 + 2 * i, 128, 21))
        av.fov = 0.6125
        av.wear(FREE_SCRIPTS if n in free else HUD_SCRIPTS, lsd=ready(av))
        avs.append(av)
    w.run(5)
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
    shot(w, ana, "portrait")
    w.run(2)
    check(linkst(ben) == "on", "Ana films: Ben's key lights (%s)" % linkst(ben))
    t = w.t
    link(w, ben)
    check(host(ben) is ana and var(ben.hud, "core", "gState") == "watch", "Ben taps Connect: he watches Ana's film")
    check(B.llVecDist(ben.camera()[0], ana.camera()[0]) < 0.05 and ben.hud.cam.get("by") == "sync", "Ben sees Ana's camera")
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
    check(host(ana) is None and "Ben isn't filming." in notes(ana, t), "Ana taps Connect while Ben watches her: Ben isn't filming")
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
    ana.wear(HUD_SCRIPTS, lsd=kept)
    w.run(8)
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
    ana.say(12, "connect"); w.run(4); ana.click("Ben"); w.run(2)
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
    ana.click("Cy"); w.run(2)
    check(host(ana) is cy, "Ana watches Cy")
    no_errors(w, "three")

    # ---- an older and a newer Take 12 -------------------------------------------------------------------------------------------
    w, (ana,) = setup(("Ana",))
    olga = w.avatar("Olga", (130, 129, 21))
    o = Obj(w, olga, [], children=()); o.worn = True; w.objects[o.key] = o
    ana.say(12, "connect"); w.run(0.3)
    w.chat(o, CH, "T12|here|T|idle|", to=ana.key)
    w.run(4)
    check("Olga (old)" in ana.labels(), "a 7.x Take 12: listed as (old) (%r)" % ana.labels())
    t = w.t
    ana.click("Olga (old)"); w.run(1)
    check("Olga's Take 12 is older. A new copy fixes it." in notes(ana, t), "tapping it explains")
    nina = w.avatar("Nina", (127, 129, 21))
    o2 = Obj(w, nina, [], children=()); o2.worn = True; w.objects[o2.key] = o2
    t = w.t
    w.chat(o2, CH, "T12|8|here|8.1.0|0", to=ana.key); w.run(1)
    w.chat(o2, CH, "T12|8|here|8.1.0|0", to=ana.key); w.run(1)
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

def fuzz(runs, seed, names, drop=0.0):
    broken = 0
    for r in range(runs):
        rng = random.Random(seed + r)
        w, avs = setup(names, seed=seed + r)
        steps = []
        if rng.random() < 0.7:                                         # most runs start connected
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
                if a.dialog and b.name in a.labels(): a.click(b.name)
            elif act == "alt": a.alt_orbit()
            elif act == "esc": a.esc(); a.keys(C["CONTROL_FWD"], hold=0.2)
            elif act == "walk": a.walk((128 + rng.uniform(-30, 30), 128 + rng.uniform(-30, 30), 21), speed=4)
            elif act == "back": a.walk((128 + rng.uniform(-3, 3), 128 + rng.uniform(-3, 3), 21), speed=4)
            elif act == "off": a.long_press()
            elif act == "rewear":
                if a.hud and a.hud.worn: a.take_off()
                else: a.wear(HUD_SCRIPTS, lsd=ready(a)); w.run(5); a.double_tap()
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
    check(12 <= n <= 20, "her camera goes out about 4 times a second (%d in 4 s)" % n)
    link(w, ben); w.run(0.5)
    mine = ben.camera()[0]
    w.chat(ana.hud, CH, "T12|8|cam|<1,1,30>|<2,2,30>|0|1.0|0", to=ben.key); w.run(0.5)
    check(B.llVecDist(ben.camera()[0], mine) < 0.5, "a late update after he stopped watching is ignored")
    no_errors(w, "streaming")

if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    scenarios()
    streaming()
    n = fuzz(runs, seed, ("Ana", "Ben"))
    n += fuzz(runs // 2, seed + 5000, ("Ana", "Ben", "Cy"))
    n += fuzz(runs // 2, seed + 9000, ("Ana", "Ben"), drop=0.05)
    check(n == 0, "%d fuzz runs broke an invariant" % n)
    print("connect (real scripts): scenarios, then %d fuzz runs on 2 and 3 HUDs (and lost messages)" % (runs * 2))
    done("connect_emu")
