# Take 12 Lite

> **PAUSED.** Lite is frozen at 4.4.5 until the full version leaves beta, so no effort goes into two products at once.
> Nothing here is updated meanwhile (scripts, notecard, listing, boards). To resume: run `python3 tools/build_lite.py`,
> bring back the two CI steps (`build_lite.py --check` and `tools/sim/lite_test.py`), add `hud-lite/src/*.lsl` back to
> `tools/lslcheck.sh`, then refresh the notecard and the listing text from the full version.

The Lite product: the scenery camera, AFK start, the tap / double-tap / hold gestures, Pace, Photo hold and the classic clapper. Everything else is in the full Take 12 (locked buttons in the menu open the listing).

The Lite scripts are **generated** from the full ones, so they cannot drift: `python3 tools/build_lite.py` copies `hud/src/cinema_core.lsl`, `cinema_ui.lsl` and `cinema_scenery.lsl` into `hud-lite/src/` with `integer LITE = 1;`. CI fails if the committed files are out of date. **Do not edit `hud-lite/src/` by hand.**

## Build it in-world
1. **Upload the texture** `hud/art/take12_icon_sheet_512x256.png` (the same sheet as the full version; Lite only shows the classic look).
2. **Make the prim** exactly as for the full version (box `<0.01, 0.04, 0.04>`, picture on the front face, transparent texture on the others) and name it `Take 12 Lite`.
3. **Set your listing link:** in `hud/src/cinema_ui.lsl`, change `BUY_URL` to your Take 12 listing, then run `python3 tools/build_lite.py` and use the new `hud-lite/src/cinema_ui.lsl`. (It is the page the locked buttons open.) If you do not have Python at hand, change the `BUY_URL` line directly in the Lite file you paste in.
4. **Add the three scripts** from `hud-lite/src/` (`cinema_core`, `cinema_ui`, `cinema_scenery`) and use **Build > Scripts > Set Scripts to Running in Selection**. Do NOT add `cinema_people`, `cinema_friends` or `cinema_picker`.
5. **Notecard:** paste `hud-lite/notecard/read_me.txt` into a notecard named `Take 12 Lite - Read Me`.
6. **Before selling:** change `PASS` (the same string at the top of every script; **use a different one from the full version**), and set the scripts to no-modify.
7. **Box and folder name:** `Take 12 Lite - Cinematic Camera HUD`.

## Ad boards
`hud-lite/marketing/*_lite.png` (square, 3:4 portrait, 4:3 landscape, wide, vendor), made by `tools/art/make_adboard.py`.

## Listing
`hud-lite/marketing/marketplace_listing_lite.md`. Suggested price: **about L$99**, with the full version at about L$299.

## What Lite does not have
Personal, Social and Friends cameras, chat cuts, skybox room views (it uses outdoor views everywhere), favourite spots, the Look choice (always Classic) and the Indoors setting. Lite does not unlock into the full version; it is a separate product.
