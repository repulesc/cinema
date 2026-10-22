// ============================================================================
//  Take 12  -  cinema_tips.lsl  (v5.8)  - the text above the button: status, sharing, tips
//  The one owner of the text above the HUD. It shows, top to bottom:
//   - the sharing block from cinema_sync (TEXT 7380): "● LIVE · 2 watching / Ana · Ben", "👁 Pano", an invitation;
//   - the status line while a camera runs: the mode and who is in charge ("◇ Scenery · auto", "♡ Only friends ·
//     your view", "◇ Scenery · started while you were idle", "▣ Photo · held", "... · paused · Esc to carry on");
//     nothing with your own camera, and only the 👁 block while you watch someone;
//   - a tip, for 6 s, when something just happened (each retires after 3 showings; after all, or 24 in all, Tips
//     turns itself off; Help > Tips brings them back, from zero).
//  Short notices of other scripts (lens, Frame, sync: "Your view is kept", "Half length", "Ana joined") take the whole
//  text for their few seconds: whatever is on screen that this script did not write is left alone, and when its
//  script clears it, the status comes back within a second.
// ============================================================================

string VERSION = "5.8.0";
string PASS    = "cinema-1.0-build1";

integer LENS        = 7319;   // lens -> friends  "<distance>|...": distance 0 = automatic, else your own view
integer UI_STATE    = 7320;   // core -> all  "<state>|<mode>|<nextCutUnix>|<why>"  (why: "idle" = idle start)
integer CFG_CHANGED = 7330;
integer MSG_VER     = 7360;
integer STATUS      = 7370;
integer TEXT        = 7380;   // sync -> here  "<live/view/inv or empty>|<the sharing block>"

integer MAXN = 3;             // showings per tip
integer ALL  = 24;            // ... and in all, then Tips is off
float   HOLD = 6.0;           // s on screen
float   LATE = 1.5;           // s after the event
float   WAIT = 10.0;          // s a tip waits for a free moment, then it is dropped (not counted)
float   GAP  = 20.0;          // s between two tips

// 0 hello  1 scenery  2 me  3 us  4 only friends  5 still  6 photo  7 paused  8 back  9 more  10 sitting  11 idle start
// Under a status line only the second line shows, so it must make sense on its own.
list TIPS = [
    "Take 12\nTap: menu · Double-tap: scenery · Hold: share",
    "Scenery\ndouble-tap: next view · any key: your camera",
    "Me\nwalk around, it follows you · tap: stop",
    "Us\nit cuts to whoever speaks · double-tap: next",
    "Only friends\nframe it yourself, then Esc: it keeps your view",
    "Still\nW/S A/D E/C: adjust · double-tap: next framing",
    "Photo\ntake your pictures · tap: carry on",
    "Paused\nyou moved the camera, so it waits for you",
    "Your camera is back\ndouble-tap: scenery again",
    "Hold › More\nhold › More: photo, next, stop, other cameras",
    "Sitting\nsitting: W/S closer or wider",
    "Idle start\nstay idle "];
list MODES = ["scenery", "personal", "social", "friends", "frame"];   // tips 1 to 5
list NAMES = ["Scenery", "Me", "Us", "Only friends", "Still"];
list MARKS = ["◇", "○", "◎", "♡", "□"];

key     gOwner;
integer gOn;                 // Tips on
integer gStat;               // the status line on
integer gSkin;               // the menu style: 0 Plain shows no marks
string  gN;                  // showings per tip, one digit each
string  gSt;                 // the last state, mode and why from core
string  gMode;
string  gWhy;
integer gLed;                // Only friends: your own view (lens)
string  gKind;               // the sharing block from sync: live / view / inv / ""
string  gSync;
string  gTip;                // the tip on screen ("" = none)
string  gLast;               // the text this script wrote last
integer gWant = -1;          // the tip waiting for a free moment
float   gWantT;
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
    gStat = (cfg("status") != "0");
    gSkin = (integer)cfg("skin");
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
}

string cur()
{
    return llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0);
}

integer free()
{
    string c = cur();
    return (c == "" || c == gLast);
}

// the status line: the mode and who is in charge; nothing with your own camera
string line()
{
    integer m = llListFindList(MODES, [gMode]);
    if (!gStat || m < 0 || (gSt != "rolling" && gSt != "frozen" && gSt != "peek")) return "";
    string s = llList2String(NAMES, m);
    string k = llList2String(MARKS, m);
    string w = "auto";
    if (gMode == "frame") w = "held";
    else if (gMode == "friends" && gLed) w = "your view";
    else if (gMode == "scenery" && gWhy == "idle") w = "started while you were idle";
    if (gSt == "frozen")
    {
        s = "Photo";
        k = "▣";
        w = "held";
    }
    else if (gSt == "peek") w = "paused · Esc to carry on";
    if (gSkin) s = k + " " + s;
    return s + " · " + w;
}

// sharing block, status line, tip: written only when it changed, and never over another script's notice
draw()
{
    string c = cur();
    if (c != "" && c != gLast) return;
    list L = [];
    if (gSync != "") L += [gSync];
    if (gKind != "view" && line() != "") L += [line()];
    if (gTip != "") L += [gTip];
    string t = llDumpList2String(L, "\n");
    if (t != c) llSetText(t, <1.0, 1.0, 1.0>, 0.85);
    gLast = t;
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
    gTip = llList2String(TIPS, i);
    if (i == 11) gTip += idleText();
    if (gKind != "view" && line() != "") gTip = llList2String(llParseString2List(gTip, ["\n"], []), 1);
    gShowT = llGetTime();
    gLastT = gShowT;
    gWant = -1;
    draw();
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
    gTip = "";                                              // a shown tip is about what was
    gShowT = 0.0;
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
}

tick()
{
    draw();
    if (gWant >= 0 || gShowT > 0.0) llSetTimerEvent(0.5);
    else if (gLast != "" || gRollT > 0.0) llSetTimerEvent(1.0);    // the status line: back within a second after a notice
    else llSetTimerEvent(0.0);
}

default
{
    state_entry()
    {
        gOwner = llGetOwner();
        load();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "tips");
        if (llGetAttached()) want(0);
        tick();
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
            gWhy = llList2String(L, 3);
            if (mode != "friends") gLed = FALSE;
        }
        else if (num == LENS) gLed = ((float)llList2String(llParseStringKeepNulls(str, ["|"], []), 0) > 0.0);
        else if (num == TEXT)
        {
            integer i = llSubStringIndex(str, "|");
            gKind = llGetSubString(str, 0, i - 1);
            gSync = llGetSubString(str, i + 1, -1);
            if (i == 0) gKind = "";
        }
        else if (num == CFG_CHANGED && (str == "tips" || str == "status" || str == "skin" || str == "all")) load();
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "tips");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/tips] v" + VERSION + " status line " + llList2String(["off", "on"], gStat) + ", tips "
                + llList2String(["off", "on"], gOn) + ", seen " + gN + ", free mem " + (string)llGetFreeMemory());
        else return;
        tick();
    }

    timer()
    {
        float now = llGetTime();
        if (gShowT > 0.0 && now - gShowT >= HOLD)
        {
            gTip = "";
            gShowT = 0.0;
        }
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
            else if (now - gWantT >= LATE && now - gLastT >= GAP && free()) show(gWant);
        }
        tick();
    }
}
