"""Connect that never stays dead, and never says "nobody" with a friend beside you (8.5.0), on the REAL scripts.
In-world, sync stopped with "Stack-Heap Collision" after a few minutes beside a friend, and Connect said "Nobody near
you wears Take 12." with the friend next to you (a stopped sync never answers: nobody is near). Now:
  - carry's watchdog starts a stopped script again within 5 s; sync, started again while worn, rejoins the ones it was
    with at once; /12 status names what was started again;
  - two Take 12s know each other within a second of meeting (a "here" from someone new is answered), so Connect
    lists a friend who has just put the HUD on, not at the next 10 s "here";
  - Connect's dialogs (now carry's) and Settings › Friends work as before."""
from emu_util import *
from connect_emu import setup, peers, S

# ---- sync stops while two friends are connected --------------------------------------------------------------------------
w, (ana, ben) = setup()
for a, b in ((ana, ben), (ben, ana)): a.hud.lsd["cin.friends"] = ("%s,%s Resident" % (b.key, b.name), PASS)
w.run(12)
check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "two friends near: connected by themselves (%r, %r)" % (peers(ana), peers(ben)))
ana.hud.crash("sync")
w.run(1)
check(not var(ana.hud, "carry", "gRe"), "(not started again yet)")
w.run(6)
check(any(x.name == "sync" and not getattr(x, "stopped", False) for x in ana.hud.scripts), "Ana's sync is running again within 5 s")
check(var(ana.hud, "carry", "gRe").split() == ["sync"], "carry notes it: %r" % var(ana.hud, "carry", "gRe"))
w.run(3)
check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "... and Ana and Ben are connected again (%r, %r)" % (peers(ana), peers(ben)))
t = w.t
ana.say(12, "status"); w.run(1)
check(any("[Take 12/carry]" in m and "started again: sync" in m for (_, _, m) in ana.chat if True), "/12 status names it")
check(any("[Take 12/sync]" in m and "heard near: Ben" in m for (_, _, m) in ana.chat), "/12 status: who sync heard near")

# any script: a stopped portrait starts again too, fresh
ana.hud.crash("portrait"); w.run(6)
check(var(ana.hud, "carry", "gRe").split() == ["sync", "portrait"], "a stopped portrait is started again (%r)" % var(ana.hud, "carry", "gRe"))
no_errors(w, "the watchdog")

# ---- a friend puts the HUD on: Connect lists them at once ------------------------------------------------------------------
w = World(seed=3)
ana = w.avatar("Ana", (128, 128, 21)); ana.fov = 0.6125
ana.wear(HUD_SCRIPTS, lsd=ready(ana)); w.run(0.5); manual(ana.hud); w.run(20)
ben = w.avatar("Ben", (130, 128, 21)); ben.fov = 0.6125
ben.wear(HUD_SCRIPTS, lsd=ready(ben)); w.run(0.5); manual(ben.hud); w.run(1.5)    # Ben's first "here", 1 s after wearing
check(any(S(ana)["gNear"][i] == ben.key for i in range(0, len(S(ana)["gNear"]), 4)), "Ana heard Ben's HUD at once")
check(any(S(ben)["gNear"][i] == ana.key for i in range(0, len(S(ben)["gNear"]), 4)), "... and Ben knows Ana at once (she answered his \"here\")")
t = w.t
ana.say(12, "connect"); w.run(0.3); ana.click("Invite"); w.run(0.5)      # alone: the Connect page, then Invite (8.6.0)
check(ana.dialog and any(x.startswith("Ben") for x in ana.labels()), "Connect lists Ben at once (%r, notes %r)" % (ana.dialog and ana.labels(), ana.notes(t)))
check(not any("Nobody" in n for n in ana.notes(t)), "never \"Nobody near you\" (%r)" % ana.notes(t))
ana.click([x for x in ana.labels() if x.startswith("Ben")][0]); w.run(1)
check(ben.dialog and "share films" in ben.dialog[1], "Ben is asked (%r)" % (ben.dialog,))
ben.click("Yes"); w.run(2)
check(peers(ana) == ["Ben"] and peers(ben) == ["Ana"], "connected (%r, %r)" % (peers(ana), peers(ben)))

# an ask left unanswered: a quiet "no" after a minute (carry's dialog closes)
cid = w.avatar("Cid", (129, 130, 21)); cid.fov = 0.6125
cid.wear(HUD_SCRIPTS, lsd=ready(cid)); w.run(0.5); manual(cid.hud); w.run(3)
t = w.t
cid.say(12, "connect"); w.run(0.3); cid.click("Invite"); w.run(1)
cid.click([x for x in cid.labels() if x.startswith("Ana")][0]); w.run(1)
check(ana.dialog and "Cid wants to share films" in ana.dialog[1], "Ana is asked by Cid")
w.run(66)
check(S(ana)["gAsk"] == C["NULL_KEY"] and "Cid" not in peers(ana), "unanswered: Ana's sync lets the ask go")
check(any("Ana didn't answer" in n or "didn" in n for n in cid.notes(t)), "Cid hears no answer (%r)" % cid.notes(t))

# Settings › Friends (now carry's): add Ben, the list, remove him
ana.hud.lsd.pop("cin.friends", None)
ana.say(12, "connect|friends") if False else ana.hud.send(7371, "connect|friends"); w.run(1)
check(ana.dialog and "None yet." in ana.dialog[1] and "Add" in ana.labels(), "Settings › Friends: none yet (%r)" % (ana.dialog,))
ana.click("Add"); w.run(4)
check(any(x.startswith("Ben") for x in ana.labels()), "Add lists Ben, connected (%r)" % ana.labels())
ana.click([x for x in ana.labels() if x.startswith("Ben")][0]); w.run(1)
check(str(ben.key) in lsd(ana.hud, "friends"), "Ben is Ana's friend (%r)" % lsd(ana.hud, "friends"))
ana.hud.send(7371, "connect|friends"); w.run(1)
check("Ben" in ana.dialog[1], "the list names him (%r)" % ana.dialog[1])
ana.click("Remove"); w.run(1)
ana.click([x for x in ana.labels() if x.startswith("Ben")][0]); w.run(1)
check(lsd(ana.hud, "friends") == "", "removed (%r)" % lsd(ana.hud, "friends"))
no_errors(w, "meeting")
done("watchdog_emu")
