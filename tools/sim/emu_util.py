"""Helpers for the 8.0 emulator tests (tools/sim/*_emu.py): where the HUD's parts are on the screen, the camera's
picture, small assertions. The tests run the REAL scripts of hud/src in tools/emu."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "emu"))
from world import *                                                    # noqa: F401,F403
from world import C, B, vec

FAILS = []


def check(cond, what):
    if not cond:
        FAILS.append(what)
        print("FAIL", what)
    return cond


def done(name):
    if FAILS:
        print("%s: %d failed" % (name, len(FAILS)))
        sys.exit(1)
    print("%s: all passed" % name)


def no_errors(w, where=""):
    check(not w.errors, "%s script errors: %s" % (where, w.errors[:5]))
    w.errors.clear()


# ---- the screen ---------------------------------------------------------------------------------------------------
POINTS = [C["ATTACH_HUD_TOP_RIGHT"], C["ATTACH_HUD_TOP_CENTER"], C["ATTACH_HUD_TOP_LEFT"], C["ATTACH_HUD_BOTTOM_LEFT"],
          C["ATTACH_HUD_BOTTOM"], C["ATTACH_HUD_BOTTOM_RIGHT"]]


def centre(point, aspect):
    """the screen centre in the attach point's frame (crop.lsl's table)"""
    if point not in POINTS: return (0.0, 0.0, 0.0)
    p = POINTS.index(point)
    return (0.0, aspect * 0.5 * [1, 0, -1, -1, 0, 1][p], 0.5 * [-1, -1, -1, 1, 1, 1][p])


def rect(h, av, name):
    """a part on the screen: (x right, z up from the screen centre, width, height, alpha); the root is "Take 12" """
    i = h.link(name) - 1
    root = h.prims[0]["pos"]
    p = h.prims[i]["pos"]
    P = p if i == 0 else (root[0] + p[0], root[1] + p[1], root[2] + p[2])
    c = centre(h.point, av.aspect)
    sz = h.prims[i]["size"]
    return (-(P[1] - c[1]), P[2] - c[2], sz[1], sz[2], h.prims[i]["alpha"])


def visible(h, av, prefix=("t12 s", "t12 o", "t12 shape", "t12 link")):
    out = {}
    for p in h.prims[1:]:
        if p["name"].startswith(prefix) and p["alpha"] > 0.02 and p["size"][1] > 0.0101:
            out[p["name"]] = rect(h, av, p["name"])
    return out


def overlap(a, b, shrink=0.0):
    ax0, ax1 = a[0] - a[2] / 2 + shrink, a[0] + a[2] / 2 - shrink
    bx0, bx1 = b[0] - b[2] / 2 + shrink, b[0] + b[2] / 2 - shrink
    az0, az1 = a[1] - a[3] / 2, a[1] + a[3] / 2
    bz0, bz1 = b[1] - b[3] / 2, b[1] + b[3] / 2
    return ax0 < bx1 - 1e-6 and bx0 < ax1 - 1e-6 and az0 < bz1 - 1e-6 and bz0 < az1 - 1e-6


# ---- the picture ---------------------------------------------------------------------------------------------------
def project(av, point, aspect=None):
    """where a world point lands in the picture: (x, y) from the centre, -0.5..0.5 of the height (y up), and depth"""
    cam, foc, _ = av.camera()
    f = B.sub(foc, cam)
    L = math.sqrt(f[0] ** 2 + f[1] ** 2 + f[2] ** 2)
    f = (f[0] / L, f[1] / L, f[2] / L)
    left = (-f[1], f[0], 0.0)
    m = math.hypot(left[0], left[1]) or 1.0
    left = (left[0] / m, left[1] / m, 0.0)
    up = (f[1] * left[2] - f[2] * left[1], f[2] * left[0] - f[0] * left[2], f[0] * left[1] - f[1] * left[0])
    d = B.sub(point, cam)
    depth = d[0] * f[0] + d[1] * f[1] + d[2] * f[2]
    if depth <= 0.01: return None
    t = math.tan(av.fov / 2)
    x = -(d[0] * left[0] + d[1] * left[1] + d[2] * left[2]) / depth / t * 0.5
    y = (d[0] * up[0] + d[1] * up[1] + d[2] * up[2]) / depth / t * 0.5
    return (x, y, depth)


def eyes(av, frac=0.935):
    return vec(av.pos[0], av.pos[1], av.pos[2] + (frac - 0.5) * av.size[2])


def feet(av):
    return vec(av.pos[0], av.pos[1], av.pos[2] - 0.5 * av.size[2])


def hud(w, name="Ana", pos=(128, 128, 21), scripts=None, **kw):
    av = w.avatar(name, pos)
    h = av.wear(scripts or HUD_SCRIPTS, lsd=ready(av), **kw)
    w.run(5)
    return av, h


def textures(h):
    """the two textures dropped in (adopted by screen)"""
    h.drop("take12_words")
    h.drop("take12_marks")
