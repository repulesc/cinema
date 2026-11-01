"""Auto while you are awake (8.9.2), on the REAL scripts. In-world: standing and clicking things, typing or turning, and
Auto cut to Drift after 10 s or to Portrait after 4 s, because only walking counted ("it dreams while I am awake").
Now tracking hears your clicks in the world and the turning keys (taken and passed on: they work as ever) and sees you
type: Drift waits for 60 s of nothing at all, Portrait with someone for 15 s with your hands still (typing is a
conversation: it may), and a click, a turn or typing while Auto rests takes you back behind you at once.
    python3 tools/sim/awake_emu.py [lab]"""
import sys
from emu_util import *

LB = C["CONTROL_LBUTTON"]
S, P = (LAB_SCRIPTS, LAB_PARTS) if sys.argv[1:2] == ["lab"] else (HUD_SCRIPTS, PARTS)

def until(w, cond, limit):
    t = 0.0
    while t < limit:
        if cond(): return t
        w.run(0.25); t += 0.25
    return t if cond() else None

w = World()
ana = w.avatar("Ana", (128, 128, 21))
h = ana.wear(S, parts=P, lsd=ready(ana)); textures(h)
w.run(5)
check(var(h, "tracking", "gAuto") == 1 and state(h) == ("film", "tracking"), "worn: Auto, Tracking")
check(var(h, "tracking", "gOwner") and next(x for x in h.scripts if x.name == "tracking").ctl[0] & LB, "tracking hears a click (taken, passed on)")
check(next(x for x in h.scripts if x.name == "tracking").ctl[2], "... passed on: clicking works as ever")

# standing, clicking things now and then: no Drift
for i in range(12):
    ana.keys(LB, hold=0.1); w.run(5)
check(state(h)[1] == "tracking", "a minute standing and clicking: Tracking, no Drift (%s)" % state(h)[1])
# typing alone: no Drift either
ana.typing = True; w.run(80); ana.typing = False
check(state(h)[1] == "tracking", "80 s typing: still Tracking (%s)" % state(h)[1])
# nothing at all: Drift after 60 s, not before
w.run(50)
check(state(h)[1] == "tracking", "50 s of nothing: not yet")
t = until(w, lambda: state(h)[1] == "scenic", 15)
check(t is not None, "60 s of nothing at all: Drift")
w.run(10)
ana.keys(LB, hold=0.1)
t = until(w, lambda: state(h)[1] == "tracking", 2)
check(t is not None, "a click while Auto rests: back behind you at once (%s)" % t)
w.run(10)
ana.keys(C["CONTROL_ROT_LEFT"], hold=0.3)
w.run(55)
check(state(h)[1] == "tracking", "a turn counts as here too")
t = until(w, lambda: state(h)[1] == "scenic", 15)
ana.typing = True
t = until(w, lambda: state(h)[1] == "tracking", 2)
check(t is not None, "typing while Auto rests: back behind you")
ana.typing = False
no_errors(w, "alone")

# with someone: clicking holds Tracking; still hands (typing is fine: a conversation) give Portrait after 6 s
ben = w.avatar("Ben", B.add(ana.pos, vec(1.5, 0.5, 0)))
w.run(1)
for i in range(10):
    ana.keys(LB, hold=0.1); last = w.t; w.run(6)
check(state(h)[1] == "tracking", "Ben near, Ana busy clicking: Tracking (%s)" % state(h)[1])
ana.typing = True
t = until(w, lambda: state(h)[1] == "portrait", 20)
check(t is not None and w.t - last >= 14.5, "hands still, typing to Ben: Portrait 15 s after the last click (%.1f s)" % (w.t - last))
ana.typing = False
no_errors(w, "with Ben")
done("awake_emu")
