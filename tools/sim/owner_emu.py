"""A new owner gets a new Take 12 (8.0.10), on the REAL scripts: Ana sets her copy up (lens, eye line, the strip at
the bottom and large, frames, friends, seats and views, a vehicle, tips seen), then the same object goes to Ben. On his
first wear nothing of hers is left: only the copy's owner and version in Linkset Data, the setup note, the strip at
the top in size M, the cinema frames, no friend, seat or view of hers, no text of hers on screen.
The scripts start in any order in Second Life: here ui starts last, after the others have read the settings."""
from emu_util import *
import os

ORDER = [p for p in HUD_SCRIPTS if not p.endswith("ui.lsl")] + [p for p in HUD_SCRIPTS if p.endswith("ui.lsl")]

w = World()
ana = w.avatar("Ana", (128, 128, 21))
h = ana.wear(ORDER, lsd=ready(ana))
w.run(5)
for k, v in {"place": "bot", "size": "l", "lens": "50", "eye": "1.12", "feel": "smooth", "shape.portrait": "4:5",
             "shape.tracking": "full", "bars": "0", "bstyle": "dim", "friends": "k1,k2", "veh": "Boat|creator",
             "seat.obj1.a": "<1,2,3>", "view.reg.par.A": "<1,2,3>", "tips.link": "3", "chime": "0", "idle": "off",
             "open": "1", "scn": "2", "trk": "1"}.items():
    h.lsd["cin." + k] = (v, PASS)
h.send(7330, "all"); w.run(2)
ana.double_tap(); w.run(1); ana.touch("t12 s1"); w.run(3)
check(var(h, "screen", "gPlace") != 0 and lsd(h, "place") == "bot", "Ana's copy: her setup (the strip at the bottom)")

# ---- the same object goes to Ben ---------------------------------------------------------------------------------
ana.take_off(h); w.run(1)
ben = w.avatar("Ben", (140, 128, 21))
h.owner, h.owner_name = ben, "Ben"
ben.huds.append(h)
t = w.t
h.attach(); w.run(8)
left = sorted(k for k in h.lsd if k not in ("cin.owner", "cin.ver"))
check(lsd(h, "owner") == str(ben.key), "the copy knows Ben as its owner")
check(left == [] or all(not any(x in k for x in ("place", "size", "lens", "eye", "shape", "friends", "veh", "seat", "view", "tips", "chime", "idle", "feel", "scn", "trk", "bars", "bstyle")) for k in left),
      "nothing of Ana's in Linkset Data (%r)" % left)
check(var(h, "screen", "gPlace") == 0, "the strip at the top (%r)" % var(h, "screen", "gPlace"))
check(abs(var(h, "strip", "gS") - var(h, "strip", "SIZES")[1]) < 1e-6, "... in size M (%r)" % var(h, "strip", "gS"))
check(var(h, "bars", "gOn") == 1 and var(h, "bars", "gDim") == 1.0, "the bars on and black")
check(var(h, "ui", "gFirst") == "start" and any("set up" in n for n in ben.notes(t)), "the setup note: %r" % ben.notes(t))
check(var(h, "strip", "gOpen") == 0, "the strip closed until the setup")
# friends, seats, views and vehicles are read from Linkset Data each time: the check above covers them
check(not any("Ana" in m for (_, _, m) in ben.chat), "no word of Ana in Ben's chat")
no_errors(w, "new owner")
done("owner_emu")
