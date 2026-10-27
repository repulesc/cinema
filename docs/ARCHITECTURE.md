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
| `t12 band` | the strip's dark band, solid at the screen edge and fading inward |
| `t12 s0` … `t12 s3` | the shot words TRACKING · PORTRAIT · FIXED · SCENIC |
| `t12 box` | the white box behind the lit shot (ink letters on it) |
| `t12 halo` | an outline: the Fixed hint (with a glow) or an accent word (KEEP NEW, UNDO) |
| `t12 o0` … `t12 o5` | the running shot's option words |
| `t12 sep` | the thin divider between two option groups |
| `t12 u0` … `t12 u2` | underlines under lit options (and under THEIR FILM) |
| `t12 shape` | `▭ 2.39` / `▭ FULL` / a dim ▭ (the bars key) |
| `t12 link` | the linked rings and one word: the count, SHARING, THEIR FILM (the Connect key) |
| `t12 note` | carries the 3 s notes (llSetText), just under the strip (above it at the bottom) |
| `t12 bar0` … `t12 bar3` | the letterbox (or pillarbox) bars |

Textures (made by `tools/art/make_strip.py`, uploaded once, dropped into the HUD; `screen` adopts them, keeping each UUID
in the root's description `take12_words <uuid>;take12_marks <uuid>` and taking the texture out of the contents):
- `take12_words` (1024²): every word in small caps, white on transparent, one cell 512 × 48 each (2 columns × 21 rows).
  The script tints a word per state. The cell table (column, row, width in px) is generated into `screen.lsl`'s WORDS.
- `take12_marks` (1024²): the [12] disc, the ring frames, the dot, the box, the halo, the band fade, and the shape and
  link cells (256 × 48).

## 2. Screen geometry (`screen.lsl`)
- **HUD space:** 1.0 tall (the window's height) and `llGetCameraAspect()` wide; +Y to the left, +Z up, +X into the
  screen. The root is placed from the attach point (crop.lsl's `centre()` table, kept in `bars`/`screen`); wear it on
  **HUD Top Center** (any point works).
- **Size:** Look › Size S · M · L = 0.8 · 1.0 · 1.25. At M: the strip is 48 px of a 1080 px window (0.0444), words 0.0222
  tall (11.5 px), the [12] 0.0407.
- **Places** (`cin.place`): `top` (under a 24 px menu bar), `topl` (lower, under 76 px of viewer bars), `bot` (above a
  46 px toolbar), `both` (higher, 96 px). The strip's centre line is at `±(0.5 − margin − H/2)`.
- **Width:** the words stay inside a centred 16:9 area (`W = min(aspect, 1.778)`); the band runs the full width.
  Shots start `inset` from the left of that area, options end `inset` from its right; `inset` = 180 px (0.1667),
  shrunk when the window is too narrow so nothing overlaps (never below 0.02).
- **Middle:** the [12] at x = 0; the shape cell ends 40 px left of it, the link cell starts 40 px right of it.
- **Depth:** dot and ring in front of the disc (−X), words at +0.001, box and halo at +0.002, band at +0.004, bars at
  +0.006 (crop's DEPTH rule: behind the button so it stays clickable).
- **Closed:** every strip part is shrunk to 0.01, alpha 0, at the root (invisible prims still catch clicks). Opening
  fades in over 0.2 s (alpha in 3 steps).
- **Touch:** `screen` reads touches on the parts (`llDetectedLinkNumber` → name): a shot word → CMD `shot|<name>`, an
  option word → OPT `<shot>|<word>`, the shape → CMD `bars`, the link → CMD `connect`. `ui` reads the root (gestures).

## 3. Scripts
All in the root; each compiles in `tools/lslcheck.sh` with **≥ 15 KB free** (the check fails below).

| Script | Job |
|---|---|
| `core` | Owns the camera (CONTROL_CAMERA, TRACK_CAMERA, TAKE_CONTROLS; one `llTakeControls`). States: `wait` (your own camera), `film`, `held` (you took the camera: Alt-click), `letgo` (flying, mouselook, a marked vehicle), `off` (hold), `watch` (you watch someone's film). Routes shots (START / STOP / NEXT / PAUSE / RESUME), applies SHOT / GLIDE / FOLLOW, the jump-cut rule, sit / stand, teleport, idle start, hold off / on, CAMSET for Connect |
| `ui` | The [12]'s gestures (tap 0.35 s → dialog, double-tap → the strip, hold 0.8 s → everything off / back), every dialog (main, Connect lists, Settings and its pages, Help, Reset), the first run, `/12` commands, defaults, the 7.x settings migration, owner change |
| `text` | Every word the user reads, by id (dialog bodies and labels, notes, tips); the notes on `t12 note` (3 s; important ones also in owner chat); the first-three-uses tip counters |
| `screen` | The strip and the [12] (section 2): places, sizes, the 16:9 cap, word states, the fade, touches, texture adoption |
| `bars` | The letterbox per shot (`cin.shape.<shot>`), Black or Dimmed, on / off; a watched film's shape; tells the shots the picture (CROP) and the strip the readout (SHAPE) |
| `tracking` | Shoulder · Film · Classic, L · R: the viewer's own follow camera (FOLLOW), walls, small rooms, running |
| `portrait` | Me · Us, Close · Medium · Wide: composed shots of you standing (SHOT / GLIDE) |
| `fixed` | Your own framing: View A / B per place, seat memory per object and spot, Keep new, Forget / Undo, Let go / Take back |
| `scenic` | Drift · Near · Room · Far: views of the place; the idle camera |
| `sync` | Connect: the nearby list, invites, two equal cameras, watching, sharing (`docs/CONNECT.md`) |
| `carry` | Between two copies worn by the same owner: carry-over of the settings, two worn (the older steps aside) |

The free **Take 12 Scenery** is generated (`tools/build_scenery.py`): core, ui, text, screen, bars, scenic, sync with
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
| 7340 OPTS | shot → screen | `<shot>\|<words, comma>\|<states, comma>`; a word `/` is the divider; states `` · `lit` · `accent` · `dim` |
| 7341 OPT | screen → shots | `<shot>\|<word>` |
| 7342 LINKST | sync → screen, core, ui | `<alone / on / shared / theirs / dim>\|<count>\|<name>` |
| 7343 STRIP | ui → screen | `toggle` · `open` · `close` · `hide` (off) · `show` (back) · `hold\|<0–8>` · `eye\|<z>` · `problem\|<0/1>` · `layout` |
| 7344 NOTE | any → text | `<id>\|<arg>` (text shows it 3 s on `t12 note`; important ids also go to owner chat) |
| 7345 TIP | screen, ui → text | `<word>` (a key's first three uses) |
| 7346 TXT / 7347 TXT_ANS | ui ↔ text | `<id>\|<args>` → `<id>\|<text>` |
| 7348 SHAPE | bars → screen | `<label>\|<on / off / dim>` |
| 7360 MSG_VER | all | `?` or a version (ui warns on a mismatch) |
| 7370 STATUS | ui → all | `?`: each script says one line |
| 7371 CMD | any → any | below |
| 7390 CROP | bars → shots | `<ratio>\|<window aspect>` (0: no bars): the picture to compose in |

CMD strings: `shot|<name>` (a shot word: start it, or its lit-tap job), `off` / `on` (hold), `bars`, `connect`,
`watch|<key>` / `unwatch` (sync → core), `letgo|veh` / `takeback` (fixed → core), `hint|<shot>`, `debug|<0/1>`,
`blend|<0/1>`, `standby` (carry: an older copy steps aside), `status`.

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
- **Off** (hold): camera, bars, strip all off; hold again restores exactly.

## 6. Linkset Data (`cin.*`, protected, PASS)
`ver`, `owner`, `place`, `size`, `open`, `shot` (the last shot, for Off / On), `por` (`<size 0–2>|<who 0 Me / 1 Us>`),
`trk` (`<look 0–2>|<side 0 L / 1 R>`), `scn` (`<band 0 drift … 3 far>`), `shape.<shot>`, `bars` (1 / 0), `bstyle`
(black / dim), `idle` (off / away / 5), `eye` (your eye line, a fraction of your height), `lens` (35 / 38 / 40),
`tips` (the uses per key), `chime`, `friends` (`key,name;…`), `veh` (`name|creator;…`), `view.<region>.<parcel>`
(Fixed's A and B), `seat.<object key>` (its spots), `seats` (the index for eviction), `gsit.<region>.<parcel>`
(ground sits), `firstrun`, `cfgv`.

## 7. Checks
`tools/lslcheck.sh` (compiles everything, fails under 15 KB free), `tools/build_scenery.py --check`, and the emulator
runs on the real scripts in `tools/sim/*_emu.py` (CI runs them all; see `.github/workflows/lsl-check.yml`).

## 8. Building the HUD
`hud/build/builder.lsl` (not shipped): rez a box, put the builder and one blank box named `t12 part` in it, touch it.
It rezzes the parts, links them, names them, then deletes itself. Add the scripts of `hud/src/` and drop the two
textures in; take it and wear it on HUD Top Center. Details: `hud/build/README.md`.
