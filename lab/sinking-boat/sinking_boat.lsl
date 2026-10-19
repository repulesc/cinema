// Sinking Boat - a gag boat that sways and drifts on open water, and slowly sinks when someone sits in it.
// Drop into the ROOT prim of the boat. Place the boat on the water, then Reset Scripts: where it stands is home.
// The boat is moved with keyframed motion (non-physical, smooth, server side), so it cannot be pushed away,
// cannot wander off the parcel, and always rides at the water level of the region.

// ---- Floating ----
float FLOAT_HEIGHT  = 0.20;   // m, how high the root prim's centre rides above the water (tune so the hull sits right)
float HEAVE         = 0.12;   // m, up-and-down bob
float ROLL_DEG      = 4.0;    // side-to-side rock
float PITCH_DEG     = 1.8;    // bow-to-stern rock
float YAW_SWING_DEG = 25.0;   // how far the bow slowly swings round
// ---- Drift ----
float DRIFT_RADIUS  = 6.0;    // m, the boat wanders within this distance of home (keep it over deep water)
float DRIFT_PERIOD  = 700.0;  // s, a wander loop takes about this long (bigger = slower; 700 s is ~5 cm/s)
// ---- Sinking ----
float SINK_TIME     = 90.0;   // s from sitting down to fully under
float SINK_DEPTH    = 3.0;    // m below the floating height when fully sunk
float SINK_PITCH    = 12.0;   // degrees bow down when sunk (the bow is the root prim's +X; use a minus value for -X)
float SINK_ROLL     = 6.0;    // degrees list to one side when sunk
float RISE_TIME     = 30.0;   // s to come back up after the sitter stands
float BOTTOM_GAP    = 0.5;    // m, never go closer than this to the sea floor
// ---- Seat ----
vector   SIT_POS    = <0.0, 0.0, 0.45>;   // sit target, relative to the root prim
rotation SIT_ROT    = ZERO_ROTATION;

float STEP = 0.5;             // s between motion updates
float LEAD = 0.625;           // s each motion segment lasts: a little longer than STEP so the boat never stops between them

vector home;
float  homeYaw;
float  sunk;                  // 0 = afloat, 1 = fully sunk
integer seated;

float wave(float t, float period, float phase)
{
    return llSin(TWO_PI * t / period + phase);
}

// where the boat should be, and how it should be turned, at time t
list pose(float t, vector here)
{
    float e = sunk * sunk * (3.0 - 2.0 * sunk);   // eased sinking: slow start, slow finish
    float calm = 1.0 - 0.8 * e;                   // waves move a sunken boat much less

    vector p = home + <DRIFT_RADIUS * wave(t, DRIFT_PERIOD, 0.0),
                       DRIFT_RADIUS * wave(t, DRIFT_PERIOD * 1.37, 0.0), 0.0>;
    // several waves of unrelated periods, so the rocking never visibly repeats
    float heave = HEAVE * (0.6 * wave(t, 5.3, 0.0) + 0.4 * wave(t, 3.1, 1.3));
    p.z = llWater(ZERO_VECTOR) + FLOAT_HEIGHT - e * SINK_DEPTH + calm * heave;
    float floor = llGround(p - here) + BOTTOM_GAP;
    if (p.z < floor) p.z = floor;

    float roll  = calm * ROLL_DEG  * (0.7 * wave(t, 6.1, 0.4) + 0.3 * wave(t, 2.9, 2.1)) + e * SINK_ROLL;
    float pitch = calm * PITCH_DEG * (0.6 * wave(t, 4.7, 0.9) + 0.4 * wave(t, 3.7, 0.0)) + e * SINK_PITCH;
    float yaw   = homeYaw + YAW_SWING_DEG * DEG_TO_RAD * (0.8 * wave(t, 97.0, 0.0) + 0.2 * wave(t, 41.0, 1.0));
    rotation r = llEuler2Rot(<roll, pitch, 0.0> * DEG_TO_RAD) * llEuler2Rot(<0.0, 0.0, yaw>);
    return [p, r];
}

default
{
    state_entry()
    {
        llSetKeyframedMotion([], [KFM_COMMAND, KFM_CMD_STOP]);
        llSetStatus(STATUS_PHYSICS, FALSE);
        llSitTarget(SIT_POS, SIT_ROT);
        llSetSitText("Sit");
        llSetClickAction(CLICK_ACTION_SIT);
        home = llGetPos();
        vector e = llRot2Euler(llGetRot());
        homeYaw = e.z;
        sunk = 0.0;
        seated = llAvatarOnSitTarget() != NULL_KEY;
        if (llGround(ZERO_VECTOR) > llWater(ZERO_VECTOR) - SINK_DEPTH)
            llOwnerSay("The water here is shallow: the boat will touch bottom before it is fully under.");
        llResetTime();
        llSetTimerEvent(STEP);
    }

    on_rez(integer n)
    {
        llResetScript();
    }

    changed(integer c)
    {
        if (c & CHANGED_LINK) seated = llAvatarOnSitTarget() != NULL_KEY;
    }

    timer()
    {
        if (seated) sunk += STEP / SINK_TIME;
        else        sunk -= STEP / RISE_TIME;
        if (sunk > 1.0) sunk = 1.0;
        if (sunk < 0.0) sunk = 0.0;

        vector here = llGetPos();
        list target = pose(llGetTime() + LEAD, here);
        // each segment starts from where the boat really is, so small errors never add up
        llSetKeyframedMotion([llList2Vector(target, 0) - here,
                              (ZERO_ROTATION / llGetRot()) * llList2Rot(target, 1),
                              LEAD], []);
    }
}
