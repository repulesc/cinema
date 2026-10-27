"""Two copies worn by the same owner (8.0), on the REAL scripts: a new copy worn while the old one is on takes the
setup over (settings, seats, views: every cin.* value, long ones in parts) and says "Moved. You can take off the old
one."; the older copy steps aside (lets go of the camera, ends its Connect, amber, "An older Take 12 is worn too");
two set-up copies: the older steps aside, nothing is copied; the free Take 12 Scenery always gives way to the full one;
nothing crosses to another owner."""
from emu_util import *

w = World()
ana = w.avatar("Ana", (128, 128, 21))
old = ana.wear(HUD_SCRIPTS, lsd=ready(ana))
w.run(5)
old.lsd["cin.lens"] = ("40", PASS)
old.lsd["cin.trk"] = ("0|0", PASS)
old.lsd["cin.seats"] = (",".join("%08x-0000-4000-8000-000000000000" % i for i in range(48)), PASS)   # a long value
old.lsd["cin.view.Lab.1234abcd"] = ("<1.00,2.00,3.00>|<4.00,5.00,6.00>|<1.00,1.00,1.00>|90|1.047~", PASS)
ana.say(12, "portrait"); w.run(3)
check(state(old) == ("film", "portrait"), "the old copy films")
t = w.t
new = ana.wear(HUD_SCRIPTS)                                         # a new copy, never set up
w.run(25)
check(var(old, "core", "gStandby") == 1 and state(old)[0] == "wait", "the older copy steps aside")
check(var(old, "screen", "gProblem") == 1, "its [12] is amber")
check(any("An older Take 12 is worn too" in c[2] for c in ana.chat), "it says so (in chat too)")
for k in ("cin.lens", "cin.trk", "cin.seats", "cin.view.Lab.1234abcd", "cin.firstrun"):
    check(lsd(new, k[4:]) == lsd(old, k[4:]), "%s carried over (%r)" % (k, lsd(new, k[4:])[:40]))
check(lsd(new, "owner") == str(ana.key) and "cin.peers" not in new.lsd, "the copy's own values stay its own")
check(any("Moved. You can take off the old one." in c[2] for c in ana.chat), "Moved.")
check(var(new, "core", "gStandby") == 0 and var(new, "screen", "gProblem") == 0, "the new copy is in use")
ana.say(12, "tracking"); w.run(3)
check(state(new) == ("film", "tracking") and state(old)[0] == "wait", "only the new copy takes the camera")
check(var(new, "tracking", "gLook") == 0, "with the old copy's options (Shoulder)")
no_errors(w, "carry-over")

# ---- two set-up copies: the older (first worn) steps aside, nothing copied ------------------------------------------------
w2 = World()
ben = w2.avatar("Ben", (128, 128, 21))
a = ben.wear(HUD_SCRIPTS, lsd=ready(ben)); w2.run(3)
a.lsd["cin.lens"] = ("35", PASS)
b = ben.wear(HUD_SCRIPTS, lsd=dict(ready(ben), **{"cin.lens": ("40", PASS)})); w2.run(10)
check(var(a, "core", "gStandby") == 1 and var(b, "core", "gStandby") == 0, "the first worn steps aside")
check(lsd(b, "lens") == "40", "a set-up copy keeps its own setup")
no_errors(w2, "two set up")

# ---- the free build gives way to the full one, whichever was worn first -----------------------------------------------------
w3 = World()
cy = w3.avatar("Cy", (128, 128, 21))
full = cy.wear(HUD_SCRIPTS, lsd=ready(cy)); w3.run(3)
free = cy.wear(FREE_SCRIPTS, lsd=ready(cy)); w3.run(10)
check(var(free, "core", "gStandby") == 1 and var(full, "core", "gStandby") == 0, "the free Take 12 Scenery steps aside for the full one")
no_errors(w3, "free")

# ---- another owner's copy is never involved -------------------------------------------------------------------------------
w4 = World()
d1 = w4.avatar("Dee", (128, 128, 21)); e1 = w4.avatar("Eve", (129, 128, 21))
hd = d1.wear(HUD_SCRIPTS, lsd=ready(d1)); he = e1.wear(HUD_SCRIPTS, lsd=ready(e1)); w4.run(10)
check(var(hd, "core", "gStandby") == 0 and var(he, "core", "gStandby") == 0, "two people, one copy each: nobody steps aside")
no_errors(w4, "owners")
done("carry_emu")
