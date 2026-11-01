"""The strip's two textures stay what you last dropped in (8.4.2), on the REAL scripts. In-world a new take12_marks was
dropped in and the Orbit showed; after a reset it was gone again until the texture was dropped in once more. The UUIDs
were kept only in the root's description, which the viewer's Edit window can put back as it was (the old marks, which
have no Orbit). Now screen keeps them in Linkset Data, and the description is a copy for a new owner.
Checked: a new marks texture survives the description being put back, a script reset, wearing it again, Settings ›
Reset › Everything and a new owner; a description with words of its own never cuts a UUID (127 characters)."""
from emu_util import *

w = World()
ana, h = hud(w)
textures(h); w.run(2)
ana.double_tap(); w.run(2)
old_desc = h.prims[0]["desc"]
old_m = h.prims[0]["tex"][0]


def marks(where, want):
    """the [12] and the Orbit both show the marks texture `want`"""
    check(str(h.prims[0]["tex"][0]) == str(want), "%s: the [12] on the marks %s (%s)" % (where, want, h.prims[0]["tex"][0]))
    check(str(h.part("t12 auto")["tex"][0]) == str(want), "%s: the Orbit on the marks %s (%s)" % (where, want, h.part("t12 auto")["tex"][0]))


def reset_all():
    for sc in h.live(): h.reset(sc)
    w.run(6)


# the new marks, dropped in
h.drop("take12_marks_1024"); w.run(3)
new_m = h.prims[0]["tex"][0]
check(str(new_m) != str(old_m), "the new marks are used at once")
marks("dropped in", new_m)
check("take12_marks_1024" not in h.inventory, "the texture leaves the contents")
check(lsd(h, "take12_marks") == str(new_m), "its UUID is kept in Linkset Data (%r)" % lsd(h, "take12_marks"))

# the viewer's Edit window puts the old description back, then the scripts are reset (the in-world report)
h.prims[0]["desc"] = old_desc
reset_all()
marks("the description put back, then a reset", new_m)
check(str(new_m) in h.prims[0]["desc"], "the description is mended: %r" % h.prims[0]["desc"])

# taken off and worn again
h.prims[0]["desc"] = old_desc
h.detach(); w.run(1); h.attach(); w.run(6); ana.double_tap(); w.run(2)
marks("worn again", new_m)

# Settings › Reset › Everything (ui empties Linkset Data and tells everyone)
h.prims[0]["desc"] = old_desc
h.llLinksetDataReset(h.scripts[0]); h.send(7330, "all"); w.run(3)
marks("after Reset › Everything", new_m)
check(lsd(h, "take12_marks") == str(new_m) and lsd(h, "take12_words") != "", "the UUIDs are written again (%r)" % sorted(h.lsd))
reset_all()
marks("Reset › Everything, then a reset", new_m)

# a new owner: Linkset Data starts empty, the description carries the textures
ben = w.avatar("Ben", (140, 128, 21))
ana.take_off(h); w.run(1)
h.owner, h.owner_name = ben, "Ben"
ben.huds.append(h)
h.lsd = {}
h.attach(); w.run(8)
marks("a new owner", new_m)

# 8.8.2: a working HUD given away as it is in-world: its Linkset Data goes with it (the last owner's settings and the
# HUD's own texture UUIDs), and the description a script set while it was worn was never saved (empty here). Every
# script starts again for the new owner, in any order. The textures stay: the new owner's wipe keeps cin.take12_*
import random
for order in range(4):
    cy = w.avatar("Cy%d" % order, (150 + order, 128, 21))
    owner = h.owner
    owner.take_off(h); w.run(1)
    h.owner, h.owner_name = cy, cy.name
    cy.huds.append(h)
    h.prims[0]["desc"] = ""
    live = list(h.live()); random.Random(order).shuffle(live)
    for sc in live: h.reset(sc)
    h.attach(); w.run(8)
    marks("given away (order %d), its description unsaved" % order, new_m)
    check(lsd(h, "owner") == str(cy.key) and not lsd(h, "firstrun"), "... the last owner's settings gone, the setup again")

# a description with words of its own: the two UUIDs are never cut at 127 characters
h.prims[0]["desc"] = "My camera, built on a Sunday afternoon at the beach, with love and a lot of coffee"
h.drop("take12_words_1024"); w.run(3)
d = h.prims[0]["desc"]
check(len(d) <= 127 and d.count("take12_") == 2 and str(new_m) in d, "the description holds both UUIDs whole: %r" % d)
no_errors(w, "textures")
done("textures_emu")
