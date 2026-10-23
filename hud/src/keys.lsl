// ============================================================================
//  Take 12  -  keys.lsl  (v6.5)  - the soft keys: a few quiet keys beside the button, only when they help
//  One strip prim linked to the HUD, named "Take 12 keys", shows a row of the key atlas (hud/art/
//  take12_keys_512x1024.png, in the HUD's contents as "take12_keys") with repeats and offsets; the touch position
//  on it (llDetectedTouchST) says which key. Without the strip everything stays in the menus.
//    Live, as the director   NEXT · HOLD · INVITE · END      (END asks first)
//    Watching someone        NEXT · ASK · LEAVE
//    Freehand                SAVE · VIEW A · VIEW B · STOP   (the view in use lit)
//    Still                   FULL · HALF · CLOSE             (the framing in use lit)
//  Anything else: no keys. Placed left of the button, as tall as it; the HUD's +Y is left (/77 crop flip, shared with
//  Frame, mirrors both). Checked in tools/sim/keys_sim.py.
// ============================================================================

string VERSION = "6.5.0";
string PASS    = "cinema-1.0-build1";

integer UI_STATE   = 7320;   // core -> all  "<state>|<mode>|..."
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer TEXT       = 7380;   // sync -> tips  "<live/view/inv or empty>|...": the sharing state
integer STILL      = 7381;   // frame -> tips  "<framing>|...": Still's framing
integer SHARE_DO   = 7393;   // here -> sync: a choice of the Share panel
integer KEYS       = 7395;   // free -> here  "free|<saved view in use, -1 none>"

string  STRIP = "Take 12 keys";
string  TEX   = "take12_keys";
float   CW    = 0.1484375;   // a key cell on the atlas: 76 x 96 of 512 x 1024
float   RH    = 0.09375;
// the rows of the atlas, top first (tools/art/make_keys.py): how many keys, and what each does
// C: a command (core, free, frame), S: a choice for sync (share.lsl's SHARE_DO), one row per entry, ";" between keys
list    ROWS = [4, 4, 3, 4, 4, 4, 3, 3, 3];
string  LIVE = "C:next;C:photo;S:who;S:endask";
string  FREE = "C:fav;C:view|0;C:view|1;C:stop";
string  STIL = "C:framing|0;C:framing|1;C:framing|2";
list    STILLS = ["Full length", "Half length", "Close"];

key     gOwner;
integer gLink;               // the strip (0: none linked)
integer gRow = -2;           // the row on show (-1: hidden)
string  gSt;                 // core's state and mode
string  gMode;
string  gShare;              // live / view / inv / ""
integer gPick = -1;          // Freehand: the saved view in use
integer gStill;              // Still: the framing

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

find()
{
    gLink = 0;
    integer i;
    for (i = 2; i <= llGetNumberOfPrims(); i++)
        if (llGetLinkName(i) == STRIP) gLink = i;
    gRow = -2;
}

// which keys, now
integer pick()
{
    integer on = (gSt == "rolling" || gSt == "frozen" || gSt == "peek");
    if (gShare == "live") return (gSt == "frozen");
    if (gShare == "view") return 2;
    if (on && gMode == "free") return 4 + gPick;
    if (gSt == "rolling" && gMode == "frame") return 6 + gStill;
    return -1;
}

// the strip: row r of the atlas, left of the button and as tall as it; r = -1 hides it
show(integer r)
{
    if (!gLink || r == gRow || !llGetAttached()) return;
    gRow = r;
    if (r < 0)
    {
        llSetLinkPrimitiveParamsFast(gLink, [PRIM_SIZE, <0.01, 0.01, 0.01>, PRIM_COLOR, ALL_SIDES, <1, 1, 1>, 0.0]);
        return;
    }
    integer n = llList2Integer(ROWS, r);
    vector s = llGetScale();
    float h = s.z;
    if (s.y > h) h = s.y;
    float w = n * h * 0.791667;                             // a key: 76 x 96
    integer sy = 1;
    list c = llParseString2List(cfg("crop_s"), ["|"], []);
    if (llGetListLength(c) == 2) sy = (integer)llList2String(c, 0);
    rotation q = llGetLocalRot();
    vector off = <0.0, sy * (h * 0.5 + 0.004 + w * 0.5), 0.0>;
    string tex = TEX;
    if (llGetInventoryType(TEX) != INVENTORY_TEXTURE) tex = llList2String(llGetLinkPrimitiveParams(gLink, [PRIM_TEXTURE, 0]), 0);
    llSetLinkPrimitiveParamsFast(gLink, [PRIM_POS_LOCAL, off / q, PRIM_ROT_LOCAL, ZERO_ROTATION / q, PRIM_SIZE, <0.01, w, h>,
        PRIM_TEXTURE, ALL_SIDES, tex, <n * CW, RH, 0.0>, <n * CW * 0.5 - 0.5, 0.5 - (r + 0.5) * RH, 0.0>, 0.0,
        PRIM_COLOR, ALL_SIDES, <1, 1, 1>, 1.0, PRIM_FULLBRIGHT, ALL_SIDES, TRUE]);
}

// a key: the action in its row
press(integer i)
{
    string row = llList2String([LIVE, LIVE, "C:scenery;S:ask;S:leave", FREE, FREE, FREE, STIL, STIL, STIL], gRow);
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
            find();
            show(pick());
        }
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
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "keys");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/keys] v" + VERSION + " strip " + llList2String(["not linked", "link " + (string)gLink], gLink > 0)
                + ", row " + (string)gRow + ", free mem " + (string)llGetFreeMemory());
        else return;
        show(pick());
    }
}
