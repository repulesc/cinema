# Freehand (6.4.0, free.lsl + core): you frame it with Second Life's own camera, hold still for a second, and the view
# is held; walking and Esc no longer move it. The focus is what sits in the middle of the frame, so a zoom keeps the
# picture (the same dolly as every camera), stopping short of a wall. Two saved views per region; a double-tap goes
# from one to the other. Ported and checked here, with the wiring in core, ui and tips.
import math, os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda n: open(os.path.join(R, "hud", "src", n)).read()
free, core, ui, tips = rd("free.lsl"), rd("core.lsl"), rd("ui.lsl"), rd("tips.lsl")
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

fov_of = lambda mm: 2 * math.atan(12.0 / mm)
sub = lambda a, b: tuple(x - y for x, y in zip(a, b))
add = lambda a, b: tuple(x + y for x, y in zip(a, b))
mul = lambda a, k: tuple(x * k for x in a)
norm = lambda a: mul(a, 1 / math.sqrt(sum(x * x for x in a)))
dist = lambda a, b: math.dist(a, b)

# ---- the dolly (zoom()): a subject at the focus keeps its size on screen at every lens pair ----------------------
def zoom(cam, foc, f_old, f_new, wall=None):
    """wall: distance from the focus along the line where something solid stands (None = open)"""
    k = math.tan(f_old / 2) / math.tan(f_new / 2)
    nc = add(foc, mul(sub(cam, foc), k))
    if wall is not None and wall < dist(nc, foc):           # the ray from 0.5 m off the subject hits it
        nc = add(foc, mul(norm(sub(cam, foc)), wall - 0.3))
    return nc if dist(nc, foc) > 0.3 else cam
size = lambda cam, foc, h, fov: (h / dist(cam, foc)) / (2 * math.tan(fov / 2))
LENSES = (21, 35, 50, 85, 105, 200)
for a in LENSES:
    for b in LENSES:
        cam, foc = (120.0, 80.0, 31.0), (124.0, 83.0, 30.2)       # a product on a table, 5 m away
        c2 = zoom(cam, foc, fov_of(a), fov_of(b))
        check(abs(size(cam, foc, 0.4, fov_of(a)) - size(c2, foc, 0.4, fov_of(b))) < 1e-9, f"{a}->{b} mm: the object changed size")
        d0, d1 = norm(sub(foc, cam)), norm(sub(foc, c2))
        check(sum(x * y for x, y in zip(d0, d1)) > 1 - 1e-12, f"{a}->{b} mm: the camera left its line")
c2 = zoom((0.0, 0.0, 2.0), (5.0, 0.0, 2.0), fov_of(21), fov_of(105), wall=8.0)
check(abs(dist(c2, (5.0, 0.0, 2.0)) - 7.7) < 1e-9, "a wall behind the camera must stop the dolly 0.3 m short")
for frag in ("float k = llTan(gFov * 0.5) / llTan(nf * 0.5);", "vector nc = gFoc + (gCam - gFoc) * k;",
             "vector s = gFoc + llVecNorm(gCam - gFoc) * 0.5;", "nc = llList2Vector(r, 1) + llVecNorm(gFoc - nc) * 0.3;",
             'llMessageLinked(LINK_SET, GLIDE, (string)gCam + "|" + (string)gFoc + "|1.5", "");',
             "if (!gHeld) return;", 'gHeld = (llGetSubString(str, 0, 7) == "rolling|");'):
    check(frag in free, f"free.lsl: the dolly no longer reads '{frag}'")

# ---- the focus: what sits in the middle of the frame (core's lock and free.lsl's own) ------------------------------
check("list h = llCastRay(c, c + u * 60.0, [RC_MAX_HITS, 1]);" in free and "return c + u * 10.0;" in free, "free.lsl: the focus ray")
check("list h = llCastRay(cp, cp + u * 60.0, [RC_MAX_HITS, 1]);" in core and "f = cp + u * 10.0;" in core, "core: the lock's focus ray")
check('"|0|10|"' in free, "free.lsl: a held view never cuts (hold 0)")

# ---- the lock and the tripod in core ----------------------------------------------------------------------------
check('|| str == "free") engage(str);' in core, "core: Freehand must start from the menu")
check('if (gMode == "free") return;                    // Freehand: a tripod' in core, "core: movement keys must not end Freehand")
check('else if (llGetTime() - gLeadT > 1.5 - 0.5 * (gMode == "free"))' in core, "core: Freehand locks after 1 s still")
check('integer own = (gMode == "friends" || gMode == "free");' in core and "if (gPeekBail && !own)" in core, "core: your own framing, never a bail")
check('|| str == "free" || str == "fav")) return;' in core, "core: the free Take 12 Scenery has no Freehand")
typing = core[core.index("if (info & AGENT_TYPING)"):core.index("if (info & AGENT_MOUSELOOK)")]
check('"free"' not in typing, "core: typing must not end Freehand")

# ---- saved views: two per region, the oldest goes; a double-tap goes round them, or holds the view on screen -------
def save(views, v):
    views = views + [v]
    return views[1:] if len(views) > 2 else views
v = []
for x in ("A", "B", "C"): v = save(v, x)
check(v == ["B", "C"], f"two views, the oldest replaced: {v}")
pick = -1; seen = []
for _ in range(4):
    pick = (pick + 1) % len(v); seen.append(v[pick])
check(seen == ["B", "C", "B", "C"], f"double-tap goes round: {seen}")
check("if (llGetListLength(v) > 2) v = llDeleteSubList(v, 0, 0);" in free and "gPick = (gPick + 1) % llGetListLength(v);" in free
      and "if (v == [])\n    {\n        here();" in free, "free.lsl: save / recall")
check('return "free." + llDumpList2String(llParseString2List(llGetRegionName(), [" "], []), "_");' in free, "free.lsl: per region")
check('if (num == CMD && str == "fav") save();' in free.replace("else if (num == CMD", "if (num == CMD") and
      'else if (gMode != "free") llOwnerSay(' in core, "Save: free.lsl keeps the view, core stays quiet")

# ---- the menu and the line above the button --------------------------------------------------------------------
check("~free|" in ui and '"frame", "free", "crop"' in ui and '|| id == "free" ||' in ui, "ui: Freehand on the main menu")
check('if (gUiMode == "scenery" || gUiMode == "free") b += ["save"];' in ui, "ui: Save in the live menu while Freehand runs")
check('"personal", "us", "frame", "free", "share"' in ui, "ui: the free Take 12 Scenery hides Freehand")
check('else if (gMode == "free") w = "held";' in tips and 'w = "framing · hold still" + lensTxt(m);' in tips, "tips: held / framing, with your lens")
check('else if (st == "peek" && mode != "free") want(7);' in tips, "tips: no 'Paused' tip while you frame")
print(f"freehand: the dolly keeps an object's size over {len(LENSES)}x{len(LENSES)} lens pairs, stops at walls; 2 views per region")
print("freehand checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
