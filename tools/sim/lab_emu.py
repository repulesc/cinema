"""The Take 12 Lab (lab/, lab 1): the Quiet and Direct pages, on the REAL lab scripts (lab/src: the product's own scripts
with the lab's strip and screen). Quiet by default: the Orbit, the running shot, the fold key, the frame, the [12],
Connect and the shutter on a notch only as wide as they are; a moment's prompt (KEEP NEW) shows there too. The shot's
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


# ---- Quiet, by default ----------------------------------------------------------------------------------------------------
check(var(h, "strip", "gQuiet") == 1, "Quiet is the default")
check(on("t12 s0") and not any(on(n) for n in SH[1:]), "Quiet: only the running shot's name (%r)" % [n for n in SH if on(n)])
check(not any(on(n) for n in OP), "Quiet: no options")
check(all(on(n) for n in MIDDLE), "Quiet: the Orbit, the fold key, the frame, the [12], Connect, the shutter (%r)" % [n for n in MIDDLE if not on(n)])
check(L("t12 auto") > -0.4 and Rt("t12 auto") < L("t12 s0") and Rt("t12 s0") < L("t12 fold") and Rt("t12 fold") < L("t12 shape"),
      "Quiet, left to right: the Orbit, TRACKING, the fold key, the frame")
check(Rt("Take 12") < L("t12 link") and Rt("t12 link") < L("t12 shut") and L("t12 shut") - Rt("t12 link") < 0.04,
      "the shutter beside Connect")
tab = R("t12 tab")
check(on("t12 tab") and tab[2] < 0.55, "the notch is there, not the band edge to edge (%.0f px wide)" % (tab[2] * 1080))
check(all(L("t12 tab") < L(n) and Rt(n) < Rt("t12 tab") for n in words_on()), "the notch holds every word")
check(abs(tab[1] - R("Take 12")[1]) < 1e-4 and abs(tab[3] - 40 / 1080.0) < 1e-4, "on the strip's line, 40 px tall")
check(abs(tab[1] + tab[3] / 2 - 0.5) < 1e-3, "flush with the screen's top edge (Top)")
check(not on("t12 band"), "Top, no margin: no black above the notch")
check(str(h.part("t12 tab")["tex"][0]) == lsd(h, "take12_marks") and abs(float(h.part("t12 tab")["tex"][3])) < 1e-6, "the notch: the marks' cell, upright")
w0 = tab[2]
ana.say(12, "portrait"); w.run(3)
check(abs(R("t12 tab")[2] - w0) < 1e-5, "the notch keeps its width from shot to shot")
no_overlap("Quiet, Portrait")
fold_x = R("t12 fold")[0]

# ---- Direct ---------------------------------------------------------------------------------------------------------------
ana.touch("t12 s1"); w.run(1)                                   # the running shot's name opens Direct
check(var(h, "strip", "gQuiet") == 0 and lsd(h, "page") == "direct", "the shot's name opens Direct, and it is kept")
check(var(h, "core", "gShot") == "portrait", "... and nothing else changes (%r)" % var(h, "core", "gShot"))
check(all(on(n) for n in SH) and on("t12 o0"), "Direct: the four shots and the options")
check(abs(R("t12 fold")[0] - fold_x) < 1e-5, "the fold key is in the same place on both pages")
check(not on("t12 tab") and R("t12 band")[2] > ana.aspect, "Direct: the band edge to edge, no notch")
no_overlap("Direct, Portrait")
ana.touch("t12 fold"); w.run(1)
check(var(h, "strip", "gQuiet") == 1 and lsd(h, "page") == "quiet" and on("t12 tab"), "the fold key folds it back to Quiet")
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
check(all(L("t12 tab") < L(n) for n in words_on()), "the notch holds the prompt too")
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
            if pg: check(all(L("t12 tab") < L(n) and Rt(n) < Rt("t12 tab") for n in words_on()), "%.2f %s: the notch holds every word" % (asp, sz))
ana.aspect = 1.778
ana.say(12, "size m"); w.run(2.5)

# ---- lower places, the bottom, closed ---------------------------------------------------------------------------------------
ana.say(12, "place topl"); w.run(2.5)
b, t = R("t12 band"), R("t12 tab")
check(on("t12 band") and abs(b[2] - t[2]) < 1e-5 and abs((b[1] - b[3] / 2) - (t[1] + t[3] / 2)) < 1e-4 and abs(b[1] + b[3] / 2 - 0.5) < 1e-3,
      "Top lower: black from the screen's edge down to the notch, as wide")
ana.say(12, "place bot"); w.run(2.5)
b, t = R("t12 band"), R("t12 tab")
check(abs(b[1] - b[3] / 2 + 0.5) < 1e-3 and abs((b[1] + b[3] / 2) - (t[1] - t[3] / 2)) < 1e-4 and abs(float(h.part("t12 tab")["tex"][3]) - 3.14159) < 1e-3,
      "at the bottom (46 px up, as the product): black from the edge up to the notch, the notch turned over")
ana.say(12, "place top"); w.run(2.5)
ana.double_tap(); w.run(1.5)
check(not on("t12 tab") and not on("t12 fold") and not on("t12 band"), "closed: the notch, the fold key and the band go")
no_errors(w, "lab")
# ---- runtime memory (as memory_emu: the static estimate, the globals, twice the biggest list; 3 KB must stay free) --
for sc in h.scripts:
    if sc.name in ("strip", "screen"):
        free = LIMIT - world.static(sc.prog.path) - sc.globals_bytes() - 2 * sc.peak
        check(free >= 3 * 1024, "lab %s: %.1f KB free at its peak (a list of %.1f KB in %s)" % (sc.name, free / 1024, sc.peak / 1024, sc.peak_at))
        print("lab %s: %.1f KB free at its peak" % (sc.name, free / 1024))
done("lab_emu")
