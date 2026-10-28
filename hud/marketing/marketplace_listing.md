# Marketplace listing: copy-paste text

The Marketplace description is plain text. Copy each block below as it is: no bold, no headings, only "-" lists.
Fields marked (you) need your own details (creator, support contact).

**Price:** L$790. Permissions: copy, no-modify, no-transfer (the Marketplace's gift option for presents). Updates are
free for life (redelivery). The free Take 12 Scenery stays L$0.

This is the 8.0 text: short, like the product. Older listings are kept in `legacy/`. The free Take 12 Scenery has its
own listing (`scenery/marketing/marketplace_listing_scenery.md`). `tools/sim/listing_check.py` keeps each Full
description well under the Marketplace's 5000 characters.

---

## Product name
Use the same text for the Marketplace title, the box and the folder, so buyers find the folder after unboxing:
```
Take 12 - Cinematic Camera HUD
```

## Short description (the line search results show; keep it first)
```
A cinematic camera for Second Life. Four shots on one quiet strip: it follows you, frames you, keeps your own framing for every seat, and shows the place while you are away.
```

## Full description
```
A cinematic camera for Second Life.

Take 12 sits at the top of your screen like a cinema camera's display: one thin line of words, and the [12]. Double-tap it, pick a shot.

TRACKING
A cinematic follow camera: over your shoulder, a slow film look, or a smooth classic view. Never through a wall; in a small room it takes the corner.

PORTRAIT
You standing, composed: a soft three-quarter view at eye level, your eyes on the upper third. Close, Medium or Wide, Me or Us: with a friend, a two-shot.

FIXED
Your own framing, kept. Frame it with your viewer's camera, hold still, and Take 12 keeps it: two views for each place, one for every seat and spot.

SCENIC
Views of the place, and the camera that starts when you are away.

CONNECT
Share films with the people near you: two equal cameras, one tap to see theirs.

FRAMES AND THE SHUTTER
Every frame is a picture. Each shot has its cinema frame, 2.39 to 1.66. Press the shutter and the moment holds in your photo frame (3:2, 4:3, 1:1 or 4:5), with the snapshot size: take your picture, press it again, and the film goes on.

A one-minute setup sets your lens and your eye line. Feedback goes straight to the maker, from the [12]'s menu.

- It only moves your view, inside your region. Nothing is recorded.
- Tap: setup. Double-tap: the strip. Hold: everything off, hold again: back.

In the box: the Take 12 HUD and the Read Me.
Try Scenic first, free: Take 12 Scenery.
Creator: (you)  ·  Support: (you)
```

## Features (the Marketplace "Features" list takes 5)
```
Tracking: a cinematic follow camera that never goes through a wall
Portrait: you standing, composed at eye level, alone or with friends
Fixed: your own framing, kept for every place and every seat
Scenic: views of the place, by itself when you are away
Connect: share films with the people near you, one tap to see theirs
```

## Keywords
```
take 12, take12, camera, camera hud, cinematic camera, cinema, film, follow camera, tracking, portrait, photography, snapshot, photo frame, 4:5, letterbox, 2.39, composition, framing, seat camera, scenery, skybox, afk, connect, share view, lens, zoom, hud
```

## Short promo lines (group notices, social posts)
```
A cinematic camera for Second Life.
Four shots on one quiet strip. Double-tap the [12].
Share films with your friends: one tap to see theirs.
```

## One line "what is it?" (for a vendor or a friend)
```
Take 12 is a cinematic camera HUD: it follows you, frames you, keeps your own framing for every seat, and shows the place while you are away.
```

## What is new in 8.0 (the Marketplace update message, or a group notice for existing buyers)
```
Take 12 8.0: rebuilt from the ground up.
- A new look: a thin strip at the top of your screen. Double-tap the [12].
- Four shots: Tracking, Portrait, Fixed, Scenic. Every frame is a picture: cinema and photo frames, with the snapshot size.
- Fixed keeps your own framing for every place and every seat.
- Connect: two equal cameras, one tap to see your friend's film.
- Feedback: tap the [12], Feedback, write a line. It reaches the maker.
Get the new version from your Marketplace purchases (Update). The old version can be deleted: 8.0 is a new camera, set up in a minute.
```

---

## Images
- **`adboard_square_1024.png`**: the main Marketplace image. Cinema black: a 2.39 frame drawn as a monitor's frame lines, the [12], the name and one line, the four shots in a quiet row.
- **`adboard_portrait_3x4_768x1024.png`**, **`adboard_landscape_4x3_1024x768.png`**, **`adboard_wide_1024x512.png`**: the same board in other ratios.
- **`adboard_vendor_1024.png`** / **`adboard_vendor_512.png`**: the same, with bigger type for vendor displays.

The boards are typographic on purpose: no drawn scenes. Real snapshots can come later as extra images, one idea each (a Tracking shot in 2.39, a Portrait two-shot, a 4:5 portrait, a seat view in Fixed, the strip at the top of a screen). The boards' text is in `tools/art/make_adboard.py` (`NAME`, `TAGLINE`); run `python3 tools/art/make_adboard.py` after a change.
