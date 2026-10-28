"""The strip on every screen (8.0), on the REAL scripts: windows from 5:4 to 32:9, the four places, sizes S / M / L.
Checked: nothing off the screen, no two words overlap, the words stay in a centred 16:9 area and 180 px (scaled) in
from its corners when there is room (less on a narrow window, never under 0.02), the words at least 19 px tall on a
1080 px window, the [12] at the strip's middle, closed every strip part shrunk away (nothing left to catch a click),
the bars cut the shot's shape (letterbox, pillarbox), the note part under the strip (above it at the bottom)."""
from emu_util import *

ASPECTS = [1.25, 1.333, 1.6, 1.778, 2.0, 2.37, 2.4, 3.2, 3.556]
PLACES = ["top", "topl", "bot", "both"]
MARGIN = {"top": 0, "topl": 52, "bot": 46, "both": 96}
SIZES = {"s": 0.8, "m": 1.0, "l": 1.25}
PADX = 8.0

w = World()
ana, h = hud(w)
textures(h)
w.run(1)
check(h.prims[0]["desc"].count("take12_") == 2 and "take12_words" not in h.inventory, "the textures are adopted: %r" % h.prims[0]["desc"])
ana.double_tap(); w.run(1)
ana.touch("t12 s2"); w.run(3)                                          # Fixed: then the widest option row there is
h.send(7340, "fixed|KEEP NEW,/,FORGET SEAT,LET GO|accent,,dim,")
h.send(7342, "theirs|3|Ben")                                          # the widest Connect word
w.run(1)
n = 0
for a in ASPECTS:
    ana.aspect = a
    for pl in PLACES:
        for sz, S in SIZES.items():
            ana.say(12, "place " + pl); ana.say(12, "size " + sz)
            w.run(2.5)
            n += 1
            tag = "%.3f %s %s" % (a, pl, sz)
            px = lambda v: v * S / 1080.0
            V = visible(h, ana)
            check(len(V) == 4 + 3 + 2 + 1 + 1 and "t12 shut" in V and "t12 auto" in V, "%s: 4 shots, 3 option words, shape, link, the shutter and the Orbit visible (%s)" % (tag, sorted(V)))
            names = sorted(V)
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    hw = px(24.0)
                    if overlap(V[names[i]], V[names[j]], PADX / 48.0 * hw):
                        check(False, "%s: %s overlaps %s" % (tag, names[i], names[j]))
            Wc = min(a, 1.778)
            for k, r in V.items():
                check(abs(r[0]) + r[2] / 2 <= Wc / 2 + 1e-4, "%s: %s outside the 16:9 area (%.3f)" % (tag, k, r[0]))
                check(abs(r[1]) + r[3] / 2 <= 0.5, "%s: %s off the screen vertically" % (tag, k))
                check(r[3] * 1080 >= 19.0, "%s: %s only %.1f px tall" % (tag, k, r[3] * 1080))
            # the corner inset: 180 px when there is room, never under 0.02
            left = min(r[0] - r[2] / 2 for r in V.values()) + Wc / 2
            right = Wc / 2 - max(r[0] + r[2] / 2 for r in V.values())
            check(left >= 0.02 - 1e-4 and right >= 0.02 - 1e-4, "%s: the words reach the edge (%.3f, %.3f)" % (tag, left, right))
            if a >= 1.6 and S <= 1.0:
                check(abs(left - px(180)) < 0.002 or left > px(180), "%s: left inset %.3f, not 180 px" % (tag, left))
            # the strip's line and the [12] in its middle
            root = rect(h, ana, "Take 12")
            mid = 0.5 - MARGIN[pl] / 1080.0 - px(48) / 2
            want = mid if pl in ("top", "topl") else -mid
            check(abs(root[1] - want) < 1e-3 and abs(root[0]) < 1e-4, "%s: the [12] at %.4f, %.4f (want 0, %.4f)" % (tag, root[0], root[1], want))
            for k, r in V.items():
                check(abs(r[1] - root[1]) < 1e-3, "%s: %s is off the strip's line" % (tag, k))
            note = rect(h, ana, "t12 note")
            check((note[1] < root[1]) == (pl in ("top", "topl")), "%s: the note part is on the wrong side" % tag)
            band = rect(h, ana, "t12 band")
            check(band[2] >= a and band[4] > 0.5, "%s: the band runs the whole width" % tag)
no_errors(w, "layout")
# Auto (8.3.0): the Orbit lit, then only the shot it chose, faint; nothing overlaps, at every window and size
h.send(7371, "auto|1"); w.run(1)
for a in ASPECTS:
    ana.aspect = a
    for sz in SIZES:
        ana.say(12, "size " + sz); w.run(2.5)
        V = visible(h, ana)
        tag = "auto %.3f %s" % (a, sz)
        shot = [k for k in V if len(k) == 6 and k.startswith("t12 s")]
        check(len(shot) == 1 and sorted(V) == sorted(["t12 auto", "t12 link", "t12 shape", "t12 shut"] + shot), "%s: the Orbit, one shot, shape, link, shutter (%s)" % (tag, sorted(V)))
        if len(shot) != 1: continue
        names = sorted(V)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if overlap(V[names[i]], V[names[j]], PADX / 48.0 * 24.0 * SIZES[sz] / 1080.0):
                    check(False, "%s: %s overlaps %s" % (tag, names[i], names[j]))
        check(V["t12 auto"][0] < V[shot[0]][0], "%s: the Orbit left of the shot" % tag)
h.send(7371, "auto|0"); ana.say(12, "size m"); w.run(2.5)
no_errors(w, "auto")
# closed: everything but the [12] (and its ring, dot, the bars, the note part) shrinks away
ana.double_tap(); w.run(1.5)
keep = ("Take 12", "t12 ring", "t12 dot", "t12 note", "t12 bar0", "t12 bar1", "t12 bar2", "t12 bar3", "t12 u2")
for p in h.prims[1:]:
    if p["name"] not in keep:
        check(p["alpha"] == 0.0 and p["size"][1] <= 0.0101 and p["size"][2] <= 0.0101, "closed: %s still there (%s, %.2f)" % (p["name"], p["size"], p["alpha"]))
# the bars cut the shape: Fixed is 1.85 by default
for a in (1.25, 1.778, 3.556):
    ana.aspect = a
    w.run(2.5)
    bars = [rect(h, ana, "t12 bar%d" % i) for i in range(4)]
    vis = [b for b in bars if b[4] > 0.5 and b[2] > 0.0101 and b[3] > 0.0101]
    if a < 1.85:
        th = (1 - a / 1.85) / 2
        check(len(vis) == 2 and all(abs(b[3] - th) < 1e-3 and abs(abs(b[1]) - (0.5 - th / 2)) < 1e-3 for b in vis), "bars on %.3f: letterbox %s" % (a, vis))
    else:
        sw = (a - 1.85) / 2
        check(len(vis) == 2 and all(abs(b[2] - sw) < 1e-3 and abs(abs(b[0]) - (1.85 + sw) / 2) < 1e-3 for b in vis), "bars on %.3f: pillarbox %s" % (a, vis))
    for b in vis:
        check(abs(b[0]) + b[2] / 2 <= a / 2 + 1e-3 and abs(b[1]) + b[3] / 2 <= 0.5 + 1e-3, "bars on %.3f: off the screen" % a)
no_errors(w, "bars")
print("%d layouts" % n)
done("layout_emu")
