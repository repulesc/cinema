"""Parametric clinker-built lake rowing boat (retro "Seerose" style), ~4.4 m.

build(lod) -> MeshSet with 5 materials:
    hull_planks  outer planking + keel board          (hull_d.png)
    interior     inner planking                       (interior_d.png)
    hull_end     transom, stem post, bow deck         (hull_end_d.png)
    wood         gunwale, benches, ribs, floor, keel  (wood_d.png)
    metal        rowlocks, stem band, bow ring        (metal_d.png)
"""
import numpy as np
from meshlib import (MeshSet, add_grid, sweep, rounded_rect, circle_profile, circle_path, norm)
import layout as LY

# ---------------------------------------------------------------- main dimensions (metres)
LEN0 = 3.95            # stem-to-transom length at the keel line (rake adds ~0.4)
X0 = -LEN0 / 2
BMAX = 0.66            # half beam at the gunwale
SM = 0.42              # station of max beam (0 = stern, 1 = bow)
BST = 0.40             # half breadth of the transom at the gunwale
KEEL = 0.20            # keel board half width as a fraction of the half breadth
KP = 1.7               # section fullness
ZP = 1.35              # section height distribution (flat bottom -> flared sides)
RB, RS = 0.28, 0.13    # stem rake, transom rake
THK = 0.024            # plank thickness
DELTA = 0.012          # clinker lap step
NSTRAKE = LY.NSTRAKES

LODS = {
    3: dict(ns=34, nt=2, nt_in=1, steps=True, ribs=10, slats=True, rail_n=20, detail=True),
    2: dict(ns=18, nt=2, nt_in=1, steps=True, ribs=5, slats=False, rail_n=12, detail=True),
    1: dict(ns=10, nt=1, nt_in=1, steps=False, ribs=0, slats=False, rail_n=7, detail=False),
    0: dict(ns=6, nt=1, nt_in=1, steps=False, ribs=0, slats=False, rail_n=5, detail=False),
}


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def Bg(s):
    s = np.asarray(s, float)
    st = BST + (BMAX - BST) * (1 - (1 - np.clip(s / SM, 0, 1)) ** 2)
    w = np.clip((s - SM) / (1 - SM), 0, 1)
    bw = BMAX * (1 - w ** 2)
    return np.where(s < SM, st, bw)


def zk(s):
    s = np.asarray(s, float)
    stern = 0.10 * np.clip(1 - s / 0.18, 0, 1) ** 2
    bow = 0.34 * np.clip((s - 0.70) / 0.30, 0, 1) ** 2.2
    return stern + bow


def zg(s):
    s = np.asarray(s, float)
    bow = 0.22 * np.clip((s - 0.45) / 0.55, 0, 1) ** 2.4
    stern = 0.05 * np.clip(1 - s / 0.35, 0, 1) ** 2
    return 0.55 + bow + stern


def pos(s, t, side):
    s, t = np.broadcast_arrays(np.asarray(s, float), np.asarray(t, float))
    bg = Bg(s)
    bk = KEEL * bg
    y = side * (bk + (bg - bk) * (1 - (1 - t) ** KP))
    zf = t ** ZP
    z = zk(s) + (zg(s) - zk(s)) * zf
    x = X0 + LEN0 * s + RB * s ** 4 * zf - RS * (1 - s) ** 3 * zf
    return np.stack([x, y, z], -1)


def outward(P):
    c = P.copy()
    c[..., 1] = 0
    c[..., 2] = 0.45
    return P - c


def nrm(s, t, side):
    """Outward unit normal of the mid-surface (finite differences)."""
    s, t = np.broadcast_arrays(np.asarray(s, float), np.asarray(t, float))
    e = 1e-3
    s1, s0 = np.clip(s + e, 0, 1), np.clip(s - e, 0, 1)
    t1, t0 = np.clip(t + e, 0, 1), np.clip(t - e, 0, 1)
    Ps = pos(s1, t, side) - pos(s0, t, side)
    Pt = pos(s, t1, side) - pos(s, t0, side)
    n = norm(np.cross(Ps, Pt))
    flip = np.sum(n * outward(pos(s, t, side)), -1) < 0
    return np.where(flip[..., None], -n, n)


# equal-arc strake boundaries measured at the beamiest station
def _strake_bounds():
    t = np.linspace(0, 1, 600)
    P = pos(np.full_like(t, SM), t, 1)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    targets = np.linspace(0, d[-1], NSTRAKE + 1)
    return np.interp(targets, d, t)


TB = _strake_bounds()


def spaced(n, power=1.0):
    """Station values 0..1, denser near both ends."""
    u = np.linspace(0, 1, n + 1)
    return 0.5 - 0.5 * np.cos(np.pi * u)


def taper(s):
    return 1 - 0.85 * ss(0.92, 1.0, s)


def inner_y(x, zabs):
    """Inner half-width of the hull at (x, z) (for benches and floorboards)."""
    s = np.clip((x - X0) / LEN0, 0.0, 1.0)
    h = zg(s) - zk(s)
    t = np.clip(((zabs - zk(s)) / h), 0, 1) ** (1 / ZP)
    bg, bk = Bg(s), KEEL * Bg(s)
    return bk + (bg - bk) * (1 - (1 - t) ** KP) - THK * 1.2


# ---------------------------------------------------------------- builder
def build(lod=3):
    cfg = LODS[lod]
    ms = MeshSet()
    S = spaced(cfg["ns"])
    rng = np.random.default_rng(5)

    def uv_u(s):
        return 0.004 + 0.992 * s

    # --- outer planking, lap steps, inner planking
    for side in (+1, -1):
        for i in range(NSTRAKE):
            nt = cfg["nt"]
            fr = np.linspace(0, 1, nt + 1)
            t = TB[i] + (TB[i + 1] - TB[i]) * fr
            s2, t2 = np.meshgrid(S, t, indexing="ij")
            n = nrm(s2, t2, side)
            if cfg["steps"]:
                off = DELTA * (1 - 0.85 * fr)[None, :] * taper(s2)
            else:
                off = DELTA * 0.5 * np.ones_like(t2) * taper(s2)
            P = pos(s2, t2, side) + n * off[..., None]
            UV = np.stack([np.broadcast_to(uv_u(s2), s2.shape),
                           np.broadcast_to(np.array([LY.strake_v(side, i, f) for f in fr])[None, :], s2.shape)], -1)
            add_grid(ms, "hull_planks", P, UV, outward)

            # inner shell, same UV rows
            nti = cfg["nt_in"]
            fri = np.linspace(0, 1, nti + 1)
            ti = TB[i] + (TB[i + 1] - TB[i]) * fri
            s3, t3 = np.meshgrid(S, ti, indexing="ij")
            Pi = pos(s3, t3, side) - nrm(s3, t3, side) * THK
            UVi = np.stack([np.broadcast_to(uv_u(s3), s3.shape),
                            np.broadcast_to(np.array([LY.strake_v(side, i, f) for f in fri])[None, :], s3.shape)], -1)
            add_grid(ms, "interior", Pi, UVi, lambda c: -outward(c))

            # lap step face between strake i and i+1
            if cfg["steps"] and i < NSTRAKE - 1:
                s4 = S
                tt = TB[i + 1]
                n4 = nrm(s4, np.full_like(s4, tt), side)
                a = pos(s4, np.full_like(s4, tt), side) + n4 * (DELTA * 0.15 * taper(s4))[:, None]
                b = pos(s4, np.full_like(s4, tt), side) + n4 * (DELTA * taper(s4))[:, None]
                P4 = np.stack([a, b], 1)
                UV4 = np.stack([np.stack([uv_u(s4), np.full_like(s4, LY.strake_v(side, i, 1.0))], -1),
                                np.stack([uv_u(s4), np.full_like(s4, LY.strake_v(side, i + 1, 0.0))], -1)], 1)
                add_grid(ms, "hull_planks", P4, UV4, outward)

    # --- keel board (outer + inner), between the two garboard edges
    def edge(side, off, inward=False):
        n = nrm(S, np.zeros_like(S), side)
        base = pos(S, np.zeros_like(S), side)
        return base + n * (off * taper(S))[:, None] if not inward else base - n * off

    eL, eR = edge(+1, DELTA * (0.5 if not cfg["steps"] else 1.0)), edge(-1, DELTA * (0.5 if not cfg["steps"] else 1.0))
    w = np.linspace(0, 1, 3)
    P = eL[:, None, :] * (1 - w)[None, :, None] + eR[:, None, :] * w[None, :, None]
    UV = np.stack([np.broadcast_to(uv_u(S)[:, None], (len(S), 3)),
                   np.broadcast_to(np.array([LY.keel_v(x) for x in w])[None, :], (len(S), 3))], -1)
    add_grid(ms, "hull_planks", P, UV, np.array([0, 0, -1.0]))
    eLi, eRi = edge(+1, THK, True), edge(-1, THK, True)
    P = eLi[:, None, :] * (1 - w)[None, :, None] + eRi[:, None, :] * w[None, :, None]
    add_grid(ms, "interior", P, UV, np.array([0, 0, 1.0]))

    # --- transom (outer painted face, inner raw face)
    tt = np.linspace(0, 1, 7)
    ww = np.linspace(0, 1, 7)
    Lp = pos(np.zeros_like(tt), tt, +1)
    Rp = pos(np.zeros_like(tt), tt, -1)
    P = Lp[:, None, :] * (1 - ww)[None, :, None] + Rp[:, None, :] * ww[None, :, None]
    zlo, zhi = P[..., 2].min(), P[..., 2].max()
    u = 0.5 - P[..., 1] / 0.96
    v = 0.345 + (P[..., 2] - zlo) / (zhi - zlo) * (0.99 - 0.345)
    add_grid(ms, "hull_end", P, np.stack([u, v], -1), np.array([-1.0, 0, 0]))
    s_in = 0.0075
    Lp = pos(np.full_like(tt, s_in), tt, +1) - nrm(np.full_like(tt, s_in), tt, +1) * THK
    Rp = pos(np.full_like(tt, s_in), tt, -1) - nrm(np.full_like(tt, s_in), tt, -1) * THK
    P2 = Lp[:, None, :] * (1 - ww)[None, :, None] + Rp[:, None, :] * ww[None, :, None]
    add_grid(ms, "wood", P2, np.stack([0.5 + P2[..., 1] / 1.0, (P2[..., 2] - zlo) / 0.8], -1), np.array([1.0, 0, 0]))

    # --- plank ends at the transom (end grain), closes the lap gap behind the transom face
    for side in (+1, -1):
        for i in range(NSTRAKE):
            fr = np.linspace(0, 1, cfg["nt"] + 1)
            tq = TB[i] + (TB[i + 1] - TB[i]) * fr
            s0 = np.zeros_like(tq)
            base = pos(s0, tq, side)
            nn = nrm(s0, tq, side)
            offs = DELTA * (1 - 0.85 * fr) if cfg["steps"] else np.full_like(fr, DELTA * 0.5)
            P = np.stack([base, base + nn * offs[:, None]], 1)
            UVe = np.stack([np.stack([np.full_like(fr, 0.30), 0.30 + 0.0 * fr], -1),
                            np.stack([np.full_like(fr, 0.32), 0.32 + 0.0 * fr], -1)], 1)
            add_grid(ms, "wood", P, UVe, np.array([-1.0, 0, 0]))
    wq = np.linspace(0, 1, 3)
    Lb, Rb = pos(0.0, 0.0, +1), pos(0.0, 0.0, -1)
    row = Lb[None, :] * (1 - wq)[:, None] + Rb[None, :] * wq[:, None]
    P = np.stack([row, row - [0, 0, DELTA]], 1)
    add_grid(ms, "wood", P, np.stack([np.full(P.shape[:2], 0.31), np.full(P.shape[:2], 0.11)], -1), np.array([-1.0, 0, 0]))

    # --- stem post + iron band + ring
    ts = np.linspace(0.0, 1.0, 9)
    stem = pos(np.ones_like(ts), ts, +1)
    stem = np.vstack([stem, stem[-1] + [0.045, 0, 0.012]])
    prof = np.array([(0.0275, -0.020), (0.0275, 0.004), (0.0, 0.025), (-0.0275, 0.004), (-0.0275, -0.020)])
    sweep(ms, "hull_end", stem, prof, up=(1, 0, 0), u_len=0.8, v_len=0.4, uv_off=(0.02, 0.02), caps=True)
    band = stem[:6]
    sweep(ms, "metal", band, rounded_rect(0.014, 0.006, 0.002, cy=0.0262), up=(1, 0, 0), u_len=0.6, v_len=0.1, caps=True)
    zr = pos(1.0, 0.62, +1)
    ring_c = zr + np.array([0.058, 0, -0.012])
    sweep(ms, "metal", circle_path(ring_c, 0.032, "y", n=18 if lod >= 2 else (8 if lod == 1 else 6)),
          circle_profile(0.0055, 6 if lod >= 2 else (4 if lod == 1 else 3)),
          closed_path=True, caps=False, u_len=0.3, v_len=0.03)

    # --- keel strip (wood, tarred): runs into the stem foot and tapers
    kS = spaced(cfg["rail_n"])
    kp = pos(kS, np.zeros_like(kS), +1)
    kp[:, 1] = 0
    sb = 1 - 0.65 * ss(0.82, 1.0, kS)
    sa = 1 - 0.40 * ss(0.82, 1.0, kS)
    kp[:, 2] -= 0.004 + 0.013 * sb
    sweep(ms, "wood", kp, rounded_rect(0.045, 0.026, 0.006), u_len=4.5, v_len=0.3, uv_off=(0.0, 0.05),
          scale=np.stack([sa, sb], 1))

    # --- gunwale cap, inwale, rubbing strake, transom rail
    rS = spaced(cfg["rail_n"])
    cap_prof = rounded_rect(0.064, 0.028, 0.008 if cfg["detail"] else 0.0)
    for side in (+1, -1):
        sc = 0.002 + 0.983 * rS
        top = pos(sc, np.ones_like(sc), side)
        top[:, 2] += 0.014
        sweep(ms, "wood", top, cap_prof, u_len=4.6, v_len=0.45, uv_off=(0.0, 0.05))
        s_in = 0.03 + 0.85 * rS
        t_in = np.full_like(s_in, 0.91)
        inw = pos(s_in, t_in, side) - nrm(s_in, t_in, side) * (THK + 0.0125)
        s_r = 0.0 + 0.975 * rS
        t_r = np.full_like(s_r, 0.80)
        rub = pos(s_r, t_r, side) + nrm(s_r, t_r, side) * (DELTA * 0.4 + 0.010) * taper(s_r)[:, None]
        sweep(ms, "wood", rub, rounded_rect(0.022, 0.034), u_len=4.5, v_len=0.3, uv_off=(0.0, 0.5))
        if cfg["detail"]:
            sweep(ms, "wood", inw, rounded_rect(0.025, 0.044), u_len=4.0, v_len=0.3, uv_off=(0.1, 0.4))
    zt = zg(0.0) + 0.014
    xt = pos(0.0, 1.0, +1)[0]
    sweep(ms, "wood", np.array([[xt, BST + 0.03, zt], [xt, 0.0, zt], [xt, -BST - 0.03, zt]]), cap_prof,
          up=(0, 0, 1), u_len=1.0, v_len=0.45, uv_off=(0.0, 0.3))

    # --- bow deck (breasthook), painted top, raw underside
    sd = np.linspace(0.885, 0.992, 10 if lod >= 2 else 4)
    ww = np.linspace(0, 1, 5)
    Lt = pos(sd, np.ones_like(sd), +1)
    Rt = pos(sd, np.ones_like(sd), -1)
    P = Lt[:, None, :] * (1 - ww)[None, :, None] + Rt[:, None, :] * ww[None, :, None]
    P[..., 2] += 0.020
    UV = np.stack([np.clip(P[..., 0] * 0.28 + 0.5, 0.02, 0.98), np.clip(0.17 + 0.4 * P[..., 1], 0.03, 0.31)], -1)
    add_grid(ms, "hull_end", P, UV, np.array([0, 0, 1.0]))
    P2 = P.copy()
    P2[..., 2] -= 0.020
    add_grid(ms, "wood", P2, np.clip(UV, 0, 1), np.array([0, 0, -1.0]))

    # --- thwarts (benches) with cleats
    benches = [(-1.52, 0.335), (-0.34, 0.285), (0.62, 0.30)]    # (x, z above keel line = absolute z)
    bench_info = []
    for bx, bz in benches:
        y = float(inner_y(bx, bz)) - 0.004
        sweep(ms, "wood", np.array([[bx, -y, bz], [bx, y, bz]]), rounded_rect(0.26, 0.028, 0.007),
              u_len=1.4, v_len=0.62, uv_off=(rng.uniform(0, 0.05), rng.uniform(0, 0.3)))
        for sd_ in ((+1, -1) if cfg["detail"] else ()):
            sweep(ms, "wood", np.array([[bx - 0.15, sd_ * (y - 0.012), bz - 0.036], [bx + 0.15, sd_ * (y - 0.012), bz - 0.036]]),
                  rounded_rect(0.026, 0.04, 0.004), u_len=0.6, v_len=0.2, uv_off=(0.1, 0.1))
        bench_info.append((bx, bz + 0.014))

    # --- floorboards
    z_f = 0.09
    if cfg["slats"]:
        xs = np.arange(-1.28, 0.93, 0.097)
        for x in xs:
            y = float(inner_y(x, z_f + 0.01)) - 0.014
            if y < 0.05:
                continue
            sweep(ms, "wood", np.array([[x, -y, z_f], [x, y, z_f]]), rounded_rect(0.085, 0.02, 0.004),
                  u_len=1.4, v_len=0.45, uv_off=(rng.uniform(0, 0.25), rng.uniform(0, 0.5)), caps=True)
    else:
        for x0_, x1_ in (((-1.28, -0.25), (-0.23, 0.93)) if lod >= 1 else ((-1.28, 0.93),)):
            xm = 0.5 * (x0_ + x1_)
            y = float(inner_y(xm, z_f + 0.01)) - 0.014
            sweep(ms, "wood", np.array([[xm, -y, z_f], [xm, y, z_f]]), rounded_rect(x1_ - x0_, 0.02, 0.004),
                  u_len=1.4, v_len=0.45, caps=True)

    # --- ribs (steam-bent frames) on the inner planking
    nrib = cfg["ribs"]
    if nrib:
        rib_prof = rounded_rect(0.022, 0.040)
        tr = np.concatenate([np.linspace(0.97, 0.0, 9), ])
        for k in range(nrib):
            sr = 0.14 + 0.72 * (k + 0.5) / nrib
            tl, trr = tr, tr[::-1][1:]
            left = pos(np.full_like(tl, sr), tl, +1) - nrm(np.full_like(tl, sr), tl, +1) * (THK + 0.011)
            right = pos(np.full_like(trr, sr), trr, -1) - nrm(np.full_like(trr, sr), trr, -1) * (THK + 0.011)
            path = np.vstack([left, right])
            sweep(ms, "wood", path, rib_prof, up=(1, 0, 0), u_len=2.6, v_len=0.12,
                  uv_off=(rng.uniform(0, 0.3), rng.uniform(0, 0.7)), caps=True)

    # --- rowlocks on the gunwale, just ahead of the rowing thwart
    xr = benches[1][0] + 0.12
    sr = (xr - X0) / LEN0
    for side in (+1, -1):
        g = pos(sr, 1.0, side)
        yg = g[1]
        zb = g[2] + 0.028
        sweep(ms, "wood", np.array([[xr - 0.05, yg, zb + 0.022], [xr + 0.05, yg, zb + 0.022]]),
              rounded_rect(0.07, 0.044, 0.008), u_len=0.3, v_len=0.3, uv_off=(0.2, 0.2))
        top = zb + 0.044
        th = np.linspace(np.pi, 2 * np.pi, 9 if lod >= 2 else 5)
        r = 0.026
        horn = [[xr - r, yg, top + 0.045], [xr - r, yg, top + 0.012]]
        horn += [[xr + r * np.cos(a), yg, top + 0.012 + r * np.sin(a) * 1.2] for a in th[1:-1]]
        horn += [[xr + r, yg, top + 0.012], [xr + r, yg, top + 0.045]]
        horn = np.array(horn)
        if lod >= 1:
            sweep(ms, "metal", horn, circle_profile(0.0055, 6), up=(0, 1, 0), u_len=0.3, v_len=0.03, caps=True)
            sweep(ms, "metal", np.array([[xr, yg, top + 0.001], [xr, yg, top - 0.05]]), circle_profile(0.0075, 6),
                  up=(1, 0, 0), u_len=0.1, v_len=0.05, caps=True)
        else:
            sweep(ms, "metal", np.array([[xr, yg, top + 0.04], [xr, yg, top - 0.01]]), rounded_rect(0.05, 0.012),
                  up=(1, 0, 0), u_len=0.1, v_len=0.05, caps=True)

    info = dict(benches=bench_info, rowlock_x=xr)
    return ms, info


def physics_hull(zlid=0.115):
    """Low-poly closed volume for the SL physics shape: the hull up to just above the
    floorboards, so passengers can stand inside the boat."""
    ms = MeshSet()
    S = np.array([0.0, 0.10, 0.25, 0.42, 0.58, 0.72, 0.84, 0.92, 0.965])
    rings = []
    for s in S:
        h = float(zg(s) - zk(s))
        zl = max(zlid, float(zk(s)) + 0.05)
        tl = ((zl - float(zk(s))) / h) ** (1 / ZP)
        T = np.array([0.0, tl * 0.5, tl])
        pts = [pos(s, t, +1) for t in T[::-1]] + [pos(s, t, -1) for t in T]
        rings.append(np.array(pts))
    rings = np.array(rings)
    ns, m = rings.shape[:2]
    V = rings.reshape(-1, 3)
    idx = np.arange(ns * m).reshape(ns, m)
    groups = []
    side, lid, cap0, cap1 = [], [], [], []
    for i in range(ns - 1):
        for k in range(m - 1):
            a, b_, c, d = idx[i, k], idx[i + 1, k], idx[i + 1, k + 1], idx[i, k + 1]
            side += [[a, b_, c], [a, c, d]]
        a, b_, c, d = idx[i, 0], idx[i + 1, 0], idx[i + 1, m - 1], idx[i, m - 1]
        lid += [[a, b_, c], [a, c, d]]
    for k in range(1, m - 1):
        cap0.append([idx[0, 0], idx[0, k], idx[0, k + 1]])
        cap1.append([idx[ns - 1, 0], idx[ns - 1, k], idx[ns - 1, k + 1]])
    c0 = V.mean(0)
    out = []
    refs = (None, np.array([0, 0, 1.0]), np.array([-1.0, 0, 0]), np.array([1.0, 0, 0]))
    for grp, ref in zip((side, lid, cap0, cap1), refs):   # orient each group as a whole
        g = np.array(grp)
        fn = np.cross(V[g[:, 1]] - V[g[:, 0]], V[g[:, 2]] - V[g[:, 0]])
        r = (V[g].mean(1) - c0) if ref is None else ref
        if (fn * r).sum() < 0:
            g = g[:, [0, 2, 1]]
        out.append(g)
    tris = np.vstack(out)
    ms.add("hull_planks", V, np.zeros((len(V), 2)) + 0.5, tris)
    return ms
