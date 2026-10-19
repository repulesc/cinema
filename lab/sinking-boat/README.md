# Sinking Boat (gag, first draft)

A boat that rides the water on its own and slowly goes under when someone sits in it. Not part of Take 12.

- **Afloat:** it bobs, rocks side to side and bow to stern, and its bow slowly swings round. These come from several
  waves with unrelated periods, so the motion never visibly repeats. It drifts very slowly (about 5 cm/s) on a lazy
  loop within `DRIFT_RADIUS` of home, and always rides at the region's water level.
- **Sit:** over `SINK_TIME` (90 s) it settles lower, tips bow down and lists a little, and the rocking calms, until it
  is `SINK_DEPTH` (3 m) under. The sitter goes down with it. It never goes into the sea floor.
- **Stand up:** it comes back up over `RISE_TIME` (30 s).

## Setting it up
1. Make or link the boat. The bow should point along the root prim's **+X** (red arrow in Build mode with Local axes);
   otherwise set `SINK_PITCH` to a minus value or turn the root prim.
2. The root prim must use the new land impact accounting (mesh does; for a prim build set the root's Physics Shape
   Type to Convex Hull), or keyframed motion refuses to run.
3. Put the boat on open water, drop `sinking_boat.lsl` into the root prim. Where it stands when the script starts is
   home. After moving it by hand, Reset Scripts, or it glides back to the old home.
4. Tune `FLOAT_HEIGHT` until the hull sits at the waterline, and `SIT_POS` / `SIT_ROT` until the sitter sits right.
