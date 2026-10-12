// ============================================================================
//  Cinema HUD  -  cinema_ui.lsl  (v4)
//  Touch decoding (tap / double-tap / long press), emoji dialog menus, /77 chat
//  commands, settings in protected Linkset Data, the button look (clap + fade),
//  first-run welcome, owner-change reset.
//  Lives in the ROOT prim with cinema_core, cinema_scenery, cinema_people and
//  cinema_friends.
// ============================================================================

string VERSION  = "4.0.1";
string PASS     = "cinema-1.0-build1";      // same in all scripts; change per build
string NOTECARD = "Cinema HUD - Read Me";

integer UI_STATE    = 7320;
integer UI_MENU     = 7321;
integer UI_FRIENDS  = 7322;
integer CFG_CHANGED = 7330;
integer MSG_VER     = 7360;
integer STATUS      = 7370;
integer CMD         = 7371;

float TAP_GAP   = 0.35;     // s  second tap within this = double-tap
float LONG_HOLD = 0.8;      // s  hold this long = long press
float gFadeA    = 0.4;      // button opacity while the camera rolls (Options > Fade)

list DEFAULTS = [
    "afk_on", "1",
    "afk_sec", "90",
    "hold", "60",
    "reach", "100",
    "reach_ok", "0",
    "indoors", "auto",
    "chat_cuts", "1",
    "emoji", "1",
    "fade", "40",
    "peek", "1",
    "peek_bail", "0",
    "phantom", "0",
    "cutmode", "0",
    "trace", "1",
    "cmd_chan", "77",
    "theta_max", "10",
    "aspect", "1.778"
];

// menu items: id, emoji, title
list ITEMS = [
    "scenery", "🏞", "Scenery", "personal", "🚶", "Personal", "social", "👥", "Social", "friends", "💞", "Friends",
    "pace", "⏳", "Pace", "afk", "💤", "AFK", "opts", "⚙", "Options", "help", "❔", "Help",
    "close", "✖", "Close", "back", "↩", "Back", "photo", "📷", "Photo", "resume", "▶", "Resume",
    "save", "⭐", "Save", "next", "⏭", "Next", "stop", "⏹", "Stop", "modes", "🎬", "Modes",
    "lively", "⚡", "Lively", "easy", "🙂", "Easy", "calm", "🍃", "Calm", "slow", "🌙", "Slow", "still", "🗿", "Still",
    "indoors", "🏠", "Indoors", "chat", "💬", "Chat cuts", "favs", "⭐", "Favourites", "altcam", "👁", "Alt-cam",
    "phantom", "🧱", "Phantom", "reach", "📏", "Reach", "trace", "📝", "Trace", "emoji", "🔤", "Emoji",
    "fade", "🔆", "Fade", "test", "🧪", "Test cam", "reset", "♻", "Reset", "gotit", "👍", "Got it",
    "off", "", "Off", "a60", "", "1 min", "a90", "", "90 s", "a120", "", "2 min", "a300", "", "5 min", "a600", "", "10 min",
    "away", "", "SL Away", "auto", "", "Auto", "inside", "", "Inside", "outside", "", "Outside", "on", "", "On",
    "here", "", "Clear here", "all", "", "Clear all", "pause", "", "Pause", "end", "", "End", "ignore", "", "Ignore",
    "r25", "", "25 m", "r50", "", "50 m", "r75", "", "75 m", "r100", "", "100 m", "relearn", "", "Re-learn", "yes", "", "Yes, reset"
];
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
integer gFirst;
string  gPage;

// touch decoder
float   gDown;
float   gTapT;
float   gClapT;
integer gHeld;
integer gLongDone;
integer gTapN;
integer gDbl;
// what the camera is doing
string  gUiState = "idle";    // idle / rolling / frozen
string  gUiMode  = "scenery";
integer gNextCut;
integer gShownIdle = TRUE;

// ============================================================================
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
    if (k == "fade") gFadeA = (float)v / 100.0;
}

initDefaults(integer force)
{
    integer i;
    integer n = llGetListLength(DEFAULTS);
    for (i = 0; i < n; i += 2)
    {
        string k = llList2String(DEFAULTS, i);
        if (force || cfgGet(k) == "") cfgWrite(k, llList2String(DEFAULTS, i + 1));
    }
    cfgWrite("ver", VERSION);
    cfgWrite("owner", (string)gOwner);
}

giveHelp()
{
    if (llGetInventoryType(NOTECARD) == INVENTORY_NOTECARD) llGiveInventory(gOwner, NOTECARD);
    else llOwnerSay("[Cinema] The Read Me notecard is not in this HUD.");
    llOwnerSay("[Cinema] Double-tap: scenery camera. Tap: menu (while rolling: stop). Long press: live menu (photo, save, next). Commands: /" + (string)gCmdChan + " help");
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
    gEmoji = (cfgGet("emoji") != "0");
    gFadeA = (float)cfgGet("fade") / 100.0;
    if (gFadeA < 0.1) gFadeA = 0.4;
    gFirst = (cfgGet("seen_intro") != "1");
    llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
}

// ============================================================================
//  the button: no colours. Idle = solid; while the camera rolls it claps once, then fades.
// ============================================================================
nextTimer()
{
    if (gHeld || gTapN || gClapT > 0.0) llSetTimerEvent(0.1);
    else if (gListen) llSetTimerEvent(5.0);
    else if (!gVerAsked) llSetTimerEvent(3.0);
    else llSetTimerEvent(0.0);
}

setLook(string st)
{
    integer idle = (st == "off" || st == "armed");
    float a = 1.0;
    if (!idle) a = gFadeA;
    if (!idle && gShownIdle)
    {
        llOffsetTexture(0.25, 0.0, ALL_SIDES);      // frame 2: clapped
        gClapT = llGetTime() + 0.3;
        a = 1.0;
    }
    gShownIdle = idle;
    llSetLinkPrimitiveParamsFast(LINK_THIS, [PRIM_COLOR, ALL_SIDES, <1.0, 1.0, 1.0>, a]);
    nextTimer();
}

endClap()
{
    gClapT = 0.0;
    llOffsetTexture(-0.25, 0.0, ALL_SIDES);        // frame 1: open
    if (!gShownIdle) llSetLinkPrimitiveParamsFast(LINK_THIS, [PRIM_COLOR, ALL_SIDES, <1.0, 1.0, 1.0>, gFadeA]);
}

// ============================================================================
//  menu
// ============================================================================
string label(string id)
{
    integer i = llListFindList(ITEMS, [id]);
    if (i < 0) return id;
    string t = llList2String(ITEMS, i + 2);
    string e = llList2String(ITEMS, i + 1);
    if (e == "" || !gEmoji) return t;
    return e + " " + t;
}

string idOf(string msg)
{
    integer i;
    integer n = llGetListLength(ITEMS);
    for (i = 0; i < n; i += 3)
    {
        string id = llList2String(ITEMS, i);
        if (label(id) == msg) return id;
    }
    return msg;
}

// llDialog fills from the bottom-left: give it the rows bottom-first, padded to full rows
list order(list ids)
{
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
    if (a == "away") return "SL Away";
    return a + " s";
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
    string h = "Cinema";
    if (gEmoji) h = "🎬 Cinema";
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
        b = ["scenery", "personal", "social", "friends", "pace", "afk", "opts", "help", "close"];
    }
    else if (page == "live")
    {
        if (gUiState == "frozen") b = ["resume"];
        else b = ["photo"];
        if (gUiMode == "scenery") b += ["save"];
        b += ["next", "stop", "modes", "close"];
        if (gNextCut > 0 && gUiState == "rolling") text += "next cut in " + (string)(gNextCut - llGetUnixTime()) + " s";
    }
    else if (page == "pace")
    {
        text += "How long each scenery view is held.\nNow: " + paceName() + ", about " + cfgGet("hold") + " s\nLively 30 · Easy 45 · Calm 60 · Slow 90 · Still 120";
        b = ["lively", "easy", "calm", "slow", "still", "back"];
    }
    else if (page == "afk")
    {
        text += "Start the scenery camera when you are idle.\nNow: " + afkText();
        b = ["off", "a60", "a90", "a120", "a300", "a600", "away", "back"];
    }
    else if (page == "opts")
    {
        text += "Indoors: " + cfgGet("indoors") + " · Chat cuts: " + onoff("chat_cuts") + "\nAlt-cam: "
            + llList2String(["ignored", "pauses", "ignored", "ends"], (integer)cfgGet("peek") + 2 * (integer)cfgGet("peek_bail"))
            + " · Reach: " + cfgGet("reach") + " m\nPhantom: " + onoff("phantom") + " · Trace: " + onoff("trace") + " · Emoji: " + onoff("emoji") + " · Button fade: " + cfgGet("fade") + " %";
        b = ["indoors", "chat", "favs", "altcam", "phantom", "reach", "trace", "emoji", "fade", "test", "reset", "back"];
    }
    else if (page == "indoors")
    {
        text += "When you are inside a room, scenery can stay in the room or look from outside.\nNow: " + cfgGet("indoors") + " (auto = inside in the sky, outside on the ground)";
        b = ["auto", "inside", "outside", "back"];
    }
    else if (page == "chat")
    {
        text += "Social and Friends cut to whoever speaks in local chat.\nNow: " + onoff("chat_cuts");
        b = ["on", "off", "back"];
    }
    else if (page == "favs")
    {
        text += "Saved scenery spots of this region (Save is in the live menu).";
        b = ["here", "all", "back"];
    }
    else if (page == "altcam")
    {
        text += "When you Alt-orbit the camera while it rolls:";
        b = ["pause", "end", "ignore", "back"];
    }
    else if (page == "reach")
    {
        text += "Furthest scenery camera distance (now " + cfgGet("reach") + " m). The HUD lowers it by itself if your viewer refuses far cameras.";
        b = ["r25", "r50", "r75", "r100", "relearn", "back"];
    }
    else if (page == "reset")
    {
        text += "Reset ALL settings to defaults?";
        b = ["yes", "back"];
    }
    else
    {
        text = "Welcome to Cinema\nDouble-tap: scenery camera\nTap: menu (while rolling: stop)\nHold: live menu\nIdle for a while and it starts by itself.";
        b = ["gotit", "help"];
    }
    llDialog(gOwner, text, order(b), gChan);
}

toggle(string k, string name)
{
    string v = "1";
    if (cfgGet(k) == "1") v = "0";
    cfgSet(k, v);
    llOwnerSay("[Cinema] " + name + ": " + onoff(k));
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
    if (id == "back")
    {
        if (gPage == "altcam" || gPage == "reach" || gPage == "reset" || gPage == "indoors" || gPage == "chat" || gPage == "favs") openMenu("opts");
        else openMenu("main");
        return;
    }
    if (gPage == "main")
    {
        if (id == "scenery" || id == "personal" || id == "social")
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
        else if (id == "modes") openMenu("main");
    }
    else if (gPage == "pace")
    {
        integer i = llListFindList(PACE_IDS, [id]);
        if (i >= 0) cfgSet("hold", llList2String(PACE_SECS, i));
        llOwnerSay("[Cinema] Pace: " + paceName() + " (about " + cfgGet("hold") + " s per view)");
        openMenu("main");
    }
    else if (gPage == "afk")
    {
        if (id == "off") cfgSet("afk_on", "0");
        else
        {
            string sec = (string)toNum(msg);
            if (id == "away") sec = "away";
            cfgSet("afk_sec", sec);
            cfgSet("afk_on", "1");
        }
        llOwnerSay("[Cinema] AFK scenery: " + afkText());
        openMenu("main");
    }
    else if (gPage == "opts")
    {
        if (id == "indoors" || id == "chat" || id == "favs" || id == "altcam" || id == "reach" || id == "reset") openMenu(id);
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
            else if (id == "fade")
            {
                string nf = "40";                           // cycle 20 -> 40 -> 70 %
                if (cfgGet("fade") == "40") nf = "70";
                else if (cfgGet("fade") == "70") nf = "20";
                cfgSet("fade", nf);
                llOwnerSay("[Cinema] Button fade while rolling: " + nf + " % visible");
                if (gUiState != "idle") setLook("rolling");
            }
            openMenu("opts");
        }
    }
    else if (gPage == "indoors")
    {
        cfgSet("indoors", id);
        llOwnerSay("[Cinema] Indoors: " + id);
        openMenu("opts");
    }
    else if (gPage == "chat")
    {
        if (id == "on") cfgSet("chat_cuts", "1");
        else cfgSet("chat_cuts", "0");
        llOwnerSay("[Cinema] Chat cuts: " + onoff("chat_cuts"));
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
        llOwnerSay("[Cinema] Favourite spots cleared.");
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
        if (id == "relearn") { cfgSet("reach", "100"); cfgSet("reach_ok", "0"); }
        else cfgSet("reach", (string)toNum(msg));
        openMenu("opts");
    }
    else if (gPage == "reset")
    {
        if (id == "yes")
        {
            initDefaults(TRUE);
            gEmoji = TRUE;
            llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
            llOwnerSay("[Cinema] Settings reset to defaults.");
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
    llOwnerSay("[Cinema] commands: /" + (string)gCmdChan + " scenery | personal | social | friends | stop | next | photo | fav | menu | status | pace <s> | reach <m>|relearn | indoors auto|inside|outside | friend list|clear | trace on|off | emoji on|off | cutmode on|off | chan <n> | grab | reset");
}

onCommand(string msg)
{
    list a = llParseString2List(llToLower(llStringTrim(msg, STRING_TRIM)), [" "], []);
    string c = llList2String(a, 0);
    string v = llList2String(a, 1);
    integer n = (integer)v;
    if (c == "scenery" || c == "personal" || c == "social" || c == "friends" || c == "stop" || c == "next" || c == "photo" || c == "fav" || c == "grab") llMessageLinked(LINK_SET, CMD, c, "");
    else if (c == "menu") openMenu("main");
    else if (c == "status")
    {
        llOwnerSay("[Cinema/ui] v" + VERSION + " commands on /" + (string)gCmdChan + ", AFK scenery " + afkText()
            + ", pace " + paceName() + " (" + cfgGet("hold") + " s), reach " + cfgGet("reach") + " m, free mem " + (string)llGetFreeMemory());
        llMessageLinked(LINK_SET, STATUS, "?", "");
    }
    else if ((c == "pace" || c == "hold") && n >= 10 && n <= 600) { cfgSet("hold", (string)n); llOwnerSay("[Cinema] Pace: about " + v + " s per view"); }
    else if (c == "reach" && v == "relearn") { cfgSet("reach", "100"); cfgSet("reach_ok", "0"); llOwnerSay("[Cinema] Reach reset to 100 m"); }
    else if (c == "reach" && n >= 20 && n <= 250) { cfgSet("reach", (string)n); llOwnerSay("[Cinema] Scenery reach: " + v + " m"); }
    else if (c == "indoors" && (v == "auto" || v == "inside" || v == "outside")) { cfgSet("indoors", v); llOwnerSay("[Cinema] Indoors: " + v); }
    else if (c == "friend" && (v == "list" || v == "clear")) llMessageLinked(LINK_SET, UI_FRIENDS, v, "");
    else if (c == "trace" || c == "emoji" || c == "cutmode")
    {
        cfgSet(c, (string)(v == "on"));
        llOwnerSay("[Cinema] " + c + ": " + onoff(c));
    }
    else if (c == "chan" && n > 0 && n != 9)
    {
        cfgSet("cmd_chan", (string)n);
        gCmdChan = n;
        if (gCmdListen) llListenRemove(gCmdListen);
        gCmdListen = llListen(gCmdChan, "", gOwner, "");
        llOwnerSay("[Cinema] Commands now on /" + v);
    }
    else if (c == "reset")
    {
        initDefaults(TRUE);
        gEmoji = TRUE;
        llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
        llOwnerSay("[Cinema] Settings reset to defaults.");
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
        llScaleTexture(0.5, 1.0, ALL_SIDES);
        llOffsetTexture(-0.25, 0.0, ALL_SIDES);
        setLook("armed");
        gCmdChan = (integer)cfgGet("cmd_chan");
        if (gCmdChan <= 0) gCmdChan = 77;
        gCmdListen = llListen(gCmdChan, "", gOwner, "");
        llOwnerSay("[Cinema] ui v" + VERSION + " ready, commands on /" + (string)gCmdChan + ", free memory " + (string)llGetFreeMemory());
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
            llOwnerSay("[Cinema] WARNING: " + (string)id + " script is version " + str + ", ui is " + VERSION + ". Re-drop all Cinema scripts from the same release.");
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
        if (gClapT > 0.0 && now >= gClapT) endClap();
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
