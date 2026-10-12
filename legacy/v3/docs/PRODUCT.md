# Cinema HUD: Product Spec (v3)

This is the source of truth for what the HUD is. Earlier versions misread the idea: they made people the centre of everything, and the scenery camera never existed. They are kept in `legacy/v1-v2/` for reference only.

## The idea in one paragraph
Cinema HUD is a one-button Second Life HUD whose **default job is a scenery camera**. When you go AFK, or tap the button, your view leaves your avatar. The HUD finds clear, high or wide vantage points around you, up to about 100 m away, with nothing blocking the view and open sky and horizon in front. It cuts between those still, grand views at a calm pace. You are tiny in the frame or not in it at all. It needs no people around. A movement key, a tap or starting to type gives your camera back instantly. Two optional modes, which **you start yourself and AFK never starts**, point the camera at people: **Personal** follows you as you walk, and **Social** frames you with the people around you.

## Modes

### 1. Scenery: the default
- **Starts:** automatically after the AFK time (menu, default 90 s), or by a **tap** on the button.
- **Looks at:** the place. Mostly landscape, sky, horizon and the area you're in. You may appear tiny, or not at all. People nearby are ignored.
- **Camera spots:** a mix of
  - **High drone views:** 10–30 m above whatever is below, 20–100 m from you, tilted 10–40° down over the area.
  - **Wide eye-level views:** 2–4 m above ground, looking along the open horizon, level.
- **A spot is good when:**
  - **Nothing blocks the view:** rays confirm the view ahead is clear for a long distance.
  - **Open sky and horizon:** prefer views that see far, horizon in frame.
  - **Variety:** every new spot comes from a clearly different direction and height than the last few.
- **Indoors / skybox:** the camera goes **outside and above the roof**. A spot is always placed above the topmost surface at its position, so it can never sit inside a building.
- **Region:** the camera always stays **inside your current region**, because rays can only check obstacles there.
- **Motion:** none. Each view is **static**, then a **hard cut** to the next.
- **Pacing:** **grand views, calm pacing.** Hold time is adjustable (menu: 30 / 45 / 60 / 90 / 120 s), default **60 s** ±25 %.
- **Reach:** the furthest distance is a setting (default 100 m). The HUD **learns** it: if your viewer refuses a far camera, it lowers the reach by itself and remembers it.

### 2. Personal: optional, from the menu
- **Starts:** long-press menu → *Personal* (or `/77 personal`). AFK never starts it.
- **Does:** composed static shots of **you**, at a level horizon with your eye line on the upper third. They **follow you as you walk**: when you leave the frame or walk more than about 4 m, it cuts to a new static shot. When you stand still, it changes angle every ~20 s. Walls are avoided with raycasts.
- **Movement keys do not end it.** You walk and it follows. Tap or typing ends it.

### 3. Social: optional, from the menu
- **Starts:** long-press menu → *Social* (or `/77 social`). AFK never starts it.
- **Does:** **pairs and group shots.**
  - With one person near you: an over-the-shoulder shot, then the reverse shot, keeping the 180-degree rule.
  - With two or more people within 8 m: a group tableau, square-on, everyone in frame.
  - It re-frames when people arrive, or when you walk.
  - If nobody is near, it says so and frames you (Personal style) until someone comes.
- **Movement keys do not end it.** Tap or typing ends it.

## Controls and exits
| Action | Result |
|---|---|
| Tap the button | Scenery on / off (any running mode off) |
| Hold the button 1 s | Menu: Scenery, Personal, Social, Stop, AFK, Hold, Options |
| Idle for the AFK time | Scenery starts (never Personal or Social) |
| Movement key | **Scenery:** ends instantly. **Personal / Social:** the camera follows you |
| Start typing | Ends any mode |
| Alt-cam / mouse orbit | Pauses (peek); ESC resumes |
| Mouselook / teleport | Pauses, then resumes / re-frames |

Chat commands (default channel **77**): `scenery`, `personal`, `social`, `stop`, `menu`, `grab`, `status`, `hold <s>`, `reach <m>`, `trace on|off`, `chan <n>`, `reset`.

## Vibe
Grand views, calm pacing. The feel is aerial grandeur held still and long, like a contemplative film that happens to be shot from a drone. There are no glides, no pans and no shaking. Horizons are level unless the camera looks down from above.

## Not in this version (by choice)
Letterbox bars, dip-to-black between cuts, snapshot helper, speaker cuts, style presets.

## Quiz answers this spec is built from (round 2)
| Topic | Answer |
|---|---|
| Scenery subject | Mostly landscape, you tiny or absent |
| Height / angle | Mix of high drone and wide eye-level |
| Distance | Up to ~100 m |
| Motion | Static, then hard cut |
| Good spot | Nothing blocks the view; open sky and horizon |
| Indoors | Go outside and above the roof |
| Region borders | Stay inside my region |
| Hold | Adjustable but very contemplative |
| Trigger | AFK timer + tap |
| Mode switch | One button + long-press menu |
| Personal | Follow you as you walk |
| Social | Pairs and group shots |
| Vibe | Grand views, calm pacing |
| Exit | Movement key, tap, typing |
| Extras | None for now |
| Delivery | Everything at once |
