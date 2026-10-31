# Take 12: Roadmap (8.0)

What it is: `docs/PRODUCT.md`. How it is built: `docs/ARCHITECTURE.md`. Earlier roadmaps are in git history.

## Status
| Step | What | State |
|---|---|---|
| 8.0 design | The master revision (about 200 questions, the Monitor mockups) | ✅ done |
| 8.0 build | Eleven scripts, the builder, two textures, the free build, the emulator tests | ✅ done, emulator-tested |
| 8.0 in-world | Build it, then the tester checklist below | ⏳ next |
| 8.0.x | Tuning from the in-world test (numbers below) | ⏳ after |
| Release | Beta (feedback by email) → release candidate → release at L$790; the cinema-black boards, real snapshots as extra images | ⏳ after the in-world test |
| Later | Portrait Us: an optional shot / reverse shot (cut between two people talking); the script-count review (with the owner's OK); a retro edition (the same engine, the 7.x pixel look, a lower price) | 💤 to discuss |
| Later | "Take 12 Lens" add-on (mm and aspect, always on); light companions; other languages | 💤 only on request |

## Next (after the in-world test, agreed 2026-10-29)
1. **The in-world test**: Connect with a friend first (it never had a real test), then the fixes it finds.
2. **The strip, polished** (mockups first): static at the top, never centred in the bar (a shot change would move
   it); its own band (a lifted black, a hairline), a smaller [12], a more geometric, unified layout. Mock up the
   [12] centred and on the left (macOS style). Notes on a dark plate under the strip, readable on any picture.
   (Settled in 8.5.6: 8.4.4's places with the 8.5 finish, after four other arrangements in 8.5.0-8.5.5 were worse. Rule from now on: no rearranging without an in-world screenshot of a real problem. The automatic fade was tried in 8.5.0 and taken out in 8.5.3:
   it hid the strip while you worked. Hiding needs another way, see 3.)
3. **A clean screen**: Settings › Look › Screen: Cinema (bars and strip) · Clear (nothing
   on screen; the [12]'s spot stays tappable). Never automatic, never on a timer. One choice, no format changes or double-taps.
4. **The free watcher, revamped**: anyone can see your film, not only people who own Take 12. Second Life only
   lets a script move the camera of someone who wears it and allows it, so a friend still wears something: a tiny,
   free, copyable "Take 12 Watch" (a small [12] only, no shots, no setup). Your HUD hands it out: Connect lists
   people near you without Take 12 too ("Give a Watch"), they accept, wear it once, and see your film; nothing to
   buy, nothing to learn. A new design and minimal features; it replaces the Scenery build as the friends' item
   (whether Scenery stays as a separate free product is decided then).
5. **Auto as a director** (later): presets set once in Settings › Auto (a style, how much Scenic, calm or lively
   cutting; neutral names, never directors' names), shot grammar (wide, medium, closer), the unified film (one
   height, glides within a scene, one frame). Later still: cuts to who speaks in local chat, only with 2–3 people
   near, never in a crowd.

## Build it in-world
1. `hud/build/README.md`: rez a box, put `builder.lsl` and a blank box named `t12 part` in it, touch it.
2. Add the twelve scripts of `hud/src/`; upload `hud/art/take12_words_1024.png` and `hud/art/take12_marks_1024.png`
   (as `take12_words`, `take12_marks`) and drop them in; add the Read Me (`hud/notecard/read_me.txt`) and, optionally,
   a chime sound.
3. Take it, wear it on HUD Top Center. `/12 status`: every script answers, "parts found", "textures kept".
4. The free build: the same with the nine scripts of `scenery/src/` and `scenery/notecard/read_me.txt`.

## Tester checklist
- [ ] A viewer with tall bars (Firestorm with its navigation and favourites bars, a small window, a larger UI size): the whole strip in view after setup's "Lower it" or Settings › Look › Place › Move in (8.5.7). Note the viewer, the window size and the UI size.
Viewers: the official viewer, Firestorm and one more. UI scale 1.0 and 1.25. Windows 16:9, 16:10, 21:9 and 4:3,
windowed and full screen. `/12 debug on` prints every Connect message.

**The strip and the [12]**
- [ ] First wear: only "Tap the [12] to set up." under the [12]; nothing else pops up; no text from before.
- [ ] The setup: the lens page shows a live mm while you zoom; the eye line moves with Page Up / Page Down and a tap keeps it; Easy to read? changes the size; the tour.
- [ ] Double-tap opens with a short fade; the words are readable and do not overlap; corner HUDs keep their space; a click on the empty strip area falls through when closed.
- [ ] Top, Top lower, Bottom, Bottom higher each clear your viewer's own bars.
- [ ] The ring while filming, the dot while connected, the soft glow while shared, the hold fill, amber (take a script out).
- [ ] Notes show 3 s under the strip; tips only the first three times.

**The shots**
- [ ] Tracking: the three looks and L · R; smooth turns; running pulls back; never through a wall; a small room's corner; out of it, behind you; PORTRAIT glows after 5 s still.
- [ ] Portrait: Close / Medium / Wide with the eyes on the upper third; the 3/4 side; lead room; walking then settling; turning away 2 s; a two-shot with a friend; a group of 3–4; a wall behind the camera; a zoom (never a cut).
- [ ] Fixed: frame it, hold still: kept. KEEP NEW over a kept view; View A / B per place; seat views per spot (a sofa's two ends); FORGET SEAT and UNDO; LET GO on a boat or car, then sitting on it again; TAKE BACK; standing up returns to the previous shot.
- [ ] Scenic: Drift, Near, Room (indoors), Far; never under ground, under water or outside the region; idle start after 5 min and on Away; a key brings back your shot.
- [ ] Sitting holds the frame and FIXED glows; Alt-click holds (the lit word dims) and a key gives it back; flying, mouselook; a teleport and a region crossing.
- [ ] One film frame for every shot (the ▭: cinema frames while filming, the snapshot size), Black and Dimmed. The shutter: the view holds in 3:2 while walking with Tracking; the ▭ then lists the photo frames; a 1800 × 1200 snapshot matches the pillarbox; pressed again, the film goes on.
- [ ] Drift: the reveal (rising, pulling back, a cut to a new close); Settings › Motion › Breathe gives the in and out.
- [ ] Auto (the guide, 8.4.0): worn, it starts after 3 s with the Orbit lit and the shot faint; walking round a room
  in short steps, Tracking all along; stop 10 s, Drift; 5 minutes or Away, Far (Room indoors); a friend beside you
  4 s, Portrait Us; they leave, Drift; a seat you framed, Fixed; another seat, Drift; Alt-click waits, Esc or walking
  goes on; tap the faint shot: manual; tap the Orbit: Auto. If anything sticks, `/12 debug on` says why.
- [ ] The box: Add it from the inventory: a card on the screen, the folder "Take 12 8.5.10", and it takes itself off.

**Connect** (two people, then three, then with the free build)
- [ ] Ask, Yes / No, a friend without asking, the chime (and Chime off).
- [ ] The flip with one person; the names with more; SHARING / THEIR FILM; the watcher sees the director's shape.
- [ ] Alt-click, flying or Fixed framing on the director's side: "isn't filming", nothing shared.
- [ ] Walk 25 m apart and back; log out and in within 30 min; Leave; a hold.
- [ ] A 7.x Take 12 near you shows as "(old)"; the free build watches but never films for others.

**Copies**
- [ ] Wear a fresh copy over a set-up one: "Moved."; the old one goes amber and lets go.
- [ ] Wear the free build with the full one: the free one steps aside.

## Tuning numbers to watch
- Strip: the margins per place (0 / 52 / 46 / 96 px), the inset of 180 px, the lit words (white, underlined) readable.
- Tracking: the distances 1.6 / 3.5 / 3.0 m, the pitches, the side offsets, the behind lag, the small room's 4.5 m.
- Portrait: THIRD 0.333, the Wide feet at −0.9, 30° and 20°, the join and leave times (2 s, 3 s), the crowd rule.
- Fixed: the capture time (1 s still), KEEP NEW's 5 s, the spot sizes (0.5 m and 45°; 2 m on the ground).
- Scenic: the 15 s hold, Drift's legs (15 s; the distances 5–26 m alone, 4.5–7 m near people), Near's 3–8 m.
- Connect: QUIET 10 s, GONE 3 s, NEAR 20 m.
- Auto: moving over 0.5 m/s for 1 s, Drift after 10 s, wide after 5 min, Portrait after 4 s with 1-3 people within
  3 m (gone 3 s), 8 s a shot, the 3 s on wear, Esc's 1.5 s.
