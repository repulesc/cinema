# Changelog

## 8.9.0, lighter (replace core, bars, fixed, tracking and ui)
A profile of the real scripts through a session (waiting, Tracking, Portrait, Scenic, Auto) counted every event, link
message and prim or camera update. Every link message wakes all twelve scripts, so the messages sent often are what
the sim pays for.
- **Drift woke all twelve scripts 1.7 times a second for nothing:** at each of its steps core sent its camera (CAMSET),
  which only sync needs, and only while someone watches you. A camera that moves by itself now goes only then (or
  once, so sync knows you film). Scenic: 53 events a second down to 31; Auto standing: 45 down to 30; waiting: 7 down
  to 5; Tracking walking: 21 down to 16.
- **tracking rests** when it has nothing to do (another shot, Auto off): it ticked twice a second regardless.
- **LSL tests every part of an `&&`:** ui read a setting at every message it got, and fixed parsed every message while
  it ran. Both only do it for their own message now.
- **core has room again** (15.1 KB to 15.9 KB): the basic shot (a level portrait when a shot's script is silent or
  Scenic finds no view) moved to bars, which has plenty, in the free build too.
- New `load_emu` (in CI): ceilings for events and messages in each kind of shot (it fails on the earlier 8.9.0), and
  the basic shot from bars. The version stays 8.9.0, so only these five scripts change.

## 8.9.0, ui updated (the setup and the guide card; replace ui only)
- **A tap closing the guide card was taken for a tap on the [12]** (in-world): ui looked at the touched part again when
  the touch ended, after the card had gone. In the setup's eye-line step it kept the line wherever it was; two such
  taps toggled the strip. Now the end of a touch counts only if it began on the [12] (the product's ui too).
- **The guide card comes at the setup's end** (the user's call): it came first, on the first wear and after
  Reset › Everything, over the setup. A tap on the [12] starts the setup, and the card closes if it is up.
- **A script late at the check** (being replaced, or stopped and started again) turned the [12] amber until the HUD
  was worn again, though the script was there. When it answers, the [12] is white again.
- Only ui changes (the new design's, and the product's touch fix); the version stays 8.9.0 so nothing else needs
  replacing.

## 8.9.0 (Connect, start to finish: a deep review)
Every script path of Connect was read end to end; each problem below was first a failing test (`connect_emu`'s
review, on the product and on the new design), then fixed. docs/CONNECT.md has the details.
- **Leave sticks:** two friends were joined again by themselves 10 s after a Leave. Asking each other still works.
- **Everything off is off for Connect:** after a hold, friends were joined again 10 s later and others could still
  ask you. Now nobody near sees you until you hold again; then your friends join again.
- **An older copy worn with a newer one** answered for you too, and whoever watched you was sent back every second.
  It now keeps out of Connect.
- **SHARING stayed** (and your camera went on to them) for up to 30 min after a watcher took the HUD off, logged off
  or walked away. It goes within 10 s now.
- **A question could get stuck:** tapping the rings when the chime sounded opened the Connect page over it; it could
  not be answered, and everyone else asking you was told you were busy until you wore the HUD again. The rings now
  show the question again, and it ends by itself.
- **A Yes after 20 s** connected only the one who said it. The asker now waits as long as the question stays open.
- **What the watcher sees:** a still shot no longer drifts as you shift in place; a new frame reaches them at once; an
  Alt-click close-up of a small thing comes out the right size through their lens (it came out four times too small,
  or from behind it: the "wall camera" seen in an early test).
- **Quieter:** at 20 m a step back and forth is no longer an "out of reach" note each time; the rings, while your one
  friend watches you, say so (they said the friend wasn't filming); a still camera is sent once a second, not 7 times.
- **Sturdier:** worn again, you rejoin even if the first message is lost; sync started again while you watch gives
  you your own film, not a frozen view.
- The Read Me's Connect section now says what is shared (what you see, an Alt-click look too; never mouselook).
- sync, core and carry change (carry took two small jobs from sync, which needed the room); every script is 8.9.0,
  the new design's too. Replace all twelve scripts.

## 8.8.2 (a given copy keeps its textures)
- **A HUD given to someone else drew grey and white squares** (a friend's test): on a new owner the scripts wiped all
  of Linkset Data, the texture UUIDs with the last owner's settings, and the copy of them in the root's description is
  not saved in-world when a script sets it on a worn HUD. The new owner's wipe now keeps `cin.take12_*`: the HUD's own
  textures, not anyone's settings. Every buyer would have hit this.
- ui changes (and the new design's ui); every script is 8.8.2. `textures_emu` gives a working HUD away with its
  description unsaved, in four script start orders (it fails before the fix).

## The new design (lab 2.2): round ends whatever the texture, seen on the bars, the picture asked, no "lab" name
- The island's round ends are real round shapes (cylinders turned to face you), no longer a cell of the marks texture
  (a marks texture uploaded for lab 1 drew them square in-world). Its black is lifted, so it shows on the film's bars.
- The setup's last step asks for the picture: Cinema (the film's bars) or Full screen. Its alignment step's Done really
  ends the setup now (in lab 2 it only closed the menu: no Auto, the strip not opened). The tour pages are gone (the
  guide card comes first).
- Nothing the wearer sees says "lab": the HUD is "Take 12", the guide card "TAKE 12", chat and `/12 status` plain.

## Take 12 Lab, lab 2.1 (the island always shows; lab/ holds only the Lab)
- The strip sends the island to screen again whenever screen starts (in-world the scripts go in one by one: a screen
  started after the strip never heard of the island and drew the full band, the product's look).
- A Lab built with the product's builder (no `t12 tab`, `t12 tab2`): the island still floats, square-ended, and says
  once in chat how to add its round ends.
- The old 7.x experiments (the 4.5.0 Photographer mode, soft keys) moved from `lab/` to `legacy/old-lab/`.

## 8.8.1 (Drift's glide, smooth)
- **The glide was choppy in-world:** 8.7.0 moved a locked camera 20 times a second, and Second Life does not ease a
  locked camera. Now the viewer's own follow camera does it, eased every frame as Tracking is: its behindness angle (how
  far round from behind you it may be) narrows a little every half second, and the viewer swings the camera in to it.
  The same glide: close, then about 40° round you at one distance and height, toward your back, never along a path a
  wall crosses; when the close cut is already behind you, the view holds.
- scenic changes; every script is 8.8.1. The emulator models the behindness angle; `scenic_emu` measures the swing.

## Take 12 Lab, lab 2 (the floating island; the setup aligns both ways; the product is unchanged)
- **The island** (from the owner's in-world screenshot: the notch was lopsided, wide on the left for a rare prompt,
  and an old iPhone's): it floats 8 px in from the edge, centred on the [12], with round ends (a disc at each end of a
  black middle, round at any width). The Orbit, the shot and `›` are left of the [12]; the frame, Connect and the
  shutter right of it, so the island is even. With the camera yours, the last shot shows faintly; a tap takes it back.
- **The setup:** the guide card comes first, on the first wear and after Reset › Everything; the alignment step has
  Up, Down and Done, 10 px a step (it could only go down, 40 px at a time).
- The lab now owns ui and text too. One more part (`t12 tab2`); the marks and the guide card change.

## The lab's guide card: the hood as it is on screen (texture only)
- The Quiet strip drawn on a slice of the picture: the film's top bar across it (1.85; at 2.39 the bar is taller and
  the notch is lost in it) and the notch hanging from the screen's edge, joined to the bar. Upload `take12_guide_lab`
  again.

## The guide cards' bottom row (texture only, the product's and the lab's)
- The three touches (tap, double-tap, hold) drawn at one size on one grid, the divider no longer against them, the
  list, the divider, the touches and the footer evenly spaced. Upload `take12_guide` again; no script changes.

## Take 12 Lab, lab 1 (the Quiet and Direct pages; the product is unchanged)
- A separate HUD in `lab/` for trying ideas without touching the product: its own strip and screen, the product's
  other ten scripts copied unchanged (`tools/build_lab.py`), its own builder (two more parts), marks (the fold key and
  the notch) and guide card. `lab/README.md` says how to build it in-world.
- **Quiet** (the default): a notch with rounded lower corners, as wide as its words: the Orbit, the running shot, `›`,
  the frame, the [12], Connect and the shutter; KEEP NEW and UNDO show there too. **Direct**: the full strip, the four
  shots in Auto too. The shot's name or `›` opens it, `‹` folds it; the page is kept. Tested in `lab_emu`.

## 8.8.0 (the guide card)
- **The guide card:** the setup ends on one card in the screen's middle: the strip drawn whole, a number under each
  key (the Orbit, the shots, the frame, the [12], Connect, the options, the shutter) and one line for each. A tap on
  the card closes it; Help › Guide and `/12 guide` show it again (the strip opens with it). Hiding the strip or
  everything off closes it too. It replaces the three tour pages.
- **In-world:** one new part, `t12 guide` (touch the builder in the HUD: it adds only what is missing), and one new
  texture, `hud/art/take12_guide_1024.png` (`tools/art/make_guide.py`), uploaded as `take12_guide` and dropped in.
  Its UUID is kept like the others, and in its part's own description, so a new owner has it.
- **Without the texture** (the free build, or before it is dropped in): the three tour pages as before, and Help ›
  Guide gives the Read Me. About › Read Me always gives the notecard.
- screen, ui and carry change; every script is 8.8.0. Tested in `guide_emu` (the setup, closing, Help › Guide,
  `/12 guide`, a 5:4 window at L, Reset › Everything, a new owner, and without the texture).

## 8.7.0 (Tracking for film and for play; Drift's glide)
- **The Tracking looks, higher and further** (Film looked up from chest height: too low for play; Shoulder was too
  close): **Film** 3.6 m, at about head height looking 6° down, you on a third; **Shoulder** 2.2 m, 8° down;
  **Classic** 4.2 m, high and centred, the game view. **Lead room:** walking, the frame leaves room ahead of you,
  eased in over 2 s (no jolt, for a friend watching too).
- **Drift's glide** (the new default): close on you, then the camera slides slowly round you at eye height (about 40°
  over 24 s, 20 small steps a second, never along a path a wall crosses, still in a cabin), then a cut to a new close.
  Settings › Motion › Reveal keeps 8.1.0's rise and pull-back. Breathe is gone (a Breathe setting plays the glide).
- **Connect, the lens match:** a friend whose zoom differs from yours saw you 16-25 % too near or too far in Tracking
  (their HUD moves along the view round your camera's aim, and for the viewer's own camera that aim was a point 3 m
  ahead, not you). The aim is now you: within 3 %. Measured in `connect_emu` (a 38 mm director, a 21 mm watcher).
  Connect's traffic checked too: 1 heartbeat a second to the one you are with, a "here" every 10 s, about 7 camera
  updates a second only while someone watches.
- tracking, scenic, ui, text and core change; every script is 8.7.0.

## 8.6.0 (menus that make sense; sitting is Fixed's; Connect and Friends together)
- **Sitting switches to Fixed by itself** (manual): the seat's kept view, or "Frame it". Standing up gives you back
  the shot you had. The seat's words, FORGET SEAT and LET GO, are on the strip the moment you sit: LET GO gives a seat
  or vehicle its own camera every time (all its copies); TAKE BACK undoes it. Auto keeps its own rules.
- **Settings in two groups:** Camera (Lens · Eye line · Motion · Idle start · Seats) and Screen (Frames & bars · Place
  · Move in · Move out · S M L · Soft or Clear). The Screen page stays open, so you watch the strip move.
- **Connect:** alone, the rings open the Connect page (Invite, Friends) instead of searching at once; connected, they
  still switch between your film and theirs in one tap. Friends moved from Settings to the Connect page, and Add lists
  anyone within 20 m, not only who wears Take 12.
- A few notes are shorter (the text script needed the room). core, ui, sync, carry and text change; every script is
  8.6.0.

## 8.5.10 (in-world fixes: a dim option, a boat's cabin, after a teleport; your lens always known)
- **A dim option did something:** tapping Scenic's dim ROOM (outdoors) switched the view. A dim option now does nothing.
- **Small closed spaces (a boat's cabin):** Scenic now agrees with Tracking's small-room test (a ceiling within 4 m
  above your head, walls within 6 m all round), so ROOM opens there. In a space with every wall within 5 m, Drift holds
  still views instead of pulling back into the walls; shots stay under a low roof. (The emulator could not rebuild the
  in-world boat exactly: tell us if Drift still leaves it.)
- **After a teleport the camera drifted in from afar:** Tracking's first frame there now snaps into place, then eases
  again.
- **Your lens, always known:** zooming shows it for a moment on the note plate ("Lens 26 mm"), as a camera shows its
  focal length.
- The /12 help list moved from text to screen (text needed the room). scenic, tracking, text and screen change; every
  script is 8.5.10.

## 8.5.9 (one film frame; Auto's shot by the Orbit)
- **One cinema frame for the whole film** (2.39 by default), the same in every shot: the bars no longer jump when the
  shot changes. The ▭ and Settings › Frames & bars › Film choose it; your photo frame still shows only while the
  shutter is open. Each shot's old frame is forgotten (a photo frame kept on a shot still becomes your photo frame).
- **Auto: the shot it chose sits next to the Orbit**, the other shots hidden (an exception to "every word in its
  place": in Auto the strip shows one word, so it reads as one).
- bars, ui, text, carry (the feedback line) and strip change; every script is 8.5.9.

## 8.5.8 (quality pass: the free build's Settings; tidy)
- **The free Take 12 Scenery's Settings showed Vehicles (Fixed's) and hid Frames & bars**, from 8.0.6 on: it took out
  two buttons by position, and a button added in 8.0.6 moved them. It now hides Eye line and Vehicles, as meant.
- **`tools/sim/free_emu.py`** (in CI): the nine free scripts on their own: their menus checked by name, the three dim
  shots and the Orbit only say "In the full Take 12.", Scenic films, no script errors.
- Four declarations nothing used are gone (core, scenic, sync, text). No other change you can see; every script is 8.5.8.

## 8.5.7 (the strip clears taller viewer bars)
- **A tester's strip sat partly under the viewer's menu bar.** A HUD cannot measure the viewer's bars or the window's
  pixel height, and our margins are fractions of the window's height while the bars are fixed pixels: a smaller window
  or a larger UI size covers more. Setup's "Is the whole strip in view?" had one step ("Lower it": 52 px), and a second
  press did nothing.
- **Now every press moves the strip a step (40 px) further from the edge, up to six.** Settings › Look › Place has
  **Move in** too (up at the bottom); choosing a place starts over. The black band follows the strip down.
- **`/12 lower`** does the same from chat, for when the bars cover the [12] itself.
- screen, ui and text change; every script is 8.5.7.

## 8.5.6 (the strip as in 8.4.4, with the 8.5 finish)
- **Back to 8.4.4's places**, which worked: the [12] in the middle with the frame just left of it and Connect just
  right of it; the shots from the left; the shutter at the right, the shot's options before it. Every button stays in
  its place; changing shot changes only the options; in Auto the chosen shot keeps its place. 8.5.0-8.5.5 moved the
  words four times (left, mirrored, pinned, Mac-style) and each was worse.
- **Kept from 8.5:** the pure black band, the smaller [12], no dividers, notes on a plate, no automatic fade. The right
  end stays 200 px from the edge (8.4.4: 180), clear of the viewer's notices.
- strip and screen change; every script is 8.5.6.

## 8.5.5 (the Mac's way: every button in one place)
- **The [12] back at the left, every button after it in one place that never changes:** the Orbit, the four shots,
  the frame, the shutter, Connect, and last the running shot's options. Changing shot changes only the options; in
  Auto the chosen shot stays in its own place. 8.5.2-8.5.4 centred the [12] and the words moved with every shot.
- **The right side is free** (200 px): the viewer's notices no longer cover anything.
- Notes sit under the [12] from its left edge. strip and screen change; every script is 8.5.5.

## 8.5.4 (a steady strip)
- **The words no longer jump when you change shot.** 8.5.2 stretched both halves of the strip to the same width and
  spread their words, so every shot had its own gaps and everything moved. Now there is one gap between every word,
  the shots and the Orbit never move, the shot's options sit next to the [12], and the frame, Connect and the shutter
  are pinned at the right end: changing shot changes only the options.
- **Tips sit in the middle of their plate** (the text rode high on it).
- strip and screen change; every script is 8.5.4.

## 8.5.3 (the strip stays)
- **The automatic fade is gone.** 8.5.0 hid the strip 4 s after your last touch, which got in the way while you
  worked. The strip now shows until you double-tap the [12] (and a double-tap brings it back), as before 8.5.0. A tap
  is always the menu. `/12 fade` is gone.
- strip, screen, ui and text get a little more room. Every script is 8.5.3.

## 8.5.2 (the strip, mirrored)
- **The [12] in the middle of the top, the strip's two blocks either side of it**, as wide as each other, their words
  evenly spread: left the Orbit and the shots, right the options, the frame, Connect and the shutter. The two sides
  balance whatever the running shot's options. The words stop short of the corners, so the viewer's notices at the
  top right no longer cover anything (the black band still runs edge to edge).
- **Faded,** only the [12] is left, in the middle. **Notes** sit centred under it, on their plate.
- **A narrow window** (5:4 at size L): the gaps close to 3 px, and if even that does not fit, the words are drawn a
  touch smaller. Nothing reaches the edge.
- **strip has more room** (18.0 KB estimated free, from 17.2): screen now tells it the window and draws the band, and
  what the left layout left behind is gone.
- Every script is 8.5.2 (strip and screen change). No new part or texture.

## 8.5.1 (strip: room to breathe; clear of the viewer's notices)
- **strip ran out of memory in-world** ("Stack-Heap Collision"): 8.5.0 put the fade and a narrow-window fit into it,
  15.4 KB estimated free, the level where sync had run out in 8.4.2. Now the fade is timed by screen (it has room),
  the narrow-window rule is two lines, strip no longer searches the contents for textures (screen keeps them), and it
  sends its parts in smaller batches: 17.2 KB. `tools/lslmem.py` warns under 17 KB (core and ui are near it).
- **The viewer's notices** (the chiclets at the top right) covered the strip's right end: it now ends 200 px from the
  edge (60 px on a 5:4 or 4:3 window, where there is no room for more).
- Every script is 8.5.1 (strip and screen change).

## 8.5.0 (the strip, redesigned: quiet, on the left)
- **The [12] at the far left; nothing in the middle.** The middle of the picture is the film's. The left: the [12],
  Auto's Orbit, the shots. The right, from the edge: the shutter, Connect, the frame, the running shot's options. Edge
  to edge, ultrawide too; on a narrow window the gaps give way.
- **Quiet:** 4 s after your last touch the strip fades away and only the [12] stays, at 60 %, like a camera's REC light.
  A tap on it brings the strip back (the menu is the next tap); a touch on the strip keeps it 4 s more. `/12 fade off`
  keeps it on screen.
- **Notes on a plate:** under the [12], on a dark plate sized to the text, readable on any picture (a new part,
  `t12 plate`: touch the builder in the HUD once, it adds only what is missing).
- **A finer strip:** a pure black band, 40 px; 12.5 px words; a smaller [12] (28 px, its ring 32); the Orbit and the
  shutter without their dividers (no hairlines anywhere). Upload `take12_marks_1024.png` again (the words are unchanged).
- **The Orbit held** hands the camera to your viewer and ends Auto, as a lit shot held does.
- The emulator: `llGetSubString`'s empty-end quirk, met again (a note's plate stayed). `tools/sim/fade_emu.py` (in CI);
  `layout_emu` checks the new places at every window, place and size.

## 8.4.4 (Auto: your Tracking look, the keys at once)
- **Auto films Tracking in your own look** (Shoulder, Film or Classic, and your side), the one you last chose by hand.
  It always used Film.
- **The walking keys switch Auto to Tracking at once** (held a quarter of a second, so a nudge is no walk). It waited
  for a full second of moving, checked twice a second. Moving without the keys (pushed, a slope) still waits 1 s.
- tracking changes; every script is 8.4.4.

## 8.4.3 (Connect never stays dead; walking in Portrait and Fixed is smooth)
- **sync stopped in-world with "Stack-Heap Collision"** after a few minutes beside a friend. A stopped script never
  starts again by itself, so Connect stayed dead until a new copy: and a friend whose sync had stopped never answers,
  which is the likely "Nobody near you wears Take 12." with them beside you.
- **The watchdog (carry):** every 5 s a stopped script is reset and started again. sync, started again while worn,
  rejoins the ones it was with at once. `/12 status`: carry names what it started again, sync names who it heard near.
- **More room for sync:** Connect's dialogs and Settings › Friends moved to carry (CONN 7349), which has room to spare.
- **Meeting:** a `here` from someone new is answered at once, so both HUDs know each other within a second; Connect
  lists from fresh answers only, and who has not said `here` for a minute is forgotten.
- **Walking in Portrait or Fixed is smooth.** The shot stepped a locked camera along with you four times a second,
  and Second Life does not ease a locked camera, so walking was choppy. Now, as you start walking, the shot hands over
  to the viewer's own follow camera from where it stands (its distance, height and side), eased every frame like
  Tracking and Drift; a second after you stop it settles into its framing, as before. portrait and fixed change.
- The emulator: a script can stop (`crash`), `llGetScriptState`, `llSetScriptState`, `llResetOtherScript`; scripts are
  in the contents. `tools/sim/watchdog_emu.py` (in CI). Every script is 8.4.3 (sync, carry, portrait and fixed change).

## 8.4.2 (the textures stay)
- **A new take12_marks dropped in lost its Orbit after a reset.** Screen kept the textures' UUIDs only in the [12]'s
  description, and the viewer's Edit window (open while you drop a texture in) can put the old description back. The
  scripts went on with the new marks until a reset, then read the old ones, which have no Orbit. Reproduced in the
  emulator (`tools/sim/textures_emu.py`).
- Now screen keeps them in Linkset Data, which only the scripts change, with a copy in the description for a new
  owner. It mends the description on every load, and writes both again after Settings › Reset › Everything or a new
  owner. The description holds only the two UUIDs, so words of its own can no longer cut one off at 127 characters.
- screen and strip change (and carry: a newer copy keeps its own textures); every script is 8.4.2. Drop take12_marks in once more after replacing them.

## 8.4.1 (the mark: TAKE (12))
- **The boards and the box say the name once.** The 8.2 boards set the [12] beside "TAKE 12", which read "12 TAKE 12".
  Now the [12] is the 12: the word TAKE and the HUD's own [12] (its disc and filming ring) make one lockup, quiet and
  centred on black, with one line: "Your Second Life, filmed." (the owner's pick of four directions). The Scenery
  boards: TAKE (12), SCENERY, "Free. The place, while you are away."
- The box: the lockup on the front (also the card on screen while the worn box unpacks), TAKE (12) up the sides, the
  [12] alone on the lid. Upload the three box textures again.
- Gone from the boards: the shot list (TRACKING · PORTRAIT · FIXED · SCENIC), the frame lines and the old 35 mm.
- **The box adopts its textures,** as the HUD does: it keeps their UUIDs in its description and takes the textures out
  of its contents (before, they stayed in, and were handed over or lost). `hud/box/unpack.lsl` only; no HUD script
  changes.
- **Mended:** the kept UUIDs were cut off. A description holds only 127 characters, and three `name uuid` entries come
  to about 160, so the lid's texture was lost. They are now `f <uuid>;s <uuid>;t <uuid>`. The box is also full bright,
  worn and rezzed. If your lid is blank, drop the top texture in again.

## 8.4.0 (Auto: the guide; the box you wear)
- **Auto was stuck in Portrait.** It waited for 2 s of walking and kept a shot 8 s, so walking a room in short steps
  never got past Portrait, and you watched yourself walk. Reproduced in the emulator (whose keys now give a walking
  speed, as in-world), then rewritten.
- **Auto: the guide** (docs/PRODUCT.md, the Read Me):
  - moving 1 s (the keys or your speed): Tracking, at once, from any shot and from an Alt-click's hold; nothing else
    while you move;
  - stopped alone: Tracking holds, then after 10 s Scenic Drift (its reveal);
  - 5 minutes still, or Away: Scenic wide, Far outdoors, Room indoors;
  - with 1-3 people within 3 m, still 4 s together: Portrait Us; 3 s after they leave, Drift again; a crowd: Drift;
  - sitting: Fixed where the seat has a kept view, otherwise Drift after 10 s;
  - a shot stays 8 s, except Tracking as you move. Auto's bands and options are never kept as yours.
  - In Auto, Settings › Idle start is off (Auto has its own resting steps).
  - `/12 debug on` says each pick and why; `/12 status` adds what Auto sees.
- **The box you wear:** Add it from the inventory and it shows as a card on the screen, hands over the folder
  `Take 12 8.4.0` and takes itself off. Rezzed, it is still the black box (a store display), touch to unpack. The
  maker wears it once on HUD Center before it goes on the Marketplace (hud/box/README.md).
- The tip for the Orbit says the guide in a line.
- Scripts changed: tracking (the director), scenic (Auto's band), core (no idle start in Auto), text (the tip); the
  rest only their version. Still twelve.
- Tests: `auto_emu.py` rewritten as a day by the guide (the stuck case first); `box_emu.py` worn; the emulator's
  keys walk with a speed; `llDetachFromAvatar`.

## 8.3.0 (Auto: the camera that directs itself)
- **Auto.** Wear Take 12 (once set up) and it picks the shot from what a script truly sees:
  - walking 2 s: Tracking (Film);
  - standing still 6 s: Portrait (Medium · Us: whoever is within 3 m, else you);
  - sitting: the seat's kept view (Fixed); a seat with none, the frame holds;
  - idle: Scenic, Drift's reveal (Settings › Idle start, as before);
  - flying, mouselook, a marked vehicle: your camera, as before.
  It is calm: at least 8 s a shot, and only once the reason has lasted 2 s, so a step or two never cuts. Its choices
  are not kept: your own Portrait size, Tracking look and Scenic band stay as you left them.
- **It never fights you.** Alt-click and it waits; walk off or press Esc and it goes on (Esc gives the shot back in
  Auto only). While you watch someone's film it waits too; your watchers see what it films.
- **The Orbit** at the strip's left end, the shutter's mirror: the shutter's ring with its dot out on the ring. Lit,
  the strip reads only the Orbit, the shot Auto chose in faint letters, the ▭, the [12], the rings and the shutter.
  Tap the faint shot (or `/12 tracking` and the like) and you direct: the shots and options come back. Tap the Orbit
  (or `/12 auto`) and Auto directs again. Every wear starts in Auto; the setup's last step starts it too.
- **A new part, `t12 auto`,** and two new cells on the marks texture (`auto`, `autoON`): upload
  `take12_marks_1024.png` again. Touch the builder in your HUD to add the part. A HUD without it still runs Auto,
  with the shot words shown.
- The director lives in `tracking.lsl` (core has no room); core only learns Auto's state and Esc. Still twelve
  scripts.
- **Mended:** the tour's Done now finishes the setup (it closed the dialog only, so the setup's end never ran).
- Tests: `auto_emu.py`, a day in Auto (walk, stop, steps, Us, a seat with and without a view, Alt-click and Esc, idle,
  flying, manual and back, an early pick on wear, Auto with Connect, a HUD without the part); the layout test in Auto
  at every window; the tests that direct by hand start manual.
- Version 8.3.0 in all twelve scripts (the free build: nine; the Orbit is dim there).

## 8.2.0 (Connect reworked; the viewer's lens stops; About; the box)
- **Connect:**
  - **Who is near is known.** Every Take 12 says "here" when worn and every 10 s, so Menu › Connect lists the people
    near you at once; no 1.5–3 s wait, and never a false "Nobody near you".
  - **Settings › Friends › Add** lists people who are connected already. In 8.1 it said "Nobody near you wears Take
    12" with the friend right there.
  - **Two friends connect by themselves** when near (each in the other's Friends list); quietly, with the chime.
    Someone who has you as a friend, but not the other way round, never makes a question pop up.
  - **One list, where everyone is:** `Ana · filming`, `Ben · watching your film`, `Cy · away`. Tap a name: Watch,
    Show my film (a friend watches at once, anyone else is asked), or My film.
  - **The shared view is smooth.** It stepped 4 times a second: a locked camera, which Second Life does not ease.
    Now the director's camera goes out about 7 times a second with their position, and the watcher's core moves the
    camera 20 times a second, eased between updates and carried with them. The watching camera moved from sync to
    core, which owns the camera.
  - **Mended:** presence no longer keeps a dropped link alive. A heartbeat from someone who thinks you are connected,
    when you are not, is answered with "bye".
  - **While you are alone,** the rings count the Take 12s near you, quietly.
- **The lens is one of the viewer's own zoom stops:** 21 · 26 · 32 · **38** · 47 · 56 mm (Ctrl+0 / Ctrl+8 / Ctrl+9).
  The classic 24 · 28 · 35 · 40 · 50 could not be reached with the keys. An earlier choice moves to the nearest stop.
  "Is your lens on" now matches within 5 %.
- **Help › About:** what 12 means. Also in the guide (ABOUT), the README and the listing's last line.
- **The box** (`hud/box/`): one black box that makes itself from three textures (`tools/art/make_box.py`). A touch
  hands its owner one folder: the HUD, the Read Me, and a Take 12 Scenery to give a friend. No menu.
- text: the `/12` commands help moved out of the notes table (its memory peak).
- Version 8.2.0 in all twelve scripts (the free build: nine).

## 8.1.0 (the shutter; Drift's reveal; Settings › Motion)
- **The shutter**, at the strip's right end, where a camera's shutter is.
  - Press it and the moment holds exactly as you see it (Tracking stops following, Drift stops), in your photo frame.
  - A note gives the snapshot size and Ctrl+Shift+S. Take your snapshot, then press it again (or tap the lit shot):
    the film goes on.
  - Alt-click still fine-tunes the held view.
- **The ▭ is the frame on screen.**
  - Filming, it shows the shot's cinema frame and its dialog lists only the cinema frames.
  - With the shutter open, it shows your photo frame (one for every shot, 3:2 to begin with) and lists only the photo
    frames: 3:2 · 4:3 · 1:1 · 4:5.
  - A photo frame chosen per shot in 8.0.9 becomes your photo frame; that shot goes back to its cinema frame.
- **Drift is the reveal:** close on you and held, then rising and pulling back over about 20 s to show the place,
  held wide, then a clean cut to a new close angle from another side. It stays near when people are around or indoors.
- **Settings › Motion** (it was Settings › Tracking):
  - Tracking: Smooth · Snappy.
  - Drift: Reveal · Breathe. Breathe is 8.0.6's in and out.
- **The frame dialog now lives in bars**, which frees room in ui. Settings › Frames & bars also opens your photo frame.
- The notes table is leaner (each note's kind is folded into its words), which keeps text's memory peak low.
- **One new part, `t12 shut`.** The builder adds it to an existing HUD: rez the HUD, drop the builder and a blank
  "t12 part" in, and touch it. The marks texture has two new cells: **upload it once more.**
- Version 8.1.0 in all twelve scripts (the free build: nine, with the shutter for Scenic).

## 8.0.10 (feedback by email; a clean copy for every new owner; the new boards)
- **Feedback, straight to the maker.** The [12]'s menu has Feedback while Take 12 is in beta (and `/12 feedback`):
  a text box, one line, Submit. It goes by email to the maker with one plain line about the copy (name, version,
  shot, frame, lens, window, region, date). One a minute, ten a day; an empty box sends nothing. The free build has it
  too. carry sends it (its 20 s email pause holds up nothing of the camera); no new script.
- **A new owner gets a new Take 12.** A copy given or sold already wiped everything of the last owner's, but the
  scripts that had read the settings before that wipe kept them: the buyer could see the seller's strip place and
  bars until they changed something. Every script now reads its settings again after the wipe.
- **The boards are cinema black:** a 2.39 frame as a monitor draws its frame lines, the [12], the name and one line.
  No drawn scenes. The listings say what 8.0.9 and 8.0.10 brought (frames, feedback).
- New tests: `owner_emu.py` (a copy goes from Ana to Ben) and `feedback_emu.py`.
- Version 8.0.10 in all twelve scripts (the free build: nine).

## 8.0.9 (every frame is a picture)
- **The ▭ on the strip opens this shot's frames**, from the widest to the tallest, the current one marked:
  2.39 · 2.00 · 1.85 · 1.66 · Full, and for Portrait, Fixed and Scenic the photo frames 3:2 · 4:3 · 1:1 · 4:5.
  Tracking keeps the cinema frames: a walking camera wants one. The dialog's line gives the snapshot size for the
  frame (e.g. "Snapshot 1920 × 1038 for 1.85", "1600 × 2000 for 4:5"), and stays open as you try them; Done closes it.
  It replaces the tap that turned the bars on and off (Full is that now, per shot; `/12 bars` still turns them all
  on and off).
- **A photo frame is a pillarbox** (bars at the sides); Portrait already composes in it.
- **In a photo frame Scenic's Drift holds still views**, ready for a picture; a cinema frame and it moves again.
- **Fixed: tapping the ▭ started Tracking** (since 8.0.0). The part is named `t12 shape`, and the strip read it as the
  first shot word `t12 s0`.
- The strip reads the new frames (`3:2`, `4:5` …): four new cells on `take12_marks`, after the others, which stay
  where they were. **Upload the new texture once.** A friend's photo-frame film reads by its frame's name too.
- Settings › Shapes & bars is now **Frames & bars**, opening the same dialog per shot.
- Version 8.0.9 in all twelve scripts (the free build: nine).

## 8.0.8 (classic lenses; Snappy by default; the [12] back to its size)
- **Settings › Lens: the classic primes, 24 · 28 · 35 · 40 · 50 mm, 35 by default** (it was 35 · 38 · 40, default 38),
  with a Done button (the page had no way out but Back or ignoring it).
  No 85 mm or longer: Take 12 is for living in Second Life on film, and portrait lenses are too tight for that.
- **Tracking is Snappy by default**, right behind you and easy to steer. The Tracking tip says where the smoother,
  steadicam feel is (Settings › Tracking).
- **The [12] is back to its size** (ring 50 px, meeting the band), which looked more like a button than 8.0.6's
  smaller one.
- Version 8.0.8 in all twelve scripts (the free build: nine).

## 8.0.7 (hold the lit shot: your viewer's camera)
- **Hold the lit shot word (0.8 s) and your viewer has the camera.** Its underline drains as you hold; the strip, the
  bars and Connect stay on. Tap any shot to take the camera back. A short tap on the lit shot is still its next view.
  It is the [12]'s own grammar one level down: hold the [12] for everything off, hold a shot for that shot off.
  Nothing new on the strip, and no new texture upload.
- The shot tips say it once ("Hold it: your viewer's camera."); a note says so when you do.
- **Connect, checked again:**
  - A friend who has just put the HUD on, and hasn't picked a shot, can be watched (her own camera). Before, she
    showed as "isn't filming" until she picked one.
  - While you are watched, your camera goes out 4 times a second (it was 2), straight to the watchers. Before, every
    update woke all twelve scripts of your HUD: about 58 script events a second while watched, now about 10.
  - A late camera update after you stop watching is ignored.
  - Connect's nearby list shows as soon as anyone answers (1.5 s); only when nobody has does it ask again and wait
    3 s.
- Version 8.0.7 in all twelve scripts (the free build: nine).

## 8.0.6 (tests with a friend: Connect shows her view; Drift smooth; Snappy Tracking)
From the user's list of reports, confirmed with them before any change:
- **Connect: you see exactly what she sees.** Only Take 12's own shots used to go out: her Alt-click framing, her
  own camera or an idle Drift left you on an old frame. Now her real camera goes out, four times a second while you
  watch (mouselook never). A watch lasts through 6 s of silence (3 s dropped it on a slow sim), and the "with you"
  note says to tap the rings. The [12]'s dot is bigger.
- **Settings › Friends › Add:** the nearby scan asks twice and waits 2.5 s ("Nobody near you" with a friend 2 m
  away). The Friends pages moved into sync, which handles Connect, so ui has room for the new settings.
- **Drift is smooth:** after its first cut it is the viewer's own follow camera, like Tracking, and it eases in and
  out every 15 s. Before, it moved a locked camera twice a second, which Second Life doesn't ease.
- **Room shows the room:** from just in from a wall (a corner when there is one), at eye height, level, looking
  across. No more high, tilted-down views.
- **Settings › Tracking: Smooth · Snappy.** Snappy stays right behind you and follows every turn, for anyone who
  finds the steadicam lag hard to walk with.
- **The setup asks "Is the whole strip in view?"** (Yes · Lower it), for viewers whose bars cover the top. Once it
  has been started or put off, it never starts again when you wear the HUD.
- **The [12] is smaller** (ring 41 px), so it sits inside the 48 px band.
- **Tips:** the outline round PORTRAIT or FIXED now explains itself the first times, FORGET SEAT and LET GO
  explain themselves when you sit, and after an Alt-click framing a tip says Esc gives the camera back.
- **Portrait Us:** with a wall on the camera's side, it tries the other side of the two of you first. A wall
  without physics stays invisible to every script.
- Version 8.0.6 in all twelve scripts (the free build: nine).

## 8.0.5 (Portrait reads your lens; notes you can read)
From the second in-world session, with screenshots ("the HUD is placed perfectly"):
- **Fixed: Portrait framed for the wrong lens.** It never asked for the permission Second Life needs before it reports
  your zoom, so it read 0 and framed every picture for the viewer's default 60°. At the setup's 38 mm lens the camera
  stood 1.8 times too close: Close showed lips and chin, Wide only the torso, Medium the face at the top right. (The
  lens step's mm reading worked, because another script reads it with the permission.) The emulator now answers
  `llGetCameraFOV` and `llGetCameraAspect` only with that permission, as Second Life does, so this cannot slip by again.
- **Fixed: an eye line above your reported height was thrown away.** With a mesh body or a hover height your eyes can
  sit above the top Second Life reports. Portrait and Tracking ignored such a value and aimed lower. They now accept it,
  and Wide keeps the whole head above it.
- **Notes sit lower,** clear of the [12], and stay 4 to 10 s depending on their length (3 s was too short). The eye
  line's instruction stays on screen until you keep or skip the line.
- **The strip is as you left it** when you wear the HUD again: open after the setup, unless you closed it.
- **Room shows up as you walk in:** Scenic looks again after 4 m (it was 10 m).
- Tracking still eases out of a wall it swings into, on purpose: stopping it hard would cost the smooth moves.
- `tools/sim/inworld_emu.py` replays this session too: 11 checks fail on 8.0.4, all pass on 8.0.5.
- Version 8.0.5 in all twelve scripts (the free build: nine).

## 8.0.4 (the first real session: readable words, the strip at the top, Portrait among bushes)
From the first in-world session of 8.0.3 (Tracking: "smooth, looks awesome"), with screenshots:
- **Fixed: the lit words were unreadable.**
  - The lit shot was ink on a white box. In-world it read as a black smudge. Now it is full white with a line under
    it, like a lit option.
  - A lit option showed a grey block over the lower half of its word. That was the underline part: 0.01 m (about 11 px,
    Second Life's smallest part), textured from a cell of the marks sheet. Every line (underlines and the eye line) is
    now a plain white face cut down to about 2 px with `PRIM_SLICE`.
  - No glow on the strip; it blurred the words.
  - No new texture upload is needed.
- **The strip sits at the very top, on a solid black band.**
  - Top had a 24 px gap above the strip; it is now flush with the top of the world view (Top lower: 52 px).
  - The band is solid black from the screen edge across the strip. Before, it faded and was see-through wherever a
    shape's bar is thinner than the strip (Portrait and Fixed's 1.85), unlike Tracking's 2.39.
- **Fixed: Portrait stood 1 m from you among bushes.**
  - It tried only the two soft 3/4 views; when something blocked both, the camera moved in to 1 m (Wide showed your
    torso, the head cut).
  - Now it also tries 60° either side and square-on, and takes the first with room for the whole shot.
  - The head is never cut.
  - `/12 debug on` now also shows each Portrait picture's numbers, including what blocked a view, in case a place still
    frames badly.
- **Fixed: "Camera control currently only supported for attachments and objects on which you are sitting."**
  - Walking into the next region in Tracking, the camera was cleared mid-move. Tracking's camera now follows you
    across by itself.
  - A teleport lets the old frame go a second later.
  - No camera call is ever made by a copy that is not worn.
- **After the setup the strip stays open**, so the controls are in view. The last tour page says a double-tap hides it.
- `tools/sim/inworld_emu.py` replays these too: on 8.0.3 it fails 12 checks, on 8.0.4 it passes.
- Version 8.0.4 in all twelve scripts (the free build: nine).

## 8.0.3 (the [12] answers every tap; the camera is never left locked)
From the first in-world use of 8.0.2:
- **Fixed: taps on the [12] were lost, so it took several tries (and up to half a minute) to get the dialog.**
  - The [12]'s ring sits just in front of the disc, and the strip's and bars' hidden parts are parked right behind it.
    A tap often landed on one of those, and only a tap on the disc itself counted.
  - Now a tap on any of them is a tap on the [12]. The hidden parts are also parked further back.
- **Fixed: the camera stayed fixed in front of you.** The setup's eye-line step holds the camera in front of you while
  you move the line. Walking did not end it, and neither did a teleport (you still saw your house) or a script reset.
  - Walking or turning now ends the step and keeps your old eye line; the setup goes on.
  - A teleport ends it too, and it ends by itself after 2 minutes.
  - When its scripts start (a reset, a new wear), Take 12 hands the camera back unless a shot is running.
  - The note says it: "Tap the [12] to keep it, or walk to skip."
- **Fixed: a dialog button pressed after a minute and a half did nothing.** Dialogs now listen for 10 minutes.
- New test `tools/sim/inworld_emu.py` (in CI) replays these reports; on 8.0.2 it fails, on 8.0.3 it passes.
- Version 8.0.3 in all twelve scripts (the free build: nine).

## 8.0.2 (screen split in two)
- **Fixed for good: `screen: Stack-Heap Collision` on save.** 8.0.1's screen still crashed in-world the moment it was saved. It was simply too big for Second Life's 64 KB, and the memory estimate had shown room that wasn't there.
  - It is now two scripts:
    - **screen:** the [12], its ring and dot, the notes, the eye line and the textures;
    - **strip:** the strip's band and words, the fade and the taps.
  - The strip's drawing is folded into one helper. Compared with the script that crashed, strip has half its list values and a fifth fewer tokens, which keeps it inside the size of `ui`, a script that runs fine in-world.
  - Each script carries only the texture cells it draws, and a cell lookup no longer copies the whole table.
- Twelve scripts now (the free build: nine). Version 8.0.2 in all of them.

## 8.0.1 (the strip no longer runs out of memory)
- **Fixed: `screen: Stack-Heap Collision`.** This was the first in-world report; "A Take 12 script is missing: screen" followed from it.
  - The strip was laid out as one list of about 460 values for every part, and while the list grew its old copy stayed alive too. That was far more than the script had room for.
  - It now goes out in small batches (about 60 values each): the same strip, a fraction of the memory.
- **The same kind of risk, removed elsewhere:**
  - **Portrait Us and Scenic's Drift** used to read the whole region's list of avatars (up to about 100 keys in a full club). They now ask a sensor (the nearest 16 within 10 m).
  - **Fixed** keeps its seat index as a string, not a list of 48 keys.
  - **Reset › Seats & views and the 7.x migration** delete settings ten at a time.
- **Fixed: a new copy that took over an old one's setup still offered the first-run setup.**
- **Memory is now measured where it runs out:**
  - The emulator notes the biggest list each script builds while running and answers `llGetFreeMemory` from it.
  - `tools/sim/memory_emu.py` (in CI) drives every script's heaviest moments and fails if any of them would leave less than 3 KB. On 8.0.0 it reproduces the in-world error: screen 9.5 KB short. Now every script keeps at least 8 KB.
  - The static estimate moved into `tools/lslmem.py`, shared by `tools/lslcheck.sh` and the emulator.
- Version 8.0.1 in all eleven scripts. Replace all of them in your HUD, and the free build's eight.

## 8.0.0 (a rebuild: the Monitor, four shots, two equal cameras)
7.2's in-world test showed the product did not work where it mattered:
- bad compositions when sitting, lying or cuddling;
- gimmicky Adjust and Show me;
- a zoom cutting to another shot;
- yesterday's text at login;
- inconsistent menus.

8.0 is the result of a long design review (`docs/PRODUCT.md`): directing is manual, and intelligence is kept only where a script can truly see.

**The look and the controls**
- **The Monitor:** a thin strip of small-caps words at the top of the screen (or the bottom), like a cinema camera's display:
  - the shots on the left, the running shot's options on the right;
  - in the middle, the bars key, the [12] and Connect.
  - Double-tap the [12] opens it with a quick fade. Tap: the setup dialog. Hold: everything off; hold again: back exactly.
  - The [12] shows a thin ring while filming, a white dot when connected, a soft glow when your film is shared, and amber for a problem.
  - Notes stay 3 s; tips come only the first three times.
  - Two textures and a builder script make the HUD (`hud/build/`).
- **A first-run setup:** your lens (with a live mm reading), your eye line (a line on screen, Page Up / Page Down), the strip's size, and a short tour.

**The shots**
- **Tracking** (Shoulder · Film · Classic, L · R): the viewer's own follow camera. A steadicam lag, never through a wall, a small room's corner.
- **Portrait** (Close · Medium · Wide, Me · Us): eye level, eyes on the upper third, a soft 3/4, lead room; two-shots and groups. A zoom keeps the framing; never a cut.
- **Fixed** (View A · B; Forget seat · Let go):
  - your own Alt-click framing, kept per place and per seat spot (48 pieces of furniture), and never replaced silently (Keep new);
  - marked vehicles let go.
- **Scenic** (Drift · Near · Room · Far): still frames about every 15 s or a slow drift, within 60 m. It is the idle camera.
- Each shot has its own shape (2.39, 1.85 …).
- Sitting holds the frame; Alt-click holds the shot; flying, mouselook and teleports are handled.

**Connect, copies, the free build**
- **Connect:** two equal cameras; one tap flips to your friend's film; friends join without asking. It rests beyond 20 m and rejoins. Only Take 12's shots are shared.
- **Two copies:** a new copy takes the setup over; the older steps aside.
- **The free Take 12 Scenery** has the same strip with Scenic, and can watch a friend's film.
- `/12` commands for gesture keys.

**Tested on the real scripts**
- The emulator (`tools/emu/`) now models prims, rays against builds, furniture, ground sits, teleports, parcels, several worn copies, and rezzing and linking.
- New tests run every window shape × place × size, every gesture and dialog, each shot's composition measured in the picture, Connect with a fuzzer, carry-over and the builder.
- Bugs they found before any in-world test:
  - Screen:
    - option taps went to the wrong word;
    - the THEIR FILM word overlapped the options on narrow windows;
    - the [12]'s dot showed only while someone filmed.
  - Portrait:
    - a float comparison made it see a wall that wasn't there (Wide lost its tilt);
    - lead room shrank the picture;
    - the two-shot leaned to the wrong side.
  - Fixed:
    - a new spot on the same seat went unnoticed;
    - views were stored too coarsely.
  - Core: framing with Alt-click counted as idle, so Scenic took over after 5 minutes.
  - Bars: an `llGetSubString` quirk kept a friend's shape after you stopped watching.
  - Tracking: a doorway hid a small room.
- `tools/lslcheck.sh` now fails a script under 15 KB free.

**Removed:**
- Framing (Me / Us / Friends), Freehand, Adjust, Show me, Format and the keys strip, replaced by the four shots and the strip;
- the Watch, since the free Take 12 Scenery can watch;
- the 7.x scripts, their sims, `docs/FRAME.md` and `docs/CALIBRATION.md`.

Version 8.0.0 in all eleven scripts.

## 7.2.0 (Show me, Scenery's own Format, a texture you just drop in)
- **Show me: where your face really is.** Second Life plays poses in each viewer, so no script can see where a body ended up on a bed or a sofa (nor can an attachment: it only reports where the avatar is anchored). Your camera can: tap > Show me, Alt-click your face, hold still, Alt-drag a little round it, hold still. Take 12 finds the face where the two views meet (to a few cm), keeps it per seat in your own frame (a turned bed turns it with you), and Me, Us and Friends frame that face, from the side it looks to, with the eyes on the golden line. Show me again redoes it; `/77 showme clear` forgets it. Views taken before you move the camera, and views that do not aim at one point near you, are never used (the emulator found the first case).
- **Scenery has its own Format** (Scenery > Format, off by default): the idle views no longer wear the shape you chose for your own shots, and the cameras that compose keep composing in yours.
- **Drop the keys texture in and forget it:** the strip keeps its UUID and the texture leaves the contents by itself, with one line in chat; only a texture you have full permissions on is adopted.
- **Tests on the real scripts:** `tools/sim/showme_emu.py` (a lying avatar, Alt-click and orbit, Me and Us framing the measured face, a turned bed, views that miss, clear) and `tools/sim/hud_emu.py` (the texture drop-in, mine and someone else's; the two Formats), in CI.
- friends.lsl: its unused trace lines are gone (memory for Show me). Version 7.2.0 in all fifteen scripts.

## 7.1.3 (Connect, debugged on the real scripts)
**An LSL emulator.** Our sims were Python ports of the scripts: they checked what we thought the code does. `tools/emu/` now runs the real `.lsl` files (LSL-PyOptimizer's parser and built-ins with LSL's own semantics, a region with avatars and worn HUDs, chat, link messages, timers, controls, the camera, permissions, Linkset Data). Pointed at old code it reproduces the two last field bugs exactly: 7.1.1's "someone is gone · disconnected" on a fresh HUD, and 7.1.0's Adjust walking you. `tools/sim/connect_emu.py` runs Connect scenarios on two and three HUDs and a Watch, then a fuzzer (random taps, holds, menu and panel choices, keys, Alt-orbits, restarts, lost messages) with invariants on what both sides believe; CI runs it on every push.
- **Found and fixed: a hub and a viewer at once.** With your Connect panel open, someone asked you to connect; you connected a third person from that panel and then said yes. You then held a connection and followed another, and the two sides disagreed about who was connected to whom. One role at a time now: joining someone ends the connection you held, connecting someone leaves the one you followed.
- **Found and fixed: a restarted HUD kept its friends hanging.** Reset Scripts (or a re-wear without taking it off) left everyone connected to it waiting for a time-out (25 to 45 s) on a HUD that no longer knew them. A restarting HUD (and Watch) now says so, and they let go at once.
- **For the next field test:** `/77 debug on` prints every Connect message sent and received, and each change of state, in your chat (off again after a reset). `/77 status` now shows who is connected and how long since each was heard from, who you follow and when you last heard from them, and the own-camera, nobody-films and looking-around states.
- Version 7.1.3; the Watch 6.8.2.

## 7.1.2 (start-up, Format through Connect, a HUD you can give away)
- **"Someone is gone · disconnected" at start-up:** in LSL an unset `key` is "", not NULL_KEY, so a fresh HUD thought it was watching someone (`gHost`) until its first real disconnect: the first camera start or the time-out then "disconnected" from nobody. The host (and the invitation) start as NULL_KEY now, in Take 12 and in the Watch (6.8.1). The same made tips hide the status line and the keys strip think you were watching, right after a reset.
- **Format through Connect:** since 7.1 the director's Format shows on every connected Take 12. It went out once (on joining and on a change); the director's heartbeat now carries it too, so a viewer whose message was lost, or who joined through a hand-over, has the right bars within 10 s.
- **A HUD you can give away:** the keys strip was textured from `take12_keys` in the contents, and an upload is usually no-transfer for the next owner, so the whole HUD became no-transfer. Now `keys` saves the texture's UUID in the strip's description while the texture is in the contents with your full permissions, and textures the strip by that UUID: wear it once, then delete `take12_keys` from the contents. `/77 status` says "texture saved". The README says what else must be transferable (the scripts and the Read Me).
- Version 7.1.2 in all fifteen scripts; the Watch 6.8.1.

## 7.1.1 (fixes from the first in-world test of 7.1)
- **Adjust walked you (the main bug):** a script holds ONE set of controls, and a second `llTakeControls` replaces the first. Core asked for all the movement keys, then for Page Up / Page Down alone, so only those two stayed taken: Adjust's W/A/S/D still walked you, and (since 7.0) Framing › Me never heard you walk, so it could not follow you. Core now makes one request, and `fit` keeps Page Up / Page Down from your avatar with its own (no jump while Fit is on).
- **Framing popped back** with "… is gone · disconnected": you were still connected to someone who had left, and the time-out cleared the camera you had just started. Leaving never clears your own running camera now, and starting a camera while the one you followed is silent disconnects at once, without the 25 s wait.
- **The Adjust help** stays 6 s, comes back once (4 s) after 15 s until you press a key, and the line above the button ends with "✛ Adjust" for as long as you adjust.
- **Format only when it matters:** the bars show while a camera runs, while you choose a Format, and while you follow a connected Format; with your own camera they go away. Your Format is kept and comes back with the next camera.
- **Bug hunt:** tapping Adjust while seated (where the keys always adjust) left Adjust on for when you stood up: it does not toggle while seated.
- Version 7.1.1 in all fifteen scripts. No new art.

## 7.1.0 (Adjust; Framing in one tap; Connect shares the Format)
**The keys either walk you or frame the shot.** In 7.0 Framing › Me let the keys walk you only, so nothing could fine-tune a shot, and a tilt was missing. 7.1 gives the keys two jobs and one clear switch.
- **Adjust:** seated, the keys always adjust the shot (you cannot walk anyway); standing they walk you, until you tap **ADJUST** (the keys strip, the live menu, `/77 adjust`); tap it again to walk. In Framing (Me, Us, Friends) and Freehand:
  - W / S (↑ / ↓) tilt the camera, A / D (← / →) swing it around you, Shift + A / D slide it sideways, Page Up / Page Down the height.
  - A tap is a small step (10 cm, 1°, 3°, 5 cm); hold for more, full speed after a second (60 cm/s, 15°/s, 45°/s, 50 cm/s). The first taps say "hold: faster".
  - In Me it stays until Full / Half / Close change or you stop, also while it recomposes after a walk. In Us and Friends adjusting holds that shot (no cut by time or by a speaker) until Next; the next one starts clean.
  - The height is still kept per seat (Fit). A camera swung behind a wall stays in front of it.
- **One rule, told once** (Read Me, tips): big moves with your viewer's camera (Alt + mouse) in Freehand or Friends; small corrections with Adjust.
- **Framing in one tap:** the Framing door starts the last one used (Me the first time); the live menu switches Me / Us / Friends (the running one has a dot) and has Adjust and the Friends list.
- **The menu does not repeat the keys:** with the keys strip linked, Next is left out of the live menu (the strip and the double-tap have it).
- **The keys strip:** FULL · HALF · CLOSE · ADJUST in Me, NEXT · ADJUST in Us and Friends, SAVE · VIEW A · VIEW B · STOP · ADJUST in Freehand. **Re-upload `hud/art/take12_keys_1024.png`** (new, 1024 × 1024) as `take12_keys`.
- **Connect shares the Format:** the bars of whoever films show on every connected Take 12, and your own come back when you leave. Lenses stay your own (the picture keeps its size); a note says once how to match theirs.
- **Fixes:** the Friends list's Back led to the welcome page (it opened a page that no longer existed): it goes back to the live menu. Seated W/S in Friends no longer step closer or wider (they adjust now; closer and wider are your zoom).
- **With Chat text on,** Adjust says the raw keys your viewer sends, to see what Shift + Page Down does in your viewer (no script sees Shift itself).
- **Scripts:** `fit` (Adjust), `core` (the keys, the trim on every shot, the held group shot), `ui`, `keys`, `tips`, `picker`, `sync`, `crop`, `lens`. Version 7.1.0 in all fifteen.

## 7.0.2 (UI review and debug)
**A professional pass over every screen, then a debugging pass.** Findings fixed:
- **One word for one thing:** the Pace page said "Still 120" next to a Slowest button (Still is gone), and "view" in one place, "shot" in another: now "shot" and "Slowest". Format's own menu and chat line still said Frame: now Format.
- **Marks mean something:** the quiet marks are now only on the doors, the cameras and the transport controls (Next, Stop, Save, Release, Connect); settings pages are plain words (they mixed marked and unmarked buttons on one page). The live menu's way back was "○ Cameras" (the Framing mark): now "☰ Menu". The dialog title no longer says "rolling".
- **No near-misses:** Connect's Disconnect had the × of Close next to it: now plain "Disconnect". Size's Back is "‹ Back" like every other.
- **Plain words:** "Test cam" is "Test camera"; Phantom says what it does ("see-through objects block the camera too").
- **Debug:** holding a connection with nobody filming, the NEXT key did nothing (core ignores next with no camera): it now films, like the double-tap. The Read Me said any movement key gives your camera back, but in Framing the keys walk you: corrected.
- **Version 7.0.2** in all fifteen scripts.

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
