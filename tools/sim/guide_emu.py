"""The guide card (8.8.0), on the REAL scripts: one picture of the strip with a numbered line for each key, on its own
part (t12 guide) in the screen's middle. It shows at the end of the setup (in place of the three tour pages), from
Help › Guide and from /12 guide; a tap on it closes it, as do hiding the strip and everything off. Without its texture
the setup keeps its three pages and Help › Guide gives the Read Me. Its UUID survives Reset › Everything and a new
owner (kept in the part's own description: the root's 127 characters hold the other two)."""
from emu_util import *

W_PX = 960.0 / 1080.0


def card(h, ana):
    """the card on screen: (x, z, width, height, alpha), or None when parked"""
    r = rect(h, ana, "t12 guide")
    return r if r[4] > 0.5 and r[2] > 0.02 else None


def help_guide(ana, w):
    ana.tap(); w.run(0.6)
    ana.click("Help"); w.run(0.5)
    ana.click("Guide"); w.run(0.5)


# ---- the setup ends on the card --------------------------------------------------------------------------------------
w = World()
ana = w.avatar("Ana", (128, 128, 21))
h = ana.wear(HUD_SCRIPTS, lsd={"cin.owner": (str(ana.key), PASS)})
h.inventory["Take 12 - Read Me"] = ("notecard", new_key(), True)
w.run(2)
textures(h)
h.drop("take12_guide_1024"); w.run(3)
check("take12_guide_1024" not in h.inventory and lsd(h, "take12_guide") != "", "the card's texture is adopted (%r)" % lsd(h, "take12_guide"))
check(str(lsd(h, "take12_guide")) in h.part("t12 guide")["desc"], "its UUID is kept in the part's description (%r)" % h.part("t12 guide")["desc"])
check(h.prims[0]["desc"].count("take12_") == 2, "the root's description keeps the other two (%r)" % h.prims[0]["desc"])
check(card(h, ana) is None, "no card before the setup")
ana.tap(); w.run(0.6)
ana.click("Start"); w.run(0.5)
ana.click("Skip"); w.run(0.5)                                        # the lens: as it is; the eye line next
ana.tap(); w.run(0.6)                                                # the eye line kept
ana.click("Good"); w.run(0.5)
ana.click("Yes"); w.run(1)
c = card(h, ana)
check(c is not None, "the setup ends on the guide card")
check(ana.dialog is None, "no tour pages: the card says it (%r)" % (ana.labels(),))
if c:
    check(abs(c[0]) < 1e-3 and abs(c[1]) < 1e-3, "the card sits in the screen's middle (%.3f, %.3f)" % (c[0], c[1]))
    check(abs(c[2] - W_PX) < 2e-3 and abs(c[3] - W_PX / 2) < 2e-3, "960 x 480 px at M (%.0f x %.0f)" % (c[2] * 1080, c[3] * 1080))
    check(str(h.part("t12 guide")["tex"][0]) == str(lsd(h, "take12_guide")), "on its texture")
check(lsd(h, "firstrun") == "done" and var(h, "screen", "gOpen") == 1, "the setup is done, the strip open")
w.run(3)
check(var(h, "tracking", "gAuto") == 1, "and Auto directs, the card on screen")
ana.touch("t12 guide"); w.run(0.5)
check(card(h, ana) is None, "a tap on the card closes it")
check(ana.dialog is None and var(h, "screen", "gOpen") == 1, "... and nothing else: no dialog, the strip stays")

# ---- Help › Guide, /12 guide, and what closes it ---------------------------------------------------------------------
help_guide(ana, w)
check(card(h, ana) is not None, "Help › Guide shows the card")
check(not any(g[1] == ana.key and "Read Me" in str(g) for g in w.given if g[0] == str(ana.key)), "... not the notecard")
ana.double_tap(); w.run(1)
check(card(h, ana) is None and var(h, "screen", "gOpen") == 0, "hiding the strip closes the card")
ana.say(12, "guide"); w.run(1)
check(card(h, ana) is not None and var(h, "screen", "gOpen") == 1, "/12 guide: the card, and the strip it explains")
ana.long_press(); w.run(2)
check(card(h, ana) is None, "everything off: the card goes too")
ana.long_press(); w.run(2)
check(card(h, ana) is None, "back on: the card stays closed")
ana.tap(); w.run(0.6); ana.click("Help"); w.run(0.5); ana.click("About"); w.run(0.5)
check("Read Me" in ana.labels() and "Guide" not in ana.labels(), "About gives the Read Me by its name (%r)" % ana.labels())
n0 = len(w.given)
ana.click("Read Me"); w.run(0.5)
check(len(w.given) == n0 + 1 and "Read Me" in str(w.given[-1]), "About › Read Me: the notecard (%r)" % (w.given[-1:],))

# ---- a narrow window, size L ---------------------------------------------------------------------------------------
ana.aspect = 1.25
ana.say(12, "size l"); w.run(3)
ana.say(12, "guide"); w.run(1)
c = card(h, ana)
check(c is not None and c[2] <= 1.25 * 0.94 + 1e-4 and abs(c[3] - c[2] / 2) < 1e-4, "a 5:4 window at L: the card within the window, 2:1 (%r)" % (c,))
ana.touch("t12 guide"); w.run(0.5)
ana.aspect = 1.778
ana.say(12, "size m"); w.run(3)

# ---- it stays through Reset › Everything and a new owner ---------------------------------------------------------------
g = lsd(h, "take12_guide")
h.llLinksetDataReset(h.scripts[0]); h.send(7330, "all"); w.run(3)
check(lsd(h, "take12_guide") == g, "after Reset › Everything the card's UUID is written again (%r)" % lsd(h, "take12_guide"))
for sc in h.live(): h.reset(sc)
w.run(6)
check(var(h, "screen", "gTG") == g, "a script reset: the card's texture is still known")
ben = w.avatar("Ben", (140, 128, 21))
ana.take_off(h); w.run(1)
h.owner, h.owner_name = ben, "Ben"
ben.huds.append(h)
h.lsd = {}
h.attach(); w.run(8)
check(lsd(h, "take12_guide") == g and var(h, "screen", "gTG") == g, "a new owner: the card comes from the part's description")
no_errors(w, "guide")

# ---- without its texture: the three pages, and Help › Guide gives the Read Me --------------------------------------------
w = World()
ana = w.avatar("Ana", (128, 128, 21))
h = ana.wear(HUD_SCRIPTS, lsd={"cin.owner": (str(ana.key), PASS)})
h.inventory["Take 12 - Read Me"] = ("notecard", new_key(), True)
w.run(2)
textures(h); w.run(2)
ana.tap(); w.run(0.6)
ana.click("Start"); w.run(0.5)
ana.click("Skip"); w.run(0.5)
ana.tap(); w.run(0.6)
ana.click("Good"); w.run(0.5)
ana.click("Yes"); w.run(1)
check(ana.dialog is not None and "Next ›" in ana.labels(), "no card's texture: the tour's pages, as before (%r)" % ana.labels())
for b in ("Next ›", "Next ›", "Done"): ana.click(b); w.run(0.5)
check(card(h, ana) is None, "no card")
n0 = len(w.given)
help_guide(ana, w)
check(len(w.given) == n0 + 1 and "Read Me" in str(w.given[-1]), "Help › Guide gives the Read Me (%r)" % (w.given[-1:],))
no_errors(w, "guide, no texture")
done("guide_emu")
