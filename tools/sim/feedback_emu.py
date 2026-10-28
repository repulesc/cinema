"""Feedback by email (8.0.10), on the REAL scripts: the main dialog's Feedback and /12 feedback open a text box; what
you write goes to the maker (panocarver@gmail.com) with one plain line about the copy; an empty box sends nothing; one
a minute and ten a day; the free build sends it too; the camera keeps filming."""
from emu_util import *
import re, os
VER = re.search(r'string VERSION = "([^"]+)"', open(os.path.join(os.path.dirname(__file__), "..", "..", "hud", "src", "carry.lsl")).read()).group(1)

w = World()
ana, h = hud(w)
ana.double_tap(); w.run(1); ana.touch("t12 s1"); w.run(3)                # Portrait
ana.dialog = None
ana.tap(); w.run(0.6)
check(var(h, "ui", "gBtn") == ["Connect", "Settings", "Help", "Feedback", "Close"], "the main dialog has Feedback (%r)" % var(h, "ui", "gBtn"))
ana.click("Feedback"); w.run(0.5)
check(ana.dialog and ana.dialog[2] == ["<text>"] and "goes to the maker" in ana.dialog[1], "Feedback: a text box that says where it goes")
t = w.t
ana.type("Portrait cut my head in the club."); w.run(1)
check(len(w.emails) == 1, "one email (%d)" % len(w.emails))
_, sc, to, subj, body = w.emails[0]
check(to == "panocarver@gmail.com" and sc == "carry", "to the maker, from carry (%s, %s)" % (to, sc))
check(subj == "Take 12 feedback · Ana Resident · " + VER, "the subject: %r" % subj)
check(body.startswith("Portrait cut my head in the club.\n\n"), "their words first")
line = body.split("\n\n", 1)[1]
for part in ("Ana Resident", VER, "Portrait · frame 1.85", "lens 35 mm"):
    check(part in line, "the line has %r: %r" % (part, line))
check(any(n.startswith("Thanks. It went to the maker") for n in ana.notes(t)), "a note thanks them")
check(state(h) == ("film", "portrait"), "Portrait still filming (%r)" % (state(h),))

ana.say(12, "feedback"); w.run(0.5)
check(ana.dialog is None and any("One a minute" in n for n in ana.notes(w.t - 0.5)), "again within a minute: not yet")
w.run(61)
ana.say(12, "feedback"); w.run(0.5)
check(ana.dialog and ana.dialog[2] == ["<text>"], "/12 feedback a minute later: the text box")
ana.type("   "); w.run(1)
check(len(w.emails) == 1, "an empty box sends nothing")
for i in range(12):
    ana.say(12, "feedback"); w.run(0.5)
    if ana.dialog and ana.dialog[2] == ["<text>"]: ana.type("note %d" % i)
    w.run(61)
check(len(w.emails) == 10, "ten a day (%d)" % len(w.emails))
no_errors(w, "feedback")

# ---- the free build sends it too -----------------------------------------------------------------------------------------
w = World()
bo, hb = hud(w, "Bo", scripts=FREE_SCRIPTS)
bo.say(12, "feedback"); w.run(0.5)
bo.type("Lovely views."); w.run(1)
check(len(w.emails) == 1 and w.emails[0][3].startswith("Take 12 Scenery feedback"), "the free build: %r" % [e[3] for e in w.emails])
no_errors(w, "free feedback")
done("feedback_emu")
