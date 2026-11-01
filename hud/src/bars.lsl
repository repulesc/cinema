// ============================================================================
//  Take 12  -  bars.lsl  (8.0)  - the letterbox: the film's frame
//  Four parts named "t12 bar0" … "t12 bar3" become the bars round the picture: top and bottom when the frame is wider
//  than your window, left and right when it is narrower (pillarbox: the photo frames, ultrawide windows). The film has
//  one cinema frame for every shot (cin.shape: 2.39 · 2.00 · 1.85 · 1.66 · full; 2.39 by default; 8.5.9, each shot had
//  its own and the bars jumped at every change). While the shutter is open (core's "photo" state, 8.1.0) the frame is your photo frame, one
//  for every shot (cin.photo: 3:2 · 4:3 · 1:1 · 4:5, 3:2 by default). The strip's ▭ shows the frame on screen and opens
//  its dialog, here: the cinema frames while filming, the photo frames while the shutter is open (Settings › Frames &
//  bars opens either). /12 bars turns them on and off for every shot (cin.bars); Black or Dimmed (cin.bstyle). They
//  show only while a Take 12 shot is on screen (not with your own camera); watching someone's film, their shape
//  (sync: CMD "bars|follow <shape>", "bars|follow" to end).
//  Tells the shots the picture to compose in (CROP "<ratio>|<window>", 0 = the whole window) and the strip what to
//  show by the frame key (SHAPE "<label>|<on/off/dim>"). HUD geometry as crop.lsl (7.x): HUD space is 1.0 tall and
//  llGetCameraAspect() wide, +Y left; the bars sit behind the [12] so it stays clickable.
// ============================================================================

string VERSION = "8.9.0";
string PASS    = "cinema-1.0-build1";

integer SHOT        = 7310;          // the basic shot (core asks: CMD "basic", 8.9.1)
integer UI_STATE    = 7320;
integer CFG_CHANGED = 7330;
integer TIP         = 7345;
integer NOTE        = 7344;
integer SHAPE       = 7348;
integer MSG_VER     = 7360;
integer STATUS      = 7370;
integer CMD         = 7371;
integer TXT         = 7346;
integer TXT_ANS     = 7347;
integer CROP        = 7390;

list    SHOTS   = ["tracking", "portrait", "fixed", "scenic"];
list    FRAMES  = ["3:2", 1.5, "4:3", 1.3333, "1:1", 1.0, "4:5", 0.8];   // the photo frames (8.0.9), "a:b"
float   DEPTH   = 0.006;           // m behind the [12] (+X into the screen)

key     gOwner;
list    gBars;                     // the four bars' links
float   gA = 1.778;                // your window
integer gSY = 1;
string  gState = "wait";
string  gShot;
string  gFollow;                   // watching: their shape ("" none)
integer gOn = TRUE;                // /12 bars: on or off for every shot
float   gDim = 1.0;                // Black 1.0, Dimmed 0.6
string  gSent;
integer gFb;                        // the basic shot's turn round you
vector  gRootAt;                   // where the root was when the bars were cut (screen moves it: place, size)
integer gChan;                     // the frame dialog (8.1.0: moved here from ui, which had no room)
integer gLh;
integer gDlgT;
string  gPage;                     // its shot, or "photo"
list    gBtn;

// a basic shot when a shot's script is silent, or Scenic finds no view (core asks; 8.9.1: it lived in core, which needed
// the room): a level portrait of you, at eye height, from a new side each time
basic()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2) return;
    vector P = llList2Vector(d, 0);
    vector F = llRot2Fwd(llList2Rot(d, 1));
    F.z = 0.0;
    if (llVecMag(F) < 0.01) F = <1.0, 0.0, 0.0>;
    F = llVecNorm(F);
    vector sz = llGetAgentSize(gOwner);
    vector E = <P.x, P.y, P.z + 0.37 * sz.z>;
    vector dir = F * llEuler2Rot(<0.0, 0.0, llList2Float([30.0, -30.0, 150.0, -150.0], gFb % 4) * DEG_TO_RAD>);
    gFb++;
    float dist = 3.0;
    list r = llCastRay(E, E + dir * dist, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
    if (llList2Integer(r, -1) == 1) dist = llVecDist(E, llList2Vector(r, 1)) - 0.4;
    if (dist < 1.2) dist = 1.2;
    vector cam = E + dir * dist;
    llMessageLinked(LINK_SET, SHOT, (string)cam + "|" + (string)<E.x, E.y, cam.z> + "|", "");
}

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

find()
{
    gBars = [0, 0, 0, 0];
    integer i;
    for (i = 2; i <= llGetNumberOfPrims(); i++)
    {
        string n = llGetLinkName(i);
        integer k = (integer)llGetSubString(n, 7, -1);
        if (llGetSubString(n, 0, 6) == "t12 bar" && k < 4) gBars = llListReplaceList(gBars, [i], k, k);
    }
}

load()
{
    gOn = (cfg("bars") != "0");
    gDim = 1.0;
    if (cfg("bstyle") == "dim") gDim = 0.6;
    gSY = 1;
    if (cfg("flip") == "1") gSY = -1;
    integer i;                          // 8.0.9 kept photo frames per shot: the first becomes your photo frame (8.1.0);
    for (i = 0; i < 4; i++)             // 8.5.9: one film frame for every shot, the shots' own ones are gone
    {
        string s = cfg("shape." + llList2String(SHOTS, i));
        if (llListFindList(FRAMES, [s]) >= 0 && cfg("photo") == "") llLinksetDataWriteProtected("cin.photo", s, PASS);
        if (s != "") llLinksetDataDeleteProtected("cin.shape." + llList2String(SHOTS, i), PASS);
    }
}

// your photo frame
string photo()
{
    string s = cfg("photo");
    if (s == "") s = "3:2";
    return s;
}

// the film's frame, the same for every shot (8.5.9: each shot had its own, and the bars jumped at every change)
string film()
{
    string s = cfg("shape");
    if (s == "") s = "2.39";
    return s;
}

// the frame dialog: a shot's cinema frames (widest first), or "photo": the photo frames, the one in use marked
frame(string p)
{
    string now = photo();
    list F = ["3:2", "4:3", "1:1", "4:5"];
    list b = [];
    if (p != "photo")
    {
        now = film();
        F = ["2.39", "2.00", "1.85", "1.66", "Full"];
        b = ["‹ Back"];
    }
    list m = [];
    integer i;
    for (i = 0; i < llGetListLength(F); i++)
    {
        string f = llList2String(F, i);
        if (llToLower(f) == now) f = "● " + f;
        m += f;
    }
    gBtn = m + b + ["Done"];
    while (llGetListLength(gBtn) % 3) gBtn += " ";
    list o = [];
    for (i = llGetListLength(gBtn) - 3; i >= 0; i -= 3) o += llList2List(gBtn, i, i + 2);   // llDialog fills from the bottom row
    gBtn = o;
    gPage = p;
    if (gLh) llListenRemove(gLh);
    gChan = -200000 - (integer)llFrand(900000000.0);
    gLh = llListen(gChan, "", gOwner, "");
    gDlgT = llGetUnixTime();
    llMessageLinked(LINK_SET, TXT, "frame|" + p + "~" + now, "bars");
}

// a shot's frame: the film's ("2.39", … or "full"); none for something that is not a shot
string shapeOf(string shot)
{
    if (llListFindList(SHOTS, [shot]) < 0) return "full";
    return film();
}


// a frame's width over height: "2.39" 2.39, "4:5" 0.8, "full" 0
float num(string s)
{
    integer i = llListFindList(FRAMES, [s]);
    if (i >= 0) return llList2Float(FRAMES, i + 1);
    return (float)s;
}

// a friend's shape comes as a number ("0.80"): its frame's name for the strip
string name(string s)
{
    integer i;
    for (i = 1; i < 8; i += 2)
        if (llFabs((float)s - llList2Float(FRAMES, i)) < 0.02) return llList2String(FRAMES, i - 1);
    if (s == "full") return "FULL";
    return s;
}

// the shape on screen now: 0 = none (your own camera, bars off, Full)
float ratio()
{
    if (gFollow != "") return num(gFollow);
    if (!gOn || gShot == "" || gState == "wait" || gState == "off" || gState == "letgo") return 0.0;
    if (gState == "photo") return num(photo());
    return num(shapeOf(gShot));
}

// the screen centre from the HUD point worn on (crop.lsl)
vector centre()
{
    integer p = llListFindList([ATTACH_HUD_TOP_RIGHT, ATTACH_HUD_TOP_CENTER, ATTACH_HUD_TOP_LEFT, ATTACH_HUD_BOTTOM_LEFT,
        ATTACH_HUD_BOTTOM, ATTACH_HUD_BOTTOM_RIGHT], [llGetAttached()]);
    if (p < 0) return ZERO_VECTOR;
    return <0.0, gA * 0.5 * gSY * llList2Float([1.0, 0.0, -1.0, -1.0, 0.0, 1.0], p), 0.5 * llList2Float([-1.0, -1.0, -1.0, 1.0, 1.0, 1.0], p)>;
}

list bar(integer link, float y, float z, float w, float h)
{
    if (!link) return [];
    vector p = llGetLocalPos();
    rotation r = llGetLocalRot();
    vector at = centre() + <p.x + DEPTH, y * gSY, z>;
    float a = gDim;
    if (w <= 0.0 || h <= 0.0)
    {
        w = 0.01;
        h = 0.01;
        a = 0.0;
        at = p + <DEPTH, 0.0, 0.0>;
    }
    return [PRIM_LINK_TARGET, link, PRIM_POS_LOCAL, (at - p) / r, PRIM_ROT_LOCAL, ZERO_ROTATION / r, PRIM_SIZE, <0.01, w, h>,
        PRIM_COLOR, ALL_SIDES, ZERO_VECTOR, a, PRIM_TEXTURE, ALL_SIDES, TEXTURE_BLANK, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0];
}

cut()
{
    if (!llGetAttached()) return;
    gRootAt = llGetLocalPos();
    float r = ratio();
    float a = gA;
    float sw = 0.0;
    float th = 0.0;
    if (r > 0.0 && r < a) sw = (a - r) * 0.5;
    else if (r > a) th = (1.0 - a / r) * 0.5;
    llSetLinkPrimitiveParamsFast(LINK_ROOT, bar(llList2Integer(gBars, 0), (r + sw) * 0.5, 0.0, sw, 1.0)
        + bar(llList2Integer(gBars, 1), -(r + sw) * 0.5, 0.0, sw, 1.0)
        + bar(llList2Integer(gBars, 2), 0.0, 0.5 - th * 0.5, a, th)
        + bar(llList2Integer(gBars, 3), 0.0, th * 0.5 - 0.5, a, th));
    tell();
}

// the shots compose inside the shape; the strip's ▭ shows it
tell()
{
    float r = ratio();
    string s = (string)r + "|" + (string)gA;
    string lbl = "DIM";
    string st = "dim";
    if (gShot != "" && gState != "off" && gState != "wait")
    {
        st = llList2String(["off", "on"], gOn);
        lbl = shapeOf(gShot);
        if (gState == "photo") lbl = photo();
        if (!gOn || lbl == "full") lbl = "FULL";
    }
    if (gFollow != "")
    {
        lbl = name(gFollow);
        st = "on";
    }
    s += "~" + lbl + "|" + st;
    if (s == gSent) return;
    gSent = s;
    if (r > 0.0) llMessageLinked(LINK_SET, TIP, "snapshot", "");   // once ever: snapshots have no bars
    llMessageLinked(LINK_SET, CROP, (string)r + "|" + (string)gA, "");
    llMessageLinked(LINK_SET, SHAPE, lbl + "|" + st, "");
}

measure()
{
    if (!(llGetPermissions() & PERMISSION_TRACK_CAMERA)) return;
    float a = llGetCameraAspect();
    if (a < 0.3 || llFabs(a - gA) < 0.005) return;
    gA = a;
    if (llFabs(a - (float)cfg("aspect")) >= 0.01) llLinksetDataWriteProtected("cin.aspect", (string)a, PASS);
    cut();
}

default
{
    state_entry()
    {
        gOwner = llGetOwner();
        find();
        load();
        gA = (float)cfg("aspect");
        if (gA < 0.3) gA = 1.778;
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "bars");
        cut();
        llSetTimerEvent(2.0);
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id == NULL_KEY) return;
        gState = "wait";
        gShot = "";
        gFollow = "";
        llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
    }

    run_time_permissions(integer p)
    {
        measure();
        cut();
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
        if (c & CHANGED_LINK) { find(); cut(); }
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == UI_STATE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            if (llList2String(L, 0) == "photo" && gState != "photo") llMessageLinked(LINK_SET, NOTE, "photo|" + photo(), "");   // the shutter open
            gState = llList2String(L, 0);
            gShot = llList2String(L, 1);
            cut();
        }
        else if (num == CMD && str == "basic") basic();
        else if (num == CMD && str == "bars")
        {
            if (gShot == "" || gState == "wait" || gState == "off") return;   // your own camera: the key is dim
            gOn = !gOn;
            llLinksetDataWriteProtected("cin.bars", (string)gOn, PASS);
            cut();
        }
        else if (num == CMD && llGetSubString(str, 0, 5) == "frames")
        {
            string p = llGetSubString(str, 7, -1);          // "frames|<shot>" or "frames|photo" (Settings), "frames" (the ▭)
            if (str == "frames")
            {
                if (gShot == "" || gState == "wait" || gState == "off") return;   // your own camera: the key is dim
                p = gShot;
                if (gState == "photo") p = "photo";
            }
            frame(p);
        }
        else if (num == TXT_ANS && id == "bars" && gLh && llGetSubString(str, 0, 5) == "frame|")
            llDialog(gOwner, llGetSubString(str, 6, -1), gBtn, gChan);
        else if (num == CMD && llGetSubString(str, 0, 10) == "bars|follow")
        {
            gFollow = "";                                   // "bars|follow": your own again
            if (str != "bars|follow") gFollow = llStringTrim(llGetSubString(str, 12, -1), STRING_TRIM);   // "full": no bars
            cut();
        }
        else if (num == CFG_CHANGED && (str == "shape" || str == "bars" || str == "bstyle" || str == "flip" || str == "all"))
        {
            load();
            gSent = "";
            cut();
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "bars");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/bars] v" + VERSION + " " + (string)ratio() + " on a " + (string)gA + " window, bars " + llList2String(["off", "on"], gOn)
                + ", " + (string)llGetListLength(llParseString2List(llDumpList2String(gBars, ","), ["0", ","], [])) + " parts, free mem " + (string)llGetFreeMemory());
    }

    listen(integer ch, string name, key id, string m)
    {
        if (ch != gChan) return;
        if (llGetSubString(m, 0, 1) == "● ") m = llGetSubString(m, 2, -1);
        if (m == "Done" || m == " " || m == "‹ Back")
        {
            llListenRemove(gLh);
            gLh = 0;
            if (m == "‹ Back") llMessageLinked(LINK_SET, CMD, "menu|shapes", "");   // Settings › Frames & bars
            return;
        }
        string k = "shape";
        if (gPage == "photo") k = "photo";
        llLinksetDataWriteProtected("cin." + k, llToLower(m), PASS);
        if (m != "Full" && !gOn) llLinksetDataWriteProtected("cin.bars", "1", PASS);   // a frame picked is a frame shown
        load();
        gSent = "";
        cut();
        frame(gPage);                                   // the dialog stays: the snapshot size for the new frame
    }

    timer()
    {
        if (gLh && llGetUnixTime() - gDlgT > 120) { llListenRemove(gLh); gLh = 0; }
        measure();
        if (llVecDist(llGetLocalPos(), gRootAt) > 0.0005) cut();      // the strip moved the root: the bars stay on the screen
    }
}
