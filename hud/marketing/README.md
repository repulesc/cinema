# Marketing material for Take 12

| File | What |
|---|---|
| `marketplace_listing.md` | Copy-paste text for the Marketplace listing (8.0): name, description, features, tags, promo lines, the "what is new" message, image list |
| `legacy/` | The earlier listings and intros (4.4, 4.8) |
| `adboard_square_1024.png` | The Marketplace main image: a dusk horizon, the [12], "TAKE 12" and "A cinematic camera for Second Life." |
| `adboard_portrait_3x4_768x1024.png`, `adboard_landscape_4x3_1024x768.png`, `adboard_wide_1024x512.png` | The same frame in the other ratios |
| `adboard_vendor_1024.png`, `adboard_vendor_512.png` | The same frame with bigger type, for in-world vendor displays |

The free Take 12 Scenery has its own listing and boards in `scenery/marketing/`. Regenerate all of them with
`python3 tools/art/make_adboard.py`. They use drawn pixel-art views, so add real snapshots as extra listing images (see
the end of `marketplace_listing.md`).
