"""The Take 12 Lab (lab/, lab 1 and 2; 8.10.0): the Quiet and Direct pages, on the REAL lab scripts (lab/src: the product's
own scripts with the lab's strip, screen, ui and text). Quiet by default: one floating island with round ends holding the
x (let go) at the far left, the Orbit, the four shots, the [12], the frame, Connect, the shutter and the fold key › at
the right end. A tap on a shot directs it (the lit one: its next view), and the island never changes its shape from
shot to shot; a moment's prompt (KEEP NEW) joins its left end. The x: one tap, your viewer's camera (the x bright, the
shots quiet); a tap again, or a shot, takes it back (Auto if Auto directed). › opens Direct (the product's full strip:
the same keys edge to edge, with the running shot's options), ‹ in the same place folds it; the page is kept for the
next wear. The setup shows the guide card last and aligns the strip Up and Down first, 10 px a step. Nothing overlaps
at any window, size or page; the notch turns over at the bottom; closed, it all goes."""
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
MIDDLE = ["t12 free", "t12 auto", "t12 fold", "t12 shape", "Take 12", "t12 link", "t12 shut"]
PX = lambda v: v * var(h, "screen", "gS") / 1080.0
FOLD = {"foldR": (256 + 32) / 1024.0 - 0.5, "foldL": (320 + 32) / 1024.0 - 0.5}      # the cells' offsets (make_lab.py)
fold_is = lambda c: abs(h.part("t12 fold")["tex"][2][0] - FOLD[c]) < 1e-4
core_st = lambda: (var(h, "core", "gState"), var(h, "core", "gShot"))


def words_on():
    return [n for n in SH + OP + MIDDLE if on(n)]


def no_overlap(where):
    vis = words_on()
    bad = [(a, b) for i, a in enumerate(vis) for b in vis[i + 1:] if overlap(R(a), R(b), shrink=0.0005)]
    check(not bad, "%s: nothing overlaps (%r)" % (where, bad[:3]))
    half = ana.aspect / 2
    check(all(-half <= L(n) and Rt(n) <= half for n in vis), "%s: everything on screen" % where)


# ---- Quiet, by default: one floating island, from the x to the fold key (8.10.0) -----------------------------------------
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
    check(abs(m[0] - (x0 + x1) / 2) < 1e-4 and abs(m[2] - (x1 - x0 - IH)) < 1e-4 and abs(m[3] - IH) < 1e-4,
          "%s: its black middle between the two ends (%.0f to %.0f px)" % (where, x0 * 1080, x1 * 1080))
    vis = words_on()
    check(all(x0 < L(n) and Rt(n) < x1 for n in vis), "%s: the island holds every key (%r)" % (where, [n for n in vis if not (x0 < L(n) and Rt(n) < x1)]))
    left = min(vis, key=L)
    check(abs((L(left) - x0) - PX(16)) < 1e-4 and abs((x1 - Rt("t12 fold")) - PX(16)) < 1e-4,
          "%s: 16 px of island either side, from %s to the fold key (%.1f, %.1f px)" % (where, left, (L(left) - x0) * 1080, (x1 - Rt("t12 fold")) * 1080))
    check(m[1] * (1 if m[1] > 0 else -1) + IH / 2 < 0.5 - 8 * var(h, "screen", "gS") / 1080.0 + 1e-4, "%s: floating, clear of the screen's edge" % where)


check(var(h, "strip", "gQuiet") == 1, "Quiet is the default")
check(all(on(n) for n in SH), "Quiet: the four shots (%r)" % [n for n in SH if not on(n)])
check(not any(on(n) for n in OP), "Quiet: no options")
check(all(on(n) for n in MIDDLE), "Quiet: the x, the Orbit, the frame, the [12], Connect, the shutter, the fold key (%r)" % [n for n in MIDDLE if not on(n)])
order = ["t12 free", "t12 auto"] + SH + ["Take 12", "t12 shape", "t12 link", "t12 shut", "t12 fold"]
check(all(Rt(a) < L(b) for a, b in zip(order, order[1:])),
      "Quiet, left to right: the x, the Orbit, TRACKING PORTRAIT FIXED SCENIC | [12] | the frame, Connect, the shutter, ›")
gaps = [L(b) - Rt(a) for a, b in zip(order[:6], order[1:6])]
check(max(gaps) - min(gaps) < 1e-4, "Quiet: the x, the Orbit and the shots evenly spaced (%r px)" % [round(g * 1080, 1) for g in gaps])
check(fold_is("foldR"), "Quiet: the fold key reads ›")
check(R("t12 s0")[4] > 0.9 and all(0.4 < R(n)[4] < 0.8 for n in SH[1:]) and on("t12 box") and abs(R("t12 box")[0] - R("t12 s0")[0]) < 1e-4,
      "Quiet: TRACKING bright and underlined, the others quiet (%r)" % [round(R(n)[4], 2) for n in SH])
check(0.4 < R("t12 free")[4] < 0.7, "Quiet: the x quiet while filming (%.2f)" % R("t12 free")[4])
island_ok("Quiet, Tracking")
b0 = isl()
for k, shot in enumerate(["portrait", "fixed", "scenic", "tracking"]):
    ana.touch(SH[(k + 1) % 4]); w.run(3)
    check(core_st() == ("film", shot) and var(h, "strip", "gQuiet") == 1, "Quiet: one tap on %s directs it, still Quiet (%r)" % (shot.upper(), core_st()))
    check(max(abs(a - b) for a, b in zip(isl(), b0)) < 1e-5, "... and the island keeps its shape exactly (%.0f to %.0f px)" % (isl()[0] * 1080, isl()[1] * 1080))
    no_overlap("Quiet, " + shot)
ana.touch("t12 s1"); w.run(3)
side0 = var(h, "portrait", "gSide")
ana.touch("t12 s1"); w.run(2)
check(var(h, "portrait", "gSide") == -side0 and core_st() == ("film", "portrait"), "Quiet: the lit shot's tap keeps its job (Portrait: the other side)")
h.send(7320, "film|portrait|fixed|"); w.run(0.3)                    # a hint (sat down): FIXED's outline, on the island
check(on("t12 halo") and abs(R("t12 halo")[0] - R("t12 s2")[0]) < 1e-4 and isl()[0] < L("t12 halo") and Rt("t12 halo") < isl()[1],
      "Quiet: a hint's outline round FIXED, inside the island")
w.run(6)
check(not on("t12 halo"), "... for 5 s")

# ---- the x: let go, and take back (8.10.0: one tap; it was a 0.8 s hold on the lit shot or the Orbit) --------------------
ana.touch("t12 free"); w.run(1.5)
check(core_st() == ("wait", "") and var(h, "strip", "gGone") == "portrait", "the x: your viewer's camera, Take 12 waits (%r)" % (core_st(),))
check(R("t12 free")[4] > 0.95 and all(R(n)[4] < 0.4 for n in SH) and not on("t12 box"), "... the x bright, the shots quiet, nothing lit (%r)" % [round(R(n)[4], 2) for n in SH])
check(any("Tap the x again" in n for n in ana.notes()), "... and the note says how to take it back")
check(max(abs(a - b) for a, b in zip(isl(), b0)) < 1e-5 and on("Take 12") and on("t12 link"), "... the island as it was, the strip on")
w.run(20)
check(core_st() == ("wait", ""), "... and it stays yours (nothing takes it back by itself)")
ana.away = True; w.run(3)
check(core_st() == ("film", "scenic") and var(h, "core", "gWhy") == "idle" and R("t12 free")[4] > 0.95, "Away: idle Scenic, as ever; the x still bright (%r)" % (core_st(),))
ana.away = False; ana.typing = True; w.run(2); ana.typing = False
check(core_st() == ("wait", "") and var(h, "strip", "gGone") == "portrait" and R("t12 free")[4] > 0.95, "back (typing): your camera again, the x still remembers Portrait (%r)" % (core_st(),))
ana.touch("t12 free"); w.run(3)
check(core_st() == ("film", "portrait") and var(h, "strip", "gGone") == "" and 0.4 < R("t12 free")[4] < 0.7, "the x again: Portrait films again (%r)" % (core_st(),))
ana.touch("t12 free"); w.run(1.5)
ana.touch("t12 s3"); w.run(3)
check(core_st() == ("film", "scenic") and var(h, "strip", "gGone") == "" and R("t12 s3")[4] > 0.9, "let go, then a shot: that shot films (%r)" % (core_st(),))
ana.say(12, "auto"); w.run(4)
picked = var(h, "core", "gShot")
check(var(h, "tracking", "gAuto") == 1 and core_st()[0] == "film", "(Auto films: %r)" % picked)
ana.touch("t12 free"); w.run(1.5)
check(core_st() == ("wait", "") and var(h, "tracking", "gAuto") == 0 and var(h, "strip", "gGone") == "auto", "the x in Auto: your viewer's camera, Auto rests (%r)" % (core_st(),))
check(R("t12 auto")[4] < 0.6, "... the Orbit no longer lit")
w.run(20)
check(core_st()[0] == "wait" and var(h, "tracking", "gAuto") == 0, "... and Auto stays out of it")
ana.touch("t12 free"); w.run(4)
check(var(h, "tracking", "gAuto") == 1 and var(h, "strip", "gAuto") == 1 and core_st()[0] == "film", "the x again: Auto directs again (%r)" % (core_st(),))
ana.touch("t12 free"); w.run(1.5)
ana.touch("t12 auto"); w.run(4)
check(var(h, "tracking", "gAuto") == 1 and var(h, "strip", "gGone") == "" and core_st()[0] == "film", "let go, then the Orbit: Auto directs (%r)" % (core_st(),))
ana.touch("t12 free"); w.run(1.5)
ana.touch("t12 s1"); w.run(3)
check(core_st() == ("film", "portrait") and var(h, "tracking", "gAuto") == 0 and var(h, "strip", "gGone") == "", "let go from Auto, then a shot: that shot, yours (%r)" % (core_st(),))
ana.touch("t12 free"); w.run(1.5)
ana.say(12, "fixed"); w.run(3)
check(core_st()[0] == "film" and var(h, "strip", "gGone") == "" and 0.4 < R("t12 free")[4] < 0.7, "let go, then /12 fixed: filming, the x quiet again")
ana.long_press(); w.run(2)
check(core_st()[0] == "off", "(held: all off)")
ana.long_press(); w.run(3)
if not var(h, "strip", "gOpen"): ana.double_tap(); w.run(1)
check(core_st()[0] == "film" and var(h, "strip", "gGone") == "", "all off and back: nothing left to take back (%r)" % (core_st(),))
h.send(7371, "stop"); w.run(1.5)
check(core_st() == ("wait", ""), "(your camera, by /12 off or Esc)")
ana.touch("t12 free"); w.run(1.5)
check(core_st() == ("wait", "") and var(h, "strip", "gGone") == "", "the x with nothing filming: nothing happens")
ana.touch("t12 s1"); w.run(3)
no_errors(w, "lab: the x")

# ---- Direct: › opens the full strip, ‹ in the same place folds it -----------------------------------------------------------
fold_x = R("t12 fold")[0]
frame_x = R("t12 shape")[0]
ana.touch("t12 fold"); w.run(1)
check(var(h, "strip", "gQuiet") == 0 and lsd(h, "page") == "direct", "› opens Direct, and it is kept")
check(core_st() == ("film", "portrait"), "... and nothing else changes (%r)" % (core_st(),))
check(all(on(n) for n in SH + ["t12 free", "t12 auto"]) and on("t12 o0"), "Direct: the x, the Orbit, the four shots and the options")
check(Rt("t12 free") < L("t12 auto") < Rt("t12 auto") < L("t12 s0"), "Direct: the x at the far left, then the Orbit, then the shots")
check(abs(R("t12 fold")[0] - fold_x) < 1e-5 and abs(R("t12 shape")[0] - frame_x) < 1e-5 and fold_is("foldL"),
      "Direct: ‹ where › was, the frame in the same place")
check(all(Rt("t12 fold") < L(n) for n in OP if on(n)), "Direct: the options right of ‹")
check(not on("t12 tab") and not on("t12 tab2") and R("t12 band")[2] > ana.aspect, "Direct: the band edge to edge, no island")
no_overlap("Direct, Portrait")
ana.touch("t12 free"); w.run(1.5)
check(core_st() == ("wait", "") and R("t12 free")[4] > 0.95, "Direct: the x lets go the same")
ana.touch("t12 free"); w.run(3)
check(core_st() == ("film", "portrait"), "... and takes back")
ana.touch("t12 fold"); w.run(1)
check(var(h, "strip", "gQuiet") == 1 and lsd(h, "page") == "quiet" and on("t12 tab2") and fold_is("foldR"), "‹ folds it back to Quiet")
ana.touch("t12 fold"); w.run(1)
check(var(h, "strip", "gQuiet") == 0, "... and › opens Direct")

# ---- the page is kept for the next wear ----------------------------------------------------------------------------------
h.detach(); w.run(1); h.attach(); w.run(6)
if not var(h, "strip", "gOpen"): ana.double_tap(); w.run(1)        # (the strip comes back as left: open)
check(var(h, "strip", "gQuiet") == 0, "worn again: Direct, as left")
ana.touch("t12 fold"); w.run(1)

# ---- a moment's prompt on Quiet: at the island's left end ---------------------------------------------------------------
ana.say(12, "fixed"); w.run(3)
b1 = isl()
h.send(7340, "fixed|VIEW A,VIEW B,KEEP NEW|lit,,accent"); w.run(0.3)
check(var(h, "strip", "gOptVis") == ["KEEP NEW"] and on("t12 o0") and not on("t12 o1"), "Quiet: KEEP NEW shows, the views do not (%r)" % var(h, "strip", "gOptVis"))
check(Rt("t12 o0") < L("t12 free"), "KEEP NEW left of the x")
check(isl()[0] < b1[0] - 0.02 and abs(isl()[1] - b1[1]) < 1e-5, "... the island grows to the left only")
island_ok("Quiet, KEEP NEW")
no_overlap("Quiet, KEEP NEW")
ana.touch("t12 o0"); w.run(1)
h.send(7340, "fixed|VIEW A,VIEW B|lit,"); w.run(0.3)
check(max(abs(a - b) for a, b in zip(isl(), b1)) < 1e-5, "... and back to its shape when it goes")

# ---- Auto: the Orbit lit, its pick faint among the four; a tap on a shot is yours ------------------------------------------
ana.say(12, "auto"); w.run(4)
check(var(h, "strip", "gAuto") == 1 and R("t12 auto")[4] > 0.95 and all(on(n) for n in SH), "Quiet in Auto: the Orbit lit, the four shots")
pick = SH[["tracking", "portrait", "fixed", "scenic"].index(var(h, "core", "gShot"))]
check(0.6 < R(pick)[4] < 0.8, "... the shot it chose, faint (%.2f)" % R(pick)[4])
island_ok("Quiet, Auto")
other = [n for n in SH if n != pick][0]
ana.touch(other); w.run(2)
check(var(h, "tracking", "gAuto") == 0 and var(h, "strip", "gQuiet") == 1, "a shot tapped in Auto: yours from here, still Quiet")
check(var(h, "core", "gShot") == ["tracking", "portrait", "fixed", "scenic"][SH.index(other)], "... that shot (%s: %r)" % (other, var(h, "core", "gShot")))
ana.touch("t12 fold"); w.run(1)
ana.say(12, "auto"); w.run(4)
check(all(on(n) for n in SH) and var(h, "strip", "gAuto") == 1, "Direct in Auto: the four shots, Auto directing")
ana.touch("t12 fold"); w.run(1)
ana.say(12, "tracking"); w.run(3)
no_overlap("Quiet, after Auto")

# ---- every window, size and page ---------------------------------------------------------------------------------------------
for asp in (1.25, 1.6, 1.778, 2.4, 3.2):
    ana.aspect = asp
    for sz in ("s", "m", "l"):
        ana.say(12, "size " + sz); w.run(2.5)
        for pg in (0, 1):
            if var(h, "strip", "gQuiet") != pg: ana.touch("t12 fold"); w.run(0.6)
            no_overlap("%.2f, %s, %s" % (asp, sz.upper(), ["Direct", "Quiet"][pg]))
            if pg: island_ok("%.2f, %s" % (asp, sz.upper()))
# ... the widest moment: Fixed's KEEP NEW on Quiet, connected (THEIR FILM, the widest Connect), at every window and size
ana.say(12, "fixed"); w.run(3)
for asp in (1.25, 1.6, 1.778, 2.4, 3.2):
    ana.aspect = asp
    for sz in ("s", "m", "l"):
        ana.say(12, "size " + sz); w.run(2.5)
        h.send(7340, "fixed|VIEW A,VIEW B,KEEP NEW|lit,,accent"); h.send(7342, "theirs|1|Ben"); w.run(0.3)
        no_overlap("%.2f, %s, KEEP NEW, THEIR FILM" % (asp, sz.upper()))
        island_ok("%.2f, %s, KEEP NEW, THEIR FILM" % (asp, sz.upper()))
h.send(7342, "alone|0|"); h.send(7340, "fixed|VIEW A,VIEW B|lit,"); w.run(0.3)
ana.aspect = 1.778
ana.say(12, "size m"); w.run(2.5)
ana.say(12, "tracking"); w.run(3)

# ---- lower places, the bottom, closed ---------------------------------------------------------------------------------------
for pl in ("topl", "bot", "both"):
    ana.say(12, "place " + pl); w.run(2.5)
    island_ok("place " + pl)
ana.say(12, "place top"); w.run(2.5)
ana.double_tap(); w.run(1.5)
check(not any(on(n) for n in ("t12 tab", "t12 tab2", "t12 fold", "t12 free", "t12 band", "t12 auto") + tuple(SH)), "closed: the island, its keys and the band go")
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
vis3 = [n for n in SH + ["t12 auto", "t12 shape", "Take 12", "t12 link", "t12 shut"] if rect(h3, cy, n)[4] > 0.02]
check(m[4] > 0.5 and m[2] < 0.7 and all(m[0] - m[2] / 2 < rect(h3, cy, n)[0] - rect(h3, cy, n)[2] / 2 and rect(h3, cy, n)[0] + rect(h3, cy, n)[2] / 2 < m[0] + m[2] / 2 for n in vis3),
      "no island parts: the island still floats, square-ended, round every key (%.0f px wide)" % (m[2] * 1080))
check(sum("Parts are missing" in str(c) and "t12 free" in str(c) for c in cy.chat) == 1, "... and says once how to add its parts")
cy.touch("t12 s1"); w3.run(3)
check(var(h3, "core", "gShot") == "portrait", "... a shot still directs")
no_errors(w3, "lab, product builder")

# ---- a Lab built before 8.10.0 (no t12 free): no x, the island from the Orbit, and it says what to do --------------------------
w6 = World()
eve, h6 = hud(w6, name="Eve", scripts=LAB_SCRIPTS, parts=[p for p in LAB_PARTS if p != "t12 free"])
textures(h6); w6.run(2)
eve.double_tap(); w6.run(1); eve.say(12, "tracking"); w6.run(3)
R6 = lambda n: rect(h6, eve, n)
x6 = (R6("t12 tab")[0] - R6("t12 tab")[2] / 2, R6("t12 tab2")[0] + R6("t12 tab2")[2] / 2)
g6 = 16 * var(h6, "screen", "gS") / 1080.0
check(abs((R6("t12 auto")[0] - R6("t12 auto")[2] / 2 - x6[0]) - g6) < 1e-4 and abs((x6[1] - R6("t12 fold")[0] - R6("t12 fold")[2] / 2) - g6) < 1e-4,
      "no x: the island from the Orbit to ›, 16 px either side")
check(sum("Parts are missing" in str(c) for c in eve.chat) == 1, "... and it says once how to add the x")
eve.touch("t12 fold"); w6.run(1)
check(var(h6, "strip", "gQuiet") == 0 and R6("t12 auto")[0] - R6("t12 auto")[2] / 2 > -eve.aspect / 2, "... Direct works, the Orbit first")
no_errors(w6, "lab, no x")

# ---- the setup: the strip aligned first (8.9.1), Up and Down 10 px a step; then lens, eye line, size, picture; the card ----
w2 = World()
bo = w2.avatar("Bo", (128, 128, 21))
h2 = bo.wear(LAB_SCRIPTS, parts=LAB_PARTS, lsd={"cin.owner": (str(bo.key), PASS)})
w2.run(1)
textures(h2); h2.drop("take12_guide_1024"); w2.run(6)
card = lambda: rect(h2, bo, "t12 guide")[4] > 0.5 and rect(h2, bo, "t12 guide")[2] > 0.02
check(not card() and bo.labels() == ["Later", "Up", "Down", "Done"] and var(h2, "screen", "gOpen") == 1,
      "the first wear: alignment opens by itself, the strip in view, no guide card (%r)" % bo.labels())
z0 = rect(h2, bo, "Take 12")[1]
for k in range(3): bo.click("Down"); w2.run(0.5)
check(lsd(h2, "drop") == "3" and abs((z0 - rect(h2, bo, "Take 12")[1]) * 1080 - 30) < 0.5, "Down x3: 30 px further in (%r)" % lsd(h2, "drop"))
bo.click("Up"); w2.run(0.5)
check(lsd(h2, "drop") == "2" and abs((z0 - rect(h2, bo, "Take 12")[1]) * 1080 - 20) < 0.5, "Up: a step back")
for k in range(4): bo.click("Up"); w2.run(0.5)
check(lsd(h2, "drop") == "0" and abs(rect(h2, bo, "Take 12")[1] - z0) < 1e-4, "Up stops at the edge")
bo.click("Done"); w2.run(0.5)
check("Skip" in bo.labels(), "then the lens (%r)" % bo.labels())
bo.click("Skip"); w2.run(0.5)
bo.tap(); w2.run(0.6)
check(bo.labels() == ["Smaller", "Good", "Larger"], "the eye line, then the size (%r)" % bo.labels())
bo.click("Good"); w2.run(1)
check(bo.labels() == ["Cinema", "Full screen"], "then the picture: Cinema or Full screen (%r)" % bo.labels())
bo.click("Full screen"); w2.run(4)
check(lsd(h2, "bars") == "0" and rect(h2, bo, "t12 bar2")[4] < 0.02, "Full screen: no bars")
check(lsd(h2, "firstrun") == "done" and card() and bo.dialog is None, "the setup ends with the guide card")
bo.touch("t12 guide"); w2.run(0.5)
check(not card() and bo.dialog is None, "a tap on it closes it, and opens nothing")
check(var(h2, "screen", "gOpen") == 1 and var(h2, "tracking", "gAuto") == 1, "... the strip open and Auto filming (the setup really finished)")
bo.tap(); w2.run(0.6); bo.click("Settings"); w2.run(0.5); bo.click("Reset"); w2.run(0.5); bo.click("Everything"); w2.run(0.5)
bo.click("Yes, reset"); w2.run(2)
check(not card() and bo.dialog and "Up" in bo.labels(), "Reset > Everything: alignment again at once, no card over it")
check(var(h2, "bars", "gOn") == 1, "... and the film's bars back, as new (the picture is asked again)")
bo.click("Later"); w2.run(0.5)
check(bo.dialog is None and lsd(h2, "firstrun") == "done", "Later: the setup another time")
no_errors(w2, "lab setup")

# ---- 8.9.1 (in-world): a tap that closes the guide card is not a tap on the [12]. ui read the touched part's size at the
# touch's end, after the card had gone (and shrunk): it took the card's tap for the [12]'s, kept the eye line wherever it
# was in the setup, or opened the menu
w4 = World()
cy4 = w4.avatar("Cy", (128, 128, 21))
h4 = cy4.wear(LAB_SCRIPTS, parts=LAB_PARTS, lsd={"cin.owner": (str(cy4.key), PASS)})
w4.run(1); textures(h4); h4.drop("take12_guide_1024"); w4.run(6)
card4 = lambda: rect(h4, cy4, "t12 guide")[4] > 0.5 and rect(h4, cy4, "t12 guide")[2] > 0.02
cy4.click("Done"); w4.run(0.5); cy4.click("Skip"); w4.run(1)
check(var(h4, "ui", "gEye"), "(the eye-line step)")
h4.send(7343, "guide|1"); w4.run(0.5)                                     # the card over the eye-line step (/12 guide)
check(card4(), "(the card shows)")
cy4.touch("t12 guide"); w4.run(1.5)
check(not card4() and var(h4, "ui", "gEye") and cy4.dialog is None, "a tap on the card closes it, and the eye-line step goes on (%r)" % (cy4.dialog and cy4.labels()))
cy4.tap(); w4.run(0.6)
check(not var(h4, "ui", "gEye") and "Good" in cy4.labels(), "a tap on the [12] keeps the eye line, as before")
cy4.click("Good"); w4.run(0.5); cy4.click("Cinema"); w4.run(4)
h4.send(7343, "guide|1"); w4.run(0.5)
cy4.touch("t12 guide"); w4.run(1.5)
check(not card4() and cy4.dialog is None and var(h4, "core", "gState") != "off", "after the setup: the card, and closing it opens nothing")
cy4.touch("t12 s0", hold=0.1); w4.run(0.3)                                 # a touch that starts on a part that changes size
check(var(h4, "core", "gState") != "off", "... and a touch on a strip part is never taken for a hold of the [12]")
no_errors(w4, "lab: the card's tap")

# ---- 8.9.1 (in-world): a script missing at the check (being replaced, or stopped and started again by carry) turned the
# [12] amber until the HUD was worn again, though the script was there and running
w5 = World()
dee = w5.avatar("Dee", (128, 128, 21))
h5 = dee.wear(LAB_SCRIPTS, parts=LAB_PARTS, lsd=ready(dee)); w5.run(0.5)
h5.crash("strip"); w5.run(4)
check(any("missing: strip" in n for n in dee.notes()) and var(h5, "screen", "gProblem"), "strip stopped at the check: the note, and the [12] amber")
w5.run(6)
check(not var(h5, "screen", "gProblem"), "strip started again (carry): the [12] is white again")
no_errors(w5, "lab: a script late")
h = mem_h
# ---- runtime memory (as memory_emu: the static estimate, the globals, twice the biggest list; 3 KB must stay free) --
for sc in h.scripts:
    if sc.name in ("strip", "screen", "ui", "text"):
        free = LIMIT - world.static(sc.prog.path) - sc.globals_bytes() - 2 * sc.peak
        check(free >= 3 * 1024, "lab %s: %.1f KB free at its peak (a list of %.1f KB in %s)" % (sc.name, free / 1024, sc.peak / 1024, sc.peak_at))
        print("lab %s: %.1f KB free at its peak (static %.1f KB, globals %.1f KB, a list of %.1f KB in %s)" % (sc.name, free / 1024, world.static(sc.prog.path) / 1024, sc.globals_bytes() / 1024, sc.peak / 1024, sc.peak_at))
done("lab_emu")
