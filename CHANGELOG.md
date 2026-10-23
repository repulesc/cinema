# Changelog

## 7.0.1 (the boards and the listings)
**The ads as minimal as the product.** The old boards were a maximalist collage: four views, chips, stamps, three clapper looks and three lines of type in one picture.
- **One frame per board:** a single quiet picture fills it (Take 12: a dusk horizon; Take 12 Scenery: the drone view; the Watch: friends at dusk), golden-line ticks barely visible at its edges, the clapper in a corner, the name and one line: "A camera for Second Life." / "Free. The place, while you are away." / "Free. See your friend's camera." Every ratio and the vendor boards (bigger type) are the same frame (`tools/art/make_adboard.py`, rewritten).
- **The listings are short:** the full Take 12's Full description is a third of what it was (one short paragraph per door), and the free Scenery's and the Watch's too.
- `listing_check` follows: the 7.0 names, nothing the product no longer has (Photo hold, Still, Only friends, Go live), short descriptions, each board's line in its listing.
- No script changes (still 7.0.0).

## 7.0.0
**One product.** The menu was a phone menu from the 2000s: about 25 entries on 6 pages, features that overlapped, and "Frame" meaning two things. 7.0 keeps what works and folds it into six doors.
- **The menu:** Framing · Freehand · Connect / Scenery · Format · Settings / Help · Close.
- **Framing** is Me · Us · Friends, with one rule everywhere: **it follows you as you walk, and holds a composed picture when you stand.**
  - **Me** is Still's composer with walking: the movement keys walk you, the camera travels with you, and a second after you stop it composes the picture again in front of you (Full / Half / Close by double-tap or the keys). The old Me and Still are this one camera now; Still's nudges are gone (Freehand is the manual camera, Fit the height of your body).
  - **Us** (everyone near) and **Friends** (the friends you picked; was Only friends) hold each group shot and change with the Pace, and to whoever speaks.
- **Scenery** is the standby camera: it still starts by itself when you are idle, and a double-tap starts it; it sits lower in the menu, with its own settings under it (Start, Idle start, Indoors, Reach).
- **Format** is the picture's shape (it was called Frame).
- **Settings:** Pace, Look (button, status line, Size, chat text), Camera (seated view, Alt-cam, chat cuts, phantom), Test cam, Reset.
- **Gone:** Photo hold (Framing and Freehand hold the camera; in the free Take 12 Scenery too), the three menu styles (one quiet style: a mark and a word), Scenery's saved favourite spots (Freehand keeps its saved views), the Timing page.
- **The Read Me** is rewritten short: one section per door (266 lines became 115); the free one too.
- **Scripts:** `ui` (the menus, 15.3 KB free, was 13.0), `core` (no Photo, the keys pass in Framing › Me, `/77 me` = Framing › Me), `frame` (walking), `scenery` (no favourites), `tips` (Me / Us / Friends; a tip when you connect), `picker`, `connect`, `crop` (one style).
- **Checks:** `menu_sim` rewritten for the six doors; `frame_sim` (walking, no nudges), `tips_sim`, `free_test`, `free_sim`, `fit_sim`, `seated_sim`, `sync_sim`, `crop_sim` follow.
- **Version 7.0.0** in all fifteen scripts (the Watch stays 6.8.0). Next: the ads and the listing, as minimal as the product.

## 6.8.0
**Connect: connect first, then whoever films leads.** Sharing is re-thought: you connect with the people near you, and once connected, everyone sees the camera of whoever films.
- **Connect** (hold the button, or tap › Connect): + name connects you with one person, + Everyone with all of them, ⇄ Join name joins someone already connected. Friends on the Take 12 Watch, or with you in their Friends list, connect at once; anyone else sees "… wants to connect · double-tap: yes". **Connecting starts no camera.**
- **Whoever films leads.** Start any camera and everyone connected sees it ("⇄ You film · Ana, Ben see it"). While you watch, starting a camera is **My turn**: the lead comes to you, and everyone (the one who filmed before too) sees yours. Two at once: the last one to start leads. When nobody films, everyone has their own camera and stays connected ("⇄ Connected · nobody films · double-tap: film").
- **A movement key while watching** no longer disconnects you: it gives you your own camera for a moment, and the shared view is back after 4 s still.
- **Disconnect** (Hold › Disconnect, or the key) is the only way out: you leave and the others stay. The one holding the connection hands it to another Take 12 (no camera starts for them); with only Watches left, it asks first.
- **Simpler panels** (`share.lsl` is now **`connect.lsl`**: delete `share` from the HUD): no Go live, End live, roster, Pass camera or lead requests (Ask / Always / Never). Holding it: Film / Next, + Invite, Disconnect. Watching: My turn, Next, Disconnect.
- **Keys:** holding it NEXT · INVITE · DISCONNECT; watching NEXT · MY TURN · DISCONNECT (the HOLD key is gone, like Photo from the menu). **Re-upload `hud/art/take12_keys_512x1024.png`** as `take12_keys`: the atlas has new rows.
- **The Watch (6.8.0)** speaks the same way: "⇄ Pano films", a tap disconnects, a movement key gives your camera for a moment, nobody filming gives your own camera.
- **Fix found by the sim:** when the lead changed twice within a second, someone joining the one in between was told "disconnected"; now they are pointed to whoever films (`director|…`).
- **Words:** Share, Go live and End live became Connect and Disconnect everywhere: the menus, the Read Me (CONNECT), `docs/CONNECT.md` (was SHARING.md), the listings and the boards (regenerated). `/77 connect` opens the panel.
- **Checks:** `sync_sim` plays the new flow in a small region: connect without a camera, at once / asked, my turn, two at once, nobody filming, your camera for a moment, every Disconnect, an older hub, heartbeats, toggles; `keys_sim`, `listing_check`, `free_test` follow.
- **Version 6.8.0** in all fifteen scripts and the Watch.

## 6.7.1
**Fit the right way up, faster; a bigger button; a missing script says so.**
- **Fit:** Page Up now raises the camera and Page Down lowers it (6.7.0 moved you up in the picture, which read as the camera going down). A tap is 5 cm (was 2). Hold for more: it starts at 10 cm/s, for precision, and speeds up to 50 cm/s after about 2 s; up to 1.5 m either way. Shift + Page Up can't be done: Second Life doesn't tell scripts about Shift, so the hold is the big move. Your 6.7.0 fits start over (they had the other sign).
- **Size:** Options › Look › Size: Small, Medium or Large (the button 0.04, 0.06 or 0.08; `/77 size s|m|l`). The keys grow with it and are now 1.2 times the button's height, so their labels read. A HUD that never chose is set to **Medium**, half again as big as before. (`keys` does it; Take 12 Scenery has no Size.)
- **A missing script says so.** Every script answers ui's version check; one that stays silent is named once in chat: "Missing or stopped: share …". Share doing nothing at all was most likely this: since 6.2 its panel is drawn by `share`, and without it nothing showed. (`tips`; Take 12 Scenery checks its own four.)
- **Checks:** `fit_sim` (the new steps and sign), `keys_sim` (the three sizes, the keys beside the button at each), `tips_sim` (every script is on the missing list and answers with its own name).
- **Version 6.7.1** in all fifteen scripts.
- **Next (6.8):** sharing becomes **Connect**.

## 6.7.0
**Fit: Page Up / Page Down move you in the picture.** A seated pose can put your body anywhere from the point Second Life reports (a deep sofa, a bar stool, a ground sit, heels), and no script can see it. Now you show it once, by eye.
- **The keys:** while Me, Us, Only friends or Still runs, Page Up moves you up in the picture and Page Down down (E / C too). A tap is 2 cm; held, 25 cm/s; up to 1.2 m either way. The camera glides at once, and every next shot is framed with it (the eye line, the camera height and its angle all follow). "Fit +12 cm · this seat" shows for a few seconds.
- **Never a jump:** while a people camera runs, these two keys are kept from your avatar; when you fly, they fly. Stopping the camera gives them back.
- **Kept where it belongs:** per seat (the object and where on it you sit, to half a metre, so each side of a sofa or a bed has its own; the last 20 seats), one for sitting on the ground, one for standing. One key pair and no mode: 5.0's Tune per seat needed a mode and more keys, and 5.1 took it out.
- **Still:** E / C no longer move the camera up and down: they are Fit, which re-frames Full, Half and Close with your real height. W / S, A / D and Shift + A / D stay.
- **The tip:** seated in any people camera, "Sitting · Page Up / Down move you in the picture"; Still's tip names the keys too.
- **New script `fit.lsl`** (fifteen in all): core hands it the keys (FITKEY 7396) and moves the shot (FIT 7397, through one `glide()`, adding the move to that camera's later glides until its next shot); people and friends add `cin.fitz` to your eyes, frame to your feet. friends keeps its memory (the two eye lines are one).
- **Checks:** new `fit_sim` (a tap, a hold and the limit; Page Up moves you up, the same on screen and in the next shot; core takes the keys only for a people camera and never flying; the other keys still nudge or walk; 20 seats, the ground and standing kept apart; the tip). `lens_sim` follows.
- **Version 6.7.0** in all fifteen scripts.
- **Next (6.8):** Me and Still become one Me.

## 6.6.0
**The composition, like a photographer's.**
- **The golden lines.** Me, Us and Still put the eyes on the golden line, 38.2 % from the top of the picture (it was the third, 33 %), and you on a golden line across, 38.2 % from one side, with the open space on the side you look to (lead room, as before). Seated looks down at you the same way.
- **Air in a full-length picture.** Still's Full length leaves 10 % above the head and 8 % below the feet (it was 7 % and 6 %), for you alone and for a group.
- **Composed inside the Frame format.** With a Frame set, the cameras compose inside it: you stand on a golden line of the 4:5 picture, never in the dimmed part, and a group is fitted to the format's width (a 2.39:1 picture is shorter, and fitted to that too). Without a Frame, nothing changes. Still re-frames at once when you change the format; Me and Us from their next shot. In the sims, people planned for the window and seen in 4:5 were cut in 242 of 598 shots; now in none.
- **The lens hint names the key:** "○ Me · auto · 21 mm · try 35 · Ctrl+0" (Ctrl+8 when your lens is longer than the camera likes).
- **No Photo in the menu.** Tap › Photo is gone from the live menu: Still and Freehand hold the camera for your pictures. Resume shows only while the shot is held (the HOLD key while live, `/77 photo`). Take 12 Scenery keeps Photo, its only way to hold a view.
- **The keys strip is found** however it was linked. A strip linked before it was named was taken by Frame as one of its bars (and renamed), so the keys never showed. Now Frame takes its own four boxes first and never a box named "… keys"; `keys` takes the box named "keys" (any case), or the fifth box Frame leaves, and names it `Take 12 keys`. An HUD where Frame already took the strip mends itself. `/77 status` shows "[Take 12/keys] … strip link N".
- **Scripts:** `people`, `friends`, `frame` (Still) read `cin.crop`; `crop` sends `CFG_CHANGED "crop"`; `tips` the key hint; `ui` the menu; `keys` and `crop` the strip. `friends` keeps its memory (two clamps and a return merged).
- **Checks:** `framing_sim` composes inside 4:5, 1:1, 3:2 and 2.39:1 on 16:9 and 16:10 windows (nobody cut, nobody under a 5 % margin, the golden lines exact); `frame_sim` checks 10 % / 8 % air and the golden eyes at every height and lens, and Still's lines inside a 2.39:1 picture; `keys_sim` ports both strip scans over six ways of linking; `seated_sim`, `lens_sim`, `zoom_sim`, `tips_sim`, `menu_sim`, `free_test` follow.
- **Version 6.6.0** in all fourteen scripts (the Watch is unchanged).

## 6.5.0 fix: Frame's bars behind the button
- In-world, the dark Frame bars sat in front of the clapper and caught its clicks. HUD space's +X points into the screen, so the bars now sit 0.02 m behind the button (`crop.lsl`, `gSX = 1`; it was −1). `/77 crop back` still flips it if a viewer differs.
- Only `crop` changes (still 6.5.0): replace that one script.

## 6.5.0
**The keys, and a live view that never ends by accident.**
- **Soft keys.** In a few busy moments a short row of quiet keys appears beside the button, and only then:
  - Live, as the director: NEXT · HOLD · INVITE · END (HOLD freezes the shot for everyone, END asks first);
  - watching someone: NEXT · ASK · LEAVE;
  - Freehand: SAVE · VIEW A · VIEW B · STOP (the view in use underlined);
  - Still: FULL · HALF · CLOSE (the framing in use underlined).
  Thin line icons in chalk on near-black keys, a coral underline the only accent. Everything else stays in the menus.
- **One prim.** The keys are one strip prim (`Take 12 keys`) showing a row of one texture (`hud/art/take12_keys_512x1024.png`, made by `tools/art/make_keys.py`); where you click on it says which key. New script `keys.lsl` (fourteen in all). Without the strip, nothing changes: the menus do it all.
- **Live pauses, it does not end.** Your camera stopping while you are live (Stop, a movement key in Scenery, typing) used to end the live view for everyone. Now it pauses it: viewers keep your last shot, held, and see "· paused"; you see "● LIVE · paused · double-tap: carry on". Start a camera again and they follow again. The `pause` message is new; older viewers just keep the last shot.
- **End live asks first:** "End the live view for 3 people?" End live / Keep, from the Share panel and from the END key.
- **Frame's bars** are now any four children but the keys strip (they were links 2–5).
- **The Watch (6.5.0)** shows "· paused" too.
- **Checks:** `keys_sim` (every row's window exact on the atlas, touches map to keys, every key's action answered by its script, the strip beside the button; a camera stop pauses and never ends live, End live asks, both viewers show the pause); `crop_sim` follows.
- **Version 6.5.0** in all fourteen scripts and the Watch.

## 6.4.0
**Freehand: you frame it, Take 12 holds it.** For photographers, of people or of objects.
- **Tap › Freehand.** Frame with Second Life's own camera (Alt-click to aim, Ctrl+Alt-drag to orbit, the wheel, Ctrl+0 / Ctrl+8 for the lens, Frame for the format). Hold the view still for a second and it is held: "✥ Freehand · held · 85 mm" above the button, and a clap.
- **A tripod.** Esc and walking no longer move it: walk into your picture, pose, take the snapshot. Move the camera to frame again ("framing · hold still", with your lens); Esc brings back the view last held. Stop is in the live menu.
- **The lens, as everywhere.** The held view is aimed at what sits in the middle of the frame (a ray from the camera), so a zoom dollies the camera along its line by k = tan(old/2) / tan(new/2): the subject keeps its size and only the perspective changes, stopping 0.3 m short of a wall. Phantom objects are seen through.
- **Saved views:** Tap › Save keeps the held view, two per region (View A, View B; a third replaces the oldest). A double-tap goes from one to the other; with none saved, it holds the view on screen at once.
- **Sharing:** viewers follow a hand-framed shot like any other.
- **New script `free.lsl`** (thirteen in all). Core: Freehand reuses Only friends' "Follow my lead" lock (1 s instead of 1.5, focus by ray), no exit on movement keys or typing. Take 12 Scenery has no Freehand.
- **Checks:** `free_sim` (the dolly keeps an object's size over 36 lens pairs, the wall stop, saving and recalling, the wiring in core, ui and tips); `lens_sim`, `tips_sim`, `menu_sim`, `sync_sim`, `crop_sim` and `free_test` follow.
- **Version 6.4.0** in all thirteen scripts.

## 6.3.0
**One meaning per gesture.** From in-world testing: a tap meant three things (menu, stop, carry on), and while a camera ran the menu hid behind Hold › ⋯ More.
- **Tap: always a menu.** Idle: the menu. A camera running, or Photo: the live menu (Resume first in Photo). Stopping is any movement key, or Stop in the live menu.
- **Double-tap: go / next,** as before: idle, Scenery; running or in Photo, the next view.
- **Hold: a shortcut to the Share panel.** Share is now in the live menu too, so nobody has to know the hold. When the hold has taken (0.8 s), the clapper claps, so you know you can let go.
- **Texts:** the welcome, the help line, the tips ("tap: menu", "tap › Resume", "Tap while it rolls"), the Release hint, both Read Mes and both listings.
- **Take 12 Scenery:** the same map (its hold opens the menu, as a tap does).
- **Checks:** `sync_sim` checks that a tap never stops the camera, Share is in both menus and the hold claps; `free_test` and `tips_sim` follow.
- **Version 6.3.0** in all twelve scripts.

## 6.2.0
**Frame: the picture format on your screen.** The first step of the composition work.
- **Tap › Frame**, then 3:2, 4:5, 1:1, 4:3, 2.39:1 or 9:16: the screen outside the picture is dimmed (black at 60 %), like a camera's viewfinder. The picture is centred and as large as the window allows. Off takes it away.
- **Exact on any window.** It reads your window with `llGetCameraAspect()` and follows a resize within 2 s. HUD space is 1.0 tall and as wide as the window; the bars are placed from the screen centre whatever HUD point the button is worn on.
- **Never in a snapshot:** viewers leave HUDs out. The Read Me says how to take the photo in the same ratio.
- **The cameras get your real window.** `cin.aspect` is now measured (it assumed 16:9), so Me, Us and Only friends fit people for your screen. They also receive the format (CROP 7390), for composing inside the frame in the next step.
- **New scripts `crop.lsl` and `share.lsl`** (twelve in all) and **four boxes** linked to the HUD (build step 3). Clicking a bar does nothing (ui ignores touches on links 2–5). `/77 crop <format|off|flip|back>`; flip and back are fallbacks if a viewer places HUDs differently.
- **Take 12 Scenery** has no Frame (no `crop.lsl`; the button is taken out by the build).
- **Fix: "Stack-Heap Collision" in sync when you hold the button.** sync, the largest script, ran out of memory building the Share panel. Its panels move to a new script, **`share.lsl`**: sync keeps the sharing itself (the protocol, the roster, the camera) and sends share what a panel needs (SHARE_UI 7392); share draws it and sends the choice back (SHARE_DO 7393). Give Watch is all in share. sync goes from about 13.7 to 21.7 KB free by the estimate (which was too hopeful for it), share has 33.6 KB. Nothing changes in how sharing looks or works.
- **Checks:** `sync_sim` checks the split (every choice share sends is acted on by sync, every page sync opens is drawn by share, no dialog left in sync, share's byte cut); `crop_sim` (every format on 16:9, 16:10, 21:9, 4:3 and 5:4 windows: the exact ratio, centred, the bars tiling the rest with no overlap; the screen centre from every HUD point; the menu, ui, picker and the free build), and `menu_sim`, `sync_sim`, `free_test` updated.
- **Version 6.2.0** in all twelve scripts.

## Take 12 Scenery's button: the same clapper in sepia
- A sun on the 4-pixel-tall slate never read well (a red dome, then a pattern). The free button is now the Take 12 clapper and its "12" in sepia, like an old film, with only the red recording light left in colour: the same logo and feel, a step below the full Take 12, which stays the colour picture. None of Take 12's three looks is sepia, so the two are never confused.
- New `scenery/art` texture and icon, and the free boards redrawn with it; the Read Me, the listing and the build steps describe it. Take 12's and the Watch's art and boards are unchanged.

## Take 12 Scenery: its own button (no change to Take 12's scripts)
- **The design:** the Take 12 clapper (Rec look, the same chalk and coral) with a coral sun setting on a chalk horizon, and a faint reflection, in place of the "12". It is the same family as the Watch and its eye: recognisable as Take 12, never mistaken for it. Open and clapped frames, so the little clap still works.
- **One design:** `scenery/art/take12_scenery_icon_sheet_512x256.png` keeps the Take 12 sheet's layout, with the Scenery frames in every look column, so the scripts' frame maths work unchanged. The free build leaves out the Button choice under Options > Look (three build substitutions; `hud/src` is untouched, still 6.1.0). A 128 px icon is there too.
- **Boards:** the free boards show the sun clapper and the full name, TAKE 12 / SCENERY, in two big lines, with "FREE CAMERA HUD" and the FREE ribbon. Take 12's and the Watch's boards are unchanged.
- **Docs:** the build steps name the new texture; the Read Me and the listing describe the one button.
- **Checks:** `sheet_test` runs the frame maths on both sheets and checks the Scenery columns match; `free_test` checks there is no Button choice and the README's texture; `listing_check` checks the free boards' clapper and title.

## 6.1.0
**Take 12 Scenery: the scenery camera on its own, free.**
- **What it is.** A free (L$0) HUD with the scenery camera of Take 12: drone views, wide horizons and skybox rooms from the inside, idle start, tap / double-tap, Photo hold, Next, Stop, Pace, Indoors, Reach, Alt-cam, the three button looks, the status line, tips and the little clap. Me, Us, Still, sharing, favourites and the seated view stay in the full Take 12. It replaces the old Lite, and the name Lite is gone.
- **One quiet pointer.** The main menu shows Scenery, Options, More cameras, Help and Close. More cameras opens the full Take 12's listing (`BUY_URL` in `ui.lsl`); the menu text says what the other cameras are. Nothing else asks to buy. Buttons the free build does not have are left out, not shown with a lock.
- **Hold**, with no sharing, opens the menu: the live menu (Photo, Next, Stop) while it rolls.
- **Generated, not copied.** `tools/build_scenery.py` writes `scenery/src` (core, ui, scenery, tips) from `hud/src`: `LITE = 1`, plus the free build's own texts (the name, the welcome, the hold help, the notecard name, the Options and Camera page lines, two tips). Every substitution must match exactly once. The full build carries none of those texts, so `ui` stays at 13.4 KB free.
- **Full Take 12:** no visible change. `ui` leaves out the buttons a build does not have (the full build: More cameras). `scenery` no longer turns rooms off in the free build.
- **Its own Read Me, listing (L$0) and six boards** (`scenery/`): a FREE ribbon, "SCENERY CAMERA HUD", the Share view dimmed as "Full Take 12", chips Drone views, Skybox rooms, Idle start, Photo hold.
- **Listings fit the Marketplace.** The Full description takes at most 5000 characters: Take 12's is now 3,586 (it was over), and it names Take 12 Scenery as the free companion. `listing_check` keeps every listing under 4800 and checks the free listing and boards.
- **CI:** `build_scenery.py --check`, `lslcheck` on `scenery/src`, `free_test` (the free scripts are the full ones with only the switch and the texts changed, rooms on, no favourites, the notecard shipped), and `menu_sim` for both builds' menus.
- **Removed:** `hud-lite/`, `tools/build_lite.py`, `tools/sim/lite_test.py`.
- **Version 6.1.0** in all ten scripts (the Watch stays 6.0.1). Re-drop all ten.

## Marketing for 6.0.1 (no script changes)
- **Listing:** "Everyone sees the same picture, whatever their own zoom" in SHARE THE VIEW, and in the update message, now "Take 12 6.0.1".
- **Watch listing:** the same line, plus a Features line, "The same picture as your friend, whatever your zoom".
- **Watch board:** the "Same picture, any zoom" chip replaces "Follows their cuts", since "See your friend's view." already says that. The Take 12 boards stay as in 6.0.

## 6.0.1
**Sharing: the same picture for everyone, each through their own lens.**
- **The problem.** A viewer received only the director's camera position and focus, and looked through their own zoom. Different zooms gave different pictures. Since 6.0 it was worse: a director zoomed to 85 mm backs the camera off about 4× so the people keep their size for them, and viewers at the normal zoom saw a tiny group.
- **The fix.** core's CAMSET (and so `cam|…`) now carries the director's field of view. Each viewer places the camera on the same line to the same focus, at the distance that keeps the picture size through their own lens:
  - `k = tan(director/2) / tan(yours/2)`, clamped to 0.2–5;
  - 0.3 m short of a wall;
  - placed again within a second if the viewer zooms while watching.
- **No lens advice for viewers, nothing to click.** The same `place()` runs in `sync` and in the Watch.
- **Compatible with 6.0:** older viewers ignore the extra field, and newer viewers apply a camera without it as it is.
- **Docs:** SHARING.md ("Each through their own lens") and the Read Me.
- **Tests:** `sync_sim` checks the picture size for viewers at 21–105 mm with an 85 mm director, the line, the wall, a camera without the lens, and `place()` being the same in both scripts.

## 6.0.0
**Your lens, everywhere.** The viewer's zoom is your lens, and every camera now frames for it, with one rule: **the lens changes the perspective, never the size of the picture.**
- **Zoom while a camera runs, and the picture keeps its size.**
  - **Me, Us and Only friends** dolly the camera along its line to the focus by `k = tan(old/2) / tan(new/2)`, as a glide (FOVMSG → GLIDE). A subject at the focus keeps its exact size, the angle down is unchanged, and the next shots are planned for the new lens. With no room (a wall, or past 25–30 m), they cut to a fresh shot for that lens.
  - **Follow my lead** scales your own distance by the same k (capped at 25 m), so a view you framed survives a zoom.
  - **core** now reports the zoom in every camera (before: only in Still) and accepts glides from Me and Us.
- **The lens shapes the shot mix,** like a camera operator: the close-view chance gets `+ clamp((mm − 35)/120, −0.15, +0.30)`, which gives about 43 % at 21 mm, 68 % at 50 mm and 85 % from 85 mm. Never two close views in a row, as before. A long lens leaves the far wide group shots to the existing fallbacks (fewer people, nearest first).
- **The status line shows your lens and the range each camera likes:**
  - Scenery ≤ 28 mm;
  - Me 35–50;
  - Us 24–50;
  - Only friends 35–85.
  In range it reads `… · 35 mm ✓`, else `… · 21 mm · try 24`. Still keeps its exact guide.
- **Scenery stays wide.** Zooming gives a telephoto detail of the same view.
- **A new tip, "Your lens":** Ctrl+0 / Ctrl+8 / Ctrl+9, once per run when the lens is outside the camera's range.
- **Memory:** `friends` is at 12.5 KB free by the stricter estimate (two trace details shortened).
- **The button comes alive, quietly.** While a camera runs, the clapper gives a tiny clap: the sheet's own clapped frame, for a quarter of a second, when it starts and then every 8–12 s. It is still with your own camera, in Photo and in a pause. There is no new texture to upload: it uses the clapped frames that are already on the sheet. It is drawn by `tips`, which has the room (ui is kept above 13 KB), with exactly ui's `frame()` maths.
- **Ads for 6.0:**
  - the coral label now reads **NEW: YOUR LENS**, under the sunset view (now HORIZON), which carries the HUD's own "85 MM" readout;
  - "Your lens" replaces the Photo hold chip;
  - the vendor and portrait stamps say Your lens.
- **The listing:**
  - lens-aware short description, a Features line (Your lens, everywhere), lens keywords and a promo line;
  - the clap in Good to know and in What is new;
  - the lens line in the shot list.
- **Docs:** a new Read Me section, YOUR LENS. ARCHITECTURE (FOVMSG, GLIDE), FRAME.md, the listing (YOUR LENS, "What is new in 6.0") and `listing_check` are updated.
- **Tests:**
  - **new `tools/sim/zoom_sim.py`:** size and angle kept over every lens pair, the fallback, the close-view table, and the scripts' handlers;
  - **`tips_sim`:** lens text per camera, ranges, the lens tip, Still and Photo unchanged;
  - **`framing_sim`** follows the close-view rule.

## 5.9.0
**Still, for real portraits: a lens guide, and Shift + A/D to slide the picture.**
- **The lens guide.** Each framing names the lens a photographer would use: Full length 50 mm, Half length 85 mm, Close 105 mm. The line above the button shows it next to yours, live, as you zoom:
  - `□ Still · Close · 105 mm · now 21 · Ctrl+0`
  - `□ Still · Close · 105 mm ✓` (within 15 %)
  - Ctrl+8 when the lens is too long.
  Take 12 reads the viewer's field of view (`llGetCameraFOV`, 35 mm equivalent `12 / tan(FOV/2)`, SL's normal view ≈ 21 mm). A script cannot change it, so the guide tells you which key to press. The camera already backs off as you zoom, keeping the picture's size: a longer lens gives the flatter, flattering portrait perspective. The line shows in Still even with the status line off.
- **Shift + A/D (or Shift + ←/→)** slides you left or right in the picture (up to 0.6 of the way to the edge), for example onto a third, without moving the camera round you. Second Life sends Shift + A/D as strafe, which a script can tell apart from turn; plain A/D still walks round you. The next framing clears it.
- **Frame writes no text of its own any more.** The framing name lives in the status line, with the lens.
- **New STILL 7381 (frame → tips).** The Still tip mentions Shift + A/D.
- **Docs:** Read Me (Still), docs/FRAME.md (the lens guide and the slide), ARCHITECTURE and the listing.
- **Tests:**
  - **`frame_sim`:** the lens table, the mm conversion, every framing exact at its lens, the strafe/turn split, and the slide landing where asked;
  - **`tips_sim`:** the guide lines, ✓, Ctrl+0 / Ctrl+8, status line off, and Plain.

## 5.8.2
**Bug fixes.** These came from your report and a code review of every script.
- **A "|" above the HUD, all the time.** When nothing was shared, the text above the button showed a stray "|". LSL reads `llGetSubString("|", 1, -1)` as an inverted range and returns the "|" itself. Fixed in `tips`.
- **The text above the HUD could freeze.** Second Life cuts hover text at 254 bytes, and `tips` then took its own text for another script's notice. It now reads the text back after writing. `sync` does the same for its notices, so a long "didn't answer" list clears again.
- **Watching could stay blank** if a sharing notice was up when it started. `tips` kept no timer for it.
- **Seated view saved the wrong angle for every button** (since 4.8.0). Off saved Auto, Auto saved Higher, and Lower deleted the setting. Now each button saves its own angle.
- **Menus that could not open:**
  - The Pick page failed when a saved friend had a long username: "✓ " pushed the label over llDialog's 24 bytes.
  - The Share panel failed when a live director with a longer name was near.
  - The roster failed when someone had just left.
  - The Share panel's text could pass 512 bytes in a crowd.
  Person labels are now cut to 24 bytes, names are remembered after people leave, and dialog texts are capped.
- **"Pass camera" to someone on a Take 12 Watch ended the live view for everyone.** A Watch has no camera of its own. The Watch now joins with `join|W`, and the roster offers only Remove for it.
- **Watching while your own camera ran** left both your camera and the shared one driving the same view. Watching now stops your own camera first.
- **Names for people who had left:** "Ana left", "Pano's camera is gone" and "👁 Pano" lost the name, because `llKey2Name` returns "" for someone outside the region. Names are now remembered, in sync and in the Watch.
- **The Watch** wiped "Pano's camera is gone" and "Your camera" the moment they appeared. They now stay for 4 s.
- **A late "Watch" after End live** sat on a dead view for 25 s. It is now answered with `end`.
- **Reset** now also puts back the chat channel (picker) and the button look (ui).
- **Changing the menu style by chat while a menu was open** sent the click to the wrong page. Clicks are now matched against the labels shown.
- **Chat command checks:** `/77 face` and `/77 trace` / `cutmode` accept only valid values.
- **Live menu:** no negative "next cut in".
- **Read Me:** "Hold › ⋯ More › Photo / Release" (hold opens the Share panel).
- **Tests:**
  - `tips_sim` models LSL's substring rules, the 254-byte cut and a stopping timer;
  - `menu_sim` checks the Seated view mapping and the Pick label bytes;
  - `sync_sim` checks Watch viewers, the late join and watching with your own camera running.

## Marketing refresh (no script changes; the HUD stays at 5.8.1)
The Marketplace texts and the ad boards were still the 4.7 ones. Now:
- **`hud/marketing/marketplace_listing.md`** is rewritten:
  - the new camera names (Scenery, Me, Us, Still);
  - **Share the view** and the free Take 12 Watch;
  - Follow my lead and the seated view;
  - the status line and tips;
  - the controls (Hold now opens the Share panel);
  - the Features list, keywords and promo lines;
  - a **"What is new in 5.8"** message for existing buyers.
  The 4.8 listing is kept in `hud/marketing/legacy/`.
- **Ad boards** (all six, regenerated by `tools/art/make_adboard.py`):
  - "Share the view" replaces the "Friends mode" chip;
  - the FRIENDS picture becomes SHARE, with the HUD's own "LIVE" tag, and a coral "NEW: SHARE THE VIEW" label;
  - the small print and the "HOLD" line are updated.
  The tagline "Your idle time, framed." stays.
- **Take 12 Watch (free)** gets its own listing, `watch/marketing/marketplace_listing_watch.md`, and board, `watch/marketing/adboard_watch_1024.png`.
- The shot list for real snapshots now includes the Share panel, the LIVE text, the status line and the seated view.
- **New `tools/sim/listing_check.py` in CI:**
  - no stale names in the listings;
  - five Features each;
  - the board text matches the listing;
  - all seven boards exist at their sizes.

## 5.8.1
**Plain script names.** The ten HUD scripts lose the `cinema_` prefix, since the HUD itself is Take 12: `core`, `ui`, `scenery`, `people`, `friends`, `picker`, `frame`, `lens`, `sync`, `tips` (`hud/src/core.lsl` …).
- Nothing else changes: no script looks another up by name, so the link messages, the settings (your saved settings and friends stay) and the behaviour are exactly 5.8.0.
- **Updating in-world:** delete **all** the old `cinema_*` scripts from the prim first, then add the ten new ones. Left in, an old script would run beside its new twin (it announces 5.8.0 against 5.8.1, so the version warning tells you).
- The version is 5.8.1 everywhere so that mixed old and new scripts are caught. Older entries below keep the names of their time. The paused Lite build (`hud-lite/`) keeps the old names too.

## 5.8.0
**A status line above the button: which camera runs, and who is in charge.** While Take 12 films, one quiet line always says so:
- `◇ Scenery · auto`, or `◇ Scenery · started while you were idle`;
- `○ Me · auto`, `◎ Us · auto`, `□ Still · held`;
- `♡ Only friends · auto`, which becomes `· your view` once you frame it yourself (and goes back to auto with Release);
- `▣ Photo · held`;
- `◇ Scenery · paused · Esc to carry on`.

Nothing above the button means your own camera. The mark follows the menu style (none in Plain). It can be turned off in Options › Look › Status line, or with `/77 statusline on|off`.

- **One owner for the text above the HUD.** `cinema_tips` now composes:
  - the sharing block (from sync, over the new TEXT 7380), with the status line under it while you're live;
  - only `👁 Pano` while you watch someone;
  - the tips, under the status line, showing only their second line.
  Other scripts' short notices (the lens, Frame, sync) still take the whole text for their few seconds. It never writes over them, and the status comes back within a second.
- **Sync no longer re-asserts its indicator itself.** It sends it as TEXT and clears its own notices after about 4 s.
- **Core:** UI_STATE carries a 4th field, `why` (`idle` when the idle start began the run).
- **Tips:** the Paused, Hold › More and Sitting tips are reworded so their second line stands alone.
- **`tools/sim/tips_sim.py` now models the whole text above the button:**
  - every camera's line, idle start, your view, Photo and pause;
  - Plain, and Status line off;
  - LIVE on top, watching alone;
  - notices never overwritten;
  - tips under the status.
  `sync_sim` checks the TEXT hand-off, and `menu_sim` checks the Look page.

## 5.7.0
**Symbols by default, and short tips above the button.**
- **Menu style:** Symbols (quiet black-and-white marks) is now the default. Plain and Color stay in Options › Look. Settings step 7 moves the 5.6.0 default (Plain) over; picking Plain again keeps it.
- **Tips** (new script `cinema_tips`, the tenth: add it to the HUD). When something just happens, a two-line tip says where you are and what you can do next:
  - the HUD is worn;
  - a camera starts (Scenery, Me, Us, Only friends, Still);
  - Photo, a pause, your camera coming back;
  - about 90 s into a run (Hold › More);
  - sitting in Only friends (W/S);
  - idle start.
  - **On screen:** each tip shows for 6 s, in a softer white, at most one per 20 s, and only when nothing else is above the HUD: the LIVE status, "Your view is kept" and Still's framing names always win.
  - **After a while:** each tip retires after 3 showings. When all have retired, or after 24 tips, Tips turns itself off with one chat line.
  - **Help is now a small page:** Read Me, and Tips on/off. Turning Tips back on starts every tip from zero. `/77 tips on|off` does the same.
- **New `tools/sim/tips_sim.py` in CI**, which plays the tips script against the core's states and the other scripts' hover text. `menu_sim` checks the Help page and the Symbols default.

## 5.6.0
**Cleaner menus: four cameras with plain names, settings in Options, and menu styles.**
- **The main menu** is down from 11 buttons to 8: **Scenery · Me · Us · Still**, plus Share, Options, Help and Close. Each camera gets one line of explanation on the page:
  - Scenery: the place, while you are away;
  - Me: follows you (it was Personal);
  - Us: you and the people around you; inside it, **Everyone near** (it was Social), **Only friends** (it was Friends) and **Friends list**;
  - Still: a held picture of you (it was Frame).
  The cameras themselves are unchanged. `/77 me`, `/77 us` and `/77 still` work too, alongside the old names.
- **Options has three groups:**
  - **Timing:** Pace, and Idle start (it was AFK);
  - **Camera:** Seated view, Indoors, Reach, Alt-cam, Chat cuts, Phantom;
  - **Look:** Menu style, Button, Chat text.
  Favourites, Test cam and Reset sit next to them. Back always goes to the page above.
- **Menu styles** (Options › Look), the same in the Share panel and the Friends list:
  - **Plain** (words only), the new default for everyone;
  - **Symbols** (quiet black-and-white marks);
  - **Color** (the emoji as before).
- **Hold** is described as "share your view" in the welcome text and the Read Me. The Pace step "Still" is now called "Slowest", so it doesn't clash with the Still camera.
- **Memory:** the chat commands moved from `cinema_ui` to `cinema_picker`, so the menus have room (UI 14.8 KB free, by the stricter estimate).
- **New `tools/sim/menu_sim.py` in CI:**
  - every page fits a dialog and every button has a name;
  - labels are distinct on each page, in all three styles;
  - Back goes to the page above;
  - Plain is the default.

## 5.5.0
**Sharing, HUD-first: hold the button, Go live.** Starting a shared view took a walk through several menus. Now:
- **Hold the HUD button** opens the **Share panel**, whatever you're doing. Going live is two actions: hold, then **🔴 Go live**. With your camera off, it starts Social.
- **The panel shows who is near** (a quick check, about 1.5 s): who has Take 12 or the Watch HUD, who is busy watching someone, who is live.
  - **+ name** invites one person.
  - **👁 name** watches someone who is already live.
  - **Give Watch** hands out the free HUD.
  - **⋯ More** opens the old live menu (photo hold, next, stop, modes, release) or the main menu.
- **While live:** who watches and who is looking around, Invite more, a **Roster** (Pass camera, Remove), **Lead: Ask / Always / Never**, and End live.
- **While viewing:** **Ask to lead**. The director gets Allow / Decline, which is declined automatically after 20 s. On Allow, everyone follows the new director.
- **Invites:** a Watch HUD, or Take 12 with you in its Friends, joins at once. Anyone else sees "Pano invites you · hold to watch" for 20 s. After an invite you get a line saying who watches, who was asked, who is busy and who didn't answer.
- **Who is connected, always:** above the director's button, "● LIVE · 3 watching" and, below it, the names: "Ana · Ben (looking around) · Dee (no signal)".
  - Every viewer's HUD sends a heartbeat every 10 s. Someone silent for 25 s shows "(no signal)", and after 45 s they are dropped ("Dee lost connection").
  - Viewers see "👁 Pano", or "👁 Pano · no signal…" when the director goes quiet.
- **Reliability:**
  - a heartbeat: viewers drop out 25 s after a director vanishes;
  - viewers who leave the region are dropped from the roster;
  - a teleport ends sharing;
  - repeated Go live / End live within 2 s is ignored;
  - a second lead request while one is waiting is declined.
- **The protocol changed (v2):** everyone sharing must update, including the Watch HUD. Design and protocol: `docs/SHARING.md`.

## 5.4.0
**Share the view: one director at a time, one Share button, and you always know who sees what.**
- **One Share button**, now in the tap menu as well as the hold menu. It does what fits the moment:
  - nothing is shared: it starts your camera if it isn't running (in your last mode) and offers your view;
  - you share: it shows who watches and who is looking around, with Offer again, Stop sharing and Give Watch;
  - you watch: Direct or Leave;
  - an offer is waiting for you: it joins.
- **One director:** everyone watching follows one camera, so two cameras never fight.
- **Direct:** a watcher with Take 12 can take over. Everyone, the old director too, then follows their camera, and all see "Ana directs now". The free Watch HUD follows the new director by itself.
- **Next for all:** a watcher's double-tap cuts for everyone. Double-taps less than 5 s apart cut once, so two friends tapping together don't make two jumps.
- **Looking around:** a watcher who orbits their own camera steps out, and the director sees "Ben is looking around". Esc puts them back on the shared view ("Ben is back").
- **Ending:** when the director stops, it ends for everyone. A movement key still gives a watcher their own camera back.

## 5.3.1
**You now see who got your Share.** Two seconds after you press Share, one line in chat and above your button tells you who answered, for example "Offered to: Ana, Ben, Cleo (double-tap)":
- a name alone is watching your view now;
- "(double-tap)" means they have Take 12 but have not saved you, so they see "double-tap to watch" above their button;
- if nobody answers: "Nobody near you wears Take 12 or Take 12 Watch (within 20 m)".

Texts above the button now stay 5 seconds instead of 3. Hover text always sits above a HUD and Second Life cannot place it below. If your button is right at the top edge of the screen, drag it down a little so the text fits; the chat line is always there.

## 5.3.0
**Share the view switches at once, no clicking.**
- **Long press › 👁 Share** now offers your view straight away. The Share dialog that follows only holds Give Watch and Stop sharing.
- **A friend wearing the free Take 12 Watch** switches to your view instantly: wearing it is the yes. Above their HUD: "Watching Pano · tap: your camera · double-tap: next".
- **A friend with Take 12 who has you in their Friends** switches instantly too.
- **Someone with Take 12 who has not saved you** is not taken over. Above their button, for 20 s: "Pano shares a view · double-tap to watch". One double-tap joins; ignored, the text goes away and the double-tap is theirs again.
- The Watch HUD has no dialog any more.

## 5.2.1
**Fix: the Watch HUD showed "trying to clear camera parameters but PERMISSION_CONTROL_CAMERA permission not set".** Taking the HUD off while watching tried to hand the camera back, but Second Life had already withdrawn the HUD's camera permission at that moment (and gives the camera back by itself). Now taking it off only tells the sharer you left. The camera is cleared only while the HUD is still worn and holds the permission. Putting the Watch HUD on asks for its permissions again. Take 12's own sync script got the same fix, and taking Take 12 off while sharing tells your watchers it ended.

## 5.2.0
**Share the view: your friends watch what your Take 12 films, live.**
- **Offer:** long press › **👁 Share** › **Offer view**. Everyone within 20 m who wears Take 12 or the free **Take 12 Watch** HUD is asked "Pano shares their view. Watch?" and taps **Watch**.
- **Watching:** their camera then follows every cut and glide of yours. When someone joins or leaves, "👁 Ana watches" or "👁 Ana left" shows above your button.
- **Anyone drives:** a watcher's double-tap cuts to the next view for everyone.
- **Leaving:** a watcher gets their own camera back with any movement key, or with a single tap on the Watch HUD. A Take 12 owner also gets it back by starting their own camera from the menu.
- **Ending:** stopping your camera, or Share › **Stop sharing**, ends it for everyone.
- **The Watch HUD's look:** the Take 12 clapper with a quiet pixel eye on the slate instead of the "12" (`watch/art/take12_watch_icon_128.png`, made by `tools/art/make_icon.py`). How to build it: `watch/README.md`.
- **Give Watch:** Share › **Give Watch** hands the free HUD to someone near you. Put the "Take 12 Watch" object in your HUD's contents for this.
- Only one thing has to be worn: a script can move an avatar's camera only with their own permission, and HUDs get that permission by themselves. Same region only.
- **New script `cinema_sync.lsl`** (nine scripts now), the free Watch HUD's script `watch/take12_watch.lsl`, and core reports every camera it sets (CAMSET 7325).
- New `tools/sim/sync_sim.py` in CI: both scripts speak the same protocol, and a simulated region checks that only people within 20 m are asked, cameras follow, double-taps cut for all, keys release, and stopping ends it.

## 5.1.1
**Fix: Follow my lead did not show "Got it", or did not keep the view.**
- **Too insensitive:** Take 12 only noticed your own camera once it was more than 1 m from the shot. In Friends it now also notices a move of 0.3 m, or a turn of the view of about 10°, so a small orbit toward your faces counts.
- **Friends undid your view:** after your view was taken, Friends kept checking "is everyone inside the frame?" against its own old camera. With a close view it decided people were out of frame and cut to a wider shot. While you lead, that check, the pull-back and the drift glide are off; your friends are followed at the next cut instead.
- "Your view is kept · Esc to continue" shows for 3 s above the button (a notice, nothing to click), only when your view really changed. The first time after each rez, one chat line explains Esc and Release. The live menu entry is now called **Release** (it was Auto): it lets go of your view.
- **Check that all eight scripts are in the HUD.** `cinema_lens` is new since 5.0, and without it nothing is kept.
- Follow my lead works in Friends only, for now.

## 5.1.0
**Follow my lead: frame it yourself with Second Life's own camera, and Take 12 keeps it.** 5.0's keys (gears, angle keys, A/D round, Tune) were too much to learn, and they fought the camera everyone already knows. They are gone.
- In Friends, frame the view the usual way: Alt-orbit, the mouse wheel, or A/D while seated. When the camera has been still for about 1.5 s, "Got it" shows, and your view becomes the shot. Press **Esc** and it carries on from there.
- From then on, every cut and double-tap variation keeps **how close, how high and where you aimed** (your faces, which a script cannot see when you sit or lie down). They are kept relative to the group, so when your friends shift, the camera follows them.
- **Seated, W/S** step about 20 % closer or wider; they do not move a seated avatar.
- **Back to automatic:** long press › **Release** (named Auto in 5.1.0). It also happens by itself when you sit down or stand up, or when a friend comes or goes.
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
