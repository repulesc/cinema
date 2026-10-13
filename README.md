# Cinema HUD

A one-button Second Life HUD that turns your idle time into cinema.

- **Scenery camera (default):** when you go AFK, or tap the button, the camera leaves your avatar and finds clear, grand vantage points around you. It uses high drone views and wide eye-level views up to about 100 m away, with nothing blocking the view. It holds each still view for about a minute, then cuts. No people needed, and you are tiny in the frame or absent.
- **Personal camera (optional):** composed shots of you that follow you as you walk.
- **Social camera (optional):** over-the-shoulder pairs and group tableaux of you and the people around you.
- A movement key, a tap or typing gives your camera back instantly.

> **Status:** v3.0.0 works in-world and is frozen in [`legacy/v3/`](legacy/v3/). **v4.0.0** is coded in `hud/` and compile-checked and simulated, but **not yet tested in-world**. The in-world test list is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

**v4 in one line:** tap opens a tidy emoji menu, double-tap starts the scenery camera, and the colour-changing button becomes a tiny pixel-art clapper that fades out while rolling. New: **Friends** mode, **room-aware Scenery** (skyboxes), **Photo hold**, **Favourite spots** and **chat cuts** in Social.

## Repository layout
| Path | Contents |
|---|---|
| `hud/src/` | The six v4 HUD scripts |
| `hud/art/` | The button texture `cinema_icon_256x128.png` (2 frames), the variants and a preview |
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
1. **Upload the texture** `hud/art/cinema_icon_256x128.png` (keep the alpha; no lossless needed).
2. **Make the prim:** one box, size `<0.01, 0.04, 0.04>` (about 40 px). Name it `Cinema HUD`.
   - Put the texture on the face that points at you when it is on a HUD (try the +X face), repeats **0.5 × 1.0**, offset horizontal **-0.25**. The script sets this up itself on first run.
   - Colour white, no glow. The scripts set fullbright.
3. **Delete any old Cinema scripts**, then add the six from `hud/src/` to the root prim: `cinema_core`, `cinema_ui`, `cinema_scenery`, `cinema_people`, `cinema_friends`, `cinema_picker`. Each prints a `ready` line with its free memory.
4. **Build › Scripts › Set Scripts to Running in Selection** (a script that once failed to compile stays "not running").
5. Create a notecard named `Cinema HUD - Read Me` with the text of `hud/notecard/read_me.txt` (paste it in as plain text) and drop it in.
6. Before giving or selling it: change `PASS` (the same string at the top of every script) and set the scripts to no-modify.
7. Attach it to **HUD Top Right**, drag it into place, and accept the permission request.

Want the v3 version instead? See [`legacy/v3/README.md`](legacy/v3/README.md).

## Checks (run before every paste)
- `tools/lslcheck.sh`: compile-checks every script and estimates its free memory (must be ≥ 15 KB).
- `tools/sim/scenery_sim.py`, `tools/sim/people_geometry.py`, and from v4 `room_sim.py`, `friends_sim.py`, `tap_test.py`.

GitHub Actions runs all of them on every push.
