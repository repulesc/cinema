"""The strip that fades, and notes on a plate (8.5.0), on the REAL scripts. 4 s after your last touch the strip fades
away and the [12] stays, quieter, on the left; a tap on it brings the strip back (the menu is the next tap); a touch on
the strip keeps it 4 s more; /12 fade off keeps it. A note sits under the [12] on a dark plate sized to its text."""
from emu_util import *

w = World()
ana = w.avatar("Ana", (128, 128, 21))
L = ready(ana)
L["cin.fade"] = ("1", PASS)                                          # as sold: the strip fades
h = ana.wear(HUD_SCRIPTS, lsd=L)
textures(h)
w.run(0.5); manual(h); w.run(4.5)
ana.double_tap(); w.run(1)
check(var(h, "strip", "gOpen") == 1 and var(h, "strip", "gFaded") == 0 and len(visible(h, ana)) >= 8, "the strip open")
root = h.prims[0]

# ---- 4 s untouched: it fades, the [12] stays at 60 % ---------------------------------------------------------------------
w.run(3)
check(var(h, "strip", "gFaded") == 0, "3 s: still there")
w.run(2.5)
check(var(h, "strip", "gFaded") == 1 and visible(h, ana) == {}, "4 s untouched: the strip faded away (%r)" % sorted(visible(h, ana)))
check(abs(root["alpha"] - 0.6) < 0.01 and var(h, "ui", "gFaded") == 1, "... the [12] stays, at 60 %% (%.2f)" % root["alpha"])
check(var(h, "strip", "gOpen") == 1, "... still open (faded, not closed: it comes back as it was)")

# ---- a tap: back (no menu); the next tap: the menu ------------------------------------------------------------------------
ana.dialog = None
ana.tap(); w.run(0.8)
check(var(h, "strip", "gFaded") == 0 and len(visible(h, ana)) >= 8 and ana.dialog is None, "a tap: the strip back, no menu")
check(abs(root["alpha"] - 1.0) < 0.01, "... the [12] whole again")
ana.tap(); w.run(0.8)
check(ana.dialog is not None, "the next tap: the menu")
ana.click("Close"); w.run(0.5)

# ---- a touch on the strip keeps it 4 s more --------------------------------------------------------------------------------
w.run(3)
ana.touch("t12 shape", hold=0.1); w.run(0.5)
if ana.dialog: ana.click("Close") if "Close" in ana.labels() else None
w.run(2.5)
check(var(h, "strip", "gFaded") == 0, "touched at 3 s: still there 3 s later")
w.run(3)
check(var(h, "strip", "gFaded") == 1, "... then it fades")

# ---- /12 fade off: it stays -------------------------------------------------------------------------------------------------
ana.say(12, "fade off"); w.run(1)
check(var(h, "strip", "gFaded") == 0 and lsd(h, "fade") == "0", "/12 fade off: back, and kept")
w.run(12)
check(var(h, "strip", "gFaded") == 0 and len(visible(h, ana)) >= 8, "... it stays")
ana.say(12, "fade on"); w.run(6)
check(var(h, "strip", "gFaded") == 1, "/12 fade on: it fades again")

# ---- a note on its plate, under the [12] ------------------------------------------------------------------------------------
h.send(7344, "kept|")                                                # "Kept." (Fixed's note)
w.run(0.5)
plate, note, r12 = rect(h, ana, "t12 plate"), rect(h, ana, "t12 note"), rect(h, ana, "Take 12")
text = h.part("t12 note")["text"]
check(text != "" and plate[4] > 0.5 and plate[2] > 0.0101, "a note: its plate shows (%r, %r)" % (text, plate))
check(abs((plate[0] - plate[2] / 2) - (r12[0] - r12[2] / 2)) < 2 / 1080.0, "... from the [12]'s left edge")
check(plate[1] + plate[3] / 2 < r12[1] - r12[3] / 2, "... under the [12]")
check(abs(plate[2] - (len(text) * 7.2 + 28) / 1080.0) < 1e-3, "... as wide as its text (%.0f px for %d characters)" % (plate[2] * 1080, len(text)))
check(abs(note[0] - plate[0]) < 1e-4, "... the text in the plate's middle")
w.run(12)
check(h.part("t12 note")["text"] == "" and rect(h, ana, "t12 plate")[2] <= 0.0101, "the note gone: its plate too")
no_errors(w, "fade")
done("fade_emu")
