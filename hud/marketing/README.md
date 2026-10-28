# Marketing material for Take 12

| File | What |
|---|---|
| `marketplace_listing.md` | Copy-paste text for the Marketplace listing (8.0): name, description, features, tags, promo lines, the "what is new" message, image list |
| `legacy/` | The earlier listings and intros (4.4, 4.8) |
| `adboard_square_1024.png` | The Marketplace main image, cinema black: the mark, TAKE (12) (the word and the HUD's own [12] as its 12, so the name is said once), and "Your Second Life, filmed." |
| `adboard_portrait_3x4_768x1024.png`, `adboard_landscape_4x3_1024x768.png`, `adboard_wide_1024x512.png` | The same in the other ratios |
| `adboard_vendor_1024.png`, `adboard_vendor_512.png` | The same, bigger, for in-world vendor displays |

The free Take 12 Scenery has its own listing and boards in `scenery/marketing/`. Regenerate all of them with
`python3 tools/art/make_adboard.py`. They are typographic on purpose (Inter, white on black, no scenes); real snapshots
can come later as extra listing images (see the end of `marketplace_listing.md`).
