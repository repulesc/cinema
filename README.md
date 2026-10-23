# Take 12

A one-button Second Life camera HUD that takes your view off your avatar's back and places it, by itself, where a camera operator would. The brand is **12**, the product is **Take 12**, and the Marketplace title is **Take 12 - Cinematic Camera HUD**.

7.0 is one product with six doors on its menu (7.1: Adjust, Framing in one tap, Connect shares the Format):
- **Framing:** Me · Us · Friends, one rule: it follows you as you walk and holds a composed (golden-line) picture when you stand. Me is Still's composer with walking (`docs/FRAME.md`); Us and Friends hold each group shot and change with the Pace. One tap starts the last one used. **Adjust** (7.1): the keys trim the shot (W/S tilt, A/D around, Shift+A/D side, Page Up/Down height): seated always, standing after ADJUST. Your lens everywhere.
- **Freehand:** you frame the shot with Second Life's own camera; held still for a second, Take 12 holds it like a tripod.
- **Connect:** connect with the people near you (Take 12 or the free Take 12 Watch); whoever films leads (`docs/CONNECT.md`).
- **Scenery:** the standby camera: when you go idle (or Scenery › Start) it finds drone views, horizons and skybox rooms. Its settings live under it.
- **Format:** the picture's shape (3:2, 4:5, 2.39:1 …), the rest of the screen dimmed; Framing composes inside it.
- **Settings:** Pace, Look (button, status line, Size, chat text), Camera.
- Tap = a menu (always), double-tap = go / next, hold = Connect. A movement key gives your camera back instantly.
- **Take 12 Scenery (free):** the scenery camera on its own, for L$0, generated from the same scripts (`scenery/`).

> **Status:** **v7.0.2** (in `hud/`), with the free Take 12 Scenery in `scenery/` and the free Take 12 Watch in `watch/`. The frozen, working v3.0.0 is in [`legacy/v3/`](legacy/v3/). The in-world checklist is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

**Naming for the box and folder** (so buyers can find it after unboxing): the box and the folder inside it are both called **`Take 12 - Cinematic Camera HUD`**. The HUD itself is `Take 12`, and the notecard is `Take 12 - Read Me`.

## Repository layout
| Path | Contents |
|---|---|
| `hud/src/` | The fifteen HUD scripts |
| `hud/art/` | The button texture `take12_icon_sheet_512x256.png` (all three looks, switchable in the menu), single-look variants and a preview |
| `scenery/` | **Take 12 Scenery** (free): the scenery camera on its own. `scenery/src` is generated from `hud/src` (`tools/build_scenery.py`); its own notecard, listing text, ad boards and build steps (`scenery/README.md`) |
| `legacy/v3/` | The frozen, working v3.0.0: scripts, docs and build steps |
| `legacy/v1-v2/` | The old people-centred v1/v2 code and design (superseded) |
| `tools/lslcheck.sh` | Compile check (LSL-PyOptimizer) plus a memory estimate for `hud/src`, the Watch, `scenery/src` and `legacy/v3/src` |
| `tools/sim/` | Python ports of the camera maths, run in CI |
| `tools/art/make_icon.py` | Generates the pixel clapper textures (Take 12, the Take 12 Watch icon, and Take 12 Scenery's sun clapper in `scenery/art/`) |
| `watch/` | The free Take 12 Watch HUD: its script, icon and build steps (`watch/README.md`) |
| `tools/art/make_adboard.py` | Generates the Marketplace and vendor ad boards in `hud/marketing/`, `scenery/marketing/` and `watch/marketing/` |

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
2. **Make the prim:** one box, size `<0.01, 0.04, 0.04>`. Name it `Take 12`. (`keys` sets it to Medium, 0.06, the first time; Options › Look › Size changes it.)
   - Put the texture on the face that points at you when it is on a HUD (try the +X face). You do not have to set repeats or offset: the script does it. Put a fully transparent texture on the other faces.
   - If the script moves the picture on the wrong faces too, tell it which face carries the picture with `/77 face <number>` (the face numbers are shown when you select a face in Build mode, starting at 0).
   - Colour white, no glow. The scripts set fullbright.
3. **Delete all old scripts from the prim** (v3 or earlier, and the `cinema_*` ones from before 5.8.1), then add the fifteen from `hud/src/` to the root prim: `core`, `ui`, `scenery`, `people`, `friends`, `picker`, `frame`, `free`, `lens`, `sync`, `connect`, `tips`, `crop`, `keys`, `fit` (6.8: `share` became `connect`; delete `share`). Each prints a `ready` line with its free memory.
   - **For the keys (6.5):** rez one more box (any size), name it exactly `Take 12 keys`, and link it with the others (the button selected last). Upload `hud/art/take12_keys_1024.png` (keep the alpha; 7.1) and drop it into the HUD's contents named `take12_keys`. `keys` sizes, places and textures the strip itself; without it, everything stays in the menus. 7.1.2: wear it once with the texture inside: `keys` saves the texture's UUID in the strip's description (`/77 status` then says `texture saved`), and you can delete `take12_keys` from the contents again, so the HUD never needs it to be transferable.
   - **For Frame (6.2):** rez four small boxes (any size), select them, select the button prim last (so it stays the root), and link them (Ctrl+L). `crop` makes them dark, see-through bars and places them itself; it never touches the button. Without the boxes everything else works, and Frame says what is missing. (Detach the HUD to link, then wear it again.)
4. **Build › Scripts › Set Scripts to Running in Selection** (a script that once failed to compile stays "not running").
5. Create a notecard named `Take 12 - Read Me` with the text of `hud/notecard/read_me.txt` (paste it in as plain text) and drop it in.
6. Before giving or selling it: change `PASS` (the same string at the top of every script) and set the scripts to no-modify. Everything left in the contents must be Transfer for the next owner (the scripts and the Read Me notecard; a no-transfer item makes the whole HUD no-transfer). Textures on faces never need it, and `take12_keys` can leave the contents once `/77 status` says `texture saved`.
7. Attach it to **HUD Top Right**, drag it into place, and accept the permission request.

Want the v3 version instead? See [`legacy/v3/README.md`](legacy/v3/README.md).

## Checks (run before every paste)
- `tools/lslcheck.sh`: compile-checks every script and estimates its free memory (keep `ui` at 13 KB or more, the others at 12.5 KB or more).
- `python3 tools/build_scenery.py --check`: the free Take 12 Scenery is up to date with `hud/src`.
- `tools/sim/*.py`: the camera maths, the menus, the tips, sharing, the listings and the free build (`free_test.py`).

GitHub Actions runs all of them on every push.
