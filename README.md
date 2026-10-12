# Cinema HUD

A one-button Second Life HUD that turns your idle time into cinema.

- **Scenery camera (default):** when you go AFK, or tap the button, the camera leaves your avatar and finds clear, grand vantage points around you. It uses high drone views and wide eye-level views up to about 100 m away, with nothing blocking the view. It holds each still view for about a minute, then cuts. No people needed, and you are tiny in the frame or absent.
- **Personal camera (optional):** composed shots of you that follow you as you walk.
- **Social camera (optional):** over-the-shoulder pairs and group tableaux of you and the people around you.
- A movement key, a tap or typing gives your camera back instantly.

## Documents
| Document | Contents |
|---|---|
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | What the HUD is: modes, controls, vibe, quiz answers (source of truth) |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phases: this delivery, in-world verification, polish |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Scripts, messages, the scenery spot finder, people modes, settings |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Text for the in-world "Cinema HUD - Read Me" notecard |
| [`docs/CALIBRATION.md`](docs/CALIBRATION.md) | In-world results to fill in |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes |
| `docs/archive/`, `archive/` | The old v1–v2 design and code (people-centred; superseded) |

## Scripts (all four go in the same root prim)
```
src/cinema_core.lsl      owns the camera: modes, triggers, exits, watchdog + basic shots
src/cinema_scenery.lsl   default mode: drone / wide spot finder (rays, region-bounded, above roofs)
src/cinema_people.lsl    optional Personal (follow-me) and Social (pairs, groups) modes
src/cinema_ui.lsl        long-press menu, /77 commands, settings
```

## Building the HUD in-world
1. Rez a prim (a small flat box or circle) and name it `Cinema HUD`. This single prim is the button.
2. **Delete every old Cinema script from it first.** Then create four new scripts and paste in the four `src/*.lsl` files. Each prints a `ready` line with its free memory when saved.
3. Select the prim in Build mode and use **Build > Scripts > Set Scripts to Running in Selection** (a script that once failed to compile stays "not running").
4. Create a notecard named exactly `Cinema HUD - Read Me` with the text of `docs/USER_GUIDE.md` and drop it in.
5. Before giving or selling: change `PASS` (same string at the top of every script) and set the scripts to *no modify*.
6. Attach it to a HUD point and tap.

## Checks (run before every paste)
- `tools/lslcheck.sh`: compile-checks `src/*.lsl` with LSL-PyOptimizer (syntax, types, undeclared names, wrong arguments) and estimates free memory per script.
- `tools/sim/scenery_sim.py`: runs the scenery spot finder in test worlds (open field, region edge, inside a house, town, skybox). It checks that the camera stays inside the region, above the top surface, with an unblocked view and the pitch in range.
- `tools/sim/people_geometry.py`: lead room, thirds, over-the-shoulder side, 180-degree rule, group side.

GitHub Actions runs all three on every push.
