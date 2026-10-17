"""Render a few preview angles of the boat -> out/preview/*.png"""
import os
import sys
import numpy as np
import boat
from render import render

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "preview")
os.makedirs(OUT, exist_ok=True)

lod = int(os.environ.get("LOD", 3))
ms, info = boat.build(lod)
mats = ms.merged()

# waterline outline (hull at ~0.17 m above the keel line)
zw = 0.17
xs, hw = [], []
for s in np.linspace(0, 1, 120):
    t = np.linspace(0, 1, 200)
    P = boat.pos(np.full_like(t, s), t, 1)
    k = np.argmin(np.abs(P[:, 2] - zw))
    xs.append(P[k, 0]); hw.append(P[k, 1] + 0.012 if boat.zk(s) < zw else 0.0)
xs, hw = np.array(xs), np.array(hw)
o = np.argsort(xs)
outline = (xs[o], hw[o])

views = {
    "front34": ((3.9, 3.1, 1.9), (0.1, 0, 0.3)),
    "rear34": ((-3.7, -3.0, 1.9), (-0.1, 0, 0.3)),
    "side": ((0.1, -5.3, 1.0), (0.1, 0, 0.3)),
    "top": ((0.1, 0.01, 5.6), (0.1, 0, 0.3)),
    "bow": ((3.2, 1.1, 1.0), (1.8, 0, 0.45)),
    "stern": ((-3.3, 1.2, 1.2), (-1.7, 0, 0.35)),
    "inside": ((1.6, 0.9, 1.5), (-0.6, 0, 0.1)),
}
pick = sys.argv[1:] or list(views)
for name in pick:
    eye, tgt = views[name]
    water = None if name in ("top", "bow", "stern") and os.environ.get("NOWATER") else zw
    ev = np.array(eye) - np.array(tgt); ev[2] = 0
    ev = ev / (np.linalg.norm(ev) + 1e-9)
    sun = (0.55 * ev[0] + 0.25 * ev[1], 0.55 * ev[1] - 0.25 * ev[0], 0.85)
    im = render(mats, eye, tgt, sun=sun, size=(1280, 800) if name != "top" else (1280, 800),
                water_z=None if os.environ.get("NOWATER") else zw - 0.0 + 0.0,
                water_outline=outline, ss=2 if os.environ.get("FAST") is None else 1)
    im.save(os.path.join(OUT, f"{name}.png"))
    print("rendered", name)
