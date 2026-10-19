// Sinking Boat 2 - a gag boat that sways and drifts on open water, and slowly sinks when someone sits in it.
// Drop into the ROOT prim of the boat, put the boat on the water and CLOSE THE EDIT WINDOW: Second Life freezes this
// kind of motion while the boat is selected. Where the boat is when the script starts is home.
// The boat is moved with keyframed motion (non-physical, smooth, run by the simulator), so it cannot be pushed away,
// cannot wander off the parcel, and always rides at the water level of the region.

// ---- Floating ----
float DRAFT         = 0.25;   // m, how deep the bottom of the hull sits in the water (the boat's size is measured)
float HEAVE         = 0.15;   // m, up-and-down bob
float ROLL_DEG      = 5.0;    // side-to-side rock
float PITCH_DEG     = 2.5;    // bow-to-stern rock
float YAW_SWING_DEG = 25.0;   // how far the bow slowly swings round
// ---- Drift ----
float DRIFT_RADIUS  = 6.0;    // m, the boat wanders within this distance of home (keep it over deep water)
float DRIFT_PERIOD  = 700.0;  // s, a wander loop takes about this long (bigger = slower; 700 s is ~5 cm/s)
// ---- Sinking ----
float SINK_TIME     = 90.0;   // s from sitting down to fully under
float SINK_DEPTH    = 3.0;    // m the boat goes down when fully sunk
float SINK_PITCH    = 12.0;   // degrees bow down when sunk (the bow is the root prim's +X; use a minus value for -X)
float SINK_ROLL     = 6.0;    // degrees list to one side when sunk
float RISE_TIME     = 30.0;   // s to come back up after the sitter stands
float BOTTOM_GAP    = 0.5;    // m, the hull never goes closer than this to the sea floor
// ---- Seat ----
vector   SIT_POS    = <0.0, 0.0, 0.45>;   // sit target, relative to the root prim
rotation SIT_ROT    = ZERO_ROTATION;

float   FRAME  = 0.6;         // s per keyframe (27/45 s: keyframe times should be whole multiples of 1/45 s)
integer FRAMES = 10;          // keyframes per batch: a new 6 s batch is sent each time the last one ends

vector  home;
float   homeYaw;
float   lift;                 // m from the water surface up to the root prim, so the hull sits DRAFT deep
integer seated;
float   batchStart;           // when the batch now playing started, and how far sunk (0 afloat, 1 under) it was then
float   batchSunk;
integer batchSeated;

float wave(float t, float period, float phase)
{
    return llSin(TWO_PI * t / period + phase);
}

float clamp01(float x)
{
    if (x < 0.0) return 0.0;
    if (x > 1.0) return 1.0;
    return x;
}

// how far sunk the boat is dt seconds after the batch started
float sunkAfter(float dt)
{
    if (batchSeated) return clamp01(batchSunk + dt / SINK_TIME);
    return clamp01(batchSunk - dt / RISE_TIME);
}

// where the boat should be, and how it should be turned, at time t; start is where the boat is now
list pose(float t, float s, vector start)
{
    float e = s * s * (3.0 - 2.0 * s);            // eased sinking: slow start, slow finish
    float calm = 1.0 - 0.8 * e;                   // waves move a sunken boat much less

    vector p = home + <DRIFT_RADIUS * wave(t, DRIFT_PERIOD, 0.0),
                       DRIFT_RADIUS * wave(t, DRIFT_PERIOD * 1.37, 0.0), 0.0>;
    // several waves of unrelated periods, so the rocking never visibly repeats
    float heave = HEAVE * (0.6 * wave(t, 5.3, 0.0) + 0.4 * wave(t, 3.1, 1.3));
    p.z = llWater(ZERO_VECTOR) + lift - e * SINK_DEPTH + calm * heave;
    float floor = llGround(p - start) + BOTTOM_GAP + lift - DRAFT;
    if (p.z < floor) p.z = floor;

    float roll  = calm * ROLL_DEG  * (0.7 * wave(t, 6.1, 0.4) + 0.3 * wave(t, 2.9, 2.1)) + e * SINK_ROLL;
    float pitch = calm * PITCH_DEG * (0.6 * wave(t, 4.7, 0.9) + 0.4 * wave(t, 3.7, 0.0)) + e * SINK_PITCH;
    float yaw   = homeYaw + YAW_SWING_DEG * DEG_TO_RAD * (0.8 * wave(t, 97.0, 0.0) + 0.2 * wave(t, 41.0, 1.0));
    rotation r = llEuler2Rot(<roll, pitch, 0.0> * DEG_TO_RAD) * llEuler2Rot(<0.0, 0.0, yaw>);
    return [p, r];
}

// plan the next 6 s of motion from where the boat really is, and play it
nextBatch()
{
    vector start = llGetPos();
    vector at = start;
    rotation was = llGetRot();
    float t = llGetTime();
    batchSunk = sunkAfter(t - batchStart);    // how far the last batch got, even if it was cut short
    batchStart = t;
    batchSeated = seated;
    list frames = [];
    integer k;
    for (k = 1; k <= FRAMES; ++k)
    {
        list p = pose(t + k * FRAME, sunkAfter(k * FRAME), start);
        vector to = llList2Vector(p, 0);
        rotation r = llList2Rot(p, 1);
        // a keyframe's move is in region axes, its turn in the boat's own axes: r = turn * was
        frames += [to - at, r / was, FRAME];
        at = to;
        was = r;
    }
    llSetKeyframedMotion(frames, []);
}

default
{
    state_entry()
    {
        llSetKeyframedMotion([], []);
        if (llGetLinkNumber() > 1)
        {
            llOwnerSay("Put this script in the ROOT prim of the boat (the one that highlights yellow when you edit it).");
            return;
        }
        if (llGetInventoryNumber(INVENTORY_SCRIPT) > 1)
            llOwnerSay("There are other scripts in this prim. If one of them is the boat's own driving script, remove it: "
                + "it turns physics on, and a physical boat cannot be moved this way.");
        llSetStatus(STATUS_PHYSICS, FALSE);
        // keyframed motion needs the new land impact accounting: a convex hull root prim switches the linkset to it
        llSetLinkPrimitiveParamsFast(LINK_THIS, [PRIM_PHYSICS_SHAPE_TYPE, PRIM_PHYSICS_SHAPE_CONVEX]);
        llSitTarget(SIT_POS, SIT_ROT);
        llSetSitText("Sit");
        llSetClickAction(CLICK_ACTION_SIT);

        home = llGetPos();
        vector e = llRot2Euler(llGetRot());
        homeYaw = e.z;
        vector low = llList2Vector(llGetBoundingBox(llGetKey()), 0);
        lift = DRAFT - low.z;                     // low.z is how far the hull bottom is below the root prim
        seated = llAvatarOnSitTarget() != NULL_KEY;
        float water = llWater(ZERO_VECTOR);
        llOwnerSay("Afloat on the water at " + (string)llRound(water) + " m. If you are editing the boat, "
            + "close the edit window: it stands still while selected.");
        if (llGround(ZERO_VECTOR) > water - SINK_DEPTH - 1.0)
            llOwnerSay("The water here is shallow: the boat will touch bottom before it is fully under.");
        llResetTime();
        batchStart = 0.0;
        batchSunk = 0.0;
        batchSeated = seated;
        nextBatch();
        llSetTimerEvent(1.0);
    }

    on_rez(integer n)
    {
        llResetScript();
    }

    changed(integer c)
    {
        if (c & CHANGED_LINK)
        {
            integer now = llAvatarOnSitTarget() != NULL_KEY;
            if (now == seated) return;
            seated = now;
            if (seated) llOwnerSay("Someone sat down: the boat starts taking on water (" + (string)llRound(SINK_TIME) + " s to go under).");
            else        llOwnerSay("The sitter stood up: the boat comes back up.");
            if (llGetStatus(STATUS_PHYSICS))
            {
                llOwnerSay("Another script turned physics on. Remove the boat's other scripts.");
                llSetStatus(STATUS_PHYSICS, FALSE);
            }
            // start the new batch now, so sitting or standing shows at once
            llSetKeyframedMotion([], []);
            nextBatch();
        }
    }

    moving_end()
    {
        nextBatch();
    }

    // backup in case a batch ends without a moving_end
    timer()
    {
        if (llGetTime() > batchStart + FRAMES * FRAME + 1.0) nextBatch();
    }
}
