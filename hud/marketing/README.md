# Marketing material for Take 12

| File | What |
|---|---|
| `marketplace_listing.md` | Copy-paste text for the Marketplace listing: name ideas, description, features, tags, promo lines, image list |
| `adboard_square_1024.png` | Square ad board for the Marketplace main image |
| `adboard_portrait_3x4_768x1024.png` | **3:4 portrait** ad (one big view, three small views, chips) |
| `adboard_landscape_4x3_1024x768.png` | 4:3 landscape ad, in case a listing shows the picture the other way round |
| `adboard_wide_1024x512.png` | Wide ad board for an in-world vendor or banner |
| `adboard_vendor_1024.png`, `adboard_vendor_512.png` | A bolder, simpler square for in-world vendor displays (such as Caspervend), where the picture is small: one big on-screen view with the button in the corner, the three clapper looks, and four short chips |

The Lite boards are in `hud-lite/marketing/`. Regenerate all of them with `python3 tools/art/make_adboard.py`. They use drawn pixel-art views, so swap in real snapshots as extra listing images (see the end of `marketplace_listing.md`).
