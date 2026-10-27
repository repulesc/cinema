"""The four shots and what happens around them (8.0), on the REAL scripts: each shot's options on the strip and the
one job of its lit tap, options remembered, sitting (every shot holds its frame and FIXED glows; standing up resumes),
Alt-click (the shot is held: nothing shared, the lit word dims; a movement key or the lit tap gives it back), flying
and mouselook let go and come back, a marked vehicle lets go, a teleport gives a fresh frame, idle starts Scenic and a
key brings back the shot you had, the jump-cut rule, /12 blend."""
from emu_util import *

def opts(h):
    """the option words on the strip now: [(word, state)]"""
    sh = var(h, "strip", "gOptShot")
    return sh, list(zip(var(h, "strip", "gOpts"), var(h, "strip", "gOptSt")))

def lit(h): return [wd for wd, st in opts(h)[1] if st == "lit"]

w = World()
ana, h = hud(w)
ana.double_tap(); w.run(1)

# ---- each shot's options -------------------------------------------------------------------------------------------
ana.touch("t12 s0"); w.run(3)
check(opts(h) == ("tracking", [("SHOULDER", ""), ("FILM", "lit"), ("CLASSIC", ""), ("/", ""), ("L", ""), ("R", "lit")]), "Tracking: Film · R the first time: %r" % (opts(h),))
check(h.cam.get("distance") and not h.cam.get("plock"), "Tracking is the viewer's follow camera")
ana.touch(opt_part(h, "SHOULDER")); w.run(1)
check(lit(h) == ["SHOULDER", "R"] and lsd(h, "trk") == "0|1", "Shoulder picked and kept: %r %r" % (lit(h), lsd(h, "trk")))
check(abs(h.cam["distance"] - 1.6) < 0.05, "Shoulder is 1.6 m: %r" % h.cam["distance"])
ana.touch("t12 s1"); w.run(3)
check(opts(h)[0] == "portrait" and lit(h) == ["MEDIUM", "ME"], "Portrait: Medium · Me first: %r" % (opts(h),))
check(h.cam.get("plock") and h.cam.get("flock"), "Portrait is a locked shot")
ana.touch("t12 s2"); w.run(3)
check(opts(h)[0] == "fixed" and [x[0] for x in opts(h)[1]] == ["VIEW A", "VIEW B"] and lit(h) == ["VIEW A"], "Fixed standing: View A · View B: %r" % (opts(h),))
check(var(h, "core", "gFree") == 1 and "Frame it, Take 12 keeps it." in ana.notes(), "Fixed with nothing kept: your camera and the note")
ana.touch("t12 s3"); w.run(3)
check(opts(h)[0] == "scenic" and lit(h) == ["DRIFT"], "Scenic: Drift first: %r" % (opts(h),))
check(dict(opts(h)[1]).get("ROOM") == "dim", "outdoors ROOM is dim")
ana.touch("t12 s0"); w.run(3)
check(lit(h) == ["SHOULDER", "R"], "Tracking remembers Shoulder: %r" % lit(h))
no_errors(w, "options")

# ---- the lit tap: one job per shot ---------------------------------------------------------------------------------
ana.touch("t12 s1"); w.run(3)
p0 = h.cam["pos"]
side0 = var(h, "portrait", "gSide")
ana.touch("t12 s1"); w.run(2)
check(var(h, "portrait", "gSide") == -side0 and B.llVecDist(h.cam["pos"], p0) > 0.5, "Portrait's lit tap: the other 3/4 side")
ana.touch("t12 s3"); w.run(3)
c0 = h.cam["pos"]
ana.touch("t12 s3"); w.run(1.5)
check(B.llVecDist(h.cam["pos"], c0) > 0.3, "Scenic's lit tap: the next view now")
no_errors(w, "lit taps")

# ---- sitting holds; FIXED glows; standing resumes ------------------------------------------------------------------
ana.touch("t12 s1"); w.run(3)
log0 = len(h.cam.get("log", []))
sofa = w.furniture("Sofa", (130, 128, 20.5))
ana.sit_on(sofa); w.run(2)
check(var(h, "core", "gSitHold") == 1 and var(h, "strip", "gHint") == "fixed", "sitting in Portrait: it holds, FIXED glows")
check(len(h.cam.get("log", [])) == log0, "sitting: the frame holds (no new camera)")
w.run(6)
check(var(h, "strip", "gHint") == "", "the glow is once (5 s)")
ana.stand(); ana.pos = vec(128, 128, 21); w.run(3)
check(state(h) == ("film", "portrait") and var(h, "core", "gSitHold") == 0 and len(h.cam.get("log", [])) > log0, "standing up: Portrait frames you again")
no_errors(w, "sitting")

# ---- Alt-click: the shot is held ------------------------------------------------------------------------------------
w.run(3)
ana.alt_orbit(); w.run(1.5)
check(state(h)[0] == "held", "Alt-click: held (%r)" % (state(h),))
check(h.part("t12 box")["alpha"] < 0.5, "held: the lit shot dims")
ana.esc(); ana.keys(C["CONTROL_FWD"], hold=0.3); w.run(2)
check(state(h)[0] == "film", "a movement key gives the shot back")
w.run(3)
ana.alt_orbit(); w.run(1.5)
ana.touch("t12 s1"); w.run(0.5); ana.esc(); w.run(2)
check(state(h)[0] == "film", "the lit tap gives the shot back")
no_errors(w, "held")

# ---- flying and mouselook let go, and come back ---------------------------------------------------------------------
ana.flying = True; w.run(1)
check(state(h)[0] == "letgo" and not h.cam.get("active"), "flying: your own camera")
ana.flying = False; w.run(3)
check(state(h) == ("film", "portrait") and h.cam.get("active"), "landed: Portrait again")
ana.mouselook = True; w.run(1)
check(state(h)[0] == "letgo", "mouselook: let go")
ana.mouselook = False; w.run(3)
check(state(h)[0] == "film", "out of mouselook: back")
no_errors(w, "let go")

# ---- a marked vehicle lets go ----------------------------------------------------------------------------------------
boat = w.furniture("Sailboat", (140, 128, 20.5), creator="11111111-2222-3333-4444-555555555555")
ana.touch("t12 s2"); w.run(2)
ana.sit_on(boat); w.run(3)
check([x[0] for x in opts(h)[1]] == ["FORGET SEAT", "LET GO"], "Fixed seated: Forget seat · Let go: %r" % (opts(h),))
ana.touch(opt_part(h, "LET GO")); w.run(1.5)
check(state(h)[0] == "letgo" and "Sailboat|11111111-2222-3333-4444-555555555555" in lsd(h, "veh"), "LET GO marks it and lets go")
check(lit(h) == ["TAKE BACK"], "on a marked seat: TAKE BACK lit: %r" % (opts(h),))
ana.stand(); w.run(3)
ana.touch("t12 s1"); w.run(3)
ana.sit_on(boat); w.run(2)
check(state(h)[0] == "letgo", "sitting on it again, in Portrait: Take 12 lets go by itself")
ana.stand(); ana.pos = vec(128, 128, 21); w.run(3)
check(state(h) == ("film", "portrait"), "standing up from it: Portrait again")
no_errors(w, "vehicle")

# ---- a teleport: the same shot, a fresh frame -------------------------------------------------------------------------
n0 = len(h.cam.get("log", []))
ana.teleport((60, 60, 21), region="Elsewhere"); w.run(1)
check(state(h) == ("film", "portrait") and not h.cam.get("active"), "teleport: the camera waits for the place to load")
w.run(3)
check(h.cam.get("active") and len(h.cam["log"]) > n0 and B.llVecDist(h.cam["pos"], ana.pos) < 6, "teleport: a fresh frame there")
no_errors(w, "teleport")

# ---- idle: Scenic by itself, and back ---------------------------------------------------------------------------------
ana.say(12, "idle 5"); w.run(1)
w.run(301)
check(state(h) == ("film", "scenic") and var(h, "core", "gWhy") == "idle", "5 min still: Scenic starts by itself (%r)" % (state(h),))
ana.keys(C["CONTROL_FWD"]); w.run(3)
check(state(h) == ("film", "portrait"), "a key: back to Portrait (%r)" % (state(h),))
ana.away = True; w.run(2)
check(state(h)[1] == "scenic", "Away: Scenic")
ana.away = False; ana.typing = True; w.run(2)
check(state(h)[1] == "portrait", "typing: back")
ana.typing = False
no_errors(w, "idle")

# ---- the jump-cut rule, and /12 blend -------------------------------------------------------------------------------------
w.run(3)
h.send(7310, "%s|%s|auto" % (V(B.add(h.cam["pos"], vec(0.1, 0.1, 0))), V(h.cam["focus"])))
w.run(0.5)
check(h.cam.get("plag") == 1.0 and h.cam.get("by") == "core", "a nearly identical automatic cut glides (1 s)")
ana.say(12, "blend on"); w.run(1)
check(lsd(h, "blend") == "1", "/12 blend on")
ana.touch("t12 s1"); w.run(2)
check(h.cam.get("plag") == 1.5, "blend: a cut is a 1.5 s glide")
no_errors(w, "blend")
done("shots_emu")
