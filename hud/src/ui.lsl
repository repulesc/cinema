// ============================================================================
//  Take 12  -  ui.lsl  (v4)
//  Touch decoding (tap / double-tap / long press), emoji dialog menus, /77 chat
//  commands, settings in protected Linkset Data, the button look (the plain logo, always the same),
//  first-run welcome, owner-change reset.
//  Lives in the ROOT prim with core, scenery, people and
//  friends.
// ============================================================================

string VERSION = "6.5.0";
string PASS     = "cinema-1.0-build1";      // same in all scripts; change per build
integer LITE    = 0;                              // the free Take 12 Scenery build (tools/build_scenery.py) sets this to 1
string BUY_URL  = "https://marketplace.secondlife.com/";   // TODO: your Take 12 listing (Take 12 Scenery's "More cameras" opens it)
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

string DEFAULTS = "afk_on=1~afk_sec=180~afk_away=1~hold=60~reach=100~reach_set=100~reach_ok=0~indoors=auto~chat_cuts=1~skin=1~tips=1~tipn=0~status=1~look=1~face=-1~peek=1~peek_bail=0~phantom=0~cutmode=0~trace=0~cmd_chan=77~theta_max=10~seat_deg=45~aspect=1.778";

// menu items: id, emoji (Color style), mark (Symbols style), title (Plain style)
string ITEMS = "~scenery|🏞|◇|Scenery~personal|🚶|○|Me~frame|🖼|□|Still~pace|⏳||Pace~afk|💤||Idle start~opts|⚙|≡|Options~help|❔|?|Help~close|✖|×|Close~back|↩|‹|Back~photo|📷|▣|Photo~resume|▶|›|Resume~save|⭐|☆|Save~next|⏭|»|Next~stop|⏹|■|Stop~modes|🎬|◇|Modes~lively|⚡||Lively~easy|🙂||Easy~calm|🍃||Calm~slow|🌙||Slow~still|🗿||Slowest~indoors|🏠||Indoors~chat|💬||Chat cuts~favs|⭐|☆|Favourites~altcam|👁||Alt-cam~phantom|🧱||Phantom~reach|📏||Reach~trace|📝||Chat text~look|🎨|◐|Look~th0|||Classic~th1|||Rec~th2|||Viewfinder~test|🧪|◌|Test cam~reset|♻|↺|Reset~gotit|👍||Got it~off|||Off~a60|||1 min~a90|||90 s~a120|||2 min~a180|||3 min~a300|||5 min~a600|||10 min~mcheck|||Mouse check~auto|||Auto~inside|||Inside~outside|||Outside~on|||On~here|||Clear here~all|||Clear all~pause|||Pause~end|||End~ignore|||Ignore~seat|🪑||Seated view~high|||Higher~low|||Lower~r50|||50 m~r100|||100 m~r150|||150 m~r200|||200 m~relearn|||Re-learn~yes|||Yes, reset~release|🔓|↺|Release~share|👁|◉|Share~us|👥|◎|Us~everyone|👥|◎|Everyone near~onlyfr|💞|♡|Only friends~flist|💞|♡|Friends list~timing|⏳|◷|Timing~camcfg|🎥|⌖|Camera~sk0|||Plain~sk1|||Symbols~sk2|||Color~full|🎬|›|More cameras~crop|◰|◰|Frame~free|✋|✥|Freehand~readme|📖|▤|Read Me~tips|💡|ⓘ|Tips~stline|🏷|≣|Status line~";
list PACE_IDS  = ["lively", "easy", "calm", "slow", "still"];
list PACE_SECS = [30, 45, 60, 90, 120];

key     gOwner;
integer gChan;
integer gListen;
integer gMenuT;
integer gVerAsked;
integer gSkin;                  // menu style: 0 Plain (words), 1 Symbols (quiet marks), 2 Color (emoji)
list    gBtn;                   // the ids of the buttons on screen
list    gLbl;                   // ... and their labels, as shown
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
    if (k == "skin") gSkin = (integer)v;
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
    llOwnerSay("[Take 12] Tap: menu. Double-tap: scenery, or the next view. Hold: share your view. Commands: /" + cfgGet("cmd_chan") + " help");
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
    if (v < 7)                                     // 5.7.0: menus with quiet symbols by default, and the tips on
    {
        if (cfgGet("skin") == "0") cfgWrite("skin", "1");
        cfgWrite("tips", "1");
        cfgWrite("tipn", "0");
        cfgWrite("cfgv", "7");
    }
    gNote = (cfgGet("trace") == "1");
    gSkin = (integer)cfgGet("skin");
    gLook = (integer)cfgGet("look");
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

// buttons a build does not show: the full Take 12 has no "More cameras"; Take 12 Scenery only the scenery camera
integer locked(string id)
{
    if (!LITE) return (id == "full");
    return (llListFindList(["personal", "us", "frame", "free", "share", "favs", "save", "seat", "chat", "modes", "release"], [id]) >= 0);
}

string label(string id)
{
    integer i = llSubStringIndex(ITEMS, "~" + id + "|");
    if (i < 0) return id;
    i += 2 + llStringLength(id);
    string r = llGetSubString(ITEMS, i, i + 40);                // one entry is shorter than this
    r = llGetSubString(r, 0, llSubStringIndex(r, "~") - 1);
    list p = llParseStringKeepNulls(r, ["|"], []);
    string t = llList2String(p, 2);
    string m = llList2String(p, (gSkin == 1));                  // Color: the emoji; Symbols: the quiet mark
    if (gSkin == 0 || m == "") return t;
    return m + " " + t;
}

// Take 12 Scenery's More cameras: tell about the full version and open its listing
upsell()
{
    llOwnerSay("[Take 12 Scenery] Me, Us, Still and sharing are in the full Take 12.");
    llLoadURL(gOwner, "Get the full Take 12", BUY_URL);
}

string idOf(string msg)
{
    integer i = llListFindList(gLbl, [msg]);
    if (i >= 0) return llList2String(gBtn, i);
    return msg;
}

// llDialog fills from the bottom-left: give it the rows bottom-first, padded to full rows
list order(list ids)
{
    list b = [];
    integer i;
    for (i = 0; i < llGetListLength(ids); i++) if (!locked(llList2String(ids, i))) b += [llList2String(ids, i)];
    ids = b;
    b = [];
    gBtn = ids;
    integer n = llGetListLength(ids);
    for (i = 0; i < n; i++) b += label(llList2String(ids, i));
    gLbl = b;
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

// the modes by the names on the menu
string modeName()
{
    integer i = llListFindList(["scenery", "personal", "social", "friends", "frame", "free"], [gUiMode]);
    return llList2String(["Scenery", "Me", "Us", "Us (friends)", "Still", "Freehand"], i);
}

// where Back goes
string up(string p)
{
    if (llSubStringIndex("~pace~afk~", "~" + p + "~") >= 0) return "timing";
    if (llSubStringIndex("~seat~indoors~reach~altcam~chat~", "~" + p + "~") >= 0) return "camcfg";
    if (llSubStringIndex("~timing~camcfg~look~favs~reset~", "~" + p + "~") >= 0) return "opts";
    return "main";
}

string title()
{
    string h = "Take 12";
    if (gSkin == 2) h = "🎬 " + h;
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
        text += "Scenery · the place, while you are away\nMe · follows you\nUs · you and the people around you\nStill · a held picture of you\nFreehand · you frame it, it holds the shot\nFrame · the picture format on your screen";
        b = ["scenery", "personal", "us", "frame", "free", "crop", "share", "opts", "full", "help", "close"];
    }
    else if (page == "us")
    {
        text += "Us · you and the people around you.\nEveryone near, or only the friends you saved.";
        b = ["everyone", "onlyfr", "flist", "back"];
    }
    else if (page == "live")
    {
        if (gUiState == "frozen") b = ["resume"];
        else b = ["photo"];
        if (gUiMode == "scenery" || gUiMode == "free") b += ["save"];
        if (gUiMode == "friends") b += ["release"];
        b += ["next", "stop", "share", "modes", "close"];
        if (gNextCut > llGetUnixTime() && gUiState == "rolling") text += "next cut in " + (string)(gNextCut - llGetUnixTime()) + " s";
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
        text += "Timing · how long views last, when the idle camera starts\nCamera · seated view, indoors, reach, Alt-cam, chat cuts\nLook · menu style, button, chat text";
        b = ["timing", "camcfg", "look", "favs", "test", "reset", "back"];
    }
    else if (page == "help")
    {
        text += "Read Me · the whole guide, as a notecard\nTips · short hints above the button, now " + onoff("tips");
        b = ["readme", "tips", "back"];
    }
    else if (page == "timing")
    {
        text += "Pace: " + paceName() + " (about " + cfgGet("hold") + " s per view)\nIdle start: " + afkText();
        b = ["pace", "afk", "back"];
    }
    else if (page == "camcfg")
    {
        text += "Seated view: " + seatText() + " · Indoors: " + cfgGet("indoors") + "\nReach: " + cfgGet("reach") + " m · Alt-cam: "
            + llList2String(["ignored", "pauses", "ignored", "ends"], (integer)cfgGet("peek") + 2 * (integer)cfgGet("peek_bail"))
            + "\nChat cuts: " + onoff("chat_cuts") + " · Phantom: " + onoff("phantom");
        b = ["seat", "indoors", "reach", "altcam", "chat", "phantom", "back"];
    }
    else if (page == "seat")
    {
        text += "Sitting or lying down: look down on you and your friends from above.\nNow: " + seatText();
        b = ["auto", "high", "low", "off", "back"];
    }
    else if (page == "look")
    {
        text += "Menu style: " + llList2String(["Plain", "Symbols", "Color"], gSkin) + " · Button: " + llList2String(["Classic", "Rec", "Viewfinder"], gLook)
            + "\nStatus line (the mode above the button): " + onoff("status") + " · Chat text: " + onoff("trace");
        b = ["sk0", "sk1", "sk2", "th0", "th1", "th2", "stline", "trace", "back"];
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
        text = "Welcome to Take 12\nTap: menu\nDouble-tap: scenery, or the next view\nHold: share your view\nAny movement key: your camera back";
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
    if (id == "full") { closeMenu(); upsell(); return; }
    if (id == "back")
    {
        openMenu(up(gPage));
        return;
    }
    if (gPage == "main")
    {
        if (id == "scenery" || id == "personal" || id == "frame" || id == "free" || id == "share" || id == "crop")
        {
            closeMenu();
            llMessageLinked(LINK_SET, CMD, id, "");
        }
        else openMenu(id);
    }
    else if (gPage == "live")
    {
        closeMenu();
        if (id == "photo" || id == "resume") llMessageLinked(LINK_SET, CMD, "photo", "");
        else if (id == "save") llMessageLinked(LINK_SET, CMD, "fav", "");
        else if (id == "next" || id == "stop" || id == "share") llMessageLinked(LINK_SET, CMD, id, "");
        else if (id == "release") llMessageLinked(LINK_SET, CMD, "auto", "");
        else if (id == "modes") openMenu("main");
    }
    else if (gPage == "us")
    {
        closeMenu();
        if (id == "everyone") llMessageLinked(LINK_SET, CMD, "social", "");
        else if (id == "onlyfr") llMessageLinked(LINK_SET, CMD, "friends", "");
        else if (id == "flist") llMessageLinked(LINK_SET, UI_FRIENDS, "page", "");
    }
    else if (gPage == "help")
    {
        if (id == "readme") { giveHelp(); closeMenu(); return; }
        if (cfgGet("tips") != "1") cfgWrite("tipn", "0");    // back on: every tip from the start
        toggle("tips", "Tips");
        openMenu("help");
    }
    else if (gPage == "timing") openMenu(id);
    else if (gPage == "pace")
    {
        integer i = llListFindList(PACE_IDS, [id]);
        if (i >= 0) cfgSet("hold", llList2String(PACE_SECS, i));
        note("Pace: " + paceName() + " (about " + cfgGet("hold") + " s per view)");
        openMenu("timing");
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
        note("Idle start: " + afkText());
        openMenu("timing");
    }
    else if (gPage == "opts")
    {
        if (id == "test")
        {
            closeMenu();
            llMessageLinked(LINK_SET, CMD, "grab", "");
        }
        else openMenu(id);
    }
    else if (gPage == "camcfg")
    {
        if (id == "phantom")
        {
            toggle("phantom", "Phantom obstacles");
            openMenu("camcfg");
        }
        else openMenu(id);
    }
    else if (gPage == "look")
    {
        if (llGetSubString(id, 0, 1) == "th") cfgSet("look", llGetSubString(id, 2, 2));
        else if (llGetSubString(id, 0, 1) == "sk") cfgSet("skin", llGetSubString(id, 2, 2));
        else if (id == "trace") toggle("trace", "Chat text");
        else if (id == "stline") toggle("status", "Status line");
        openMenu("look");
    }
    else if (gPage == "indoors")
    {
        cfgSet("indoors", id);
        note("Indoors: " + id);
        openMenu(up(gPage));
    }
    else if (gPage == "chat")
    {
        if (id == "on") cfgSet("chat_cuts", "1");
        else cfgSet("chat_cuts", "0");
        note("Chat cuts: " + onoff("chat_cuts"));
        openMenu(up(gPage));
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
        cfgSet("seat_deg", llList2String(["0", "45", "60", "30"], llListFindList(["off", "auto", "high", "low"], [id])));
        note("Seated view: " + seatText());
        openMenu(up(gPage));
    }
    else if (gPage == "altcam")
    {
        if (id == "pause") { cfgSet("peek", "1"); cfgSet("peek_bail", "0"); }
        else if (id == "end") { cfgSet("peek", "1"); cfgSet("peek_bail", "1"); }
        else if (id == "ignore") cfgSet("peek", "0");
        openMenu(up(gPage));
    }
    else if (gPage == "reach")
    {
        if (id == "relearn") setReach(cfgGet("reach_set"));
        else setReach((string)toNum(msg));
        openMenu(up(gPage));
    }
    else if (gPage == "reset")
    {
        if (id == "yes")
        {
            initDefaults(TRUE);
            gSkin = 1;
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
// tap: always a menu. Idle: the main menu; a camera running (or Photo): the live menu. Any movement key stops it
onTap()
{
    openMenu(llList2String(["main", "live"], gUiState != "idle"));
}

onDouble()
{
    if (gUiState == "idle") llMessageLinked(LINK_SET, CMD, "scenery", "");
    else llMessageLinked(LINK_SET, CMD, "next", "");
}

// hold: a shortcut to the Share panel (share.lsl); Share is in both menus too. Its ⋯ More comes back here
onLong()
{
    if (LITE) onTap();                                      // Take 12 Scenery: no sharing
    else llMessageLinked(LINK_SET, CMD, "share", "");
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
        if (llDetectedKey(0) != gOwner || llDetectedLinkNumber(0) > 1) return;   // not the Frame's bars (crop)
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
        if (llDetectedKey(0) != gOwner || llDetectedLinkNumber(0) > 1) return;
        gHeld = FALSE;
        if (gLongDone) { frame(2 * gLook); nextTimer(); return; }
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
        if (num == CMD && (str == "livemenu" || str == "mainmenu")) openMenu(llGetSubString(str, 0, -5));
        else if (num == UI_STATE)
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
        else if (num == CFG_CHANGED)                        // a chat command (picker) may have changed these
        {
            gSkin = (integer)cfgGet("skin");
            gNote = (cfgGet("trace") == "1");
            gFace = (integer)cfgGet("face");
            gLook = (integer)cfgGet("look");
            frame(2 * gLook);
        }
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/ui] v" + VERSION + " idle start " + afkText() + ", pace " + paceName() + " (" + cfgGet("hold") + " s), reach "
                + cfgGet("reach") + " m, free mem " + (string)llGetFreeMemory());
        else if (num == MSG_VER && str != "?" && str != VERSION)
            llOwnerSay("[Take 12] WARNING: " + (string)id + " script is version " + str + ", ui is " + VERSION + ". Re-drop all Take 12 scripts from the same release.");
    }

    listen(integer channel, string name, key id, string msg)
    {
        if (id != gOwner) return;
        gMenuT = llGetUnixTime();
        onChoice(msg);
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
            frame(2 * gLook + 1);                           // the clapper claps: the hold has taken, let go
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
