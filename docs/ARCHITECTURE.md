# Cinema HUD: Architecture (v3)

What the product is: `docs/PRODUCT.md`. The order of work: `docs/ROADMAP.md`. The old v1–v2 design is in `docs/archive/`.

## Scripts (all four in the ROOT prim of the HUD)
| Script | Job |
|---|---|
| `cinema_core.lsl` | Owns the camera. Permissions, controls, AFK timer, touch (tap / long-press), modes, exits, hold timer, Alt-cam peek, pauses, **watchdog**, a **basic fallback shot** for every mode, reach verification, `grab` test |
| `cinema_scenery.lsl` | **Default mode.** Finds drone and wide views: region-bounded, above the top surface, unobstructed, varied. Learns the viewer's reach |
| `cinema_people.lsl` | Optional **Personal** (follow-me portraits) and **Social** (over-the-shoulder pairs, group tableaux) modes |
| `cinema_ui.lsl` | Long-press menu, `/77` chat commands, settings in protected Linkset Data, button colour, first run |

Each script is compile-checked with LSL-PyOptimizer (`tools/lslcheck.sh`) and must estimate ≥ 15 KB free memory.

## Link messages
| num | from → to | string |
|---|---|---|
| 7301 START | core → all | `"<mode>|<fov>"`, mode = `scenery` / `personal` / `social`; only the matching script takes it |
| 7302 STOP | core → all | reason |
| 7303 NEXT | core → active | why (`hold`, `retry`) |
| 7304 PAUSE / 7305 RESUME | core → active | `ml` / `tp` / `peek` |
| 7306 MOVING | core → active | owner pressed a movement key (Personal / Social) |
| 7310 SHOT | worker → core | `"<pos>|<focus>|<hold>|<type>"` |
| 7311 NO_SHOT | worker → core | reason (core covers with a basic shot) |
| 7313 ACK | worker → core | mode, sent the moment START is taken |
| 7314 REACH_FAIL | core → scenery | camera distance (m) the viewer did not honour |
| 7320 UI_STATE / 7321 UI_MENU | core → ui | `off` / `armed` / `rolling` / `peek` ; open menu |
| 7330 CFG_CHANGED | ui → all | key |
| 7360 VERSION | all | version, or `?` |
| 7370 STATUS | ui → all | `?` → every script prints one line |
| 7371 CMD | ui → core | `scenery` / `personal` / `social` / `stop` / `grab` |

**Shot types:**
- Scenery: 5 drone, 6 wide.
- People: 0 portrait, 1 pair, 2 group.
- Core: 9 basic fallback.

## Core: modes, exits, watchdog
- **States:** IDLE, WAIT (asked for the first shot), ROLL, PAUSE (mouselook / teleport), PEEK (Alt-cam), TEST.
- **Triggers:**
  - Tap → scenery (or stop, if running).
  - Long-press → menu.
  - AFK → scenery.
  - Menu or commands → any mode.
- **Exits:**
  - Typing → stop, in every mode.
  - Tap → stop, in every mode.
  - Movement key → stop in **scenery**; in personal / social it sends MOVING instead.
  - Sit / stand change → stop in scenery.
- **Watchdog:** START or NEXT sets "asking". If no SHOT arrives within 1.5 s (first) or 2.5 s (next), or the worker sends NO_SHOT, core cuts to a basic shot for that mode:
  - Scenery basic: 15 m behind you and 10 m above the top surface there, looking down over your area.
  - People basic: a level 3 m portrait orbit.
  - Both are wall-checked with one ray.
  - If the worker never ACKed, core says so once and re-sends START at every hold.
- **Reach verification (scenery):** 2.5 s after a cut, core compares `llGetCameraPos()` with the requested spot. If the camera is much closer to you than requested (the viewer clamped it), core sends REACH_FAIL with the requested distance and does **not** treat it as a peek. After that first check, a deviation of more than 1 m means you took the camera, so core goes to PEEK.

## Scenery spot finder
Every cut builds 10 candidates and keeps the best one. The cost is about 2 rays per candidate.

1. **Context, once per session or after you move 10 m:**
   - Up-ray from your eye (40 m): are you under a roof?
   - Down-ray from 80 m above you: the top surface over your position (`topZ`).
   - Water level from `llWater`.
2. **Candidate i:**
   - Azimuth: random start + i × 36°, skipping directions within 40° of the last two shots.
   - Distance: 20 m to `reach`.
   - Kind: 60 % drone, 40 % wide.
   - Camera x and y = you + direction × distance, kept inside [3, 253]. Skip it if the clamp left less than 15 m.
3. **Height, ray A:** a down-ray at the camera x and y, from `max(you, topZ) + 80` down to `your z − 40`, finds the **topmost surface** there (roofs and trees included). It never goes below water.
   - Drone: surface + 10–30 m. Wide: surface + 2.5–4 m.
   - Under a roof: the camera is also at least `topZ + 5` (outside and above).
   - Because the camera starts above the top surface at its own position, it can never be inside a building.
4. **View:**
   - Drone: look at a point on your area (you + up to 15 m random offset, at ground level). The pitch is clamped to 10–40° down.
   - Wide: look back across your area, ±60° random, level (2° down).
5. **Ray B, nothing blocks the view:** cast from the camera along the view for 60 m. The candidate is valid if there is no hit before `min(25 m, 0.8 × distance to the target)`.
6. **Score:**
   - 3 × clear length / 60.
   - 2 × direction novelty (angle from the last shots, capped at 90°).
   - 1 if the height class differs from the last shot.
   - 0.5 if the pitch is ≤ 25° (horizon in frame).
   - Plus 0–0.5 random.
7. If no candidate is valid, the finder relaxes (distance 15 m, clear 12 m) and tries once more. If that fails, it sends NO_SHOT and core covers.
8. **Hold:** the `hold` setting (default 60 s) ±25 %.
9. **REACH_FAIL:** reach = max(20 m, 0.8 × the failed distance), saved in Linkset Data (`cin.reach`), then a new shot at once.

## People modes (`cinema_people.lsl`)
- **Sensing:**
  - Up to 5 other avatars within 8 m (region agent list, nearest first).
  - A 10-ray survey (8 directions, up and down) for floor, roof and openness.
- **Composition:**
  - The camera is level. Its height puts the eye line on the upper third: `cam.z = eye − d·tan(vfov/2)/3`.
  - The rule-of-thirds yaw leaves lead room; group shots are centred.
  - 7 candidate azimuths are tried around the plan, and the best 2 are verified with a reverse ray.
- **Personal:**
  - Portrait angles 45, −45, 135, −135, 180 and 0°, 2.5–3.5 m away.
  - Hold 20 s.
  - When you walk: re-frame when you leave the frame cone or move more than 4 m.
- **Social:**
  - 2 or more others within 8 m: group tableau, square-on to the long axis (the two members farthest apart), on the side you face, 4–12 m away.
  - 1 other within 4.5 m: over-the-shoulder, alternating shot and reverse shot on the same side of the axis.
  - Nobody: a Personal-style portrait plus a one-time note.
  - Re-frames when someone arrives, or when you walk.

## Settings (Linkset Data, `cin.*`, protected)
| Key | Default | Meaning |
|---|---|---|
| `afk_on` | 1 | AFK start |
| `afk_sec` | 90 | seconds, or `away` |
| `hold` | 60 | scenery hold, in seconds |
| `reach` | 100 | furthest scenery camera distance (m); learned |
| `peek` | 1 | watch for Alt-cam |
| `peek_bail` | 0 | Alt-cam ends instead of pausing |
| `phantom` | 0 | rays hit phantom objects |
| `cutmode` | 0 | clear camera first, if cuts glide |
| `trace` | 1 | one chat line per cut |
| `cmd_chan` | 77 | chat command channel |
