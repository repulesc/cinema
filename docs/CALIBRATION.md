# Calibration and in-world log (v4)

Fill this in while testing in-world. `/77 status` and the trace lines give most of it.

| Question | Result |
|---|---|
| Is the clapper crisp at 40 px? Is the right face / offset set? | |
| Tap opens the menu after a short beat; do double-taps register reliably (0.35 s window)? | |
| Does a long press (0.8 s) open the live menu? | |
| Emoji show on the buttons? (if boxes: Options › Emoji off) | |
| Does the button fade to 15 % and clap once on start? | |
| Scenery outdoors: varied views, nothing blocked, reach your viewer allows | |
| Skybox: do views stay inside the room (corner / centre / you small)? Trace line "inside a room"? | |
| House on the ground: views from outside above the roof? | |
| Photo hold: frozen until a tap? Double-tap = next? | |
| Favourites: ⭐ Save, then do they come back (about every 4th cut)? | |
| Friends: does the glide look smooth (lag 1.5 s)? If the camera does not ease: report it, there is a step-glide fallback | |
| Friends: someone runs out of frame: snap within about 1 s to a wider shot? | |
| Social / Friends chat cuts: a cut to the speaker within about 6 s, not more often than every 10 s? | |
| Typing in Social / Friends keeps the camera rolling and cuts to you? | |
| Free memory printed by each script (core / ui / scenery / people / friends / picker) | |

Numbers I may tune from your feedback:
- tap window 0.35 s, long press 0.8 s, fade 15 %;
- glide lag 1.5 s and the 0.2 m glide threshold, the 1 s snap, the 25 m max distance;
- room heights (corner at most 6 m above the floor, centre 1.7 m, you-small 2.5 m);
- chat cut hold 10 s and cooldown 10 s;
- drone height 10-30 m, wide 2.5-4 m, distance 20 m to reach, pace 60 s +/-25 %.
