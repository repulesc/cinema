# 7.2 on the REAL scripts (tools/emu): the keys texture dropped into the HUD is adopted (its UUID on the strip, the
# texture out of the contents) only when it is yours; Scenery has its own Format, apart from yours.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "emu"))
from world import World, HUD_SCRIPTS

ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)
def g(a, n): return next(s for s in a.hud.scripts if s.name == n).g

# ---- the keys texture, dropped in --------------------------------------------------------------------------------
w = World()
a = w.avatar("Ana", (128, 128, 22))
hud = a.wear(HUD_SCRIPTS, textures=())
w.run(3)
hud.drop("take12_keys_1024")
w.run(2)
strip = hud.prims[g(a, "keys")["gLink"] - 1]
check("take12_keys_1024" not in hud.inventory and strip["desc"].startswith("take12_keys ") and len(strip["desc"]) == 12 + 36,
      "your keys texture: its UUID on the strip (%r), out of the contents (%s)" % (strip["desc"], list(hud.inventory)))
check(any("can be given away" in c[2] for c in a.chat), "and you are told once")
a.say(77, "status"); w.run(1)
check(any("texture saved" in c[2] for c in a.chat), "/77 status: texture saved")
w2 = World()
b = w2.avatar("Ben", (128, 128, 22))
h2 = b.wear(HUD_SCRIPTS, textures=())
w2.run(3)
h2.drop("take12_keys", full=False)
w2.run(2)
check("take12_keys" in h2.inventory and not any(p["desc"] for p in h2.prims), "someone else's texture (not full permissions) is left alone")

# ---- Scenery's own Format -------------------------------------------------------------------------------------------
crop = lambda: g(a, "crop")
a.tap(); w.run(1); a.click("◰ Format"); w.run(1); a.click("4:5"); w.run(1); a.click("‹ Back"); w.run(1)
a.click("× Close") if a.dialog else None
a.tap(); w.run(1); a.click("◇ Scenery"); w.run(1); a.click("Format"); w.run(1)
check("Scenery's Format" in a.dialog[1], "Scenery > Format opens Scenery's own: %r" % a.dialog[1][:60])
a.click("2.39:1"); w.run(1); a.click("‹ Back"); w.run(1)
check(a.dialog and "Idle start" in a.labels(), "its Back goes back to Scenery: %s" % a.labels())
a.click("‹ Back"); w.run(1); a.click("× Close"); w.run(30)
eff = lambda: crop()["gRS"] if (crop()["gScen"] and not crop()["gFollow"]) else crop()["gR"]
check(abs(crop()["gR"] - 0.8) < 1e-6 and abs(crop()["gRS"] - 2.39) < 1e-6, "two Formats kept: yours 4:5, Scenery's 2.39:1")
check(not crop()["gLive"], "nothing runs: no bars")
a.tap(); w.run(1); a.click("◇ Scenery"); w.run(1); a.click("› Start"); w.run(3)
check(crop()["gLive"] and crop()["gScen"] and abs(eff() - 2.39) < 1e-6, "Scenery runs: Scenery's Format")
a.tap(); w.run(1); a.click("■ Stop"); w.run(1)
a.tap(); w.run(1); a.click("○ Framing"); w.run(3)
check(crop()["gLive"] and not crop()["gScen"] and abs(eff() - 0.8) < 1e-6, "Framing: your Format")
check(abs(float(a.hud.lsd["cin.crop"][0]) - 0.8) < 1e-6, "the cameras compose in yours (cin.crop), not Scenery's")
check(not w.errors and not w2.errors, "no script errors: %s" % (w.errors + w2.errors))
print("hud (real scripts): a dropped-in keys texture is adopted only when yours; Scenery's Format apart from yours")
print("hud_emu checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
