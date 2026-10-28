"""The box (8.2.0; worn, 8.4.0), on the REAL script. Worn (Add or Wear, the classic way): a card on the screen, one
folder "Take 12 <version>" (the HUD, the Read Me, a Take 12 Scenery to give, never the script or the textures), the
note, and it takes itself off; worn again, a fresh copy. Rezzed (a store display): with its three textures dropped
in, it shapes itself (0.45 x 0.25 x 0.45 m, the name, the faces); touched by its owner, the same folder; nobody else
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
U = {}
for f in ("take12_box_front", "take12_box_side", "take12_box_top"):
    box.inventory[f] = ("texture", new_key(), True)
    U[f] = str(box.inventory[f][1])
for sc in box.live(): box.event(sc, "changed", (C["CHANGED_INVENTORY"],))
w.run(1)
check(not any(f in box.inventory for f in U), "the textures are adopted: taken out of the contents (%r)" % sorted(box.inventory))
check(all(f[12] + " " + u in box.prims[0]["desc"] for f, u in U.items()) and len(box.prims[0]["desc"]) <= 127,
      "... all three UUIDs kept in the description, which holds 127 characters (%r)" % box.prims[0]["desc"])
check(box.prims[0].get("full") is True or box.prims[0].get("full") == 1, "... full bright (%r)" % box.prims[0].get("full"))
check(box.prims[0]["name"] == "Take 12 - Cinematic Camera HUD" and tuple(round(v, 2) for v in box.prims[0]["size"]) == (0.45, 0.25, 0.45),
      "the textures in: the box shapes itself (%r, %r)" % (box.prims[0]["name"], box.prims[0]["size"]))
check(str(box.prims[0]["tex"][0]) == U["take12_box_top"], "... textured by UUID, the lid last (%r)" % (box.prims[0]["tex"],))
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

# ---- the box you wear ----------------------------------------------------------------------------------------------------
w = World()
cat = w.avatar("Cat", (128, 128, 21))
def worn_box():
    o = Obj(w, cat, [BOX], children=(), point=C["ATTACH_HUD_CENTER_2"])
    for f in ("take12_box_front", "take12_box_side", "take12_box_top"): o.inventory[f] = ("texture", new_key(), True)
    for n, t in (("Take 12", "object"), ("Take 12 - Read Me", "notecard"), ("Take 12 Scenery (to give a friend)", "object")):
        o.inventory[n] = (t, new_key(), True)
    w.objects[o.key] = o
    cat.huds.append(o)
    o.attach()
    return o
b = worn_box(); w.run(0.01)
check(not any(k.startswith("take12_box") for k in b.inventory), "worn: no textures left in the contents")
check(b.prims[0].get("full") in (True, 1), "worn: full bright")
check(tuple(round(v, 2) for v in b.prims[0]["size"]) == (0.02, 0.22, 0.22) and str(b.prims[0]["tex"][0]) in b.prims[0]["desc"],
      "worn: a card on the screen, the board (%r)" % (b.prims[0]["size"],))
w.run(1)
check(len(w.given) == 1 and w.given[0][0] == str(cat.key) and w.given[0][1] == "Take 12 " + VER, "worn: one folder to the wearer %r" % w.given)
check(sorted(w.given[0][2]) == sorted(["Take 12", "Take 12 - Read Me", "Take 12 Scenery (to give a friend)"]), "... never the script or the textures")
check(any("in your inventory" in c[2] for c in cat.chat), "it says where")
check(not b.worn and b not in cat.huds, "then it takes itself off")
b = worn_box(); w.run(1)
check(len(w.given) == 2 and not b.worn, "worn again: a fresh copy, and off again")
b.pos = vec(130, 128, 20.5); w.objects[b.key] = b; b.rez(); w.run(0.5)
check(tuple(round(v, 2) for v in b.prims[0]["size"]) == (0.45, 0.25, 0.45), "the same box rezzed: the black box again (a display)")
no_errors(w, "worn")
done("box_emu")
