# Take 12: the product (8.0)

The source of truth for what Take 12 is. How it is built: `docs/ARCHITECTURE.md`. Connect: `docs/CONNECT.md`. 8.0 is
a rebuild from a long design review (about 200 questions with the owner, after 7.2's in-world test); its outcome is
summarised here. 7.2 and earlier live in git history; v3 is frozen in `legacy/v3/`.

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
- Directing is manual: nothing switches shot by itself, except Scenic as the idle camera.

**The promise:** "I'm in a film." Everyday residents first, couples and friends next. Never a gimmick: a one-time setup is fine, rituals are not.

## The look: the Monitor
A cinema camera's on-screen display, as part of the viewer:
- **The strip:** one thin line of small-caps words at the top of the screen (Settings › Look › Place: Top, Top lower, Bottom, Bottom higher), on a soft dark band.
- **The words' places:** the shots sit on the left. The running shot's options sit on the right. In the middle are the bars key `▭ 2.39`, the [12], and Connect (two linked rings with a count, `SHARING` or `THEIR FILM`).
- **Lit states:** the lit shot is ink on a white box; a lit option is underlined; KEEP NEW and UNDO sit in an outline.
- **Room for other HUDs:** the words stay in a centred 16:9 area, 180 px in from its corners.
- **Size:** S, M or L; the strip is 48 px of a 1080 px window at M.
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

Wearing it: your own camera, Take 12 waits. First wear: a note "Tap the [12] to set up", and the first tap starts a one-minute setup, every step skippable:
- the lens: a cinema lens of 35, 38 or 40 mm, with a live mm reading;
- the eye line: a line on screen that Page Up / Page Down move onto your eyes, and a tap keeps it;
- "Easy to read?" (the strip's size);
- a three-page tour.

## The shots
Each shot remembers its options across logins; a tap on the lit shot does its one job.

| Shot | Options | What it is | The lit tap |
|---|---|---|---|
| **Tracking** | SHOULDER · FILM · CLASSIC, L · R | The viewer's own follow camera (1.6 m over a shoulder, 3.5 m a little low, 3 m from above), a steadicam lag, 30 % further when running. Walls pull it in; a small closed room (under ~4 × 4 m) gives its corner. Standing 5 s, PORTRAIT glows once. | Back into the look |
| **Portrait** | CLOSE · MEDIUM · WIDE, ME · US | You standing: a soft 3/4 at 30°, eye level, eyes on the upper third, lead room. Close is to the chest, Medium to the waist, Wide is all of you with the feet 5 % up. Us is the nearest 3 within 3 m: with one, a two-shot 20° toward your side; with 3–4, the open side of the group. A crowd (over 6 within 10 m) gets no people cuts. Walking, it follows then settles; turned away 2 s, a cut; a wall moves it in; a zoom keeps the framing. | The other side (a second tap crosses the 180° line) |
| **Fixed** | VIEW A · VIEW B; seated: FORGET SEAT · LET GO | Your own Alt-click framing: an empty view is kept after 1 s still. A kept one is replaced only by KEEP NEW (5 s), never silently. Views are kept per place (region + parcel) and per seat spot (furniture and position, in its frame), or per place + spot for ground sits; the least used of 48 pieces of furniture is forgotten. Walking off, the same angle on you. A zoom dollies. LET GO marks a vehicle (name + creator) and Take 12 lets go on it; TAKE BACK unmarks. | Back to the kept view |
| **Scenic** | DRIFT · NEAR · ROOM · FAR | Still frames cut about every 15 s, or Drift (the only moving one: close, out, back). Rays for open sight; within 60 m, inside the region, above ground and water; indoors every band stays in the room. Drift stays near when anyone is within 10 m. It is also the idle camera. | The next view now |

**Shapes:** each shot has its own: Tracking and Scenic 2.39, Portrait and Fixed 1.85 (Settings › Shapes & bars: 1.66 · 1.85 · 2.00 · 2.39 · Full). The bars are Black or Dimmed. The bars key turns them on or off for every shot (it is dim with your own camera).

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
- **Settings:** Lens · Eye line · Shapes & bars · Vehicles · Idle start · Friends · Look (place, size) · Reset (Tips again · Seats & views · Everything).
- **Commands** (`/12`, for gesture keys): tracking, portrait, fixed, scenic, bars, next, off, strip, connect, status, debug, blend, place, size, idle, flip.
- **Not in 8.0, kept for later:** a "Take 12 Lens" add-on (an always-on mm and aspect readout), light companions, other languages (every word is in `text.lsl`).
