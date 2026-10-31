# Take 12

A cinematic camera HUD for Second Life. The brand is **12**, the product is **Take 12**, and the Marketplace title is
**Take 12 - Cinematic Camera HUD**.

8.0 is a rebuild (`docs/PRODUCT.md`). It looks like a cinema camera's on-screen display: one thin strip of words at
the top of the screen and the [12].
- **Four shots:**
  - **Tracking:** a cinematic follow camera.
  - **Portrait:** you standing, composed; Me or Us.
  - **Fixed:** your own framing, kept for every place and every seat.
  - **Scenic:** views of the place, and the idle camera.
- **Auto (8.3.0):** the camera directs itself, from what a script truly sees (walking, standing still, sitting, idle);
  the Orbit at the strip's left end, one tap to direct yourself.
- **Frames and the shutter:** one cinema frame for the whole film (2.39, 1.85 …), picked with the ▭; the shutter holds the moment for a photo in your photo frame (3:2, 4:3, 1:1, 4:5), with the snapshot size.
- **Connect:** two equal cameras; one tap to see your friend's film.
- **The [12]:** tap for the setup dialog, double-tap for the strip, hold for everything off (hold again: back).
- **Take 12 Scenery (free):** Scenic on its own, generated from the same scripts (`scenery/`).

> **Status:** **v8.6.0** (in `hud/`), emulator-tested; its in-world test is under way (`docs/ROADMAP.md` has the tester
> checklist). The free Take 12 Scenery is in `scenery/`. The frozen v3.0.0 is in [`legacy/v3/`](legacy/v3/).

**Naming for the box and folder:** both are called **`Take 12 - Cinematic Camera HUD`**. The HUD itself is `Take 12`,
and the notecard is `Take 12 - Read Me`.

## About
Take 12 is made by 12: the maker's name in Second Life, and the name of this camera. A name ties a thing to one
person; a number is broader and quieter, and it points outward: there is something out there. In a virtual world what
we make can outlast us, and a number keeps without the person behind it. Two digits, because one stands still and two
make movement. Twelve, because it is how we keep time. A take is a moment in time; Take 12 keeps them.

The box (`hud/box/`) is worn, the classic way: Add it and it shows on the screen, hands over one folder (the HUD, the
Read Me and a Take 12 Scenery to give a friend) and takes itself off. Rezzed, it is a black box for a store display.

## Repository layout
| Path | Contents |
|---|---|
| `hud/src/` | The twelve HUD scripts (core, ui, text, screen, strip, bars, tracking, portrait, fixed, scenic, sync, carry) |
| `hud/build/` | The builder script that makes the HUD object, and how to use it |
| `hud/art/` | The two textures: `take12_words_1024.png` (the strip's words) and `take12_marks_1024.png` (the [12], rings, band, readouts) |
| `hud/notecard/` | The in-world Read Me (the user guide) |
| `hud/marketing/` | Marketplace listing text and the ad boards |
| `scenery/` | **Take 12 Scenery** (free): `scenery/src` is generated from `hud/src` (`tools/build_scenery.py`); its notecard, listing and boards |
| `tools/lslcheck.sh` | Compile check (LSL-PyOptimizer) and a memory estimate; fails under 15 KB free |
| `tools/emu/` | An LSL emulator that runs the real scripts: a region, avatars, worn HUDs, furniture, builds and rays, chat, the camera |
| `tools/sim/` | The tests on the real scripts (`*_emu.py`), the text, listing and free-build checks |
| `tools/art/` | `make_strip.py` (the two textures, and the cell tables in `strip.lsl` and `screen.lsl`), `make_adboard.py` (the boards) |
| `legacy/` | v3.0.0 (frozen, working) and the old v1/v2 |
| `lab/` | Experiments, not part of the product |

## Documents
| Document | Contents |
|---|---|
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | What 8.0 is: the look, the gestures, the shots, Connect (source of truth) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The coding spec: parts, geometry, scripts, link messages, settings |
| [`docs/CONNECT.md`](docs/CONNECT.md) | Connect's behaviour and protocol |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Status, building in-world, the tester checklist, numbers to tune |
| [`hud/notecard/read_me.txt`](hud/notecard/read_me.txt) | The in-world Read Me (plain text, end-user language) |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes |

## Building the HUD in-world
1. Build the object with the builder: [`hud/build/README.md`](hud/build/README.md) (rez a box, add `builder.lsl` and a
   blank box named `t12 part`, touch it: 26 parts are made, linked and named).
2. Add the twelve scripts of `hud/src/`, each with the file's name.
3. Upload the two textures of `hud/art/` once (named `take12_words` and `take12_marks`) and drop them in: the HUD keeps
   their UUIDs and takes them out of its contents, so it can be given away.
4. Add a notecard named `Take 12 - Read Me` with the text of `hud/notecard/read_me.txt`; optionally a sound for the
   Connect chime.
5. Before giving or selling it: change `PASS` (the same string at the top of every script) and set the scripts to
   no-modify; everything left in the contents must be Transfer for the next owner.
6. Wear it on **HUD Top Center**. A note says "Tap the [12] to set up." `/12 status` prints one line per script.

## Checks (CI runs them on every push)
- `bash tools/lslcheck.sh`: compiles every script; fails if one has less than 15 KB free (the model is in `tools/lslmem.py`).
- `python3 tools/build_scenery.py --check`: the free build is up to date.
- `python3 tools/art/make_strip.py --check`: the textures' cell tables in `strip.lsl` and `screen.lsl` match the art.
- The emulator tests:
  - `tools/sim/layout_emu.py`: every window from 5:4 to 32:9 × 4 places × 3 sizes;
  - `gestures_emu.py`, `shots_emu.py`;
  - `portrait_emu.py`, `tracking_emu.py`, `fixed_emu.py`, `scenic_emu.py`, `auto_emu.py` (a day in Auto);
  - `connect_emu.py [runs] [seed]`: scenarios and a fuzzer, with invariants;
  - `carry_emu.py`, `builder_emu.py`;
  - `memory_emu.py`: every script's heaviest moments (the strip at every size, a crowd of 90, full seat memory, carry-over, a 7.x migration) must leave 3 KB of its 64 KB, measured on the lists it builds while running.
- `tools/sim/text_check.py` (every word, note and button), `free_test.py`, `listing_check.py`.
