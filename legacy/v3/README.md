# Cinema HUD v3.0.0 (legacy, frozen)

**Frozen. Tested in-world and working. Ready to hand out.**

This is the last release before the v4 UX revamp. It is kept here unchanged, so it can still be given away or sold as "Cinema HUD Classic". Active work happens in `hud/` (see the root `README.md` and `docs/ROADMAP.md`).

## What it does
- **Scenery (default):** AFK or a tap. Drone views and wide eye-level views up to about 100 m away, unobstructed, held about 60 s, then hard cuts.
- **Personal:** follow-me portraits.
- **Social:** over-the-shoulder pairs and group tableaux.
- **Controls:** tap = Scenery on/off, long press = menu, `/77` chat commands.
- **Status:** the button changes colour (grey off, white armed, red rolling, amber peek).

## Build
1. Rez one prim named `Cinema HUD`. Delete any old Cinema scripts from it.
2. Add the four scripts from `src/` to the root prim: `cinema_core`, `cinema_scenery`, `cinema_people` and `cinema_ui`.
3. **Build > Scripts > Set Scripts to Running in Selection.**
4. Put the text of `docs/USER_GUIDE.md` into a notecard named `Cinema HUD - Read Me`.
5. Before giving or selling it: change `PASS` (the same string at the top of every script) and set the scripts to no-modify.

The v3 docs are in `docs/`. `tools/lslcheck.sh` (repo root) still compile-checks `legacy/v3/src`.
