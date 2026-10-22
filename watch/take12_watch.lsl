// ============================================================================
//  Take 12 Watch  -  take12_watch.lsl  (v5.5)  - free, one script, one prim HUD
//  For friends without Take 12: when someone near you goes live with Take 12 and invites you, your camera follows
//  theirs at once (wearing it is the yes). Double-tap this HUD: the next view, for everyone watching. Orbit your own
//  camera to look around (the director is told); Esc brings you back. A single tap or any movement key: your own
//  camera back. A new director (a hand-over) is followed by itself. It cannot lead: it has no camera of its own.
//  Speaks the same "T12|..." messages on the same channel as cinema_sync.lsl (docs/SHARING.md).
// ============================================================================

string  VERSION = "5.8.0";
integer SYNC_CH = -7712120;
float   NEAR    = 20.0;
float   TAP_GAP = 0.35;
integer GONE    = 25;        // s  no camera and no heartbeat from the director: it is gone

key     gOwner;
key     gHost;               // whose view you follow
vector  gApplied;            // the camera last set from it
float   gApplyT;             // ... and until when it may still be moving there
integer gIsAway;             // you are looking around on your own
integer gHearT;              // the last word from the director
integer gBeatT;              // your last heartbeat to the director (it sees you are connected)
string  gShownS;             // the text above the HUD now
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
    string s = "👁 " + llKey2Name(gHost) + "\ntap: your camera · double-tap: next";
    if (llGetUnixTime() - gHearT > 15) s = "👁 " + llKey2Name(gHost) + " · no signal…";
    else if (gIsAway) s = "👁 " + llKey2Name(gHost) + " · looking around (Esc: back)";
    if (s != gShownS) llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gShownS = s;
}

follow(key host)
{
    gHost = host;
    gIsAway = FALSE;
    gApplied = ZERO_VECTOR;
    gHearT = llGetUnixTime();
    gBeatT = gHearT;
    gShownS = "";
    say(gHost, "join");
    if (llGetPermissions() & PERMISSION_TAKE_CONTROLS) llTakeControls(831, TRUE, TRUE);
    shown();
    llSetTimerEvent(1.0);
}

leave(integer tell, integer clear, string why)
{
    if (gHost == NULL_KEY) return;
    if (tell) say(gHost, "leave");
    gHost = NULL_KEY;
    // taking the HUD off: Second Life has already withdrawn the camera and gives it back by itself
    clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;
    if (clear && (llGetPermissions() & PERMISSION_CONTROL_CAMERA)) llClearCameraParams();
    if (clear && (llGetPermissions() & PERMISSION_TAKE_CONTROLS)) llTakeControls(831, FALSE, TRUE);
    llSetText(why, <1.0, 1.0, 1.0>, 0.85);
    llSetTimerEvent(4.0);                                   // the note, then a clean screen
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
        if (c & CHANGED_REGION) leave(FALSE, TRUE, "");     // sharing does not cross regions
    }

    attach(key id)
    {
        if (id == NULL_KEY) leave(TRUE, FALSE, "");         // taken off: only tell the director
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
            if (gHost == NULL_KEY) llOwnerSay("Take 12 Watch: when someone near you goes live with Take 12, their view comes up here by itself.");
            else if (gTaps >= 2) say(gHost, "next");         // double-tap: the next view for everyone
            else leave(TRUE, TRUE, "Your camera");           // tap: your own camera back
        }
        if (gHost != NULL_KEY && llGetUnixTime() - gBeatT >= 10)
        {
            gBeatT = llGetUnixTime();
            say(gHost, "hb");                                // your heartbeat: the director sees you are connected
        }
        if (gHost != NULL_KEY) shown();
        if (gHost != NULL_KEY)
        {
            if (llGetUnixTime() - gHearT > GONE) leave(FALSE, TRUE, llKey2Name(gHost) + "'s camera is gone");
            // your own camera (Alt-orbit) while watching: looking around; Esc puts it back on the shared view
            else if (gApplied != ZERO_VECTOR && llGetTime() > gApplyT && (llGetPermissions() & PERMISSION_TRACK_CAMERA))
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
        }
        if (gTapPend) return;
        if (gHost == NULL_KEY)
        {
            llSetText("", ZERO_VECTOR, 0.0);
            llSetTimerEvent(0.0);
        }
        else llSetTimerEvent(1.0);
    }

    control(key id, integer level, integer edge)
    {
        if (edge & level) leave(TRUE, TRUE, "Your camera");
    }

    listen(integer ch, string name, key id, string msg)
    {
        if (llGetSubString(msg, 0, 3) != "T12|") return;
        key who = llGetOwnerKey(id);
        if (who == gOwner) return;
        list L = llParseStringKeepNulls(msg, ["|"], []);
        string w = llList2String(L, 1);
        if (w == "who")
        {
            if (!near(who)) return;
            string st = "idle";
            string d = "";
            if (gHost != NULL_KEY) { st = "view"; d = llKey2Name(gHost); }
            say(who, "here|W|" + st + "|" + d);
        }
        else if (w == "invite")
        {
            if (gHost != NULL_KEY) say(who, "busy|watching " + llKey2Name(gHost));
            else if (near(who))
            {
                say(who, "ack|1");                           // wearing the Watch is the yes: their view at once
                follow(who);
            }
        }
        else if (who != gHost) return;
        else if (w == "cam" && (llGetPermissions() & PERMISSION_CONTROL_CAMERA))
        {
            gHearT = llGetUnixTime();
            float lag = (float)llList2String(L, 4);
            gApplied = (vector)llList2String(L, 2);
            gApplyT = llGetTime() + lag + 2.0;
            llSetCameraParams([CAMERA_ACTIVE, TRUE, CAMERA_POSITION, gApplied, CAMERA_FOCUS, (vector)llList2String(L, 3),
                CAMERA_POSITION_LOCKED, TRUE, CAMERA_FOCUS_LOCKED, TRUE, CAMERA_POSITION_LAG, lag, CAMERA_FOCUS_LAG, lag,
                CAMERA_POSITION_THRESHOLD, 0.0, CAMERA_FOCUS_THRESHOLD, 0.0]);
        }
        else if (w == "hb") gHearT = llGetUnixTime();
        else if (w == "director") follow((key)llList2String(L, 2));   // someone else leads now
        else if (w == "kick") leave(FALSE, TRUE, llKey2Name(gHost) + " stopped sharing with you");
        else if (w == "end") leave(FALSE, TRUE, llKey2Name(gHost) + " ended the live view");
    }
}
