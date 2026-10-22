# Take 12 Scenery (free)

The scenery camera of Take 12, on its own, for L$0: a free way in to the full Take 12.

- **What it has:** the scenery camera (drone views, wide horizons, skybox rooms from the inside), idle start, tap / double-tap, Photo hold (hold the button while it rolls), Next, Stop, Pace, Indoors, Reach, Alt-cam, the menu styles, the status line with your lens, tips and the little clap.
- **What it leaves to the full Take 12:** Me, Us, Still, sharing, favourite spots, the seated view and the three button looks.
- **Its own button:** the Take 12 clapper (Rec look) with a coral sun setting on a chalk horizon in place of the "12", like the Watch's eye. One design; Options > Look has no Button choice.
- **The one pointer:** a "More cameras" button on the main menu opens the full Take 12's Marketplace listing. Nothing else asks you to buy.
- **Hold:** with no sharing, holding the button opens the menu (the live menu while it rolls: Photo, Next, Stop).

## The scripts are generated
`scenery/src/` is generated from `hud/src/` by `tools/build_scenery.py`: the same `core`, `ui`, `scenery` and `tips`, with `integer LITE = 1;` and a few texts of its own ("Take 12 Scenery", the welcome, the hold help, the notecard name). Never edit `scenery/src` by hand. After changing `hud/src`:
```
python3 tools/build_scenery.py
```
CI runs `python3 tools/build_scenery.py --check` (fails if `scenery/src` is out of date) and `tools/sim/free_test.py` (the free scripts are the full ones with only those lines changed).

## Make it
1. **Set the listing link first.** In `hud/src/ui.lsl`, set `BUY_URL` to the full Take 12's Marketplace page, then run `python3 tools/build_scenery.py`. (The full Take 12 never shows that button.)
2. **The texture:** upload `scenery/art/take12_scenery_icon_sheet_512x256.png` (keep the alpha). It has the Take 12 sheet's layout, with the Scenery clapper (open and clapped) in every look column, so the scripts need nothing else. `scenery/art/take12_scenery_icon_128.png` is the same button on its own, for the Marketplace or a vendor. Both come from `python3 tools/art/make_icon.py`.
3. **The prim:** one box, size `<0.01, 0.04, 0.04>`, named **Take 12 Scenery**, built exactly as Take 12 (see the main `README.md`, step 2).
4. **The scripts:** the four from `scenery/src/`: `core`, `ui`, `scenery`, `tips`. Each prints a `ready` line with its free memory. Then Build › Scripts › Set Scripts to Running in Selection.
5. **The notecard:** a notecard named `Take 12 Scenery - Read Me` with the text of `scenery/notecard/read_me.txt`.
6. **Before giving it away:** set the scripts to no-modify (`PASS` comes from `hud/src`, so change it there, before you build, if you change it at all). Next owner: copy and transfer, no modify.
7. **Box and folder:** `Take 12 Scenery`.

Settings live in protected Linkset Data in the HUD itself, so someone who later buys the full Take 12 starts the full HUD fresh; the two never share a prim.

## Listing and ads
The Marketplace text is in [`marketing/marketplace_listing_scenery.md`](marketing/marketplace_listing_scenery.md) (price L$0), and the boards are `marketing/*_scenery.png`, generated with the full Take 12's by `python3 tools/art/make_adboard.py`.
