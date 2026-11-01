"""The HUD builder (8.0), on the REAL script: a rezzed box with hud/build/builder.lsl and a blank "t12 part" in its
contents; a touch makes the 29 parts (rezzed, linked, named, laid flat), names the root "Take 12", then takes the part
and itself out of the contents; touched again on a HUD that misses parts, it adds only those. The result, worn with
the twelve scripts, is found by screen and strip and lays out."""
from emu_util import *
from world import Obj, new_key, PARTS, LAB_PARTS, LAB_SCRIPTS
import os

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
check(sorted(names[1:]) == sorted(PARTS) and len(names) == len(PARTS) + 1, "the %d parts, each named once (%d)" % (len(PARTS), len(names)))
check(all(p["size"][1] <= 0.0101 and p["alpha"] == 0.0 for p in box.prims[1:]), "the parts lie flat and hidden inside the root")
check("t12 part" not in box.inventory and box.scripts[0].dead, "the builder takes the part and itself out")
check(any("Built: %d parts" % (len(PARTS) + 1) in c[2] for c in ana.chat), "Built.")
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
w.run(0.5); manual(h); w.run(4.5)
check(var(h, "strip", "gFound") == 1, "strip finds the parts")
ana.double_tap(); w.run(1)
check(len(visible(h, ana)) >= 6, "the strip opens on the built HUD")
no_errors(w, "worn")

# the lab's builder (8.10.0) on a lab HUD built before the x: it adds t12 free, and nothing else; worn, the x is there
LAB_BUILDER = os.path.join(os.path.dirname(BUILDER), "..", "..", "lab", "build", "builder.lsl")
w = World()
bo = w.avatar("Bo", (128, 128, 21))
old = Obj(w, bo, [LAB_BUILDER], children=(), rezzed=True)
old.prims = [old.prims[0]] + [dict(old.prims[0], name=n, key=new_key()) for n in LAB_PARTS if n != "t12 free"]
old.prims[0]["name"] = "Take 12"
old.inventory["t12 part"] = ("object", new_key(), True)
w.objects[old.key] = old
old.rez(); w.run(1)
bo.touch(o=old); w.run(10)
names = [p["name"] for p in old.prims[1:]]
check(sorted(names) == sorted(LAB_PARTS) and names.count("t12 free") == 1, "the lab's builder on a lab HUD before 8.10.0: it adds the x, nothing doubled")
h = bo.wear(LAB_SCRIPTS, parts=names, lsd=ready(bo))
w.run(0.5); manual(h); w.run(4.5)
bo.double_tap(); w.run(1); bo.say(12, "tracking"); w.run(3)
check(rect(h, bo, "t12 free")[4] > 0.3, "... worn: the x on the island")
no_errors(w, "lab repair")
done("builder_emu")
