"""What the first in-world test of 8.0.2 ran into, on the REAL scripts (8.0.3):
- a tap on the [12] landed on its ring (in front of the disc) or on a part parked behind it, and was lost: you had to tap
  again and again;
- the eye-line check (the setup) held the camera in front of you: walking, a teleport and a script reset left it there.
Now every tap on the [12] counts, walking or a teleport ends the eye line (the old line is kept), it ends by itself
after 2 minutes, a reset never leaves the camera locked, and a dialog answered late still works.
And what the first real session of 8.0.3 showed (8.0.4): the lit words read cleanly (no ink on a white box, no grey
block under them: thin sliced lines, no glow), the strip sits flush at the top on a solid black band, Portrait among
bushes looks round for room instead of standing 1 m from you (and never cuts the head), no camera call while not worn or
while Tracking walks into the next region, and the setup leaves the strip open.
And the second session (8.0.5): Portrait framed every picture for a 60° lens (it never asked for the permission that
reads your zoom: at 38 mm the camera stood 1.8 times too close, the head out of the top), an eye line above 1.0 (a mesh
body, hover height) was thrown away, notes sat right under the [12] and went in 3 s, the eye line's instruction went
before you could read it, Room stayed dim after walking into a room, and the strip started hidden on every wear.
And the tests with a friend (8.0.6): Room composes from the room's edge, level; the outline hint explains itself; the
[12] sits inside the band; Settings › Friends works (now sync's); Settings › Tracking › Snappy; the setup asks whether
the strip is in view; once asked, the setup never starts again on a re-wear."""
from emu_util import *

w = World()
ana = w.avatar("Ana", (128, 128, 21))
h = ana.wear(HUD_SCRIPTS)
w.run(5)

# ---- every tap on the [12] counts ----------------------------------------------------------------------------------
for part in ("t12 ring", "t12 dot", "t12 s0", "t12 band", "t12 bar0"):
    ana.dialog = None
    ana.touch(part); w.run(0.8)
    check(ana.dialog is not None, "a tap on the [12] that lands on %s opens the dialog" % part)
    if ana.dialog and ana.labels() == ["Start", "Later"]: ana.click("Later"); w.run(0.5)
ana.dialog = None
ana.touch("t12 ring"); w.run(0.1); ana.touch("t12 s1"); w.run(0.6)
check(var(h, "strip", "gOpen") == 1, "a double-tap across the ring and a parked part opens the strip")
ana.touch("t12 s1"); w.run(0.6)
check(var(h, "strip", "gOpen") == 1 and ana.dialog is None, "an open strip's word is the word, not the [12]")
check(var(h, "core", "gShot") == "portrait", "... it starts Portrait")
h.send(7371, "stop"); w.run(0.5)                                       # back to your own camera for what follows
ana.double_tap(); w.run(0.6)
check(var(h, "strip", "gOpen") == 0, "the strip closes")
no_errors(w, "taps")


def eye_line():
    ana.dialog = None
    ana.tap(); w.run(0.6)
    if ana.labels() == ["Start", "Later"]:
        ana.click("Start"); w.run(0.5)
        ana.click("Skip"); w.run(0.5)
    else:
        ana.click("Settings"); w.run(0.5)
        ana.click("Eye line"); w.run(0.5)
    cam, foc, scripted = ana.camera()
    check(scripted and var(h, "core", "gEyeOn"), "the eye line holds the camera in front of you")


def free(why):
    cam, foc, scripted = ana.camera()
    check(not scripted, "%s: your camera again, not locked" % why)
    check(not var(h, "core", "gEyeOn") and not var(h, "ui", "gEye"), "%s: the eye line has ended" % why)
    check(rect(h, ana, "t12 u2")[4] < 0.02 or var(h, "strip", "gOpen"), "%s: the line is off the screen" % why)


# ---- walking ends the eye line (the setup goes on) ------------------------------------------------------------------
eye0 = lsd(h, "eye")
eye_line()
ana.keys(C["CONTROL_FWD"], hold=0.5); w.run(1.0)
free("walking")
check(lsd(h, "eye") == eye0, "walking: the old eye line is kept")
check(ana.labels() == ["Smaller", "Good", "Larger"], "walking: the setup goes on to the size: %r" % ana.labels())
ana.click("Good"); w.run(0.5)
ana.click("Yes"); w.run(0.5)
for p in ("Next ›", "Next ›", "Done"): ana.click(p); w.run(0.5)
check(lsd(h, "firstrun") == "done", "the setup is done")

# ---- turning (the arrow keys) ends it too; a teleport; 2 minutes --------------------------------------------------------
eye_line()
ana.keys(C["CONTROL_ROT_LEFT"], hold=0.3); w.run(0.6)
free("turning")
eye_line()
ana.teleport((60, 60, 30), region="Elsewhere"); w.run(3)
free("a teleport")
eye_line()
w.run(119)
check(ana.camera()[2], "the eye line waits while you look")
w.run(3)
free("two minutes")
eye_line()
ana.keys(C["CONTROL_UP"], hold=0.3); w.run(0.5)
check(var(h, "core", "gEyeOn"), "PgUp moves the line, it does not end it")
ana.tap(); w.run(0.6)
free("kept with a tap")
no_errors(w, "eye line")

# ---- a script reset never leaves the camera locked ------------------------------------------------------------------
eye_line()
for sc in h.scripts:
    if sc.name in ("core", "ui"): h.reset(sc)
w.run(3)
check(not ana.camera()[2], "core and ui reset during the eye line: the camera is yours again")
no_errors(w, "reset")

# ---- a dialog answered late still works -----------------------------------------------------------------------------
ana.dialog = None
ana.tap(); w.run(0.6)
w.run(300)
ana.click("Settings"); w.run(0.5)
check("Eye line" in ana.labels(), "a dialog answered after 5 minutes: %r" % ana.labels())
no_errors(w, "late")

# ==== 8.0.4 =========================================================================================================
w = World()
ana, h = hud(w)
ana.face(90)
ana.double_tap(); w.run(1)
ana.touch("t12 s1"); w.run(3)                                          # Portrait, Medium · Me
P = lambda n: h.part(n)
word = rect(h, ana, "t12 s1")

# ---- the lit words read cleanly ---------------------------------------------------------------------------------------
check(P("t12 s1")["color"] == vec(1, 1, 1) and P("t12 s1")["alpha"] > 0.95, "the lit shot: white, full (not ink on a box)")
line = rect(h, ana, "t12 box")
sl = P("t12 box")["slice"]
check(str(P("t12 box")["tex"][0]) == C["TEXTURE_BLANK"] and (sl[1] - sl[0]) * 0.01 * 1080 < 3.5, "the lit shot's underline: a thin blank line (%r)" % (sl,))
check(abs(line[0] - word[0]) < 1e-3 and line[1] < word[1] - 0.007 and line[4] > 0.5, "... under its word (%.4f, %.4f)" % (line[1], word[1]))
lit = [x for x, st in zip(var(h, "strip", "gOpts"), var(h, "strip", "gOptSt")) if st == "lit"]
for i, n in enumerate(("t12 u0", "t12 u1")):
    sl = P(n)["slice"]
    check(P(n)["alpha"] > 0.5 and (sl[1] - sl[0]) * 0.01 * 1080 < 3.5 and str(P(n)["tex"][0]) == C["TEXTURE_BLANK"],
          "a lit option's underline is a thin line, not a 0.01 m textured block (%s %r)" % (n, sl))
for p in h.prims:
    check(p["glow"] == 0.0 or p["name"] in ("t12 dot",), "no glow on the strip (%s: %.2f)" % (p["name"], p["glow"]))

# ---- flush at the top, on a solid black band ------------------------------------------------------------------------------
band = rect(h, ana, "t12 band")
check(abs(band[1] + band[3] / 2 - 0.5) < 1e-3, "the band reaches the top edge (%.4f)" % (band[1] + band[3] / 2))
check(abs(band[3] - 48 / 1080.0) < 1e-3, "the band is the strip's height (%.1f px)" % (band[3] * 1080))
check(P("t12 band")["color"] == vec(0, 0, 0) and band[4] > 0.99 and str(P("t12 band")["tex"][0]) == C["TEXTURE_BLANK"], "the band: solid black")
root = rect(h, ana, "Take 12")
check(abs(root[1] - (0.5 - 24 / 1080.0)) < 1e-3, "the [12] in the band's middle, no gap above (%.4f)" % root[1])
no_errors(w, "look")

# ---- Portrait among bushes: it looks round for room ------------------------------------------------------------------------
def dist():
    c = h.cam["pos"]
    return B.llVecDist(vec(c[0], c[1], 0), vec(ana.pos[0], ana.pos[1], 0))
def head_in():
    top = vec(ana.pos[0], ana.pos[1], ana.pos[2] + 0.5 * ana.size[2])
    r = project(ana, top)
    return r is not None and r[1] < 0.5
d0 = dist()
bushes = []
for dx in (-0.5, 0.5):                                               # right where both 3/4 views would stand
    b = Box((ana.pos[0] + dx - 0.3, ana.pos[1] + 0.87 - 0.3, ana.pos[2] - 1, ana.pos[0] + dx + 0.3, ana.pos[1] + 0.87 + 0.3, ana.pos[2] + 1.5), "bush")
    w.boxes.append(b); bushes.append(b)
ana.touch("t12 s1"); w.run(2)
check(dist() > 0.9 * d0, "bushes on both 3/4 sides: another angle with room (%.2f m, open %.2f m)" % (dist(), d0))
check(head_in(), "... the head in the picture")
ana.touch(opt_part(h, "WIDE")); w.run(2)
check(dist() > 1.5 and head_in(), "Wide among the bushes: the whole of you (%.2f m)" % dist())
for b in bushes: w.boxes.remove(b)
no_errors(w, "bushes")

# ---- no camera call while not worn ------------------------------------------------------------------------------------------
o = Obj(w, ana, HUD_SCRIPTS)
w.objects[o.key] = o
o.rez(); w.run(3)
for sc in o.scripts:
    if sc.name == "core":                                            # as if it had the permission (in-world: the error)
        sc.perms = C["PERMISSION_TAKE_CONTROLS"] | C["PERMISSION_CONTROL_CAMERA"] | C["PERMISSION_TRACK_CAMERA"]
        sc.g["gPermOK"] = 1
o.send(7371, "shot|tracking"); w.run(3)
o.send(7371, "shot|portrait"); w.run(3)
check(not o.cam.get("active"), "a copy on the ground never sets the camera: %r" % (o.cam,))
w.errors.clear()

# ---- Tracking into the next region: nothing set mid-move ------------------------------------------------------------------
ana.touch("t12 s0"); w.run(3)
check(var(h, "core", "gFollow") == 1, "Tracking runs")
t0 = h.cam.get("t")
h._changed(C["CHANGED_REGION"]); w.run(0.2)
check(h.cam.get("t") == t0 and h.cam.get("active") and var(h, "core", "gTpT") == 0.0, "walking into the next region: the camera is left alone")
no_errors(w, "region")

# ==== 8.0.5 =========================================================================================================
def picture(av, h, p):
    """a point in the picture: x, y in -1..1 of its half-width / half-height"""
    r = project(av, p)
    ts = var(h, "portrait", "gTs")
    return (r[0] / (0.5 * var(h, "portrait", "gAsp") * ts), r[1] / (0.5 * ts))

w = World()
ana = w.avatar("Ana", (128, 128, 21))
L = ready(ana)
L["cin.eye"] = ("1.12", PASS)                                       # a mesh body / hover height: the eyes above 1.0
h = ana.wear(HUD_SCRIPTS, lsd=L)
ana.fov = 2 * math.atan(12.0 / 38.0)                                 # the user's 38 mm lens
w.run(5)
ana.face(90)
ana.double_tap(); w.run(1)
ana.touch("t12 s1"); w.run(3)
check(abs(var(h, "portrait", "gFov") - ana.fov) < 0.01, "Portrait reads your lens (%.3f, not 60°)" % var(h, "portrait", "gFov"))
E = vec(ana.pos[0], ana.pos[1], ana.pos[2] + (1.12 - 0.5) * ana.size[2])
for word in ("CLOSE", "MEDIUM", "WIDE"):
    ana.touch(opt_part(h, word)); w.run(2)
    y = picture(ana, h, E)[1]
    if word == "WIDE": check(picture(ana, h, vec(E[0], E[1], E[2] + 0.15))[1] < 1.0, "Wide: the head in the picture")
    else: check(abs(y - 0.333) < 0.05, "%s: the eyes (at 1.12) on the upper third (%.3f)" % (word, y))
no_errors(w, "lens and eyes")

# ---- the notes: lower, longer; the eye line's instruction stays --------------------------------------------------------------
note = rect(h, ana, "t12 note")
band = rect(h, ana, "t12 band")
check(note[1] <= band[1] - band[3] / 2 - 56 / 1080.0, "the notes' part well under the band (%.0f px below)" % ((band[1] - band[3] / 2 - note[1]) * 1080))
ana.double_tap(); w.run(1)
check(rect(h, ana, "t12 note")[1] <= rect(h, ana, "Take 12")[1] - 80 / 1080.0, "closed: well under the [12]")
h.send(7345, "SCENIC"); w.run(3.5)
check(h.part("t12 note")["text"] != "", "a tip still shows after 3.5 s")
w.run(8)
check(h.part("t12 note")["text"] == "", "... and goes")
ana.tap(); w.run(0.6); ana.click("Settings"); w.run(0.5); ana.click("Eye line"); w.run(0.5)
w.run(30)
check("PgUp" in h.part("t12 note")["text"], "the eye line's instruction stays while the line is up: %r" % h.part("t12 note")["text"])
ana.tap(); w.run(0.6)
check("PgUp" not in h.part("t12 note")["text"], "... and goes when it is kept")
no_errors(w, "notes")

# ---- the strip as you left it, worn again ------------------------------------------------------------------------------------------
ana.double_tap(); w.run(1)
check(var(h, "strip", "gOpen") == 1, "open")
ana.take_off(h); w.run(1)
ana.huds.append(h); h.attach(); w.run(5)
check(var(h, "strip", "gOpen") == 1 and var(h, "screen", "gOpen") == 1, "worn again: the strip open, as left")
ana.double_tap(); w.run(1)
ana.take_off(h); w.run(1)
ana.huds.append(h); h.attach(); w.run(5)
check(var(h, "strip", "gOpen") == 0, "left closed: closed")
no_errors(w, "re-wear")

# ---- Room as soon as you walk in ----------------------------------------------------------------------------------------------------
w = World()
w.boxes += room(120, 120, 20.0, 130, 130, 3.0, door=(123, 127))
ana, h = hud(w, pos=(115, 125, 21))
ana.double_tap(); w.run(1)
ana.touch("t12 s3"); w.run(4)
check(var(h, "scenic", "gLocal") == 0, "outside: outdoors")
ana.walk((124, 125, 21)); w.run(12)
check(var(h, "scenic", "gLocal") == 1, "9 m on, inside the room: indoors")
st = dict(zip(var(h, "strip", "gOpts"), var(h, "strip", "gOptSt")))
check(st.get("ROOM") != "dim", "ROOM is no longer dim (%r)" % st)
no_errors(w, "room")

# ==== 8.0.6 =========================================================================================================
# ---- Room: from the room's edge, level, across ---------------------------------------------------------------------------
w = World()
w.boxes += room(120, 120, 20.0, 125, 124, 3.0)                       # a 5 x 4 m room
ana, h = hud(w, pos=(122.5, 122, 21))
ana.double_tap(); w.run(1)
ana.touch("t12 s3"); w.run(4)
ana.touch(opt_part(h, "ROOM")); w.run(3)
for i in range(4):
    c, f = h.cam["pos"], h.cam["focus"]
    wall = min(c[0] - 120, 125 - c[0], c[1] - 120, 124 - c[1])
    tilt = math.degrees(math.atan2(c[2] - f[2], math.hypot(f[0] - c[0], f[1] - c[1])))
    check(wall < 1.3, "Room shot %d: the camera by a wall (%.2f m from it)" % (i, wall))
    check(abs(tilt) <= 6.0, "Room shot %d: level (%.1f°)" % (i, tilt))
    ana.touch("t12 s3"); w.run(3)                                    # the lit tap: the next view
no_errors(w, "room shots")

# ---- the [12] inside the band; the hint explains itself; Friends; Snappy -------------------------------------------------
w = World()
ana, h = hud(w)
ana.double_tap(); w.run(1)
ring, band = rect(h, ana, "t12 ring"), rect(h, ana, "t12 band")
check(ring[3] < band[3] - 4 / 1080.0, "the [12]'s ring inside the band (%.0f px in %.0f px)" % (ring[3] * 1080, band[3] * 1080))
ana.touch("t12 s0"); w.run(9)
check(any("Portrait is ready" in n for n in ana.notes()), "the outline on PORTRAIT says why: %r" % ana.notes()[-3:])
ana.dialog = None
ana.tap(); w.run(0.6); ana.click("Settings"); w.run(0.5); ana.click("Friends"); w.run(1)
check(ana.labels()[:2] == ["Add", "Remove"] and "Chime" in " ".join(ana.labels()), "Settings › Friends: %r" % ana.labels())
ana.click("‹ Back"); w.run(1)
check("Tracking" in ana.labels(), "Back: Settings again (%r)" % ana.labels())
ana.click("Tracking"); w.run(0.5)
check(ana.labels() == ["● Smooth", "Snappy", "‹ Back"], "Settings › Tracking: %r" % ana.labels())
ana.click("Snappy"); w.run(1)
ana.click("‹ Back"); w.run(0.5); ana.click("‹ Back"); w.run(0.5); ana.click("Close"); w.run(0.5)
ana.touch("t12 s0"); w.run(1); ana.touch("t12 s0"); w.run(3)
check(h.cam.get("plag", 1) <= 0.1 and h.cam.get("blag", 1) <= 0.1, "Snappy: Tracking right behind you (lags %r, %r)" % (h.cam.get("plag"), h.cam.get("blag")))
no_errors(w, "look, hint, friends, snappy")

# ---- the setup: asked once, never again on a re-wear -----------------------------------------------------------------------
w = World()
ana = w.avatar("Ana", (128, 128, 21))
h = ana.wear(HUD_SCRIPTS)
w.run(5)
ana.tap(); w.run(0.6); ana.click("Start"); w.run(0.5)
ana.dialog = None                                                    # the dialog closed half way (Ignore)
ana.take_off(h); w.run(1)
t = w.t
ana.huds.append(h); h.attach(); w.run(6)
check(not any("set up" in n for n in ana.notes(t)), "worn again after a setup begun: no setup again (%r)" % ana.notes(t))
no_errors(w, "setup once")
done("inworld_emu")
