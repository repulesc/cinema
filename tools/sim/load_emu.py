"""The HUD's load on the sim (8.9.1), on the REAL scripts (the new design, lab/src, and the product). Every link message
wakes all twelve scripts, so the messages sent often are what costs: Drift's every step (once a second) sent core's
camera to all twelve for nobody (CAMSET, only sync needs it, and only while someone watches you). This counts events and
link messages in each kind of shot and checks they stay under a ceiling; and the basic shot (core's, now bars') still
comes when a shot's script is silent or Scenic finds no view, in the free build too.
    python3 tools/sim/load_emu.py"""
import collections
from emu_util import *
import world as W

count = collections.Counter()
_run = W.Obj._run
def run(o, sc, name, args, detected, gen):
    if gen == sc.timer_gen and not getattr(sc, "dead", False) and not getattr(sc, "stopped", False) and (o.worn or o.rezzed):
        count[("ev", o.owner.name)] += 1
    return _run(o, sc, name, args, detected, gen)
W.Obj._run = run
_lm = W.Obj.llMessageLinked
def lm(o, sc, link, num, msg, k):
    count[("lm", o.owner.name, sc.name, num)] += 1
    return _lm(o, sc, link, num, msg, k)
W.Obj.llMessageLinked = lm

def measure(w, av, secs):
    count.clear()
    w.run(secs)
    ev = count[("ev", av.name)] / secs
    msgs = sum(v for k, v in count.items() if k[0] == "lm" and k[1] == av.name) / secs
    camset = sum(v for k, v in count.items() if k[0] == "lm" and k[1] == av.name and k[2] == "core" and k[3] == 7325) / secs
    return ev, msgs, camset

for label, scripts, parts in (("the new design", LAB_SCRIPTS, LAB_PARTS), ("the product", HUD_SCRIPTS, PARTS)):
    w = World(seed=5)
    ana = w.avatar("Ana", (128, 128, 21)); ana.fov = 0.6125
    ana.wear(scripts, parts=parts, lsd=ready(ana)); w.run(0.5); manual(ana.hud); w.run(5)
    ana.double_tap(); w.run(2)
    ev, msgs, cs = measure(w, ana, 20)
    check(ev < 7.0 and msgs < 0.2, "%s, waiting: %.1f events and %.2f link messages a second" % (label, ev, msgs))
    ana.hud.send(7371, "shot|scenic"); w.run(4)
    ev, msgs, cs = measure(w, ana, 40)
    print("%s, Drift: %.1f events, %.2f link messages, core's camera %.2f a second" % (label, ev, msgs, cs))
    check(cs < 0.1 and msgs < 2.2 and ev < 36, "%s, Scenic's Drift: core's camera to nobody %.2f a second (8.9.0: 1.7), %.1f link messages, %.1f events a second" % (label, cs, msgs, ev))
    ana.hud.send(7371, "shot|tracking"); w.run(4)
    ana.walk((150, 128, 21), speed=1.5)
    ev, msgs, cs = measure(w, ana, 15)
    check(cs < 0.1 and ev < 20, "%s, Tracking walking: %.1f events a second, core's camera %.2f" % (label, ev, cs))
    no_errors(w, label)

# ---- the basic shot (bars, 8.9.1; core's before): a shot's script silent, or Scenic finding no view ----------------------
for label, scripts, parts, shot in (("the product", HUD_SCRIPTS, PARTS, "portrait"), ("the free build", FREE_SCRIPTS, PARTS, "scenic")):
    w = World(seed=7)
    bo = w.avatar("Bo", (128, 128, 21)); bo.fov = 0.6125
    h = bo.wear(scripts, parts=parts, lsd=ready(bo)); w.run(0.5); manual(h); w.run(5)
    h.crash(shot); h.crash("carry")                      # silent, and nobody starts it again
    h.send(7371, "shot|" + shot); w.run(3.5)
    c = bo.camera()
    eye = bo.pos[2] + 0.37 * bo.size[2]
    d = B.llVecDist(c[0], bo.pos)
    check(h.cam.get("active") and 1.1 < d < 3.5 and abs(c[1][2] - c[0][2]) < 0.01 and abs(c[0][2] - eye) < 0.05,
          "%s, %s silent: the basic shot, level at eye height, %.1f m from you" % (label, shot, d))
    no_errors(w, label + " basic")
done("load_emu")
