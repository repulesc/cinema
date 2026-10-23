// ============================================================================
//  Take 12  -  crop.lsl  (v6.2)  - Frame: the picture format on your screen
//  Darkens your screen outside a chosen picture format (3:2, 4:5, 1:1, 4:3, 2.39:1, 9:16), like a camera's
//  viewfinder, with four bars: four boxes linked to the HUD (any links but the root and the keys strip). Snapshots
//  leave HUDs out, so the bars never spoil a picture: set the snapshot size to the same ratio.
//  HUD space is 1.0 tall and as wide as your window (llGetCameraAspect), +Y to the left, +Z up, +X into the screen; every HUD point has
//  its origin at its own corner, edge or the centre. The bars are placed from the screen centre, through the root's
//  own position and rotation, so the button can sit anywhere.
//  Also measures your window for the cameras (cin.aspect; they assumed 16:9) and tells them the format (CROP).
//  Its own menu (ui routes the Frame button here); chat: /77 crop 4:5 | off | flip | back (via picker).
//  Checked in tools/sim/crop_sim.py.
// ============================================================================

string VERSION = "6.6.0";
string PASS    = "cinema-1.0-build1";

integer START       = 7301;
integer UI_MENU     = 7321;
integer CFG_CHANGED = 7330;
integer MSG_VER     = 7360;
integer STATUS      = 7370;
integer CMD         = 7371;
integer CROP        = 7390;   // here -> cameras  "<format>|<window>" (format 0 = off), for composing inside the frame

list    NAMES  = ["3:2", "4:5", "1:1", "4:3", "2.39:1", "9:16"];
list    RATIOS = [1.5, 0.8, 1.0, 1.333333, 2.39, 0.5625];
float   DIM    = 0.6;         // how dark outside the frame (1 = black)
float   DEPTH  = 0.02;        // m  the bars sit this far behind the button (HUD +X points into the screen)

key     gOwner;
float   gR;                  // the format (width / height), 0 = off
float   gA = 1.777778;       // your window
integer gSY = 1;             // HUD +Y is to the left (/77 crop flip if a viewer differs)
integer gSX = 1;             // ... and the bars go behind the button, so it stays clickable (/77 crop back flips it)
list    gBars;               // the four bars' link numbers (any child but the keys strip, keys.lsl)
integer gChan;
integer gL;                  // the menu's listener (0: closed)
integer gMenuT;

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

set(string k, string v)
{
    llLinksetDataWriteProtected("cin." + k, v, PASS);
}

string ratioName(float r)
{
    integer i = llListFindList(RATIOS, [r]);
    if (i < 0) return "off";
    return llList2String(NAMES, i);
}

// the screen centre, seen from the HUD point the button is worn on
vector centre()
{
    integer p = llListFindList([ATTACH_HUD_TOP_RIGHT, ATTACH_HUD_TOP_CENTER, ATTACH_HUD_TOP_LEFT, ATTACH_HUD_BOTTOM_LEFT,
        ATTACH_HUD_BOTTOM, ATTACH_HUD_BOTTOM_RIGHT], [llGetAttached()]);
    if (p < 0) return ZERO_VECTOR;                          // Center, Center 2
    float y = gA * 0.5 * gSY * llList2Float([1.0, 0.0, -1.0, -1.0, 0.0, 1.0], p);
    float z = 0.5 * llList2Float([-1.0, -1.0, -1.0, 1.0, 1.0, 1.0], p);
    return <0.0, y, z>;
}

// one bar: its middle (y, z) and size (w, h) on the screen, around the centre; w = 0 hides it
bar(integer link, float y, float z, float w, float h)
{
    rotation r = llGetLocalRot();
    vector p = llGetLocalPos();
    vector at = centre() + <p.x + gSX * DEPTH, y * gSY, z>;
    float a = DIM;
    if (w <= 0.0 || h <= 0.0)
    {
        w = 0.01;
        h = 0.01;
        a = 0.0;
    }
    llSetLinkPrimitiveParamsFast(link, [PRIM_POS_LOCAL, (at - p) / r, PRIM_ROT_LOCAL, ZERO_ROTATION / r,
        PRIM_SIZE, <0.01, w, h>, PRIM_COLOR, ALL_SIDES, ZERO_VECTOR, a]);
}

// the four bars: left and right when the format is narrower than your window, top and bottom when it is wider
cut()
{
    if (llGetListLength(gBars) < 4 || !llGetAttached()) return;
    float r = gR;
    float a = gA;
    float sw = 0.0;
    float th = 0.0;
    if (r > 0.0 && r < a) sw = (a - r) * 0.5;
    else if (r > a) th = (1.0 - a / r) * 0.5;
    bar(llList2Integer(gBars, 0), (r + sw) * 0.5, 0.0, sw, 1.0);       // left (+Y)
    bar(llList2Integer(gBars, 1), -(r + sw) * 0.5, 0.0, sw, 1.0);      // right
    bar(llList2Integer(gBars, 2), 0.0, 0.5 - th * 0.5, a, th);         // top
    bar(llList2Integer(gBars, 3), 0.0, th * 0.5 - 0.5, a, th);         // bottom
}

// the timer runs only while a frame is on (your window may change) or the menu is open
tick()
{
    llSetTimerEvent(2.0 * (gR > 0.0 || gL != 0));
}

// your window: kept for the cameras, which compose for it
measure(integer force)
{
    if (!(llGetPermissions() & PERMISSION_TRACK_CAMERA)) return;
    float a = llGetCameraAspect();
    if (a < 0.3 || (!force && llFabs(a - gA) < 0.005)) return;
    gA = a;
    cut();
    if (llFabs(a - (float)cfg("aspect")) >= 0.01)
    {
        set("aspect", (string)a);
        llMessageLinked(LINK_SET, CFG_CHANGED, "aspect", "");
    }
    tell();
}

tell()
{
    llMessageLinked(LINK_SET, CROP, (string)gR + "|" + (string)gA, "");
}

choose(float r)
{
    gR = r;
    set("crop", (string)r);
    llMessageLinked(LINK_SET, CFG_CHANGED, "crop", "");      // the cameras compose inside the new format
    cut();
    tick();
    tell();
}

menu()
{
    if (gL) llListenRemove(gL);
    gChan = -(integer)(llFrand(1000000000.0) + 1000.0);
    gL = llListen(gChan, "", gOwner, "");
    gMenuT = llGetUnixTime();
    tick();
    string t = "Frame · the picture format on your screen, outside dimmed\nNow: " + ratioName(gR) + " · your window "
        + llGetSubString((string)gA, 0, 3) + ":1\nSnapshots: set the same ratio as the snapshot size.";
    if (llGetListLength(gBars) < 4) t = "Frame needs four small boxes linked to the HUD, with the button as the root (Read Me > FRAME).";
    list b = [];
    integer i;
    for (i = 0; i < 6; i++)
    {
        string n = llList2String(NAMES, i);
        if (llList2Float(RATIOS, i) == gR) n = "✓ " + n;
        b += [n];
    }
    string back = llList2String(["Back", "‹ Back", "↩ Back"], (integer)cfg("skin"));
    llDialog(gOwner, t, ["Off", " ", back] + llList2List(b, 3, 5) + llList2List(b, 0, 2), gChan);
}

hear(string m)
{
    if (llSubStringIndex(m, "Back") >= 0)
    {
        llListenRemove(gL);
        gL = 0;
        tick();
        llMessageLinked(LINK_SET, UI_MENU, "main", "");
        return;
    }
    if (m == " ") return;
    if (m == "Off") choose(0.0);
    else
    {
        integer i = llListFindList(NAMES, [llList2String(llParseString2List(m, [" "], []), -1)]);
        if (i < 0) return;
        choose(llList2Float(RATIOS, i));
    }
    menu();
}

// /77 crop <format | off | flip | back>
command(string v)
{
    integer i = llListFindList(NAMES, [v]);
    if (i >= 0) choose(llList2Float(RATIOS, i));
    else if (v == "off") choose(0.0);
    else if (v == "flip" || v == "back")
    {
        if (v == "flip") gSY = -gSY;
        else gSX = -gSX;
        set("crop_s", (string)gSY + "|" + (string)gSX);
        llMessageLinked(LINK_SET, CFG_CHANGED, "crop_s", "");     // the keys (keys.lsl) follow the same side
        cut();
    }
    llOwnerSay("[Take 12] Frame: " + ratioName(gR));
}

load()
{
    gR = (float)cfg("crop");
    if (ratioName(gR) == "off") gR = 0.0;
    list s = llParseString2List(cfg("crop_s"), ["|"], []);
    if (llGetListLength(s) == 2)
    {
        gSY = (integer)llList2String(s, 0);
        gSX = (integer)llList2String(s, 1);
    }
}

// the boxes: plain, dark, quiet; once
setup()
{
    gBars = [];
    integer n;
    integer i;
    // the boxes that are bars already first, then any other child, lowest link first; never the soft-key strip
    // (named "... keys", or the highest unclaimed child, which keys.lsl takes)
    for (n = 0; n < 2; n++)
        for (i = 2; i <= llGetNumberOfPrims() && llGetListLength(gBars) < 4; i++)
        {
            string m = llToLower(llGetLinkName(i));
            if ((m == "take 12 frame") == (n == 0) && llSubStringIndex(m, "keys") < 0)
            {
                gBars += [i];
                llSetLinkPrimitiveParamsFast(i, [PRIM_NAME, "Take 12 frame", PRIM_TEXTURE, ALL_SIDES, TEXTURE_BLANK, <1, 1, 0>, ZERO_VECTOR, 0.0,
                    PRIM_FULLBRIGHT, ALL_SIDES, TRUE, PRIM_GLOW, ALL_SIDES, 0.0]);
            }
        }
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        load();
        setup();
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "crop");
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
            setup();
            cut();
        }
    }

    attach(key id)
    {
        if (id != NULL_KEY) llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
    }

    run_time_permissions(integer p)
    {
        measure(TRUE);                                      // measure afresh
        cut();
        tick();
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == CMD && str == "crop") menu();
        else if (num == CMD && llGetSubString(str, 0, 4) == "crop|") command(llDeleteSubString(str, 0, 4));
        else if (num == START) measure(FALSE);
        else if (num == CFG_CHANGED && str == "all")
        {
            load();
            cut();
            tick();
            tell();
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "crop");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/crop] v" + VERSION + " frame " + ratioName(gR) + ", window " + (string)gA + ", "
                + (string)llGetListLength(gBars) + " bars, free mem " + (string)llGetFreeMemory());
    }

    listen(integer ch, string name, key id, string msg)
    {
        hear(msg);
    }

    timer()
    {
        if (gL && llGetUnixTime() - gMenuT > 60)
        {
            llListenRemove(gL);
            gL = 0;
        }
        measure(FALSE);
        tick();
    }
}
