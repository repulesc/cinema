# Marketing material for Take 12

| File | What |
|---|---|
| `marketplace_listing.md` | Copy-paste text for the Marketplace listing (7.0: short, like the product): name, description, features, tags, promo lines, the "what is new" message, image list |
| `legacy/` | The earlier listings and intros (4.4, 4.8) |
| `adboard_square_1024.png` | The Marketplace main image (7.0.1: one frame): a dusk horizon, the clapper, "TAKE 12" and "A camera for Second Life." |
| `adboard_portrait_3x4_768x1024.png`, `adboard_landscape_4x3_1024x768.png`, `adboard_wide_1024x512.png` | The same frame in the other ratios |
| `adboard_vendor_1024.png`, `adboard_vendor_512.png` | The same frame with bigger type, for in-world vendor displays |

The free Take 12 Watch has its own listing and board: `watch/marketing/`, and the free Take 12 Scenery its own: `scenery/marketing/`. Regenerate all of them with `python3 tools/art/make_adboard.py`. They use drawn pixel-art views, so swap in real snapshots as extra listing images (see the end of `marketplace_listing.md`).
