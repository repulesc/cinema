# Take 12

A one-button Second Life HUD that turns your idle time into cinema. The brand is **12**, the product is **Take 12**, and the Marketplace title is **Take 12 - Cinematic Camera HUD**.

- **Scenery camera (default):** when you go AFK, or double-tap the button, the camera leaves your avatar and finds clear, grand vantage points around you: high drone views and wide eye-level views up to about 150 m away, and rooms of a skybox from the inside. It holds each still view for about a minute, then cuts.
- **Personal, Social and Friends cameras (optional):** shots of you, of you with the people around you, and of you with the friends you picked.
- Tap = menu, double-tap = go, hold = live menu. A movement key gives your camera back instantly.

> **Status:** **v4.3.0** (in `hud/`, and its Lite build in `hud-lite/`) works in-world in the tests so far. The frozen, working v3.0.0 is in [`legacy/v3/`](legacy/v3/). The in-world checklist is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

**Naming for the box and folder** (so buyers can find it after unboxing): the box and the folder inside it are both called **`Take 12 - Cinematic Camera HUD`**. The HUD itself is `Take 12`, and the notecard is `Take 12 - Read Me`.

## Repository layout
| Path | Contents |
|---|---|
| `hud/src/` | The six v4 HUD scripts |
| `hud/art/` | The button texture `take12_icon_sheet_512x256.png` (all three looks, switchable in the menu), single-look variants and a preview |
| `hud-lite/` | **Take 12 Lite**: the scenery camera, Photo hold and the classic look. Generated from `hud/src` (`tools/build_lite.py`), with its own notecard, listing text and ad boards |
| `legacy/v3/` | The frozen, working v3.0.0: scripts, docs and build steps |
| `legacy/v1-v2/` | The old people-centred v1/v2 code and design (superseded) |
| `tools/lslcheck.sh` | Compile check (LSL-PyOptimizer) plus a memory estimate for `hud/src` and `legacy/v3/src` |
| `tools/sim/` | Python ports of the camera maths, run in CI |
| `tools/art/make_icon.py` | Generates the pixel clapper textures |
| `tools/art/make_adboard.py` | Generates the Marketplace and vendor ad boards in `hud/marketing/` |

## Documents
| Document | Contents |
|---|---|
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | What v4 is: gestures, menus, modes, exits, quiz answers (source of truth) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The v4 coding spec: scripts, link protocol, algorithms, settings |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phase B milestones for the build, the in-world test list, critiques, backlog |
| [`hud/notecard/read_me.txt`](hud/notecard/read_me.txt) | The in-world Read Me notecard (plain text, end-user language) |
| [`hud/marketing/`](hud/marketing/) | Marketplace listing text and the ad graphics |
| [`docs/CALIBRATION.md`](docs/CALIBRATION.md) | In-world results to fill in |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes |

## Building the HUD in-world (v4)
1. **Upload the texture** `hud/art/take12_icon_sheet_512x256.png` (keep the alpha; no lossless needed). It holds every look, and the menu (Options > Look) picks one.
2. **Make the prim:** one box, size `<0.01, 0.04, 0.04>` (about 40 px). Name it `Take 12`.
   - Put the texture on the face that points at you when it is on a HUD (try the +X face). You do not have to set repeats or offset: the script does it. Put a fully transparent texture on the other faces.
   - If the script moves the picture on the wrong faces too, tell it which face carries the picture with `/77 face <number>` (the face numbers are shown when you select a face in Build mode, starting at 0).
   - Colour white, no glow. The scripts set fullbright.
3. **Delete any old scripts from the prim (v3 or earlier)**, then add the six from `hud/src/` to the root prim: `cinema_core`, `cinema_ui`, `cinema_scenery`, `cinema_people`, `cinema_friends`, `cinema_picker`. Each prints a `ready` line with its free memory.
4. **Build › Scripts › Set Scripts to Running in Selection** (a script that once failed to compile stays "not running").
5. Create a notecard named `Take 12 - Read Me` with the text of `hud/notecard/read_me.txt` (paste it in as plain text) and drop it in.
6. Before giving or selling it: change `PASS` (the same string at the top of every script) and set the scripts to no-modify.
7. Attach it to **HUD Top Right**, drag it into place, and accept the permission request.

Want the v3 version instead? See [`legacy/v3/README.md`](legacy/v3/README.md).

## Checks (run before every paste)
- `tools/lslcheck.sh`: compile-checks every script and estimates its free memory (must be ≥ 15 KB).
- `tools/sim/scenery_sim.py`, `tools/sim/people_geometry.py`, `indoor_sim.py` (inside views, with Second Life's exact ray-result layout), `friends_sim.py`, `tap_test.py`, `sheet_test.py`, `lite_test.py`.

GitHub Actions runs all of them on every push.
