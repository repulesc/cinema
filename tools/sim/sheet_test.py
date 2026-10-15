# Checks the sprite-sheet maths of frame() in hud/src/cinema_ui.lsl against the real texture
# hud/art/take12_icon_sheet_512x256.png. In Second Life the visible window of a face is centred at
# (offset + 0.5) on each axis, repeats <rx, ry> give its size, and v runs up from the bottom of the image.
# For every frame k the window must land exactly on cell k (column k % 4, row k // 4 from the top), frames
# 0..5 must hold a sprite, and frames 6 and 7 (spare) must be empty.
import os
from PIL import Image
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hud", "art", "take12_icon_sheet_512x256.png")
im = Image.open(path).convert("RGBA"); W, H = im.size
assert (W, H) == (512, 256), (W, H)
def lsl_frame(k):                               # mirror of frame() in cinema_ui.lsl
    oy = 0.25
    if k > 3: oy = -0.25
    return 0.25, 0.5, ((k % 4) + 0.5) / 4.0 - 0.5, oy
ok = True
for k in range(8):
    rx, ry, ox, oy = lsl_frame(k)
    u0, u1 = ox + 0.5 - rx / 2, ox + 0.5 + rx / 2           # window in texture coordinates
    v0, v1 = oy + 0.5 - ry / 2, oy + 0.5 + ry / 2           # v up from the bottom
    box = (round(u0 * W), round((1 - v1) * H), round(u1 * W), round((1 - v0) * H))
    want = ((k % 4) * 128, (k // 4) * 128, (k % 4) * 128 + 128, (k // 4) * 128 + 128)
    solid = im.crop(box).getchannel("A").getbbox() is not None
    good = box == want and solid == (k < 6)
    ok &= good
    print(f"frame {k}: window {box} {'==' if box == want else '!='} cell {want}, sprite {'yes' if solid else 'no '} {'ok' if good else 'FAIL'}")
print("sheet checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
