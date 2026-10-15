#!/usr/bin/env python3
"""The button idle (open clapper) and while the camera runs (closed clapper), both at full strength, for each of the
three looks, at real on-screen size on a light and a dark background. Writes hud/art/running_looks_preview.png.

    python3 tools/art/make_running_looks.py
"""
import os
from PIL import Image, ImageDraw
import make_icon as icon

def main():
    looks = icon.LOOKS
    cw, ch, top = 150, 90, 34
    img = Image.new("RGB", (40 + cw * 4, top + ch * len(looks)), (246, 245, 240))
    d = ImageDraw.Draw(img)
    heads = ["idle (light)", "running (light)", "idle (dark)", "running (dark)"]
    for j, h in enumerate(heads):
        d.text((40 + j * cw + 30, 12), h, fill=(60, 60, 70))
    for i, look in enumerate(looks):
        sh = icon.sheet(look)
        frames = [sh.crop((0, 0, 128, 128)), sh.crop((128, 0, 256, 128))]      # open, closed
        y0 = top + i * ch
        d.text((6, y0 + ch // 2 - 6), look[:5], fill=(60, 60, 70))
        for j in range(4):
            bg = (232, 236, 242) if j < 2 else (30, 30, 38)
            cell = Image.new("RGBA", (cw - 8, ch - 8), bg + (255,))
            f = frames[j % 2].resize((40, 40), Image.LANCZOS)
            cell.alpha_composite(f, ((cw - 8 - 40) // 2, (ch - 8 - 40) // 2))
            img.paste(cell.convert("RGB"), (40 + j * cw + 4, y0 + 4))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hud", "art", "running_looks_preview.png")
    img.save(out)
    print("wrote", os.path.normpath(out))

if __name__ == "__main__":
    main()
