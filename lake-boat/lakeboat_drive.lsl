// "Seerose" lake boat -- single pilot drive script
//
// Put this in the ROOT prim (the uploaded boat mesh). The boat is NOT physical while parked;
// the script turns physics on when someone sits on the rowing thwart and off again when
// they stand up.
//
// Keys:  W / Up = row forward     S / Down = back water     A,D / Left,Right = steer
//
// Coordinates below are metres from the middle of the boat's bounding box (that is the
// root prim position). The boat's bow is local +X. The numbers come from the mesh generator
// (out/mesh/lakeboat_info.json); everything marked TUNE is meant to be adjusted in-world.

// ---------------------------------------------------------------- TUNE
vector   SIT_POS     = <-0.425, 0.0, 0.29>; // pilot on the rowing thwart (thwart top is z = -0.087)
rotation SIT_ROT     = ZERO_ROTATION;       // facing the bow
string   SIT_ANIM    = "";                  // name of an animation in inventory ("" = default sit)

float    MAX_FWD     = 3.0;   // m/s, rowing speed at full effort
float    MAX_REV     = 1.0;   // m/s, backing water
float    ACCEL       = 3.0;   // seconds to reach speed (bigger = lazier)
float    TURN_RATE   = 0.9;   // rad/s at full steer
float    HOVER       = 0.20;  // height of the boat's centre above the water surface. The centre
                              // sits 0.386 m above the keel, so 0.20 puts the keel ~0.19 m deep.

vector   CAM_EYE     = <-7.5, 0.0, 2.6>;    // camera behind and above the boat
vector   CAM_AT      = <1.5, 0.0, 0.6>;     // ...looking at a point ahead of the boat's centre

string   LOOP_SOUND  = "row_loop";          // optional sound in inventory (looped while moving)
integer  NUDGE_CH    = 77;                  // owner chat channel for sit-position nudges

// ---------------------------------------------------------------- state
key      gPilot  = NULL_KEY;
integer  gMoving = FALSE;
integer  gListen = 0;

setupVehicle()
{
    llSetVehicleType(VEHICLE_TYPE_BOAT);

    // floats on water only, pushes up but never pulls down, stays upright (rolls a little)
    llSetVehicleFlags(VEHICLE_FLAG_HOVER_WATER_ONLY | VEHICLE_FLAG_HOVER_UP_ONLY
                      | VEHICLE_FLAG_LIMIT_ROLL_ONLY);
    llSetVehicleFloatParam(VEHICLE_HOVER_HEIGHT,     HOVER);
    llSetVehicleFloatParam(VEHICLE_HOVER_EFFICIENCY, 0.6);
    llSetVehicleFloatParam(VEHICLE_HOVER_TIMESCALE,  1.5);
    llSetVehicleFloatParam(VEHICLE_BUOYANCY,         0.0);

    // water grip: slides a little sideways, barely at all along the keel
    llSetVehicleVectorParam(VEHICLE_LINEAR_FRICTION_TIMESCALE,  <3.0, 0.8, 1.0>);
    llSetVehicleVectorParam(VEHICLE_ANGULAR_FRICTION_TIMESCALE, <5.0, 5.0, 1.5>);

    // keep the motors on while a key is held (the control() event only fires on changes)
    llSetVehicleFloatParam(VEHICLE_LINEAR_MOTOR_TIMESCALE,       ACCEL);
    llSetVehicleFloatParam(VEHICLE_LINEAR_MOTOR_DECAY_TIMESCALE, 120.0);
    llSetVehicleFloatParam(VEHICLE_ANGULAR_MOTOR_TIMESCALE,      0.6);
    llSetVehicleFloatParam(VEHICLE_ANGULAR_MOTOR_DECAY_TIMESCALE, 120.0);

    // self-righting, plus a gentle lean into turns
    llSetVehicleFloatParam(VEHICLE_VERTICAL_ATTRACTION_EFFICIENCY, 0.6);
    llSetVehicleFloatParam(VEHICLE_VERTICAL_ATTRACTION_TIMESCALE,  2.0);
    llSetVehicleFloatParam(VEHICLE_BANKING_EFFICIENCY, -0.2);
    llSetVehicleFloatParam(VEHICLE_BANKING_MIX,        0.8);
    llSetVehicleFloatParam(VEHICLE_BANKING_TIMESCALE,  1.0);
}

startWake()
{
    llParticleSystem([
        PSYS_PART_FLAGS, PSYS_PART_INTERP_COLOR_MASK | PSYS_PART_INTERP_SCALE_MASK
                         | PSYS_PART_EMISSIVE_MASK | PSYS_PART_FOLLOW_VELOCITY_MASK,
        PSYS_SRC_PATTERN, PSYS_SRC_PATTERN_ANGLE_CONE,
        PSYS_SRC_ANGLE_BEGIN, 1.2, PSYS_SRC_ANGLE_END, 1.5,
        PSYS_PART_START_COLOR, <0.85, 0.92, 0.95>, PSYS_PART_END_COLOR, <0.85, 0.92, 0.95>,
        PSYS_PART_START_ALPHA, 0.35, PSYS_PART_END_ALPHA, 0.0,
        PSYS_PART_START_SCALE, <0.18, 0.18, 0.0>, PSYS_PART_END_SCALE, <0.7, 0.7, 0.0>,
        PSYS_SRC_BURST_RATE, 0.08, PSYS_SRC_BURST_PART_COUNT, 2,
        PSYS_SRC_BURST_RADIUS, 0.55,
        PSYS_SRC_BURST_SPEED_MIN, 0.05, PSYS_SRC_BURST_SPEED_MAX, 0.25,
        PSYS_PART_MAX_AGE, 2.6, PSYS_SRC_MAX_AGE, 0.0
    ]);
}

setMoving(integer on)
{
    if (on == gMoving) return;
    gMoving = on;
    if (on) {
        startWake();
        if (llGetInventoryType(LOOP_SOUND) == INVENTORY_SOUND) llLoopSound(LOOP_SOUND, 0.4);
    } else {
        llParticleSystem([]);
        llStopSound();
    }
}

park()
{
    llSetTimerEvent(0.0);
    setMoving(FALSE);
    llSetVehicleVectorParam(VEHICLE_LINEAR_MOTOR_DIRECTION,  ZERO_VECTOR);
    llSetVehicleVectorParam(VEHICLE_ANGULAR_MOTOR_DIRECTION, ZERO_VECTOR);
    llSetStatus(STATUS_PHYSICS, FALSE);
    llReleaseControls();
    gPilot = NULL_KEY;
}

applySitTarget()
{
    llSitTarget(SIT_POS, SIT_ROT);
}

default
{
    state_entry()
    {
        llSetSitText("Row");
        llSetStatus(STATUS_PHYSICS, FALSE);
        applySitTarget();
        llSetCameraEyeOffset(CAM_EYE);
        llSetCameraAtOffset(CAM_AT);
        setupVehicle();
        if (gListen) llListenRemove(gListen);
        gListen = llListen(NUDGE_CH, "", llGetOwner(), "");
        llOwnerSay("Seerose ready. Sit on the boat to row. Owner: say /" + (string)NUDGE_CH
            + " up|down|fwd|back|left|right to nudge the seat, then stand up and sit again.");
    }

    on_rez(integer p) { llResetScript(); }

    changed(integer c)
    {
        if (c & CHANGED_LINK) {
            key who = llAvatarOnSitTarget();
            if (who != NULL_KEY && gPilot == NULL_KEY) {
                gPilot = who;
                llRequestPermissions(who, PERMISSION_TAKE_CONTROLS | PERMISSION_TRIGGER_ANIMATION);
            } else if (who == NULL_KEY && gPilot != NULL_KEY) {
                park();
            }
        }
    }

    run_time_permissions(integer perm)
    {
        if (perm & PERMISSION_TAKE_CONTROLS) {
            llTakeControls(CONTROL_FWD | CONTROL_BACK | CONTROL_LEFT | CONTROL_RIGHT
                           | CONTROL_ROT_LEFT | CONTROL_ROT_RIGHT, TRUE, FALSE);
        }
        if ((perm & PERMISSION_TRIGGER_ANIMATION) && SIT_ANIM != ""
            && llGetInventoryType(SIT_ANIM) == INVENTORY_ANIMATION) {
            llStopAnimation("sit");
            llStartAnimation(SIT_ANIM);
        }
        llSetStatus(STATUS_PHYSICS, TRUE);
        llSetTimerEvent(0.5);
    }

    control(key id, integer level, integer edge)
    {
        vector lin = ZERO_VECTOR;
        vector ang = ZERO_VECTOR;

        if (level & CONTROL_FWD)       lin.x =  MAX_FWD;
        else if (level & CONTROL_BACK) lin.x = -MAX_REV;

        if (level & (CONTROL_LEFT  | CONTROL_ROT_LEFT))  ang.z += TURN_RATE;
        if (level & (CONTROL_RIGHT | CONTROL_ROT_RIGHT)) ang.z -= TURN_RATE;

        llSetVehicleVectorParam(VEHICLE_LINEAR_MOTOR_DIRECTION,  lin);
        llSetVehicleVectorParam(VEHICLE_ANGULAR_MOTOR_DIRECTION, ang);
    }

    timer()
    {
        // wake + sound only while actually under way
        setMoving(llVecMag(llGetVel()) > 0.4);
    }

    listen(integer ch, string name, key id, string msg)
    {
        float step = 0.02;
        if      (msg == "up")    SIT_POS.z += step;
        else if (msg == "down")  SIT_POS.z -= step;
        else if (msg == "fwd")   SIT_POS.x += step;
        else if (msg == "back")  SIT_POS.x -= step;
        else if (msg == "left")  SIT_POS.y += step;
        else if (msg == "right") SIT_POS.y -= step;
        else return;
        applySitTarget();
        llOwnerSay("SIT_POS = " + (string)SIT_POS + "  (stand up and sit again to apply; paste this into the script to keep it)");
    }
}
