// ============================================================================
//  Cinema HUD  -  cinema_ui.lsl
//  Settings in Linkset Data (protected), long-press dialog menu, button look,
//  first-run welcome + notecard, owner-change reset, version check, probes.
//
//  Lives in the ROOT prim with cinema_core and cinema_director.
//  Design: docs/ARCHITECTURE.md  (6.3 settings, 6.4 UI)
// ============================================================================

string VERSION  = "1.0.2";
string PASS     = "cinema-1.0-build1";      // same in all 3 scripts; change per build
string NOTECARD = "Cinema HUD - Read Me";   // give this notecard together with the HUD

// ---- link message numbers (section 6.2) ------------------------------------
integer UI_STATE    = 7320;
integer UI_MENU     = 7321;
integer CFG_CHANGED = 7330;
integer PROBE       = 7350;
integer MSG_VER     = 7360;
integer STATUS      = 7370;
integer CMD         = 7371;

// ---- defaults (section 6.3) ---------------------------------------------------
list DEFAULTS = [
    "afk_on", "1",
    "afk_sec", "90",
    "style", "blend",
    "hold_mul", "1.0",
    "cool_min", "10",
    "speaker", "0",
    "phantom", "0",
    "man_vista_end", "0",
    "peek", "1",
    "peek_bail", "0",
    "theta_max", "10",
    "fovaxis", "v",
    "aspect", "1.778",
    "maxcam", "45",
    "cutmode", "0",
    "debug", "1",
    "trace", "1",
    "far_ok", "0",
    "overlay", "0"
];

key     gOwner;
integer gChan;
integer gListen;
integer gMenuT;
integer gVerAsked;
integer gCmdListen;
string  gPage;

// ============================================================================
//  settings
// ============================================================================
string cfgGet(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

cfgWrite(string k, string v)
{
    llLinksetDataWriteProtected("cin." + k, v, PASS);
}

// write + tell the other scripts
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
    else llOwnerSay("[Cinema] The Read Me notecard is not in this HUD. See the user guide in the product listing.");
}

welcome()
{
    llOwnerSay("[Cinema] Welcome! Tap the button to start / stop the cinema camera. Hold it for 1 second for the menu."
        + " It also starts by itself after " + cfgGet("afk_sec") + " s without activity. Any movement key brings your camera back.");
    giveHelp();
}

// new owner => wipe whatever the previous owner configured
checkOwner()
{
    string o = cfgGet("owner");
    if (o != (string)gOwner)
    {
        llLinksetDataReset();
        initDefaults(TRUE);
        welcome();
    }
    else
    {
        initDefaults(FALSE);        // keeps user settings, adds new keys after an update
    }
    llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
}

// ============================================================================
//  button look
// ============================================================================
setLook(string st)
{
    vector c = <0.9, 0.9, 0.9>;
    float g = 0.0;
    if (st == "off") c = <0.3, 0.3, 0.3>;
    else if (st == "armed") c = <0.9, 0.9, 0.9>;
    else if (st == "rolling") { c = <1.0, 0.1, 0.1>; g = 0.15; }
    else if (st == "peek") { c = <1.0, 0.7, 0.1>; g = 0.1; }
    else if (st == "noshot") { c = <0.2, 0.5, 1.0>; g = 0.05; }
    llSetLinkPrimitiveParamsFast(LINK_THIS, [PRIM_COLOR, ALL_SIDES, c, 1.0, PRIM_GLOW, ALL_SIDES, g, PRIM_FULLBRIGHT, ALL_SIDES, TRUE]);
}

// ============================================================================
//  menus
// ============================================================================
string onoff(string k)
{
    if (cfgGet(k) == "1") return "ON";
    return "off";
}

string holdText()
{
    string h = cfgGet("hold_mul");
    if ((float)h == 0.0) return "until an event";
    return "x" + h;
}

string afkText()
{
    if (cfgGet("afk_on") != "1") return "off";
    string a = cfgGet("afk_sec");
    if (a == "away") return "when SL says Away";
    return a + " s";
}

closeMenu()
{
    if (gListen) llListenRemove(gListen);
    gListen = 0;
}

dlg(string text, list btns)
{
    llDialog(gOwner, text, btns, gChan);
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
    if (page == "main")
        dlg(head + "Style: " + cfgGet("style") + "\nAFK start: " + afkText() + "\nHold: " + holdText(),
            ["Style", "AFK", "Holds", "Options", "Help", "About", "Close"]);
    else if (page == "style")
        dlg(head + "Director style (now: " + cfgGet("style") + ")\nBlend mixes all three.",
            ["Blend", "Ozu", "Jarmusch", "Nouvelle V.", "< Back"]);
    else if (page == "afk")
        dlg(head + "Start the cinema after this long without activity (now: " + afkText() + ")",
            ["Off", "60 s", "90 s", "120 s", "3 min", "5 min", "10 min", "SL Away", "< Back"]);
    else if (page == "holds")
        dlg(head + "How long a shot is held (now: " + holdText() + ")",
            ["x0.5", "x1", "x1.5", "x2", "x3", "Until event", "< Back"]);
    else if (page == "opts")
        dlg(head + "Speaker cut: " + cfgGet("speaker") + "  (0 off, 1 typing, 2 typing+chat)"
            + "\nPhantom obstacles: " + onoff("phantom")
            + "\nManual: vista ends on move: " + onoff("man_vista_end")
            + "\nAlt-cam: peek " + cfgGet("peek") + " / ends " + cfgGet("peek_bail")
            + "\nCooldown after: " + cfgGet("cool_min") + " min"
            + "\nCut mode clear-first: " + onoff("cutmode")
            + "\nDebug: " + onoff("debug"),
            ["Speaker", "Phantom", "Man. vista", "Alt-cam", "Cooldown", "Cut mode", "Debug", "Probe", "Reset", "< Back"]);
    else if (page == "speaker")
        dlg(head + "Cut to whoever speaks near you.\nTyping = typing flag only.\nTyping+chat also listens to local chat.",
            ["Off", "Typing", "Typing+chat", "< Back"]);
    else if (page == "altcam")
        dlg(head + "When you Alt-orbit the camera while the cinema runs:\nPeek = pause, resume after ESC\nEnds cinema = stop\nIgnore = do not watch for it",
            ["Peek", "Ends cinema", "Ignore", "< Back"]);
    else if (page == "cool")
        dlg(head + "After this long idle, favour empty sky / sea shots (lighter on the GPU)",
            ["Off", "5 min", "10 min", "20 min", "< Back"]);
    else if (page == "probe")
        dlg(head + "In-world tests. Stop the cinema first. Results are printed in chat; note them in docs/CALIBRATION.md.\nCut = instant cut or glide?\nCamPos = does the viewer report Alt-cam?\nDistance = how far can the camera go?",
            ["Cut", "CamPos", "Distance", "FOV", "< Back"]);
    else if (page == "reset")
        dlg(head + "Reset ALL settings to defaults?", ["Yes, reset", "< Back"]);
}

string parentOf(string page)
{
    if (page == "speaker" || page == "altcam" || page == "cool" || page == "probe" || page == "reset") return "opts";
    return "main";
}

toggle(string k, string label)
{
    string v = "1";
    if (cfgGet(k) == "1") v = "0";
    cfgSet(k, v);
    llOwnerSay("[Cinema] " + label + ": " + onoff(k));
}

about()
{
    llOwnerSay("[Cinema] Cinema HUD v" + VERSION + "  |  ui free memory " + (string)llGetFreeMemory() + " bytes"
        + "  |  style " + cfgGet("style") + ", afk " + afkText() + ", hold " + holdText());
}

onChoice(string msg)
{
    if (msg == "Close") { closeMenu(); return; }
    if (msg == "< Back") { openMenu(parentOf(gPage)); return; }

    if (gPage == "main")
    {
        if (msg == "Style") openMenu("style");
        else if (msg == "AFK") openMenu("afk");
        else if (msg == "Holds") openMenu("holds");
        else if (msg == "Options") openMenu("opts");
        else if (msg == "Help") { giveHelp(); openMenu("main"); }
        else if (msg == "About") { about(); openMenu("main"); }
    }
    else if (gPage == "style")
    {
        string s = "blend";
        if (msg == "Ozu") s = "ozu";
        else if (msg == "Jarmusch") s = "jarmusch";
        else if (msg == "Nouvelle V.") s = "nv";
        cfgSet("style", s);
        llOwnerSay("[Cinema] Style: " + s);
        openMenu("main");
    }
    else if (gPage == "afk")
    {
        if (msg == "Off") cfgSet("afk_on", "0");
        else
        {
            string sec = "90";
            if (msg == "60 s") sec = "60";
            else if (msg == "90 s") sec = "90";
            else if (msg == "120 s") sec = "120";
            else if (msg == "3 min") sec = "180";
            else if (msg == "5 min") sec = "300";
            else if (msg == "10 min") sec = "600";
            else if (msg == "SL Away") sec = "away";
            cfgSet("afk_sec", sec);
            cfgSet("afk_on", "1");
        }
        llOwnerSay("[Cinema] AFK start: " + afkText());
        openMenu("main");
    }
    else if (gPage == "holds")
    {
        string h = "1.0";
        if (msg == "x0.5") h = "0.5";
        else if (msg == "x1.5") h = "1.5";
        else if (msg == "x2") h = "2.0";
        else if (msg == "x3") h = "3.0";
        else if (msg == "Until event") h = "0";
        cfgSet("hold_mul", h);
        llOwnerSay("[Cinema] Hold: " + holdText());
        openMenu("main");
    }
    else if (gPage == "opts")
    {
        if (msg == "Speaker") openMenu("speaker");
        else if (msg == "Alt-cam") openMenu("altcam");
        else if (msg == "Cooldown") openMenu("cool");
        else if (msg == "Probe") openMenu("probe");
        else if (msg == "Reset") openMenu("reset");
        else
        {
            if (msg == "Phantom") toggle("phantom", "Phantom obstacles");
            else if (msg == "Man. vista") toggle("man_vista_end", "Manual: vista ends on move");
            else if (msg == "Cut mode") toggle("cutmode", "Cut mode clear-first");
            else if (msg == "Debug") toggle("debug", "Debug");
            openMenu("opts");
        }
    }
    else if (gPage == "speaker")
    {
        string sp = "0";
        if (msg == "Typing") sp = "1";
        else if (msg == "Typing+chat") sp = "2";
        cfgSet("speaker", sp);
        llOwnerSay("[Cinema] Speaker cut: " + sp);
        openMenu("opts");
    }
    else if (gPage == "altcam")
    {
        if (msg == "Peek") { cfgSet("peek", "1"); cfgSet("peek_bail", "0"); }
        else if (msg == "Ends cinema") { cfgSet("peek", "1"); cfgSet("peek_bail", "1"); }
        else if (msg == "Ignore") cfgSet("peek", "0");
        llOwnerSay("[Cinema] Alt-cam: " + msg);
        openMenu("opts");
    }
    else if (gPage == "cool")
    {
        string c = "10";
        if (msg == "Off") c = "0";
        else if (msg == "5 min") c = "5";
        else if (msg == "20 min") c = "20";
        cfgSet("cool_min", c);
        llOwnerSay("[Cinema] Cooldown after " + c + " min");
        openMenu("opts");
    }
    else if (gPage == "probe")
    {
        string p = "";
        if (msg == "Cut") p = "cut";
        else if (msg == "CamPos") p = "campos";
        else if (msg == "Distance") p = "dist";
        else if (msg == "FOV") p = "fov";
        closeMenu();
        if (p != "") llMessageLinked(LINK_SET, PROBE, p, "");
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

// chat commands: /9 <command>   (works even if the long-press menu does not)
help()
{
    llOwnerSay("[Cinema] commands: /9 menu | start | stop | grab | status | debug on|off | trace on|off | far on|off | maxcam <m> | probe cut|campos|dist|fov | reset");
}

onCommand(string msg)
{
    list a = llParseString2List(llToLower(llStringTrim(msg, STRING_TRIM)), [" "], []);
    string c = llList2String(a, 0);
    string v = llList2String(a, 1);
    if (c == "menu") openMenu("main");
    else if (c == "start") llMessageLinked(LINK_SET, CMD, "start", "");
    else if (c == "stop") llMessageLinked(LINK_SET, CMD, "stop", "");
    else if (c == "status")
    {
        llOwnerSay("[Cinema/ui] v" + VERSION + " style " + cfgGet("style") + ", afk " + afkText() + ", hold " + holdText()
            + ", debug " + cfgGet("debug") + ", far shots " + cfgGet("far_ok") + ", maxcam " + cfgGet("maxcam")
            + ", free mem " + (string)llGetFreeMemory());
        llMessageLinked(LINK_SET, STATUS, "?", "");
    }
    else if (c == "debug")
    {
        if (v == "on") cfgSet("debug", "1");
        else cfgSet("debug", "0");
        llOwnerSay("[Cinema] Debug: " + onoff("debug"));
    }
    else if (c == "trace")
    {
        if (v == "on") cfgSet("trace", "1");
        else cfgSet("trace", "0");
        llOwnerSay("[Cinema] Progress messages: " + onoff("trace"));
    }
    else if (c == "grab") llMessageLinked(LINK_SET, CMD, "grab", "");
    else if (c == "far")
    {
        if (v == "on") cfgSet("far_ok", "1");
        else cfgSet("far_ok", "0");
        llOwnerSay("[Cinema] Long shots (25-45 m): " + onoff("far_ok"));
    }
    else if (c == "maxcam")
    {
        float m = (float)v;
        if (m >= 5.0 && m <= 60.0)
        {
            cfgSet("maxcam", (string)m);
            llOwnerSay("[Cinema] maxcam: " + (string)m + " m");
        }
        else llOwnerSay("[Cinema] maxcam needs a number between 5 and 60.");
    }
    else if (c == "probe")
    {
        if (v == "cut" || v == "campos" || v == "dist" || v == "fov") llMessageLinked(LINK_SET, PROBE, v, "");
        else help();
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
        gVerAsked = FALSE;
        checkOwner();
        setLook("armed");
        if (gCmdListen) llListenRemove(gCmdListen);
        gCmdListen = llListen(9, "", gOwner, "");
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
        else if (num == MSG_VER)
        {
            if (str != "?" && str != VERSION)
                llOwnerSay("[Cinema] WARNING: script version mismatch: " + (string)id + " is " + str + ", ui is " + VERSION
                    + ". Re-drop all three scripts from the same release.");
        }
    }

    listen(integer channel, string name, key id, string msg)
    {
        if (id != gOwner) return;
        if (channel == 9)
        {
            onCommand(msg);
            return;
        }
        gMenuT = llGetUnixTime();
        onChoice(msg);
    }

    timer()
    {
        if (!gVerAsked)
        {
            gVerAsked = TRUE;
            llMessageLinked(LINK_SET, MSG_VER, "?", "ui");   // core + director answer with their version
        }
        if (gListen && llGetUnixTime() - gMenuT > 60) closeMenu();
        if (!gListen) llSetTimerEvent(0.0);
    }
}
