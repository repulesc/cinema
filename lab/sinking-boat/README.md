# Sinking Boat (gag)

A boat that rides the water on its own and slowly goes under when someone sits in it. Not part of Take 12.

- **Afloat:** it rises and falls a few centimetres, rocks softly side to side (2°) and bow to stern (under 1°), and
  its bow slowly swings round: Second Life water is flat, so the motion is kept small and slow. It comes from several
  slow swells (6 to 10 s) with unrelated periods, so it never visibly repeats. It drifts very slowly (about 5 cm/s) on a lazy
  loop within `DRIFT_RADIUS` of home. It finds the water level and its own size, and sits with the hull bottom
  `DRAFT` (25 cm) under the surface.
- **Sit:** it starts taking on water. Over `SINK_TIME` (90 s) it settles lower, tips bow down and lists a little, and
  the rocking calms, until it is `SINK_DEPTH` (3 m) under: about 3 cm after 5 s, 0.8 m after 30 s, 1.5 m after 45 s.
  The sitter goes down with it. It never goes into the sea floor.
- **Stand up:** it comes back up over `RISE_TIME` (30 s).
- It tells its owner in chat what it is doing (afloat, sinking, coming back up) and what is wrong if it cannot move.

## Setting it up
1. **Remove the boat's own scripts** (a driving/vehicle script turns physics on when you sit, and a physical boat
   cannot be moved this way: it just drops). This script must be the only one moving the boat.
2. The bow should point along the root prim's **+X** (red arrow in Build mode with Local axes); otherwise set
   `SINK_PITCH` and `SINK_ROLL` to minus values or turn the root prim.
3. Put the boat on open water, drop `sinking_boat.lsl` into the **root prim**, and **close the edit window**: Second
   Life freezes keyframed motion while the boat is selected. Where the boat is when the script starts is home; after
   moving it by hand, use **Align** in the owner menu.
4. The script sets the root prim's physics shape to Convex Hull, which keyframed motion needs.
5. Tune `DRAFT` if the boat sits too high or too low, and `SIT_POS` / `SIT_ROT` until the sitter sits right.

## Owner menu (Align)
Only the owner gets it. Left-click still sits people down (that is the gag), so open the menu with
**right-click the boat > Touch**, or say **`/9 boat`** in chat (use this if your pie menu has no Touch entry).
- **Align:** put the boat on the water level where it is now, level it, and make this spot its home. Use it after
  moving the boat by hand (instead of Reset Scripts), or whenever the boat floats at the wrong height.
- **Higher / Lower:** move the hull 5 cm up or down in the water, then align again. The boat tells you the new depth
  in chat; to keep it after a script reset, copy that number into `DRAFT` at the top of the script.

## How it moves
Keyframed motion (non-physical, played by the simulator): the boat cannot be pushed away and cannot leave its patch
of water. The script plans 6 s of motion at a time (ten 0.6 s keyframes) from where the boat really is, and sends
the next batch when the last one ends. A keyframe's move is in region axes and its turn in the boat's own axes.
