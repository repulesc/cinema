"""The free Take 12 Scenery on its own (8.5.8), on the REAL nine scripts of scenery/src: its menus, its strip, its one shot.
Connect (watching, never filming for others) is in connect_emu, carry-over in carry_emu, feedback in feedback_emu."""
from emu_util import *

w = World()
ana, h = hud(w, scripts=FREE_SCRIPTS)
textures(h)
w.run(2)

# ---- Settings: no Eye line (Portrait's), no Vehicles (Fixed's); Frames & bars there (8.0.6-8.5.7 hid it by mistake) ------
ana.tap(); w.run(1)
check(sorted(ana.labels()) == sorted(["Connect", "Settings", "Help", "Feedback", "Close"]), "the main menu: %r" % ana.labels())
ana.click("Settings"); w.run(1)
L = ana.labels()
check("Frames & bars" in L and "Eye line" not in L and "Vehicles" not in L, "Settings: Frames & bars, no Eye line, no Vehicles (%r)" % L)
check(all(b in L for b in ("Lens", "Motion", "Idle start", "Friends", "Look", "Reset", "‹ Back")), "... and the rest (%r)" % L)
ana.click("Frames & bars"); w.run(1)
check(ana.dialog is not None and "Film" in ana.labels(), "Frames & bars opens (%r)" % ana.labels())
ana.dialog = None

# ---- the strip: the four shots, three dim; a dim one only says where it is -----------------------------------------------
ana.double_tap(); w.run(1)
V = visible(h, ana)
check(all(k in V for k in ("t12 s0", "t12 s1", "t12 s2", "t12 s3")), "the four shots on the strip (%r)" % sorted(V))
alpha = lambda n: h.part(n)["alpha"]
check(all(alpha("t12 s%d" % i) < 0.3 for i in range(3)) and alpha("t12 s3") > 0.4, "Tracking, Portrait, Fixed dim; Scenic not (%s)" % [round(alpha("t12 s%d" % i), 2) for i in range(4)])
for i in range(3):
    t = w.t
    ana.touch("t12 s%d" % i); w.run(2)
    check(var(h, "core", "gState") != "film" and any("full Take 12" in n for n in ana.notes(t)), "a tap on dim t12 s%d: \"In the full Take 12.\", nothing starts" % i)
t = w.t
ana.touch("t12 auto"); w.run(2)
check(any("full Take 12" in n for n in ana.notes(t)) and var(h, "strip", "gAuto") == 0, "the Orbit: the same note, no Auto")

# ---- Scenic runs ---------------------------------------------------------------------------------------------------------
ana.touch("t12 s3"); w.run(4)
check(var(h, "core", "gState") == "film" and var(h, "core", "gShot") == "scenic", "Scenic films (%s %s)" % (var(h, "core", "gState"), var(h, "core", "gShot")))
check(len([k for k in visible(h, ana) if k.startswith("t12 o")]) == 4, "its four options (Drift, Near, Room, Far)")
w.run(40)
no_errors(w, "free")
done("free_emu")
