// ============================================================================
//  Take 12  -  keys.lsl  (v6.6)  - the soft keys: a few quiet keys beside the button, only when they help
//  One strip prim linked to the HUD, named "Take 12 keys", shows a row of the key atlas (hud/art/
//  take12_keys_1024.png, in the HUD's contents as "take12_keys"; 7.1: two columns of ten rows) with repeats and
//  offsets; the touch position on it (llDetectedTouchST) says which key. Without the strip everything stays in the menus.
//    Connected, holding it   NEXT · INVITE · DISCONNECT               (6.8: Connect; the Watches only: DISCONNECT asks)
//    Connected, watching     NEXT · MY TURN · DISCONNECT              (MY TURN: you film, everyone sees yours)
//    Freehand                SAVE · VIEW A · VIEW B · STOP · ADJUST   (the view in use lit; ADJUST lit while the keys adjust)
//    Framing › Me            FULL · HALF · CLOSE · ADJUST             (the framing in use lit)
//    Framing › Us, Friends   NEXT · ADJUST
//  With the strip the live menu leaves Next out (ui.lsl).
//  Anything else: no keys. Placed left of the button, 1.2 times as tall as it (so the labels read); the HUD's +Y is
//  left (/77 crop flip, shared with Frame, mirrors both).
//  6.7.1, Size: Options > Look > Size (or /77 size s|m|l): the button 0.04, 0.06 or 0.08 (Small, Medium, Large;
//  Medium when never set), the keys with it. Checked in tools/sim/keys_sim.py.
// ============================================================================

string VERSION = "7.1.0";
string PASS    = "cinema-1.0-build1";

integer UI_STATE   = 7320;   // core -> all  "<state>|<mode>|..."
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer TEXT       = 7380;   // sync -> tips  "<live/view/inv or empty>|...": the connection
integer STILL      = 7381;   // frame -> tips  "<framing>|...": Still's framing
integer SHARE_DO   = 7393;   // here -> sync: a choice of the Connect panel
integer KEYS       = 7395;   // free -> here  "free|<saved view in use, -1 none>"
integer UI_MENU    = 7321;   // here -> ui: back to a menu page

string  STRIP = "Take 12 keys";
string  TEX   = "take12_keys";
float   CW    = 0.07421875;  // a key cell on the atlas: 76 x 96 of 1024 x 1024
float   RH    = 0.09375;
integer PER   = 10;          // rows in a column (two columns, 512 wide)
// the rows of the atlas, top first (tools/art/make_keys.py): how many keys, and what each does
// C: a command (core, free, frame), S: a choice for sync (connect.lsl's SHARE_DO), one row per entry, ";" between keys
list    ROWS = [3, 3, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 2, 2];
string  LIVE = "C:next;S:who;S:disconnect";
string  WTCH = "C:scenery;S:film;S:disconnect";
string  FREE = "C:fav;C:view|0;C:view|1;C:stop;C:adjust";
string  STIL = "C:framing|0;C:framing|1;C:framing|2;C:adjust";
string  GRP  = "C:next;C:adjust";
list    STILLS = ["Full length", "Half length", "Close"];
list    SIZES  = ["Small", "Medium", "Large"];
list    EDGES  = [0.04, 0.06, 0.08];   // m  the button's height (and width) for each size

key     gOwner;
integer gLink;               // the strip (0: none linked)
integer gRow = -2;           // the row on show (-1: hidden)
string  gSt;                 // core's state and mode
string  gMode;
integer gAdj;                // the keys adjust the shot (core)
string  gShare;              // live / view / inv / ""
integer gPick = -1;          // Freehand: the saved view in use
integer gStill;              // Still: the framing
integer gChan;               // the Size dialog
integer gL;

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

// the strip: a child named "... keys" (any case); else, with five or more children, the highest one that is not one of
// Frame's four bars (crop.lsl claims the bars it named first, then the lowest children). Named STRIP once found, so a strip linked before it was named works.
find()
{
    gLink = 0;
    integer f;
    integer nf;
    integer i;
    for (i = 2; i <= llGetNumberOfPrims(); i++)
    {
        string m = llToLower(llGetLinkName(i));
        if (llSubStringIndex(m, "keys") >= 0) gLink = i;
        else
        {
            if (m == "take 12 frame") nf++;                 // a fifth "frame" box: a strip Frame took before 6.6
            if (m != "take 12 frame" || nf > 4) f = i;
        }
    }
    if (!gLink && llGetNumberOfPrims() >= 6) gLink = f;
    if (gLink) llSetLinkPrimitiveParamsFast(gLink, [PRIM_NAME, STRIP]);
    gRow = -2;
}

// the button's size: 0 Small, 1 Medium, 2 Large
size(integer i)
{
    if (i < 0 || i > 2) return;
    float e = llList2Float(EDGES, i);
    vector s = llGetScale();
    llSetScale(<s.x, e, e>);
    llLinksetDataWriteProtected("cin.size", (string)i, PASS);
    gRow = -2;                                              // the keys follow
}

menu()
{
    if (gL) llListenRemove(gL);
    gChan = -(integer)(llFrand(1000000000.0) + 1000.0);
    gL = llListen(gChan, "", gOwner, "");
    llSetTimerEvent(60.0);
    integer i = (integer)cfg("size");
    llDialog(gOwner, "Size of the button and the keys\nNow: " + llList2String(SIZES, i), SIZES + ["‹ Back"], gChan);
}

// which keys, now
integer pick()
{
    integer on = (gSt == "rolling" || gSt == "frozen" || gSt == "peek");
    if (gShare == "live") return 0;
    if (gShare == "view") return 1;
    if (on && gMode == "free") return 3 + gPick + 3 * gAdj;
    if (gSt == "rolling" && gMode == "frame") return 8 + gStill + 3 * gAdj;
    if (on && (gMode == "social" || gMode == "friends")) return 14 + gAdj;
    return -1;
}

// the strip: row r of the atlas, left of the button and as tall as it; r = -1 hides it
show(integer r)
{
    if (gLink && llGetLinkName(gLink) != STRIP) find();     // re-linked or renamed: look again
    if (!gLink || r == gRow || !llGetAttached()) return;
    gRow = r;
    if (r < 0)
    {
        llSetLinkPrimitiveParamsFast(gLink, [PRIM_SIZE, <0.01, 0.01, 0.01>, PRIM_COLOR, ALL_SIDES, <1, 1, 1>, 0.0]);
        return;
    }
    integer n = llList2Integer(ROWS, r);
    vector s = llGetScale();
    float b = s.z;
    if (s.y > b) b = s.y;
    float h = 1.2 * b;                                      // a little taller than the button: the labels read
    float w = n * h * 0.791667;                             // a key: 76 x 96
    integer sy = 1;
    list c = llParseString2List(cfg("crop_s"), ["|"], []);
    if (llGetListLength(c) == 2) sy = (integer)llList2String(c, 0);
    rotation q = llGetLocalRot();
    vector off = <0.0, sy * (b * 0.5 + 0.004 + w * 0.5), 0.0>;
    string tex = TEX;
    if (llGetInventoryType(TEX) != INVENTORY_TEXTURE) tex = llList2String(llGetLinkPrimitiveParams(gLink, [PRIM_TEXTURE, 0]), 0);
    llSetLinkPrimitiveParamsFast(gLink, [PRIM_POS_LOCAL, off / q, PRIM_ROT_LOCAL, ZERO_ROTATION / q, PRIM_SIZE, <0.01, w, h>,
        PRIM_TEXTURE, ALL_SIDES, tex, <n * CW, RH, 0.0>, <(r / PER) * 0.5 + n * CW * 0.5 - 0.5, 0.5 - (r % PER + 0.5) * RH, 0.0>, 0.0,
        PRIM_COLOR, ALL_SIDES, <1, 1, 1>, 1.0, PRIM_FULLBRIGHT, ALL_SIDES, TRUE]);
}

// a key: the action in its row
press(integer i)
{
    string row = llList2String([LIVE, WTCH, FREE, FREE, FREE, FREE, FREE, FREE, STIL, STIL, STIL, STIL, STIL, STIL, GRP, GRP], gRow);
    string a = llList2String(llParseString2List(row, [";"], []), i);
    if (llGetSubString(a, 0, 0) == "S") llMessageLinked(LINK_SET, SHARE_DO, llDeleteSubString(a, 0, 1), "");
    else llMessageLinked(LINK_SET, CMD, llDeleteSubString(a, 0, 1), "");
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        if (cfg("size") == "") size(1);                     // never set: Medium
        find();
        show(-1);
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "keys");
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
        if (c & CHANGED_LINK)
        {
            find();                                         // (also when the strip is linked after it was named)
            show(pick());
        }
    }

    listen(integer ch, string name, key id, string msg)
    {
        llListenRemove(gL);
        gL = 0;
        llSetTimerEvent(0.0);
        if (msg == "‹ Back") llMessageLinked(LINK_SET, UI_MENU, "look", "");
        else
        {
            size(llListFindList(SIZES, [msg]));
            show(pick());
            menu();                                         // see it, try another
        }
    }

    timer()
    {
        if (gL) llListenRemove(gL);
        gL = 0;
        llSetTimerEvent(0.0);
    }

    touch_start(integer n)
    {
        if (llDetectedKey(0) != gOwner || llDetectedLinkNumber(0) != gLink || gRow < 0) return;
        vector st = llDetectedTouchST(0);
        if (st.x < 0.0) return;                             // a viewer without touch positions
        integer k = (integer)(st.x * llList2Integer(ROWS, gRow));
        if (k >= llList2Integer(ROWS, gRow)) k = llList2Integer(ROWS, gRow) - 1;
        press(k);
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == UI_STATE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            gSt = llList2String(L, 0);
            gMode = llList2String(L, 1);
            gAdj = (integer)llList2String(L, 4);
            if (gMode != "free") gPick = -1;
        }
        else if (num == TEXT) gShare = llList2String(llParseStringKeepNulls(str, ["|"], []), 0);
        else if (num == STILL)
        {
            gStill = llListFindList(STILLS, [llList2String(llParseStringKeepNulls(str, ["|"], []), 0)]);
            if (gStill < 0) gStill = 0;
        }
        else if (num == KEYS) gPick = (integer)llList2String(llParseStringKeepNulls(str, ["|"], []), 1);
        else if (num == CFG_CHANGED && (str == "all" || str == "crop_s")) gRow = -2;
        else if (num == CMD && str == "size") menu();
        else if (num == CMD && llGetSubString(str, 0, 4) == "size|") size(llListFindList(["s", "m", "l"], [llGetSubString(str, 5, 5)]));
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "keys");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/keys] v" + VERSION + " strip " + llList2String(["not linked", "link " + (string)gLink], gLink > 0)
                + ", row " + (string)gRow + ", free mem " + (string)llGetFreeMemory());
        else return;
        show(pick());
    }
}
