# Cinema HUD - Read Me
*(Put this text into a notecard named exactly **Cinema HUD - Read Me** inside the HUD.)*

## What it does
Cinema HUD turns your camera into a quiet film camera. It never glides or swoops: it **cuts** between still, carefully composed shots - a portrait of you, a tableau of the people around you, a long shot of you small in the landscape, an empty "pillow shot" of sky or sea - and holds each one for a while, in the spirit of Ozu, Jarmusch and the French New Wave.

It starts by itself when you go idle, and the moment you move, type or touch the HUD, your own camera is back instantly.

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
| Press a movement key (while *you* started it) | Social shots keep rolling and re-frame when you walk out of shot. Long shots can end instead (Options > Man. vista). |
| Start typing in local chat | The cinema stops. |
| Sit down / stand up | The cinema stops. |
| Alt-orbit / free-look the camera | The cinema **pauses** ("peek"); press ESC to let it carry on. |
| Enter mouselook | It pauses and resumes when you leave mouselook. |
| Teleport / change region | It pauses, then re-frames the new place. |

Button colours: grey = off, white = ready, red = rolling, amber = peeking, blue = no usable shot (it keeps trying).

## Menu
- **Style** - *Blend* (default), *Ozu* (low, level, frontal), *Jarmusch* (symmetric, deadpan, long holds), *Nouvelle V.* (restless, jump cuts).
- **AFK** - start after 60 s / 90 s / 2 / 3 / 5 / 10 min, when Second Life marks you Away, or off.
- **Holds** - how long a shot stays: x0.5 ... x3, or *Until event* (cuts only when something changes).
- **Options**
  - *Speaker* - cut to whoever starts typing near you (off / typing / typing + local chat).
  - *Phantom* - treat phantom objects (foliage, triggers) as obstacles.
  - *Man. vista* - in a manual session, end when you walk during a long shot.
  - *Alt-cam* - what Alt-orbiting does: peek / end the cinema / ignore.
  - *Cooldown* - after this long idle (default 10 min) it prefers empty sky and sea shots, which are lighter for your graphics card.
  - *Cut mode* - use if you see the camera glide instead of cut.
  - *Debug* - prints why each shot was chosen.
  - *Probe* - in-world tests (see below).
  - *Reset* - back to defaults.

## Good to know
- It works best outdoors and in rooms with some space. In a tiny room it falls back to a camera just behind your shoulder, and if nothing works it hands your camera back (blue button) and tries again later.
- It only moves *your* view. Nobody else sees what the camera does.
- It needs no scripts rights on the land except what the HUD itself uses; it also works in no-script parcels.

## Probes (for tinkerers)
*Options > Probe* runs small tests and prints the results in chat: *Cut* (instant cut or glide?), *CamPos* (can the HUD see Alt-cam?), *Distance* (how far can the camera sit from you?), *FOV* (what field of view does your viewer report?).

## Troubleshooting
| Problem | Try |
|---|---|
| Nothing happens when I tap | Re-attach the HUD and accept the permissions. Check the button is not grey/blue. |
| Camera glides instead of cutting | Options > Cut mode. |
| Shots look cropped at the sides | Raise/lower your viewer field of view, or ask the creator to switch the FOV axis setting. |
| It starts too early / late | Menu > AFK. |
| "script version mismatch" message | Re-drop all three scripts from the same release. |
