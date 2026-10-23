# Take 12: Product Spec (v4)

> **7.0 note:** the product is now one menu with six doors: Framing (Me · Us · Friends), Freehand, Connect, Scenery, Format, Settings (see README and the Read Me). Personal, Social, Friends, Frame and Still below are the v4–6 names; Photo hold and favourite spots were removed in 7.0. This spec is kept for its reasoning.

This is the source of truth for what the v4 HUD is. v3.0.0 is frozen and working in `legacy/v3/`. The older people-centred versions are in `legacy/v1-v2/`. The quiz answers this spec is built from are at the bottom.

## The idea in one paragraph
Take 12 is a tiny, fun-looking one-button Second Life camera HUD that shows you your world from beyond your avatar's back. It moves the camera by itself to where a camera operator would put it, and gives it back with any movement key; it records nothing. Its **default job is the scenery camera**. When you go idle, or double-tap the button, your view leaves your avatar and cuts between still, grand views of the place you are in. Those are high drone views and wide eye-level views, up to about 100 m away, with nothing blocking the view, held long and calm. In a skybox or another enclosed sky build, it can stay **inside the room** instead. Three optional cameras are a tap away in a clean emoji menu, and AFK never starts them:
- **Personal** follows you.
- **Social** frames you with the people around you, cutting to whoever speaks.
- **Friends** keeps you and your chosen friends in frame, gliding gently.

A movement key, a tap or typing gives your camera back.

**Design rules for every decision:** static, contemplative, minimal, nothing gimmicky, and nothing the user has to babysit.

## Principles
A guide for every feature, not ad copy.
1. **It decides; you accept or skip.** Take 12 chooses the view. Your part is a double-tap at most.
2. **Calm.** Long holds, few cuts, a quiet chat, a small button that stays still with your own camera (6.0: a tiny clap now and then while filming).
3. **No settings on screen.** No numbers, no jargon. Details live in the Read Me.
4. **One button.** Everything else is optional.
5. **Restraint.** A feature earns its place by making the experience easier, not by being a feature.

The tone of every text follows the product: plain, understated, no slogans. Think of a good point-and-shoot camera: it works well and says little.

## The button
| Look | Value |
|---|---|
| Icon | A **deliberately pixel-art clapperboard**: 16×16, a few colours with a dark 1 px outline, fun rather than serious. The textures are in `hud/art/`; "Rec" is the default |
| Size and place | About 40 px, **top right** by default. You can move it like any HUD |
| Feedback | **A tiny clap while filming (6.0).** The button is the plain logo at full strength. While a camera runs, `tips` shows the sheet's clapped frame for a quarter second when it starts and then every 8–12 s; with your own camera, in Photo and in a pause it is still. (4.7 removed the 40 % fade, which washed the small icon out on busy scenes; HUDs are not in snapshots anyway.) |

## Gestures
| Gesture | Idle | Rolling | Photo hold |
|---|---|---|---|
| **Tap** | Open the **menu** | **Stop**, your camera is back | **Resume** rolling |
| **Double-tap** (two taps ≤ 0.35 s apart) | Start **Scenery** | **Next** shot now | Next shot now (and resume) |
| **Long press** (≥ 0.8 s) | Open the **menu** | Open the **live menu** | Open the live menu |

- A single tap acts 0.35 s after release. That short wait is how a double-tap is told apart from a single tap.
- AFK starts **Scenery only**.

## Menu
- The standard Second Life dialog with **emoji buttons** and a **status line** at the top.
- Options › Emoji switches to a **text-only** fallback for viewers that cannot show emoji. The labels are the same, without the icons.
- Buttons are listed below in reading order: top row first, left to right.

### Main (tap while idle, or 🎬 Modes from the live menu)
```
🎬 Cinema · idle                     ← or "Scenery rolling", "Friends rolling", …
Pace: Calm (60 s) · AFK: 3 min + mouse check · Indoors: auto

[🏞 Scenery ][🚶 Personal][👥 Social ]
[💞 Friends ][⏳ Pace    ][💤 AFK    ]
[⚙ Options ][❔ Help    ][✖ Close   ]
```
- Picking a mode while another one is rolling switches to it straight away.

### Live (long press while rolling)
```
🎬 Cinema · Scenery rolling · next cut in 42 s

[📷 Photo   ][⭐ Save    ][⏭ Next    ]
[⏹ Stop    ][🎬 Modes   ][✖ Close   ]
```
- 📷 Photo shows as **▶ Resume** while frozen.
- ⭐ Save shows only in Scenery.

### ⏳ Pace
Applies to **all** cameras (4.4.3). Scenery holds a view for the full Pace time. Personal, Social and Friends hold a shot for about 75 % of it (Calm: about 45 s, a group tableau about 55 s), and they hold longer when Pace is slower.
```
How long each view is held. Now: Calm, about 60 s

[⚡ Lively ][🙂 Easy   ][🍃 Calm   ]
[🌙 Slow   ][🗿 Still  ][↩ Back   ]
```
- The values are Lively 30 s, Easy 45 s, **Calm 60 s (default)**, Slow 90 s and Still 120 s, each ±25 %.
- The current choice is marked with ✓ in the text line.

### 💤 AFK
`[Off][1 min][90 s] [2 min][3 min][5 min] [10 min][Mouse check][↩ Back]`. The default is 3 min with the mouse check on: no keys, typing or camera moves for that long, **and** the viewer reports you Away (the viewer clears Away on any mouse movement; a script cannot see the mouse). Once Scenery runs, only a movement key, typing or a tap ends it. AFK starts Scenery only.

### 💞 Friends
```
💞 Friends · 3 saved · 2 here now
Ana, Bo, Kit

[▶ Start   ][➕ Pick    ][➖ Remove ]
[🗑 Clear  ][↩ Back    ][✖ Close   ]
```
- **➕ Pick** opens the **picker**: up to 9 avatars within 20 m, nearest first, one button each.
  - A saved friend is shown as `✓ name`. Tapping a name toggles it.
  - The picker re-opens after each toggle, until you press Done.
  - If more than 9 avatars are in range, ▶ More shows the next page.
- **➖ Remove** lists every saved friend (here or not); tap a name to remove just that person.
- Up to **10 friends** can be saved, stored in the HUD. A script cannot read your SL friends list.

### ⚙ Options
```
[🏠 Indoors ][💬 Chat cuts][⭐ Favourites]
[👁 Alt-cam ][🧱 Phantom ][📏 Reach   ]
[📝 Chat text][🎨 Look    ][🪑 Seated view]
[🧪 Test cam][♻ Reset   ][↩ Back    ]
```
| Option | Choices (default first) | What it does |
|---|---|---|
| 🏠 Indoors | **Auto** / Inside / Outside | Where Scenery puts the camera when you are enclosed (see Scenery) |
| 💬 Chat cuts | **On** / Off | Social and Friends cut to whoever speaks in local chat |
| ⭐ Favourites | Clear here / Clear all | Saved Scenery spots of this region |
| 👁 Alt-cam | **Pause** / End / Ignore | What happens when you Alt-orbit during a shot |
| 🧱 Phantom | **Off** / On | Rays treat phantom objects as walls |
| 🪑 Seated view | **Auto (45°)** / Higher (60°) / Lower (30°) / Off | While you are seated or lying down, Social, Personal and Friends place the camera above you, looking down at that angle (same fitting of everyone). Indoors the ceiling caps it; sitting or standing up brings a calm re-frame. Stored as `seat_deg` (0 = off) |
| 📏 Reach | 50 / **100** / 150 / 200 m / Re-learn | The furthest Scenery camera distance (the nearest is always 20 m). If your viewer really holds the camera closer (it stops short at the same distance twice), the HUD lowers it by itself and slowly grows it back up to your choice. Orbiting, Alt-cam, mouselook or a minimised viewer never lower it. Re-learn goes back to your choice |
| 📝 Chat text | On / **Off** | Chat feedback. **Off by default**: the HUD says nothing in chat, except errors, warnings and the answers to commands you type. On: one line per cut (with what it found and why), and a line after each menu choice. The setting is stored as `trace` |
| 🎨 Look | **Classic** / **Rec** (default) / **Viewfinder**; plus 🔤 Emoji (**On** / Off) | The button picture, how visible it stays while the camera rolls, and emoji on the menu buttons |
| 🧪 Test cam | – | 3 s camera test (the old `grab`) |
| ♻ Reset | – | All settings to defaults (asks first) |

The v3 "Cut mode" option is dropped from the menu. It stays as the `/77 cutmode on|off` command for anyone whose viewer glides on cuts.

### ❔ Help
Gives the Read Me notecard and prints a 4-line gesture summary in chat.

## Modes

### 1. 🏞 Scenery: the default
- **Starts:** AFK (default 3 min + mouse check), a **double-tap**, the menu, or `/77 scenery`.
- **Looks at:** the place, mostly landscape, sky and horizon. You may be tiny in the frame or absent. People are ignored.
- **Outdoors (unchanged from v3):**
  - A mix of **high drone views**, 10–30 m above the topmost surface, 20 m up to the reach away, tilted 10–40° down over your area.
  - **Wide eye-level views**, 2.5–4 m up, level along the horizon.
  - Nothing may block the view. Every new spot comes from a clearly different direction.
  - The camera stays inside your region.
- **Indoors (reworked in 4.4.0, rules refined in 4.4.1):** the HUD judges a place by the **floor under you**, the one surface that always has physics because people walk on it. Walls, ceilings and windows are often built without physics, and rays pass through them, so they are only used when they can be seen.

  | Where you are | Auto | Indoors = Inside | Indoors = Outside |
  |---|---|---|---|
  | **On a build in the sky:** skybox, sky mall, sky club, sky deck (no land within 100 m under you) | **inside** | inside | outdoor views |
  | **On a build on the ground, with a roof over you:** a house, a shop, a trailer, a roofed mall | **inside** (4.4.1) | inside | outdoor views |
  | **On a build on the ground, no roof:** a plaza, a deck, a pier | outdoor views | inside | outdoor views |
  | **On the land, in the open** | outdoor views | inside, near you (an override) | outdoor views |
  | A build whose floor, walls and roof all have **no physics** (rays see nothing) | outdoor views (nothing to detect) | inside, near you | outdoor views |

  - **Auto does not flip.** Once it decides you are inside, it stays inside until you are clearly outdoors (no build floor and no roof) or 30 m away from where it last confirmed it.
  - **Indoors = Inside is a real override.** If you choose it, it stays inside even where nothing can be detected: the camera then stays within 12–20 m of you at eye height or under the ceiling.
  - **Inside views**, mixed: **high** (under the ceiling, looking down across your area), **eye level** (looking back across your area), **you small** (from across the space).
  - Every inside camera passes four checks:
    1. A clear line from your eye, with 0.5 m to spare.
    2. **Your floor under it**, and the camera within the outline of your floor. This works even where walls have no physics, and it keeps the camera on your storey.
    3. Head room.
    4. A view that reaches past you.
  - The camera stays under the ceiling. If the ceiling can't be seen, it stays about 3.4 m above the floor. It also stays within 12 m of you, or 20 m in a big open hall.
  - **Never outside while inside:** if no spot passes, it tries closer spots, then a close shot from just behind you. It never cuts to a view from outside.
  - In a busy region that refuses some rays, it skips those spots, tries again shortly, and measures the place again on the next cut.
- **⭐ Favourite spots (new):**
  - Long press › ⭐ Save stores the view on screen as a favourite for this region (up to 8 per region).
  - Scenery mixes one in about every 4th cut, when it is within reach and was not the last one used.
- **Motion:** static, then a hard cut.
- **Pace:** the Pace setting, default 60 s ±25 %.
- **Exits:** any movement key, tap, typing, sitting down or standing up.

### 2. 🚶 Personal: optional
- **Starts:** the menu or `/77 personal`.
- Composed static shots of **you** (eye line on the upper third, lead room). They follow you as you walk: when you leave the frame or move more than about 4 m, it cuts to a new shot. Unchanged from v3.
- **Exits:** tap or typing. Movement keys don't exit, because it follows you.

### 3. 👥 Social: optional
- **Starts:** the menu or `/77 social`.
- **Shots:**
  - With one person near you: over-the-shoulder pairs, shot and reverse shot.
  - With two or more within 8 m: a group tableau.
  - With nobody near: Personal-style shots and a one-time note.
- **💬 Chat cuts (new, on by default):**
  - When someone within 8 m speaks in local chat, the camera cuts to them over the shoulder of the person nearest them.
  - When **you** start typing, it cuts to you.
  - A cut waits at least 15 s at Calm (a quarter of Pace, never under 12 s), and the same person is not cut to again within 30 s, so a fast chat does not flicker. A speaker shot lasts about 18 s.
- **Exits:** tap. **Typing does not exit Social**, because you are part of the scene. Movement keys don't exit either.

### 4. 💞 Friends: optional (new)
- **Starts:** the menu (💞 Friends › ▶ Start) or `/77 friends`.
- **Frames** you plus every saved friend who is within 30 m right now. Friends who arrive join at the next cut. With no friends present it behaves like Personal and says so once.
- **Motion:** the only mode that moves.
  - While everyone is in the frame, the camera **glides slowly** to keep the group well framed. It moves over about 1.5 s, and only when the group has really moved.
  - If anyone stays out of the frame for about **1 s**, it **hard-cuts** to a wider shot that holds everyone, up to 25 m away. If that is not enough, it frames the friends nearest to you.
  - About every 45 s at Calm (75 % of Pace) it cuts to a fresh angle, so the shot does not go stale.
- **💬 Chat cuts:** the same as Social, but only for you and your friends.
- **Exits:** tap. Typing and movement keys do not exit.

### 5. 🖼 Frame: optional (4.6)
A held, well-composed view for your own snapshots: of you, or of you and whoever stands within about 3 m (chosen automatically). Three framings, Full length → Half length → Close (double-tap = next). The movement keys nudge it; the camera never moves by itself. The framing's name shows for 3 s, then the screen is clean. Spec: `docs/FRAME.md`. A fuller version (more subjects, landscapes, photo shapes, lens guidance) is kept in `lab/` for a possible later composition tool.

## 📷 Photo hold (all modes)
- Long press › 📷 Photo freezes the current shot **indefinitely**. No cuts and no re-framing; Friends stops gliding.
- Take your snapshots in peace.
- **Tap** resumes the camera; **double-tap** resumes with a new shot.
- The mode's own exits still work (for example, a movement key in Scenery).

## Exits and pauses at a glance
| Event | Scenery | Personal | Social | Friends |
|---|---|---|---|---|
| Tap | stop | stop | stop | stop |
| Movement key | **stop** | follow | follow | follow |
| Start typing | **stop** | **stop** | cut to you | cut to you |
| Sit or stand | stop | – | – | – |
| Alt-cam orbit | pause (option) | pause | pause | pause |
| Mouselook, teleport | pause, then resume | pause, then resume | pause, then resume | pause, then resume |

## Chat commands (channel 77, changeable)
- `scenery` · `personal` · `social` · `friends` · `stop` · `next` · `photo` · `fav` · `menu` · `status` · `grab`
- `pace <s>` (the old `hold <s>` still works)
- `reach <m>|relearn` · `indoors auto|inside|outside`
- `friend list|clear` · `trace on|off` (Chat text) · `emoji on|off` · `cutmode on|off` · `chan <n>` · `reset`

## Vibe
Grand views, calm pacing. The feel is still, long, contemplative views, as if a calm camera operator placed your camera on a drone, in a corner of the room, or over a friend's shoulder. The only motion in the whole product is Friends' slow glide, which keeps your group together.

## Explicitly not doing (by choice)
- Letterbox bars and dip-to-black. Tested in the quiz: not wanted.
- Pans, orbits, shakes, "cinematic" moves, presets and style packs.
- Window or door shots indoors.
- Multi-button HUDs or a big panel. One small button stays.
- Anything that needs the user's supervision to look good.

## Quiz answers this spec is built from
### Round 3 (v4)
| Topic | Answer |
|---|---|
| Idle tap / double-tap | Tap = menu, double-tap = Scenery |
| Rolling taps | Tap stops, double-tap skips |
| Long press | Live menu |
| Menu style | SL dialog with emoji |
| Main page | Modes plus quick settings, 9 buttons |
| Button look | Pixel-art clapper, fun, avoid clichés |
| Hide while rolling | Fade to about 15 % |
| On-air feedback | None, the view is enough |
| Size and place | Top right, about 40 px |
| Friends | Own mode; pick from nearby; glide and snap after 1 s; frame who's here |
| Indoors | Auto plus override; corner, centre, you small |
| New features | Photo hold, Favourite spots, Chat-aware Social |
| Typing in Social and Friends | Keep rolling, cut to you |
| Photo hold release | Tap resumes |
| Repo | v3 frozen in `legacy/v3/`, v4 in `hud/` |
| Delivery | Everything at once |

### Round 2 (v3, still in force)
Landscape, you tiny or absent · mix of drone and eye-level · up to about 100 m · static then a hard cut · nothing blocking, open sky · indoors on the ground: above the roof · stay in the region · contemplative holds · AFK plus a gesture · grand views, calm pacing.
