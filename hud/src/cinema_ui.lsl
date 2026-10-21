// ============================================================================
//  Take 12  -  cinema_ui.lsl  (v4)
//  Touch decoding (tap / double-tap / long press), emoji dialog menus, /77 chat
//  commands, settings in protected Linkset Data, the button look (the plain logo, always the same),
//  first-run welcome, owner-change reset.
//  Lives in the ROOT prim with cinema_core, cinema_scenery, cinema_people and
//  cinema_friends.
// ============================================================================

string VERSION = "5.3.0";
string PASS     = "cinema-1.0-build1";      // same in all scripts; change per build
integer LITE    = 0;                              // the Lite build (tools/build_lite.py) sets this to 1
string BUY_URL  = "https://marketplace.secondlife.com/";   // TODO: your Take 12 listing, shown by the Lite upgrade buttons
string NOTECARD = "Take 12 - Read Me";   // any notecard whose name contains "Read Me" also works

integer UI_STATE    = 7320;
integer UI_MENU     = 7321;
integer UI_FRIENDS  = 7322;
integer CFG_CHANGED = 7330;
integer MSG_VER     = 7360;
integer STATUS      = 7370;
integer CMD         = 7371;

float TAP_GAP   = 0.35;     // s  second tap within this = double-tap
float LONG_HOLD = 0.8;      // s  hold this long = long press

string DEFAULTS = "afk_on=1~afk_sec=180~afk_away=1~hold=60~reach=100~reach_set=100~reach_ok=0~indoors=auto~chat_cuts=1~emoji=1~look=1~face=-1~peek=1~peek_bail=0~phantom=0~cutmode=0~trace=0~cmd_chan=77~theta_max=10~seat_deg=45~aspect=1.778";

// menu items: id, emoji, title
string ITEMS = "~scenery|🏞|Scenery~personal|🚶|Personal~social|👥|Social~friends|💞|Friends~frame|🖼|Frame~pace|⏳|Pace~afk|💤|AFK~opts|⚙|Options~help|❔|Help~close|✖|Close~back|↩|Back~photo|📷|Photo~resume|▶|Resume~save|⭐|Save~next|⏭|Next~stop|⏹|Stop~modes|🎬|Modes~lively|⚡|Lively~easy|🙂|Easy~calm|🍃|Calm~slow|🌙|Slow~still|🗿|Still~indoors|🏠|Indoors~chat|💬|Chat cuts~favs|⭐|Favourites~altcam|👁|Alt-cam~phantom|🧱|Phantom~reach|📏|Reach~trace|📝|Chat text~emoji|🔤|Emoji~look|🎨|Look~th0||Classic~th1||Rec~th2||Viewfinder~test|🧪|Test cam~reset|♻|Reset~gotit|👍|Got it~off||Off~a60||1 min~a90||90 s~a120||2 min~a180||3 min~a300||5 min~a600||10 min~mcheck||Mouse check~auto||Auto~inside||Inside~outside||Outside~on||On~here||Clear here~all||Clear all~pause||Pause~end||End~ignore||Ignore~seat|🪑|Seated view~high||Higher~low||Lower~r50||50 m~r100||100 m~r150||150 m~r200||200 m~relearn||Re-learn~yes||Yes, reset~release|🔓|Release~share|👁|Share~";
list PACE_IDS  = ["lively", "easy", "calm", "slow", "still"];
list PACE_SECS = [30, 45, 60, 90, 120];

key     gOwner;
integer gChan;
integer gListen;
integer gMenuT;
integer gCmdListen;
integer gCmdChan;
integer gVerAsked;
integer gEmoji;
list    gBtn;                   // the ids of the buttons on screen
integer gFirst;
string  gPage;

// touch decoder
float   gDown;
float   gTapT;
integer gHeld;
integer gLongDone;
integer gTapN;
integer gDbl;
// what the camera is doing
string  gUiState = "idle";    // idle / rolling / frozen
string  gUiMode  = "scenery";
integer gNextCut;
integer gShownIdle = TRUE;
integer gLook = 1;          // 0 classic, 1 rec, 2 viewfinder (frames 2n open, 2n+1 clapped on the sheet)
integer gFace = ALL_SIDES;  // the prim face that carries the picture

// ============================================================================
// show frame k of the 4 x 2 sprite sheet (frame k: column k % 4, row k / 4, row 0 on top)
frame(integer k)
{
    float oy = 0.25;
    if (k > 3) oy = -0.25;
    llScaleTexture(0.25, 0.5, gFace);
    llOffsetTexture(((float)(k % 4) + 0.5) / 4.0 - 0.5, oy, gFace);
}

string cfgGet(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

cfgWrite(string k, string v)
{
    llLinksetDataWriteProtected("cin." + k, v, PASS);
}

cfgSet(string k, string v)
{
    cfgWrite(k, v);
    llMessageLinked(LINK_SET, CFG_CHANGED, k, "");
    if (k == "emoji") gEmoji = (integer)v;
    if (k == "trace") gNote = (integer)v;
    if (k == "look") { gLook = (integer)v; frame(2 * gLook); }
    if (k == "face") { gFace = (integer)v; frame(2 * gLook); }
}

initDefaults(integer force)
{
    integer i;
    list D = llParseString2List(DEFAULTS, ["~"], []);
    integer n = llGetListLength(D);
    for (i = 0; i < n; i++)
    {
        list kv = llParseString2List(llList2String(D, i), ["="], []);
        string k = llList2String(kv, 0);
        if (force || cfgGet(k) == "") cfgWrite(k, llList2String(kv, 1));
    }
    cfgWrite("ver", VERSION);
    cfgWrite("owner", (string)gOwner);
}

giveHelp()
{
    string card = "";
    if (llGetInventoryType(NOTECARD) == INVENTORY_NOTECARD) card = NOTECARD;
    else
    {
        // forgiving: any notecard in this prim with "Read Me" in its name
        integer i;
        for (i = llGetInventoryNumber(INVENTORY_NOTECARD) - 1; i >= 0; i--)
        {
            string nm = llGetInventoryName(INVENTORY_NOTECARD, i);
            if (llSubStringIndex(nm, "Read Me") >= 0) card = nm;
        }
    }
    if (card != "") llGiveInventory(gOwner, card);
    else llOwnerSay("[Take 12] No Read Me notecard in this prim. Add one with \"Read Me\" in its name.");
    llOwnerSay("[Take 12] Double-tap: scenery. Tap: menu (rolling: stop). Hold: live menu. Commands: /" + (string)gCmdChan + " help");
}

// new owner (or first run): wipe whatever was configured before
checkOwner()
{
    if (cfgGet("owner") != (string)gOwner)
    {
        llLinksetDataReset();
        initDefaults(TRUE);
        giveHelp();
    }
    else initDefaults(FALSE);
    integer v = (integer)cfgGet("cfgv");            // settings version: each step runs once
    if (v < 2) cfgWrite("trace", "0");             // 4.4.2: chat feedback is off by default
    if (v < 4)                                     // 4.4.5: reach 100 m; a reach shrunk by false alarms starts over
    {
        string rr = cfgGet("reach_set");
        if (rr != "50" && rr != "200") rr = "100";
        setReach(rr);
    }
    if (v < 5)                                     // 4.7.0: idle start 3 min + mouse check by default
    {
        string a = cfgGet("afk_sec");
        if (a == "away" || a == "90" || a == "") cfgWrite("afk_sec", "180");
        cfgWrite("afk_away", "1");
        cfgWrite("cfgv", "5");
    }
    gNote = (cfgGet("trace") == "1");
    gEmoji = (cfgGet("emoji") != "0");
    gLook = (integer)cfgGet("look");
    if (LITE) gLook = 0;
    gFace = (integer)cfgGet("face");
    gFirst = (cfgGet("seen_intro") != "1");
    llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
}

// ============================================================================
//  the button: the plain logo, always at full strength, the same idle or rolling (the screen shows the state).
// ============================================================================
nextTimer()
{
    if (gHeld || gTapN) llSetTimerEvent(0.1);
    else if (gListen) llSetTimerEvent(5.0);
    else if (!gVerAsked) llSetTimerEvent(3.0);
    else llSetTimerEvent(0.0);
}

setLook(string st)
{
    gShownIdle = (st == "off" || st == "armed");
    frame(2 * gLook);
    llSetLinkPrimitiveParamsFast(LINK_THIS, [PRIM_COLOR, ALL_SIDES, <1.0, 1.0, 1.0>, 1.0]);
    nextTimer();
}

// ============================================================================
//  menu
// ============================================================================
// chat feedback after menu choices: only when Options > Chat text is on (off by default, the menu itself shows the value)
integer gNote;
note(string s)
{
    if (gNote) llOwnerSay("[Take 12] " + s);
}

// features that only the full version has (the Lite build shows them with a lock)
integer locked(string id)
{
    if (!LITE) return FALSE;
    return (llListFindList(["personal", "social", "friends", "frame", "save", "indoors", "chat", "favs", "look", "th1", "th2"], [id]) >= 0);
}

string label(string id)
{
    integer i = llSubStringIndex(ITEMS, "~" + id + "|");
    if (i < 0) return id;
    i += 2 + llStringLength(id);
    string r = llGetSubString(ITEMS, i, i + 40);                // one entry is shorter than this
    r = llGetSubString(r, 0, llSubStringIndex(r, "~") - 1);
    list p = llParseStringKeepNulls(r, ["|"], []);
    string e = llList2String(p, 0);
    string t = llList2String(p, 1);
    if (locked(id))
    {
        if (gEmoji) return "🔒 " + t;
        return t + " (full)";
    }
    if (e == "" || !gEmoji) return t;
    return e + " " + t;
}

// the Lite build: tell about the full version and open its listing
upsell()
{
    llOwnerSay("[Take 12] That is in the full Take 12.");
    llLoadURL(gOwner, "Get the full Take 12", BUY_URL);
}

string idOf(string msg)
{
    integer i;
    integer n = llGetListLength(gBtn);
    for (i = 0; i < n; i++)
    {
        string id = llList2String(gBtn, i);
        if (label(id) == msg) return id;
    }
    return msg;
}

// llDialog fills from the bottom-left: give it the rows bottom-first, padded to full rows
list order(list ids)
{
    gBtn = ids;
    list b = [];
    integer i;
    integer n = llGetListLength(ids);
    for (i = 0; i < n; i++) b += label(llList2String(ids, i));
    while (llGetListLength(b) % 3) b += " ";
    list o = [];
    for (i = llGetListLength(b) - 3; i >= 0; i -= 3) o += llList2List(b, i, i + 2);
    return o;
}

string onoff(string k)
{
    if (cfgGet(k) == "1") return "on";
    return "off";
}

string afkText()
{
    if (cfgGet("afk_on") != "1") return "off";
    string a = cfgGet("afk_sec");
    integer n = (integer)a;
    string t = (string)n + " s";
    if (n % 60 == 0) t = (string)(n / 60) + " min";
    if (cfgGet("afk_away") == "1") t += " + mouse check";
    return t;
}

string seatText()
{
    integer d = (integer)cfgGet("seat_deg");
    if (d <= 0) return "off";
    if (d == 45) return "auto (45°)";
    return (string)d + "°";
}

string paceName()
{
    integer i = llListFindList(PACE_SECS, [(integer)cfgGet("hold")]);
    if (i < 0) return "custom";
    return llToUpper(llGetSubString(llList2String(PACE_IDS, i), 0, 0)) + llDeleteSubString(llList2String(PACE_IDS, i), 0, 0);
}

string modeName()
{
    return llToUpper(llGetSubString(gUiMode, 0, 0)) + llDeleteSubString(gUiMode, 0, 0);
}

string title()
{
    string h = "Take 12";
    if (LITE) h = "Take 12 Lite";
    if (gEmoji) h = "🎬 " + h;
    string s = "idle";
    if (gUiState == "rolling") s = modeName() + " rolling";
    else if (gUiState == "frozen") s = modeName() + " frozen";
    return h + " · " + s;
}

closeMenu()
{
    if (gListen) llListenRemove(gListen);
    gListen = 0;
    nextTimer();
}

openMenu(string page)
{
    closeMenu();
    gPage = page;
    gChan = -(integer)(llFrand(1000000000.0) + 1000.0);
    gListen = llListen(gChan, "", gOwner, "");
    gMenuT = llGetUnixTime();
    nextTimer();
    string text = title() + "\n";
    list b;
    if (page == "main")
    {
        text += "Pace: " + paceName() + " (" + cfgGet("hold") + " s) · AFK: " + afkText() + " · Indoors: " + cfgGet("indoors");
        b = ["scenery", "personal", "social", "friends", "frame", "pace", "afk", "opts", "help", "close"];
    }
    else if (page == "live")
    {
        if (gUiState == "frozen") b = ["resume"];
        else b = ["photo"];
        if (gUiMode == "scenery") b += ["save"];
        if (gUiMode == "friends") b += ["release"];
        b += ["share"];
        b += ["next", "stop", "modes", "close"];
        if (gNextCut > 0 && gUiState == "rolling") text += "next cut in " + (string)(gNextCut - llGetUnixTime()) + " s";
    }
    else if (page == "pace")
    {
        text += "How long each view is held.\nNow: " + paceName() + ", about " + cfgGet("hold") + " s\nLively 30 · Easy 45 · Calm 60 · Slow 90 · Still 120";
        b = ["lively", "easy", "calm", "slow", "still", "back"];
    }
    else if (page == "afk")
    {
        text += "Start scenery after this long with no keys.\nNow: " + afkText() + "\nMouse check: also wait until your viewer sets you Away (it notices the mouse).";
        b = ["off", "a60", "a90", "a120", "a180", "a300", "a600", "mcheck", "back"];
    }
    else if (page == "opts")
    {
        text += "Indoors: " + cfgGet("indoors") + " · Chat cuts: " + onoff("chat_cuts") + "\nAlt-cam: "
            + llList2String(["ignored", "pauses", "ignored", "ends"], (integer)cfgGet("peek") + 2 * (integer)cfgGet("peek_bail"))
            + " · Reach: " + cfgGet("reach") + " m\nPhantom: " + onoff("phantom") + " · Chat text: " + onoff("trace") + "\nSeated view: " + seatText();
        b = ["indoors", "chat", "favs", "altcam", "phantom", "reach", "trace", "look", "seat", "test", "reset", "back"];
        if (LITE) b = llListReplaceList(b, ["emoji"], 7, 7);        // Look is locked in Lite: Emoji goes here instead
    }
    else if (page == "seat")
    {
        text += "Sitting or lying down: look down on you and your friends from above.\nNow: " + seatText();
        b = ["auto", "high", "low", "off", "back"];
    }
    else if (page == "look")
    {
        text += "Button look: " + llList2String(["Classic", "Rec", "Viewfinder"], gLook) + "\nEmoji on menus: " + onoff("emoji");
        b = ["th0", "th1", "th2", "emoji", "back"];
    }
    else if (page == "indoors")
    {
        text += "Inside or outside?\nNow: " + cfgGet("indoors") + " (auto: inside in the sky)";
        b = ["auto", "inside", "outside", "back"];
    }
    else if (page == "chat")
    {
        text += "Cut to whoever speaks.\nNow: " + onoff("chat_cuts");
        b = ["on", "off", "back"];
    }
    else if (page == "favs")
    {
        text += "Saved spots of this region.";
        b = ["here", "all", "back"];
    }
    else if (page == "altcam")
    {
        text += "When you Alt-orbit while it rolls:";
        b = ["pause", "end", "ignore", "back"];
    }
    else if (page == "reach")
    {
        text += "Furthest scenery camera.\nChosen " + cfgGet("reach_set") + " m, using " + cfgGet("reach") + " m (lowers itself if your viewer holds the camera closer).";
        b = ["r50", "r100", "r150", "r200", "relearn", "back"];
    }
    else if (page == "reset")
    {
        text += "Reset ALL settings to defaults?";
        b = ["yes", "back"];
    }
    else
    {
        text = "Welcome to Take 12\nDouble-tap: scenery\nTap: menu (rolling: stop)\nHold: live menu";
        b = ["gotit", "help"];
    }
    llDialog(gOwner, text, order(b), gChan);
}

toggle(string k, string name)
{
    string v = "1";
    if (cfgGet(k) == "1") v = "0";
    cfgSet(k, v);
    note(name + ": " + onoff(k));
}

// the furthest scenery distance you chose (reach_set) and what the HUD is using now (reach: it lowers itself if your
// viewer refuses far cameras, and grows back up to reach_set)
setReach(string m)
{
    cfgSet("reach_set", m);
    cfgSet("reach", m);
    cfgSet("reach_ok", "0");
}

// "2 min" -> 120, "90 s" -> 90, "75 m" -> 75
integer toNum(string msg)
{
    integer n = (integer)msg;
    if (llSubStringIndex(msg, "min") >= 0) n = n * 60;
    return n;
}

string favKey()
{
    return "cin.fav." + llDumpList2String(llParseString2List(llGetRegionName(), [" "], []), "_");
}

onChoice(string msg)
{
    string id = idOf(msg);
    if (id == "close" || id == " ") { closeMenu(); return; }
    if (locked(id)) { closeMenu(); upsell(); return; }
    if (id == "back")
    {
        if (gPage == "altcam" || gPage == "seat" || gPage == "reach" || gPage == "reset" || gPage == "indoors" || gPage == "chat" || gPage == "favs" || gPage == "look") openMenu("opts");
        else openMenu("main");
        return;
    }
    if (gPage == "main")
    {
        if (id == "scenery" || id == "personal" || id == "social" || id == "frame")
        {
            closeMenu();
            llMessageLinked(LINK_SET, CMD, id, "");
        }
        else if (id == "friends") { closeMenu(); llMessageLinked(LINK_SET, UI_FRIENDS, "page", ""); }
        else if (id == "pace" || id == "afk") openMenu(id);
        else if (id == "opts") openMenu("opts");
        else if (id == "help") { giveHelp(); closeMenu(); }
    }
    else if (gPage == "live")
    {
        closeMenu();
        if (id == "photo" || id == "resume") llMessageLinked(LINK_SET, CMD, "photo", "");
        else if (id == "save") llMessageLinked(LINK_SET, CMD, "fav", "");
        else if (id == "next" || id == "stop") llMessageLinked(LINK_SET, CMD, id, "");
        else if (id == "release") llMessageLinked(LINK_SET, CMD, "auto", "");
        else if (id == "share") llMessageLinked(LINK_SET, CMD, "share", "");
        else if (id == "modes") openMenu("main");
    }
    else if (gPage == "pace")
    {
        integer i = llListFindList(PACE_IDS, [id]);
        if (i >= 0) cfgSet("hold", llList2String(PACE_SECS, i));
        note("Pace: " + paceName() + " (about " + cfgGet("hold") + " s per view)");
        openMenu("main");
    }
    else if (gPage == "afk")
    {
        if (id == "mcheck") { toggle("afk_away", "Mouse check"); openMenu("afk"); return; }
        if (id == "off") cfgSet("afk_on", "0");
        else
        {
            cfgSet("afk_sec", (string)toNum(msg));
            cfgSet("afk_on", "1");
        }
        note("AFK scenery: " + afkText());
        openMenu("main");
    }
    else if (gPage == "opts")
    {
        if (id == "indoors" || id == "chat" || id == "favs" || id == "altcam" || id == "seat" || id == "reach" || id == "reset" || id == "look") openMenu(id);
        else if (id == "test")
        {
            closeMenu();
            llMessageLinked(LINK_SET, CMD, "grab", "");
        }
        else
        {
            if (id == "phantom") toggle("phantom", "Phantom obstacles");
            else if (id == "trace") toggle("trace", "Trace lines");
            else if (id == "emoji") toggle("emoji", "Emoji");
            openMenu("opts");
        }
    }
    else if (gPage == "look")
    {
        if (llGetSubString(id, 0, 1) == "th") cfgSet("look", llGetSubString(id, 2, 2));
        else if (id == "emoji") toggle("emoji", "Emoji");
        openMenu("look");
    }
    else if (gPage == "indoors")
    {
        cfgSet("indoors", id);
        note("Indoors: " + id);
        openMenu("opts");
    }
    else if (gPage == "chat")
    {
        if (id == "on") cfgSet("chat_cuts", "1");
        else cfgSet("chat_cuts", "0");
        note("Chat cuts: " + onoff("chat_cuts"));
        openMenu("opts");
    }
    else if (gPage == "favs")
    {
        if (id == "here") llLinksetDataDeleteProtected(favKey(), PASS);
        else
        {
            list ks = llLinksetDataFindKeys("^cin\\.fav\\.", 0, 100);
            integer j;
            for (j = 0; j < llGetListLength(ks); j++) llLinksetDataDeleteProtected(llList2String(ks, j), PASS);
        }
        note("Favourite spots cleared.");
        openMenu("opts");
    }
    else if (gPage == "seat")
    {
        cfgSet("seat_deg", llList2String(["0", "45", "60", "30"], llListFindList(["off", "auto", "high", "low"], [id]) + 1));
        note("Seated view: " + seatText());
        openMenu("opts");
    }
    else if (gPage == "altcam")
    {
        if (id == "pause") { cfgSet("peek", "1"); cfgSet("peek_bail", "0"); }
        else if (id == "end") { cfgSet("peek", "1"); cfgSet("peek_bail", "1"); }
        else if (id == "ignore") cfgSet("peek", "0");
        openMenu("opts");
    }
    else if (gPage == "reach")
    {
        if (id == "relearn") setReach(cfgGet("reach_set"));
        else setReach((string)toNum(msg));
        openMenu("opts");
    }
    else if (gPage == "reset")
    {
        if (id == "yes")
        {
            initDefaults(TRUE);
            gEmoji = TRUE;
            llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
            note("Settings reset to defaults.");
        }
        openMenu("opts");
    }
    else
    {
        closeMenu();
        if (id == "help") giveHelp();
    }
}

// ============================================================================
//  touch gestures
// ============================================================================
onTap()
{
    if (gUiState == "rolling") llMessageLinked(LINK_SET, CMD, "stop", "");
    else if (gUiState == "frozen") llMessageLinked(LINK_SET, CMD, "photo", "");
    else openMenu("main");
}

onDouble()
{
    if (gUiState == "idle") llMessageLinked(LINK_SET, CMD, "scenery", "");
    else llMessageLinked(LINK_SET, CMD, "next", "");
}

onLong()
{
    if (gUiState == "idle") openMenu("main");
    else openMenu("live");
}

// ============================================================================
//  chat commands: /77 <command>
// ============================================================================
help()
{
    llOwnerSay("[Take 12] Commands on /" + (string)gCmdChan + ": scenery personal social friends frame stop next photo menu status pace reach indoors face chan reset (details: Read Me).");
}

onCommand(string msg)
{
    list a = llParseString2List(llToLower(llStringTrim(msg, STRING_TRIM)), [" "], []);
    string c = llList2String(a, 0);
    string v = llList2String(a, 1);
    integer n = (integer)v;
    if (LITE && (c == "personal" || c == "social" || c == "friends" || c == "frame" || c == "fav" || c == "friend" || c == "indoors")) upsell();
    else if (c == "scenery" || c == "personal" || c == "social" || c == "friends" || c == "frame" || c == "stop" || c == "next" || c == "photo" || c == "fav" || c == "grab") llMessageLinked(LINK_SET, CMD, c, "");
    else if (c == "menu") openMenu("main");
    else if (c == "status")
    {
        llOwnerSay("[Take 12/ui] v" + VERSION + " commands on /" + (string)gCmdChan + ", AFK scenery " + afkText()
            + ", pace " + paceName() + " (" + cfgGet("hold") + " s), reach " + cfgGet("reach") + " m, free mem " + (string)llGetFreeMemory());
        llMessageLinked(LINK_SET, STATUS, "?", "");
    }
    else if ((c == "pace" || c == "hold") && n >= 10 && n <= 600) { cfgSet("hold", (string)n); llOwnerSay("[Take 12] Pace: about " + v + " s per view"); }
    else if (c == "reach" && v == "relearn") { setReach(cfgGet("reach_set")); llOwnerSay("[Take 12] Reach re-learned from " + cfgGet("reach_set") + " m"); }
    else if (c == "reach" && n >= 20 && n <= 250) { setReach(v); llOwnerSay("[Take 12] Scenery reach: " + v + " m"); }
    else if (c == "indoors" && (v == "auto" || v == "inside" || v == "outside")) { cfgSet("indoors", v); llOwnerSay("[Take 12] Indoors: " + v); }
    else if (c == "face" && v != "")
    {
        if (v == "all") n = -1;
        cfgSet("face", (string)n);
        llOwnerSay("[Take 12] Picture face: " + v);
    }
    else if (c == "friend" && (v == "list" || v == "clear")) llMessageLinked(LINK_SET, UI_FRIENDS, v, "");
    else if (c == "trace" || c == "emoji" || c == "cutmode")
    {
        cfgSet(c, (string)(v == "on"));
        llOwnerSay("[Take 12] " + c + ": " + onoff(c));
    }
    else if (c == "chan" && n > 0 && n != 9)
    {
        cfgSet("cmd_chan", (string)n);
        gCmdChan = n;
        if (gCmdListen) llListenRemove(gCmdListen);
        gCmdListen = llListen(gCmdChan, "", gOwner, "");
        llOwnerSay("[Take 12] Commands now on /" + v);
    }
    else if (c == "reset")
    {
        initDefaults(TRUE);
        gEmoji = TRUE;
        llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
        llOwnerSay("[Take 12] Settings reset to defaults.");
    }
    else help();
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        checkOwner();
        llSetLinkPrimitiveParamsFast(LINK_THIS, [PRIM_GLOW, ALL_SIDES, 0.0, PRIM_FULLBRIGHT, ALL_SIDES, TRUE]);
        frame(2 * gLook);
        setLook("armed");
        gCmdChan = (integer)cfgGet("cmd_chan");
        if (gCmdChan <= 0) gCmdChan = 77;
        gCmdListen = llListen(gCmdChan, "", gOwner, "");
        if (gFirst)
        {
            cfgWrite("seen_intro", "1");
            openMenu("welcome");
        }
        nextTimer();
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
    }

    touch_start(integer n)
    {
        if (llDetectedKey(0) != gOwner) return;
        float now = llGetTime();
        if (gTapN)
        {
            gTapN = FALSE;
            if (now - gTapT <= TAP_GAP) gDbl = TRUE;
            else onTap();
        }
        gDown = now;
        gHeld = TRUE;
        gLongDone = FALSE;
        nextTimer();
    }

    touch_end(integer n)
    {
        if (llDetectedKey(0) != gOwner) return;
        gHeld = FALSE;
        if (gLongDone) { nextTimer(); return; }
        if (gDbl)
        {
            gDbl = FALSE;
            onDouble();
        }
        else
        {
            gTapN = TRUE;
            gTapT = llGetTime();
        }
        nextTimer();
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == UI_STATE)
        {
            list L = llParseString2List(str, ["|"], []);
            string st = llList2String(L, 0);
            gUiMode = llList2String(L, 1);
            gNextCut = (integer)llList2String(L, 2);
            if (st == "rolling" || st == "peek") gUiState = "rolling";
            else if (st == "frozen") gUiState = "frozen";
            else gUiState = "idle";
            setLook(st);
        }
        else if (num == UI_MENU) openMenu(str);
        else if (num == MSG_VER && str != "?" && str != VERSION)
            llOwnerSay("[Take 12] WARNING: " + (string)id + " script is version " + str + ", ui is " + VERSION + ". Re-drop all Take 12 scripts from the same release.");
    }

    listen(integer channel, string name, key id, string msg)
    {
        if (id != gOwner) return;
        if (channel == gCmdChan) onCommand(msg);
        else
        {
            gMenuT = llGetUnixTime();
            onChoice(msg);
        }
    }

    timer()
    {
        float now = llGetTime();
        if (!gVerAsked)
        {
            gVerAsked = TRUE;
            llMessageLinked(LINK_SET, MSG_VER, "?", "ui");
        }
        if (gHeld && !gLongDone && !gDbl && now - gDown >= LONG_HOLD)
        {
            gLongDone = TRUE;
            onLong();
        }
        if (gTapN && now - gTapT > TAP_GAP)
        {
            gTapN = FALSE;
            onTap();
        }
        if (gListen && llGetUnixTime() - gMenuT > 60) closeMenu();
        nextTimer();
    }
}
