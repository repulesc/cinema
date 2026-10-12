// ============================================================================
//  Cinema HUD  -  cinema_ui.lsl  (v3)
//  Long-press menu, /77 chat commands, settings in protected Linkset Data,
//  button colour, first-run welcome + notecard, owner-change reset.
//  Lives in the ROOT prim with cinema_core, cinema_scenery and cinema_people.
// ============================================================================

string VERSION  = "3.0.0";
string PASS     = "cinema-1.0-build1";      // same in all scripts; change per build
string NOTECARD = "Cinema HUD - Read Me";

integer UI_STATE    = 7320;
integer UI_MENU     = 7321;
integer CFG_CHANGED = 7330;
integer MSG_VER     = 7360;
integer STATUS      = 7370;
integer CMD         = 7371;

list DEFAULTS = [
    "afk_on", "1",
    "afk_sec", "90",
    "hold", "60",
    "reach", "100",
    "peek", "1",
    "peek_bail", "0",
    "phantom", "0",
    "cutmode", "0",
    "trace", "1",
    "cmd_chan", "77",
    "theta_max", "10",
    "aspect", "1.778"
];

key     gOwner;
integer gChan;
integer gListen;
integer gMenuT;
integer gCmdListen;
integer gCmdChan;
integer gVerAsked;
string  gPage;

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
}

// new owner (or first run): wipe whatever was configured before
checkOwner()
{
    if (cfgGet("owner") != (string)gOwner)
    {
        llLinksetDataReset();
        initDefaults(TRUE);
        llOwnerSay("[Cinema] Welcome! Tap the button for the scenery camera, tap again to stop. Hold it 1 s for the menu (Personal and Social cameras are there). It also starts by itself when you are idle. Any movement key brings your camera back.");
        giveHelp();
    }
    else initDefaults(FALSE);
    llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
}

setLook(string st)
{
    vector c = <0.9, 0.9, 0.9>;
    float g = 0.0;
    if (st == "off") c = <0.3, 0.3, 0.3>;
    else if (st == "rolling") { c = <1.0, 0.1, 0.1>; g = 0.15; }
    else if (st == "peek") { c = <1.0, 0.7, 0.1>; g = 0.1; }
    llSetLinkPrimitiveParamsFast(LINK_THIS, [PRIM_COLOR, ALL_SIDES, c, 1.0, PRIM_GLOW, ALL_SIDES, g, PRIM_FULLBRIGHT, ALL_SIDES, TRUE]);
}

string onoff(string k)
{
    if (cfgGet(k) == "1") return "ON";
    return "off";
}

string afkText()
{
    if (cfgGet("afk_on") != "1") return "off";
    string a = cfgGet("afk_sec");
    if (a == "away") return "when SL says Away";
    return "after " + a + " s";
}

// ============================================================================
//  menu
// ============================================================================
closeMenu()
{
    if (gListen) llListenRemove(gListen);
    gListen = 0;
}

openMenu(string page)
{
    closeMenu();
    gPage = page;
    gChan = -(integer)(llFrand(1000000000.0) + 1000.0);
    gListen = llListen(gChan, "", gOwner, "");
    gMenuT = llGetUnixTime();
    llSetTimerEvent(5.0);
    string head = "Cinema HUD v" + VERSION + "\n";
    string text;
    list b;
    if (page == "main")
    {
        text = "Scenery = grand views of the place (default, also starts when you are AFK " + afkText() + ").\nPersonal = shots of you, follows you.\nSocial = you and the people around you.";
        b = ["Scenery", "Personal", "Social", "Stop", "AFK", "Hold", "Options", "Help", "Close"];
    }
    else if (page == "afk")
    {
        text = "Start the scenery camera when idle (now: " + afkText() + ")";
        b = ["Off", "60 s", "90 s", "2 min", "5 min", "10 min", "SL Away", "< Back"];
    }
    else if (page == "hold")
    {
        text = "How long each scenery view is held (now: about " + cfgGet("hold") + " s)";
        b = ["30 s", "45 s", "60 s", "90 s", "2 min", "< Back"];
    }
    else if (page == "opts")
    {
        text = "Phantom obstacles: " + onoff("phantom") + "\nAlt-cam: " + llList2String(["ignored", "pauses", "ignored", "ends"], (integer)cfgGet("peek") + 2 * (integer)cfgGet("peek_bail"))
            + "\nCut mode clear-first: " + onoff("cutmode") + "\nTrace lines: " + onoff("trace") + "\nScenery reach: " + cfgGet("reach") + " m";
        b = ["Phantom", "Alt-cam", "Cut mode", "Trace", "Reach", "Test camera", "Reset", "< Back"];
    }
    else if (page == "altcam")
    {
        text = "When you Alt-orbit the camera while the cinema runs:";
        b = ["Pause", "End", "Ignore", "< Back"];
    }
    else if (page == "reach")
    {
        text = "Furthest scenery camera distance (now " + cfgGet("reach") + " m). The HUD lowers it by itself if your viewer refuses far cameras.";
        b = ["25 m", "50 m", "75 m", "100 m", "< Back"];
    }
    else if (page == "reset")
    {
        text = "Reset ALL settings to defaults?";
        b = ["Yes, reset", "< Back"];
    }
    llDialog(gOwner, head + text, b, gChan);
}

toggle(string k, string label)
{
    string v = "1";
    if (cfgGet(k) == "1") v = "0";
    cfgSet(k, v);
    llOwnerSay("[Cinema] " + label + ": " + onoff(k));
}

// "2 min" -> 120, "45 s" -> 45, "75 m" -> 75
integer toNum(string msg)
{
    integer n = (integer)msg;
    if (llSubStringIndex(msg, "min") >= 0) n = n * 60;
    return n;
}

onChoice(string msg)
{
    if (msg == "Close") { closeMenu(); return; }
    if (msg == "< Back")
    {
        if (gPage == "altcam" || gPage == "reach" || gPage == "reset") openMenu("opts");
        else openMenu("main");
        return;
    }
    if (gPage == "main")
    {
        if (msg == "Scenery" || msg == "Personal" || msg == "Social" || msg == "Stop")
        {
            closeMenu();
            llMessageLinked(LINK_SET, CMD, llToLower(msg), "");
        }
        else if (msg == "AFK") openMenu("afk");
        else if (msg == "Hold") openMenu("hold");
        else if (msg == "Options") openMenu("opts");
        else if (msg == "Help") { giveHelp(); closeMenu(); }
    }
    else if (gPage == "afk")
    {
        if (msg == "Off") cfgSet("afk_on", "0");
        else
        {
            string sec = (string)toNum(msg);
            if (msg == "SL Away") sec = "away";
            cfgSet("afk_sec", sec);
            cfgSet("afk_on", "1");
        }
        llOwnerSay("[Cinema] AFK scenery: " + afkText());
        openMenu("main");
    }
    else if (gPage == "hold")
    {
        cfgSet("hold", (string)toNum(msg));
        llOwnerSay("[Cinema] Scenery hold: about " + cfgGet("hold") + " s");
        openMenu("main");
    }
    else if (gPage == "opts")
    {
        if (msg == "Alt-cam") openMenu("altcam");
        else if (msg == "Reach") openMenu("reach");
        else if (msg == "Reset") openMenu("reset");
        else if (msg == "Test camera")
        {
            closeMenu();
            llMessageLinked(LINK_SET, CMD, "grab", "");
        }
        else
        {
            if (msg == "Phantom") toggle("phantom", "Phantom obstacles");
            else if (msg == "Cut mode") toggle("cutmode", "Cut mode clear-first");
            else if (msg == "Trace") toggle("trace", "Trace lines");
            openMenu("opts");
        }
    }
    else if (gPage == "altcam")
    {
        if (msg == "Pause") { cfgSet("peek", "1"); cfgSet("peek_bail", "0"); }
        else if (msg == "End") { cfgSet("peek", "1"); cfgSet("peek_bail", "1"); }
        else if (msg == "Ignore") cfgSet("peek", "0");
        openMenu("opts");
    }
    else if (gPage == "reach")
    {
        cfgSet("reach", (string)toNum(msg));
        openMenu("opts");
    }
    else if (gPage == "reset")
    {
        if (msg == "Yes, reset")
        {
            initDefaults(TRUE);
            llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
            llOwnerSay("[Cinema] Settings reset to defaults.");
        }
        openMenu("opts");
    }
}

// ============================================================================
//  chat commands: /77 <command>
// ============================================================================
help()
{
    llOwnerSay("[Cinema] commands: /" + (string)gCmdChan + " scenery | personal | social | stop | menu | grab | status | hold <s> | reach <m> | trace on|off | chan <n> | reset");
}

onCommand(string msg)
{
    list a = llParseString2List(llToLower(llStringTrim(msg, STRING_TRIM)), [" "], []);
    string c = llList2String(a, 0);
    string v = llList2String(a, 1);
    integer n = (integer)v;
    if (c == "scenery" || c == "personal" || c == "social" || c == "stop" || c == "grab") llMessageLinked(LINK_SET, CMD, c, "");
    else if (c == "menu") openMenu("main");
    else if (c == "status")
    {
        llOwnerSay("[Cinema/ui] v" + VERSION + " commands on /" + (string)gCmdChan + ", AFK scenery " + afkText()
            + ", hold " + cfgGet("hold") + " s, reach " + cfgGet("reach") + " m, free mem " + (string)llGetFreeMemory());
        llMessageLinked(LINK_SET, STATUS, "?", "");
    }
    else if (c == "hold" && n >= 10 && n <= 600) { cfgSet("hold", (string)n); llOwnerSay("[Cinema] Scenery hold: about " + v + " s"); }
    else if (c == "reach" && n >= 20 && n <= 250) { cfgSet("reach", (string)n); llOwnerSay("[Cinema] Scenery reach: " + v + " m"); }
    else if (c == "trace")
    {
        cfgSet("trace", (string)(v == "on"));
        llOwnerSay("[Cinema] Trace lines: " + onoff("trace"));
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
        setLook("armed");
        gCmdChan = (integer)cfgGet("cmd_chan");
        if (gCmdChan <= 0) gCmdChan = 77;
        gCmdListen = llListen(gCmdChan, "", gOwner, "");
        llOwnerSay("[Cinema] ui v" + VERSION + " ready, commands on /" + (string)gCmdChan + ", free memory " + (string)llGetFreeMemory());
        llSetTimerEvent(3.0);
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
        if (num == UI_STATE) setLook(str);
        else if (num == UI_MENU) openMenu("main");
        else if (num == MSG_VER && str != "?" && str != VERSION)
            llOwnerSay("[Cinema] WARNING: " + (string)id + " script is version " + str + ", ui is " + VERSION + ". Re-drop all four scripts from the same release.");
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
        if (!gVerAsked)
        {
            gVerAsked = TRUE;
            llMessageLinked(LINK_SET, MSG_VER, "?", "ui");
        }
        if (gListen && llGetUnixTime() - gMenuT > 60) closeMenu();
        if (!gListen) llSetTimerEvent(0.0);
    }
}
