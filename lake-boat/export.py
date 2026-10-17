"""Build all LODs + physics shape, centre them on the high-LOD bounding box and write
COLLADA (.dae) files for the Second Life mesh uploader, plus an OBJ for Blender & friends."""
import json
import os
import numpy as np
import boat
from meshlib import write_dae, write_obj, match_bbox

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(os.path.join(OUT, "mesh"), exist_ok=True)

built = {lod: boat.build(lod) for lod in (3, 2, 1, 0)}
hi_ms, info = built[3]
lo, hi = hi_ms.bbox()
centre = (lo + hi) / 2
for lod, (ms, _) in built.items():
    ms.translate(-centre)
lo, hi = lo - centre, hi - centre

phys = boat.physics_hull()
phys.translate(-centre)
match_bbox(phys, lo, hi, "hull_planks")

report = {}
for lod, (ms, _) in built.items():
    match_bbox(ms, lo, hi, "hull_planks")
    path = os.path.join(OUT, "mesh", f"lakeboat_LOD{lod}.dae")
    write_dae(ms, path, name="lakeboat")
    report[f"LOD{lod}"] = dict(tris=ms.tri_count(), verts=ms.vert_count(),
                               bbox=[np.round(x, 3).tolist() for x in ms.bbox()])
write_dae(phys, os.path.join(OUT, "mesh", "lakeboat_physics.dae"), name="lakeboat")
report["physics"] = dict(tris=phys.tri_count(), bbox=[np.round(x, 3).tolist() for x in phys.bbox()])
write_obj(built[3][0], os.path.join(OUT, "mesh", "lakeboat.obj"))

size = hi - lo
report["size_m"] = np.round(size, 3).tolist()
benches = [(round(float(x - centre[0]), 3), round(float(z - centre[2]), 3)) for x, z in info["benches"]]
report["bench_top_xz_from_centre"] = benches
report["rowlock_x_from_centre"] = round(float(info["rowlock_x"] - centre[0]), 3)
report["keel_z_from_centre"] = round(float(-centre[2]), 3)
with open(os.path.join(OUT, "mesh", "lakeboat_info.json"), "w") as f:
    json.dump(report, f, indent=1)
print(json.dumps(report, indent=1))
