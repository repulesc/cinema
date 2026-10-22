# Take 12: Architecture (v4)

- What the product is: `docs/PRODUCT.md`.
- The order of work: `docs/ROADMAP.md`.
- The frozen v3 is in `legacy/v3/`, with its own ARCHITECTURE.

This document is the coding spec. Where it gives a number or a formula, use it. Where it says "verify in-world", leave a `// TUNE:` comment and a CALIBRATION row.

## 1. Scripts
All ten scripts go in the **root prim** of a one-prim HUD. Each must compile clean in `tools/lslcheck.sh` and estimate **≥ 15 KB free**.

| Script | Job | v3 statements | v4 target (est. free) |
|---|---|---|---|
| `cinema_core.lsl` | Owns the camera: permissions, controls, AFK, modes, exits, hold timer, peek, pauses, watchdog plus basic shots, reach verification, `grab` test. **New:** FREEZE (photo hold), GLIDE, SPEAKER (owner typing), FAV forwarding, richer UI_STATE. **Touch handlers removed.** | 302 | ~350 (≥ 23 KB) |
| `cinema_scenery.lsl` | Default mode. Outdoor drone and wide finder (v3). **New:** room classifier, room-shot finder, favourites | 178 | ~330 (≥ 25 KB) |
| `cinema_people.lsl` | Personal and Social (v3). **New:** chat cuts in Social | 384 | ~420 (≥ 21 KB) |
| `cinema_friends.lsl` | **New.** Friends mode (group framing, glide and snap, chat cuts) | – | 472 (18.4 KB est.) |
| `cinema_lens.lsl` | **New in 5.0, reworked in 5.1: Follow my lead.** Core sends LEAD 7324 `"<cam>\|<focus>"` when your own camera (Alt-orbit) has been still for 1.5 s in Friends, and holds that view. Lens keeps how far, how high, from where and the aim (relative to the subject Friends planned, sent as the 5th SHOT field) and sends LENS 7319 `"<distance>\|<angle down>\|<from>\|<aim>\|<cut>"` (distance 0 = automatic). Seated W/S scale the distance (core keeps back only FWD/BACK). Auto: long press, sitting or standing up, a friend coming or going (`autoq` from Friends) | – | 90 (40.7 KB est.) |
| `cinema_sync.lsl` | **The sharing manager (5.5).** Hold = the Share panel (CMD `share` from the UI's long press and the tap menu). States IDLE / LIVE / VIEWING / INVITED, a `who` check, push invites, pull views, Ask / Always / Never lead, a roster (Pass camera, Remove), heartbeat and timeouts, the state above the HUD. Core starts the camera (CMD `sharecam` → Social) and reports it (CAMSET 7325); `⋯ More` sends CMD `livemenu` / `mainmenu` back to the UI. Everything else, protocol included: `docs/SHARING.md` | – | 396 (19.5 KB est.) |
| `cinema_frame.lsl` | **New in 4.6.** Frame: three held framings of you, or of you and whoever stands within 3 m (automatic), the two-anchor solver, lead room, seated framings, mixed-height groups, obstacle tries, key nudges, silent zoom re-framing, the name shown for 3 s. No menus or listeners. See `docs/FRAME.md` | – | 261 (31.0 KB est.) |
| `cinema_picker.lsl` | **New.** The Friends menu page and the picker. It was split out of `cinema_friends` to keep both above 15 KB | – | 156 (35.8 KB est.) |
| `cinema_tips.lsl` | **The text above the button (5.8; tips since 5.7).** The one owner of the hover text. It composes, top to bottom: the sharing block from sync (TEXT 7380), the **status line** while a camera runs (mode and who is in charge, from UI_STATE's `why` and LENS 7319: `◇ Scenery · auto`, `… · started while you were idle`, `♡ Only friends · your view`, `▣ Photo · held`, `… · paused · Esc to carry on`; nothing with your own camera, only the 👁 block while watching; `cin.status` 0 hides it), and a tip. It writes only when the composed text changes and never over another script's short notice (text on screen that it did not write last); when that is cleared it redraws within 1 s. Tips: UI_STATE transitions, 6 s, at most one per 20 s, the second line only under a status line; a tip that finds no free moment in 10 s is dropped, not counted. Each tip retires after 3 showings (`cin.tipn`); when all have retired, or after 24 in all, it writes `tips=0`, sends CFG_CHANGED `tips` and says one line. No menus or listeners | – | 154 (34.3 KB est.) |
| `cinema_ui.lsl` | **Touch decoding** (tap, double-tap, long press), emoji menus, `/77` commands, settings, the button look (the plain logo, always the same) | 173 | ~300 (≥ 17 KB) |

If a script lands under 15 KB, move text out of it first (help lines, long trace strings). Do not split logic across scripts mid-function.

## 2. Link messages
The numbers from v3 are unchanged. **Bold** marks what is new in v4.

| num | from → to | string | notes |
|---|---|---|---|
| 7301 START | core → all | `"<mode>|<fov>"` | mode = `scenery` / `personal` / `social` / **`friends`** / **`frame`**. Only the owner of that mode takes it |
| 7302 STOP | core → all | reason | |
| 7303 NEXT | core → active | why: `hold` / `retry` / **`skip`** | |
| 7304 PAUSE / 7305 RESUME | core → active | `ml` / `tp` / `peek` / **`photo`** | |
| 7306 MOVING | core → active | – | movement key in a following mode |
| 7310 SHOT | worker → core | `"<pos>|<focus>|<hold>|<type>"` | a hard cut |
| 7311 NO_SHOT | worker → core | reason | core covers it with a basic shot |
| **7312 GLIDE** | friends, frame → core | `"<pos>|<focus>"` or `"<pos>|<focus>|<lag>"` | a slow move, see §5 (Frame: 0.35 s for nudges and zoom changes) |
| 7313 ACK | worker → core | mode | |
| 7314 REACH_FAIL | core → scenery | `<asked>\|<allowed>` distances from you | |
| **7315 SPEAKER** | core → active | owner key | you started typing (Social and Friends only) |
| **7316 FAV** | core → scenery | `"<pos>|<focus>"` | save the shot on screen as a favourite |
| **7317 NUDGE** | core → frame | control level bits | Frame: the movement keys held now (sent on each change); core holds the keys with pass-on off in this mode only |
| **7318 FOVMSG** | core → frame | radians | Frame: the viewer's field of view changed (checked every 0.5 s) |
| **7319 LENS** | lens → friends | `<distance>\|<angle down rad>\|<from rad>\|<aim>\|<cut now>` | 5.1 Follow my lead: distance 0 = automatic. Friends plans its group shot from it: subject + aim, that distance and angle, from that side |
| **7325 CAMSET** | core → sync | `<pos>\|<focus>\|<lag>` | 5.2: every camera core puts on screen (cuts and glides), relayed to watchers |
| **7324 LEAD** | core → lens | `<cam>\|<focus>` | 5.1: in Friends, your own camera held still for 1.5 s; core holds it as the shot |
| 7320 UI_STATE | core → ui, tips | **`"<state>|<mode>|<nextCutUnix>|<why>"`** | state = `off` / `armed` / `rolling` / `peek` / **`frozen`**; why (5.8) = `idle` when the idle start began this run, else empty |
| 7321 UI_MENU | picker → ui | page: `main` / `live` / `opts` | the picker sends `main` for "↩ Back" |
| **7322 UI_FRIENDS** | ui → picker | `page` / `pick` / `list` / `clear` | the picker script runs the Friends page and the picker |
| 7330 CFG_CHANGED | ui or friends → all | key | |
| 7360 VERSION | all | version, or `?` | |
| **7380 TEXT** | sync → tips | `"<live/view/inv or empty>\|<the sharing block>"` | 5.8: tips stacks it above the status line |
| 7370 STATUS | ui → all | `?` | every script prints one line |
| 7371 CMD | ui → core | `scenery` / `personal` / `social` / **`friends`** / **`frame`** / `stop` / **`next`** / **`photo`** / **`fav`** / `grab` | |

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
- **UI_STATE:** `setUi(st)` sends `st + "|" + gMode + "|" + (string)gNextCut + "|" + gWhy`. `engage()` clears `gWhy`; the idle start sets it to `idle` after engaging and sends `rolling` again.
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
  - `main`, `live`, `pace`, `afk`, `opts`, `indoors`, `chat`, `favs`, `altcam`, `seat`, `reach` and `reset`.
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
| `afk_on`, `afk_sec`, `afk_away` | 1, 180, 1 | idle start after `afk_sec` with no keys, typing or camera moves; with `afk_away` also only while the viewer reports AGENT_AWAY (the viewer clears it on mouse movement). Settings step 5 (4.7.0) moves 90 s and the old "away" to 180 + mouse check |
| `hold` | 60 | the Pace value in seconds (key kept for compatibility) |
| `reach` | **100** (4.4.5) | the furthest Scenery camera in use. Learned: lowered when the viewer really stops far cameras short (§6.5), and grown back up to `reach_set` |
| `reach_set` | **100** | the furthest you chose (menu 50 / 100 / 150 / 200, or `/77 reach <m>`, 20–250). `relearn` sets `reach` back to `reach_set` and clears `reach_ok`. `cfgv` is a number and each step runs once (4.4.4 compared strings, so every rez re-ran them: Chat text was forced off and the learned reach was copied into `reach_set`). Step 4 (4.4.5) sets both to 100, keeping only a chosen 50 or 200 |
| `seat_deg` | **45** (4.8.0) | seated view: degrees above your eye line (0 off, 30 / 45 / 60). Read by people and friends (`gSeatEl`); `camZ` raises the camera while `gOSit`, `tryCand` pitches it down by that angle plus the rule-of-thirds offset; a change of sit state sets the `seat` event for a calm re-frame |
| `reach_ok` | 0 | scenery: cuts since the last REACH_FAIL, for regrowth (§6.5) |
| `indoors` | `auto` | `auto` / `inside` / `outside` |
| `chat_cuts` | 1 | |
| `skin` | **1** (5.7.0) | menu style: 0 Plain, 1 Symbols, 2 Color (Options › Look, `/77 skin`). Settings step 7 moves the 5.6.0 default (Plain) to Symbols |
| `status` | 1 (5.8.0) | the status line above the button (Options › Look › Status line, `/77 statusline on\|off`) |
| `tips`, `tipn` | 1, 0 | Tips on, and the showings per tip (one digit each, 12 tips). Help › Tips (or `/77 tips on`) turning them back on writes `tipn` 0 first. Step 7 turns them on for everyone |
| `peek`, `peek_bail`, `phantom`, `cutmode`, `cmd_chan` | as v3 | `cutmode` is now command-only |
| `trace` | **0** (4.4.2; it was 1) | "Chat text". Off: no startup lines, no per-cut lines, no echo after menu choices. Errors, warnings and the answers to typed commands always show. A one-time migration (`cfgv` = 2) turned it off on older installs |
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
  - Distance: `needAt()` (§7.1), 3–25 m.
  - If the fit wants more than 25 m, drop the target farthest from you and re-plan, until it fits or only you are left.
  - If no side has room (walls closer than the fit, 4.4.6), re-plan with one friend fewer, nearest first, up to 3 times, before the portrait.
  - With only you left: Personal-style `planA(FALSE)` and one note.
- **Hold:** `gBase` = 0.75 × Pace (20–150 s; Calm 60 s → 45 s) × (0.85–1.15) for a fresh angle (type 3). A speaker shot (type 4) is `max(14, 0.4 × gBase)`.
- **Glide and snap loop** (timer 0.5 s while active and not paused):
  1. Refresh the owner and target positions (no full region scan; that stays at 1 s).
  2. `allIn` = every target passes `inFrame(p)`, using `gCurCam` / `gCurV` and `0.9 × halfH`.
  3. If `allIn`:
     - `gOutTicks = 0`.
     - If the centroid C has moved more than 0.4 m since the last shot or glide: the new cam = old cam + (C − C_last), with z re-derived by `camZ`, and the new focus = old focus + (C − C_last).
     - Check `ray(oldCam, newCam)` and `ray(newCam, newFocus)`. If both are clear, send GLIDE. Otherwise re-plan with a SHOT.
  4. If not `allIn`: `gOutTicks++`. At **2 ticks (1 s)**: re-plan with `MARGIN` × 1.3 → SHOT (a snap).
  5. **Pull-back (4.4.6):** everyone is in, but someone is past 80 % of the half-width: GLIDE the camera (and focus) straight back along the view until everyone is within 60 % again. No cut. If the camera would end more than 25 m from the group, or a ray says there is a wall behind it, cut to a wider shot instead. (In 4.4.6 `allIn` uses 97 %, and the glide threshold is 0.2 m.)
  6. The **arrival** of a new friend means a pending cut at the next `gMinHold` boundary (`max(12, 0.25 × Pace)`; Calm 15 s).
- **Chat cuts:**
  - `llListen(0, "", NULL_KEY, "")` while active and `chat_cuts` is on. Remove it on STOP.
  - A speaker must be in `gFKeys` and present, or be the owner (from SPEAKER).
  - The speaker is not cut to again within 30 s (`SPK_COOL`), and at least `gMinHold` must have passed since the last cut.
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

### 6.2 Inside or outdoors (`context()`, once per place; v4.4.0 design)
**Principle:** judge a build by its **floor**. Floors always have physics, because people walk on them. Walls, ceilings, windows and decor are often built without physics, and `llCastRay` only sees physics. The v4.0–4.3 design counted walls (a roof and 6, later 5, of 8 walls) and failed in exactly those builds, and in big halls whose walls are more than 60 m away.

**Second Life's ray result:** `[key, position]` per hit, then the hit count (negative = refused). The land reports `NULL_KEY`. There is one hit per object. 4.3.1 read 3 entries per hit, so every skybox looked like "land below". `tools/sim/indoor_sim.py` now models this exact layout.

1. **Under you** (essential; if refused, retry later): one ray from you, 100 m down, up to 4 hits.
   - The first hit is your floor (`gFloorZ`).
   - `gPrimFloor` = that hit is a build, not the land.
   - `gSky` = none of the hits is the land.
2. **Over you:** 5 rays, 40 m, from `floor + 1.8`: straight up and 25° off in four directions. `gRoofs` is the number that hit, and the ceiling is the lowest hit. A refused ray counts as no information.
3. **Around you:** 8 rays at eye height (`floor + 1.6`), 60 m → `gWallD`. A refused ray counts as a wall at 4 m.
4. **Floor outline:** in each of the 8 directions, `floorOK()` is probed at 1.5, 3, 5, 8, 12 and 20 m, stopping at a wall or at the first gap. A refused probe is skipped. The result is `gFloorD`.
5. **Decision** (v4.4.1):
   - Auto: `gPrimFloor && (gSky || gRoofs >= 3 || (gRoofs >= 1 && nHit >= 5))`. A build floor in the sky, or on the ground under a roof. A plaza with no roof stays outdoors.
   - Inside: always `TRUE`, an override. If nothing is detectable, the camera stays near you. `floorOK()` then accepts the land as your floor, because the land *is* your floor.
   - Outside, and Lite: `FALSE`.
   - **Sticky (not for Outside):** if the raw answer is "outdoors", but you were inside a moment ago, you are still on a build floor or under a roof (or 5 or more walls hit), and you are within 30 m of `gLocalAt` (where it last confirmed), you stay inside. This stops flipping near a door or where one ray misses. START clears the memory.
6. **Limits:**
   - `gCapZ` = ceiling − 0.4, kept between floor + 1.6 and floor + 6. With no roof seen it is floor + 3.4.
   - `gDmax` = 12 m, or 20 m if 5 or more directions are open for 25 m or more.
7. **Caching:** cached only when at most 3 rays were refused. Otherwise this cut uses the data, and the next cut measures again.
8. **Trace line** (only with Chat text on): `scenery: inside, the camera stays on your floor (floor a build, in the sky, roof 3/5, walls 8/8, up to 4 m high, 12 m away)`, or `outdoors (...)` with the reason.

### 6.3 Inside shots (`localShot`, `safeShot`)
- **`floorOK(c)`:** a ray from `c` down to `floor − 1` must hit a build (not the land) between `floor − 1` and `floor + 1.5`. Furniture is fine, and another storey is not.
- **`edge(i)`** = min(`gWallD[i]` − 0.8, `gFloorD[i]` − 0.5). A camera between directions i and i+1 uses the smaller of the two edges, capped at `gDmax`.
- **Candidates:** up to 8 per cut, 45° apart from a random start (± 0.2 rad). It stops after 3 good ones, or after 6 refused rays. Each candidate:
  - a novelty of 0.3 or more (relaxed pass: any);
  - **high** (40 %): at `gCapZ − 0.2`, 60–100 % of the edge away, looking down 12–35° at your area (needs `gCapZ ≥ floor + 2.2`);
  - **you small** (25 %, edge ≥ 5 m): 75–100 % of the edge away, at floor + 1.8–2.4, looking at you;
  - otherwise **eye level**: at floor + 1.5–1.9, looking back across your area ± 40°.
- **Checks, in order:**
  1. A clear line from your eye to the camera, plus 0.6 m beyond it (no hit before the camera distance + 0.5).
  2. `floorOK(c)` and `floorOK(c + 0.6 m outward)`.
  3. Head room: 0.5 m clear above (skipped in the relaxed pass).
  4. A view clear for min(camera distance + 1, 6) m. For "you small", it must reach you.
- **Score:** 2 × clear/30 + 2 × novelty + 1 if the kind changed + rand(0.5).
- **Order:** the normal pass, then the relaxed pass (≤ 6 m, eye level, no head-room check), then **`safeShot`**. That one goes behind you, behind-left or behind-right, whichever is most open, 0.8–2.2 m away, at eye height, looking where you look. A refused ray counts as no room.
- **Inside it never falls back to an outdoor view.** If even the floor probe is refused, the scenery script retries twice (0.7 s apart), then sends NO_SHOT. Core's basic shot then checks for a roof (one ray; refused counts as roof) and uses the close portrait view, not the high outdoor one.
- **Shot types:** 10 high, 11 eye level, 12 you small, 13 close.
- **Measured in `indoor_sim.py`:** 17 places, plus 16 standing spots × 4 facings per inside place. The result is no bad camera, and close fallbacks at 0–10 % in ordinary rooms (100 % in a 4 × 4 m room; 43 % when a quarter of all rays are refused).

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

### 6.5 Reach learning (4.4.5)
- **Core check, 2.5 s after a scenery cut** (types 5, 6, 7). `gCamBefore` is `llGetCameraPos()` just before the cut. A REACH_FAIL `"<asked>|<allowed>"` is sent only when the camera:
  - is more than 3 m from the spot asked for;
  - **moved** more than 1 m since before the cut (a minimised, frozen or slow viewer reports the old spot);
  - is 15 m or more from you and closer than 0.9 × the asked distance;
  - lies on the line from you to the spot (cos > 0.99, about 8°). A viewer limit pulls the camera straight in; orbiting, Alt-cam and mouselook put it anywhere else, which the peek check handles.
- **Scenery:** one REACH_FAIL only cuts again. A second within 10 cuts whose allowed distance agrees within 10 % (a real limit stops at the same distance every time) sets `gReach` = 0.9 × that distance (at least 20 m, never higher than before).
- **While learned** (`gReach` < `gReachSet`), a candidate further than `gReach` in a straight line (height included) is rejected.
- **Regrowth:** after 20 cuts in a row without a REACH_FAIL (`cin.reach_ok`), `gReach` grows by 10 %, up to `gReachSet`.
- **`tools/sim/reach_sim.py`** ports all of this plus the settings migration and runs 600 cuts × 8 seeds per viewer: unlimited, stale, slow, mouselook, Alt-cam, camera lifted off the land, orbiting 20 % / 50 % (reach must stay 100 m), and limits of 90 / 64 / 48 / 32 m with and without orbiting (must settle near the limit, ≤ 6 % short views afterwards). It also runs the 4.4.4 logic and asserts it collapses to 20 m, the reported bug.

## 7. People (`cinema_people.lsl`): chat cuts in Social
- On START `social` with `chat_cuts` on: `gChat = llListen(0, "", NULL_KEY, "")`. Remove it on STOP and on a switch.
- `listen`:
  - Ignore non-agents (`llGetAgentSize(id) == ZERO_VECTOR`) and the owner (the owner arrives as SPEAKER).
  - The speaker must be within `R_GRP` (8 m), and not the same speaker within 30 s.
  - Set `gSpeaker = id` and `gPendEvent = "speaker"`.
- **SPEAKER (owner):** `gSpeaker = owner` and `gPendEvent = "speaker"`.
- **In `nextShot`**, when the event is "speaker":
  - A speaker other than you: `gNPos` / `gNEye` = the speaker, `gRev = FALSE`, then `planA(TRUE)` → over your shoulder, facing them.
  - You: `gNPos` = the nearest other, `gRev = TRUE`, then `planA(TRUE)` → over their shoulder, facing you.
  - Nobody else near: a portrait of you.
  - The type is 4, and the hold is 8–12 s.
- The pending-event mechanism is unchanged, but its minimum is `gMinHold` (4.4.3), and Social holds a shot `gBase` = 0.75 × Pace (group × 1.2).

### 7.1 Framing people (4.4.6, both scripts)
`tools/sim/framing_sim.py` measured the 4.4.5 planning. **14.7 % of Social/Friends shots cut someone off, and 52 % left someone within 10 % of the screen edge.** It was worst in chat circles and small rooms. There were three causes:
- Social's group fit ignored depth.
- `sweep()` swung up to ±80° around a distance sized for the straight-on view.
- At a wall it moved the camera closer without re-fitting.

The fix:
- **`gMeas`:** who must be fully in the picture.
  - Group: everyone. Friends: you plus the friends used.
  - Pair or speaker: the person facing the camera. The over-the-shoulder foreground is left out on purpose.
  - Portrait: you.
- **`needAt(az)`:** the distance a camera on side `az` needs, for its real view direction (`viewDir`, including the rule-of-thirds turn). For each person, with `o` = offset from the focus point, `V` = view, `P` = its left, `u` = the side and `k = tanH / MARGIN`:
  - `need ≥ (o·P + BODY_R − k·o·V) / (k·(−u·V) + u·P)`;
  - and the same with `−o·P` and `−u·P`.
  - The result is at least `gVNeed` (the height of the shot).
- **`sweep()`:** each side gets `max(needAt(az), gPLo)`. A side is skipped if that is beyond `gPHi`, or if a wall is closer than it (`hit − STANDOFF`). It is never squeezed. Limits:
  - pair 2.5–6.5 m;
  - group 4–12 m;
  - Friends 3–25 m;
  - portrait 2.5–3.5 m.
- **`MARGIN` 1.3** (was 1.15). The fit assumes a window no wider than 16:10 (`tanH = tanV × min(aspect, 1.6)`). The outermost body then ends at least about 12 % of the screen width from the edge on 16:10, and about 16 % on 16:9. The rule-of-thirds turn still uses your real aspect.
- **Drift:**
  - **Social:** `framed()` checks everyone who should be in (group: all; pair: the facing person) against 80 % of the half-width on each scan. Anyone outside it means a re-frame at the next calm cut (`gMinHold`).
  - **Friends:** pulls back (§5).
- **Result in the sim:** 0 % cut and 0 % under a 10 % margin over 15,000 shots. Some group shots in 6 × 6 m rooms fall back:
  - Social to a pair;
  - Friends to fewer friends.

## 8. Building and textures
- **Icon (v4.2.0: one sprite sheet with every look):**
  - The source is `tools/art/make_icon.py`, with the pixel grids as strings.
  - `hud/art/take12_icon_sheet_512x256.png`: 4 columns × 2 rows of 128×128 frames, each holding a 16×16 sprite ×7 with an 8 px clear margin.
  - **Frame k** is at column `k % 4`, row `k / 4` (row 0 is the top). **Look n** uses frame `2n` (open) and `2n + 1` (clapped). Looks: 0 classic, 1 rec (default), 2 viewfinder. Frames 6 and 7 are spare for a fourth look.
  - **How the UI script shows frame k** (`frame()` in `cinema_ui.lsl`): repeats `<0.25, 0.5>`, offset `<(k % 4 + 0.5) / 4 − 0.5, +0.25 for the top row, −0.25 for the bottom row>`, on the face `cin.face` (default −1 = all faces; `/77 face <n>` picks one).
  - **Settings:** `look` (0–2, default 1) and `face` (default −1). Options › 🎨 Look changes the look and the emoji (the fade is gone in 4.7).
  - Single-look, two-frame sheets are in `hud/art/variants/`, for anyone who wants only one look.
  - **Upload settings:** no lossless needed; the alpha must be kept.
  - **On the prim:** put the sheet on the face that points at you on the HUD, and a fully transparent texture on the other faces. The script sets the repeats and offset itself.
- **Prim:** one box, size `<0.01, 0.04, 0.04>`, which is about 40 px on a 1080 px screen. Attach it to **HUD Top Right** and drag it into place.

## 9. Checks and sims
| Tool | Covers |
|---|---|
| `tools/lslcheck.sh` | Compiles `hud/src/*.lsl` and `legacy/v3/src/*.lsl` and estimates memory (Lite is paused) |
| `tools/sim/scenery_sim.py` | Outdoor finder (v3), unchanged |
| `tools/sim/people_geometry.py` | Composition, unchanged |
| **`tools/sim/framing_sim.py`** | §7.1: ports the people/friends planning (old and new) and measures every person's margin to the screen edge over pairs, lines, circles, clusters, open space, 10 × 8 and 6 × 6 rooms, 16:9 and 16:10. It asserts that nobody is cut and that at most 1 % of shots are under a 10 % margin; the old planning must show the problem |
| **`tools/sim/reach_sim.py`** | §6.5 reach learning against 16 simulated viewers, plus the settings migration |
| **`tools/sim/indoor_sim.py`** (replaces room_sim.py) | A line-by-line port of §6.2–6.3. Its `llCastRay` returns Second Life's layout (`[key, position]` per hit, then the count; the land is `NULL_KEY`; one hit per object; physics only; can refuse rays). It runs 17 places: skyboxes (plain, no-physics ceiling, glass walls, floor-only physics, furnished, two-storey, L-shaped, tiny), a 120 m mall with 64 shops, an open sky deck, a busy region refusing 25 % of rays, a ground house and a trailer (Auto and Inside), and an open field. Then a stress run: 4 standing spots × 4 facings per inside place. It asserts the classification, every camera inside the interior and not in a solid part, never an outdoor view while inside, close fallbacks ≤ 15 % in ordinary rooms, and that the old 3-per-hit stride bug is still detected |
| **`tools/sim/friends_sim.py`** | Port of the §5 loop. Targets walk on scripted paths. Assert: a glide when the centroid moves more than 0.4 m with everyone in frame; a snap within 2 ticks when someone leaves; the fit distance ≤ 25 m; no glide through a wall box |
| **`tools/sim/tap_test.py`** | The §4.1 decoder sequences |

CI (`.github/workflows/lsl-check.yml`) runs all of them.
