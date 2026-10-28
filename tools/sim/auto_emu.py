"""Auto (8.3.0; its rhythm 8.4.0, docs/PRODUCT.md "Auto: the guide"), on the REAL scripts: a day with the camera
directing itself. Moving 1 s (keys or speed): Tracking at once, from any shot, from a hold too, never anything else
while moving (8.3.0 kept Portrait while you walked a room in short bursts). Still alone 10 s: Scenic Drift; 5 minutes
or Away: Scenic wide (Far outdoors, Room indoors). Still 4 s with 1-3 people within 3 m: Portrait Us; a crowd: Drift.
A seat with a kept view: Fixed; another seat: Drift. 8 s a shot. Auto's options never kept; core's idle start off.
The strip: the Orbit lit, the shot faint. Manual and back, Connect, a HUD without the Orbit part."""
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

# ---- on wear: Auto, Tracking (it holds behind you) ---------------------------------------------------------------------
w.run(2.5)
check(var(h, "tracking", "gAuto") == 1 and var(h, "strip", "gAuto") == 1 and var(h, "core", "gAuto") == 1, "on wear, set up: Auto")
check(state(h) == ("film", "tracking"), "standing on wear: Tracking %r" % (state(h),))
check(var(h, "tracking", "gLook") == 1 and lsd(h, "trk") == "0|1", "Auto's Tracking: Film, hers kept")
check(any(n.startswith("Auto: Tracking as you move") for n in ana.notes()), "the tip says what Auto does")
check(h.part("t12 auto")["alpha"] > 0.9, "the Orbit is lit")
check(faint(h, ana) == {"t12 s0": 0.36}, "the strip: only the shot Auto chose, faint %r" % faint(h, ana))
check(opts_on(h, ana) == [], "the strip: no options in Auto %r" % opts_on(h, ana))
o, s0 = rect(h, ana, "t12 auto"), rect(h, ana, "t12 s0")
check(o[0] < s0[0] - (o[2] + s0[2]) / 2 + 1e-6 and o[0] < rect(h, ana, "t12 shape")[0], "the Orbit at the left end, then the shot")
no_errors(w, "wear")

# ---- resting: Tracking holds, then Drift after 10 s --------------------------------------------------------------------
w.run(4)
check(state(h)[1] == "tracking", "still 6.5 s: Tracking holds")
t = until(w, lambda: state(h)[1] == "scenic", 6)
check(t is not None and var(h, "scenic", "gBand") == 0 and lsd(h, "scn") == "2", "still 10 s: Scenic Drift (hers, Room, kept)")
check(faint(h, ana) == {"t12 s3": 0.36}, "the strip: SCENIC, faint %r" % faint(h, ana))
w.run(8)
# a key tapped is not a walk
for i in range(3):
    ana.keys(C["CONTROL_FWD"], hold=0.4); w.run(3)
check(state(h)[1] == "scenic", "a step: no cut")

# ---- moving: Tracking at once, also walking a room in short bursts (8.3.0 stayed in Portrait) ----------------------------
ana.keys(C["CONTROL_FWD"], hold=3)
t = until(w, lambda: state(h)[1] == "tracking", 3)
check(t is not None and t <= 1.75, "walking with the keys: Tracking within 1.5 s (%s)" % t)
w.run(3)
for i in range(4):
    ana.keys(C["CONTROL_FWD"], hold=1.6); w.run(2.4); ana.face(90 * (i + 1))
check(state(h)[1] == "tracking", "short bursts round a room: Tracking all along")
no_errors(w, "move and rest")

# ---- someone near: Portrait Us; they leave: Drift ------------------------------------------------------------------------
ben = w.avatar("Ben", B.add(ana.pos, vec(1.5, 0.5, 0)))
t = until(w, lambda: state(h)[1] == "portrait", 10)
check(t is not None and t >= 3.5, "Ben within 3 m, both still: Portrait after 4 s (%s)" % t)
check(var(h, "portrait", "gSize") == 1 and var(h, "portrait", "gUs") == 1 and lsd(h, "por") == "2|0", "Auto's Portrait: Medium · Us, hers kept")
w.run(3)
check(len(var(h, "portrait", "gWith")) == 1, "Us has Ben (%r)" % var(h, "portrait", "gWith"))
w.run(20)
check(state(h)[1] == "portrait", "a conversation: Portrait holds")
ana.keys(C["CONTROL_FWD"], hold=2)
t = until(w, lambda: state(h)[1] == "tracking", 2)
check(t is not None, "walking off from Portrait: Tracking at once")
ana.walk(ana.pos); w.run(1)
ben.pos = B.add(ana.pos, vec(1.0, -1.0, 0)); w.run(12)
check(state(h)[1] == "portrait", "Ben comes along: Portrait again")
ben.pos = vec(200, 200, 21)
t = until(w, lambda: state(h)[1] == "scenic", 8)
check(t is not None and t >= 2.5, "Ben gone 3 s: Drift (%s)" % t)
crowd = [w.avatar("P%d" % i, B.add(ana.pos, vec(1.0 + 0.3 * i, 1.0, 0))) for i in range(5)]
w.run(16)
check(state(h)[1] == "scenic", "a crowd within 3 m: Drift, no Portrait")
for p in crowd: p.pos = vec(220, 220 + p.pos[1], 21)
no_errors(w, "company")

# ---- a long while: Scenic wide (Far outdoors); Away: at once ---------------------------------------------------------------
w.run(300)
check(state(h)[1] == "scenic" and var(h, "scenic", "gBand") == 3 and lsd(h, "scn") == "2", "5 minutes outdoors: Far (%s)" % var(h, "scenic", "gBand"))
check(var(h, "core", "gWhy") == "", "core's idle start stays off in Auto")
ana.keys(C["CONTROL_FWD"], hold=2)
t = until(w, lambda: state(h)[1] == "tracking", 2)
check(t is not None, "from Far, walking: Tracking at once")
ana.walk(ana.pos); w.run(12)
ana.away = True
t = until(w, lambda: var(h, "scenic", "gBand") == 3 and state(h)[1] == "scenic", 9)
check(t is not None, "Away: wide (once Drift has had its 8 s)")
ana.away = False
no_errors(w, "long while")

# ---- Alt-click: Auto waits; walking off or Esc gives it back --------------------------------------------------------------
ana.keys(C["CONTROL_FWD"], hold=2); w.run(4)                          # Tracking, then still
ana.alt_orbit(to=B.add(ana.pos, vec(9, 9, 4))); w.run(3)
check(state(h) == ("held", "tracking"), "Alt-click: held %r" % (state(h),))
w.run(15)
check(state(h) == ("held", "tracking"), "held: Auto keeps its hands off (no Drift) %r" % (state(h),))
ana.esc()
t = until(w, lambda: state(h)[0] == "film", 4)
check(t is not None, "Esc: the shot again (%s s)" % t)
w.run(9)
ana.alt_orbit(to=B.add(ana.pos, vec(9, 9, 4))); w.run(3)
ana.esc(); ana.keys(C["CONTROL_FWD"], hold=2)
t = until(w, lambda: state(h) == ("film", "tracking"), 2)
check(t is not None, "held, then walking off: Tracking")
ana.walk(ana.pos)
no_errors(w, "held")

# ---- sitting: a kept seat, Fixed; another seat, Drift ------------------------------------------------------------------------
w.run(9)
stool = w.furniture("Stool", B.add(ana.pos, vec(0, 3, -0.5)))
ana.sit_on(stool); w.run(5)
check(state(h)[1] == "tracking" and var(h, "core", "gSitHold") == 1, "a seat with nothing kept: the frame holds first %r" % (state(h),))
t = until(w, lambda: state(h)[1] == "scenic", 8)
check(t is not None, "... then Drift")
ana.stand(); w.run(4)
sofa = w.furniture("Sofa", B.add(ana.pos, vec(0, -4, -0.5)))
h.lsd["cin.seat." + str(sofa.key)] = ("<2.5, -0.5, 1.2>|<0.0, -0.5, 1.0>|<0.0, -0.5, 0.6>|0.0|1.047198", PASS)
w.run(9)
ana.sit_on(sofa, at=(0, -0.5, 0.6))
t = until(w, lambda: state(h)[1] == "fixed", 4)
check(t is not None and t >= 1.5, "the sofa's kept view: Fixed after 2 s (%s)" % t)
w.run(1)
want = B.add(sofa.pos, vec(2.5, -0.5, 1.2))
check(B.llVecDist(h.cam["pos"], want) < 0.2, "... at that view (%s, want %s)" % (h.cam.get("pos"), want))
w.run(20)
check(state(h)[1] == "fixed", "seated at a kept view: Fixed stays")
ana.stand(); ana.pos = B.add(sofa.pos, vec(0, 3, 0.5)); ana.keys(C["CONTROL_FWD"], hold=2)
t = until(w, lambda: state(h)[1] == "tracking", 3)
check(t is not None, "up and walking: Tracking")
ana.walk(ana.pos)
no_errors(w, "seats")

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
# /12 portrait: manual, her own options; /12 auto: Auto
ana.walk(ana.pos); ana.vel = vec(0, 0, 0)
ana.say(12, "portrait"); w.run(1)
check(var(h, "tracking", "gAuto") == 0 and state(h)[1] == "portrait", "/12 portrait: manual")
check(var(h, "portrait", "gSize") == 2 and var(h, "portrait", "gUs") == 0, "... in her own Wide · Me")
ana.say(12, "auto"); w.run(1)
check(var(h, "tracking", "gAuto") == 1, "/12 auto: Auto")
no_errors(w, "manual")

# ---- indoors: wide is Room ---------------------------------------------------------------------------------------------
w5 = World()
w5.boxes += room(120, 120, 20.0, 130, 130, 3.0)
dee, hd = hud(w5, "Dee", (125, 125, 21.0), auto=True)
w5.run(14)
check(state(hd)[1] == "scenic" and var(hd, "scenic", "gLocal") == 1, "indoors, resting: Drift in the room")
dee.away = True
t = until(w5, lambda: var(hd, "scenic", "gBand") == 2, 4)
check(t is not None, "indoors, Away: Room (%s)" % var(hd, "scenic", "gBand"))
no_errors(w5, "indoors")

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
check(var(h3, "tracking", "gAuto") == 1 and state(h3)[1] == "tracking", "no Orbit part: Auto directs")
check(len(visible(h3, cat, ("t12 s",))) >= 4, "... and the shot words stay (a tap is manual)")
no_errors(w2, "no part")
done("auto_emu")
