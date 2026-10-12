# Cinema HUD - Read Me
*(Put this text into a notecard named exactly **Cinema HUD - Read Me** inside the HUD.)*

## What it does
When you go AFK, or tap the button, your view leaves your avatar and becomes a quiet film camera over the place you are in. It finds **clear, grand vantage points**: high drone views looking down over the area, and wide eye-level views along the horizon, up to about 100 m away, with nothing blocking the view. It holds each still view for about a minute, then cuts to the next. You are tiny in the frame or not in it at all. Nobody has to be around.

The moment you press a movement key, tap the button or start typing, your own camera is back.

Two **optional** cameras are in the menu. AFK never starts them:
- **Personal:** composed shots of **you** that follow you as you walk (it cuts to a new still shot when you leave the frame).
- **Social:** you and the **people around you**: over-the-shoulder shots with the person next to you, or a tableau of the group.

## Setup
1. Wear the HUD (right-click > *Attach To HUD*) and accept the permission request if one appears.
2. That's all. The button is white when ready.

## Using it
| You do | It does |
|---|---|
| **Tap** the button | Scenery camera on (tap again: off) |
| **Hold** the button 1 s | Menu: Scenery, Personal, Social, Stop, AFK, Hold, Options |
| Stay idle (default 90 s) | Scenery camera starts by itself |
| Movement key | Scenery: your camera comes back. Personal / Social: the camera follows you |
| Start typing in chat | Your camera comes back (any mode) |
| Alt-orbit the camera | Pauses (the button turns amber); press ESC to carry on |
| Mouselook / teleport | Pauses, then carries on |

Button colours: grey = off, white = ready, red = rolling, amber = paused by Alt-cam.

## Menu
- **Scenery / Personal / Social / Stop:** start a camera, or stop.
- **AFK:** when the scenery camera starts by itself (60 s ... 10 min, when SL says Away, or off).
- **Hold:** how long each scenery view stays (30 s ... 2 min).
- **Options:**
  - *Phantom*: count phantom objects (foliage) as obstacles.
  - *Alt-cam*: pause, end, or ignore.
  - *Cut mode*: use if you see the camera glide instead of cut.
  - *Trace*: one chat line per cut.
  - *Reach*: furthest camera distance (25–100 m).
  - *Test camera*: takes your camera for 3 s to check that the viewer allows it.
  - *Reset*.

## Chat commands (channel 77)
`/77 scenery` | `personal` | `social` | `stop` | `menu` | `grab` | `status` | `hold <seconds>` | `reach <metres>` | `trace on|off` | `chan <number>` | `reset`

- `/77 status`: each of the four scripts prints one line. Include it when asking for help.
- If another HUD also uses 77, move ours with `/77 chan <number>`.

## Good to know
- The camera never goes outside your region, and it is always placed above whatever is below it, so it never ends up inside a building. When you are indoors it goes outside, above the roof.
- If your viewer won't put the camera as far as asked, the HUD notices, says so, and uses a shorter reach from then on.
- It only moves *your* view. Nobody else sees what the camera does.

## Troubleshooting
| Problem | Try |
|---|---|
| Nothing happens at all | Press **ESC** once (a free / Alt-orbited camera makes the viewer ignore scripts), then `/77 grab`. |
| Chat says "the scenery (or personal / social) script is not answering" | You still get basic shots. Select the HUD in Build mode and use **Build > Scripts > Set Scripts to Running in Selection**. Also check the **Script Errors** window. |
| A script does not answer `/77 status` | Same as above. |
| Camera glides instead of cutting | Options > Cut mode. |
| Views too short / too long | Menu > Hold. |
| "script is version ..." warning | Re-drop all four scripts from the same release. |
