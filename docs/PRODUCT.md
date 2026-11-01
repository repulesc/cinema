# Take 12: the product (8.0)

The source of truth for what Take 12 is. How it is built: `docs/ARCHITECTURE.md`. Connect: `docs/CONNECT.md`. 8.0 is
a rebuild from a long design review (about 200 questions with the owner, after 7.2's in-world test); its outcome is
summarised here. 7.2 and earlier live in git history; v3 is frozen in `legacy/v3/`.

## Scope
Take 12 is an experience: it inspires, with a few helpful tools. It never outweighs the freedom Second Life already
gives you; photographers frame with Alt-click, and that stays the heart of it.
- Your own framing always wins: Alt-click yields at once, and Fixed keeps what you framed.
- Nothing starts by itself, except Auto (8.3.0), which you can hand back with one tap, and Scenic when you are idle.
- No demos, no gimmicks, nothing that takes the wheel in the first minute.
- A feature earns its place only if it gives more freedom than it takes.

Considered and set aside (2026-10): end credits, `/12 action · cut · wrap`, golden-hour framing, a first-minute demo.

## Why 8.0
7.2 failed where it mattered:
- the compositions were bad when sitting, lying or cuddling;
- Adjust and Show me were gimmicks;
- a zoom cut to another shot;
- yesterday's text showed at login;
- the menus were inconsistent.

The facts we design around:
- A script cannot see a pose (animations play in each viewer).
- A script can see the avatar's position and size, a seat, walls (rays), the camera, and the lens.
- **Intelligence is kept only where a script truly sees:** standing (Portrait), walking (Tracking, with rays) and places (Scenic). Poses get your own framing (Fixed).
- Directing: Auto (8.3.0) picks the shot from what a script truly sees; one tap and it is manual. In manual nothing
  switches shot by itself, except Scenic as the idle camera.

**The promise:** "I'm in a film." Everyday residents first, couples and friends next. Never a gimmick: a one-time setup is fine, rituals are not.

## The look: the Monitor
A cinema camera's on-screen display, as part of the viewer:
- **The strip:** one thin line of small-caps words at the top of the screen (Settings › Screen › Place: Top, Top lower, Bottom, Bottom higher; Move in, Move out), on a pure black band, edge to edge.
- **The words' places (8.5.6, as in 8.4.4):** the [12] in the middle, the frame `▭ 2.39` just left of it and Connect (two linked rings with a count, `SHARING` or `THEIR FILM`) just right of it. The shots, with Auto's Orbit, from the left; the shutter at the right, the running shot's options before it. Every button stays in its place; changing shot changes only the options. The right 200 px stay free for the viewer's notices; closed (a double-tap), only the [12] is left.
- **It stays (8.5.3):** the strip never hides by itself; a double-tap on the [12] hides it and brings it back. (8.5.0's fade after 4 s untouched was taken out: it hid the strip while you worked.)
- **Notes (8.5.0):** under the [12], on a dark plate, readable on any picture.
- **Lit states:** the lit shot is ink on a white box; a lit option is underlined; KEEP NEW and UNDO sit in an outline.
- **Size:** S, M or L; the strip is 40 px of a 1080 px window at M, its words 12.5 px.
- **Opening:** the strip opens and closes with a 0.2 s fade. Closed, only the [12] stays.
- **The [12]:** a round dark disc:
  - a thin ring while filming;
  - a white dot while connected;
  - a soft white glow while someone watches your film;
  - amber for a problem;
  - it fills as you hold.

  No red, no "on air", no wordmark on screen.
- **Notes:** a 3 s line under the strip, in Second Life's own floating text. Important ones also go to your chat.
- **Tips:** each key's first three uses.
- **The voice:** calm, short, second person, no exclamation marks.

## The gestures
| Gesture | Does |
|---|---|
| Tap | The dialog, 0.35 s later (setup only: Connect · Settings · Help) |
| Double-tap | The strip opens or closes |
| Hold 0.8 s | Everything off (camera, bars, strip, Connect); hold again: back exactly as it was |

Wearing it: your own camera for 3 s, then Auto (once set up; the setup's last step starts it too). First wear: a note "Tap the [12] to set up", and the first tap starts a one-minute setup, every step skippable:
- the lens: one of the viewer's own zoom stops, 21 · 26 · 32 · 38 (default) · 47 · 56 mm, with a live mm reading (8.2.0: the classic 24 · 28 · 35 · 40 · 50 could not be reached with the zoom keys);
- the eye line: a line on screen that Page Up / Page Down move onto your eyes, and a tap keeps it;
- "Easy to read?" (the strip's size);
- the guide card (8.8.0): the strip drawn whole, a number under each key and one line for each; a tap closes it, and
  Help › Guide or `/12 guide` shows it again. (Without its texture, as in the free build: three short tour pages.)

## Auto (8.3.0; the guide, 8.4.0)
The camera that directs itself, for the everyday: you need not think about shots at all.
- **The sign:** the Orbit, at the strip's left end: the shutter's ring with its dot out on the ring. The shutter holds
  still (its dot in the middle); Auto moves (the dot riding round you). Lit while Auto directs; quiet when you do.
- **The strip in Auto:** the Orbit, the shot it chose in faint letters, the ▭, the [12], the rings, the shutter.
  No options: nothing to choose.

**Auto: the guide.** Only what a script truly sees: moving, standing still, sitting, someone within 3 m, Away.

| You | Auto films | After |
|---|---|---|
| **Moving** (walking, running: the keys or your speed) | **Tracking** (your own look and side; Smooth or Snappy as set) | the walking keys at once (held 0.25 s), otherwise 1 s of moving, from any shot, and from an Alt-click's hold (walking off). Never anything else while you move. |
| **Stopped, alone** | Tracking holds behind you, then **Scenic · Drift** (its glide round you, or the reveal) | 10 s still |
| **Still a long while, alone**, or Away | **Scenic · Far** outdoors, **Scenic · Room** indoors: the place, wide | 5 min still (Away: as soon as the shot has had its 8 s) |
| **Stopped with someone** (1–3 people within 3 m: a conversation) | **Portrait · Us**, Medium (a two-shot; a group of 3–4) | 4 s still together; it holds while they stay; 3 s after they leave, the rows above |
| **A crowd** (more than 3 within 3 m) | Scenic · Drift (it stays near when people are around) | 10 s |
| **Sitting** | **Fixed** where the seat has a view you kept; otherwise **Scenic · Drift** | 2 s seated (Drift: 10 s) |
| **Flying, mouselook, a marked vehicle** | your own camera | as in manual |

- **Calm:** a shot stays at least 8 s, except Tracking as you move, which comes at once. A key tapped (under 1 s)
  is not a walk.
- **Your Alt-click wins:** Auto waits; Esc or walking off gives Auto the camera back. While you watch someone's
  film it waits too.
- **Its choices are not kept:** your own Tracking look, Portrait size and Scenic band stay as you left them.
- **Settings › Idle start** is for manual; Auto has its own resting steps.
- **Manual:** tap the faint shot, or `/12 tracking` and the like: that shot goes on, the four shots and their options
  come back, and nothing switches by itself. Tap the Orbit (or `/12 auto`) and Auto directs again. Each wear starts
  in Auto.
- **Why (8.4.0):** 8.3.0 waited 2 s of walking and kept a shot 8 s, so walking a room in short steps left you in
  Portrait, watching yourself walk. Portrait is now for company only; resting is Scenic's.
- Not in the free Take 12 Scenery (the Orbit is dim there).

## The shots
Each shot remembers its options across logins; a tap on the lit shot does its one job.

| Shot | Options | What it is | The lit tap |
|---|---|---|---|
| **Tracking** | SHOULDER · FILM · CLASSIC, L · R | The viewer's own follow camera (1.6 m over a shoulder, 3.5 m a little low, 3 m from above), a steadicam lag, 30 % further when running. Walls pull it in; a small closed room (under ~4 × 4 m) gives its corner. Standing 5 s, PORTRAIT glows once. | Back into the look |
| **Portrait** | CLOSE · MEDIUM · WIDE, ME · US | You standing: a soft 3/4 at 30°, eye level, eyes on the upper third, lead room. Close is to the chest, Medium to the waist, Wide is all of you with the feet 5 % up. Us is the nearest 3 within 3 m: with one, a two-shot 20° toward your side; with 3–4, the open side of the group. A crowd (over 6 within 10 m) gets no people cuts. Walking, it follows then settles; turned away 2 s, a cut; a wall moves it in; a zoom keeps the framing. | The other side (a second tap crosses the 180° line) |
| **Fixed** | VIEW A · VIEW B; seated: FORGET SEAT · LET GO | Your own Alt-click framing: an empty view is kept after 1 s still. A kept one is replaced only by KEEP NEW (5 s), never silently. Views are kept per place (region + parcel) and per seat spot (furniture and position, in its frame), or per place + spot for ground sits; the least used of 48 pieces of furniture is forgotten. Walking off, the same angle on you. A zoom dollies. LET GO marks a vehicle (name + creator) and Take 12 lets go on it; TAKE BACK unmarks. | Back to the kept view |
| **Scenic** | DRIFT · NEAR · ROOM · FAR | Still frames cut about every 15 s, or Drift (the only moving one: the glide, close on you then sliding slowly round you at eye height, a cut to a new close; Settings › Motion › Reveal: rising and pulling back, held wide; 8.7.0). Rays for open sight; within 60 m, inside the region, above ground and water; indoors every band stays in the room. Drift stays near when anyone is within 10 m. It is also the idle camera. | The next view now |

**Frames and the shutter (every frame is a picture, 8.0.9; the shutter, 8.1.0):**
- **The cinema frame:** one for the whole film, every shot (2.39 by default), so the bars never jump when the shot changes (8.5.9). The photo frame shows only while the shutter is open.
- **Auto:** the shot it chose sits next to the Orbit, the other shots hidden.
- **The frame key `▭`** always shows, and edits, the frame on screen.
  - Filming, its dialog lists the cinema frames, widest first: 2.39 · 2.00 · 1.85 · 1.66, and Full (no bars).
  - With the shutter open, it lists the photo frames: 3:2 · 4:3 · 1:1 · 4:5.
  - Each dialog gives the snapshot size.
- **The shutter**, at the right end, is the photographer's key.
  - Press it and the moment holds exactly as it is, in your photo frame: one for every shot, 3:2 to begin with, a
    pillarbox.
  - A note gives the snapshot size and Ctrl+Shift+S. Pressing it again (or tapping the lit shot) lets the film go on.
  - A script cannot take the snapshot, so it never pretends to.
- **The bars** are Black or Dimmed; `/12 bars` turns them off for every shot. The key and the shutter are dim with
  your own camera.

## Around the shots
- **Sitting:** the shot holds its frame and FIXED glows once. Standing up resumes it; from Fixed, standing up goes back to the shot you had before you sat.
- **Alt-click:** the shot is held: the lit word dims, nothing is shared. A movement key or the lit tap gives it back.
- **Flying, mouselook, a marked vehicle:** your camera; it comes back as it was.
- **Teleport or region crossing:** the same shot, a fresh frame after about 2 s.
- **Idle** (Settings › Idle start: Off · Away · 5 min): Scenic starts by itself; a key or typing brings back your shot. Framing your own camera counts as activity.
- **A zoom:** never a cut.

## Connect
Two equal cameras: each films their own shot, and anyone connected can watch anyone's film. With one other person the Connect key flips; with more it opens the names. Friends join without being asked. It rests beyond 20 m and comes back by itself; it ends after 30 min apart, on Leave, or on a hold. Only Take 12's shots are shared. Details: `docs/CONNECT.md`.

## Two copies, the free build, settings
- **A new copy** worn while the old one is on takes the setup over ("Moved. You can take off the old one."). **Two set-up copies:** the older steps aside (amber). A 7.x copy cannot be seen; the guide says to take it off.
- **Take 12 Scenery (free):** the same strip, Scenic only; Tracking, Portrait and Fixed are dim ("In the full Take 12."). It can watch a friend's film, never film for others.
- **Settings:** Lens · Eye line · Camera (Lens · Eye line · Motion: Tracking Smooth / Snappy, Drift Glide / Reveal · Idle start · Seats) · Screen (Frames & bars · Place · Move in / out · size) · Reset (Tips again · Seats & views · Everything).
- **Commands** (`/12`, for gesture keys): auto, tracking, portrait, fixed, scenic, bars, next, off, strip, connect, status, debug, blend, place, size, idle, flip.
- **Not in 8.0, kept for later:** a "Take 12 Lens" add-on (an always-on mm and aspect readout), light companions, other languages (every word is in `text.lsl`).
