// ============================================================================
//  Take 12  -  tracking.lsl  (8.0)  - Tracking: a cinematic follow camera
//  Shoulder · Film · Classic, L · R (cin.trk "<look 0-2>|<side 0 L / 1 R>"; Film · R the first time).
//    Shoulder  ~1.6 m, over one shoulder, at eye height, you filling a third
//    Film      ~3.5 m, a little low, you on your third; slow and steady (the cinematic one)
//    Classic   ~3 m, behind and a bit above, nearly centred: Second Life's own camera, smooth and wall-aware
//  L · R is the side of the picture you walk on, in every look. It is the viewer's own follow camera (FOLLOW to core:
//  distance, pitch, focus offset and lags), so it moves smoothly at every frame: a steadicam lag of about 0.5 s, easing
//  into turns; a U-turn swings round behind you. Height eases on stairs and slopes, short hops are ignored.
//  Walls: never through one. The camera pulls in closer behind you (rays from your head), and in a small closed room
//  (under about 4 × 4 m, measured with rays) it takes the room's best corner and pans with you (FOLLOW lock); out of the
//  room, behind you again. Running pulls it back about 30 %. Standing still, it holds; after 5 s the PORTRAIT word glows
//  once (a standing shot is ready). The lit tap: back into the look, behind you. Distances scale with your size.
//  Auto (8.3.0) lives here too, the walking camera knowing when you walk and stop: the director. On wear (once set
//  up) it picks the shot from what a script truly sees: walking, Tracking; standing still 6 s, Portrait (Medium · Us:
//  whoever is within 3 m, else you); sitting, Fixed where this seat has a kept view, else the frame holds; idle,
//  core's Scenic (Drift's reveal). At least 8 s per shot, and only once the reason has lasted 2 s. It keeps its hands
//  off while you hold the camera (it comes back as you walk off or press Esc), fly, watch someone or hold a photo.
//  A shot tapped (the strip, /12 tracking …) or the Orbit tapped: yours, manual, until the Orbit is tapped again.
// ============================================================================

string VERSION = "8.3.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer ACK        = 7313;
integer FOLLOW     = 7314;
integer UI_STATE   = 7320;
integer TIP        = 7345;
integer CFG_CHANGED= 7330;
integer OPTS       = 7340;
integer OPT        = 7341;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;

list    LOOKS  = ["SHOULDER", "FILM", "CLASSIC"];
list    DIST   = [1.6, 3.5, 3.0];      // m for a 1.8 m avatar
list    PITCH  = [4.0, -3.0, 14.0];    // degrees (down +)
list    SIDE   = [0.42, 0.55, 0.22];   // m  the focus beside you: you on your third
list    HIGH   = [0.0, -0.18, 0.05];   // the focus above your eye line, a fraction of your height
list    BLAG   = [0.5, 1.0, 0.6];      // s  the swing round behind you

key     gOwner;
integer gOn;
integer gHold;
integer gLook = 1;
integer gRight = 1;
float   gSent;                         // the distance last sent
string  gMode;                         // "" behind you, or "lock": a corner of a small room
vector  gRoomAt;                       // where the small room was measured
float   gStillT;
integer gHinted;
integer gRun;
integer gAuto;                         // Auto directs (8.3.0)
float   gWear;                         // ... worn at: it starts 3 s later, once set up
integer gWearing;                      // ... not started yet on this wear
string  gCore = "wait";                // core: its state, shot and why (UI_STATE)
string  gCShot;
string  gCWhy;
float   gShotT;                        // ... that shot since
string  gWant;                         // what Auto would pick now, and since
float   gWantT;
float   gStillA;                       // standing still since
integer gEyeA;                         // the eye-line check is on

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

load()
{
    list c = llParseString2List(cfg("trk"), ["|"], []);
    if (c != [])
    {
        gLook = (integer)llList2String(c, 0);
        gRight = (integer)llList2String(c, 1);
    }
    if (gLook < 0 || gLook > 2) gLook = 1;
    if (gAuto) gLook = 1;                               // Auto films in Film (its side stays yours); not kept
}

opts()
{
    list st = ["", "", "", "", "", ""];
    st = llListReplaceList(st, ["lit"], gLook, gLook);
    st = llListReplaceList(st, ["lit"], 4 + gRight, 4 + gRight);
    llMessageLinked(LINK_SET, OPTS, "tracking|SHOULDER,FILM,CLASSIC,/,L,R|" + llDumpList2String(st, ","), "");
}

float scale()
{
    vector sz = llGetAgentSize(gOwner);
    if (sz.z < 0.3) return 1.0;
    return sz.z / 1.8;
}

float eyeFrac()
{
    float e = (float)cfg("eye");
    if (e < 0.5 || e > 1.5) e = 0.935;                  // above 1.0 too: a mesh body or hover height (8.0.5)
    return e;
}

// where the look wants the camera, and how far it may go: a ray from your head back along it
float clearBehind(float D)
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2) return D;
    vector P = llList2Vector(d, 0);
    rotation R = llList2Rot(d, 1);
    float s = scale();
    float side = llList2Float(SIDE, gLook) * s * (2 * gRight - 1);
    vector H = P + <0.0, side, (eyeFrac() - 0.5) * 1.8 * s> * R;
    vector back = <-llCos(llList2Float(PITCH, gLook) * DEG_TO_RAD), 0.0, llSin(llList2Float(PITCH, gLook) * DEG_TO_RAD)> * R;
    list r = llCastRay(H, H + back * D, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
    if (llList2Integer(r, -1) <= 0) return D;
    float c = llVecDist(H, llList2Vector(r, 1)) - 0.3;
    if (c < 0.6) c = 0.6;
    return c;
}

// the follow camera for the look (pulled in by a wall)
send(integer force)
{
    float s = scale();
    float D = llList2Float(DIST, gLook) * s;
    if (gRun) D *= 1.3;
    D = clearBehind(D);
    if (!force && llFabs(D - gSent) < 0.3) return;
    gSent = D;
    gMode = "";
    float side = llList2Float(SIDE, gLook) * s * (2 * gRight - 1);
    vector off = <0.0, side, (eyeFrac() - 0.5 + llList2Float(HIGH, gLook)) * 1.8 * s>;
    float bl = llList2Float(BLAG, gLook) + 0.3 * gRun;
    string lags = "|0.5|0.25";
    if (cfg("feel") != "smooth") { bl = 0.0; lags = "|0.05|0.05"; }   // Snappy (the default, 8.0.8): right behind you, easy to steer
    llMessageLinked(LINK_SET, FOLLOW, (string)D + "|" + (string)llList2Float(PITCH, gLook) + "|" + (string)off + "|"
        + (string)bl + lags, "");
}

// a small closed room: under about 4 x 4 m with a ceiling. Then the best corner: [corner] or []
list smallRoom(vector P)
{
    float s = scale();
    vector E = <P.x, P.y, P.z + (eyeFrac() - 0.5) * 1.8 * s>;
    list up = llCastRay(E, E + <0.0, 0.0, 4.0>, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
    if (llList2Integer(up, -1) != 1) return [];
    list D = [];
    integer miss;
    integer i;
    for (i = 0; i < 8; i++)
    {
        vector u = <llCos(i * 0.785398), llSin(i * 0.785398), 0.0>;
        list r = llCastRay(E, E + u * 6.0, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
        if (llList2Integer(r, -1) == 1) D += [llVecDist(E, llList2Vector(r, 1))];
        else { D += [-1.0]; miss++; }
    }
    if (miss > 1) return [];                                // one ray may go out through a door
    for (i = 0; i < 4; i++)
    {
        float a = llList2Float(D, i);
        float b = llList2Float(D, i + 4);
        if (a < 0.0) a = b;                                 // the door: as far as the other side
        if (b < 0.0) b = a;
        if (i % 2 == 0 && a + b > 4.5) return [];
    }
    // the corner furthest from you (the diagonals 1, 3, 5, 7)
    float best;
    integer bi = 1;
    for (i = 1; i < 8; i += 2)
        if (llList2Float(D, i) > best) { best = llList2Float(D, i); bi = i; }
    vector c = E + <llCos(bi * 0.785398), llSin(bi * 0.785398), 0.0> * (best - 0.4) + <0.0, 0.0, 0.35 * s>;
    return [c];
}

check()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_VELOCITY]);
    if (llGetListLength(d) < 2) return;
    vector P = llList2Vector(d, 0);
    vector v = llList2Vector(d, 1);
    float sp = llVecMag(<v.x, v.y, 0.0>);
    integer run = (sp > 4.2);
    if (run != gRun)
    {
        gRun = run;
        if (gMode == "") send(TRUE);
    }
    // a small room: its corner, panning with you; out of it, behind you again
    if (gMode == "lock" && llVecDist(P, gRoomAt) > 3.0)
    {
        gMode = "";
        send(TRUE);
    }
    if (gMode == "")
    {
        list c = smallRoom(P);
        if (c != [])
        {
            gMode = "lock";
            gRoomAt = P;
            llMessageLinked(LINK_SET, FOLLOW, "lock|" + (string)llList2Vector(c, 0), "");
            return;
        }
        send(FALSE);
    }
    // standing still: it holds; after 5 s Portrait glows once
    if (sp < 0.2)
    {
        if (gStillT == 0.0) gStillT = llGetTime();
        else if (!gHinted && !gAuto && llGetTime() - gStillT > 5.0)
        {
            gHinted = TRUE;
            llMessageLinked(LINK_SET, CMD, "hint|portrait", "");
        }
    }
    else
    {
        gStillT = 0.0;
        gHinted = FALSE;
    }
}

// ---- Auto (8.3.0) -------------------------------------------------------------------------------
// on or off: everyone hears it (core, the strip, the shots)
auto(integer on)
{
    gAuto = on;
    gWant = "";
    llMessageLinked(LINK_SET, CMD, "auto|" + (string)on, "");
}

// the director: each pick is a tap Auto makes for you (CMD shot|<shot>|auto)
direct()
{
    float t = llGetTime();
    if (gWearing && t - gWear > 3.0)
    {
        gWearing = FALSE;                                   // on wear, if set up (a setup ends with /12 auto, ui)
        if (cfg("firstrun") == "done") { auto(TRUE); llMessageLinked(LINK_SET, TIP, "auto", ""); }
    }
    if (!gAuto || gEyeA || gCWhy == "idle" || (gCore != "wait" && gCore != "film")) return;
    integer info = llGetAgentInfo(gOwner);
    if (info & (AGENT_FLYING | AGENT_MOUSELOOK)) return;
    list d = llGetObjectDetails(gOwner, [OBJECT_VELOCITY, OBJECT_ROOT]);
    vector v = llList2Vector(d, 0);
    string want = gCShot;
    integer sat = (info & AGENT_SITTING) != 0;
    if (sat)
    {
        // this seat's kept view; none: the frame holds (nothing on yet: Fixed, frame it and it is kept)
        if (gCShot == "" || cfg("seat." + llList2String(d, 1)) != "") want = "fixed";
        gStillA = 0.0;
    }
    else if (llVecMag(<v.x, v.y, 0.0>) > 0.5)
    {
        want = "tracking";
        gStillA = 0.0;
    }
    else
    {
        if (gStillA == 0.0) gStillA = t;
        if (t - gStillA > 4.0 || gCShot == "") want = "portrait";   // 4 s + the 2 s below: 6 s still
    }
    if (want != gWant) { gWant = want; gWantT = t; }
    if (want == gCShot || want == "") return;
    if (gCShot != "")                                       // nothing on yet: at once
    {
        if (t - gWantT < 2.0) return;                       // the reason has to last 2 s
        if (t - gShotT < 8.0 && !sat && gCShot != "fixed") return;   // and a shot 8 s (not sitting down, standing up)
    }
    gShotT = t;
    llMessageLinked(LINK_SET, CMD, "shot|" + want + "|auto", "");
}

default
{
    state_entry()
    {
        gOwner = llGetOwner();
        load();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "tracking");
        if (llGetAttached()) { gWear = llGetTime(); gWearing = TRUE; llSetTimerEvent(0.5); }
    }

    attach(key id)
    {
        gAuto = FALSE;
        gCore = "wait";
        gCShot = "";
        gWear = llGetTime();
        gWearing = (id != NULL_KEY);
        llSetTimerEvent(0.5 * (id != NULL_KEY));
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
            gOn = (llList2String(llParseString2List(str, ["|"], []), 0) == "tracking");
            if (!gOn) return;
            llMessageLinked(LINK_SET, ACK, "tracking", "");
            load();
            opts();
            gHold = FALSE;
            gMode = "";
            gStillT = 0.0;
            gHinted = FALSE;
            send(TRUE);
            llSetTimerEvent(0.5);
        }
        else if (num == UI_STATE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            gCore = llList2String(L, 0);
            if (llList2String(L, 1) != gCShot) gShotT = llGetTime();
            gCShot = llList2String(L, 1);
            gCWhy = llList2String(L, 3);
        }
        else if (num == CMD)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            if (str == "auto" && !gAuto) auto(TRUE);                // /12 auto, the end of the setup
            else if (llList2String(L, 0) == "shot" && llGetListLength(L) == 2)
            {
                gWearing = FALSE;                                   // a shot of your own (a tap, /12 tracking …): manual
                if (gAuto && llList2String(L, 1) != gCShot) auto(FALSE);
            }
            else if (llGetSubString(str, 0, 4) == "auto|") { gAuto = (str == "auto|1"); gWant = ""; gWearing = FALSE; }
            else if ((str == "stop" || str == "standby") && gAuto) auto(FALSE);   // your viewer's camera; an older copy
            else if (llGetSubString(str, 0, 6) == "eyecam|") gEyeA = (str != "eyecam|off");
            else if (str == "eyequit") gEyeA = FALSE;
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "tracking");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/tracking] v" + VERSION + " " + llList2String(["off", "on"], gOn) + ", " + llList2String(LOOKS, gLook)
                + " · " + llList2String(["L", "R"], gRight) + ", " + llList2String(["behind you", "a room's corner"], gMode == "lock")
                + ", " + (string)gSent + " m, auto " + (string)gAuto + ", free mem " + (string)llGetFreeMemory());
        else if (!gOn) return;
        else if (num == STOP) gOn = FALSE;
        else if (num == PAUSE) gHold = TRUE;
        else if (num == RESUME)
        {
            gHold = FALSE;
            gMode = "";
            send(TRUE);
        }
        else if (num == NEXT)
        {
            gMode = "";                                     // the lit tap: back into the look, behind you
            send(TRUE);
        }
        else if (num == OPT)
        {
            string w = llList2String(llParseStringKeepNulls(str, ["|"], []), 1);
            integer i = llListFindList(LOOKS, [w]);
            if (i >= 0) gLook = i;
            else if (w == "L" || w == "R") gRight = (w == "R");
            llLinksetDataWriteProtected("cin.trk", (string)gLook + "|" + (string)gRight, PASS);
            opts();
            gMode = "";
            send(TRUE);
        }
        else if (num == CFG_CHANGED && (str == "eye" || str == "feel" || str == "all")) send(TRUE);
    }

    timer()
    {
        if (gOn && !gHold) check();
        direct();
    }
}
