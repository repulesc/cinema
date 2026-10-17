// ============================================================================
//  Take 12  -  cinema_lens.lsl  (v5.0)  - the framing keys in Friends
//  Closeness (gears), the seated camera angle, and Tune: where the faces really are on a bed, a sofa or the ground,
//  remembered per seat. Core forwards the movement keys as NUDGE; this script turns them into a LENS message for
//  the Friends camera. The name of a change shows for 3 s, then the screen is clean.
//    seated or lying:  W/S closer/wider   E/C angle higher/lower   A/D round the group
//    standing:         E/C closer/wider   (W A S D walk)
//    Tune (long press > Tune): W/S/A/D move the aim across, E/C up/down; saved for this seat at once
// ============================================================================

string VERSION = "5.0.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer NUDGE      = 7317;
integer LENS       = 7319;   // lens -> friends  "<vneed half-height>|<nearest>|<body allowance>|<eye lift>|<angle deg>|<aim>|<round rad>"
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;

// gears: name, half-height the picture needs (m), nearest camera (m), extra body allowance seated (m), eye lift (m)
list GEARS = [
    "Auto",  0.0,  0.0, 0.0,  0.0,
    "Wide",  1.3,  6.0, 0.0,  0.0,
    "Group", 1.3,  3.0, 0.0,  0.0,
    "Half",  0.9,  2.0, 0.45, 0.1,
    "Close", 0.75, 1.2, 0.45, 0.15,
    "Faces", 0.45, 0.8, 0.3,  0.15
];
list ANGLES = [60, 45, 30, 15, 0];

key     gOwner;
integer gActive;             // Friends is running
integer gGear;               // 0 Auto .. 5 Faces
integer gAng;                // index in ANGLES
float   gAz;                 // round the group (radians)
vector  gAim;                // where the faces are, from the shot's centre, in the seat's frame
integer gTune;
integer gPrev;               // keys held at the last NUDGE
string  gSeat;               // this seat's store key ("" standing)
rotation gSeatRot;
float   gTextT;

// the seat you are on: the object, and where on it you sit (to 0.5 m), so each side or pose of a bed has its own aim
string seatKey()
{
    if (!(llGetAgentInfo(gOwner) & AGENT_SITTING)) return "";
    list d = llGetObjectDetails(gOwner, [OBJECT_ROOT, OBJECT_POS]);
    key root = llList2Key(d, 0);
    list o = llGetObjectDetails(root, [OBJECT_POS, OBJECT_ROT]);
    if (root == gOwner || llGetListLength(o) < 2) return "";
    gSeatRot = llList2Rot(o, 1);
    vector v = (llList2Vector(d, 1) - llList2Vector(o, 0)) / gSeatRot;
    return "cin.seat." + (string)root + "." + (string)llRound(v.x * 2.0) + "," + (string)llRound(v.y * 2.0) + "," + (string)llRound(v.z * 2.0);
}

// sat down, stood up or moved to another seat: its saved aim (or none)
seat()
{
    string k = seatKey();
    if (k == gSeat) return;
    gSeat = k;
    gAim = ZERO_VECTOR;
    if (k != "") gAim = (vector)llLinksetDataReadProtected(k, PASS);
    gTune = gTune && (k != "");
}

send()
{
    integer g = gGear * 5;
    llMessageLinked(LINK_SET, LENS, llDumpList2String(llList2List(GEARS, g + 1, g + 4)
        + [llList2Integer(ANGLES, gAng), (string)(gAim * gSeatRot), (string)gAz], "|"), "");
}

show(string s)
{
    llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gTextT = llGetTime();
}

gear(integer d)
{
    if (gGear == 0) gGear = 3 + d;                          // from Auto: closer goes to Close, wider to Group
    else gGear += d;
    if (gGear > 5) gGear = 5;
    if (gGear < 0) gGear = 0;
    show(llList2String(GEARS, gGear * 5));
}

// one key press; cr = your camera, so in Tune W moves the aim away from you on screen, A to the left
press(integer k, rotation cr)
{
    integer sit = (gSeat != "");
    if (gTune)
    {
        vector f = llRot2Fwd(cr);
        f.z = 0.0;
        f = llVecNorm(f);
        vector m;
        if (k & CONTROL_FWD) m = f * 0.1;
        if (k & CONTROL_BACK) m = f * -0.1;
        if (k & (CONTROL_LEFT | CONTROL_ROT_LEFT)) m = <-f.y, f.x, 0.0> * 0.1;
        if (k & (CONTROL_RIGHT | CONTROL_ROT_RIGHT)) m = <f.y, -f.x, 0.0> * 0.1;
        if (k & CONTROL_UP) m.z = 0.05;
        if (k & CONTROL_DOWN) m.z = -0.05;
        gAim += m / gSeatRot;                               // kept in the seat's frame: right however the bed is turned
        llLinksetDataWriteProtected(gSeat, (string)gAim, PASS);
        show("Tune: aim at your faces");
    }
    else if (sit)
    {
        if (k & CONTROL_FWD) gear(1);
        if (k & CONTROL_BACK) gear(-1);
        if (k & (CONTROL_UP | CONTROL_DOWN))
        {
            if (k & CONTROL_UP) { if (gAng > 0) gAng--; }
            else if (gAng < 4) gAng++;
            show((string)llList2Integer(ANGLES, gAng) + "°");
        }
        if (k & (CONTROL_LEFT | CONTROL_ROT_LEFT)) gAz += 0.35;
        if (k & (CONTROL_RIGHT | CONTROL_ROT_RIGHT)) gAz -= 0.35;
    }
    else
    {
        if (k & CONTROL_UP) gear(1);
        else if (k & CONTROL_DOWN) gear(-1);
        else return;                                        // walking
    }
    send();
}

loadAng()
{
    gAng = llListFindList(ANGLES, [(integer)llLinksetDataReadProtected("cin.seat_deg", PASS)]);
    if (gAng < 0) gAng = 1;
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        gSeatRot = ZERO_ROTATION;
        loadAng();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "lens");
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == START)
        {
            gActive = (llList2String(llParseString2List(str, ["|"], []), 0) == "friends");
            gPrev = 0;
            gTune = FALSE;
            gSeat = "-";
            if (!gActive) return;
            seat();
            send();
            llSetTimerEvent(1.0);
        }
        else if (num == STOP)
        {
            gActive = FALSE;
            gTune = FALSE;
            llSetText("", ZERO_VECTOR, 0.0);
            llSetTimerEvent(0.0);
        }
        else if (num == CFG_CHANGED)
        {
            loadAng();
            if (gActive) send();
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "lens");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/lens] v" + VERSION + " " + llList2String(GEARS, gGear * 5) + ", " + (string)llList2Integer(ANGLES, gAng)
                + " deg, tuned " + (string)(gAim != ZERO_VECTOR) + ", free mem " + (string)llGetFreeMemory());
        else if (!gActive) return;
        else if (num == NUDGE)
        {
            integer lv = (integer)str;
            integer k = lv & ~gPrev;
            gPrev = lv;
            if (k) press(k, (rotation)llList2String(llParseString2List(str, ["|"], []), 1));
        }
        else if (num == CMD && (str == "tune" || str == "untune"))
        {
            seat();
            if (gSeat == "") show("Tune: sit or lie down first");
            else if (str == "untune")
            {
                llLinksetDataDeleteProtected(gSeat, PASS);
                gAim = ZERO_VECTOR;
                gTune = FALSE;
                show("Tune cleared");
                send();
            }
            else
            {
                gTune = !gTune;
                if (gTune) show("Tune: aim at your faces\nW S A D across · E C up and down\nlong press > Tune when done");
                else show("Tuned for this seat");
            }
        }
    }

    timer()
    {
        if (gTextT > 0.0 && llGetTime() - gTextT > 3.0 + 5.0 * gTune)
        {
            gTextT = 0.0;
            llSetText("", ZERO_VECTOR, 0.0);
        }
        string before = gSeat;
        seat();
        if (gSeat != before) send();                        // sat down, stood up, changed seats
    }
}
