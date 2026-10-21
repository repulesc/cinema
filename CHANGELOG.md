# Changelog

## 5.1.1
**Fix: Follow my lead did not show "Got it", or did not keep the view.**
- **Too insensitive:** Take 12 only noticed your own camera once it was more than 1 m from the shot. In Friends it now also notices a move of 0.3 m, or a turn of the view of about 10°, so a small orbit toward your faces counts.
- **Friends undid your view:** after your view was taken, Friends kept checking "is everyone inside the frame?" against its own old camera. With a close view it decided people were out of frame and cut to a wider shot. While you lead, that check, the pull-back and the drift glide are off; your friends are followed at the next cut instead.
- "Your view is kept · Esc to continue" shows for 3 s above the button (a notice, nothing to click), only when your view really changed. The first time after each rez, one chat line explains Esc and Auto.
- **Check that all eight scripts are in the HUD.** `cinema_lens` is new since 5.0, and without it nothing is kept.
- Follow my lead works in Friends only, for now.

## 5.1.0
**Follow my lead: frame it yourself with Second Life's own camera, and Take 12 keeps it.** 5.0's keys (gears, angle keys, A/D round, Tune) were too much to learn, and they fought the camera everyone already knows. They are gone.
- In Friends, frame the view the usual way: Alt-orbit, the mouse wheel, or A/D while seated. When the camera has been still for about 1.5 s, "Got it" shows, and your view becomes the shot. Press **Esc** and it carries on from there.
- From then on, every cut and double-tap variation keeps **how close, how high and where you aimed** (your faces, which a script cannot see when you sit or lie down). They are kept relative to the group, so when your friends shift, the camera follows them.
- **Seated, W/S** step about 20 % closer or wider; they do not move a seated avatar.
- **Back to automatic:** long press › **Auto**. It also happens by itself when you sit down or stand up, or when a friend comes or goes.
- Standing, the movement keys just walk, as before 5.0.
- Other modes keep the Alt-cam setting (pause, end, ignore) as before.
- `tools/sim/lens_sim.py` now checks the whole chain: 400 orbited views come back exactly as the next planned shot, follow a moving group, and scale with W/S.

## 5.0.0
**Friends: you choose how close, from what angle, and where the faces are.** Sitting or lying together, Friends was still too far away, because a script cannot see where a seated or lying body really is: an avatar on a bed reports the same position it would standing, and only the animation lays it down.
- **Closeness gears:** Auto (the mix of 4.9, the default) → Wide → Group → Half → Close → Faces. Seated or lying, **W/S** step closer or wider; standing, **E/C** do (W A S D still walk). From Auto, closer goes to Close and wider to Group; wider past Wide is Auto again. A gear stays until you change it; double-tap still cuts to another angle in the same gear. Faces brings the camera to about 1 m from a couple side by side.
- **Angle (seated or lying):** **E/C** step through 60°, 45°, 30°, 15° and level. It starts from Options › Seated view. **A/D** turn round the group.
- **Tune:** long press › **Tune**, then W/S/A/D move the aim across the screen and E/C up or down, until the faces are where you want them; long press › Tune again when done. The aim is saved at once for that seat (the object, and where on it you sit, so each side or pose of a bed has its own), and comes back by itself the next time you sit there. Long press › Clear tune forgets it.
- What changed shows for 3 seconds, then the screen is clean.
- **New script `cinema_lens.lsl`** (eight scripts now): replace all of them.
- Friends memory: the unused friend-names list and two diagnostic counters are gone, so Friends stays where it was (13.2 KB by the stricter estimate).
- New `tools/sim/lens_sim.py` in CI: each gear is closer than the one before, nobody is cut at any gear, Faces is closer than Frame's nearest, the Tune aim comes back exactly however the bed is turned.
- Social and Personal get the same keys once this is right in-world.
- To check in-world: standing in Friends, E/C must change the gear without making you jump or crouch (two control requests: W A S D passed on, E/C kept).

## 4.9.2
**Fix: seated and lying shots were far too far away; close views now reach pairs and lying people.** A screenshot of two people lying on a bed showed the whole bed.
- **Cause 1:** the raised seated camera was placed as if it were level. At 45° the real distance to the people is about 40 % longer than the distance the framing had worked out, so every seated shot came out too far. The camera now stands so that its true distance, along the line of sight, is what the framing needs: seated shots are about 30 % closer, wide ones included. A low ceiling is accounted for.
- **Cause 2:** the close view only applied to groups of three or more. A pair (you and one person, over the shoulder in Social) never got it. Now it does.
- **Lying down:** an avatar lying on a bed is about 1.8 m long, not the 0.7 m width the framing assumes, and a head can be 0.8 m from where the avatar is. A close view of seated people therefore keeps a wider body allowance, so the faces stay in the picture. While you are seated it is chosen more often (about every other cut).
- Friends is tight on memory again (13.2 KB by the stricter estimate): please send `/77 status` if anything misbehaves.

## 4.9.1
**The close views are now intimate: heads and shoulders, much closer.** 4.9.0's close view (about 2 m, down to the thighs) was still too far for people sitting together.
- A close view now frames **heads and shoulders**, with faces large. The camera comes in to about **1.7 m** for a tight group (under 2 m across; 2.2 m on average over all compact groups, against 3.3 m for the wide views), and it stays clear of the screen edges as before.
- Bodies are cropped on purpose; only faces and heads must stay in. A little extra headroom keeps the head of a neighbour who is 0.3 m taller in the picture in 99 % of the simulated cases.
- Same rhythm as before: about one cut in three, never two close views in a row, only when everyone stands within 3.5 m of each other.

## 4.9.0
**Close views for people who stand close together.** The group shots in Social and Friends were always the wide, environmental kind, with the camera at least 3-4 m away even for two friends side by side.
- When everyone in the shot stands within about **3.5 m** of each other, now and then (about one cut in three, never two in a row) the camera comes in for a **close, half-length view**: roughly 2 m away instead of 3-4 m, the faces larger. In the simulations the camera comes out about 30 % closer on average (2.3 m against 3.3 m), and for a tight pair about half.
- The wide views stay exactly as they were, and are still the usual choice. Spread-out groups always get the wide view.
- The same fitting as before keeps everyone clear of the screen edges (at least 10 % margin in all tests). In a small room a close view needs less space, so it fits more often.
- No new setting. "Next" (double-tap) can land on either kind.

## 4.8.1
**Fix: "Stack-Heap Collision" in the UI script when you pressed the HUD (4.8.0 only).**
- Cause: the UI script was already close to its memory limit, and the new Seated view entries tipped it over. The memory estimate had missed that every element of a constant list is its own object: the menu table and the defaults held about 250 of them.
- Fix: the menu table and the defaults are now single strings, and a menu choice is matched only against the buttons on screen instead of the whole table. Same menus, same behaviour, much less memory.
- `tools/lslcheck.sh` now counts list elements in its memory estimate.
- Replace all seven scripts (the version is now 4.8.1). `/77 status` shows each script's free memory.

## 4.8.0
**Seated view: when you sit or lie down, the camera looks down on you.** Meant for a beach blanket, a bed, a sofa with friends.
- **Automatic** in Social, Personal and Friends: while you are seated (anything you sit on, including a pose bed), the camera rises and looks down at about **45 degrees**, with the same fitting of everyone as before, so people no longer hide behind each other. Indoors the ceiling caps the rise (under about 10 degrees it stays level). Scenery and Frame are unchanged.
- **Adjustable:** Options › **Seated view**: Auto (45°), Higher (60°), Lower (30°) or Off. Stored as `seat_deg`.
- **Sitting or standing up** brings a calm re-frame at the next quiet moment (no sooner than the usual minimum hold), never an abrupt jump.
- A script can tell seated from standing but not sitting upright from lying down (a pose bed uses its own animation), so one elevated view serves both.
- New `tools/sim/seated_sim.py` in CI.

## 4.7.1
**Fix: "next" (double-tap, or Next in the live menu) did nothing visible in Social, Personal and Friends.** Only Scenery changed the view. Three causes, all fixed:
- **Group shots never varied.** Social's group shot and Friends' shot are planned from where people stand, so "next" planned exactly the same camera again (the framing test showed it: 300 of 300 repeated). Now a shot asked for with "next" must come from a spot at least 1.5 m from the camera on screen, and it still frames everyone.
- **Tight spaces fell back to one fixed shot.** Since 4.4.6 a side with too little room is skipped (so nobody is cut), and in a trailer or small room every side could be skipped, leaving the same "behind your head" shot each time. Now there is first a closer, half-length view of you, and the last-resort shot alternates shoulders.
- **"Next" was swallowed during a peek pause.** When the HUD thought you were moving the camera yourself, it paused the mode and ignored "next". Now "next" ends the pause and cuts.

## 4.7.0
**Idle start that also respects the mouse, and a clearer button.**
- **Idle start:** after **3 minutes** (new default; 1 min, 90 s, 2, 5 and 10 min stay) with no keys, no typing and no camera moves, **and**, with the new **Mouse check** (on by default), only once your viewer reports you Away. A script cannot see the mouse, but the viewer clears its Away status on any mouse movement, so mouse-only use (menus, inventory, the web) no longer counts as idle. Set the viewer's own Away timer short, or turn the mouse check off if your viewer never sets you Away. The old "SL Away" choice and the old 90 s default move to 3 min + mouse check once.
- **Once the scenery camera runs** nothing changes: moving the mouse does not end it; a movement key, typing or a tap does.
- **The button no longer fades or changes.** It is the plain logo at full strength, idle or rolling: the screen already shows that the camera runs, and the old fade only made the small icon hard to find. The clap on start is gone too. Options › Look › Fade is gone.

## Ad boards (marketing only, no script change)
- **New wording on all six boards:** "Your idle time, framed." (the calm tone of the old line, without "film", which suggested recording) and "Double-tap to start. Any key brings you back." (in place of "walk away"). The footer line is unchanged.
- The 4:3 board now has the second line and the footer as well, with its views a little smaller to make room.
- Frame is deliberately not on the boards: they sell the automatic camera. Lite's boards stay frozen with Lite (`--lite` rebuilds them).

## 4.6.0
**Frame replaces Photographer, much slimmer.** Take 12 stays the calm, automatic camera; Frame is a small extra for when you want a picture of yourself.
- **Frame** (main menu, or `/77 frame`) holds a well-composed view of you, or of you and whoever stands right next to you (chosen automatically). Three framings: **Full length, Half length, Close**. Double-tap for the next one.
- The movement keys adjust it (closer or further, round, up or down) while you stand still. Tap to leave. The camera never moves by itself.
- **No settings on screen:** the framing's name shows for 3 seconds, then the screen is clean. The zoom is followed silently.
- **Gone from the shipped mode:** the person picker, landscapes, photo shapes, the lens line and Photographer's own menus. The full 4.5.0 version is kept, not shipped, in `lab/frame-full-4.5.0/` as the start of a possible later composition tool.
- The script is now `cinema_frame.lsl` (still seven scripts in all; remove `cinema_photo` if you added it). It is about half the size.
- **Product principles** are written down in `docs/PRODUCT.md`: it decides and you accept or skip; calm; no settings on screen; one button; restraint.
- New `tools/sim/frame_sim.py` in CI.

## 4.5.0
**New: Photographer**, a fifth camera for taking your own pictures. It places the camera by classic photo rules and holds it: no cuts, and it never moves by itself.
- **Subjects:** you, a person you pick (within 20 m), the group around you (within 8 m), or the landscape where you face.
- **Five framings, A to E.** Double-tap for the next one. For a person: Environment (35 mm), Full length (50 mm), Three-quarter (50 mm), Half body (85 mm), Head and shoulders (85 mm). Groups and landscapes have their own five.
- **Framed for each avatar's height,** worked out every time. Mixed-height groups never cut the tallest head and keep side room. Someone sitting gets seated framings.
- **The lens is your viewer zoom.** The camera distance follows your field of view, so the picture stays the same size and only the perspective changes. A line next to the button shows each framing's lens and whether yours matches, e.g. `C · Three-quarter · 50 mm (now 21) Ctrl+0`. The camera never goes closer than 1.2 m; with too wide a lens it frames a little looser and says so.
- **Fine-tune with the movement keys:** W/S closer or further, A/D round the subject, E/C higher or lower with the framing kept. Your avatar stands still meanwhile. Tap to leave.
- **Photo shapes:** 16:9, 4:3 (also the Second Life profile picture shape) and 3:2.
- **Obstacles:** a blocked spot is tried 15° and 30° to either side, then from the other side; the status line says when.
- New script `cinema_photo.lsl`. The HUD now has **seven** scripts; re-drop them all. Core forwards the keys and lens changes; the UI has a menu entry, a long press while it runs, and `/77 photographer`.
- `tools/sim/photographer_sim.py` checks the framing maths over avatar heights 1.55–2.35 m, lenses 21–105 mm and the three shapes. It also checks that the script's preset tables match the tested ones.
- **To be tuned in-world:** the body proportions (where the eyes, chest and belt are, as a fraction of the avatar height) and the framings themselves. See "Calibration" in `docs/PHOTOGRAPHER.md`.

## 4.4.6
**People stay clear of the screen edges in Social and Friends.** The report was right. A new test, `tools/sim/framing_sim.py`, measures where every person lands on screen. With 4.4.5, 15 % of group and pair shots cut someone off, and half of them left someone right at the edge. Chat circles and small rooms were the worst.
- **The shot is now sized for the side it is taken from.** The camera tries several sides around the group. Each side now gets the distance it needs so that everyone fits, counting that people nearer the camera look wider. Before, the distance was worked out for the straight-on view only, and Social ignored depth altogether.
- **A wall closer than that distance means that side is skipped.** It used to push the camera in closer, which cut people off.
- **More breathing room:** the outermost person now ends at least about 12 % of the screen width from the edge (16 % on a 16:9 window). Before it was about 7 %.
- **Friends glides back gently** when someone wanders toward the edge, with no cut. It still cuts wider if someone is lost or there is a wall behind the camera. If walls leave no room for the whole group, it frames fewer friends (nearest first) instead of falling back to a shot of you alone.
- **Social** now also notices when someone other than you drifts to the edge, and re-frames at the next calm moment.
- In the test: 0 % cut and 0 % at the edge, over 15,000 planned shots. The over-the-shoulder shot still puts the near person's shoulder at the edge; that is the composition.

**Clearer texts.** The Marketplace listing, the Read Me intro and the README now say plainly what happens: your camera leaves your avatar's back and goes, by itself, where a camera operator would put it. Words like "film" and "walk away" are gone, because they made it sound like the HUD records video. The old texts are kept in `hud/marketing/legacy/`.

**Lite is paused,** frozen at 4.4.5 until the full version leaves beta. It is no longer built or checked in CI. `hud-lite/README.md` lists how to resume it.

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
