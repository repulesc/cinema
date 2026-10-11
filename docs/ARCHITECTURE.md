# Cinema HUD — Architecture & Build Spec (Second Life / LSL Mono)

## Context
The user wants a minimalist Second Life HUD that turns their viewer into an autonomous "static tableau" cinema camera (Ozu / Jarmusch / Nouvelle Vague grammar). One tap toggles it, and it also engages by itself when the user goes AFK. While it runs, it **cuts** between locked, composed vantage points and never glides. A Gemini-written brief set the vision. This document is the architecture and algorithm spec that Sonnet will implement in one pass. The HUD will be **given away or sold**, so v1 must be distribution-ready.

**Status:** architecture approved. Next step: Sonnet implements all scripts in one delivery, following §6. Quiz answers are in [`DECISIONS.md`](DECISIONS.md).

---

## 0. Reality checks on the Gemini brief (verified against the SL wiki)
| Brief says | Reality in SL | Design response |
|---|---|---|
| "Chat focus" bails out | LSL can't see where UI focus is | Poll `llGetAgentInfo(owner) & AGENT_TYPING`. It follows the viewer's start/stop-typing messages. |
| Input via `llTakeControls` | Controls see movement keys only, not mouse orbit or Alt-cam | Camera poll via `llGetCameraPos` (TRACK_CAMERA). Alt-cam = **peek**, not bail (§4.2) |
| Alt-cam / ESC | Free camera / Alt-orbit **silently overrides** scripted params. ESC *reverts to* the scripted camera. Scripted camera doesn't work in mouselook | Peek: pause cutting while the camera deviates, resume when it returns. Mouselook pauses and resumes the cinema |
| One 64 KB budget | 64 KB is **per script**, and permissions are **per script** | 3 scripts. The script that bails out also holds CONTROL_CAMERA + TAKE_CONTROLS → "Core" |
| Scripts keep running everywhere | `llTakeControls` keeps scripts running in no-script parcels **only for scripts in the same prim** | All scripts live in the **root prim** |
| Ghost inputs | A ghost FWD+BACK `control()` event fires after teleport | Ignore `control()` for 2 s after `CHANGED_TELEPORT` |
| Vista = GPU cooldown | A far camera looking *back* at the sim can show *more* geometry and makes objects stream in around the new camera | Vista splits into **Long shot** and **Pillow shot** (sky, sea, horizon, no avatars). Only the pillow shot is the cooldown shot |
| Floor height via ground | `llGround` is terrain only, so it's useless in skyboxes and buildings | Floor = a downward ray. `llGround`/`llWater` are only guards against the camera going below terrain or water |
| Sensor sees "the user" | Attachments can't detect their wearer. Results are capped at 32, sorted nearest-first, same region only | Owner via `llGetObjectDetails(owner,[OBJECT_POS,OBJECT_ROT])`. Others via one-shot `llSensor`, keeping the 12 nearest |
| Horizon lock via `focus.z = pos.z` | Correct, but a level camera at eye height centres the head and leaves an empty top half | **Compose vertically by camera HEIGHT, never by tilt** (§2.4) |
| FOV-based framing | Scripts can *read* FOV (`llGetCameraFOV`, TRACK_CAMERA) but not set it. Aspect ratio is unknown | Read FOV at engage (default 1.047 rad), treat it as vertical (setting), aspect 16:9 (setting) |

**Unknowns the wiki doesn't settle.** Code has to handle both outcomes, because there is no milestone in which to test them first:
- (a) Lag 0 might glide instead of cutting. Setting `cin.cutmode`: `0` = set params directly, `1` = `llClearCameraParams()` then set in the same event.
- (b) We don't know whether `llClearCameraParams` snaps back or eases back. Nothing to handle; just record it.
- (c) `llGetCameraPos` might not follow Alt-orbit. Then peek simply never triggers, which is harmless.
- (d) The maximum distance between a locked camera and the avatar is unknown. Setting `cin.maxcam` defaults to 45 m and clamps every shot.
- (e) The FOV axis is unknown. Setting `cin.fovaxis`.
- (f) ESC behaviour. Covered by peek.

The debug menu has a **Probe** item that runs (a), (c) and (d) as scripted tests and prints the results, so the user can fill in CALIBRATION.md.

---

## 1. System overview
```
 HUD linkset (v1 = a single prim: the BUTTON. All 3 scripts live in it.)
 ┌───────────────────────────────────────────────────────────────────┐
 │ cinema_core.lsl  ◄──── link msgs ────►  cinema_director.lsl       │
 │  perms, controls, AFK timer, state      scene scan, survey rays,  │
 │  machine, touch (tap / long-press),     composition math, ray     │
 │  camera apply / CLEAR, peek, button     scoring, editing grammar  │
 │  look                                                             │
 │        ▲                                                          │
 │        └──── link msgs ────►  cinema_ui.lsl                       │
 │                               dialog menus, llLinksetData config, │
 │                               first-run, help, debug/probe, ver   │
 └───────────────────────────────────────────────────────────────────┘
 Phase 2 (optional, separate project, can be shelved): screen-overlay prims:
 FADE (dip-to-black) + BAR_TOP/BAR_BOT (letterbox), all switchable off.
```
**Rule:** Core never waits on anyone to stop. Bail-out stays inside Core: an integer compare, then `llClearCameraParams()` as the first statement. Director is the "brains" and may be slow. Core keeps the previous shot on screen until a new one arrives, so there are no gaps and no flashes of the default camera.

**Transitions in v1:** hard cuts everywhere. The chosen "dip-to-black for far cuts" needs the FADE prim, so it ships with Phase 2. Director already sets a `fade` flag on each SHOT (TRUE for C1 long shots and any cut longer than 20 m). Core ignores the flag until a FADE prim exists, which it finds by prim name at startup.

---

## 2. Vector mathematics & framing formulas

### 2.1 Notation & primitives
- `P0`: owner position (centre of the avatar's bounding box). `F0`: owner facing, `norm(flat(llRot2Fwd(rot)))`.
- `flat(v) = <v.x, v.y, 0>`. `yaw(v, a) = v * llEuler2Rot(<0,0,a>)`. `UP = <0,0,1>`.
- `V`: view direction, a horizontal unit vector from camera to subject. Right vector `R = <V.y, −V.x, 0>`.
- Eye height: `eyeZ(i) = Pi.z + K_EYE·size.z`.
  - `K_EYE_STAND ≈ 0.37`, `K_EYE_SIT ≈ 0.25`.
  - `size = llGetAgentSize(k)`.
  - Sitting comes from `llGetAgentInfo(k) & AGENT_SITTING`, which works on other avatars in the region.
- Floor `Zf` = the hit of a 10 m down ray from `P0`.
- Lens: `VFOV = llGetCameraFOV()`, `ASPECT = 1.778`.
  - `tanV = tan(VFOV/2) ≈ 0.577`.
  - `tanH = tanV·ASPECT ≈ 1.026`.

### 2.2 Horizon lock (keystone suppression)
- Default: `focus.z = cam.z` exactly. Pitch is 0, so vertical lines stay parallel.
- Controlled down-angle `θ ∈ [5°,10°]`, used for seated subjects and ring-shaped groups: `focus.z = cam.z − d·tan θ`.
- Clamp `θ ≤ THETA_MAX` (10°, a setting). Only fallback F3 may go to 15°.
- Every shot is normalized before it is sent: `f.z = cam.z − d·tan(clamp(θ, 0, THETA_MAX))`.

### 2.3 Fit distance
```
halfW = max_i |(Pi − C)·R| + BODY_R            (BODY_R ≈ 0.35 m)
dW    = halfW / tanH
dH    = HALF_H / tanV                           (HALF_H: CU 0.6, MS 0.9, FULL 1.3)
d     = clamp( max(dW,dH) · MARGIN, DMIN_arch, DMAX_arch )      (MARGIN ≈ 1.15)
```

### 2.4 Vertical composition by camera height (the core trick)
To put the eye line on the upper-third line with a perfectly level camera:
```
(eyeZ − cam.z)/d = tanV/3   ⇒   cam.z = eyeZ − d·tanV/3
```
- At d = 3 m the camera drops about 0.58 m, to chest height. That is Ozu's low, level camera. Walls stay straight and headroom is right.
- For seated subjects the same formula gives tatami height.
- Guard: `cam.z ≥ Zf + 0.35`.

### 2.5 Horizontal composition (rule of thirds via yaw; yaw doesn't cause keystoning)
- Thirds offset: `α = atan(tanH/3)` (≈ 18.9°).
- Lead room: put the subject on the third opposite to where they face, with `side = sign(F_subject·R)`.
- Then `V' = yaw(V, side·α)` and `focus = cam + V'·d`, with z from §2.2.

### 2.6 Archetype A — Intimate (solo portrait / two-shot / three-shot)
`S` = owner + up to 2 nearest avatars within `R_INT = 4.5 m`. Weighted centroid `C = (W_OWN·P0 + ΣPi)/(W_OWN + k)`, with `W_OWN = 1.5`.
- **k = 0, solo portrait.**
  - Camera azimuth relative to owner facing, weighted by style: `φ ∈ {±135° 3/4 rear, ±45° 3/4 front, 180° Jarmusch back, 0° frontal symmetric}`.
  - `Dcam = yaw(F0, φ)`, `cam = C + Dcam·d`, `V = −Dcam`. Thirds per §2.5.
- **k ≥ 1, axis of action.**
  - Axis `A = norm(flat(P1 − P0))`, normal `N = <−A.y, A.x, 0>`.
  - 180° rule: keep side `s ∈ {±1}` for the whole scene.
  - Over the owner's shoulder: `Dcam = norm(N·s·cos γ − A·sin γ)`, γ ≈ 35°.
  - Reverse shot: use `A → −A` and keep the same `s`.
  - `d` per §2.3, MS framing, clamped to [2.5, 5].
- **k = 2:** mini-ensemble (§2.7), d clamped to [3, 6].
- Height per §2.4 using the mean eyeZ. If seated, θ = 5°.
- Others are framed freely, close two-shots included.
- **Speaker cut** is optional and OFF by default. When on, the subject role may move to the avatar who is typing.

### 2.7 Archetype B — Social ensemble tableau
1. Members: single-link cluster seeded with the owner, over avatars within `R_ENS = 10 m`. Link distance 3.5 m, cap 6.
2. Centroid `C` and the XY covariance `Sxx, Syy, Sxy`.
3. Principal axis: `θp = 0.5·llAtan2(2Sxy, Sxx−Syy)`, `L = <cos θp, sin θp, 0>`, `N = <−sin θp, cos θp, 0>`.
   - Eigenvalues: `λ1,2 = (Sxx+Syy)/2 ± sqrt(((Sxx−Syy)/2)² + Sxy²)`.
   - Anisotropy: `a = (λ1−λ2)/(λ1+λ2)`.
4. Row or line (`a > 0.35`): camera along `±N`. Pick the sign by facing score `Σ F_i·(±N)`, then by rays.
5. Ring or blob (`a ≤ 0.35`): take the azimuth from the sweep, scored by facing score and owner visibility. Raise the camera to `cam.z = meanEye + 0.4` with θ = 6°.
6. Owner occlusion is a pure-math penalty: another member nearer the camera and within 4° of the owner's bearing.
7. `d` per §2.3, FULL framing, clamped to [6, 10] (up to 14 if the fit demands and clearance allows).

### 2.8 Archetype C — Architectural vista
`Do` = the survey ray direction with the most clearance.
- **C1 Long shot (figure in landscape).**
  - `cam = P0 + Do·d`, with `d ∈ [25, min(45, cin.maxcam)]`, limited by `clear(Do) − 2`.
  - `cam.z = max(Zf + 1.6, ground + 1.6)`.
  - Level focus toward the owner, owner on a third.
  - Needs a line-of-sight ray. `fade = TRUE`.
- **C2a Rückenfigur.** Camera 3 m behind the owner, owner on a third, looking out along `Do`.
- **C2b Pillow shot (GPU cooldown).**
  - Camera 1 m beside the owner, at eye height + 0.3, looking along `Do`. Focus 60 m out. No avatars in frame.
  - Optional: horizon on the lower third with a pitch-up of `atan(tanV/3)` (≈ 10.9°). Pillow shots only.
- **Interiors:** C1 and C2 only if some survey ray reaches past 15 m (a "window shot"). Otherwise use A instead.

---

## 3. Raycast candidate selection pipeline (`llCastRay`)
**Ray parameters**
- `[RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]`, plus `RC_DETECT_PHANTOM, TRUE` only if `cin.phantom` is on (default OFF).
- Status is the last list element: `<0` error, `0` clear, `1` hit. Terrain is hit, with key `NULL_KEY`.

**Blind spots**
- A ray that starts inside a prim doesn't detect that prim.
- Prims with `PRIM_PHYSICS_SHAPE_NONE` are never hit.
- **Clamp both ray endpoints into [0.5, 255.5] in x and y.**

### 3.1 Survey
- **When:** on engage, after a teleport or region change, when the owner has moved more than 2 m, and every 6 cuts.
- **Rays (10 total)**, from `E = <P0.x, P0.y, eyeZ>`:
  - 8 horizontal rays, 45° apart, to 50 m.
  - An up ray to 40 m (`roofZ`).
  - A down ray to 10 m (`Zf`).
- **Openness:** `O = Σ min(clear_i, 50)/400`.
- **Environment class:**
  - INTERIOR: `roof < 12 && O < 0.25`.
  - SEMI: `roof < 12 || O < 0.5`.
  - Otherwise EXTERIOR.

### 3.2 Candidate sweep (per cut)
- Each archetype proposes an ideal `(φ*, d*, cam.z, θ)`.
- Make 7 candidates at `φ* + {0, ±25°, ±50°, ±80°}`.
- Cast a ray from the **focus point to each candidate camera**:
  - A hit at distance h gives `d_eff = h − 0.4`. A clear ray gives `d_eff = d*`.
  - A candidate is valid if `d_eff ≥ max(0.7·DMIN, 1.2)`.
  - Recompute `cam.z` for `d_eff`.

### 3.3 Score
```
S = 3.0·min(d_eff/d*,1) + 2.0·cos(φ−φ*) + 1.5·min(|φ−φ_last|/60°,1)
  + 1.0·[same 180° side] + 1.0·facingScore − 2.0·ownerOccluded
```

### 3.4 Verify (top 2 only)
1. Reverse ray from camera to focus. Ignore hits within 0.8 m of the focus (the subject's own sofa).
2. Ensemble: at most 2 line-of-sight rays to the farthest members. A blocked ray is a soft penalty.
3. Guards:
   - Region clamp.
   - `cam.z ≥ llGround(off) + 0.5` and `≥ llWater(off) + 0.2` (only near terrain).
   - INTERIOR: `cam.z ≤ roofZ − 0.3`.
   - `|cam − P0| ≤ cin.maxcam`.

Worst case is about 11 rays per cut.

### 3.5 Fallback ladder
- **F1 Shrink:** accept `d_eff ≥ 1.2` and step framing down FULL → MS → CU.
- **F2 Shoulder:** camera 0.9 m behind the owner's head and 0.25 m to the side, looking forward, level.
- **F3 High corner:** the survey direction with the most clearance, `d = min(clear − 0.4, 3)`, `cam.z = min(roofZ − 0.3, eyeZ + 1)`, θ ≤ 15°.
- **F4 Hold:** re-check the current shot with one ray and extend its hold.
- **F5 Release:** send `NO_SHOT`. Core goes back to the default camera and the button shows "no shot". Retry in 15 s.
- **Ray errors** (−2 / −3): keep the current shot and retry in 3 s. After 3 failures, go to F4.

---

## 4. State machine & control loop

### 4.1 Core states
```
        tap / AFK≥T            first SHOT                 hold expired / event
 IDLE ─────────────► ENGAGING ───────────► ROLLING ─────────────────────► CUTTING
  ▲ (armed if AFK on)   │ 5 s no shot       ▲  ▲      SHOT applied          │
  │                     ▼                   │  └──────────────────────────────┘
  │                   NOSHOT ── retry ──────┘
  │                                 ROLLING ⇄ PEEK  (camera deviates / returns)
  │                                 ROLLING ⇄ PAUSED (mouselook / teleport / region; resume after 3 s)
  └──── BAIL (per §4.2 policy) from any active state
```
`gSource ∈ {MANUAL, AFK}`. `gArch` = the archetype of the current shot.

### 4.2 Activity policy (decided in the quiz)
| Event | AFK-started session | MANUAL-started session |
|---|---|---|
| Movement keys | **Bail** (instant, first line of `control()`) | **A/B shots: keep rolling** (director mode, §4.5). **C shots:** setting `cin.man_vista_end`, default 0 = keep rolling |
| HUD tap | Bail | Bail (toggle off) |
| Typing (`AGENT_TYPING`, polled every 0.5 s) | **Bail** | **Bail** |
| Sit / stand change (`AGENT_SITTING`/`AGENT_ON_OBJECT` toggled) | **Bail** | **Bail** |
| Camera deviates > 0.3 m from the shot (Alt-cam/orbit) | **Peek:** freeze cutting and the hold timer; resume when the camera returns (ESC). Setting `cin.peek_bail` (default 0) turns this into a bail | same |
| Mouselook | Pause, resume on exit | same |
| Teleport / region change | Clear now, PAUSED, re-survey, resume | same |
| Detach | `llClearCameraParams()` (CONTROL_CAMERA is revoked anyway) | same |

Idle-side activity, which resets the AFK clock: control events, typing, and the camera moving while IDLE (orbiting counts as being present).

### 4.3 Timers (one per script)
- **Core IDLE:** 2 s tick. Fires the AFK trigger when `now − gLastAct ≥ cin.afk_sec`. The AFK option `"away"` triggers on the `AGENT_AWAY` flag instead.
- **Core active:** 0.5 s tick. Polls, runs the hold countdown and the peek check. Never uses `llSleep`.
- **Director, active only:**
  - Sensor rescan every 5 s: `llSensor("", NULL_KEY, AGENT, 20, PI)`, one-shot.
  - In MANUAL with movement: owner-only position check every 1 s through `llGetObjectDetails`.
  - All intervals double when `llGetRegionTimeDilation() < 0.8`.

### 4.4 Editing grammar (Director)
| Context | A Intimate/Portrait | B Ensemble | C1 Long | C2 Pillow/Rücken |
|---|---|---|---|---|
| solo, exterior | 15 | – | 30 | **55** |
| solo, interior | 45 | – | 0 (window only) | 55 (window/F2) |
| pair/trio | 55 | 20 | 10 | 15 |
| group ≥ 3 | 30 | 45 | 10 | 15 |
| **cooldown** (AFK ≥ `cin.cool_min`, 10 min) | ×0.5 | ×0.5 | ×0.7 | ×2.5 |

(Solo scenes favour landscape and pillow shots, as chosen.)

**Rules**
- The first shot of a scene is an establishing shot (B or C1).
- No archetype twice in a row, except A shot / reverse shot.
- A pillow shot every 4–6 cuts.
- A scene change (group membership changes, or the owner moves more than 3 m) means re-establish and pick a new 180° side.

**Holds**
- Base: A 20 s, B 25 s, C1 18 s, C2 8 s.
- ±20% jitter, × `cin.hold_mul` (0.5–3), × the style preset multiplier.
- `hold_mul = 0` means "hold until an event".

**Event cuts** (after `MIN_HOLD = 6 s`):
- The subject leaves the frame cone, `angle(V, owner − cam) > 0.85·HFOV/2`.
- Someone arrives within R_INT.
- Speaker cut, if enabled.

### 4.5 Director mode (MANUAL + movement)
- Core sends `DIR_MOVING` when a control event arrives in a MANUAL session.
- Director checks the owner every 1 s against the frame cone.
- When the owner leaves the frame or moves more than 4 m: an event cut with MIN_HOLD = 2 s, preferring A (portrait or two-shot).
- Still only cuts, never glides.
- If `cin.man_vista_end = 1` and the current shot is C: bail as if AFK.

### 4.6 Style presets (`cin.style`)
| Preset | Height | Azimuth weights (solo A) | Holds × | Pillow every | Extra |
|---|---|---|---|---|---|
| Blend (default) | §2.4 | mixed | 1.0 | 4–6 | — |
| Ozu | §2.4 − 0.25 m (low) | frontal 0°/180° heavy | 1.2 | 3–4 | axial cuts (same φ, d×0.6) |
| Jarmusch | §2.4 | 0°/180° symmetric, centred (no thirds yaw) | 1.6 | 6–8 | wider d ×1.2 |
| Nouvelle Vague | §2.4 | ±45°/±135° | 0.6 | 8+ | jump cuts (same φ, d×0.75, 30% chance) |

### 4.7 Applying a shot (Core)
```
if (cin.cutmode) llClearCameraParams();
llSetCameraParams([CAMERA_ACTIVE,TRUE, CAMERA_POSITION,p, CAMERA_FOCUS,f,
  CAMERA_POSITION_LOCKED,TRUE, CAMERA_FOCUS_LOCKED,TRUE,
  CAMERA_POSITION_LAG,0.0, CAMERA_FOCUS_LAG,0.0,
  CAMERA_POSITION_THRESHOLD,0.0, CAMERA_FOCUS_THRESHOLD,0.0]);
gShotPos = p;   // for peek detection
```

---

## 5. Resource & memory budget (Mono, 64 KB per script)
| Script | Target | `llSetMemoryLimit` | Notes |
|---|---|---|---|
| core | ≤ 18 KB | peak + 8 KB | no lists beyond the current shot |
| director | ≤ 46 KB | peak + 8 KB | if it goes over 50 KB, split out `cinema_composer.lsl` (pure math, called by link message) |
| ui | ≤ 20 KB | peak + 6 KB | dialog lists built on demand |

- Avatar list: `gAv = [key, vector pos, float yaw, float eyeZ, integer flags]`, stride 5, at most 12 entries, rebuilt once per scan.
- Survey: an 8-float list, plus `gRoofZ, gFloorZ, gOpen, gEnv`.
- Shot message: `"<p>|<f>|hold|arch|fade"`.
- Settings live in **`llLinksetData`**. They survive resets and cost no script memory. Scripts cache them in globals and refresh on the `linkset_data` event.
- No `llSensorRepeat`. A channel-0 listen only when speaker cut level 2 is on. Rays average under 1 per second.

---

## 6. Implementation spec for Sonnet (build all at once)

### 6.1 Repo layout
```
README.md                 what it is, how to build the HUD prim, install
docs/ARCHITECTURE.md      this spec
docs/DECISIONS.md         quiz answers
docs/CALIBRATION.md       constants + in-world probe results (to fill in)
docs/USER_GUIDE.md        becomes the in-world "Cinema HUD — Read Me" notecard
src/cinema_core.lsl
src/cinema_director.lsl
src/cinema_ui.lsl
CHANGELOG.md
```

### 6.2 Link-message protocol (`llMessageLinked(LINK_THIS, num, str, id)`)
| num | from → to | name | str |
|---|---|---|---|
| 7301 | core → dir | DIR_START | `afk` / `manual` |
| 7302 | core → dir | DIR_STOP | — |
| 7303 | core → dir | DIR_NEXT | `hold` / `invalid` / `retry` |
| 7304 | core → dir | DIR_PAUSE / 7305 DIR_RESUME | `ml` / `tp` / `region` / `peek` |
| 7306 | core → dir | DIR_MOVING | — (manual director mode) |
| 7307 | core → dir | DIR_COOLDOWN | `1` once AFK ≥ cool_min |
| 7310 | dir → core | SHOT | `"<p>|<f>|hold|arch|fade"` |
| 7311 | dir → core | NO_SHOT | retry seconds |
| 7312 | dir → core | EARLY_CUT / END_SESSION | reason |
| 7320 | core → ui | UI_STATE | `off` / `armed` / `rolling` / `peek` / `noshot` |
| 7321 | core → ui | UI_MENU | (long press) |
| 7330 | ui → all | CFG_CHANGED | LSD key |
| 7340 | any → ui | DEBUG | text (printed only when `cin.debug`) |
| 7350 | ui → core/dir | PROBE | `cut` / `campos` / `dist` |

### 6.3 Settings (`llLinksetData`, prefix `cin.`, defaults in brackets)
| Key | Default | Range / meaning |
|---|---|---|
| `afk_on` | 1 | 0 / 1 |
| `afk_sec` | 90 | 60, 90, 120, 180, 300, 600, or `away` |
| `style` | `blend` | `blend`, `ozu`, `jarmusch`, `nv` |
| `hold_mul` | 1.0 | 0 (hold until an event), 0.5–3 |
| `cool_min` | 10 | 0 = off |
| `speaker` | 0 | 0 = off, 1 = typing flag, 2 = typing + local-chat listen |
| `phantom` | 0 | |
| `man_vista_end` | 0 | |
| `peek_bail` | 0 | |
| `theta_max` | 10 | |
| `fovaxis` | `v` | |
| `aspect` | 1.778 | |
| `maxcam` | 45 | |
| `cutmode` | 0 | |
| `debug` | 0 | |
| `overlay` | 0 | Phase 2 |
| `ver` | — | |

**Distribution hardening**
- Write `cin.*` keys with `llLinksetDataWriteProtected` and a per-build pass constant, so other scripts that get into the linkset can't change them.
- On `CHANGED_OWNER`, wipe and reset to defaults, and show first-run.

### 6.4 UI (long-press menu, `llDialog` on a random negative channel, listener removed after 60 s)
**Button behaviour**
- Tap toggles the cinema.
- Long-press (`touch_end` with more than 1 s since `touch_start`) opens the menu.

**Main menu:** Style · AFK · Holds · Options · Help · About
- **AFK:** On/Off, 60 / 90 / 120 / 180 / 300 / 600 / "SL Away".
- **Holds:** ×0.5 / ×1 / ×1.5 / ×2 / ×3 / Until event.
- **Options:** Speaker cut (Off / Typing / Typing + chat), Phantom obstacles, Manual vista ends on move, Alt-cam ends cinema, Cooldown (Off / 5 / 10 / 20 min), Debug, Probe, Reset.
- **Help:** gives the Read Me notecard.

**Button look:** colour or glow per UI_STATE: off = dim grey, armed = soft white, rolling = red dot, peek = amber, noshot = blue.

**First run:** a one-time `llOwnerSay` welcome, plus the notecard offer.

**About:** the version string. Each script has a `VERSION` constant that it checks against the others at startup, and it warns on a mismatch.

### 6.5 Function prototypes
**core**
```
engage(integer src); bail(string why); pause(string why); resume();
applyShot(string packed); setUi(string st); integer camDeviates();
requestPerms();   // TAKE_CONTROLS|CONTROL_CAMERA|TRACK_CAMERA, auto-granted for attachments
```
**director**
```
vector flat(vector v); vector yaw(vector v, float a);
float  eyeZ(vector pos, vector size, integer sitting);
vector clampRegion(vector v);
list   ray(vector a, vector b);                       // [status, dist]
integer survey();                                     // gClear, gRoofZ, gFloorZ, gOpen, gEnv
float  fitDistance(list members, vector V, float halfH);
float  camHeightThirds(float eye, float d);           // §2.4
vector thirdsYaw(vector V, vector faceDir);           // §2.5
list   composeIntimate(); list composeEnsemble(); list composeVista(integer variant);
list   composeFallback(integer level);
list   sweep(vector focus, float phiIdeal, float dIdeal, float dMin, float camZ, float theta);
integer chooseArchetype(); float holdFor(integer arch);
integer inFrame(vector p);                            // frame-cone test (event cuts, director mode)
string packShot(vector p, vector f, float hold, integer arch, integer fade);
```
**ui**
```
menu(string page); cfgGet(string k); cfgSet(string k, string v); firstRun(); runProbe(string which); dbg(string s);
```

### 6.6 Build order inside the single delivery
Sonnet writes everything in one pass but in this order, and syntax-checks each file as it goes:
1. **core:** perms, controls, states, peek, the `cutmode` handling.
2. **ui:** LSD defaults, menus, protected writes, first-run, probe.
3. **director:**
   - Scan and survey.
   - A (with §2.4/§2.5).
   - The ray pipeline and fallbacks.
   - B, then C.
   - Grammar, styles, cooldown, director mode, speaker cut.
4. Docs: README (prim setup: one prim, HUD attach point Center or Bottom Right, drop in the 3 scripts and the notecard), USER_GUIDE, CHANGELOG.

### 6.7 Calibration constants (initial values, all collected in a top-of-file block per script)
`K_EYE_STAND 0.37, K_EYE_SIT 0.25, BODY_R 0.35, MARGIN 1.15, THETA_MAX 10°, STANDOFF 0.4, R_INT 4.5, R_ENS 10, LINK 3.5, W_OWN 1.5, MIN_HOLD 6, SURVEY_RANGE 50, VISTA 25–45, PEEK_TOL 0.3`

---

## 7. Verification
**Offline:** run each `.lsl` through `lslint` (or LSL-PyOptimizer) if it can be installed in the container. Otherwise do a careful manual review against the wiki signatures.

**In-world** (the user, with Debug on):
1. Probe menu → record (a) cut vs glide, (c) campos follows Alt-cam, (d) max distance in CALIBRATION.md, and adjust `cutmode` / `maxcam`.
2. Open field, solo: mostly pillow and long shots; portraits with straight walls, eyes on the upper third, correct lead room.
3. Small room with a ceiling: never behind a wall or above the roof; F2/F3 appear in debug.
4. Sofa with a friend: two-shot / over-the-shoulder, θ = 5°, no false hits on your own sofa.
5. Club crowd: ensemble ≤ 6 members, no script-time spikes (Top Scripts, `llGetSPMaxMemory`).
6. Skybox at 3000 m, region border, teleport: pause, then a clean resume.
7. Policy table §4.2: AFK + key = instant bail. Manual + walking = keeps cutting. Typing and sit/stand bail. Alt-cam = peek, ESC resumes.
8. After 10 min AFK: the pillow-shot share visibly rises.
9. Give a copy to an alt: first-run greeting, defaults reset, notecard delivered.

---

## 8. Decisions (quiz answers) → `docs/DECISIONS.md`
| # | Topic | Decision |
|---|---|---|
| 1 | AFK delay | 90 s default; submenu presets 60–600 s + "SL Away" |
| 2 | What ends cinema | Movement keys (AFK sessions), HUD tap, **typing**, **sit/stand**. Alt-cam = peek (option to bail). Mouselook = pause |
| 3 | Manual mode + movement | Social shots (A/B) keep rolling in "director mode". Vista: option, default keeps rolling |
| 4 | Transitions | Hard cut near, dip-to-black far. Dip-to-black ships with the Phase 2 overlay; v1 hard-cuts everywhere |
| 5 | Style | Blend default; Ozu / Jarmusch / Nouvelle Vague presets in the menu |
| 6 | Hold | 20–30 s varied by shot type, menu multiplier (incl. "until event") |
| 7 | Letterbox | Deferred to Phase 2 (optional, can be shelved), with an off switch. v1 = button only |
| 8 | Vertical composition | Thirds by camera height, level camera |
| 9 | Solo scenes | Mostly landscape and pillow shots |
| 10 | Speaker cut | Optional (menu): Off / typing flag / typing + chat listen; default Off |
| 11 | Other avatars | Framed freely, incl. close two-shots |
| 12 | GPU cooldown | After 10 min AFK, favour pillow shots |
| 13 | Phantom objects | Ignored by default, menu toggle |
| 14 | Settings UI | Long-press button → dialog menu, settings stored in Linkset Data |
| 15 | Build approach | All scripts in one delivery, with in-world probe tools for the unknowns |
| 16 | Audience | Give or sell: first-run, notecard, protected settings, owner-change reset, versioning |

---

## 9. Implementation notes (v1.0.0)
Where the shipped scripts differ from, or add to, the spec above. The scripts are the source of truth.

| # | Topic | What the code does |
|---|---|---|
| 1 | Thirds yaw sign (§2.5) | The spec text says `V' = yaw(V, side·α)`. That puts a subject who faces right on the right third, so they look out of the frame. The code uses `V' = yaw(V, −side·α)`: the subject sits on the third *opposite* to where they look (lead room). |
| 2 | Reverse shot (§2.6) | Shot / reverse shot alternate each time a pair scene is composed. The camera keeps the **same world side** of the axis (`N·s·cos γ ∓ A·sin γ`), so the 180° rule holds. The spec's "swap A → −A" would flip the side. |
| 3 | Link messages (§6.2) | `7312` is `END_SESSION` only (`EARLY_CUT` was dropped: the director simply sends a new `SHOT` early). `7340 DEBUG` is unused: each script prints its own debug lines when `cin.debug` is on. `7360 MSG_VER` was added (version announce / `"?"` request). `7350 PROBE` also carries `fov`. |
| 4 | FOV | Permissions are per script, so only core can call `llGetCameraFOV()`. It sends the value to the director inside `DIR_START` as `"afk|1.047"` / `"manual|1.047"`. |
| 5 | Settings | Added `peek` (1 = watch for Alt-cam, 0 = ignore). Menu: Options → Alt-cam → Peek / Ends cinema / Ignore. |
| 6 | Floor / water guards (§3.4) | A HUD's `llGetPos()` is not a world position, so `llGround()` is not used. Terrain/floor under a candidate camera comes from short down-rays; the region water height comes from `llWater(ZERO_VECTOR)` once per engage. |
| 7 | Speaker cut | Level 1 polls `AGENT_TYPING` once per second for the cached near avatars (not only at each 5 s scan). Level 2 additionally listens on channel 0 and only reacts to avatars already in the scan list. |
| 8 | Overlay (phase 2) | Not implemented. The director already sends the `fade` flag (long shots and cuts > 20 m); core ignores it. |
| 9 | Memory limit | `llSetMemoryLimit` is not called; the scripts run with the default 64 KB each. Measure `llGetFreeMemory()` in-world (Menu → About shows the UI script's value) and tighten later. |
| 10 | Pause behaviour | Mouselook and Alt-cam "peek" pause the director and the hold timer; on resume core re-applies the last shot. Teleport / region change clears the camera, pauses 3 s, then asks for a fresh establishing shot (new scan + survey). |
| 11 | Axial / jump cuts (§4.6) | Ozu (axial, d×0.6) and Nouvelle Vague (jump, d×0.75) re-use the previous solo angle with 30 % probability when the last shot was a solo portrait. |
| 12 | Ray budget | Survey 10 rays (on engage, teleport, > 2 m movement, every 6 cuts) + per cut: 7 sweep rays, up to 2 candidates × (reverse ray [+ floor ray] [+ 2 member rays for ensembles]) ≈ 11–15, plus fallbacks. Pillow shots use 2–4 rays. |
