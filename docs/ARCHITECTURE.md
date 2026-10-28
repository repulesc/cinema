# Take 12: Architecture (8.0)

- What the product is and why: `docs/PRODUCT.md` (and the decision log of the 8.0 master revision, summarised there).
- Connect's protocol: `docs/CONNECT.md`.
- Older versions: 7.2.0 is the last release before this rebuild (git tag / history); `legacy/` keeps v1–v3.

This document is the coding spec: names, numbers and formats here are what the scripts use.

## 1. The HUD object
One linked object worn as a HUD (made by `hud/build/builder.lsl`, section 8). **All scripts sit in the root.**
Every part is found by its name (any link order):

| Part (link name) | What it shows |
|---|---|
| `Take 12` (root) | the [12]: a dark disc (`take12_marks`), always visible |
| `t12 ring` | over the disc: the thin ring while filming, the hold fill (8 steps), amber for a problem |
| `t12 dot` | on the disc's rim: white while connected; a soft white glow while someone watches your film |
| `t12 band` | the strip's band: solid black, from the screen edge across the strip (8.0.4) |
| `t12 s0` … `t12 s3` | the shot words TRACKING · PORTRAIT · FIXED · SCENIC |
| `t12 box` | the lit shot's underline (8.0.4; before, a white box with ink letters, unreadable in-world) |
| `t12 halo` | an outline: the Fixed hint (with a glow) or an accent word (KEEP NEW, UNDO) |
| `t12 o0` … `t12 o5` | the running shot's option words |
| `t12 sep` | the thin divider between two option groups |
| `t12 u0` … `t12 u2` | underlines under lit options (and under THEIR FILM); `u2` is also the eye line. Every line is a blank face cut to ~2 px with `PRIM_SLICE` (a 0.01 m part is the smallest Second Life allows) |
| `t12 shape` | `▭ 2.39` / `▭ 4:5` / `▭ FULL` / a dim ▭ (the frame key) |
| `t12 link` | the linked rings and one word: the count, SHARING, THEIR FILM (the Connect key) |
| `t12 note` | carries the 3 s notes (llSetText), just under the strip (above it at the bottom) |
| `t12 bar0` … `t12 bar3` | the letterbox (or pillarbox) bars |
| `t12 shut` | the shutter, at the right end (8.1.0): ready, or lit while the moment is held |
| `t12 auto` | Auto's Orbit, at the left end (8.3.0): lit while Auto directs, quiet in manual; an older HUD without it works, Auto then shows the shots as usual |

Textures (made by `tools/art/make_strip.py`, uploaded once, dropped into the HUD; `screen` adopts them, keeping each UUID
in Linkset Data (`cin.take12_words`, `cin.take12_marks`, which only the scripts change) with a copy in the root's
description `take12_words <uuid>;take12_marks <uuid>` for a new owner, and taking the texture out of the contents.
`screen` writes both again after Linkset Data is emptied (Reset › Everything, a new owner) and mends the description
on every load (8.4.2: the viewer's Edit window could put the old description back, and the old marks lost the Orbit):
- `take12_words` (1024²): every word in small caps, white on transparent, one cell 512 × 48 each (2 columns × 21 rows).
  The script tints a word per state. The cell tables (column, row, width in px) are generated into `strip.lsl` (WORDS, the strip's marks) and `screen.lsl` (the [12]'s marks).
- `take12_marks` (1024²): the [12] disc, the ring frames, the dot, the halo, and the shape and link cells (256 × 48; the photo frames' cells after the links, 8.0.9).
  The box, underline and band-fade cells are still on the sheet but drawn by nothing since 8.0.4 (no new upload).

## 2. Screen geometry (`screen.lsl`: the [12]; `strip.lsl`: the strip)
- **HUD space:** 1.0 tall (the window's height) and `llGetCameraAspect()` wide; +Y to the left, +Z up, +X into the
  screen. The root is placed from the attach point (crop.lsl's `centre()` table, kept in `bars`/`screen`); wear it on
  **HUD Top Center** (any point works).
- **Size:** Look › Size S · M · L = 0.8 · 1.0 · 1.25. At M: the strip is 48 px of a 1080 px window (0.0444), words 0.0222
  tall (11.5 px), the [12] 0.0407.
- **Places** (`cin.place`): `top` (flush with the top of the world view, which starts under the viewer's own bars),
  `topl` (52 px lower), `bot` (above a 46 px toolbar), `both` (higher, 96 px). The strip's centre line is at `±(0.5 − margin − H/2)`.
- **Width:** the words stay inside a centred 16:9 area (`W = min(aspect, 1.778)`); the band runs the full width.
  Shots start `inset` from the left of that area, options end `inset` from its right; `inset` = 180 px (0.1667),
  shrunk when the window is too narrow so nothing overlaps (never below 0.02).
- **Middle:** the [12] at x = 0; the shape cell ends 40 px left of it, the link cell starts 40 px right of it.
- **Depth:** dot and ring in front of the disc (−X), words and lines at +0.001, halo at +0.002, band at +0.004, bars at
  +0.006 (crop's DEPTH rule: behind the button so it stays clickable).
- **Lit:** a lit word is full white with a line under it (shots and options alike); the rest are quieter (55 % or
  75 %, Look › Keys). No glow on the strip: it blurs small text.
- **Closed:** every strip part is shrunk to 0.01, alpha 0, parked behind the root (`ui` counts a tap on any of them,
  or on the ring or dot, as a tap on the [12]: 8.0.3). Opening
  fades in over 0.2 s (alpha in 3 steps).
- **Touch:** `strip` reads touches on the parts (`llDetectedLinkNumber` → name): a shot word → CMD `shot|<name>`, an
  option word → OPT `<shot>|<word>`, the shape → CMD `frames` (bars' frame dialog), the shutter → CMD `shutter` (core: the "photo" state), the link → CMD `connect`, the Orbit → CMD `auto|<0/1>` (in Auto a shot word → CMD `auto|0`). `ui` reads the root (gestures).

## 3. Scripts
All in the root; each compiles in `tools/lslcheck.sh` with **≥ 15 KB free** (the check fails below).

| Script | Job |
|---|---|
| `core` | Owns the camera (CONTROL_CAMERA, TRACK_CAMERA, TAKE_CONTROLS; one `llTakeControls`). States: `wait` (your own camera), `film`, `held` (you took the camera: Alt-click), `letgo` (flying, mouselook, a marked vehicle), `off` (hold), `watch` (you watch someone's film). Routes shots (START / STOP / NEXT / PAUSE / RESUME), applies SHOT / GLIDE / FOLLOW, the jump-cut rule, sit / stand, teleport, idle start, hold off / on, CAMSET for Connect |
| `ui` | The [12]'s gestures (tap 0.35 s → dialog, double-tap → the strip, hold 0.8 s → everything off / back), every dialog (main, Connect lists, Settings and its pages, Help, Reset), the first run, `/12` commands, defaults, the 7.x settings migration, owner change |
| `text` | Every word the user reads, by id (dialog bodies and labels, notes, tips); the notes on `t12 note` (3 s; important ones also in owner chat); the first-three-uses tip counters |
| `screen` | The [12] (section 2): the root's place, its ring and dot, the notes' part, the eye line, texture adoption |
| `strip` | The strip (section 2): the band, the words and their states, the 16:9 cap, the fade, touches (8.0.2: split from `screen`, which was too big for 64 KB) |
| `bars` | The letterbox per shot (`cin.shape.<shot>`), Black or Dimmed, on / off; a watched film's shape; tells the shots the picture (CROP) and the strip the readout (SHAPE) |
| `tracking` | Shoulder · Film · Classic, L · R: the viewer's own follow camera (FOLLOW), walls, small rooms, running. And Auto's director (8.3.0, core has no room): walking, still, sitting → CMD `shot|<shot>|auto` |
| `portrait` | Me · Us, Close · Medium · Wide: composed shots of you standing (SHOT / GLIDE) |
| `fixed` | Your own framing: View A / B per place, seat memory per object and spot, Keep new, Forget / Undo, Let go / Take back |
| `scenic` | Drift · Near · Room · Far: views of the place; the idle camera |
| `sync` | Connect: the nearby list, invites, two equal cameras, watching, sharing (`docs/CONNECT.md`) |
| `carry` | Between two copies worn by the same owner: carry-over of the settings, two worn (the older steps aside); Feedback: the text box and the email to the maker (8.0.10); Connect's dialogs and Settings › Friends (8.4.3, for sync's memory); the watchdog: every 5 s a stopped script (a run-time error) is reset and started again, and `/12 status` names it (8.4.3) |

The free **Take 12 Scenery** is generated (`tools/build_scenery.py`): core, ui, text, screen, strip, bars, scenic, sync, carry with
`LITE = 1` (Tracking / Portrait / Fixed dim; it can watch a friend's film, never film for others).

## 4. Link messages

| num | from → to | string |
|---|---|---|
| 7301 START | core → shots | `<shot>\|<why: start / resume / tp / idle / stand>` (only that shot's script takes it) |
| 7302 STOP | core → shots | why |
| 7303 NEXT | core → the running shot | `tap` (the lit shot tapped: its one job, section 5) |
| 7304 PAUSE / 7305 RESUME | core → the running shot | `held` / `sit` / `stand` / `watch` / `fly` / `ml` / `tp` / `off` |
| 7306 MOVING | core → shots | `<movement keys held>` (0: let go) |
| 7310 SHOT | shot → core | `<pos>\|<focus>\|<kind>`: `cut` (always a cut), `auto` (the jump-cut rule), `keep` (the same view again) |
| 7311 NO_SHOT | shot → core | `free` (Fixed: no view kept, your own camera to frame it) or a reason (core's basic shot) |
| 7312 GLIDE | shot → core | `<pos>\|<focus>\|<lag>` |
| 7313 ACK | shot → core | `<shot>` |
| 7314 FOLLOW | tracking → core | `<distance>\|<pitch°>\|<focus offset>\|<behindness lag>\|<position lag>\|<focus lag>`, or `lock\|<pos>` (the camera stays at a corner, the focus follows you) |
| 7318 FOVMSG | core → shots | your lens, radians |
| 7320 UI_STATE | core → all | `<state>\|<shot>\|<hint>\|<why>`: hint = a shot to glow once (`fixed`, `portrait`) |
| 7325 CAMSET | core → sync | `<pos>\|<focus>\|<lag>\|<fov>` while filming; `-` when it stops (nothing is shared then) |
| 7330 CFG_CHANGED | any → all | the `cin.` key changed (`all` after a reset) |
| 7340 OPTS | shot → strip | `<shot>\|<words, comma>\|<states, comma>`; a word `/` is the divider; states `` · `lit` · `accent` · `dim` |
| 7341 OPT | strip → shots | `<shot>\|<word>` |
| 7342 LINKST | sync → screen, strip, ui | `<alone / on / shared / theirs / dim>\|<count>\|<name>` |
| 7343 STRIP | ui → screen, strip | `toggle` · `open` · `close` · `hide` (off) · `show` (back) · `hold\|<0–8>` · `eye\|<z>` · `problem\|<0/1>` · `layout` |
| 7344 NOTE | any → text | `<id>\|<arg>` (text shows it 3 s on `t12 note`; important ids also go to owner chat) |
| 7345 TIP | strip, ui → text | `<word>` (a key's first three uses) |
| 7346 TXT / 7347 TXT_ANS | ui ↔ text | `<id>\|<args>` → `<id>\|<text>` |
| 7348 SHAPE | bars → strip | `<label>\|<on / off / dim>` |
| 7349 CONN | sync ↔ carry | sync: `<page>\|<args>`, id `label\nkey\n…` (a dialog of Connect); carry: `ans\|<page>\|<button>`, id the button's key (no button: the ask closed unanswered) |
| 7360 MSG_VER | all | `?` or a version (ui warns on a mismatch) |
| 7370 STATUS | ui → all | `?`: each script says one line |
| 7371 CMD | any → any | below |
| 7390 CROP | bars → shots | `<ratio>\|<window aspect>` (0: no bars): the picture to compose in |

CMD strings: `shot|<name>` (a shot word: start it, or its lit-tap job), `off` / `on` (hold), `bars`, `connect`,
`watch|<key>` / `unwatch` (sync → core), `letgo|veh` / `takeback` (fixed → core), `hint|<shot>`, `debug|<0/1>`,
`blend|<0/1>`, `standby` (carry: an older copy steps aside), `status`. Auto (8.3.0): `shot|<name>|auto` (Auto's pick,
tracking → core: a tap it makes), `auto|<0/1>` (Auto on or off, to everyone: core, strip, the shots), `auto` (`/12 auto`
and the setup's end → tracking turns it on). A `shot|<name>` of your own for another shot ends Auto.

## 5. Behaviour (summary; the details are in each script's header)
- **The lit tap** (`shot|<lit shot>` → NEXT `tap`): Portrait Me the other 3/4 side; the two-shot swaps sides (inside the
  180° line, a real crossing on a second tap); Tracking back into its look; Fixed back to the kept view; Scenic the next
  view now.
- **Jump cuts:** an `auto` SHOT less than 30° and one size step from the shot on screen glides (1 s) instead of cutting.
- **Held:** while filming, the camera leaving the scripted spot (Alt-click) is `held`: the lit shot dims, nothing is
  shared, the shot pauses; a movement key or the lit tap gives it back. In Fixed it is how you frame (Keep new).
- **Sitting:** every shot holds its last frame and Fixed glows once (hint); standing up resumes it. Seated in Fixed,
  standing up goes back to the shot you had before sitting.
- **Let go:** flying, mouselook and a marked vehicle release the camera; it comes back as it was.
- **Teleport / region crossing:** the same shot, a fresh frame after ~2 s.
- **Idle start** (`cin.idle`: off · away · 5): Scenic starts by itself; a key or typing brings back the shot you had.
- **Auto** (8.3.0, the guide 8.4.0, `tracking.lsl`): on wear (set up) after 3 s, or at the setup's end. Every 0.5 s
  it reads core's state (UI_STATE): in `wait`, `film`, or `held` (only to walk off), not flying or in mouselook, not
  during the eye line. Moving = over 0.5 m/s, or the movement keys (core's MOVING), or AGENT_WALKING: 1 s of it →
  Tracking at once. Still: with 1-3 agents within 3 m (its own `llSensorRepeat`, 1 s) for 4 s → Portrait; 300 s or
  AGENT_AWAY → Scenic `wide`; 10 s → Scenic `drift`; seated, Fixed if `cin.seat.<root>` holds a view (2 s), else
  Drift. A shot stays 8 s except Tracking on moving; nothing running: at once. Scenic's band goes as CMD
  `aband|drift` or `aband|wide` (Room indoors, Far outdoors), never into `cin.scn`; the other shots take Auto's
  options without keeping them (Portrait Medium · Us); Tracking films in your own look and side (8.4.4). Core, in Auto: no idle start; held, the camera
  back on its spot (Esc) for 1.5 s resumes the shot. `/12 debug on`: each pick and why in chat.
- **Off** (hold): camera, bars, strip all off; hold again restores exactly.
- **Portrait's solver** (from 7.x `frame.lsl`): two heights on you must land on two picture heights (Medium: the eyes
  on the upper third, y = +0.333, and the belt line, 52 % of your height, at the bottom, y = −1). With the camera at
  your eye height and a tilt φ, a height z shows at y = tan(atan((z − zc) / D) + φ) / t (t: the picture's half-height
  as a tangent, the bars' shape included). The angle between the two shrinks as D grows, so D is found by bisection
  and the tilt follows. Lead room turns the view by θ = atan(x · t · aspect), x = ⅓ (Wide ¼), and the camera stands
  back to D / cos θ, so your depth along the picture's axis is still D. A wall moves the camera in; the eyes stay on
  the third (the size word stays). Every height comes from your size and your eye line (`cin.eye`).

## 6. Linkset Data (`cin.*`, protected, PASS)
| Key | Value |
|---|---|
| `owner`, `ver` | whose settings these are (an owner change wipes them), the version that wrote them |
| `firstrun` | `done` after the first run |
| `lens`, `eye` | 35 / 38 / 40; your eye line as a fraction of your height |
| `place`, `size`, `keys`, `flip` | the strip: top / topl / bot / both; s / m / l; soft / clear; a mirrored HUD axis |
| `aspect` | your window, last measured (bars) |
| `trk`, `por`, `scn` | `<look 0–2>\|<side 0 L / 1 R>`; `<size 0–2>\|<who 0 Me / 1 Us>`; `<band 0 drift … 3 far>` |
| `shape.<shot>`, `bars`, `bstyle` | each shot's frame (1.66 … 2.39, 3:2 · 4:3 · 1:1 · 4:5, full); 1 / 0; black / dim |
| `idle`, `blend` | off / away / 5; 1: every cut a 1.5 s glide (`/12 blend on`) |
| `view.<region>.<parcel>` | Fixed: `<A>~<B>~<ground spots…>`, each `<cam>\|<focus>\|<where you were>\|<facing°>\|<lens>` |
| `places` | those places, least used first (20 kept) |
| `seat.<object key>`, `seats` | a piece of furniture's spots (up to 4, in its own frame); the furniture, least used first (48 kept) |
| `veh` | marked vehicles, `name\|creator;…`, newest first |
| `tips` | `WORD:uses;…` (three each, the snapshot tip once) |
| `friends`, `chime`, `peers`, `newer` | Connect: `key,name;…`; 0 = off; who you were with and when (rejoin); the newer version already told |

Carry-over copies every key but `owner`, `ver`, `cfgv` and `peers`.

## 7. Checks
`tools/lslcheck.sh` (compiles everything, fails under 15 KB free), `tools/build_scenery.py --check`, and the emulator
runs on the real scripts in `tools/sim/*_emu.py` (CI runs them all; see `.github/workflows/lsl-check.yml`).
**Memory at runtime (8.0.1):** a list and its copy while it grows are what runs a script out of memory (8.0.0's screen
died in-world building one list for the whole strip). Never build a list of everything at once: send prim parameters
in batches (`strip`'s `put` / `go`), page Linkset Data keys (`ui`'s `wipe`), keep indexes as strings (`fixed`'s `lru`),
and use a sensor (16 nearest) rather than the region's avatar list. `tools/sim/memory_emu.py` measures every script's
biggest runtime list against `tools/lslmem.py`'s model and fails under 3 KB to spare.

## 8. Building the HUD
`hud/build/builder.lsl` (not shipped): rez a box, put the builder and one blank box named `t12 part` in it, touch it.
It rezzes the parts, links them, names them, then deletes itself. Add the scripts of `hud/src/` and drop the two
textures in; take it and wear it on HUD Top Center. Details: `hud/build/README.md`.
