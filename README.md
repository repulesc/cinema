# Cinema HUD

A one-button Second Life HUD that turns your idle time into cinema.

- **Scenery camera (default):** when you go AFK, or tap the button, the camera leaves your avatar and finds clear, grand vantage points around you. It uses high drone views and wide eye-level views up to about 100 m away, with nothing blocking the view. It holds each still view for about a minute, then cuts. No people needed, and you are tiny in the frame or absent.
- **Personal camera (optional):** composed shots of you that follow you as you walk.
- **Social camera (optional):** over-the-shoulder pairs and group tableaux of you and the people around you.
- A movement key, a tap or typing gives your camera back instantly.

> **Status:** v3.0.0 works in-world and is frozen in [`legacy/v3/`](legacy/v3/). **v4.0.0** is specified and being built in `hud/`. Until then, `hud/src/` holds an exact copy of v3. The plan is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

**v4 in one line:** tap opens a tidy emoji menu, double-tap starts the scenery camera, and the colour-changing button becomes a tiny pixel-art clapper that fades out while rolling. New: **Friends** mode, **room-aware Scenery** (skyboxes), **Photo hold**, **Favourite spots** and **chat cuts** in Social.

## Repository layout
| Path | Contents |
|---|---|
| `hud/src/` | The v4 HUD scripts (work in progress, see the roadmap) |
| `hud/art/` | The button texture `cinema_icon_256x128.png` (2 frames), the variants and a preview |
| `legacy/v3/` | The frozen, working v3.0.0: scripts, docs and build steps |
| `legacy/v1-v2/` | The old people-centred v1/v2 code and design (superseded) |
| `tools/lslcheck.sh` | Compile check (LSL-PyOptimizer) plus a memory estimate for `hud/src` and `legacy/v3/src` |
| `tools/sim/` | Python ports of the camera maths, run in CI |
| `tools/art/make_icon.py` | Generates the pixel clapper textures |

## Documents
| Document | Contents |
|---|---|
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | What v4 is: gestures, menus, modes, exits, quiz answers (source of truth) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The v4 coding spec: scripts, link protocol, algorithms, settings |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phase B milestones for the build, the in-world test list, critiques, backlog |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Notecard text (v3 until milestone B7) |
| [`docs/CALIBRATION.md`](docs/CALIBRATION.md) | In-world results to fill in |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes |

## Building the HUD in-world
- **Today (v3):** follow [`legacy/v3/README.md`](legacy/v3/README.md).
- **v4:** the steps arrive with milestone B6/B7. In short:
  1. Make one box `<0.01, 0.04, 0.04>` and attach it to HUD Top Right.
  2. Apply `hud/art/cinema_icon_256x128.png` to the front face (repeats 0.5 × 1, offset −0.25).
  3. Add the five scripts from `hud/src/` and use **Set Scripts to Running**.

## Checks (run before every paste)
- `tools/lslcheck.sh`: compile-checks every script and estimates its free memory (must be ≥ 15 KB).
- `tools/sim/scenery_sim.py`, `tools/sim/people_geometry.py`, and from v4 `room_sim.py`, `friends_sim.py`, `tap_test.py`.

GitHub Actions runs all of them on every push.
