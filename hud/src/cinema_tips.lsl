// ============================================================================
//  Take 12  -  cinema_tips.lsl  (v5.7)  - short tips above the button
//  When something just happened (the camera starts, a Photo freeze, a pause, a stop), a two-line tip says where you
//  are and what you can do next. It shows for 6 s, only when nothing else is above the HUD (sharing, Still's framing
//  names and the lens notices always win), at most one per 20 s. Each tip retires after 3 showings; when all have
//  retired, or after 24 tips in all, Tips turns itself off. Help > Tips (or /77 tips on) brings them back, from zero.
// ============================================================================

string VERSION = "5.7.0";
string PASS    = "cinema-1.0-build1";

integer STOP        = 7302;
integer UI_STATE    = 7320;   // core -> all  "<state>|<mode>|<nextCutUnix>"
integer CFG_CHANGED = 7330;
integer MSG_VER     = 7360;
integer STATUS      = 7370;

integer MAXN = 3;             // showings per tip
integer ALL  = 24;            // ... and in all, then Tips is off
float   HOLD = 6.0;           // s on screen
float   LATE = 1.5;           // s after the event
float   WAIT = 10.0;          // s a tip waits for a free moment, then it is dropped (not counted)
float   GAP  = 20.0;          // s between two tips

// 0 hello  1 scenery  2 me  3 us  4 only friends  5 still  6 photo  7 paused  8 back  9 more  10 sitting  11 idle start
list TIPS = [
    "Take 12\nTap: menu · Double-tap: scenery · Hold: share",
    "Scenery\ndouble-tap: next view · any key: your camera",
    "Me\nwalk around, it follows you · tap: stop",
    "Us\nit cuts to whoever speaks · double-tap: next",
    "Only friends\nframe it yourself, then Esc: it keeps your view",
    "Still\nW/S A/D E/C: adjust · double-tap: next framing",
    "Photo\ntake your pictures · tap: carry on",
    "Paused\nEsc: carry on",
    "Your camera is back\ndouble-tap: scenery again",
    "Hold › More\nphoto, next, stop, other cameras",
    "Sitting\nW/S: closer or wider",
    "Idle start\nstay idle "];
list MODES = ["scenery", "personal", "social", "friends", "frame"];   // tips 1 to 5

key     gOwner;
integer gOn;                 // Tips on
string  gN;                  // showings per tip, one digit each
string  gSt;                 // the last state and mode from core
string  gMode;
integer gWant = -1;          // the tip waiting for a free moment
float   gWantT;
string  gShown;              // the tip on screen
float   gShowT;
float   gLastT = -100.0;
float   gRollT;              // rolling since (0: not rolling)
integer gMore;               // the "Hold > More" tip was offered this run
integer gSat;                // ... and the sitting one

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

load()
{
    gOn = (cfg("tips") != "0");
    gN = cfg("tipn");
    while (llStringLength(gN) < llGetListLength(TIPS)) gN += "0";
}

integer seen(integer i)
{
    return (integer)llGetSubString(gN, i, i);
}

want(integer i)
{
    if (!gOn || seen(i) >= MAXN) return;
    gWant = i;
    gWantT = llGetTime();
    llSetTimerEvent(0.5);
}

string cur()
{
    return llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0);
}

clear()
{
    if (gShowT > 0.0 && cur() == gShown) llSetText("", ZERO_VECTOR, 0.0);
    gShowT = 0.0;
}

string idleText()
{
    integer s = (integer)cfg("afk_sec");
    string t = (string)s + " s";
    if (s % 60 == 0) t = (string)(s / 60) + " min";
    return t + ": the scenery starts by itself";
}

show(integer i)
{
    gShown = llList2String(TIPS, i);
    if (i == 11) gShown += idleText();
    llSetText(gShown, <1.0, 1.0, 1.0>, 0.7);                // a little softer than the HUD's own notices
    gShowT = llGetTime();
    gLastT = gShowT;
    gWant = -1;
    string c = (string)(seen(i) + 1);
    gN = llInsertString(llDeleteSubString(gN, i, i), i, c);
    llLinksetDataWriteProtected("cin.tipn", gN, PASS);
    integer k;
    integer all;
    integer done = TRUE;
    for (k = 0; k < llStringLength(gN); k++)
    {
        all += seen(k);
        if (seen(k) < MAXN) done = FALSE;
    }
    if (done || all >= ALL)
    {
        gOn = FALSE;
        llLinksetDataWriteProtected("cin.tips", "0", PASS);
        llMessageLinked(LINK_SET, CFG_CHANGED, "tips", "");
        llOwnerSay("[Take 12] Tips are off now · Help › Tips brings them back.");
    }
}

// the state changed: a tip for what just happened
onState(string st, string mode)
{
    integer rolling = (st == "rolling");
    integer idle = (st != "rolling" && st != "frozen" && st != "peek");
    integer was = (gSt == "rolling" || gSt == "frozen" || gSt == "peek");
    clear();                                                // a shown tip is about what was
    if (gWant != 0 || !idle) gWant = -1;                    // the hello waits through the start-up states
    if (rolling && (!was || mode != gMode))                 // a new run (not the end of a Photo or a pause)
    {
        gRollT = llGetTime();
        gMore = FALSE;
        gSat = FALSE;
        integer m = llListFindList(MODES, [mode]);
        if (m >= 0) want(m + 1);
    }
    else if (st == "frozen") want(6);
    else if (st == "peek") want(7);
    else if (idle && was)
    {
        gRollT = 0.0;
        if (seen(8) < MAXN) want(8);
        else if (st == "armed" && cfg("afk_on") == "1") want(11);
    }
    gSt = st;
    gMode = mode;
    if (gRollT > 0.0 && gWant < 0) llSetTimerEvent(1.0);
}

default
{
    state_entry()
    {
        gOwner = llGetOwner();
        load();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "tips");
        if (llGetAttached()) want(0);
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
        if (num == UI_STATE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            string st = llList2String(L, 0);
            string mode = llList2String(L, 1);
            if (st != gSt || (st == "rolling" && mode != gMode)) onState(st, mode);
        }
        else if (num == CFG_CHANGED && (str == "tips" || str == "all")) load();
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "tips");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/tips] v" + VERSION + " tips " + llList2String(["off", "on"], gOn) + ", seen " + gN
                + ", free mem " + (string)llGetFreeMemory());
    }

    timer()
    {
        float now = llGetTime();
        if (gShowT > 0.0 && now - gShowT >= HOLD) clear();
        if (gRollT > 0.0 && gSt == "rolling" && gWant < 0 && gShowT == 0.0)
        {
            if (!gSat && gMode == "friends" && (llGetAgentInfo(gOwner) & AGENT_SITTING))
            {
                gSat = TRUE;
                want(10);
            }
            else if (!gMore && now - gRollT >= 90.0)
            {
                gMore = TRUE;
                want(9);
            }
        }
        if (gWant >= 0)
        {
            if (!gOn || now - gWantT > WAIT) gWant = -1;    // no free moment: dropped, not counted
            else if (now - gWantT >= LATE && now - gLastT >= GAP && cur() == "") show(gWant);
        }
        if (gShowT > 0.0 || gWant >= 0) llSetTimerEvent(0.5);
        else if (gRollT > 0.0) llSetTimerEvent(1.0);
        else llSetTimerEvent(0.0);
    }
}
