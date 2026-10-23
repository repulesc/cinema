# Marketplace listing: copy-paste text

The Marketplace description is plain text. Copy each block below as it is: no bold, no headings, only "-" lists.
Fields marked (you) need your own details (price, creator, support contact).

This is the 7.0 text: short, like the product. Older listings are kept in `legacy/`. The free Take 12 Watch has its
own listing (`watch/marketing/marketplace_listing_watch.md`), and so does the free Take 12 Scenery
(`scenery/marketing/marketplace_listing_scenery.md`). `tools/sim/listing_check.py` keeps each Full description well
under the Marketplace's 5000 characters.

---

## Product name
Use the same text for the Marketplace title, the box and the folder, so buyers find the folder after unboxing:
```
Take 12 - Cinematic Camera HUD
```

## Short description (the line search results show; keep it first)
```
A camera for Second Life. It frames you and the people with you, holds your own shots like a tripod, connects your friends to one camera, and shows the place while you are away. One button.
```

## Full description
```
A camera for Second Life.

Take 12 moves your view off your avatar's back and composes it the way a photographer would: eyes on the golden line, room to look into, air around a full-length picture. One small button. Any movement key gives your camera back.

FRAMING
Me, Us or Friends. It follows you as you walk and holds a composed picture when you stand. Page Up and Page Down set the height for the way you sit; it remembers each seat.

FREEHAND
Frame it yourself with Second Life's camera. Hold still for a second and Take 12 holds it, like a tripod.

CONNECT
Connect with the people near you. Whoever films leads: everyone connected sees that camera. Friends without Take 12 wear the free Take 12 Watch.

SCENERY
While you are away: drone views, wide horizons, the corners of a skybox. It starts by itself when you go idle.

FORMAT
3:2, 4:5, 2.39:1 and more: the screen outside the picture is dimmed, and Framing composes inside it.

Your viewer's zoom is your lens: every camera frames for it.

- It only moves your view, inside your region. Nothing is recorded.
- Works on any HUD point; your own camera is always restored.

In the box: the Take 12 HUD, the Read Me, and the free Take 12 Watch to give to friends.
Try the scenery camera first, free: Take 12 Scenery.
Creator: (you)  ·  Support: (you)
```

## Features (the Marketplace "Features" list takes 5)
```
Framing: you and the people with you, composed on the golden lines
Freehand: frame it yourself, Take 12 holds it like a tripod
Connect: whoever films leads; the free Take 12 Watch for friends
Scenery: drone views, horizons and skybox rooms while you are away
One button; any movement key gives your camera back
```

## Keywords
```
take 12, take12, camera, camera hud, cinematic camera, auto camera, portrait, photography, photo, snapshot, framing, golden ratio, composition, tripod, freehand, drone camera, drone view, scenery, skybox, afk, friends, group shot, connect, share view, watch, lens, zoom, hud
```

## Short promo lines (group notices, social posts)
```
A camera for Second Life.
Framed like a photographer would. One button.
Connect, and whoever films leads.
```

## One line "what is it?" (for a vendor or a friend)
```
Take 12 is a one-button camera HUD: it frames you and your friends, holds your own shots, connects everyone to one camera, and shows the place while you are away.
```

## What is new in 7.0 (the Marketplace update message, or a group notice for existing buyers)
```
Take 12 7.0: one product.
- Six doors on the menu: Framing, Freehand, Connect, Scenery, Format, Settings.
- Framing (Me, Us, Friends) follows you as you walk and holds a composed picture when you stand.
- Connect: connect with the people near you; whoever films leads.
- Page Up / Page Down set the camera's height for your pose, remembered per seat.
Get the new version from your Marketplace purchases (Update), and read the new notecard.
```

---

## Images
- **`adboard_square_1024.png`**: the main Marketplace image. One quiet frame (a dusk horizon), the clapper, the name and one line.
- **`adboard_portrait_3x4_768x1024.png`**, **`adboard_landscape_4x3_1024x768.png`**, **`adboard_wide_1024x512.png`**: the same frame in other ratios.
- **`adboard_vendor_1024.png`** / **`adboard_vendor_512.png`**: the same, with bigger type for vendor displays.

The boards are drawn pixel art, not screenshots. Add 4 to 6 real snapshots as extra images, one idea each: a Framing portrait on the golden line, a group in Us, a Freehand shot, a drone view, and the Format bars on screen. Hide your UI for them (Ctrl+Alt+F1 in Firestorm). The boards' text is in `tools/art/make_adboard.py` (`NAME`, `TAGLINE`); run `python3 tools/art/make_adboard.py` after a change.
