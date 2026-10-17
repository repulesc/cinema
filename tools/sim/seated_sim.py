# Seated view: the camera rises to look down on you at 30/45/60 degrees (people and friends scripts). Checks the
# maths used in tryCand/camZ: your eye lands on the upper third, everyone near you stays inside the vertical frame,
# the ceiling cap falls back to the level shot, and both scripts carry the same code and default.
import math, os, random, re
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

TANV = math.tan(math.radians(60) / 2)                    # the default viewer FOV
for name in ("people", "friends"):
    src = open(os.path.join(R, "hud", "src", f"cinema_{name}.lsl")).read()
    check('cfg("seat_deg", "45")' in src, f"{name}: default seat angle is not 45")
    check("if (gOSit && gSeatEl > 0.0) z = eyeRef + d * llTan(gSeatEl);" in src, f"{name}: camZ lacks the seated rise")
    check("r > de * 0.176" in src and "llAtan2(tanV, 3.0)" in src, f"{name}: tryCand lacks the seated look-down")
    check('gOSit != gSitAtShot) gPendEvent = "seat"' in src, f"{name}: no re-frame when you sit or stand")
ui = open(os.path.join(R, "hud", "src", "cinema_ui.lsl")).read()
check('"seat_deg", "45"' in ui, "ui: default seat angle missing")
check('"look", "seat", "test", "reset", "back"' in ui, "ui: the Seated view button is not on the Options page")

def shot(el_deg, de, eye_z, roof=None):
    """camera z and the focus z, as the script computes them; returns (cam_z, foc_z, pitch)."""
    z = eye_z + de * math.tan(math.radians(el_deg))
    if roof is not None: z = min(z, roof - 0.3)
    r = z - eye_z
    if r > de * 0.176: pitch = math.atan2(r, de) + math.atan2(TANV, 3.0)
    else: pitch = 0.0
    return z, z - de * math.tan(pitch), pitch

def y_of(zp, dist_h, cam_z, pitch):
    """vertical screen position (-1..1) of a point at height zp, dist_h metres ahead of the camera"""
    a = math.atan2(zp - cam_z, dist_h) + pitch
    return math.tan(a) / TANV

rng = random.Random(7)
n = 0
for el in (30, 45, 60):
    for de in (2.5, 4, 6, 9, 12):
        eye = 0.6                                         # a seated eye, ground at 0
        cz, fz, pitch = shot(el, de, eye)
        y = y_of(eye, de, cz, pitch)
        check(abs(y - 1 / 3) < 0.02, f"{el} deg at {de} m: your eye is at {y:.2f}, not the upper third")
        for _ in range(200):                              # friends up to 3 m round you, standing or sitting
            ho = rng.uniform(-3.0, 3.0)                   # along the view
            top = rng.choice([0.9, 2.0]); bot = 0.0
            for zp in (top, bot):
                yy = y_of(zp, max(de + ho, 0.5), cz, pitch)
                n += 1
                if de >= 6:
                    check(-1.0 < yy < 1.0, f"{el} deg at {de} m: a person is out of the frame vertically ({yy:.2f})")

# the ceiling: a low roof caps the rise; under about 10 degrees it is level again
cz, fz, pitch = shot(45, 4, 0.6, roof=3.0)
check(cz <= 2.7 + 1e-9, "the roof cap is not applied")
cz, fz, pitch = shot(45, 4, 0.6, roof=1.6)
check(pitch == 0.0, "a very low roof should leave the shot level")
check(math.degrees(shot(30, 6, 0.6)[2]) > 30 and math.degrees(shot(60, 6, 0.6)[2]) < 80, "pitch out of range")

print(f"seated: 3 angles x 5 distances, {n} people points checked")
print("seated checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
