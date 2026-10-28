"""The box (8.2.0), on the REAL script: with its three textures dropped in, it shapes itself (0.45 x 0.25 x 0.45 m,
the name, the faces); touched by its owner, everything in it but the script and the textures goes to them in one
folder, "Take 12 <version>" (the HUD, the Read Me, a Take 12 Scenery to give); again on every touch; nobody else
can unpack it; an empty box gives nothing."""
from emu_util import *
from world import Obj, new_key
import os, re

BOX = os.path.join(os.path.dirname(__file__), "..", "..", "hud", "box", "unpack.lsl")
VER = re.search(r'string VERSION = "([^"]+)"', open(BOX).read()).group(1)
w = World()
ana = w.avatar("Ana", (128, 128, 21))
ben = w.avatar("Ben", (129, 128, 21))
box = Obj(w, ana, [BOX], children=(), rezzed=True)
box.pos = vec(129, 128, 20.5)
w.objects[box.key] = box
box.rez(); w.run(1)
ana.touch(o=box); w.run(1)
check(w.given == [], "an empty box gives nothing")
for f in ("take12_box_front", "take12_box_side", "take12_box_top"):
    box.inventory[f] = ("texture", new_key(), True)
for sc in box.live(): box.event(sc, "changed", (C["CHANGED_INVENTORY"],))
w.run(1)
check(box.prims[0]["name"] == "Take 12 - Cinematic Camera HUD" and tuple(round(v, 2) for v in box.prims[0]["size"]) == (0.45, 0.25, 0.45),
      "the textures in: the box shapes itself (%r, %r)" % (box.prims[0]["name"], box.prims[0]["size"]))
check(any(str(x) in ("take12_box_front", "take12_box_side", "take12_box_top") for x in box.prims[0]["tex"]), "... textured (%r)" % (box.prims[0]["tex"],))
ana.touch(o=box); w.run(1)
check(w.given == [], "only its textures: nothing to give")
for n, t in (("Take 12", "object"), ("Take 12 - Read Me", "notecard"), ("Take 12 Scenery (to give a friend)", "object")):
    box.inventory[n] = (t, new_key(), True)
ben.touch(o=box); w.run(1)
check(w.given == [], "someone else's touch: nothing")
ana.touch(o=box); w.run(1)
check(len(w.given) == 1 and w.given[0][0] == str(ana.key) and w.given[0][1] == "Take 12 " + VER, "one folder to its owner: %r" % w.given)
check(sorted(w.given[0][2]) == sorted(["Take 12", "Take 12 - Read Me", "Take 12 Scenery (to give a friend)"]), "... the HUD, the Read Me, the Scenery to give, not the script")
check(any("in your inventory" in c[2] for c in ana.chat), "it says where")
ana.touch(o=box); w.run(1)
check(len(w.given) == 2, "again on every touch: a fresh copy")
no_errors(w, "box")
done("box_emu")
