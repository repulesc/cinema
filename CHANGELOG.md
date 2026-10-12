# Changelog

## 4.0.0: planned (spec ready, build in progress)
- **Repo:** v3.0.0 is frozen in `legacy/v3/`, the old v1/v2 material is in `legacy/v1-v2/`, and v4 lives in `hud/`. CI checks both.
- **Spec from the round-3 quiz:**
  - Gestures: tap = menu, double-tap = Scenery, long press = live menu. While rolling, tap stops and double-tap skips.
  - Menus: emoji SL dialogs.
  - Button: pixel-art clapper, no colours, fades to 15 % while rolling.
  - Friends mode: glide and snap.
  - Room-aware Scenery: skyboxes stay inside.
  - Photo hold, Favourite spots, and chat cuts in Social and Friends. Typing no longer ends Social or Friends.
- **Docs:** `docs/PRODUCT.md`, `docs/ARCHITECTURE.md` and `docs/ROADMAP.md` rewritten for v4.
- **Art:** `tools/art/make_icon.py` generates `hud/art/cinema_icon_256x128.png` (variants classic, rec and viewfinder).

## 3.0.0 - the scenery camera (rebuilt from scratch around the real idea)
- **The default is now the scenery camera**, which earlier versions never had. On AFK or a tap, the camera finds clear, grand views of the place: drone views 10–30 m up and wide eye-level views, 20–100 m away. It ignores people, stays inside the region, sits above the topmost surface at its spot (outside and above the roof when you are indoors), checks the view with rays, varies direction and height, holds each view about 60 s (adjustable), and hard-cuts.
- **Personal** (follows you as you walk) and **Social** (pairs and groups) are optional modes from the long-press menu or `/77`. AFK never starts them. Movement keys don't end them.
- **Reach learning:** if the viewer refuses a far camera, core reports it and the scenery script lowers and saves its reach.
- Scripts: `cinema_core`, `cinema_scenery` (new), `cinema_people` (new, from the v2 director), `cinema_ui`. The old director is archived.
- New docs: `docs/PRODUCT.md` (spec from the round-2 quiz), `docs/ROADMAP.md`, a rewritten `docs/ARCHITECTURE.md`. The old docs are in `docs/archive/`.
- Checks: LSL-PyOptimizer compile check plus two Python simulations, run in GitHub Actions.

## 2.0.0 - it always shoots; compiler-checked
- Every script is now compile-checked with LSL-PyOptimizer (`tools/lslcheck.sh`, also run by GitHub Actions on every push). Earlier versions were never compiled before pasting.
- Finding: the 1.1.0 director compiles clean, so its silence in-world was not a syntax error. Most likely it was flagged "not running" after the old compile error, or failed at load; both are invisible in local chat.
- Core now has a built-in basic composer (level portrait orbit, wall-checked) and a director watchdog: if the director has not answered within 1.5 s, or says it has nothing, core cuts to a basic shot. The blue "no shot" state is gone - a tap always moves the camera.
- The director acknowledges every start (`DIR_ACK`, 7313) and prints "ready" on load; `/77 status` shows whether it answered.
- Director v2: people within 8 m (up to 5) + 10-ray survey of the space; portrait, over-the-shoulder pair, **group tableau** (new), empty view; people-first after a scene change; one trace line per cut.
- Removed the calibration probes from core (kept `/77 grab` / Options > Test camera) to free memory. Estimated free memory: core 27 KB, director 16 KB, ui 29 KB.

## 1.1.0 - lean director (fits in one script)
- **Why:** the 1.0.x director (~1,500 lines) did not fit the 64 KB Mono limit, so it never ran. Measured: core ~47 KB used at ~650 lines.
- New `cinema_director.lsl` (about 470 statements, est. 18 KB free): portrait, over-the-shoulder pair, pillow shot, shoulder fallback, 7-candidate raycast sweep, event cuts, director mode. It prints "ready, free memory N" when it starts.
- The full director is kept as `src/future/cinema_director_full.lsl` for a later multi-script split (groups, long shots, speaker cut, style presets).
- Chat commands moved from channel 9 (clashed with another HUD) to **77**, configurable with `chan <n>`. Menu items for removed features (Style, Speaker) are gone.

## 1.0.2 - find out why the camera is not grabbed
- `/9 grab`: takes the camera for 4 s without the director, prints permission bits and whether the viewer followed.
- Progress messages (`/9 trace on|off`, default on): started, scan, survey, shot type tried, shot received, and a camera check that compares where the view really is with where it was asked to be.
- A loud message if the director does not answer within 5 s.

## 1.0.1 - first in-world test fixes
- Long-press opens the menu while the button is still held (`touch` event), not only on release.
- Chat commands on channel 9 (`/9 menu|start|stop|status|debug|far|maxcam|probe|reset`) so the HUD can be driven and diagnosed even if the menu does not open.
- `/9 status`: every script prints one line (state, permissions, memory).
- Director always prints first shot, ray errors and "no usable shot" (no longer hidden behind debug).
- Long shots (25-45 m) are opt-in (`/9 far on`) until the distance probe has been run.
- Test build defaults `debug` to on for fresh installs.

## 1.0.0 - first complete version
- `cinema_core.lsl`: permissions, controls, AFK detection (timer or SL "Away"), state machine
  (idle / engaging / rolling / paused / peek / no-shot / probe), instant bail-out on movement keys,
  HUD tap, typing and sit/stand; Alt-cam "peek"; mouselook + teleport pause/resume; in-world probes.
- `cinema_director.lsl`: scene scan, 10-ray environment survey, composition maths (thirds by camera
  height, level horizon, lead room), three archetypes (intimate, ensemble, vista incl. pillow shots),
  7-candidate raycast sweep with verification and a fallback ladder, editing grammar with four style
  presets, cooldown mode, optional speaker cut, director mode for manual sessions.
- `cinema_ui.lsl`: long-press dialog menu, protected Linkset Data settings, button states, first-run
  welcome + notecard, owner-change reset, script version check.
- Not included yet (phase 2): letterbox bars and dip-to-black overlay.
