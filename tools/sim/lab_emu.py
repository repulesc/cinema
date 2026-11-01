"""The Take 12 Lab (lab/, lab 1 and 2): the Quiet and Direct pages, on the REAL lab scripts (lab/src: the product's own
scripts with the lab's strip, screen, ui and text). Quiet by default: the Orbit, the running shot and the fold key left
of the [12], the frame, Connect and the shutter right of it, on a floating island centred on the [12] with round ends;
a moment's prompt (KEEP NEW) shows there too, and with the camera yours the last shot, faint, takes it back. The setup
shows the guide card first and aligns the strip Up and Down, 10 px a step. The shot's
name or the fold key opens Direct (the product's full strip, the four shots in Auto too), the fold key (the same place)
folds it; the page is kept for the next wear. The shutter sits beside Connect on both pages. Nothing overlaps at any
window, size or page; the notch turns over at the bottom; closed, it all goes."""
from emu_util import *
import world
from lslmem import LIMIT

w = World()
ana, h = hud(w, scripts=LAB_SCRIPTS, parts=LAB_PARTS)
textures(h)
w.run(2)
ana.double_tap(); w.run(1)
ana.say(12, "tracking"); w.run(3)

R = lambda n: rect(h, ana, n)
on = lambda n: R(n)[4] > 0.02 and R(n)[2] > 0.0101
L = lambda n: R(n)[0] - R(n)[2] / 2
Rt = lambda n: R(n)[0] + R(n)[2] / 2
SH = ["t12 s0", "t12 s1", "t12 s2", "t12 s3"]
OP = ["t12 o%d" % i for i in range(6)]
MIDDLE = ["t12 auto", "t12 fold", "t12 shape", "Take 12", "t12 link", "t12 shut"]


def words_on():
    return [n for n in SH + OP + MIDDLE if on(n)]


def no_overlap(where):
    vis = words_on()
    bad = [(a, b) for i, a in enumerate(vis) for b in vis[i + 1:] if overlap(R(a), R(b), shrink=0.0005)]
    check(not bad, "%s: nothing overlaps (%r)" % (where, bad[:3]))
    half = ana.aspect / 2
    check(all(-half <= L(n) and Rt(n) <= half for n in vis), "%s: everything on screen" % where)


# ---- Quiet, by default: a floating island, centred on the [12] (lab 2) ------------------------------------------------------
IH = 36 / 1080.0
isl = lambda: (L("t12 tab"), Rt("t12 tab2"))


def island_ok(where):
    IH = 36 * var(h, "screen", "gS") / 1080.0                 # the island scales with the strip's size
    x0, x1 = isl()
    m = R("t12 band")
    caps = [h.part(n) for n in ("t12 tab", "t12 tab2")]
    check(all(c.get("type") == C["PRIM_TYPE_CYLINDER"] and abs(c["size"][0] - IH) < 1e-4 and abs(c["size"][1] - IH) < 1e-4
              and c["alpha"] > 0.5 and abs(abs(c["rot"][1]) - 0.7071) < 1e-3 for c in caps),
          "%s: the island's two round ends: discs (cylinders facing you), %.0f px, whatever the texture" % (where, caps[0]["size"][1] * 1080))
    isle = h.part("t12 band")["color"]
    check(0.05 < isle[0] < 0.2 and h.part("t12 band")["pos"][0] < 0.006, "%s: a lifted black, in front of the film's bars" % where)
    check(abs(m[0]) < 1e-4 and abs(m[2] - (x1 - x0 - IH)) < 1e-4 and abs(m[3] - IH) < 1e-4, "%s: its black middle between them" % where)
    check(abs(x0 + x1) < 1e-4, "%s: centred on the [12] (%.0f, %.0f px)" % (where, x0 * 1080, x1 * 1080))
    check(all(x0 < L(n) and Rt(n) < x1 for n in words_on()), "%s: the island holds every word" % where)
    top = m[1] + IH / 2
    check(m[1] * (1 if m[1] > 0 else -1) + IH / 2 < 0.5 - 8 * var(h, "screen", "gS") / 1080.0 + 1e-4, "%s: floating, clear of the screen's edge" % where)


check(var(h, "strip", "gQuiet") == 1, "Quiet is the default")
check(on("t12 s0") and not any(on(n) for n in SH[1:]), "Quiet: only the running shot's name (%r)" % [n for n in SH if on(n)])
check(not any(on(n) for n in OP), "Quiet: no options")
check(all(on(n) for n in MIDDLE), "Quiet: the Orbit, the fold key, the frame, the [12], Connect, the shutter (%r)" % [n for n in MIDDLE if not on(n)])
order = ["t12 auto", "t12 s0", "t12 fold", "Take 12", "t12 shape", "t12 link", "t12 shut"]
check(all(Rt(a) < L(b) for a, b in zip(order, order[1:])), "Quiet, left to right: the Orbit, TRACKING, the fold key | [12] | the frame, Connect, the shutter")
island_ok("Quiet, Tracking")
x0, x1 = isl()
l_side, r_side = -L("t12 auto"), Rt("t12 shut")
check(abs(l_side - r_side) < 60 / 1080.0, "balanced either side of the [12] (%.0f and %.0f px)" % (l_side * 1080, r_side * 1080))
w0 = x1 - x0
ana.say(12, "portrait"); w.run(3)
check(abs((isl()[1] - isl()[0]) - w0) < 1e-5, "the island keeps its width from shot to shot")
no_overlap("Quiet, Portrait")
fold_x = R("t12 fold")[0]
frame_x = R("t12 shape")[0]

# ---- the camera yours: the last shot, faint, a tap takes it back ------------------------------------------------------------
h.send(7371, "stop"); w.run(1.5)
check(var(h, "core", "gState") == "wait" and on("t12 s1") and R("t12 s1")[4] < 0.45, "your camera: PORTRAIT, faint, in its place (%.2f)" % R("t12 s1")[4])
island_ok("Quiet, your camera")
ana.touch("t12 s1"); w.run(2)
check(var(h, "core", "gShot") == "portrait" and var(h, "strip", "gQuiet") == 1, "a tap on it takes it back, still Quiet")

# ---- Direct ---------------------------------------------------------------------------------------------------------------
ana.touch("t12 s1"); w.run(1)                                   # the running shot's name opens Direct
check(var(h, "strip", "gQuiet") == 0 and lsd(h, "page") == "direct", "the shot's name opens Direct, and it is kept")
check(var(h, "core", "gShot") == "portrait", "... and nothing else changes (%r)" % var(h, "core", "gShot"))
check(all(on(n) for n in SH) and on("t12 o0"), "Direct: the four shots and the options")
check(abs(R("t12 fold")[0] - fold_x) < 1e-5 and abs(R("t12 shape")[0] - frame_x) < 1e-5, "the fold key and the frame in the same place on both pages")
check(not on("t12 tab") and not on("t12 tab2") and R("t12 band")[2] > ana.aspect, "Direct: the band edge to edge, no island")
no_overlap("Direct, Portrait")
ana.touch("t12 fold"); w.run(1)
check(var(h, "strip", "gQuiet") == 1 and lsd(h, "page") == "quiet" and on("t12 tab2"), "the fold key folds it back to Quiet")
ana.touch("t12 fold"); w.run(1)
check(var(h, "strip", "gQuiet") == 0, "... and opens Direct")

# ---- the page is kept for the next wear ----------------------------------------------------------------------------------
h.detach(); w.run(1); h.attach(); w.run(6)
if not var(h, "strip", "gOpen"): ana.double_tap(); w.run(1)        # (the strip comes back as left: open)
check(var(h, "strip", "gQuiet") == 0, "worn again: Direct, as left")
ana.touch("t12 fold"); w.run(1)

# ---- a moment's prompt on Quiet --------------------------------------------------------------------------------------------
ana.say(12, "fixed"); w.run(3)
h.send(7340, "fixed|VIEW A,VIEW B,KEEP NEW|lit,,accent"); w.run(0.3)
check(var(h, "strip", "gOptVis") == ["KEEP NEW"] and on("t12 o0") and not on("t12 o1"), "Quiet: KEEP NEW shows, the views do not (%r)" % var(h, "strip", "gOptVis"))
check(Rt("t12 o0") < L("t12 fold") and Rt("t12 s2") < L("t12 o0"), "FIXED, then KEEP NEW, then the fold key")
island_ok("Quiet, KEEP NEW")
no_overlap("Quiet, KEEP NEW")

# ---- Auto: Quiet shows its pick; Direct, every shot to direct with ------------------------------------------------------------
ana.say(12, "auto"); w.run(4)
check(var(h, "strip", "gAuto") == 1 and on("t12 auto") and sum(on(n) for n in SH) == 1, "Quiet in Auto: the Orbit and the shot it chose")
ana.touch("t12 fold"); w.run(1)
check(all(on(n) for n in SH) and var(h, "strip", "gAuto") == 1, "Direct in Auto: the four shots, Auto still directing")
other = [n for n in SH if not R(n)[4] > 0.7][0]
ana.touch(other); w.run(2)
check(var(h, "tracking", "gAuto") == 0, "a shot tapped in Auto: yours from here")
check(var(h, "core", "gShot") == ["tracking", "portrait", "fixed", "scenic"][SH.index(other)], "... that shot (%s: %r)" % (other, var(h, "core", "gShot")))
no_overlap("Direct, after Auto")

# ---- every window, size and page ---------------------------------------------------------------------------------------------
for asp in (1.25, 1.6, 1.778, 2.4, 3.2):
    ana.aspect = asp
    for sz in ("s", "m", "l"):
        ana.say(12, "size " + sz); w.run(2.5)
        for pg in (0, 1):
            if var(h, "strip", "gQuiet") != pg: ana.touch("t12 fold"); w.run(0.6)
            no_overlap("%.2f, %s, %s" % (asp, sz.upper(), ["Direct", "Quiet"][pg]))
            if pg: island_ok("%.2f, %s" % (asp, sz.upper()))
ana.aspect = 1.778
ana.say(12, "size m"); w.run(2.5)

# ---- lower places, the bottom, closed ---------------------------------------------------------------------------------------
for pl in ("topl", "bot", "both"):
    ana.say(12, "place " + pl); w.run(2.5)
    island_ok("place " + pl)
ana.say(12, "place top"); w.run(2.5)
ana.double_tap(); w.run(1.5)
check(not on("t12 tab") and not on("t12 tab2") and not on("t12 fold") and not on("t12 band"), "closed: the island, the fold key and the band go")
# ---- the screen script started again after the strip (in-world: scripts added one by one): the island comes back --------
for sc in h.live():                                              # (the strip closed, as left above)
    if sc.name == "screen": h.reset(sc)
w.run(4)
ana.double_tap(); w.run(1.5)                                       # opened again: the strip sends the island anew
island_ok("screen started again")
no_errors(w, "lab")
mem_h = h

# ---- a Lab built with the product's builder (no island parts): it still floats, and says what to do ---------------------------
w3 = World()
cy, h3 = hud(w3, name="Cy", scripts=LAB_SCRIPTS, parts=PARTS)
textures(h3); w3.run(2)
cy.double_tap(); w3.run(1); cy.say(12, "tracking"); w3.run(3)
m = rect(h3, cy, "t12 band")
check(m[4] > 0.5 and m[2] < 0.6 and abs(m[0]) < 1e-4, "no island parts: the island still floats, square-ended (%.0f px wide)" % (m[2] * 1080))
check(any("round ends are missing" in str(c) for c in cy.chat), "... and says once how to add its parts")
no_errors(w3, "lab, product builder")

# ---- the setup (lab 2): the guide card first, then Up and Down, 10 px a step ------------------------------------------------
w2 = World()
bo = w2.avatar("Bo", (128, 128, 21))
h2 = bo.wear(LAB_SCRIPTS, parts=LAB_PARTS, lsd={"cin.owner": (str(bo.key), PASS)})
w2.run(1)
textures(h2); h2.drop("take12_guide_1024"); w2.run(6)
card = lambda: rect(h2, bo, "t12 guide")[4] > 0.5 and rect(h2, bo, "t12 guide")[2] > 0.02
check(card(), "the first wear: the guide card first")
bo.touch("t12 guide"); w2.run(0.5)
check(not card(), "a tap on it closes it")
bo.tap(); w2.run(0.6); bo.click("Start"); w2.run(0.5); bo.click("Skip"); w2.run(0.5)
bo.tap(); w2.run(0.6); bo.click("Good"); w2.run(0.5)
check(bo.labels() == ["Up", "Down", "Done"], "the setup aligns the strip both ways: %r" % bo.labels())
z0 = rect(h2, bo, "Take 12")[1]
for k in range(3): bo.click("Down"); w2.run(0.5)
check(lsd(h2, "drop") == "3" and abs((z0 - rect(h2, bo, "Take 12")[1]) * 1080 - 30) < 0.5, "Down x3: 30 px further in (%r)" % lsd(h2, "drop"))
bo.click("Up"); w2.run(0.5)
check(lsd(h2, "drop") == "2" and abs((z0 - rect(h2, bo, "Take 12")[1]) * 1080 - 20) < 0.5, "Up: a step back")
for k in range(4): bo.click("Up"); w2.run(0.5)
check(lsd(h2, "drop") == "0" and abs(rect(h2, bo, "Take 12")[1] - z0) < 1e-4, "Up stops at the edge")
bo.click("Done"); w2.run(1)
check(bo.labels() == ["Cinema", "Full screen"], "then the picture: Cinema or Full screen (%r)" % bo.labels())
bo.click("Full screen"); w2.run(4)
check(lsd(h2, "bars") == "0" and rect(h2, bo, "t12 bar2")[4] < 0.02, "Full screen: no bars")
check(lsd(h2, "firstrun") == "done" and not card() and bo.dialog is None, "the setup ends, no card again (it came first)")
check(var(h2, "screen", "gOpen") == 1 and var(h2, "tracking", "gAuto") == 1, "... the strip open and Auto filming (the setup really finished)")
bo.tap(); w2.run(0.6); bo.click("Settings"); w2.run(0.5); bo.click("Reset"); w2.run(0.5); bo.click("Everything"); w2.run(0.5)
bo.click("Yes, reset"); w2.run(2)
check(card() and bo.dialog is not None, "Reset > Everything: the guide card again, and the setup")
check(var(h2, "bars", "gOn") == 1, "... and the film's bars back, as new (the picture is asked again)")
no_errors(w2, "lab setup")
h = mem_h
# ---- runtime memory (as memory_emu: the static estimate, the globals, twice the biggest list; 3 KB must stay free) --
for sc in h.scripts:
    if sc.name in ("strip", "screen", "ui", "text"):
        free = LIMIT - world.static(sc.prog.path) - sc.globals_bytes() - 2 * sc.peak
        check(free >= 3 * 1024, "lab %s: %.1f KB free at its peak (a list of %.1f KB in %s)" % (sc.name, free / 1024, sc.peak / 1024, sc.peak_at))
        print("lab %s: %.1f KB free at its peak" % (sc.name, free / 1024))
done("lab_emu")
