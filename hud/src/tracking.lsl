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
//  Auto (8.3.0; its rhythm 8.4.0) lives here too, the walking camera knowing when you walk and stop: the director.
//  On wear (once set up) it picks the shot from what a script truly sees (docs/PRODUCT.md, Auto: the guide):
//    moving 1 s (speed, the movement keys)     Tracking, at once, from any shot, also from an Alt-click's hold
//    still 10 s, alone (or in a crowd)         Scenic · Drift (its reveal); 5 minutes or Away: Scenic wide (Room
//                                              indoors, Far outdoors)
//    still 4 s with 1-3 people within 3 m      Portrait (Medium · Us); 3 s after they leave, the rest again
//    sitting                                   Fixed where this seat has a kept view (2 s), else Drift (10 s)
//  A shot stays at least 8 s, except Tracking as you move (8.3.0's 2 s rule kept you in Portrait while you walked a
//  room in short steps). Hands off while you fly, watch someone, hold a photo or set the eye line; an Alt-click waits
//  until you walk off (or Esc: core). A shot of your own (the strip, /12 tracking …) or the Orbit: manual, until the
//  Orbit is tapped again. Auto's options are never kept as yours.
// ============================================================================

string VERSION = "8.7.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer MOVING     = 7306;
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
// 8.7.0: higher and further for play as well as film (Film looked up from chest height, "the belly button": too low;
// Shoulder too close): Film at about head height looking a little down, you on a third; Shoulder over the shoulder with
// room; Classic the game view, centred, high, seeing far ahead
list    DIST   = [2.2, 3.6, 4.2];      // m for a 1.8 m avatar
list    PITCH  = [8.0, 6.0, 16.0];     // degrees (down +)
list    SIDE   = [0.45, 0.5, 0.0];     // m  the focus beside you: you on your third (Classic centred)
list    HIGH   = [0.03, 0.0, 0.06];    // the focus above your eye line, a fraction of your height
list    BLAG   = [0.5, 1.0, 0.6];      // s  the swing round behind you

key     gOwner;
integer gOn;
integer gHold;
integer gLook = 1;
integer gRight = 1;
float   gSent;                         // the distance last sent
integer gSnap;                         // after a teleport: the first follow camera without easing (8.5.10: it drifted in from afar)
string  gMode;                         // "" behind you, or "lock": a corner of a small room
vector  gRoomAt;                       // where the small room was measured
float   gStillT;
integer gHinted;
integer gRun;
float   gLead;                         // ... walking: the frame leaves room ahead of you (8.7.0), eased in and out
integer gAuto;                         // Auto directs (8.3.0)
float   gWear;                         // ... worn at: it starts 3 s later, once set up
integer gWearing;                      // ... not started yet on this wear
string  gCore = "wait";                // core: its state, shot and why (UI_STATE)
string  gCShot;
string  gCWhy;
float   gShotT;                        // ... that shot since
string  gBandA;                        // Scenic's band Auto asked for (drift, wide)
float   gMoveT;                        // moving since (0: still)
float   gStillA;                       // still since (sitting down or standing up starts it again)
integer gSatA;
integer gKeysA;                        // the movement keys held (core's MOVING)
float   gKeyT;                          // ... pressed at
integer gWith;                         // people within 3 m (the sensor), since, gone since
float   gWithT;
float   gGoneT;
integer gEyeA;                         // the eye-line check is on
integer gDebug;

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
    if (gLook < 0 || gLook > 2) gLook = 1;              // (Auto films in your look and side too, 8.4.4)
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
    vector off = <gLead, side, (eyeFrac() - 0.5 + llList2Float(HIGH, gLook)) * 1.8 * s>;   // walking: lead room ahead (8.7.0)
    float bl = llList2Float(BLAG, gLook) + 0.3 * gRun;
    string lags = "|0.5|0.25";
    if (cfg("feel") != "smooth") { bl = 0.0; lags = "|0.05|0.05"; }   // Snappy (the default, 8.0.8): right behind you, easy to steer
    if (gSnap == 1) { bl = 0.0; lags = "|0.0|0.0"; gSnap = 2; }      // there at once; the next tick eases again
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
    float lead = 0.5 * scale() * (sp > 0.5);
    if (run != gRun || lead != gLead)
    {
        gRun = run;
        if (lead > gLead + 0.13) lead = gLead + 0.125 * scale();   // in steps over 2 s: never a jolt (a friend watching too)
        else if (lead < gLead - 0.13) lead = gLead - 0.125 * scale();
        gLead = lead;
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
// on or off: everyone hears it (core, the strip, the shots); the people within 3 m while it is on
auto(integer on)
{
    gAuto = on;
    gBandA = "";
    gStillA = 0.0;
    llMessageLinked(LINK_SET, CMD, "auto|" + (string)on, "");
    if (on) llSensorRepeat("", NULL_KEY, AGENT, 3.0, PI, 1.0);   // 16 at most, never the region's list (8.0.1)
    else { llSensorRemove(); gWith = 0; }
}

// a pick: a tap Auto makes for you (and Scenic's band, not kept)
pick(string shot, string band, string why)
{
    if ((band == "" || band == gBandA) && shot == gCShot) return;
    if (band != "")
    {
        gBandA = band;
        llMessageLinked(LINK_SET, CMD, "aband|" + band, "");
    }
    if (shot != gCShot)
    {
        gShotT = llGetTime();
        llMessageLinked(LINK_SET, CMD, "shot|" + shot + "|auto", "");
    }
    if (gDebug) llOwnerSay("[Take 12] Auto: " + shot + " " + band + " (" + why + ")");
}

// the director, twice a second
direct()
{
    float t = llGetTime();
    if (gWearing && t - gWear > 3.0)
    {
        gWearing = FALSE;                                   // on wear, if set up (a setup ends with /12 auto, ui)
        if (cfg("firstrun") == "done") { auto(TRUE); llMessageLinked(LINK_SET, TIP, "auto", ""); }
    }
    if (!gAuto || gEyeA || gCWhy == "idle" || (gCore != "wait" && gCore != "film" && gCore != "held")) return;
    integer info = llGetAgentInfo(gOwner);
    if (info & (AGENT_FLYING | AGENT_MOUSELOOK)) return;
    list d = llGetObjectDetails(gOwner, [OBJECT_VELOCITY, OBJECT_ROOT]);
    vector v = llList2Vector(d, 0);
    float sp = llVecMag(<v.x, v.y, 0.0>);
    integer sat = (info & AGENT_SITTING) != 0;
    integer moving = !sat && (sp > 0.5 || gKeysA || (info & AGENT_WALKING));
    if (sat != gSatA) { gSatA = sat; gStillA = t; }         // sat down, stood up: the still clock starts again
    if (moving) { if (gMoveT == 0.0) gMoveT = t; gStillA = 0.0; }
    else { gMoveT = 0.0; if (gStillA == 0.0) gStillA = t; }
    if (gCore == "held" && !moving) return;                  // your Alt-click: until you walk off (or Esc, core)
    float still = t - gStillA;
    integer kept = sat && cfg("seat." + llList2String(d, 1)) != "";
    integer with = (gWith > 0 && gWith <= 3 && t - gWithT >= 4.0) || (gCShot == "portrait" && t - gGoneT < 3.0);
    if (moving)
    {
        // the walking keys: at once (held 0.25 s: a nudge is no walk); moving otherwise (pushed, a slope): 1 s (8.4.4)
        if (t - gMoveT >= 1.0 || (gKeysA && t - gKeyT >= 0.25) || gCShot == "") pick("tracking", "", "moving " + (string)sp + " m/s");
        return;                                             // never anything else while you move
    }
    if (kept && still >= 2.0) { pick("fixed", "", "a kept seat"); return; }
    if (gCShot == "") { if (sat) pick("scenic", "drift", "seated"); else pick("tracking", "", "worn"); return; }
    if (t - gShotT < 8.0) return;                           // a shot stays 8 s
    if (with && !sat && still >= 4.0) pick("portrait", "", (string)gWith + " near");
    else if (still >= 300.0 || (info & AGENT_AWAY)) pick("scenic", "wide", "a long while");
    else if (still >= 10.0 && !(kept && gCShot == "fixed")) pick("scenic", "drift", "resting");
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
        if (gAuto) auto(FALSE);
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
            gSnap = (llList2String(llParseString2List(str, ["|"], []), 1) == "tp");
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
            else if (llGetSubString(str, 0, 4) == "auto|")
            {
                gWearing = FALSE;
                if ((str == "auto|1") != gAuto) auto(str == "auto|1");   // (from the strip: the sensor follows)
            }
            else if (llGetSubString(str, 0, 5) == "debug|") gDebug = (str == "debug|1");
            else if ((str == "stop" || str == "standby") && gAuto) auto(FALSE);   // your viewer's camera; an older copy
            else if (llGetSubString(str, 0, 6) == "eyecam|") gEyeA = (str != "eyecam|off");
            else if (str == "eyequit") gEyeA = FALSE;
        }
        else if (num == MOVING)
        {
            gKeysA = ((integer)str != 0);
            if (gKeysA && gAuto) { gKeyT = llGetTime(); llSetTimerEvent(0.3); }   // Auto looks again in 0.3 s
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "tracking");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/tracking] v" + VERSION + " " + llList2String(["off", "on"], gOn) + ", " + llList2String(LOOKS, gLook)
                + " · " + llList2String(["L", "R"], gRight) + ", " + llList2String(["behind you", "a room's corner"], gMode == "lock")
                + ", " + (string)gSent + " m, auto " + (string)gAuto + " (" + gCore + " " + gCShot + " " + gBandA + ", still "
                + (string)((integer)(llGetTime() - gStillA) * (gStillA > 0.0)) + " s, near " + (string)gWith + "), free mem " + (string)llGetFreeMemory());
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
        llSetTimerEvent(0.5);
        if (gSnap == 2) { gSnap = 0; if (gOn && gMode == "") send(TRUE); }
        if (gOn && !gHold) check();
        direct();
    }

    sensor(integer n)
    {
        if (!gWith) gWithT = llGetTime();
        gWith = n;
    }

    no_sensor()
    {
        if (gWith) gGoneT = llGetTime();
        gWith = 0;
    }
}
