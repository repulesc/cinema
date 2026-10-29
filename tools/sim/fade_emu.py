"""The strip stays (8.5.3: the 8.5.0 fade, 4 s after the last touch, is gone: it hid the strip while you worked), on the
REAL scripts. A double-tap on the [12] hides it, the [12] stays whole; another brings it back; a tap is always the menu.
A note sits under the [12] on a dark plate sized to its text."""
from emu_util import *

w = World()
ana = w.avatar("Ana", (128, 128, 21))
h = ana.wear(HUD_SCRIPTS, lsd=ready(ana))
textures(h)
w.run(0.5); manual(h); w.run(4.5)
ana.double_tap(); w.run(1)
check(var(h, "strip", "gOpen") == 1 and len(visible(h, ana)) >= 8, "the strip open")
root = h.prims[0]

# ---- untouched, it stays -------------------------------------------------------------------------------------------------
w.run(30)
check(var(h, "strip", "gOpen") == 1 and len(visible(h, ana)) >= 8, "30 s untouched: the strip still there (%r)" % sorted(visible(h, ana)))
check(abs(root["alpha"] - 1.0) < 0.01, "... the [12] whole")
ana.dialog = None
ana.tap(); w.run(0.8)
check(ana.dialog is not None, "a tap: the menu, at once")
ana.click("Close"); w.run(0.5)

# ---- a double-tap hides it, another brings it back ------------------------------------------------------------------------
ana.double_tap(); w.run(1)
check(var(h, "strip", "gOpen") == 0 and visible(h, ana) == {}, "a double-tap: the strip hidden (%r)" % sorted(visible(h, ana)))
check(abs(root["alpha"] - 1.0) < 0.01, "... the [12] stays, whole")
w.run(10)
check(var(h, "strip", "gOpen") == 0, "... and stays hidden")
ana.double_tap(); w.run(1)
check(var(h, "strip", "gOpen") == 1 and len(visible(h, ana)) >= 8, "another double-tap: back")

# ---- a note on its plate, under the [12] ------------------------------------------------------------------------------------
h.send(7344, "kept|")                                                # "Kept." (Fixed's note)
w.run(0.5)
plate, note, r12 = rect(h, ana, "t12 plate"), rect(h, ana, "t12 note"), rect(h, ana, "Take 12")
text = h.part("t12 note")["text"]
check(text != "" and plate[4] > 0.5 and plate[2] > 0.0101, "a note: its plate shows (%r, %r)" % (text, plate))
check(abs(plate[0] - r12[0]) < 1e-4, "... centred under the [12] (8.5.2)")
check(plate[1] + plate[3] / 2 < r12[1] - r12[3] / 2, "... under the [12]")
check(abs(plate[2] - (len(text) * 7.2 + 28) / 1080.0) < 1e-3, "... as wide as its text (%.0f px for %d characters)" % (plate[2] * 1080, len(text)))
check(abs(note[0] - plate[0]) < 1e-4, "... the text in the plate's middle")
w.run(12)
check(h.part("t12 note")["text"] == "" and rect(h, ana, "t12 plate")[2] <= 0.0101, "the note gone: its plate too")
no_errors(w, "fade")
done("fade_emu")
