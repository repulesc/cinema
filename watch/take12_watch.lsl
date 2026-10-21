// ============================================================================
//  Take 12 Watch  -  take12_watch.lsl  (v5.4)  - free, one script, one prim HUD
//  For friends without Take 12: when someone near you shares their Take 12 view, your camera follows their cuts at
//  once (wearing it is the yes). Double-tap this HUD: the next view, for everyone watching. Orbit your own camera to
//  look around (the director is told); Esc brings you back. A single tap or any movement key: your own camera back.
//  When another Take 12 owner takes over as director, you follow them by yourself.
//  Speaks the same "T12|..." messages on the same channel as cinema_sync.lsl.
// ============================================================================

string  VERSION = "5.4.0";
integer SYNC_CH = -7712120;
float   NEAR    = 20.0;
float   TAP_GAP = 0.35;

key     gOwner;
key     gHost;               // whose view you follow
vector  gApplied;            // the camera last set from it
float   gApplyT;             // ... and until when it may still be moving there
integer gIsAway;             // you are looking around on your own
float   gTapT;
integer gTaps;
integer gTapPend;

say(key k, string m)
{
    llRegionSayTo(k, SYNC_CH, "T12|" + m);
}

integer near(key k)
{
    list d = llGetObjectDetails(k, [OBJECT_POS]);
    return (llGetListLength(d) > 0 && llVecDist(llList2Vector(d, 0), llGetPos()) <= NEAR);
}

shown()
{
    string s = "Watching " + llKey2Name(gHost) + "\ntap: your camera · double-tap: next";
    if (gIsAway) s = "Looking around · Esc: back to " + llKey2Name(gHost) + "'s view";
    llSetText(s, <1.0, 1.0, 1.0>, 0.85);
}

follow(key host)
{
    gHost = host;
    gIsAway = FALSE;
    gApplied = ZERO_VECTOR;
    say(gHost, "join");
    shown();
    llSetTimerEvent(0.25);
}

leave(integer tell, integer clear)
{
    if (gHost == NULL_KEY) return;
    if (tell) say(gHost, "leave");
    gHost = NULL_KEY;
    // taking the HUD off: Second Life has already withdrawn the camera and gives it back by itself
    clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;
    if (clear && (llGetPermissions() & PERMISSION_CONTROL_CAMERA)) llClearCameraParams();
    if (clear && (llGetPermissions() & PERMISSION_TAKE_CONTROLS)) llTakeControls(831, FALSE, TRUE);
    llSetText("", ZERO_VECTOR, 0.0);
}

perms()
{
    llRequestPermissions(gOwner, PERMISSION_CONTROL_CAMERA | PERMISSION_TAKE_CONTROLS | PERMISSION_TRACK_CAMERA);
}

default
{
    state_entry()
    {
        gOwner = llGetOwner();
        llSetText("", ZERO_VECTOR, 0.0);
        llListen(SYNC_CH, "", NULL_KEY, "");
        if (llGetAttached()) perms();
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
    }

    attach(key id)
    {
        if (id == NULL_KEY) leave(TRUE, FALSE);             // taken off: only tell the director
        else perms();
    }

    touch_start(integer n)
    {
        if (llDetectedKey(0) != gOwner) return;
        float now = llGetTime();
        if (now - gTapT < TAP_GAP) gTaps++;
        else gTaps = 1;
        gTapT = now;
        gTapPend = TRUE;
        llSetTimerEvent(0.1);
    }

    timer()
    {
        if (gTapPend && llGetTime() - gTapT > TAP_GAP)
        {
            gTapPend = FALSE;
            if (gHost == NULL_KEY) llOwnerSay("Take 12 Watch: when someone near you shares their Take 12 view, it comes up here by itself.");
            else if (gTaps >= 2) say(gHost, "next");         // double-tap: the next view for everyone
            else leave(TRUE, TRUE);                           // tap: your own camera back
        }
        // your own camera (Alt-orbit) while watching: looking around; Esc puts it back on the shared view
        if (gHost != NULL_KEY && gApplied != ZERO_VECTOR && llGetTime() > gApplyT && (llGetPermissions() & PERMISSION_TRACK_CAMERA))
        {
            float d = llVecDist(llGetCameraPos(), gApplied);
            if (!gIsAway && d > 0.6)
            {
                gIsAway = TRUE;
                say(gHost, "away");
                shown();
            }
            else if (gIsAway && d < 0.3)
            {
                gIsAway = FALSE;
                say(gHost, "back");
                shown();
            }
        }
        if (gHost == NULL_KEY && !gTapPend) llSetTimerEvent(0.0);
        else if (!gTapPend) llSetTimerEvent(1.0);
    }

    control(key id, integer level, integer edge)
    {
        if (edge & level) leave(TRUE, TRUE);
    }

    listen(integer ch, string name, key id, string msg)
    {
        if (llGetSubString(msg, 0, 3) != "T12|") return;
        key who = llGetOwnerKey(id);
        if (who == gOwner) return;
        list L = llParseStringKeepNulls(msg, ["|"], []);
        string w = llList2String(L, 1);
        if (w == "offer" && gHost == NULL_KEY && near(who))
        {
            say(who, "ack|1");                               // so the director sees who got it
            follow(who);                                     // wearing the Watch is the yes: their view at once
            if (llGetPermissions() & PERMISSION_TAKE_CONTROLS) llTakeControls(831, TRUE, TRUE);
        }
        else if (who == gHost && w == "director") follow((key)llList2String(L, 2));   // someone else directs now
        else if (who == gHost && w == "cam" && (llGetPermissions() & PERMISSION_CONTROL_CAMERA))
        {
            float lag = (float)llList2String(L, 4);
            gApplied = (vector)llList2String(L, 2);
            gApplyT = llGetTime() + lag + 2.0;
            llSetCameraParams([CAMERA_ACTIVE, TRUE, CAMERA_POSITION, gApplied, CAMERA_FOCUS, (vector)llList2String(L, 3),
                CAMERA_POSITION_LOCKED, TRUE, CAMERA_FOCUS_LOCKED, TRUE, CAMERA_POSITION_LAG, lag, CAMERA_FOCUS_LAG, lag,
                CAMERA_POSITION_THRESHOLD, 0.0, CAMERA_FOCUS_THRESHOLD, 0.0]);
        }
        else if (who == gHost && w == "end") leave(FALSE, TRUE);
    }
}
