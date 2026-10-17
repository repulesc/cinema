"""Small numpy helpers for procedural textures (no scipy needed)."""
import numpy as np


def gnoise(shape, sx, sy, rng):
    """Periodic gaussian-filtered noise, zero mean / unit std.
    sx, sy are feature sizes (sigma) in pixels along x / y."""
    h, w = shape
    n = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    F = np.fft.fft2(n) * np.exp(-2 * np.pi ** 2 * ((sx * fx) ** 2 + (sy * fy) ** 2))
    r = np.fft.ifft2(F).real
    return (r - r.mean()) / (r.std() + 1e-9)


def fbm(shape, size_x, size_y, rng, octaves=4, gain=0.55):
    """Sum of octaves; sizes halve every octave."""
    out = np.zeros(shape)
    amp, tot = 1.0, 0.0
    for _ in range(octaves):
        out += amp * gnoise(shape, max(size_x, 0.4), max(size_y, 0.4), rng)
        tot += amp
        amp *= gain
        size_x *= 0.5
        size_y *= 0.5
    out /= tot
    return (out - out.mean()) / (out.std() + 1e-9)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blur(a, sx, sy):
    h, w = a.shape[:2]
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    k = np.exp(-2 * np.pi ** 2 * ((sx * fx) ** 2 + (sy * fy) ** 2))
    if a.ndim == 2:
        return np.fft.ifft2(np.fft.fft2(a) * k).real
    return np.stack([np.fft.ifft2(np.fft.fft2(a[..., c]) * k).real for c in range(a.shape[2])], -1)


def normal_from_height(hgt, strength=1.0):
    """Tangent-space (OpenGL, +Y up) normal map from a height field."""
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5 * strength
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5 * strength
    # image rows grow downward, so +v (up) is -row direction
    nx, ny, nz = -gx, gy, np.ones_like(gx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], -1)


def lerp(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) == 2 else t
    return a + (b - a) * t


def to_u8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
