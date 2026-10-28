"""Auto (8.3.0), on the REAL scripts: a day with the camera directing itself. On wear (set up) Auto lights the Orbit and
picks the shot from what a script sees: standing, Portrait (Medium · Us, not kept); walking 2 s, Tracking (Film, not
kept); standing still 6 s, Portrait again; at least 8 s a shot and no ping-pong for a step or two; sitting, the seat's
kept view (Fixed), else the frame holds; idle, Scenic's Drift; flying, hands off. Alt-click yields, Esc gives the shot
back. The strip in Auto: the Orbit lit, the shot it chose faint, no options. A tap on the faint shot (or a shot of your
own, /12 tracking) is manual; the Orbit (or /12 auto) gives the camera back to Auto."""
from emu_util import *

def faint(h, ana):
    """the shot words on the strip now: {name: alpha}"""
    return {n: round(r[4], 2) for n, r in visible(h, ana, ("t12 s",)).items() if len(n) == 6}

def opts_on(h, ana): return sorted(n for n in visible(h, ana, ("t12 o",)))

def until(w, cond, limit):
    """run until cond() holds, at most limit s: the seconds it took, or None"""
    t = 0.0
    while t < limit:
        if cond(): return t
        w.run(0.25); t += 0.25
    return t if cond() else None

w = World()
w.avatar("Cid", (140, 140, 21))                                      # someone in the region, far away
ana = w.avatar("Ana", (128, 128, 21))
L = ready(ana)
L["cin.por"] = ("2|0", PASS)                                         # her own Portrait: Wide · Me
L["cin.trk"] = ("0|1", PASS)                                         # her own Tracking: Shoulder · R
L["cin.scn"] = ("2", PASS)                                           # her own Scenic: Room
L["cin.open"] = ("1", PASS)
h = ana.wear(HUD_SCRIPTS, lsd=L)
textures(h)
w.run(2)
check(state(h) == ("wait", ""), "worn: Take 12 waits a moment %r" % (state(h),))

# ---- on wear: Auto ----------------------------------------------------------------------------------------------------
w.run(2.5)
check(var(h, "tracking", "gAuto") == 1 and var(h, "strip", "gAuto") == 1 and var(h, "core", "gAuto") == 1, "on wear, set up: Auto")
check(state(h) == ("film", "portrait"), "standing: Portrait %r" % (state(h),))
check(var(h, "portrait", "gSize") == 1 and var(h, "portrait", "gUs") == 1 and lsd(h, "por") == "2|0", "Auto's Portrait: Medium · Us, hers kept (%s)" % lsd(h, "por"))
check(any(n.startswith("Auto picks the shot") for n in ana.notes()), "the tip says what Auto does")
check(h.part("t12 auto")["alpha"] > 0.9, "the Orbit is lit")
check(faint(h, ana) == {"t12 s1": 0.36}, "the strip: only the shot Auto chose, faint %r" % faint(h, ana))
check(opts_on(h, ana) == [], "the strip: no options in Auto %r" % opts_on(h, ana))
o, s1 = rect(h, ana, "t12 auto"), rect(h, ana, "t12 s1")
check(o[0] < s1[0] - (o[2] + s1[2]) / 2 + 1e-6 and o[0] < rect(h, ana, "t12 shape")[0], "the Orbit at the left end, then the shot")
no_errors(w, "wear")

# ---- walking: Tracking, after 2 s of it and 8 s of Portrait -------------------------------------------------------------
w.run(6)
ana.walk((128, 160)); w.run(1.0)
check(state(h)[1] == "portrait", "a step is not a walk: still Portrait")
t = until(w, lambda: state(h)[1] == "tracking", 6)
check(t is not None and t >= 0.8, "walking 2 s: Tracking (%s s later)" % t)
check(var(h, "tracking", "gLook") == 1 and lsd(h, "trk") == "0|1", "Auto's Tracking: Film, hers kept")
check(faint(h, ana) == {"t12 s0": 0.36}, "the strip: TRACKING, faint %r" % faint(h, ana))
w.run(8)

# ---- standing still 6 s: Portrait -----------------------------------------------------------------------------------
ana.walk(ana.pos); ana.vel = vec(0, 0, 0)
w.run(4.5)
check(state(h)[1] == "tracking", "still 4.5 s: still Tracking")
t = until(w, lambda: state(h)[1] == "portrait", 3)
check(t is not None, "still 6 s: Portrait")
# no ping-pong: a step or two and stop
cuts = []
for i in range(3):
    ana.walk(B.add(ana.pos, vec(1.2, 0, 0))); w.run(1.0); w.run(3)
    cuts.append(state(h)[1])
check(cuts == ["portrait"] * 3, "steps of a second: no cut %r" % cuts)
no_errors(w, "walk and stop")

# ---- someone near: Us ---------------------------------------------------------------------------------------------------
ben = w.avatar("Ben", B.add(ana.pos, vec(1.5, 0.5, 0)))
w.run(4)
check(len(var(h, "portrait", "gWith")) == 1, "Ben within 3 m: Us has him (%r)" % var(h, "portrait", "gWith"))
ben.pos = vec(200, 200, 21); w.run(4)

# ---- sitting: the frame holds; a seat with a kept view: Fixed ------------------------------------------------------------
stool = w.furniture("Stool", B.add(ana.pos, vec(0, 3, -0.5)))
ana.sit_on(stool); w.run(5)
check(state(h)[1] == "portrait" and var(h, "core", "gSitHold") == 1, "a seat with nothing kept: the frame holds %r" % (state(h),))
ana.stand(); w.run(4)
sofa = w.furniture("Sofa", B.add(ana.pos, vec(0, -4, -0.5)))
h.lsd["cin.seat." + str(sofa.key)] = ("<2.5, -0.5, 1.2>|<0.0, -0.5, 1.0>|<0.0, -0.5, 0.6>|0.0|1.047198", PASS)
ana.sit_on(sofa, at=(0, -0.5, 0.6)); w.run(1)
check(state(h)[1] == "portrait", "sat down: 2 s first")
t = until(w, lambda: state(h)[1] == "fixed", 3)
check(t is not None, "the sofa's kept view: Fixed")
w.run(1)
want = B.add(sofa.pos, vec(2.5, -0.5, 1.2))
check(B.llVecDist(h.cam["pos"], want) < 0.2, "... at that view (%s, want %s)" % (h.cam.get("pos"), want))
ana.stand(); ana.pos = B.add(sofa.pos, vec(0, 3, 0.5)); w.run(1)
check(state(h)[1] == "portrait", "standing up: the shot before (core)")
w.run(3)
no_errors(w, "seats")

# ---- Alt-click: Auto yields; Esc gives the shot back ---------------------------------------------------------------------
w.run(9)
ana.alt_orbit(); w.run(3)
check(state(h)[0] == "held", "Alt-click: held")
w.run(10)
check(state(h) == ("held", "portrait"), "held: Auto keeps its hands off")
ana.esc()
t = until(w, lambda: state(h)[0] == "film", 4)
check(t is not None, "Esc: the shot again (%s s)" % t)
no_errors(w, "held")

# ---- idle: Drift --------------------------------------------------------------------------------------------------------
ana.away = True; w.run(2)
check(state(h) == ("film", "scenic") and var(h, "scenic", "gBand") == 0 and lsd(h, "scn") == "2", "away: Scenic, Drift (hers, Room, kept)")
w.run(12)
check(state(h)[1] == "scenic", "idle: Auto leaves Scenic alone")
ana.away = False; ana.keys(C["CONTROL_FWD"], hold=0.3); w.run(2)
check(state(h)[1] == "portrait", "back: the shot before")
no_errors(w, "idle")

# ---- flying: hands off ----------------------------------------------------------------------------------------------------
w.run(9)
ana.flying = True; ana.vel = vec(3, 0, 0); w.run(5)
check(state(h)[0] == "letgo", "flying: your camera %r" % (state(h),))
ana.flying = False; ana.vel = vec(0, 0, 0); w.run(3)
check(state(h)[0] == "film", "landed: the shot again")
no_errors(w, "fly")

# ---- manual: the faint shot tapped -----------------------------------------------------------------------------------------
w.run(9)
shot = state(h)[1]
ana.touch("t12 s%d" % ["tracking", "portrait", "fixed", "scenic"].index(shot)); w.run(1)
check(var(h, "tracking", "gAuto") == 0 and var(h, "strip", "gAuto") == 0 and state(h) == ("film", shot), "the faint shot tapped: yours, the shot goes on")
check(len(faint(h, ana)) == 4 and opts_on(h, ana) != [], "manual: the four shots and the options back")
check(h.part("t12 auto")["alpha"] < 0.8, "the Orbit quiet")
ana.walk((128, 200)); w.run(12)
check(state(h)[1] == shot, "manual: walking changes nothing")
# the Orbit: Auto again
ana.touch("t12 auto"); w.run(0.5)
check(var(h, "tracking", "gAuto") == 1 and var(h, "strip", "gAuto") == 1, "the Orbit tapped: Auto")
t = until(w, lambda: state(h)[1] == "tracking", 4)
check(t is not None, "still walking: Tracking")
# /12 portrait: manual; /12 auto: Auto
ana.walk(ana.pos); ana.vel = vec(0, 0, 0)
ana.say(12, "portrait"); w.run(1)
check(var(h, "tracking", "gAuto") == 0 and state(h)[1] == "portrait", "/12 portrait: manual")
check(var(h, "portrait", "gSize") == 2 and var(h, "portrait", "gUs") == 0, "... in her own Wide · Me")
ana.say(12, "auto"); w.run(1)
check(var(h, "tracking", "gAuto") == 1, "/12 auto: Auto")
no_errors(w, "manual")

# ---- a shot tapped before Auto starts: manual for this wear ---------------------------------------------------------------
ana.take_off(h); w.run(1)
h = ana.wear(HUD_SCRIPTS, lsd={k: v for k, v in h.lsd.items()})
w.run(1)
ana.say(12, "scenic"); w.run(6)
check(var(h, "tracking", "gAuto") == 0 and state(h)[1] == "scenic", "a shot of your own on wear: no Auto over it")
no_errors(w, "early tap")

# ---- Connect: Ben watches Ana's Auto film; his own Auto waits, and goes on after ------------------------------------------
w4 = World()
ana4, ha = hud(w4, "Ana", (128, 128, 21), auto=True)
ben4, hb = hud(w4, "Ben", (130, 128, 21), auto=True)
for av in (ana4, ben4): av.double_tap()
w4.run(2)
ana4.say(12, "connect"); w4.run(4)
if "Invite" in ana4.labels(): ana4.click("Invite"); w4.run(4)
nm = [x for x in ana4.labels() if x.lstrip("★ ").startswith("Ben")]
check(nm != [], "Ana's list has Ben %r" % ana4.labels())
if nm:
    ana4.click(nm[0]); w4.run(1)
    if ben4.dialog and "share films" in ben4.dialog[1]: ben4.click("Yes"); w4.run(1.5)
w4.run(2)
ben4.touch("t12 link"); w4.run(2)
check(var(hb, "core", "gState") == "watch", "Ben watches Ana's film (%s)" % var(hb, "core", "gState"))
w4.run(6)
ana4.walk((128, 170)); ben4.walk((130, 140))
t = until(w4, lambda: state(ha)[1] == "tracking", 12)
check(t is not None, "Ana walks: her Auto cuts to Tracking")
w4.run(3)
check(var(hb, "core", "gState") == "watch" and var(hb, "tracking", "gAuto") == 1, "Ben walks too: his Auto keeps its hands off while he watches")
check(B.llVecDist(ben4.camera()[0], ana4.camera()[0]) < 1.0, "Ben sees Ana's Tracking (%.2f m)" % B.llVecDist(ben4.camera()[0], ana4.camera()[0]))
ben4.touch("t12 link"); w4.run(1)
if ben4.dialog and "My film" in ben4.labels(): ben4.click("My film"); w4.run(1)
t = until(w4, lambda: var(hb, "core", "gState") == "film", 10)
check(t is not None, "Ben back to his own film: his Auto directs again (%s)" % (state(hb),))
no_errors(w4, "connect")

# ---- the strip without the Orbit's part (an older HUD): Auto still directs, the shots stay ---------------------------------
w2 = World()
cat = w2.avatar("Cat", (128, 128, 21))
h3 = cat.wear(HUD_SCRIPTS, lsd=ready(cat), parts=[p for p in PARTS if p != "t12 auto"])
w2.run(5); cat.double_tap(); w2.run(1)
check(var(h3, "tracking", "gAuto") == 1 and state(h3)[1] == "portrait", "no Orbit part: Auto directs")
check(len(visible(h3, cat, ("t12 s",))) >= 4, "... and the shot words stay (a tap is manual)")
no_errors(w2, "no part")
done("auto_emu")
