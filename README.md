# Cinema HUD

A minimalist Second Life HUD that turns your viewer into an autonomous **static tableau cinema camera**, in the visual grammar of Ozu, Jarmusch and the French New Wave.

- **One button.** Tap to start or stop. Long-press for the menu.
- **AFK cinema.** After 90 s idle (adjustable), it starts by itself, and any movement key brings your camera back instantly.
- **Cuts, never glides.** The camera locks onto composed, level vantage points (rule of thirds by camera height, no keystoning) and cuts between intimate shots, ensemble tableaux, long shots and Ozu-style pillow shots.
- **Aware of its surroundings.** A light raycast pass keeps the camera out of walls, roofs and terrain.

## Status
Design phase complete. Implementation (LSL) is next.

| Document | Contents |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full spec: vector math, raycast pipeline, state machine, memory budget, link protocol, function prototypes |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Product decisions from the design quiz |
| [`docs/CALIBRATION.md`](docs/CALIBRATION.md) | In-world probe and calibration log (to fill in) |

## Planned layout
```
src/cinema_core.lsl       permissions, controls, AFK, state machine, camera apply/clear
src/cinema_director.lsl   scene scan, raycasts, composition, editing grammar
src/cinema_ui.lsl         menus, Linkset Data settings, first-run, probes
```
All three scripts go in a single prim (the HUD button) so they keep running in no-script parcels.
