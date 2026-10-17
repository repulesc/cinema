"""Tiny mesh toolkit: per-material triangle soup, sweep / grid builders, OBJ + COLLADA export.
Coordinates follow Second Life: +X forward, +Y left, +Z up, metres."""
import numpy as np
import os


def norm(v, eps=1e-12):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + eps)


class MeshSet:
    def __init__(self):
        self.parts = {}     # material -> list of (V, UV, T)

    def add(self, mat, V, UV, T):
        V = np.asarray(V, float).reshape(-1, 3)
        UV = np.asarray(UV, float).reshape(-1, 2)
        T = np.asarray(T, int).reshape(-1, 3)
        self.parts.setdefault(mat, []).append((V, UV, T))

    def materials(self):
        return list(self.parts.keys())

    def merged(self):
        """material -> (V, N, UV, T) with area-weighted vertex normals."""
        out = {}
        for mat, lst in self.parts.items():
            Vs, UVs, Ts, off = [], [], [], 0
            for V, UV, T in lst:
                Vs.append(V)
                UVs.append(UV)
                Ts.append(T + off)
                off += len(V)
            V, UV, T = np.vstack(Vs), np.vstack(UVs), np.vstack(Ts)
            fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
            N = np.zeros_like(V)
            for k in range(3):
                np.add.at(N, T[:, k], fn)
            Nn = norm(N)
            Nn[np.linalg.norm(Nn, axis=1) < 0.5] = (0.0, 0.0, 1.0)
            out[mat] = (V, Nn, UV, T)
        return out

    def bbox(self):
        allv = np.vstack([V for lst in self.parts.values() for V, _, _ in lst])
        return allv.min(0), allv.max(0)

    def tri_count(self):
        return sum(len(T) for lst in self.parts.values() for _, _, T in lst)

    def vert_count(self):
        return sum(len(V) for lst in self.parts.values() for V, _, _ in lst)

    def translate(self, d):
        d = np.asarray(d, float)
        for lst in self.parts.values():
            for i, (V, UV, T) in enumerate(lst):
                lst[i] = (V + d, UV, T)


def orient(V, T, ref):
    """Flip all triangles if, on average, their normal opposes `ref` (vector or per-face array)."""
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    ref = np.broadcast_to(np.asarray(ref, float), fn.shape)
    if (fn * ref).sum() < 0:
        T = T[:, [0, 2, 1]]
    return T


def grid(P, UV):
    """Quad grid (nu x nv points) -> verts, uv, tris (winding arbitrary, orient afterwards)."""
    nu, nv = P.shape[:2]
    V = P.reshape(-1, 3)
    uv = UV.reshape(-1, 2)
    idx = np.arange(nu * nv).reshape(nu, nv)
    a, b, c, d = idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]
    T = np.concatenate([np.stack([a, b, c], -1).reshape(-1, 3),
                        np.stack([a, c, d], -1).reshape(-1, 3)])
    return V, uv, T


def add_grid(ms, mat, P, UV, ref, double_mat=None):
    """Add a grid oriented so its normals follow `ref` (vector or fn(face_centroids)->vectors)."""
    V, uv, T = grid(np.asarray(P, float), np.asarray(UV, float))
    cen = V[T].mean(1)
    r = ref(cen) if callable(ref) else ref
    T = orient(V, T, r)
    ms.add(mat, V, uv, T)
    if double_mat:
        ms.add(double_mat, V, uv, T[:, [0, 2, 1]])


def rounded_rect(w, h, bevel=0.0, cx=0.0, cy=0.0):
    """CCW closed profile (a along 'right', b along 'up')."""
    a, b = w / 2, h / 2
    r = min(bevel, a * 0.9, b * 0.9)
    if r <= 1e-6:
        pts = [(a, -b), (a, b), (-a, b), (-a, -b)]
    else:
        pts = [(a, -b + r), (a, b - r), (a - r, b), (-a + r, b),
               (-a, b - r), (-a, -b + r), (-a + r, -b), (a - r, -b)]
    return np.array(pts) + np.array([cx, cy])


def circle_profile(r, n=8):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([r * np.cos(t), r * np.sin(t)], -1)


def sweep(ms, mat, path, profile, up=(0, 0, 1), closed_path=False, caps=True,
          u_len=1.0, v_len=1.0, uv_off=(0.0, 0.0), scale=None, smooth=False):
    """Extrude a closed 2D profile along a 3D polyline.
    u = distance along the path / u_len ; v = distance around the profile / v_len.
    scale: optional per-ring (sa, sb) array for tapering."""
    path = np.asarray(path, float)
    profile = np.asarray(profile, float)
    n, m = len(path), len(profile)
    up = np.asarray(up, float)
    T = np.gradient(path, axis=0)
    if closed_path:
        T = np.roll(path, -1, 0) - np.roll(path, 1, 0)
    T = norm(T)
    R = norm(np.cross(up, T))
    U = norm(np.cross(T, R))
    sc = np.ones((n, 2)) if scale is None else np.asarray(scale, float)
    ring = (path[:, None, :] + (profile[None, :, 0] * sc[:, 0:1])[..., None] * R[:, None, :]
            + (profile[None, :, 1] * sc[:, 1:2])[..., None] * U[:, None, :])        # n x m x 3
    seg = np.linalg.norm(np.diff(path, axis=0, append=path[:1] if closed_path else path[-1:]), axis=1)
    dist = np.concatenate([[0], np.cumsum(seg[:-1])])
    per = np.linalg.norm(np.roll(profile, -1, 0) - profile, axis=1)
    pcum = np.concatenate([[0], np.cumsum(per)])
    ncols = n if closed_path else n - 1
    tot_u = (dist[-1] + seg[-1]) / u_len
    tot_v = pcum[-1] / v_len + per[-1] / v_len if False else (pcum[-1] + per[-1]) / v_len
    if tot_u > 0.98:
        u_len *= tot_u / 0.98
        tot_u = 0.98
    if tot_v > 0.98:
        v_len *= tot_v / 0.98
        tot_v = 0.98
    uv_off = (float(np.clip(uv_off[0], 0.005, max(0.005, 0.995 - tot_u))),
              float(np.clip(uv_off[1], 0.005, max(0.005, 0.995 - tot_v))))
    for k in range(m):
        k2 = (k + 1) % m
        for_ring = np.arange(ncols)
        i2 = (for_ring + 1) % n
        A, B = ring[for_ring, k], ring[i2, k]
        C, D = ring[i2, k2], ring[for_ring, k2]
        ua = dist[for_ring] / u_len + uv_off[0]
        ub = (dist[for_ring] + seg[for_ring]) / u_len + uv_off[0]
        va = pcum[k] / v_len + uv_off[1]
        vb = (pcum[k] + per[k]) / v_len + uv_off[1]
        V = np.stack([A, B, C, D], 1).reshape(-1, 3)
        UV = np.stack([np.stack([ua, np.full_like(ua, va)], -1),
                       np.stack([ub, np.full_like(ub, va)], -1),
                       np.stack([ub, np.full_like(ub, vb)], -1),
                       np.stack([ua, np.full_like(ua, vb)], -1)], 1).reshape(-1, 2)
        base = np.arange(ncols) * 4
        Tt = np.concatenate([np.stack([base, base + 1, base + 2], -1),
                             np.stack([base, base + 2, base + 3], -1)])
        cen = V[Tt].mean(1)
        ctr = np.tile(path[for_ring], (2, 1))
        Tt = orient(V, Tt, cen - ctr)
        ms.add(mat, V, UV, Tt)
    if caps and not closed_path:
        for end, nrm in ((0, -T[0]), (n - 1, T[-1])):
            pts = ring[end]
            cpt = pts.mean(0)
            V = np.vstack([cpt[None], pts])
            loc = np.vstack([[profile.mean(0)], profile])
            UV = np.clip(np.array(uv_off) + 0.02 + (loc - loc.mean(0)) * 2.0, 0.005, 0.995)
            Tt = np.array([[0, 1 + k, 1 + (k + 1) % m] for k in range(m)])
            Tt = orient(V, Tt, nrm)
            ms.add(mat, V, UV, Tt)


def circle_path(center, radius, axis="y", n=24, start=0.0):
    t = start + np.linspace(0, 2 * np.pi, n, endpoint=False)
    c = np.asarray(center, float)
    if axis == "y":     # ring lies in the x-z plane
        return c + np.stack([radius * np.cos(t), np.zeros_like(t), radius * np.sin(t)], -1)
    raise ValueError(axis)


def add_tiny_tri(ms, mat, p, size=0.0015):
    p = np.asarray(p, float)
    V = np.array([p, p + [size, 0, 0], p + [0, size, 0]])
    ms.add(mat, V, np.zeros((3, 2)) + 0.5, np.array([[0, 1, 2]]))


def match_bbox(ms, lo, hi, mat):
    """Pad a mesh with invisible 1.5 mm triangles so its bbox equals (lo, hi) (SL scales each
    LOD to its own bounding box, so the boxes of all LODs must agree)."""
    blo, bhi = ms.bbox()
    for i in range(3):
        if blo[i] > lo[i] + 1e-6:
            p = blo.copy(); p[i] = lo[i]
            add_tiny_tri(ms, mat, p)
        if bhi[i] < hi[i] - 1e-6:
            p = bhi.copy(); p[i] = hi[i] - 0.0015
            add_tiny_tri(ms, mat, p)


# ---------------------------------------------------------------- export
def write_obj(ms, path, name="lakeboat", tex_prefix="textures/"):
    mats = sl_materials(ms)
    base = os.path.splitext(path)[0]
    with open(base + ".mtl", "w") as f:
        for m in mats:
            f.write(f"newmtl {m}\nKd 1 1 1\nmap_Kd {tex_prefix}{TEXMAP.get(m, m)}_d.png\n\n")
    with open(path, "w") as f:
        f.write(f"mtllib {os.path.basename(base)}.mtl\no {name}\n")
        off = 1
        for m, (V, N, UV, T) in mats.items():
            for v in V:
                f.write("v %.5f %.5f %.5f\n" % tuple(v))
            for v in UV:
                f.write("vt %.5f %.5f\n" % tuple(v))
            for v in N:
                f.write("vn %.4f %.4f %.4f\n" % tuple(v))
            f.write(f"usemtl {m}\n")
            for t in T + off:
                f.write("f " + " ".join(f"{i}/{i}/{i}" for i in t) + "\n")
            off += len(V)


TEXMAP = {"hull_planks": "hull", "interior": "interior", "hull_end": "hull_end",
          "wood": "wood", "metal": "metal"}

# Second Life numbers faces by material NAME order (alphabetical), not by order in the file.
# Prefixing f0..f4 makes both orders identical, so face N is always the same material.
FACE_ORDER = ["hull_planks", "interior", "hull_end", "wood", "metal"]
SL_NAME = {m: f"f{i}_{m}" for i, m in enumerate(FACE_ORDER)}
for _m, _n in SL_NAME.items():
    TEXMAP[_n] = TEXMAP[_m]


def sl_materials(ms):
    """merged() with materials renamed to SL_NAME and sorted by face order."""
    mats = ms.merged()
    return {SL_NAME[k]: mats[k] for k in FACE_ORDER if k in mats}


def write_dae(ms, path, name="lakeboat", tex_dir="textures"):
    """COLLADA 1.4.1, Z_UP, metres, one <triangles> block per material (= one SL face each)."""
    mats = sl_materials(ms)
    L = []
    L.append('<?xml version="1.0" encoding="utf-8"?>')
    L.append('<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">')
    L.append('<asset><contributor><authoring_tool>lake-boat generator</authoring_tool></contributor>'
             '<unit name="meter" meter="1"/><up_axis>Z_UP</up_axis></asset>')
    L.append("<library_images>")
    for m in mats:
        L.append(f'<image id="{m}-img" name="{m}-img"><init_from>{tex_dir}/{TEXMAP.get(m, m)}_d.png</init_from></image>')
    L.append("</library_images>")
    L.append("<library_effects>")
    for m in mats:
        L.append(f'<effect id="{m}-fx"><profile_COMMON>'
                 f'<newparam sid="{m}-surf"><surface type="2D"><init_from>{m}-img</init_from></surface></newparam>'
                 f'<newparam sid="{m}-samp"><sampler2D><source>{m}-surf</source></sampler2D></newparam>'
                 f'<technique sid="common"><phong><diffuse><texture texture="{m}-samp" texcoord="UVMap"/></diffuse>'
                 f'<specular><color>0.1 0.1 0.1 1</color></specular><shininess><float>20</float></shininess></phong></technique>'
                 f'</profile_COMMON></effect>')
    L.append("</library_effects>")
    L.append("<library_materials>")
    for m in mats:
        L.append(f'<material id="{m}-material" name="{m}"><instance_effect url="#{m}-fx"/></material>')
    L.append("</library_materials>")
    gid = f"{name}-mesh"
    L.append(f'<library_geometries><geometry id="{gid}" name="{name}"><mesh>')
    # one shared vertex pool (COLLADA allows exactly one <vertices> per mesh)
    Vs, Ns, UVs, offs, off = [], [], [], {}, 0
    for m, (V, N, UV, T) in mats.items():
        Vs.append(V); Ns.append(N); UVs.append(UV)
        offs[m] = off
        off += len(V)
    for kind, arr, comps, params in (("pos", np.vstack(Vs), 3, "XYZ"), ("nrm", np.vstack(Ns), 3, "XYZ"),
                                     ("uv", np.vstack(UVs), 2, "ST")):
        sid = f"{name}-{kind}"
        flat = " ".join("%.5f" % x for x in arr.reshape(-1))
        pdecl = "".join(f'<param name="{c}" type="float"/>' for c in params)
        L.append(f'<source id="{sid}"><float_array id="{sid}-arr" count="{arr.size}">{flat}</float_array>'
                 f'<technique_common><accessor source="#{sid}-arr" count="{len(arr)}" stride="{comps}">{pdecl}</accessor>'
                 f'</technique_common></source>')
    L.append(f'<vertices id="{name}-vtx"><input semantic="POSITION" source="#{name}-pos"/></vertices>')
    for m, (V, N, UV, T) in mats.items():
        idx = " ".join(f"{i} {i} {i}" for i in (T + offs[m]).reshape(-1))
        L.append(f'<triangles material="{m}-material" count="{len(T)}">'
                 f'<input semantic="VERTEX" source="#{name}-vtx" offset="0"/>'
                 f'<input semantic="NORMAL" source="#{name}-nrm" offset="1"/>'
                 f'<input semantic="TEXCOORD" source="#{name}-uv" offset="2" set="0"/>'
                 f'<p>{idx}</p></triangles>')
    L.append("</mesh></geometry></library_geometries>")
    L.append('<library_visual_scenes><visual_scene id="Scene" name="Scene">'
             f'<node id="{name}" name="{name}" type="NODE"><instance_geometry url="#{gid}"><bind_material><technique_common>')
    for m in mats:
        L.append(f'<instance_material symbol="{m}-material" target="#{m}-material">'
                 f'<bind_vertex_input semantic="UVMap" input_semantic="TEXCOORD" input_set="0"/></instance_material>')
    L.append("</technique_common></bind_material></instance_geometry></node></visual_scene></library_visual_scenes>")
    L.append('<scene><instance_visual_scene url="#Scene"/></scene></COLLADA>')
    with open(path, "w") as f:
        f.write("\n".join(L))
