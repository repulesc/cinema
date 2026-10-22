# Marketing material for Take 12

| File | What |
|---|---|
| `marketplace_listing.md` | Copy-paste text for the Marketplace listing (6.0.1; the Full description is kept under the Marketplace's 5000 characters): name ideas, description, features, tags, promo lines, the "what is new" update message, image list |
| `legacy/` | The earlier listings and intros (4.4, 4.8) |
| `adboard_square_1024.png` | Square ad board for the Marketplace main image (with the coral "NEW: YOUR LENS" label and the "85 MM" lens readout) |
| `adboard_portrait_3x4_768x1024.png` | **3:4 portrait** ad (one big view, three small views, chips) |
| `adboard_landscape_4x3_1024x768.png` | 4:3 landscape ad, in case a listing shows the picture the other way round |
| `adboard_wide_1024x512.png` | Wide ad board for an in-world vendor or banner |
| `adboard_vendor_1024.png`, `adboard_vendor_512.png` | A bolder, simpler square for in-world vendor displays (such as Caspervend), where the picture is small: one big on-screen view with the button in the corner, the three clapper looks, and four short chips |

The free Take 12 Watch has its own listing and board: `watch/marketing/`, and the free Take 12 Scenery its own: `scenery/marketing/`. Regenerate all of them with `python3 tools/art/make_adboard.py`. They use drawn pixel-art views, so swap in real snapshots as extra listing images (see the end of `marketplace_listing.md`).
