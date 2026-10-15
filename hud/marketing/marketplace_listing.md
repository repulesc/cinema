# Marketplace listing: copy-paste text

The Marketplace description is plain text. Copy each block below as it is: no bold, no headings, only "-" lists.
Fields marked (you) need your own details (price, creator, support contact).

The earlier wording ("your idle time, on film", "walk away") is kept in `legacy/` in case we want it back. It was
replaced because "film" and "filming" made people think the HUD records video, which it does not.

---

## Product name
Use the same text for the Marketplace title, the box and the folder, so buyers find the folder after unboxing:
```
Take 12 - Cinematic Camera HUD
```
Longer title, if you want more search words in it:
```
Take 12 - Cinematic Camera HUD: Drone Views, Skybox Rooms, Friends in Frame
```

## Short description (the line search results show; keep it first)
```
A camera HUD that takes your view off your avatar's back: drone views, wide horizons, skybox corners and group shots, chosen automatically, a new one every minute. One button. Any movement key brings your camera back.
```

## Full description
```
See your Second Life from somewhere other than behind your own back.

Take 12 lifts your camera off your avatar and places it where a camera operator would: high above the region, out across the horizon, in a corner of your skybox, or around you and your friends. It chooses each view by itself, holds it for about a minute, then cuts to the next one.

You stay in control. A double-tap on the button starts it or skips to the next view, a single tap stops it, and any movement key gives your normal camera back instantly.

FOUR CAMERAS

Scenery (the default) shows the place itself. Drone views 10 to 30 m up look down over your area, and wide eye-level views run along the horizon, up to 100 m away. Every spot is checked so that nothing blocks the picture. You are a small figure in the frame, or not in it at all. In a skybox or another closed room in the sky, it stays inside: views from the corners, from the middle of the room, and of you, small in the space. In a house on the ground, it looks from outside, above the roof. Scenery starts with a double-tap, or by itself when you are idle.

Personal shows you. Composed shots from different sides, with room in front of you in the direction you face. When you walk, it re-frames.

Social is for when you are with people. Over-the-shoulder shots between you and the person nearest to you, group shots of everyone within 8 m, and a cut to whoever speaks in local chat.

Friends keeps you and your friends together. Choose up to 10 friends from the people near you. The camera holds you and those friends in one frame, glides slowly as the group moves, and widens when someone wanders toward the edge.

And Frame: when you want a picture of yourself, or of you and a friend, Frame holds a still, well-composed view: full length, half length or close. Double-tap for the next, use your movement keys to adjust, take your snapshot.

Personal, Social, Friends and Frame are chosen from the menu. Going idle only ever starts Scenery.

ALSO
- Photo hold: freeze the current view while you take snapshots.
- Favourite spots: save a view you like, and it comes back now and then.
- Pace: from 30 seconds to 2 minutes per view.
- Idle start after 3 minutes with no keys and no mouse (adjustable, or off).
- Typing in chat does not stop Social or Friends.

CONTROLS
- Tap: open the menu. While the camera runs, a tap stops it.
- Double-tap: start Scenery, or skip to the next view.
- Hold: the live menu (photo hold, save spot, next, stop).
- Any movement key: your normal camera, instantly.

WHO IT IS FOR
- Explorers who want to see a region from above and from afar.
- Photographers looking for angles they would not find by hand.
- Anyone who likes to sit back in a beautiful place and simply watch it.
- Couples and groups who want to see themselves together, not the back of their own head.

GOOD TO KNOW
- One small button, a pixel-art clapper in three looks. Its clapper closes while the camera runs. (Second Life leaves HUDs out of snapshots unless you ask for them.)
- Wear it on a HUD point (Top Right is usual) and allow camera control once.
- It only moves your view, inside the region you are in. Nothing is recorded or sent anywhere.
- The menu icons need a recent viewer. They can be switched off.
- Read Me notecard included.
- Permissions: (you)
- Support: (you)
```

## Features (the Marketplace "Features" list takes 5)
```
Automatic camera views from beyond your avatar's back
Scenery: drone and horizon views up to 100 m, skybox aware
Frame: three held framings for your own snapshots
One button: tap, double-tap, hold; any movement key to return
Personal, Social and Friends cameras; photo hold; favourite spots
```

## Keywords
```
take 12, take12, camera, camera hud, cinematic camera, auto camera, portrait, camera control, drone camera, drone view, scenery, skybox, afk, photography, snapshot, view, friends, social, group shot, photo, hud
```

## Short promo lines (group notices, social posts)
```
Your idle time, framed.
Your camera, off your avatar's back.
See your region from the sky, the horizon and the corner of the room. Automatically.
One button: drone views, skybox rooms, friends in one frame.
```

## One line "what is it?" (for a vendor or a friend)
```
Take 12 is a one-button HUD that moves your camera off your avatar to drone views, wide horizons and skybox corners by itself, and gives it back with any movement key.
```

---

## Images
- **`adboard_square_1024.png`**: the main Marketplace image (square), with all three clapper looks.
- **`adboard_portrait_3x4_768x1024.png`** (3:4) and **`adboard_landscape_4x3_1024x768.png`** (4:3): the same ad in the two other ratios.
- **`adboard_wide_1024x512.png`**: an in-world vendor board or banner.
- **`adboard_vendor_1024.png`** and **`adboard_vendor_512.png`**: a simpler, bolder square for vendor displays, where the picture shows small. Use the 512 for vendors that want a smaller texture.

The boards use drawn pixel-art "views", **not real screenshots**. Marketplace buyers trust real pictures, so add 3 to 5 real snapshots as extra listing images:
1. A drone view over your favourite region (Scenery).
2. A wide horizon view at sunrise or sunset (Scenery).
3. A corner view inside a skybox (Scenery, room mode).
4. A group of friends framed together (Friends).
5. The menu open on screen: Tap > shows the Main menu.

Tips for the snapshots: use Photo hold for a steady shot, hide your UI (Ctrl+Alt+F1 in Firestorm), and use a high-quality setting. Keep the same look: square, with a little room around the subject.

The boards say "Your idle time, framed." and "Double-tap to start. Any key brings you back." To change a line, edit the `NAME`, `DESCRIPTOR`, `TAGLINE` and `HOWTO` constants (and the chip texts) in `tools/art/make_adboard.py` and run `python3 tools/art/make_adboard.py`. Frame is not on the boards on purpose: they sell the automatic camera. (Lite's boards are paused with Lite; add `--lite` to rebuild them.)
