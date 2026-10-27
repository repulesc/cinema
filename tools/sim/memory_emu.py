"""Runtime memory on the REAL scripts (8.0.1). 8.0.0's screen.lsl died in-world with "Stack-Heap Collision": it built
one 464-element list for the whole strip, while tools/lslcheck.sh only measured the code. Here every script runs its
heaviest paths (the strip open at every size and place, every shot and option, Connect with three people, a crowd of
90 avatars, seat memory full and then reset, carry-over with a full setup, a 7.x migration) while the emulator notes
the biggest list each one builds. For every script: the static estimate (tools/lslmem.py) + its globals + twice the
biggest list (`+=` keeps the old copy while it builds the new one) must leave 3 KB of the 64 KB."""
from emu_util import *
import world
from lslmem import LIMIT
from world import Obj, new_key

MARGIN = 3 * 1024
seen = {}                                   # script name -> (free bytes, peak bytes, where, globals)

def note(h):
    for sc in h.scripts:
        free = LIMIT - world.static(sc.prog.path) - sc.globals_bytes() - 2 * sc.peak
        old = seen.get(sc.name)
        if old is None or free < old[0]: seen[sc.name] = (free, sc.peak, sc.peak_at, sc.globals_bytes())

def full_lsd(av):
    """a setup at its limits: 48 pieces of furniture (4 spots each), 20 places, 20 vehicles, 20 friends, the tips"""
    d = dict(ready(av))
    spot = "<1.23,-0.45,0.67>|<2.34,1.56,0.78>|<0.10,-0.50,0.60>|-135|1.047"
    seats = []
    for i in range(48):
        k = "%08x-0000-4000-8000-0000000000%02x" % (0xabc000 + i, i)
        seats.append(k)
        d["cin.seat." + k] = ("~".join([spot] * 4), PASS)
    d["cin.seats"] = (",".join(seats), PASS)
    places = ["Region_Number_%02d.%08x" % (i, i) for i in range(20)]
    for p in places:
        d["cin.view." + p] = ("~".join(["<101.25,102.50,23.75>|<104.00,105.25,22.50>|<103.00,104.00,22.00>|90|1.047"] * 6), PASS)
    d["cin.places"] = (",".join(places), PASS)
    d["cin.veh"] = (";".join("Some Long Vehicle Name %02d|%s" % (i, new_key()) for i in range(20)), PASS)
    d["cin.friends"] = (";".join("%s,Friend Number%02d Resident" % (new_key(), i) for i in range(20)), PASS)
    d["cin.tips"] = (";".join("%s:3" % w for w in ("TRACKING", "PORTRAIT", "FIXED", "SCENIC", "CLOSE", "ME", "SHOULDER", "L", "VIEW A", "FORGET SEAT", "DRIFT", "shape", "link", "kept", "flying", "snapshot")), PASS)
    return d

# ---- the strip, every shot and option, every place and size --------------------------------------------------------------
w = World()
ana, h = hud(w)
textures(h); w.run(1)
ana.double_tap(); w.run(1)
for shot in ("t12 s0", "t12 s1", "t12 s2", "t12 s3"):
    ana.touch(shot); w.run(3)
    for wd in list(var(h, "screen", "gOptVis")):
        if wd in var(h, "screen", "gOptVis"): ana.touch(opt_part(h, wd)); w.run(1.5)
h.send(7342, "theirs|3|Ben"); w.run(1)
for a in (1.25, 1.778, 3.556):
    ana.aspect = a
    for pl, sz in (("top", "l"), ("bot", "s"), ("both", "m")):
        ana.say(12, "place " + pl); ana.say(12, "size " + sz); w.run(2.5)
ana.double_tap(); w.run(1); ana.double_tap(); w.run(1)
ana.long_press(); w.run(2); ana.long_press(); w.run(3)
note(h); no_errors(w, "strip")

# ---- Connect with three ----------------------------------------------------------------------------------------------------------
w2 = World()
avs = []
for i, n in enumerate(("Ana", "Ben", "Cy")):
    a = w2.avatar(n, (128 + 2 * i, 128, 21)); a.wear(HUD_SCRIPTS, lsd=ready(a)); avs.append(a)
w2.run(5)
for b in avs[1:]:
    avs[0].say(12, "connect"); w2.run(2.5)
    if "Invite" in avs[0].labels(): avs[0].click("Invite"); w2.run(2.5)
    nm = [x for x in avs[0].labels() if x.startswith(b.name)]
    if nm:
        avs[0].click(nm[0]); w2.run(1)
        if b.dialog: b.click("Yes"); w2.run(2)
for a in avs: a.say(12, "portrait")
w2.run(4)
avs[1].touch("t12 link"); w2.run(2)
if avs[1].dialog and "Ana" in avs[1].labels(): avs[1].click("Ana")
w2.run(20)
for a in avs: note(a.hud)
no_errors(w2, "connect")

# ---- a crowd of 90: Portrait Us and Scenic Drift ----------------------------------------------------------------------------
w3 = World()
amy, h3 = hud(w3, "Amy")
import random
r = random.Random(3)
for i in range(90):
    d = 1.5 + (i % 20) * 1.4 if i < 40 else r.uniform(12, 60)
    a = r.uniform(0, 6.283)
    w3.avatar("Crowd%02d" % i, (128 + d * math.cos(a), 128 + d * math.sin(a), 21))
amy.say(12, "portrait"); w3.run(3)
amy.double_tap(); w3.run(1)
amy.touch(opt_part(h3, "US")); w3.run(8)
amy.say(12, "scenic"); w3.run(40)
note(h3); no_errors(w3, "crowd")

# ---- seat memory full, then a new seat, then Reset › Seats & views; carry-over; a 7.x migration ------------------------
w4 = World()
bo = w4.avatar("Bo", (128, 128, 21))
h4 = bo.wear(HUD_SCRIPTS, lsd=full_lsd(bo)); w4.run(5)
bo.say(12, "fixed"); w4.run(3)
chair = w4.furniture("Chair", (130, 128, 20.5))
bo.sit_on(chair); w4.run(3.5)
bo.alt_orbit(to=vec(132, 127, 22), focus=B.add(bo.pos, vec(0, 0, 0.6))); w4.run(2.5); bo.esc(); w4.run(1)
check(len(lsd(h4, "seats").split(",")) == 48, "the seat index stays at 48")
bo.stand(); w4.run(2)
new = bo.wear(HUD_SCRIPTS); w4.run(30)                               # a fresh copy: the full setup is carried over
check(lsd(new, "seats") == lsd(h4, "seats"), "carried over in full")
note(h4); note(new)
bo.take_off(h4); w4.run(1)
bo.tap(); w4.run(0.6); bo.click("Settings"); w4.run(0.5); bo.click("Reset"); w4.run(0.5); bo.click("Seats & views"); w4.run(1)
check(not [k for k in new.lsd if k.startswith(("cin.seat", "cin.view", "cin.places"))], "Seats & views: all gone")
note(new); no_errors(w4, "seats")
w5 = World()
cy = w5.avatar("Cy", (128, 128, 21))
old = {"cin.owner": (str(cy.key), PASS), "cin.ver": ("7.2.0", PASS), "cin.friends": ("%s,Ana Resident" % new_key(), PASS)}
for i in range(120): old["cin.fitc.%s@%d:%d" % (new_key(), i, i)] = ("0.125000", PASS)
h5 = cy.wear(HUD_SCRIPTS, lsd=old); w5.run(6)
check(not [k for k in h5.lsd if "fitc" in k] and lsd(h5, "friends"), "7.x settings migrated (friends kept)")
note(h5); no_errors(w5, "migration")

# ---- the verdict ---------------------------------------------------------------------------------------------------------------------
print("%-9s %9s %9s %9s  %s" % ("script", "free KB", "peak KB", "globals", "where the biggest list was built"))
for n, (free, peak, at, gl) in sorted(seen.items(), key=lambda x: x[1][0]):
    print("%-9s %9.1f %9.1f %9.1f  %s" % (n, free / 1024, peak / 1024, gl / 1024, at))
    check(free >= MARGIN, "%s: only %.1f KB left at its peak (a list of %.1f KB in %s)" % (n, free / 1024, peak / 1024, at))
done("memory_emu")
