# Take 12: Architecture (v4)

- What the product is: `docs/PRODUCT.md`.
- The order of work: `docs/ROADMAP.md`.
- The frozen v3 is in `legacy/v3/`, with its own ARCHITECTURE.

This document is the coding spec. Where it gives a number or a formula, use it. Where it says "verify in-world", leave a `// TUNE:` comment and a CALIBRATION row.

## 1. Scripts
All six scripts go in the **root prim** of a one-prim HUD. Each must compile clean in `tools/lslcheck.sh` and estimate **≥ 15 KB free**.

| Script | Job | v3 statements | v4 target (est. free) |
|---|---|---|---|
| `cinema_core.lsl` | Owns the camera: permissions, controls, AFK, modes, exits, hold timer, peek, pauses, watchdog plus basic shots, reach verification, `grab` test. **New:** FREEZE (photo hold), GLIDE, SPEAKER (owner typing), FAV forwarding, richer UI_STATE. **Touch handlers removed.** | 302 | ~350 (≥ 23 KB) |
| `cinema_scenery.lsl` | Default mode. Outdoor drone and wide finder (v3). **New:** room classifier, room-shot finder, favourites | 178 | ~330 (≥ 25 KB) |
| `cinema_people.lsl` | Personal and Social (v3). **New:** chat cuts in Social | 384 | ~420 (≥ 21 KB) |
| `cinema_friends.lsl` | **New.** Friends mode (group framing, glide and snap, chat cuts) | – | 472 (18.4 KB est.) |
| `cinema_picker.lsl` | **New.** The Friends menu page and the picker. It was split out of `cinema_friends` to keep both above 15 KB | – | 156 (35.8 KB est.) |
| `cinema_ui.lsl` | **Touch decoding** (tap, double-tap, long press), emoji menus, `/77` commands, settings, the button look (alpha fade and clap) | 173 | ~300 (≥ 17 KB) |

If a script lands under 15 KB, move text out of it first (help lines, long trace strings). Do not split logic across scripts mid-function.

## 2. Link messages
The numbers from v3 are unchanged. **Bold** marks what is new in v4.

| num | from → to | string | notes |
|---|---|---|---|
| 7301 START | core → all | `"<mode>|<fov>"` | mode = `scenery` / `personal` / `social` / **`friends`**. Only the owner of that mode takes it |
| 7302 STOP | core → all | reason | |
| 7303 NEXT | core → active | why: `hold` / `retry` / **`skip`** | |
| 7304 PAUSE / 7305 RESUME | core → active | `ml` / `tp` / `peek` / **`photo`** | |
| 7306 MOVING | core → active | – | movement key in a following mode |
| 7310 SHOT | worker → core | `"<pos>|<focus>|<hold>|<type>"` | a hard cut |
| 7311 NO_SHOT | worker → core | reason | core covers it with a basic shot |
| **7312 GLIDE** | friends → core | `"<pos>|<focus>"` | a slow move, see §5 |
| 7313 ACK | worker → core | mode | |
| 7314 REACH_FAIL | core → scenery | distance | |
| **7315 SPEAKER** | core → active | owner key | you started typing (Social and Friends only) |
| **7316 FAV** | core → scenery | `"<pos>|<focus>"` | save the shot on screen as a favourite |
| 7320 UI_STATE | core → ui | **`"<state>|<mode>|<nextCutUnix>"`** | state = `off` / `armed` / `rolling` / `peek` / **`frozen`** |
| 7321 UI_MENU | picker → ui | page: `main` / `live` / `opts` | the picker sends `main` for "↩ Back" |
| **7322 UI_FRIENDS** | ui → picker | `page` / `pick` / `list` / `clear` | the picker script runs the Friends page and the picker |
| 7330 CFG_CHANGED | ui or friends → all | key | |
| 7360 VERSION | all | version, or `?` | |
| 7370 STATUS | ui → all | `?` | every script prints one line |
| 7371 CMD | ui → core | `scenery` / `personal` / `social` / **`friends`** / `stop` / **`next`** / **`photo`** / **`fav`** / `grab` | |

**Shot types**
| Group | Type | Meaning |
|---|---|---|
| People | 0 | portrait |
| People | 1 | pair or over-the-shoulder |
| People | 2 | group |
| People | **3** | friends group |
| People | **4** | speaker |
| Scenery | 5 | drone |
| Scenery | 6 | wide |
| Scenery | **7** | favourite |
| Scenery | **10** | room corner |
| Scenery | **11** | room centre |
| Scenery | **12** | room "you small" |
| Core | 9 | basic |

Reach verification (§3) applies to types 5, 6 and 7 only.

## 3. Core changes
**States:** IDLE 0, WAIT 1, ROLL 2, PAUSE 3, PEEK 4, TEST 5, **FREEZE 6**.

- **Touch:** delete `touch_start`, `touch` and `touch_end` from core, along with `gTouchT`, `gTouchSkip`, `gMenuShown` and `TOUCH_LONG`. The UI sends CMDs instead.
- **UI_STATE:** `setUi(st)` sends `st + "|" + gMode + "|" + (string)gNextCut`.
  - `gNextCut = llGetUnixTime() + llRound(gHold)` is set in `applyShot`.
  - Call `setUi` on every applyShot, not only on a state change. That is cheap, and the live menu shows "next cut in N s".
- **CMD `next`:** if the state is ROLL or FREEZE: leave FREEZE (send RESUME `photo`), then `askWorker("skip")`.
- **CMD `photo`:**
  - From ROLL or PEEK → FREEZE:
    - send PAUSE `photo`;
    - re-apply `gLast` (snap back if the user had orbited);
    - `setUi("frozen")`.
  - From FREEZE → ROLL:
    - send RESUME `photo`;
    - re-apply `gLast`;
    - `gHold = 8.0`, so it continues briefly and then cuts;
    - `setUi("rolling")`.
- **FREEZE behaviour in `activeTick`:**
  - The exits run as for the mode: typing, sitting, and movement keys in Scenery.
  - Mouselook and teleport pause as usual. Resuming from that pause returns to FREEZE, not ROLL; keep a `gFrozen` flag.
  - **No** hold countdown, **no** peek check and **no** watchdog.
  - Incoming SHOT or GLIDE messages are ignored while frozen (the workers are paused too), so the frozen shot never changes.
- **CMD `fav`:**
  - In Scenery while ROLL or FREEZE: send FAV with the pos and focus of `gLast` (the first two fields), and say "⭐ saved".
  - Otherwise say "⭐ Save works in Scenery".
- **GLIDE (7312):**
  - Accept it only in ROLL, with `gMode == "friends"`.
  - Call `llSetCameraParams([CAMERA_POSITION, p, CAMERA_FOCUS, f, CAMERA_POSITION_LAG, 1.5, CAMERA_FOCUS_LAG, 1.5])`, leaving the locks and thresholds as already set.
  - Set `gShotPos = p` and `gGlideUntil = llGetTime() + 3.0`.
  - The peek check is skipped while `llGetTime() < gGlideUntil`.
  - Do **not** touch `gHold`, `gType` or `gVerify`.
  - Set `gGlided = TRUE`.
- **The cut after a glide:** in `setCam`, if `gGlided`, call `llClearCameraParams()` first (the same as cut mode) and clear `gGlided`. The lag-0 cut is then never eased by the leftover lag. *Verify in-world that lag eases a locked camera between positions. v3's "cut mode" shows that viewers do ease locked cameras. If lag does nothing, fall back to 5 GLIDE steps 0.3 s apart sent by the friends script (TUNE).*
- **Typing:** in `activeTick`, `if (info & AGENT_TYPING)`:
  - Mode `scenery` or `personal` → `bail("typing")`, as in v3.
  - Mode `social` or `friends`:
    - If `!gTypingSent`: send SPEAKER with the owner key and set `gTypingSent = TRUE`.
    - Clear `gTypingSent` when typing stops.
- **Watchdog and basic shots:** `friends` uses the people basic shot (portrait orbit).
- **Status line:** add `frozen`, the glide count and `friends` to the mode names.

## 4. UI (`cinema_ui.lsl`)
### 4.1 Touch decoder
Owner only:
```
touch_start: gDown = llGetTime(); gHeld = TRUE; gLongDone = FALSE; fast timer (0.05 s)
timer:       if gHeld && !gLongDone && now-gDown >= 0.8 → gLongDone = TRUE; onLong()
             if gTapN && now-gTapT > 0.35 → gTapN = FALSE; onTap()
touch_end:   gHeld = FALSE
             if gLongDone → return                      // long press already handled
             if gTapN && now-gTapT <= 0.35 → gTapN = FALSE; onDouble()
             else gTapN = TRUE; gTapT = now
```
- The timer returns to the menu-timeout cadence (5 s) or to off when nothing is pending. Use one `timer()` with a `nextTimer()` helper that picks the rate.
- `gUiState` (from UI_STATE):
  - `idle` = off or armed;
  - `rolling` = rolling or peek;
  - `frozen`.

| | idle | rolling | frozen |
|---|---|---|---|
| `onTap()` | `openMenu("main")` | CMD `stop` | CMD `photo` (resume) |
| `onDouble()` | CMD `scenery` | CMD `next` | CMD `next` |
| `onLong()` | `openMenu("main")` | `openMenu("live")` | `openMenu("live")` |

Port this decoder to Python in `tools/sim/tap_test.py` and test these sequences:
- a single tap;
- a double tap at 0.2 s;
- two taps 0.5 s apart (two singles);
- a long press of 1.0 s;
- a long press followed by a tap.

### 4.2 Button look
- `setLook(state)`:
  - `PRIM_COLOR, ALL_SIDES, <1,1,1>, alpha` with alpha 1.0 when idle and **0.15** when rolling or frozen;
  - `PRIM_GLOW 0` and `PRIM_FULLBRIGHT TRUE`, set once.
- **No colour changes ever.**
- **Clap** on idle→rolling:
  - `llOffsetTexture(0.25, 0.0, ALL_SIDES)` (frame 2, clapped);
  - after 0.3 s `llOffsetTexture(-0.25, 0.0, ALL_SIDES)` (frame 1);
  - then fade.
- The texture is set up by the builder (README): repeats 0.5 × 1.0, offset -0.25. `state_entry` calls `llScaleTexture(0.5, 1.0, ALL_SIDES)` and `llOffsetTexture(-0.25, 0.0, ALL_SIDES)`, so a fresh prim is right too.

### 4.3 Menus
- **Table-driven.** Each button is a pair `[id, emoji]`, for example `["scenery", "🏞"]`.
  - The label is `emoji + " " + Title(id)`, or `Title(id)` alone when `cin.emoji` is `0`.
  - Replies are matched by stripping everything up to and including the first space when the label starts with a non-ASCII character, then comparing case-insensitively with the title. One `onChoice` handles both styles.
- **Layout helper:** `llDialog` fills from the **bottom-left**, so write each page top row first and pass it through `order(list b)`, which reverses the rows of three.
- **Label rules:** at most 24 bytes; aim for ≤ 10 visible characters after the emoji. The exact labels are in PRODUCT.md. Keep them.
- **Header:**
  - First line: `🎬 Cinema · <status>`.
  - Second line: `Pace: <name> (<s> s) · AFK: <text> · Indoors: <auto|inside|outside>`.
  - The live page shows `next cut in N s` from `nextCutUnix`.
  - The text-only fallback uses `Cinema - ` in place of the emoji.
  - Keep each dialog under 512 bytes.
- **Pages:**
  - `main`, `live`, `pace`, `afk`, `opts`, `indoors`, `chat`, `favs`, `altcam`, `reach` and `reset`.
  - `friends` and `pick` belong to the friends script: the UI sends UI_FRIENDS `page`, and the friends script answers "↩ Back" with UI_MENU `main`.
- **Live page:**
  - 📷 Photo shows as ▶ Resume when frozen.
  - ⭐ Save shows only when the mode is `scenery`; in other modes the space is left out.
- **The listener:**
  - removed on Close, on choosing a mode, and after **60 s** of no reply;
  - re-created on each `openMenu` with a fresh random negative channel.
- **First run** (new owner): one welcome **dialog**, not a chat wall:
  ```
  🎬 Welcome to Cinema
  Double-tap: scenery camera
  Tap: menu · while rolling, tap stops
  Hold: live menu · AFK starts it by itself
  ```
  Buttons `[👍 Got it][❔ Help]`. It also gives the notecard.

### 4.4 Settings (`cin.*`, protected Linkset Data)
| Key | Default | Notes |
|---|---|---|
| `afk_on`, `afk_sec` | 1, 90 | as v3 |
| `hold` | 60 | the Pace value in seconds (key kept for compatibility) |
| `reach` | 100 | learned. `relearn` sets 100 and clears `reach_ok` |
| `reach_ok` | 0 | scenery: cuts since the last REACH_FAIL, for regrowth (§6.5) |
| `indoors` | `auto` | `auto` / `inside` / `outside` |
| `chat_cuts` | 1 | |
| `emoji` | 1 | |
| `peek`, `peek_bail`, `phantom`, `cutmode`, `trace`, `cmd_chan` | as v3 | `cutmode` is now command-only |
| `friends` | "" | written by the friends script: `key,name;key,name;…`, at most 10 |
| `fav.<region>` | "" | written by scenery: `pos|focus;pos|focus;…`, at most 8. The region name has spaces replaced by `_` |
| `seen_intro` | 0 | the welcome dialog has been shown |
| `theta_max`, `aspect` | 10, 1.778 | as v3 |

**Version mismatch warning:** "Re-drop all Cinema scripts from the same release." It no longer says "four".

### 4.5 Commands
All commands are listed in PRODUCT.md.
- `pace <s>` takes 10–600 s and writes `hold`; `hold <s>` is kept as an alias.
- `friend list|clear` is forwarded to the friends script as CMD-like UI_FRIENDS `list` / `clear`.

## 5. Friends (`cinema_friends.lsl`, new)
- **Copied from `cinema_people.lsl`** (separate memory, so they are copied, not shared): `cfg`, `fmin`, `fmax`, `fclamp`, `dirOf`, `tsay`, `ray`, `refreshOwner`, `survey`, `camZ`, `fitDist`, `planG` (generalised below), `tryCand`, `sweep`, `shoulderShot`, `inFrame`, and the FOV maths in `loadCfg` / START.
- **Friends list:**
  - Kept as two lists, `gFKeys` and `gFNames`, loaded from `cin.friends` on START and on CFG_CHANGED `friends`.
- **Presence scan** (1 s):
  - From `llGetAgentList(AGENT_LIST_REGION, [])`, keep the keys that are in `gFKeys` and within **30 m** of you.
  - `gTargets = [you] + their positions`, with eye heights from `llGetAgentSize`.
- **Planning:**
  - `planF()` = `planG` over `gTargets`. It already works for two people (you plus 1 friend, a two-shot square-on to your axis).
  - Distance: `fitDist(spread, 1.3, 3.0, 25.0)`.
  - If the fit wants more than 25 m, drop the target farthest from you and re-plan, until it fits or only you are left.
  - With only you left: Personal-style `planA(FALSE)` and one note.
- **Hold:** a cut every 25 s × (0.8–1.2) for a fresh angle (type 3).
- **Glide and snap loop** (timer 0.5 s while active and not paused):
  1. Refresh the owner and target positions (no full region scan; that stays at 1 s).
  2. `allIn` = every target passes `inFrame(p)`, using `gCurCam` / `gCurV` and `0.9 × halfH`.
  3. If `allIn`:
     - `gOutTicks = 0`.
     - If the centroid C has moved more than 0.4 m since the last shot or glide: the new cam = old cam + (C − C_last), with z re-derived by `camZ`, and the new focus = old focus + (C − C_last).
     - Check `ray(oldCam, newCam)` and `ray(newCam, newFocus)`. If both are clear, send GLIDE. Otherwise re-plan with a SHOT.
  4. If not `allIn`: `gOutTicks++`. At **2 ticks (1 s)**: re-plan with `MARGIN` × 1.3 → SHOT (a snap).
  5. The **arrival** of a new friend means a pending cut at the next `MIN_HOLD` (6 s) boundary.
- **Chat cuts:**
  - `llListen(0, "", NULL_KEY, "")` while active and `chat_cuts` is on. Remove it on STOP.
  - A speaker must be in `gFKeys` and present, or be the owner (from SPEAKER).
  - The speaker is not cut to again within 10 s, and at least 6 s must have passed since the last cut.
  - Speaker shot (type 4), held 8 s, no glide during it:
    - a friend speaks → an over-the-shoulder shot from behind you, facing the friend (`planA(TRUE)` logic with N = the speaker and `gRev = FALSE`);
    - you speak → from behind the nearest friend, facing you (`gRev = TRUE`).
  - Then back to a group shot.
- **Menu pages** (own dialog channel, own listener, 60 s timeout):
  - `page`:
    - header `💞 Friends · <n> saved · <m> here now` plus their names, truncated to 400 bytes;
    - buttons `[▶ Start][➕ Pick][🗑 Clear] [↩ Back][✖ Close]`;
    - ▶ Start → CMD `friends`.
  - `pick`:
    - avatars within 20 m, nearest first, excluding you, 9 per page;
    - label = `"✓ " + llGetUsername(k)` if saved, else the username, cut to 22 bytes;
    - extra buttons `[▶ More]` (if there is another page) and `[✔ Done]`;
    - a tap toggles and re-opens the same page;
    - map label → key with a parallel list built when the page opens;
    - at most 10 saved; at 10 say "Friends list is full (10)".
  - `🗑 Clear` asks for confirmation, `[Yes, clear][↩ Back]`.
- **Status line:** saved count, present count, glides, snaps and free memory.

## 6. Scenery (`cinema_scenery.lsl`)
### 6.1 Outdoor
Unchanged from v3: `findShot`, `nextShot`, context, `REACH_FAIL`. Read `legacy/v3/docs/ARCHITECTURE.md` §Scenery.

### 6.2 Room classifier (in `context()`, once per session or after a 10 m move)
- Eye point `E = gOP + <0, 0, 0.6>`.
- Rays:
  - **8 horizontal rays** from E, 60 m long, at azimuths `i × 45°` → `gWallD[i]` (60 if not hit). Let `nHit` be the count of hits.
  - **Up:** the existing 40 m ray → `gCovered`, and the ceiling `gCeilZ = E.z + hit distance`.
  - **Down:** from `gOP` to `gOP − <0, 0, 30>` → `gFloorZ` (the hit z), or `gFloorless = TRUE` if nothing is hit.
- `gEnclosed = gCovered && nHit >= 6`.
- `gSky = gFloorless || (gOP.z − llGround(ZERO_VECTOR) > 50.0)`.
- Decide `gInside`:
  - `indoors == "inside"` → `gInside = gEnclosed`;
  - `"outside"` → FALSE;
  - `auto` → `gEnclosed && gSky`.
- `gSpan` = the largest `gWallD`, and `gInsideFails = 0`.
- **Trace (once per context):** `scenery: inside a room (8/8 walls, ceiling 4 m, span 23 m)`, or `outdoors`, or `enclosed on the ground → above the roof`.

### 6.3 Room shots (when `gInside`)
- `findRoomShot()` builds up to **6 candidates**, two of each kind, and keeps the best by score. The kinds are chosen with weights corner 0.45, centre 0.30 and small 0.25, with each candidate rolling its kind.
- The camera height `zc` is always clamped to `[gFloorZ + 1.2, gCeilZ − 0.6]`.

| Kind | Camera | Focus |
|---|---|---|
| **Corner wide (10)** | `zc = min(gCeilZ − 0.6, gFloorZ + 6.0)`. From `<gOP.x, gOP.y, zc>` (first check that the vertical ray from E to there is clear), cast 8 diagonal-biased rays at `22.5° + i × 45°`, 60 m long. Take the 2 longest (corners in a box room) and put the camera `0.8 m` back from each hit | The point on the floor plane 1/3 of the way from the opposite corner to you (looks across the room through your area), pitch clamped to 15–45° down |
| **Room centre (11)** | The centroid of the 8 horizontal wall-hit points from §6.2, at `gFloorZ + 1.7` | Along the direction from the centroid to the farthest wall-hit point, level (2° down) |
| **You small (12)** | Along the longest `gWallD[i]`, `gWallD[i] − 0.8` from you, at `gFloorZ + 2.5`. Skip it if that is less than 6 m | You (`gOP`), so you are a small figure in the frame |

**Every candidate must pass, in this order** (stop at the first failure to save rays):
1. Inside the region `[1, 255]`.
2. **Same room:** `ray(E, cam)` has no hit before `|cam − E| − 0.2`.
3. **Clearance:** 5 rays of 0.5 m from the camera (±x, ±y, +z) are all clear.
4. **View:** `ray(cam, cam + norm(focus − cam) × 60)` is clear for at least `max(3, 0.4 × gSpan)`. For "you small": clear up to `|focus − cam| − 1`.

**Score** = `3 × clear/60 + 2 × novelty(az of cam from you) + 1 if the kind differs from the last + rand(0.5)`.

If nothing passes:
- `gInsideFails++` and fall back to `findShot` (outdoor logic, which puts the camera above the roof);
- after 3 fails in a row, trace once: "room too small for room views; using outside views here".

**Hold:** `gHold × (0.75 + 0.5 × rand)`, the same as outdoors.

### 6.4 Favourites
- **FAV received** (from core):
  - append `pos|focus` to `cin.fav.<region>`;
  - drop the oldest beyond 8;
  - trace "⭐ saved (n/8 here)".
- **Using favourites:** when `gCuts % 4 == 3` and the region has favourites, pick one that:
  - is not `gLastFav`;
  - has a camera within `gReach + 20` of you;
  - passes a 10 m view-ray check (`ray(cam, cam + norm(focus − cam) × 10)` is clear).

  Send it as type 7. If none passes, fall through to the normal finder.
- **Clearing:** Options › Favourites › Clear here / Clear all. The UI deletes the keys with `llLinksetDataDeleteProtected`, or for "all", by finding the keys with `llLinksetDataFindKeys("^cin\\.fav\\.", 0, 0)`.

### 6.5 Reach regrowth (fix)
- After **20 consecutive cuts** without a REACH_FAIL (saved in `cin.reach_ok`), raise `gReach` by 10 %, up to 100 m, and save it.
- REACH_FAIL resets the count.

## 7. People (`cinema_people.lsl`): chat cuts in Social
- On START `social` with `chat_cuts` on: `gChat = llListen(0, "", NULL_KEY, "")`. Remove it on STOP and on a switch.
- `listen`:
  - Ignore non-agents (`llGetAgentSize(id) == ZERO_VECTOR`) and the owner (the owner arrives as SPEAKER).
  - The speaker must be within `R_GRP` (8 m), and not the same speaker within 10 s.
  - Set `gSpeaker = id` and `gPendEvent = "speaker"`.
- **SPEAKER (owner):** `gSpeaker = owner` and `gPendEvent = "speaker"`.
- **In `nextShot`**, when the event is "speaker":
  - A speaker other than you: `gNPos` / `gNEye` = the speaker, `gRev = FALSE`, then `planA(TRUE)` → over your shoulder, facing them.
  - You: `gNPos` = the nearest other, `gRev = TRUE`, then `planA(TRUE)` → over their shoulder, facing you.
  - Nobody else near: a portrait of you.
  - The type is 4, and the hold is 8–12 s.
- The pending-event mechanism and MIN_HOLD 6 s are unchanged.

## 8. Building and textures
- **Icon:**
  - The source is `tools/art/make_icon.py`, with pixel grids as strings.
  - Its outputs:
    - `hud/art/cinema_icon_256x128.png`: 2 frames side by side, each 16×16 scaled ×8 with nearest-neighbour, on a transparent background;
    - previews.
  - **Upload settings:** no lossless needed; the alpha must be kept.
  - **On the prim:**
    - Texture face: the face that points at you on the HUD. In Edit, select the face, apply the texture, repeats 0.5 × 1, offset −0.25.
    - All other faces get the default transparent texture.
- **Prim:** one box, size `<0.01, 0.04, 0.04>`, which is about 40 px on a 1080 px screen. Attach it to **HUD Top Right** and drag it into place.

## 9. Checks and sims
| Tool | Covers |
|---|---|
| `tools/lslcheck.sh` | Compiles `hud/src/*.lsl` and `legacy/v3/src/*.lsl` and estimates memory |
| `tools/sim/scenery_sim.py` | Outdoor finder (v3), unchanged |
| `tools/sim/people_geometry.py` | Composition, unchanged |
| **`tools/sim/room_sim.py`** | Python port of §6.2–6.3 over these worlds: skybox box 20×20×5 at z 3000, sky mall 60×40×8, small room 4×4×3, ground house (must classify as enclosed-ground → outside), open field (must not be enclosed), and an L-shaped room. Assert: `gInside` is as expected, and the camera is inside the room's box with ≥ 0.5 m margin, in the same room as the owner and with a clear view. Seeded, 40 shots per world |
| **`tools/sim/friends_sim.py`** | Port of the §5 loop. Targets walk on scripted paths. Assert: a glide when the centroid moves more than 0.4 m with everyone in frame; a snap within 2 ticks when someone leaves; the fit distance ≤ 25 m; no glide through a wall box |
| **`tools/sim/tap_test.py`** | The §4.1 decoder sequences |

CI (`.github/workflows/lsl-check.yml`) runs all of them.
