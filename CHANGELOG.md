# Changelog

## 4.4.5
**Scenery reach 100 m by default, and it no longer shrinks for no reason.**
- The default reach is **100 m** (menu 50 / **100** / 150 / 200 m). Re-learn goes back to the reach you chose.
- **Why it could fall to 20 m:** the check after each cut counted any camera that was not where it was asked as "the viewer refused a far camera". A minimised or frozen viewer, mouselook, orbiting or Alt-cam all looked like that, and each one cut the reach by 20 %. Now a short camera counts only if it actually moved, straight out toward the planned spot, and stopped 15 m or more from you. One short view just cuts again. The reach is lowered only when it happens twice within 10 cuts at the same distance (within 10 %), which is what a real viewer limit does. It is then lowered to 90 % of that distance.
- **Settings bug:** the settings-version check compared text, so it ran again on every rez. Each time it forced Chat text off and copied the shortened reach into your chosen reach, so the shortening became permanent. It now runs each step once. On this update, every install moves to 100 m once (a chosen 50 or 200 m is kept), which also clears a reach that was shortened by mistake.
- While a shorter reach is learned, it counts the straight-line distance (height included).
- New `tools/sim/reach_sim.py` (in CI) runs the learning against 16 simulated viewers and checks the settings migration. The 4.4.4 logic drops to 20 m in the same test, matching the report.

## 4.4.4
**Scenery reaches further: 150 m by default** (it was 100 m).
- The reach menu is 50 / 100 / **150** / 200 m, and `/77 reach <m>` takes 20–250 m. The nearest scenery camera stays at 20 m, so a view is never a close-up of you.
- "Re-learn" now means: back to 150 m. (Some viewers refuse a script camera that is very far from you. The HUD notices, shortens its reach to 80 % of that distance and remembers it. Re-learn lets it try the far views again.)
- A fix: the reach grew back only up to a fixed 100 m after it had been shortened. Now what you chose (`reach_set`) and what the HUD is using (`reach`) are kept apart, and it grows back up to your choice.
- Installs that still had the old default of 100 m move to 150 m once. A reach you chose yourself is kept.
- The scenery simulation now also runs with a 150 m reach in all five test worlds.

## 4.4.3
**Much calmer people cameras.** Social and Friends (and Personal) cut far less often.
- They follow your **Pace** setting now. At Calm (60 s) a shot is held about 45 s (a group about 55 s), where it was 20–25 s. Faster Paces still hold a minimum of 20 s.
- An event (someone arrives, someone leaves the frame, a speaker) waits at least 15 s at Calm before it cuts, where it was 6 s.
- A speaker shot lasts about 18 s (was 10 s), and the same person is not cut to again within 30 s (was 10 s).
- The re-frame while you walk waits 4 s (was 2 s). Friends still snaps to a wider shot when someone is lost for about a second, because that one has to be fast.

## 4.4.2
**Quiet in chat.** The HUD no longer talks while you use it.
- Off by default: the startup lines, the line for every cut, and the confirmation after every menu choice. The menu itself shows the new value when it reopens.
- Still shown: errors and warnings (no permission, a script not answering, a version mismatch), the answers to commands you type, and one line when you save a spot.
- Options › 📝 Chat text turns the detailed lines back on (it is the old Trace setting, now off by default). With it on, each cut says what it found and why, which helps when you report a problem.
- Older installs are switched to quiet once. Friends › Clear and Remove are silent, because the picker shows the result.

## 4.4.1
**Indoors: consistent in a trailer, and a real override for places rays cannot see.**
- **Auto now also goes inside on a build on the ground when there is a roof over you** (house, shop, trailer, roofed mall). A plaza or deck with no roof stays outdoors. Before, ground builds always got outdoor views in Auto, and a measurement that differed from one moment to the next made the trailer flip between in and out.
- **No flipping:** once inside, it stays inside until you are clearly outdoors or 30 m away.
- **Indoors = Inside always stays inside**, even where the floor, walls and roof have no physics. It then works near you, with the land as your floor.
- The simulation gained a ground plaza, a ground mall without physics (Auto stays outdoors, Inside works), a trailer in Auto, a walk through a trailer's doorway, and the open-field override.

## 4.4.0
**Indoor mode reworked to be reliable** (it failed at Velour Mall and in skyboxes):
- **A bug:** 4.3.1 read Second Life's ray results with the wrong stride (3 entries per hit instead of 2), so every skybox looked like "land below" and Auto never went inside.
- **The design:** a build is now judged by the **floor under you**, which always has physics, instead of counting walls and a roof. Walls, ceilings and windows are often built without physics, and big halls have walls more than 60 m away.
  - Auto goes inside on any build in the sky.
  - Inside works on any build floor or under a roof.
- **Every inside camera** has a clear line from your eye, your floor under it, and stays within the outline of your floor and under the ceiling. That holds even where walls have no physics, and it keeps the camera on your storey.
- **Never outside while inside:** when no spot fits, it uses closer spots, then a close shot just behind you. The old design cut to an outdoor view whenever a room shot failed. Core's own fallback shot also stays inside under a roof.
- **Busy regions:** a refused ray drops only that spot, and the scenery script retries shortly. A place measured with many refused rays is measured again on the next cut, instead of caching a wrong answer.
- **New `tools/sim/indoor_sim.py`** (replaces `room_sim.py`): its `llCastRay` returns Second Life's exact list layout, sees physics only, and can refuse rays. It covers 17 places, from skyboxes with glass walls or no-physics ceilings, a 120 m mall with 64 shops and a two-storey skybox, to a busy region and a trailer, from 16 standing spots each. There were 0 bad cameras.

## 4.3.1
**Skybox rooms: Auto goes inside more reliably, and tells you why when it does not.**
- Auto needs a roof and 5 of 8 walls (it was 6), so a balcony or a doorway no longer sends the camera outside. Indoors = Inside needs only a roof and 3 walls, and no longer needs the sky.
- A sturdier "in the sky" test: a multi-hit ray under you instead of `llGround`, which is unreliable from an attached HUD. The simulation caught that a ray starting under the floor would put a house on the terrain "in the sky", so the test starts at you and treats the land or anything more than 2 m below your floor as not the sky.
- Rays that escape through a gap are no longer counted as walls, so they cannot skew the room's centre, size or corner views.
- The trace line now states the reason: roof yes or no, walls n/8, in the sky or something solid below, and what it needs to go inside.
- New room tests: a furnished skybox, a skybox open on one or two sides, a room 150 m up, the 60 m limit, and the Inside and Outside overrides.

## 4.3.0
**Take 12 Lite**, a lower-priced entry (about L$99; the full version about L$299). Same code: `hud-lite/src` is generated from `hud/src` by `tools/build_lite.py` (CI checks it is up to date).
- Lite has the scenery camera (outdoor views), AFK start, the gestures, Pace, Photo hold and the classic look. Personal, Social, Friends, skybox rooms, favourites, look choice and chat cuts are full-version only, shown as locked buttons that open the listing (`BUY_URL` in `cinema_ui.lsl`).
- Lite ships only three scripts (core, ui, scenery) and has no chat listener at all.
- New: Lite notecard, Lite listing text and Lite ad boards (a LITE ribbon, Room and Friends dimmed as full-version features) in `hud-lite/`.
- Fixes found on the way: the memory estimator in `tools/lslcheck.sh` chopped a line that had `//` inside a string (it now reads strings and comments in one pass), and the longest chat strings in the UI script were shortened for headroom (15.6 KB free).

## 4.2.0
**Pick the look of the button from the menu** (Options > Look: Classic, Rec, Viewfinder).
- One texture now holds every look: `hud/art/take12_icon_sheet_512x256.png` (4 x 2 frames). The script shows the right frame, so nothing else needs to be in the HUD. Re-upload and set it on the picture face; the repeats and offset are set by the script.
- New setting `face` (`/77 face <n>`) when the picture should only go on one face of the prim. Other faces keep their own (for example fully transparent) texture.
- Fade and Emoji moved into the Look page. Options still has 11 buttons.

## 4.1.0
**The product is now called Take 12** (brand 12, Marketplace title "Take 12 - Cinematic Camera HUD").
- The clapper icon shows "12" on its slate, in three looks: classic (white), rec (red light) and viewfinder (cyan). Re-upload `hud/art/cinema_icon_256x128.png` to get it.
- Names in chat lines, menus and the welcome dialog changed from Cinema to Take 12.
- The Read Me notecard is `Take 12 - Read Me`, and the HUD now also accepts any notecard in its prim whose name contains "Read Me".
- End-user Read Me notecard (`hud/notecard/read_me.txt`), Marketplace listing text, and ad boards (`hud/marketing/`) with all three clapper looks.

## 4.0.1
- The button no longer fades so hard: 40 % visible by default (it was 15 % and got lost). Options › 🔆 Fade cycles 20 / 40 / 70 %.
- Friends › ➖ Remove lists all saved friends (here or not) and removes just the one you tap.
- Clapper texture: clear margin, no halo, no black edge lines or white fringes.

## 4.0.0
**New look and controls**
- Tap opens the menu, double-tap starts Scenery, long press opens the live menu. While rolling, tap stops and double-tap skips to the next view.
- Emoji dialog menus with a status line (Options › Emoji switches to text only). The Hold setting is now called Pace, with named steps.
- The button is a pixel-art clapper that claps once and then fades to 15 %. All colour feedback is gone.
- First run shows a short welcome dialog.

**New features**
- **Friends mode**: pick up to 10 friends from the people nearby. The camera glides to keep the group framed, and cuts to a wider shot if someone is out of frame for about 1 s.
- **Room-aware Scenery**: in a skybox or another enclosed sky build, the camera stays inside the room (corner wides, room-centre views, you small in the room). On the ground it still looks from outside, above the roof. Options › Indoors can force either.
- **Photo hold**, **Favourite spots** (saved per region, mixed into Scenery) and **chat cuts** in Social and Friends. Typing no longer ends Social or Friends.

**Fixes**
- Reach regrows by 10 % after 20 clean cuts, and can be re-learned from the menu.
- The version warning no longer says "four scripts".
- The dialog listener times out after 60 s.

**Under the hood**
- Six scripts: `cinema_core`, `cinema_ui`, `cinema_scenery`, `cinema_people`, `cinema_friends`, `cinema_picker`. Each has at least 15 KB free (estimated).
- New link messages: GLIDE 7312, SPEAKER 7315, FAV 7316, UI_FRIENDS 7322. UI_STATE now carries `state|mode|nextCut`.
- New sims in CI: `tap_test.py`, `room_sim.py`, `friends_sim.py`. The friends sim found and fixed a fit bug (people nearer the camera than the group's centre fell out of frame).
- v3.0.0 is frozen unchanged in `legacy/v3/`.

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
