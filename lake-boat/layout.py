"""Shared texture-atlas layout for the planked hull (geometry + textures agree on this)."""

TEX = 1024          # hull / interior texture size
ROW_H = 80          # pixels per plank row
NROWS = 12          # 6 strakes starboard + 6 port
KEEL_H = TEX - NROWS * ROW_H   # 64 px strip at the bottom of the image for the keel board
NSTRAKES = 6

GUTTER = 0.04       # fraction of a row kept free at both plank edges (mip bleed / lap shadow)


def row_for(side, i):
    """Image row index for strake i (0 = garboard at the keel .. 5 = sheer strake).
    side: -1 starboard, +1 port. Higher strakes sit in the row above, so the lap
    step face between two strakes maps to the thin seam between two rows."""
    base = 0 if side < 0 else NSTRAKES
    return base + (NSTRAKES - 1 - i)


def strake_v(side, i, frac):
    """v coordinate (0 = bottom of image) for strake i at frac 0 (lower edge) .. 1 (upper edge)."""
    j = row_for(side, i)
    frac = GUTTER + (1 - 2 * GUTTER) * frac
    y = (j + 1) * ROW_H - frac * ROW_H          # image row (0 = top)
    return 1.0 - y / TEX


def keel_v(frac):
    """v for the keel board strip (frac 0..1 across the board)."""
    y0 = NROWS * ROW_H
    y = y0 + 3 + frac * (KEEL_H - 6)
    return 1.0 - y / TEX
