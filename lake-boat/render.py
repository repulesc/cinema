"""Minimal numpy z-buffer renderer for previewing the boat with its textures
(back-face culled like Second Life, mip-mapped bilinear textures, sun + sky light, optional water)."""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.join(HERE, "out", "textures")
from meshlib import TEXMAP, norm

SPEC = {"hull_planks": (0.25, 40), "interior": (0.12, 20), "hull_end": (0.22, 40), "wood": (0.10, 16), "metal": (0.35, 30)}


def load_tex(name):
    base = TEXMAP.get(name, name)
    im = Image.open(os.path.join(TEXDIR, f"{base}_d.png")).convert("RGB")
    levels = [np.asarray(im, np.float32) / 255.0]
    while min(im.size) > 2:
        im = im.resize((im.size[0] // 2, im.size[1] // 2), Image.BOX)
        levels.append(np.asarray(im, np.float32) / 255.0)
    return levels


def sample(levels, uv, lod):
    lv = int(np.clip(round(lod), 0, len(levels) - 1))
    tex = levels[lv]
    h, w = tex.shape[:2]
    u = uv[:, 0] * w - 0.5
    v = (1 - uv[:, 1]) * h - 0.5
    x0 = np.floor(u).astype(int); y0 = np.floor(v).astype(int)
    fx = (u - x0)[:, None]; fy = (v - y0)[:, None]
    x0m, x1m = x0 % w, (x0 + 1) % w
    y0m, y1m = y0 % h, (y0 + 1) % h
    return (tex[y0m, x0m] * (1 - fx) * (1 - fy) + tex[y0m, x1m] * fx * (1 - fy)
            + tex[y1m, x0m] * (1 - fx) * fy + tex[y1m, x1m] * fx * fy)


def look_at(eye, target, up=(0, 0, 1)):
    f = norm(np.asarray(target, float) - eye)
    r = norm(np.cross(f, up))
    u = np.cross(r, f)
    return r, u, f


def render(mats, eye, target, size=(1280, 800), fov=38, ss=2, water_z=None, water_outline=None,
           sun=(0.45, -0.55, 0.70), bg=True, cull=True, tex_override=None):
    W, H = size[0] * ss, size[1] * ss
    eye = np.asarray(eye, float)
    r, u, f = look_at(eye, target)
    focal = 0.5 * H / np.tan(np.radians(fov) / 2)
    sun = norm(np.asarray(sun, float))
    cbuf = np.zeros((H, W, 3), np.float32)
    # sky / ground backdrop
    yy = np.linspace(0, 1, H)[:, None, None]
    sky = np.array([0.55, 0.70, 0.85]) * (1 - yy) + np.array([0.82, 0.88, 0.92]) * yy
    cbuf[:] = sky if bg else 0.5
    zbuf = np.full((H, W), np.inf, np.float32)
    levels_cache = {}

    for mat, (V, N, UV, T) in mats.items():
        levels = levels_cache.setdefault(mat, load_tex(mat))
        sp, sh = SPEC.get(mat, (0.1, 20))
        d = V - eye
        cx, cy, cz = d @ r, d @ u, d @ f
        ok = cz > 0.05
        sx = np.where(ok, W / 2 + focal * cx / np.maximum(cz, 1e-6), 0)
        sy = np.where(ok, H / 2 - focal * cy / np.maximum(cz, 1e-6), 0)
        # per-vertex lighting
        ndl = np.clip(N @ sun, 0, 1)
        hemi = 0.55 + 0.25 * N[:, 2]
        view = norm(eye - V)
        hv = norm(view + sun)
        spec = sp * np.clip(np.sum(N * hv, 1), 0, 1) ** sh
        for tri in T:
            a, b, c = tri
            if not (ok[a] and ok[b] and ok[c]):
                continue
            x0, y0, x1, y1, x2, y2 = sx[a], sy[a], sx[b], sy[b], sx[c], sy[c]
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            if cull and area >= 0:       # CCW in world = CW on screen (y down) -> front-facing is area<0
                continue
            if abs(area) < 1e-6:
                continue
            xmin = max(int(np.floor(min(x0, x1, x2))), 0); xmax = min(int(np.ceil(max(x0, x1, x2))), W - 1)
            ymin = max(int(np.floor(min(y0, y1, y2))), 0); ymax = min(int(np.ceil(max(y0, y1, y2))), H - 1)
            if xmin > xmax or ymin > ymax:
                continue
            px, py = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
            w0 = ((x1 - px) * (y2 - py) - (x2 - px) * (y1 - py)) / area
            w1 = ((x2 - px) * (y0 - py) - (x0 - px) * (y2 - py)) / area
            w2 = 1 - w0 - w1
            m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not m.any():
                continue
            # perspective-correct weights
            iz = np.array([1 / cz[a], 1 / cz[b], 1 / cz[c]])
            q0, q1, q2 = w0 * iz[0], w1 * iz[1], w2 * iz[2]
            qs = q0 + q1 + q2
            p0, p1, p2 = q0 / qs, q1 / qs, q2 / qs
            depth = 1 / qs
            zb = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            m &= depth < zb
            if not m.any():
                continue
            uv = (p0[..., None] * UV[a] + p1[..., None] * UV[b] + p2[..., None] * UV[c])[m]
            uva, uvb, uvc = UV[a], UV[b], UV[c]
            tex_area = abs((uvb[0] - uva[0]) * (uvc[1] - uva[1]) - (uvc[0] - uva[0]) * (uvb[1] - uva[1])) * levels[0].shape[0] * levels[0].shape[1]
            lod = 0.5 * np.log2(max(tex_area / abs(area / 2) * 0.5, 1e-6)) if tex_area > 0 else 0
            col = sample(levels, uv, lod + 0.2)
            nn = (p0[..., None] * N[a] + p1[..., None] * N[b] + p2[..., None] * N[c])[m]
            nn = norm(nn)
            light = np.clip(nn @ sun, 0, 1)[:, None] * 0.85 + (0.62 + 0.25 * nn[:, 2:3]) * 0.78
            pw = (p0[..., None] * V[a] + p1[..., None] * V[b] + p2[..., None] * V[c])[m]
            vv = norm(eye - pw)
            hh = norm(vv + sun)
            specv = sp * np.clip(np.sum(nn * hh, 1), 0, 1) ** sh
            out = col * light + specv[:, None] * 0.9
            sub = cbuf[ymin:ymax + 1, xmin:xmax + 1]
            sub[m] = out
            zb[m] = depth[m]

    if water_z is not None:
        px, py = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
        dirs = (r[None, None, :] * ((px - W / 2) / focal)[..., None] +
                u[None, None, :] * (-(py - H / 2) / focal)[..., None] + f[None, None, :])
        tt = (water_z - eye[2]) / np.where(np.abs(dirs[..., 2]) < 1e-6, -1e-6, dirs[..., 2])
        hit = eye[None, None, :] + dirs * tt[..., None]
        zdepth = tt * (dirs @ f)
        valid = (tt > 0) & (zdepth < zbuf)
        if water_outline is not None:
            xs, hw = water_outline
            w_at = np.interp(hit[..., 0], xs, hw, left=-1, right=-1)
            valid &= ~(np.abs(hit[..., 1]) < w_at)
        X, Y = hit[..., 0], hit[..., 1]
        rip = (np.sin(X * 3.1 + Y * 1.7) + np.sin(X * 1.3 - Y * 4.1 + 1.0) * 0.7 + np.sin(Y * 7.3 + X * 2.2) * 0.4)
        base = np.array([0.09, 0.22, 0.25]) + 0.035 * rip[..., None]
        cosi = np.clip(-dirs[..., 2] / np.linalg.norm(dirs, axis=-1), 0, 1)
        fres = (0.04 + 0.96 * (1 - cosi) ** 5)[..., None]
        wcol = base * (1 - fres) + sky_at(yy, H)[..., :] * 0 + np.array([0.60, 0.74, 0.86]) * fres
        wcol = wcol * (1 - np.exp(-np.maximum(tt, 0)[..., None] / 28)) + np.array([0.62, 0.74, 0.82]) * np.exp(-np.maximum(tt, 0)[..., None] / 28)
        # shore-ish fade to haze at distance already handled; darken slightly in boat's shadow zone near hull
        cbuf[valid] = wcol[valid]
        zbuf[valid] = zdepth[valid]

    img = cbuf.reshape(size[1], ss, size[0], ss, 3).mean((1, 3))
    img = np.clip(img, 0, 1) ** (1 / 1.0)
    return Image.fromarray((img * 255).astype(np.uint8))


def sky_at(yy, H):
    return np.zeros((1, 1, 3))
