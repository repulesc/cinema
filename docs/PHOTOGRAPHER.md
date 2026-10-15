# Photographer mode: spec (design stage, nothing coded yet)

A fifth mode in Take 12 (Full only). It puts the camera where a portrait photographer would, by clear rules, and
**holds** it: it never cuts on a timer and never moves on its own. You cycle through five framings with a
double-tap, fine-tune with the movement keys, and take your snapshot. Mock-ups, computed by the maths below:
`python3 tools/sim/photographer_sim.py --html out.html` (published for review as "Photographer Presets").

## Decisions (quiz, Oct 2026)
| Topic | Decision |
|---|---|
| Lineup | A mode inside Take 12 Full (not a separate product or tier) |
| Subjects | You (default), a person you pick (people within 20 m), the group in front of you, the landscape |
| Looks | Classic, fashion / full length, editorial, close beauty: spread over the five framings |
| Variations | Five, A to E. Double-tap = next. Each is held until you change it |
| Fine-tune | Movement keys nudge the camera; a tap leaves the mode |
| Photo shape | A setting: Wide 16:9, 4:3 (also the Second Life profile picture shape), 3:2 classic. No 1:1 |
| Lens | Each framing names its lens in mm. The HUD reads your viewer's FOV live and shows the match |
| Status | One line of HUD text next to the button (Photographer only): `B · Full length · 50 mm (now 21) Ctrl+0`, `✓` when matched |
| Subject moves | The camera stays put. Double-tap re-places the current framing |
| Menu | A fifth entry on the main menu, "Photographer"; its own pages (subject, shape) live in the photo script |

## What Second Life lets a script do
| | Read | Set | Consequence |
|---|---|---|---|
| FOV (the lens) | `llGetCameraFOV()` | no, viewer only (Ctrl+0 / Ctrl+8 / Ctrl+9, Phototools) | Framing is made by distance. The lens is your choice; the HUD adapts and guides |
| Camera position and aim | – | exact (`llSetCameraParams`, lag 0) | No roll, no depth of field, no exposure: viewer side |
| Avatar height | `llGetAgentSize()` for anyone | – | Body heights are fractions of it (table below, to calibrate) |
| Facing | `OBJECT_ROT` | – | The camera goes round from the nose |
| Sitting | `AGENT_SITTING` | – | v1: C, D and E only, eye from the existing sitting estimate |
| Obstacles | `llCastRay` | – | A blocked spot is tried 15° and 30° to each side, then the status line says why |
| Window shape | no | – | Assumed 16:9; the photo shape is cut from its middle |
| Face or bone positions | no | – | Estimated from the height; the nudges cover the rest |

**FOV and lens.** The lens is the full-frame equivalent of the viewer's vertical FOV: `mm = 12 / tan(FOV / 2)`.
The viewer default (60°) is about 21 mm, much wider than any portrait lens. The HUD never refuses a framing because
of the lens: it computes the distance for the FOV you have. Closer than 1.2 m it does not go (mesh hair clips the
camera and faces distort), so with a lens too wide for a close framing it frames a little looser from 1.2 m,
keeps the eyes on the third, and the status line asks for the preset's lens.

## Body model (fractions of `llGetAgentSize().z`, from the feet) - to calibrate in-world
top 1.00 · eyes 0.935 · chin 0.87 · shoulders 0.82 · chest 0.72 · elbow 0.63 · waist 0.60 · belt 0.56 · hip 0.52 ·
mid-thigh 0.38 · knee 0.285 · feet 0.00. Frames are cut **between** joints (mid-thigh, belt, chest), never at one.
The current HUD puts the eyes at 0.87 (37 % of the height above the centre): that is chin level, and is one of the
things the calibration settles.

## The maths
A framing fixes two body heights to two screen lines (y from −1 at the bottom to +1 at the top of the photo shape),
for example "eyes on the upper third (y = 1/3), frame bottom at mid-thigh (y = −1)", plus the camera height. With
camera height zc, horizontal distance D and tilt φ (down positive), a height z appears at
`y = tan(atan((z − zc) / D) + φ) / tan(FOV / 2)`. The two anchors span a fixed angle, which shrinks monotonically
as D grows, so D is found by bisection (24 steps in LSL) and φ follows. The subject's centre line is then turned to
its x (centre, a third, or the golden line at 0.236 from the centre), on the side that gives lead room.
Mixed-height groups: the tallest head never goes above y = 0.9; if it would, the top anchor takes over.
Side margins come from the 4.4.6 people framing (`needAt`), with the photo shape's width.
Landscape: the horizon is a direction, so its line on screen depends on the tilt alone: `tan φ = y × tan(FOV/2)`.

## Presets
**Portrait (you, or a person you picked)**
| | Name | Look | Lens | Camera height | Round from the nose | Anchors | Across |
|---|---|---|---|---|---|---|---|
| A | Environment | editorial | 35 mm | eye level | 30° | head top y +0.18, feet y −0.72 | golden line |
| B | Full length | fashion | 50 mm | hip (0.50) | 15° | head top y +0.86, feet y −0.88 | centre |
| C | Three-quarter | classic | 50 mm | shoulder (0.80) | 30° | eyes on the upper third, mid-thigh at the bottom | a third |
| D | Half body | classic | 85 mm | eye level | 30° | eyes on the upper third, belt at the bottom | a third |
| E | Head and shoulders | beauty | 85 mm | just above the eyes (0.98) | 25° | eyes on the upper third, chest at the bottom | near a third |

**Group (you and the people around you, mixed heights)**
| | Name | Lens | Notes |
|---|---|---|---|
| A | Group in the place | 35 mm | everyone small in the setting |
| B | Full group | 50 mm | head to toe; the camera at 60 % of the mean height |
| C | Three-quarter group | 50 mm | eyes on the third, mid-thigh of the shortest at the bottom |
| D | Half-body group | 50 mm | eyes on the third, belt of the shortest at the bottom |
| E | From above | 35 mm | 1.6 m above the eyes, looking down so a back row is seen |

**Landscape (from where you stand, looking where you face)**
| | Name | Lens | Horizon |
|---|---|---|---|
| A | Big sky | 24 mm | lower third |
| B | The land | 24 mm | upper third, camera 3 m up |
| C | You in the place | 35 mm | upper third, you small on the lower-left third |
| D | High view | 24 mm | near the top, camera 12 m up |
| E | Far detail | 85 mm | upper third |

## Controls in Photographer
- **Double-tap:** next framing (A → E → A). **Tap:** leave. **Hold:** live menu (subject, photo shape, reset nudges, leave).
- **Movement keys** (your avatar stands still meanwhile): W / S closer / further (the framing's size), A / D round the
  subject by 5°, E / C camera higher / lower with the tilt re-solved so the framing holds (straight-on ↔ slightly
  from above). Nudges are kept until the next framing or a reset.
- Core takes the controls with pass-on off in this mode only (`llTakeControls(..., TRUE, FALSE)`), and back to
  pass-on when it ends; the movement keys keep ending every other mode as today.

## Build outline (after the mock-ups are approved)
- New `cinema_photo.lsl` (worker for START `photo`): presets, solver, placement with obstacle tries, nudges, status
  text (`llSetText` on the button prim, cleared on STOP), its own dialog pages, its own camera-tracking permission
  (granted silently to attachments) for the live FOV.
- Core: mode `photo` (never started by AFK; held shots, `hold = 0`; control events forwarded as NUDGE 7317 instead of
  ending the mode; peek bail off). UI: one main-menu entry and the double-tap route. Every script keeps ≥ 15 KB free.
- `tools/sim/photographer_sim.py` grows into the port of `cinema_photo.lsl` and stays in CI.

## Calibration (needs you in-world, once)
1. `/77 photo calib` frames you side-on, level, at a known distance, with the eyes meant to sit on the upper third.
2. You send two snapshots (a short and a tall shape). From them the body fractions above are corrected.
3. Same for a sitting pose.
