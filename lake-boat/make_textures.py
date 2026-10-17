"""Procedural textures for the lake boat.

Paint history, bottom to top: bare brown wood -> old yellow paint -> green paint.
The green has flaked off in patches (mostly along plank edges, the waterline and the
bow), showing yellow; in a few spots the yellow is gone too and bare wood shows.

Outputs (out/textures):  <name>_d.png diffuse, <name>_n.png normal (alpha = env intensity 0),
                         <name>_s.png specular (alpha = glossiness)
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tex_lib import gnoise, fbm, smoothstep, blur, normal_from_height, to_u8
import layout as L

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "textures")

GREEN = np.array([0.215, 0.430, 0.305])
GREEN_FADED = np.array([0.470, 0.590, 0.500])
YELLOW = np.array([0.790, 0.640, 0.290])
YELLOW_OLD = np.array([0.700, 0.600, 0.380])
WOOD_DARK = np.array([0.300, 0.215, 0.145])
WOOD_LIGHT = np.array([0.530, 0.415, 0.295])
WOOD_GREY = np.array([0.560, 0.520, 0.465])
RUST = np.array([0.430, 0.200, 0.085])
CREAM = np.array([0.770, 0.700, 0.470])


class Ctx:
    """Noise factory in *physical* units: a feature of N mm looks the same size along
    both texture axes even though mm-per-pixel differs."""

    def __init__(self, shape, mmx, mmy, seed):
        self.shape, self.mmx, self.mmy = shape, mmx, mmy
        self.rng = np.random.default_rng(seed)

    def n(self, sx_mm, sy_mm, octaves=1):
        return fbm(self.shape, sx_mm / self.mmx, sy_mm / self.mmy, self.rng, octaves)


def wood_grain(c, axis="x", scale=1.0):
    """Returns (grain 0..1, streak) for planks whose grain runs along `axis`."""
    along, across = (c.mmx, c.mmy) if axis == "x" else (c.mmy, c.mmx)
    h, w = c.shape
    X = (np.arange(w)[None, :] * c.mmx) * np.ones((h, 1))
    Y = (np.arange(h)[:, None] * c.mmy) * np.ones((1, w))
    coord = Y if axis == "x" else X
    warp = (c.n(500, 25) if axis == "x" else c.n(25, 500))
    rings = 0.5 + 0.5 * np.sin(2 * np.pi * (coord / (9.0 * scale) + 2.6 * warp))
    streak = c.n(900, 1.6) if axis == "x" else c.n(1.6, 900)
    fine = c.n(120, 0.9) if axis == "x" else c.n(0.9, 120)
    g = 0.30 * rings + 0.35 * smoothstep(-1.6, 1.6, streak) + 0.35 * smoothstep(-1.4, 1.4, fine)
    return np.clip(g, 0, 1), streak


def paint_stack(c, f, bias, top, mid, cov_top, cov_mid, axis="x", extra=None,
                top_faded=GREEN_FADED, chalky=True):
    """Weathered two-layer paint over wood.  f = 0..1 across each plank (0 = lower edge),
    bias = per-pixel wear bias.  Returns dict of rgb/height/spec/masks."""
    shape = c.shape
    big = c.n(800, 120, 3) if axis == "x" else c.n(120, 800, 3)
    midn = c.n(160, 40, 3) if axis == "x" else c.n(40, 160, 3)
    fine = c.n(14, 5, 2)
    edge_low = np.exp(-f / 0.10)
    edge_hi = np.exp(-(1 - f) / 0.09)
    w1 = 0.55 * big + 0.32 * midn + 0.55 * edge_low + 0.35 * edge_hi + bias
    if extra is not None:
        w1 = w1 + extra
    w1r = w1 + 0.20 * fine
    th1 = np.quantile(w1r, 1.0 - cov_top)
    w2 = w1 + 0.30 * c.n(70, 20, 2) + 0.12 * fine
    th2 = np.quantile(w2, 1.0 - cov_mid)

    m_top = smoothstep(th1 - 0.035, th1 + 0.035, w1r)      # 1 = top coat gone
    m_mid = smoothstep(th2 - 0.04, th2 + 0.04, w2) * m_top  # 1 = mid coat gone too

    # --- wood
    grain, streak = wood_grain(c, axis)
    weather = smoothstep(-0.3, 1.2, c.n(300, 60, 2) if axis == "x" else c.n(60, 300, 2))
    wood = WOOD_DARK + (WOOD_LIGHT - WOOD_DARK) * grain[..., None]
    wood = wood + (WOOD_GREY - wood) * (0.55 * weather)[..., None]

    # --- mid coat (yellow), dirtier and patchy
    ymod = c.n(220, 60, 3) if axis == "x" else c.n(60, 220, 3)
    yel = YELLOW + (YELLOW_OLD - YELLOW) * smoothstep(-0.5, 1.0, ymod)[..., None]
    yel = yel * (1 + 0.05 * ymod[..., None])
    yel = yel * (0.93 + 0.14 * grain[..., None])                # grain prints through
    near = 1 - smoothstep(0.0, 0.5, (w2 - th2) * -1)            # ~1 close to losing yellow
    yel = yel * (1 - 0.18 * near[..., None])

    # --- top coat
    tmod = c.n(900, 200, 2) if axis == "x" else c.n(200, 900, 2)
    topc = top * (1 + 0.075 * tmod[..., None])
    topc = topc * (0.965 + 0.07 * grain[..., None])
    thin = smoothstep(th1 - 0.55, th1, w1r) * (1 - m_top)       # about to flake
    if chalky:
        topc = topc + (top_faded - topc) * (0.50 * thin)[..., None]
    # craquelure along the grain in the thin zone
    cr = c.n(90, 1.8) if axis == "x" else c.n(1.8, 90)
    crack = (1 - smoothstep(0.0, 0.11, np.abs(cr))) * thin
    topc = topc * (1 - 0.40 * crack[..., None])
    # pinhole chips scattered over the sound paint
    pin = c.n(5, 5)
    pins = smoothstep(2.15, 2.5, pin) * (1 - m_top)

    col = topc + (yel - topc) * m_top[..., None]
    col = col + (wood - col) * m_mid[..., None]
    col = col + (yel - col) * (pins * 0.9)[..., None]
    # dark crisp rim where a flake lifted
    rim = np.clip(4.0 * m_top * (1 - m_top), 0, 1) + 0.0
    col = col * (1 - 0.30 * rim[..., None])
    rim2 = np.clip(4.0 * m_mid * (1 - m_mid), 0, 1)
    col = col * (1 - 0.35 * rim2[..., None])

    # --- height & spec
    h = (0.05 * grain
         + 0.20 * (1 - m_mid) * (m_top)               # yellow layer
         + 0.20 * (1 - m_top)                         # top coat (on top of yellow)
         - 0.10 * crack - 0.05 * pins)
    h = h + 0.02 * c.n(4, 4)
    spec = (0.30 * (1 - m_top) + 0.16 * m_top * (1 - m_mid) + 0.04 * m_mid)
    gloss = (0.50 * (1 - m_top) + 0.30 * m_top * (1 - m_mid) + 0.10 * m_mid) * (1 - 0.5 * thin)
    return dict(rgb=col, h=h, spec=spec, gloss=gloss, m_top=m_top, m_mid=m_mid, grain=grain,
                wood=wood, thin=thin)


def streak_stains(c, rgb, strength=0.12, tint=np.array([0.10, 0.09, 0.05])):
    """Vertical rain / rust streaks (run along image y)."""
    s = c.n(5, 70, 2)
    m = smoothstep(0.4, 2.0, s) * strength
    return rgb + (rgb * 0.55 + tint * 0.25 - rgb) * m[..., None]


def save_set(name, rgb, h, spec, gloss, normal_strength=7.0):
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(to_u8(rgb), "RGB").save(os.path.join(OUT, f"{name}_d.png"))
    n = normal_from_height(blur(h, 0.7, 0.7), normal_strength)
    nrgba = np.concatenate([n * 0.5 + 0.5, np.zeros(n.shape[:2] + (1,))], -1)
    Image.fromarray(to_u8(nrgba), "RGBA").save(os.path.join(OUT, f"{name}_n.png"))
    srgba = np.concatenate([np.repeat(spec[..., None], 3, -1), gloss[..., None]], -1)
    Image.fromarray(to_u8(srgba), "RGBA").save(os.path.join(OUT, f"{name}_s.png"))


# ------------------------------------------------------------------ hull planking
def plank_fields(size, mm_len, row_mm):
    """f (0 lower edge..1 upper edge), strake index i (0 = garboard), per pixel."""
    yy = np.arange(size)[:, None] + 0.5
    j = np.floor(yy / L.ROW_H).astype(int)
    in_row = j < L.NROWS
    f = np.where(in_row, ((j + 1) * L.ROW_H - yy) / L.ROW_H, (size - yy) / L.KEEL_H)
    idx = np.where(in_row, L.NSTRAKES - 1 - (j % L.NSTRAKES), 0)
    return (np.broadcast_to(f, (size, size)).copy(),
            np.broadcast_to(idx, (size, size)).copy(),
            np.broadcast_to(np.where(in_row, j, -1), (size, size)).copy())


def hull_exterior(seed=7):
    S = L.TEX
    c = Ctx((S, S), 4300.0 / S, 130.0 / L.ROW_H, seed)
    f, idx, rowj = plank_fields(S, 4300, 130)
    xs = (np.arange(S)[None, :] / S) * np.ones((S, 1))
    # wear bias: sheer strake & waterline & bow get most abuse
    tab = np.array([0.20, -0.04, -0.14, -0.08, 0.03, 0.22])
    bias = tab[idx]
    rng = c.rng
    plank_off = rng.uniform(-0.12, 0.12, L.NROWS + 1)
    bias = bias + plank_off[np.where(rowj < 0, L.NROWS, rowj)]
    bias = bias + 0.30 * smoothstep(0.78, 1.0, xs) + 0.12 * smoothstep(0.22, 0.0, xs)
    st = paint_stack(c, f, bias, GREEN, YELLOW, cov_top=0.31, cov_mid=0.115, axis="x")
    rgb = st["rgb"]
    # lap shadow: dark seam at the very lower edge of each plank, light catch at upper edge
    seam = np.exp(-f / 0.05)
    rgb = rgb * (1 - 0.42 * seam[..., None])
    rgb = rgb * (1 + 0.10 * (np.exp(-(1 - f) / 0.04))[..., None])

    # waterline grime: garboard & 2nd strake, wavy upper limit
    wave = 0.50 + 0.10 * c.n(300, 3) + 0.05 * c.n(40, 3)
    g1 = (1 - smoothstep(wave - 0.06, wave + 0.06, f)) * (idx == 0)
    g2 = (1 - smoothstep(0.10, 0.45, f + 0.25 * c.n(200, 8))) * (idx == 1) * 0.65
    grime = np.clip(g1 + g2, 0, 1) * (0.55 + 0.45 * smoothstep(-1, 1, c.n(250, 20)))
    gcol = np.array([0.105, 0.115, 0.060])
    rgb = rgb + (rgb * 0.45 + gcol * 0.55 - rgb) * (0.72 * grime)[..., None]
    h = st["h"] - 0.04 * grime
    gloss = st["gloss"] * (1 - 0.6 * grime)
    spec = st["spec"] * (1 - 0.5 * grime)

    rgb = streak_stains(c, rgb, 0.10)

    # rivets / roves along each lap (not on the garboard)
    rim = Image.fromarray(np.zeros((S, S), np.uint8))
    img = rgb.copy()
    pitch = 15.7
    for j in range(L.NROWS):
        if (L.NSTRAKES - 1 - (j % L.NSTRAKES)) == 0:
            continue
        yc = (j + 1) * L.ROW_H - 0.13 * L.ROW_H
        for k in range(int(S / pitch) + 1):
            xc = (k + 0.5) * pitch + rng.uniform(-0.5, 0.5)
            x0, x1 = int(xc - 6), int(xc + 7)
            y0, y1 = int(yc - 8), int(yc + 22)
            if x1 >= S or x0 < 0:
                continue
            ys, xs_ = np.mgrid[y0:y1, x0:x1]
            d = np.sqrt(((xs_ - xc) / 2.3) ** 2 + ((ys - yc) / 3.4) ** 2)
            dot = 1 - smoothstep(0.75, 1.1, d)
            ring = smoothstep(0.7, 1.0, d) * (1 - smoothstep(1.0, 1.5, d))
            lit = np.clip(0.5 - 0.5 * ((ys - yc) / 3.4) - 0.2 * ((xs_ - xc) / 2.3), 0, 1)
            bare = st["m_top"][int(yc), int(xc)]
            rusty = rng.random() < 0.22
            sub = img[y0:y1, x0:x1]
            paint_c = sub * (0.92 + 0.22 * lit[..., None])
            metal_c = np.array([0.36, 0.24, 0.17]) * (0.8 + 0.5 * lit[..., None])
            if rusty or bare > 0.5:
                tgt = metal_c * (0.9 + 0.2 * rng.random())
                # rust bleed running down
                bleed = (np.exp(-np.abs(xs_ - xc) / 1.6) *
                         smoothstep(yc, yc + 4, ys) * np.exp(-(ys - yc) / 9.0)) * 0.55
                sub[:] = sub + (RUST * 0.8 - sub) * bleed[..., None]
            else:
                tgt = paint_c
            sub[:] = sub + (tgt - sub) * dot[..., None]
            sub[:] = sub * (1 - 0.35 * ring[..., None])
            h[y0:y1, x0:x1] += 0.34 * dot * (0.5 + 0.5 * lit)
            spec[y0:y1, x0:x1] += 0.10 * dot
    rgb = img
    save_set("hull", rgb, h, spec, gloss, normal_strength=6.0)
    return rgb


def hull_interior(seed=11):
    S = L.TEX
    c = Ctx((S, S), 4300.0 / S, 130.0 / L.ROW_H, seed)
    f, idx, rowj = plank_fields(S, 4300, 130)
    xs = (np.arange(S)[None, :] / S) * np.ones((S, 1))
    tab = np.array([-0.25, -0.15, 0.0, 0.05, 0.10, 0.16])    # bilge protected, top rubbed
    bias = tab[idx] + c.rng.uniform(-0.1, 0.1, L.NROWS + 1)[np.where(rowj < 0, L.NROWS, rowj)]
    st = paint_stack(c, f, bias, CREAM, YELLOW_OLD * 0.95, cov_top=0.30, cov_mid=0.10,
                     axis="x", top_faded=np.array([0.80, 0.76, 0.58]))
    rgb = st["rgb"]
    seam = np.exp(-f / 0.05) + 0.6 * np.exp(-(1 - f) / 0.05)
    rgb = rgb * (1 - 0.36 * np.clip(seam, 0, 1)[..., None])
    # bilge: water stains and dirt, strongest on the lowest strakes + keel board
    low = np.where(idx <= 1, 1.0, 0.0) * (1 - 0.4 * (idx == 1) * f)
    dirt = np.clip(low * (0.55 + 0.45 * smoothstep(-1, 1.2, c.n(200, 15, 2))), 0, 1)
    dcol = np.array([0.150, 0.115, 0.070])
    rgb = rgb + (rgb * 0.4 + dcol * 0.6 - rgb) * (0.75 * dirt)[..., None]
    rgb = streak_stains(c, rgb, 0.14, tint=np.array([0.12, 0.08, 0.04]))
    # dark clench-nail roves along the laps
    img = rgb.copy()
    h = st["h"].copy()
    rng = c.rng
    for j in range(L.NROWS):
        yc = (j + 1) * L.ROW_H - 0.11 * L.ROW_H
        for k in range(int(S / 15.7) + 1):
            xc = (k + 0.5) * 15.7 + rng.uniform(-0.5, 0.5)
            x0, x1, y0, y1 = int(xc - 5), int(xc + 6), int(yc - 6), int(yc + 7)
            if x1 >= S or x0 < 0:
                continue
            ys, xs_ = np.mgrid[y0:y1, x0:x1]
            d = np.sqrt(((xs_ - xc) / 2.0) ** 2 + ((ys - yc) / 3.0) ** 2)
            dot = 1 - smoothstep(0.8, 1.1, d)
            img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - 0.8 * dot[..., None]) + \
                np.array([0.12, 0.10, 0.09]) * (0.8 * dot[..., None])
            h[y0:y1, x0:x1] += 0.25 * dot
    save_set("interior", img, h, st["spec"] * 0.8, st["gloss"] * 0.8, normal_strength=5.0)


# ------------------------------------------------------------------ transom / stem / trim (512)
def hull_end(seed=22):
    S = 512
    c = Ctx((S, S), 950.0 / S, 520.0 / 340.0, seed)   # transom ~0.95 m wide, 0.52 m tall in 340 rows
    TR = 340                                           # rows 0..339 -> transom, rest -> trim strip
    yy = np.arange(S)[:, None] + 0.5
    xx = np.arange(S)[None, :] + 0.5
    # vertical boards on the transom (width ~0.2 m), grain along y
    board_w = S / 4.7
    bpos = (xx / board_w) % 1.0
    f_t = np.broadcast_to(bpos, (S, S)).copy()
    bid = np.floor(xx / board_w)
    top_rows = yy < TR
    # trim strip: horizontal grain
    cx, cy = c.shape, None
    c2 = Ctx((S, S), 1100.0 / S, 80.0 / (S - TR), seed + 1)

    bias = (0.0 + 0.10 * np.exp(-(TR - yy) / 30.0) + 0.10 * np.exp(-yy / 25.0)
            + 0.05 * (np.abs(bpos - 0.5) > 0.44) + 0.04 * np.sin(bid * 2.1)) * np.ones((S, S))
    st = paint_stack(c, f_t, bias, GREEN, YELLOW, cov_top=0.26, cov_mid=0.07, axis="y")
    rgb_t, h_t, sp_t, gl_t = st["rgb"], st["h"], st["spec"], st["gloss"]
    seam = np.exp(-np.minimum(bpos, 1 - bpos) / 0.012)
    rgb_t = rgb_t * (1 - 0.5 * seam[..., None])

    # name, painted in worn cream-yellow
    txt = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(txt)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 52)
    except Exception:
        font = ImageFont.load_default()
    name = "SEEROSE"
    tw = d.textlength(name, font=font)
    d.text(((S - tw) / 2, 150), name, font=font, fill=255)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 26)
    d.text(((S - d.textlength("Starnberg", font=small)) / 2, 214), "Starnberg", font=small, fill=255)
    tm = np.asarray(txt, np.float64) / 255.0
    tm = blur(tm, 0.5, 0.5)
    lw = c.n(60, 30, 3)
    wear_txt = smoothstep(0.7, 1.3, lw + 0.8 * st["m_top"] * 0 + 0.5 * c.n(8, 8))
    tm = tm * (1 - 0.55 * wear_txt) * (1 - 0.8 * st["m_top"])
    letter = np.array([0.82, 0.72, 0.42]) * (0.9 + 0.1 * st["grain"][..., None])
    rgb_t = rgb_t + (letter - rgb_t) * tm[..., None]
    h_t = h_t + 0.12 * tm
    sp_t = sp_t + 0.1 * tm

    # trim strip
    f2 = np.broadcast_to(np.clip((S - yy) / (S - TR), 0, 1), (S, S)).copy()
    st2 = paint_stack(c2, f2, 0.05 * np.ones((S, S)), GREEN, YELLOW, cov_top=0.22, cov_mid=0.06, axis="x")

    rgb = np.where(top_rows[..., None], rgb_t, st2["rgb"])
    h = np.where(top_rows, h_t, st2["h"])
    spec = np.where(top_rows, sp_t, st2["spec"])
    gloss = np.where(top_rows, gl_t, st2["gloss"])
    rgb = streak_stains(c, rgb, 0.08)
    # thin dark line between regions
    save_set("hull_end", rgb, h, spec, gloss, normal_strength=5.0)


# ------------------------------------------------------------------ bare wood (benches, gunwale, ribs)
def wood(seed=31):
    S = 512
    c = Ctx((S, S), 1000.0 / S, 400.0 / S, seed)
    grain, streak = wood_grain(c, "x", scale=0.9)
    w = WOOD_DARK + (WOOD_LIGHT - WOOD_DARK) * grain[..., None]
    wear = smoothstep(-0.4, 1.3, c.n(260, 50, 3))
    w = w + (WOOD_GREY - w) * (0.45 * wear)[..., None]
    # a few dark knots
    rng = c.rng
    X = np.arange(S)[None, :] * c.mmx
    Y = np.arange(S)[:, None] * c.mmy
    h = 0.12 * grain
    for _ in range(4):
        kx, ky = rng.uniform(0, 1000), rng.uniform(40, 360)
        d = np.sqrt(((X - kx) / 22.0) ** 2 + ((Y - ky) / 9.0) ** 2)
        k = np.exp(-d * d)
        w = w * (1 - 0.45 * k[..., None])
        h = h - 0.15 * k
    # grime in grain direction + varnish remnants (glossier patches)
    vn = smoothstep(0.2, 1.4, c.n(200, 50, 2))
    w = w * (1 - 0.10 * smoothstep(0.5, 2.0, c.n(90, 6))[..., None])
    spec = 0.05 + 0.20 * vn
    gloss = 0.12 + 0.35 * vn
    save_set("wood", w, h, spec, gloss, normal_strength=4.0)


def metal(seed=41):
    S = 128
    c = Ctx((S, S), 1.0, 1.0, seed)
    base = np.array([0.150, 0.150, 0.155])
    n = c.n(3, 3, 3)
    rust = smoothstep(0.35, 1.4, c.n(4, 4, 3))
    rgb = base[None, None, :] * (1 + 0.25 * n[..., None])
    rgb = rgb + (RUST * 0.9 - rgb) * (0.75 * rust)[..., None]
    h = 0.12 * n + 0.08 * rust
    spec = 0.45 * (1 - rust) + 0.05
    gloss = 0.45 * (1 - rust) + 0.1
    save_set("metal", rgb, h, spec, gloss, normal_strength=3.0)


if __name__ == "__main__":
    which = sys.argv[1:] or ["hull", "interior", "hull_end", "wood", "metal"]
    for w in which:
        {"hull": hull_exterior, "interior": hull_interior, "hull_end": hull_end,
         "wood": wood, "metal": metal}[w]()
        print("wrote", w)
