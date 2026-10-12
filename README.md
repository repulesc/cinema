# Cinema HUD

A minimalist Second Life HUD that turns your viewer into an autonomous **static tableau cinema camera**, in the visual grammar of Ozu, Jarmusch and the French New Wave.

- **One button.** Tap to start or stop. Long-press for the menu.
- **AFK cinema.** After 90 s idle (adjustable), it starts by itself, and any movement key brings your camera back instantly.
- **Cuts, never glides.** The camera locks onto composed, level vantage points (rule of thirds by camera height, no keystoning) and cuts between intimate shots, ensemble tableaux, long shots and Ozu-style pillow shots.
- **Aware of its surroundings.** A light raycast pass keeps the camera out of walls, roofs and terrain.

## Status
Version 2.0.0. All scripts pass a real LSL compile check (`tools/lslcheck.sh`, LSL-PyOptimizer). The camera itself is proven in-world (`/77 grab`); v2 makes sure a tap always cuts to a shot, using core's basic shots if the director is not running. In-world confirmation of the smart director is the next step.

| Document | Contents |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full spec: vector math, raycast pipeline, state machine, memory budget, link protocol, function prototypes |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Product decisions from the design quiz |
| [`docs/CALIBRATION.md`](docs/CALIBRATION.md) | In-world probe and calibration log (to fill in) |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Text for the in-world "Cinema HUD - Read Me" notecard |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes |

## Layout
```
src/cinema_core.lsl       permissions, controls, AFK, state machine, camera, basic shots + director watchdog
src/cinema_director.lsl   smart views: people + space sensing, composition, raycast sweep, editing
src/future/               full-featured director, too big for one script (not for pasting)
src/cinema_ui.lsl         menus, Linkset Data settings, first-run, button look
```

## Building the HUD in-world
1. Rez a prim (a flat box or a small circle works well) and name it `Cinema HUD`. This single prim is the button.
2. **Delete any old Cinema scripts from the prim first.** Create three new scripts in it and paste in the contents of the three `src/*.lsl` files. **All three go in the same (root) prim**, so they keep running in no-script parcels. Each prints a "ready" line with its free memory when saved.
3. With the prim selected in Build mode, use **Build > Scripts > Set Scripts to Running in Selection** (scripts that once failed to compile stay "not running").
4. Create a notecard named exactly `Cinema HUD - Read Me`, paste in `docs/USER_GUIDE.md`, and drop it into the prim.
5. Set the scripts to *no modify* before giving or selling the HUD. Change `PASS` (the same string at the top of each script) to your own build secret first.
6. Attach it to a HUD point (e.g. *HUD Bottom Right*), accept the permissions, tap to test.

## Checking scripts before pasting
`tools/lslcheck.sh` fetches LSL-PyOptimizer, compile-checks `src/*.lsl` (syntax, types, undeclared names, wrong function arguments) and prints an estimated free memory per script. GitHub Actions runs the same check on every push.
