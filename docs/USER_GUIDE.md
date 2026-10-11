# Cinema HUD - Read Me
*(Put this text into a notecard named exactly **Cinema HUD - Read Me** inside the HUD.)*

## What it does
Cinema HUD turns your camera into a quiet film camera. It never glides or swoops: it **cuts** between still, carefully composed shots and holds each one for a while, in the spirit of Ozu, Jarmusch and the French New Wave.

It starts by itself when you go idle, and the moment you move, type or touch the HUD, your own camera is back instantly.

**Shots in this version:** a portrait of you (varied angles), an over-the-shoulder shot of you and a person standing near you (with shot / reverse shot), and a "pillow shot" of the empty sky, sea or horizon. It keeps the camera out of walls and keeps the horizon level.
**Coming later:** group tableaux, long landscape shots, speaker cuts, director style presets, letterbox bars.

## Setup
1. Wear the HUD (right-click > *Attach To HUD*). Accept the permission request if one appears: it needs control of your camera and your movement keys (to notice that you are back).
2. A small button appears on your screen. That is all.

## Using it
| You do | It does |
|---|---|
| **Tap** the button | Start the cinema (manual). Tap again to stop. |
| **Hold** the button for 1 second | Open the menu. |
| Stay idle for 90 seconds (default) | The cinema starts by itself. |
| Press any movement key (while it started itself) | Your camera returns instantly. |
| Press a movement key (while *you* started it) | It keeps rolling and re-frames when you walk out of shot. |
| Start typing in local chat | The cinema stops. |
| Sit down / stand up | The cinema stops. |
| Alt-orbit / free-look the camera | The cinema **pauses** ("peek"); press ESC to let it carry on. |
| Enter mouselook | It pauses and resumes when you leave mouselook. |
| Teleport / change region | It pauses, then re-frames the new place. |

Button colours: grey = off, white = ready, red = rolling, amber = peeking, blue = no usable shot (it keeps trying).

## Menu
- **AFK** - start after 60 s / 90 s / 2 / 3 / 5 / 10 min, when Second Life marks you Away, or off.
- **Holds** - how long a shot stays: x0.5 ... x3, or *Until event* (cuts only when something changes).
- **Options**
  - *Phantom* - treat phantom objects (foliage, triggers) as obstacles.
  - *Man. vista* - in a manual session, end when you walk during an empty-view shot.
  - *Alt-cam* - what Alt-orbiting does: peek / end the cinema / ignore.
  - *Cooldown* - after this long idle (default 10 min) it prefers empty sky and sea shots, which are lighter for your graphics card.
  - *Cut mode* - use if you see the camera glide instead of cut.
  - *Debug* - prints extra information.
  - *Probe* - in-world tests (see below).
  - *Reset* - back to defaults.

## Chat commands
Type these in local chat (default channel **77**, only you can use them). Change the channel with `/77 chan <number>` if another HUD uses 77.
`/77 menu` | `start` | `stop` | `grab` | `status` | `debug on|off` | `trace on|off` | `maxcam <metres>` | `chan <number>` | `probe cut|campos|dist|fov` | `reset`

- `/77 grab` is a 4-second test that takes your camera **without** the director: your view should jump 4 m in front of you, and chat says whether the viewer followed.
- `/77 status` prints one line from each of the three scripts (state, permissions, free memory). Include it when asking for help.
- `trace` prints a few progress lines each time a shot is chosen (on by default).

## Probes (for tinkerers)
*Options > Probe* (or `/77 probe ...`) runs small tests and prints the results in chat: *Cut* (instant cut or glide?), *CamPos* (can the HUD see Alt-cam?), *Distance* (how far can the camera sit from you?), *FOV* (what field of view does your viewer report?).

## Troubleshooting
| Problem | Try |
|---|---|
| Camera never changes at all | Press **ESC** once (an Alt-orbited / free camera makes the viewer ignore scripts), leave mouselook, then type `/77 grab`. If grab works but the cinema does not, type `/77 status` and send what the three scripts print. |
| A script says nothing at `/77 status` | That script is not running: re-save it, check it is in the same prim, and look for a script error in chat. |
| Button turns red but the camera does not change | After 5 s with no shot the button turns blue and chat explains why. |
| Long-press shows no menu | Keep the button held for a full second (the menu opens while held), or type `/77 menu`. |
| Camera glides instead of cutting | Options > Cut mode. |
| Shots look cropped at the sides | Ask the creator to switch the FOV axis setting (`fovaxis`). |
| It starts too early / late | Menu > AFK. |
| "script version mismatch" message | Re-drop all three scripts from the same release. |
