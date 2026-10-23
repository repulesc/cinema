// ============================================================================
//  Take 12 Watch  -  take12_watch.lsl  (v6.8)  - free, one script, one prim HUD
//  For friends without Take 12: when someone near you connects with Take 12, you are connected at once (wearing it is
//  the yes) and see the camera of whoever films. Nobody filming: your own camera, still connected. Double-tap this
//  HUD: the next view, for everyone. Orbit your own camera to look around; Esc brings you back. Any movement key:
//  your own camera for a moment (4 s still and the shared view is back). A single tap: disconnect. Whoever starts
//  filming next is followed by itself. It cannot film: it has no camera of its own.
//  Speaks the same "T12|..." messages on the same channel as sync.lsl (docs/CONNECT.md).
// ============================================================================

string  VERSION = "6.8.2";
integer SYNC_CH = -7712120;
float   NEAR    = 20.0;
float   TAP_GAP = 0.35;
integer GONE    = 25;        // s  no camera and no heartbeat from the director: it is gone

key     gOwner;
key     gHost = NULL_KEY;    // whose view you follow (6.8.1: an unset key is "", not NULL_KEY)
string  gHostN;              // ... their name (kept: llKey2Name is "" once they have left the region)
float   gNoteT;              // a note above the HUD ("... camera is gone") until then + 4 s
string  gCam;                // the director's last camera, as sent: re-placed when your own lens changes
float   gMyFov;              // your lens when it was placed
vector  gApplied;            // the camera last set from it
float   gApplyT;             // ... and until when it may still be moving there
integer gIsAway;             // you are looking around on your own
integer gHeld;               // nobody films: your own camera, still connected
float   gOwnT;               // a movement key: your own camera since (0: following)
integer gHearT;              // the last word from the director
integer gBeatT;              // your last heartbeat to the director (it sees you are connected)
string  gShownS;             // the text above the HUD now
float   gTapT;
integer gTaps;
integer gTapPend;

// the director's camera through YOUR lens: the same line to the same focus, at the distance that gives the same
// picture size (k = tan(theirs / 2) / tan(yours / 2)); a wall on the way stops it 0.3 m short. again: your zoom changed
place(integer again)
{
    list L = llParseStringKeepNulls(gCam, ["|"], []);
    vector p = (vector)llList2String(L, 0);
    vector f = (vector)llList2String(L, 1);
    float lag = (float)llList2String(L, 2);
    float df = (float)llList2String(L, 3);
    gMyFov = llGetCameraFOV();
    if (again) lag = 0.5;
    if (df > 0.05 && gMyFov > 0.05)
    {
        float k = llTan(df * 0.5) / llTan(gMyFov * 0.5);
        if (k < 0.2) k = 0.2;
        if (k > 5.0) k = 5.0;
        vector q = f + (p - f) * k;
        list r = llCastRay(f, q, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
        if (llList2Integer(r, -1) > 0) q = llList2Vector(r, 1) + llVecNorm(f - q) * 0.3;
        p = q;
    }
    gApplied = p;
    gApplyT = llGetTime() + lag + 2.0;
    llSetCameraParams([CAMERA_ACTIVE, TRUE, CAMERA_POSITION, p, CAMERA_FOCUS, f,
        CAMERA_POSITION_LOCKED, TRUE, CAMERA_FOCUS_LOCKED, TRUE, CAMERA_POSITION_LAG, lag, CAMERA_FOCUS_LAG, lag,
        CAMERA_POSITION_THRESHOLD, 0.0, CAMERA_FOCUS_THRESHOLD, 0.0]);
}

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
    string s = "⇄ " + gHostN + " films\ndouble-tap: next · tap: disconnect";
    if (llGetUnixTime() - gHearT > 15) s = "⇄ " + gHostN + " · no signal…";
    else if (gHeld) s = "⇄ Connected with " + gHostN + " · nobody films";
    else if (gOwnT > 0.0) s = "⇄ " + gHostN + " films · your camera for a moment";
    else if (gIsAway) s = "⇄ " + gHostN + " films · looking around (Esc: back)";
    if (s != gShownS) llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gShownS = s;
}

follow(key host, string n)
{
    gHost = host;
    gHeld = FALSE;
    gHostN = n;
    gCam = "";
    gIsAway = FALSE;
    gOwnT = 0.0;
    gApplied = ZERO_VECTOR;
    gHearT = llGetUnixTime();
    gBeatT = gHearT;
    gShownS = "";
    say(gHost, "join|W");                                   // W: a Watch, it cannot lead (no "Pass camera" to it)
    if (llGetPermissions() & PERMISSION_TAKE_CONTROLS) llTakeControls(831, TRUE, TRUE);
    shown();
    llSetTimerEvent(1.0);
}

leave(integer tell, integer clear, string why)
{
    if (gHost == NULL_KEY) return;
    if (tell) say(gHost, "leave");
    gHost = NULL_KEY;
    gCam = "";
    // taking the HUD off: Second Life has already withdrawn the camera and gives it back by itself
    clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;
    if (clear && (llGetPermissions() & PERMISSION_CONTROL_CAMERA)) llClearCameraParams();
    if (clear && (llGetPermissions() & PERMISSION_TAKE_CONTROLS)) llTakeControls(831, FALSE, TRUE);
    llSetText(why, <1.0, 1.0, 1.0>, 0.85);
    gNoteT = llGetTime();
    llSetTimerEvent(1.0);                                   // the note for 4 s, then a clean screen
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
        llRegionSay(SYNC_CH, "T12|reset");                  // 6.8.2: restarted: the one you followed lets go of you now
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
            if (gHost == NULL_KEY) llOwnerSay("Take 12 Watch: when someone near you connects with Take 12, their camera comes up here by itself.");
            else if (gTaps >= 2) say(gHost, "next");         // double-tap: the next view for everyone
            else leave(TRUE, TRUE, "Disconnected");          // tap: disconnect, your own camera back
        }
        if (gHost != NULL_KEY && gCam != "" && llFabs(llGetCameraFOV() - gMyFov) > 0.004) place(TRUE);   // you zoomed: same picture
        if (gHost != NULL_KEY && llGetUnixTime() - gBeatT >= 10)
        {
            gBeatT = llGetUnixTime();
            say(gHost, "hb");                                // your heartbeat: the director sees you are connected
        }
        if (gHost != NULL_KEY && gOwnT > 0.0 && llGetTime() - gOwnT > 4.0)
        {
            gOwnT = 0.0;                                     // still again: back on the shared view
            say(gHost, "back");
            if (gCam != "" && !gHeld) place(FALSE);
        }
        if (gHost != NULL_KEY) shown();
        if (gHost != NULL_KEY)
        {
            if (llGetUnixTime() - gHearT > GONE) leave(FALSE, TRUE, gHostN + " is gone · disconnected");
            // your own camera (Alt-orbit) while watching: looking around; Esc puts it back on the shared view
            else if (gApplied != ZERO_VECTOR && gOwnT == 0.0 && !gHeld && llGetTime() > gApplyT && (llGetPermissions() & PERMISSION_TRACK_CAMERA))
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
        if (gHost == NULL_KEY && llGetTime() - gNoteT < 4.0) llSetTimerEvent(1.0);    // the note stays its 4 s
        else if (gHost == NULL_KEY)
        {
            llSetText("", ZERO_VECTOR, 0.0);
            llSetTimerEvent(0.0);
        }
        else llSetTimerEvent(1.0);
    }

    // a movement key: your own camera for a moment; you stay connected
    control(key id, integer level, integer edge)
    {
        if (gHost == NULL_KEY || !(level | edge)) return;
        if (gOwnT == 0.0)
        {
            if (llGetPermissions() & PERMISSION_CONTROL_CAMERA) llClearCameraParams();
            say(gHost, "away");
            gOwnT = llGetTime();
            shown();
        }
        gOwnT = llGetTime();
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
            if (gHost != NULL_KEY) { st = "view"; d = gHostN; }
            say(who, "here|W|" + st + "|" + d);
        }
        else if (w == "invite")
        {
            if (gHost != NULL_KEY) say(who, "busy|connected with " + gHostN);
            else if (near(who))
            {
                say(who, "ack|1");                           // wearing the Watch is the yes: their view at once
                follow(who, llKey2Name(who));
            }
        }
        else if (who != gHost) return;
        else if (w == "cam" && (llGetPermissions() & PERMISSION_CONTROL_CAMERA))
        {
            gHearT = llGetUnixTime();
            gCam = llDumpList2String(llList2List(L, 2, -1), "|");    // pos | focus | lag | their lens (6.0.1)
            gHeld = FALSE;
            if (gOwnT == 0.0) place(FALSE);
        }
        else if (w == "hb") gHearT = llGetUnixTime();
        else if (w == "pause")
        {
            gHearT = llGetUnixTime();
            gHeld = TRUE;                                   // nobody films: your own camera, still connected
            if (llGetPermissions() & PERMISSION_CONTROL_CAMERA) llClearCameraParams();
            shown();
        }
        else if (w == "director") follow((key)llList2String(L, 2), llList2String(L, 3));   // someone else films now
        else if (w == "kick") leave(FALSE, TRUE, gHostN + " disconnected you");
        else if (w == "end" || w == "reset") leave(FALSE, TRUE, gHostN + " disconnected");   // 6.8.2: their HUD restarted
    }
}
