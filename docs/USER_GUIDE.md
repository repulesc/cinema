# Cinema HUD - Read Me
*(Put this text into a notecard named exactly **Cinema HUD - Read Me** inside the HUD.)*

## What it does
Cinema HUD turns your time in Second Life into a quiet film. Your view leaves your avatar and cuts between **still, grand views** of the place you are in: high drone views and wide eye-level views, up to about 100 m away, with nothing in the way. Each view is held for about a minute (you can change that), then it cuts to the next. In a skybox or another closed room in the sky, it stays **inside the room** instead.

## The button
The small clapper at the top right is the whole HUD.

| You do | Idle | While the camera rolls | While frozen (photo hold) |
|---|---|---|---|
| **Tap** | Open the menu | Stop: your camera is back | Resume |
| **Double-tap** | Start the scenery camera | Next view now | Next view now |
| **Hold** (about 1 s) | Open the menu | Live menu: Photo, Save, Next, Stop | Live menu |

The button fades to almost invisible while the camera rolls, so it stays out of your pictures. It is still there to click.

## Cameras
- **🏞 Scenery** is the default. It also starts by itself when you have been idle for a while (default 90 s). It looks at the place, not at people.
- **🚶 Personal** (menu): shots of you that follow you as you walk.
- **👥 Social** (menu): you and the people around you, over-the-shoulder pairs and group shots. It cuts to whoever speaks in local chat. Typing cuts to you, and the camera keeps rolling.
- **💞 Friends** (menu): you and the friends you picked. Menu › Friends › Pick shows people within 20 m; tap a name to add or remove it (up to 10). While your group stays in the picture, the camera glides slowly to keep it there. If someone is out of the picture for about a second, it cuts to a wider shot that holds everyone.

AFK only ever starts Scenery.

## Live menu (hold the button while it rolls)
- **📷 Photo** freezes the view so you can take pictures. A tap resumes.
- **⭐ Save** keeps the view on screen as a favourite spot for this region (Scenery). Saved spots come back now and then.
- **⏭ Next** cuts to the next view. **⏹ Stop** gives your camera back.

## Getting your camera back
Press a movement key (Scenery), tap the button, or start typing (Scenery and Personal). Personal, Social and Friends follow you when you walk. If you Alt-orbit the camera, it pauses until you press ESC.

## Settings (tap › Options, Pace, AFK)
- **⏳ Pace:** Lively 30 s · Easy 45 s · **Calm 60 s** · Slow 90 s · Still 120 s per view.
- **💤 AFK:** off, 1 min, 90 s, 2 min, 5 min, 10 min, or when SL says you are away.
- **🏠 Indoors:** Auto (inside in the sky, above the roof on the ground), Inside, or Outside.
- **💬 Chat cuts**, **👁 Alt-cam**, **🧱 Phantom**, **📏 Reach**, **📝 Trace**, **🔤 Emoji** (turn it off if your viewer shows boxes), **🧪 Test cam**, **♻ Reset**.

## Chat commands (channel 77)
`/77 scenery` · `personal` · `social` · `friends` · `stop` · `next` · `photo` · `fav` · `menu` · `status` · `pace <s>` · `reach <m>` · `indoors auto|inside|outside` · `friend list|clear` · `trace on|off` · `emoji on|off` · `chan <n>` · `reset`

## If something is off
- Nothing happens: send `/77 status`. It lists every script. A missing one is not running: select the HUD in Build mode and use **Build › Scripts › Set Scripts to Running in Selection**.
- A script warns about a version: re-drop all Cinema scripts from the same release.
- The camera stays near you: your viewer limits how far a script camera can go. The HUD notices and shortens its reach by itself. **📏 Reach › Re-learn** resets it.
