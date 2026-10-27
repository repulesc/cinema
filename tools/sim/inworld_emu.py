"""What the first in-world test of 8.0.2 ran into, on the REAL scripts (8.0.3):
- a tap on the [12] landed on its ring (in front of the disc) or on a part parked behind it, and was lost: you had to tap
  again and again;
- the eye-line check (the setup) held the camera in front of you: walking, a teleport and a script reset left it there.
Now every tap on the [12] counts, walking or a teleport ends the eye line (the old line is kept), it ends by itself
after 2 minutes, a reset never leaves the camera locked, and a dialog answered late still works."""
from emu_util import *

w = World()
ana = w.avatar("Ana", (128, 128, 21))
h = ana.wear(HUD_SCRIPTS)
w.run(5)

# ---- every tap on the [12] counts ----------------------------------------------------------------------------------
for part in ("t12 ring", "t12 dot", "t12 s0", "t12 band", "t12 bar0"):
    ana.dialog = None
    ana.touch(part); w.run(0.8)
    check(ana.dialog is not None, "a tap on the [12] that lands on %s opens the dialog" % part)
    if ana.dialog and ana.labels() == ["Start", "Later"]: ana.click("Later"); w.run(0.5)
ana.dialog = None
ana.touch("t12 ring"); w.run(0.1); ana.touch("t12 s1"); w.run(0.6)
check(var(h, "strip", "gOpen") == 1, "a double-tap across the ring and a parked part opens the strip")
ana.touch("t12 s1"); w.run(0.6)
check(var(h, "strip", "gOpen") == 1 and ana.dialog is None, "an open strip's word is the word, not the [12]")
check(var(h, "core", "gShot") == "portrait", "... it starts Portrait")
h.send(7371, "stop"); w.run(0.5)                                       # back to your own camera for what follows
ana.double_tap(); w.run(0.6)
check(var(h, "strip", "gOpen") == 0, "the strip closes")
no_errors(w, "taps")


def eye_line():
    ana.dialog = None
    ana.tap(); w.run(0.6)
    if ana.labels() == ["Start", "Later"]:
        ana.click("Start"); w.run(0.5)
        ana.click("Skip"); w.run(0.5)
    else:
        ana.click("Settings"); w.run(0.5)
        ana.click("Eye line"); w.run(0.5)
    cam, foc, scripted = ana.camera()
    check(scripted and var(h, "core", "gEyeOn"), "the eye line holds the camera in front of you")


def free(why):
    cam, foc, scripted = ana.camera()
    check(not scripted, "%s: your camera again, not locked" % why)
    check(not var(h, "core", "gEyeOn") and not var(h, "ui", "gEye"), "%s: the eye line has ended" % why)
    check(rect(h, ana, "t12 u2")[4] < 0.02 or var(h, "strip", "gOpen"), "%s: the line is off the screen" % why)


# ---- walking ends the eye line (the setup goes on) ------------------------------------------------------------------
eye0 = lsd(h, "eye")
eye_line()
ana.keys(C["CONTROL_FWD"], hold=0.5); w.run(1.0)
free("walking")
check(lsd(h, "eye") == eye0, "walking: the old eye line is kept")
check(ana.labels() == ["Smaller", "Good", "Larger"], "walking: the setup goes on to the size: %r" % ana.labels())
ana.click("Good"); w.run(0.5)
for p in ("Next ›", "Next ›", "Done"): ana.click(p); w.run(0.5)
check(lsd(h, "firstrun") == "done", "the setup is done")

# ---- turning (the arrow keys) ends it too; a teleport; 2 minutes --------------------------------------------------------
eye_line()
ana.keys(C["CONTROL_ROT_LEFT"], hold=0.3); w.run(0.6)
free("turning")
eye_line()
ana.teleport((60, 60, 30), region="Elsewhere"); w.run(3)
free("a teleport")
eye_line()
w.run(119)
check(ana.camera()[2], "the eye line waits while you look")
w.run(3)
free("two minutes")
eye_line()
ana.keys(C["CONTROL_UP"], hold=0.3); w.run(0.5)
check(var(h, "core", "gEyeOn"), "PgUp moves the line, it does not end it")
ana.tap(); w.run(0.6)
free("kept with a tap")
no_errors(w, "eye line")

# ---- a script reset never leaves the camera locked ------------------------------------------------------------------
eye_line()
for sc in h.scripts:
    if sc.name in ("core", "ui"): h.reset(sc)
w.run(3)
check(not ana.camera()[2], "core and ui reset during the eye line: the camera is yours again")
no_errors(w, "reset")

# ---- a dialog answered late still works -----------------------------------------------------------------------------
ana.dialog = None
ana.tap(); w.run(0.6)
w.run(300)
ana.click("Settings"); w.run(0.5)
check("Eye line" in ana.labels(), "a dialog answered after 5 minutes: %r" % ana.labels())
no_errors(w, "late")
done("inworld_emu")
