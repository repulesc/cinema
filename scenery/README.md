# Take 12 Scenery (free)

The Scenic camera of Take 12, on its own, for L$0: a free way in to the full Take 12.

- **What it has:** the same strip and [12] as Take 12, with Scenic (Drift · Near · Room · Far), idle start, the bars
  and their shapes, the setup (lens, size), Connect to **watch** a friend's Take 12 film, and carry-over to a full Take 12.
- **What it leaves to the full Take 12:** Tracking, Portrait and Fixed. They are on the strip, dim; a tap says "In the
  full Take 12." and nothing else ever asks you to buy. It never films for others.
- **Two worn:** with a full Take 12 worn too, the free one steps aside and the full one carries your setup over.

## The scripts are generated
`scenery/src/` is generated from `hud/src/` by `tools/build_scenery.py`: core, ui, text, screen, bars, scenic, sync
and carry, with `integer LITE   = 1;` where a script has the switch. Never edit `scenery/src` by hand. After
changing `hud/src`:
```
python3 tools/build_scenery.py
```
CI runs `python3 tools/build_scenery.py --check` (fails if `scenery/src` is out of date) and `tools/sim/free_test.py`
(the free scripts are the full ones with only the switch changed).

## Make it
1. **The object:** build it with the same builder as Take 12 (`hud/build/README.md`), and name the root
   **Take 12 Scenery**.
2. **The textures:** the same two as Take 12 (`hud/art/take12_words_1024.png`, `hud/art/take12_marks_1024.png`).
3. **The scripts:** the eight from `scenery/src/`. `/12 status` lists them.
4. **The notecard:** `Take 12 Scenery - Read Me` with the text of `scenery/notecard/read_me.txt`.
5. **Before giving it away:** the scripts no-modify (`PASS` comes from `hud/src`). Next owner: copy and transfer.
6. **Box and folder:** `Take 12 Scenery`.

## Listing and ads
The Marketplace text is in [`marketing/marketplace_listing_scenery.md`](marketing/marketplace_listing_scenery.md)
(price L$0); the boards are `marketing/*_scenery.png`, made with the full Take 12's by `python3 tools/art/make_adboard.py`.
