"""The HUD builder (8.0), on the REAL script: a rezzed box with hud/build/builder.lsl and a blank "t12 part" in its
contents; a touch makes the 27 parts (rezzed, linked, named, laid flat), names the root "Take 12", then takes the part
and itself out of the contents; touched again on a HUD that misses parts, it adds only those. The result, worn with
the twelve scripts, is found by screen and strip and lays out."""
from emu_util import *
from world import Obj, new_key, PARTS

w = World()
ana = w.avatar("Ana", (128, 128, 21))
box = Obj(w, ana, [BUILDER], children=(), rezzed=True)
box.name = "Object"
box.prims[0]["name"] = "Object"
box.pos = vec(129, 128, 20.5)
w.objects[box.key] = box
box.rez(); w.run(1)
check(any("t12 part" in c[2] for c in ana.chat), "it says what to put in it")
ana.touch(o=box); w.run(1)
check(any("Put a blank box" in c[2] for c in ana.chat), "no part yet: it says so")
box.inventory["t12 part"] = ("object", new_key(), True)
ana.touch(o=box); w.run(40)
names = [p["name"] for p in box.prims]
check(names[0] == "Take 12", "the root is Take 12 (%r)" % names[0])
check(sorted(names[1:]) == sorted(PARTS) and len(names) == 28, "the 27 parts, each named once (%d)" % len(names))
check(all(p["size"][1] <= 0.0101 and p["alpha"] == 0.0 for p in box.prims[1:]), "the parts lie flat and hidden inside the root")
check("t12 part" not in box.inventory and box.scripts[0].dead, "the builder takes the part and itself out")
check(any("Built: 28 parts" in c[2] for c in ana.chat), "Built.")
no_errors(w, "build")
# a HUD that misses parts: only those are added
box.prims = [p for p in box.prims if p["name"] not in ("t12 o5", "t12 bar3")]
fix = Obj(w, ana, [BUILDER], children=(), rezzed=True)
fix.prims = box.prims
fix.inventory["t12 part"] = ("object", new_key(), True)
w.objects[fix.key] = fix
fix.rez(); w.run(1)
ana.touch(o=fix); w.run(10)
check(sorted(p["name"] for p in fix.prims[1:]) == sorted(PARTS), "the missing parts are added, nothing doubled")
no_errors(w, "repair")
# worn with the scripts: screen finds every part
order = [p["name"] for p in box.prims[1:]]
h = ana.wear(HUD_SCRIPTS, parts=order, lsd=ready(ana))
w.run(5)
check(var(h, "strip", "gFound") == 1, "strip finds the parts")
ana.double_tap(); w.run(1)
check(len(visible(h, ana)) >= 6, "the strip opens on the built HUD")
no_errors(w, "worn")
done("builder_emu")
