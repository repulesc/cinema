// ============================================================================
//  Take 12  -  ui.lsl  (8.0)  - the [12]'s gestures, the dialogs, the first run, /12 commands
//  Tap the [12]: the dialog (setup only: Connect · Settings · Help). Double-tap: the strip opens or closes. Hold 0.8 s
//  (the ring fills as you hold): everything off; hold again: back exactly as it was. The dialog's words come from
//  text.lsl (TXT); the labels here are the buttons' ids.
//  First wear: nothing pops up; a note says "Tap the [12] to set up", and the first tap starts it: the lens (a live mm
//  reading), the eye line (a line on screen, PgUp / PgDn onto your eyes, tap to keep), the size of the strip, and a
//  three-step tour. Every step can be skipped. /12 <command>: tracking, portrait, fixed, scenic, bars, off, next,
//  status, debug on|off, blend on|off, place …, size s|m|l, idle off|away|5, flip, help (bind them to gesture keys).
//  Settings live in protected Linkset Data (cin.*); an owner change wipes them; a 7.x HUD's settings are migrated.
// ============================================================================

string VERSION = "8.0.10";
string PASS    = "cinema-1.0-build1";
integer LITE   = 0;                 // the free Take 12 Scenery build sets this to 1

integer UI_STATE    = 7320;
integer CFG_CHANGED = 7330;
integer LINKST      = 7342;
integer STRIP       = 7343;
integer NOTE        = 7344;
integer TXT         = 7346;
integer TXT_ANS     = 7347;
integer MSG_VER     = 7360;
integer STATUS      = 7370;
integer CMD         = 7371;

float   TAP_GAP   = 0.35;           // s  a second tap within this: a double-tap
float   LONG_HOLD = 0.8;            // s  held this long: everything off (or back)
float   EYE_D     = 2.5;            // m  the eye-line check's camera, in front of you
string  NEED = "core ui text screen strip bars tracking portrait fixed scenic sync carry";

key     gOwner;
integer gChan;
integer gListen;
integer gCmdL;
integer gMenuT;
string  gPage;
list    gBtn;                       // the buttons shown (labels)
string  gState = "wait";            // core
string  gShot;
string  gLink = "alone";
integer gOpen;                      // the strip is open
integer gOpenOff;                   // ... it was, when everything went off
// gestures
float   gDown;
float   gTapT;
integer gHeld;
integer gLongDone;
integer gTapN;
integer gDbl;
integer gFill;
// the first run and the eye line
string  gFirst;                     // "" done; else the step
integer gEye;                       // the eye-line check runs
float   gEyeZ;                      // the line, screen height from the middle
vector  gEyeCam;
float   gFeet;
float   gTall;
integer gLensL;                     // the lens page shows the live mm
list    gVer;                       // the scripts that answered
integer gVerT;                      // the version check: asked at
integer gVerStep;
integer gLensTold;

// ============================================================================
string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

set(string k, string v)
{
    llLinksetDataWriteProtected("cin." + k, v, PASS);
    llMessageLinked(LINK_SET, CFG_CHANGED, k, "");
}

note(string id, string a)
{
    llMessageLinked(LINK_SET, NOTE, id + "|" + a, "");
}

// delete the keys matching a pattern, ten at a time (a list of every key at once can run the script out of memory, 8.0.1);
// a key it cannot delete (another password) is stepped over
wipe(string re)
{
    integer skip;
    list K = llLinksetDataFindKeys(re, 0, 10);
    while (K != [] && skip < 200)
    {
        integer i;
        for (i = 0; i < llGetListLength(K); i++) skip += (llLinksetDataDeleteProtected(llList2String(K, i), PASS) != 0);
        K = llLinksetDataFindKeys(re, skip, 10);
    }
}

// new owner, first wear, a 7.x HUD: settings
checkOwner()
{
    string v = cfg("ver");
    integer wiped = (cfg("owner") != (string)gOwner || (v != "" && llGetSubString(v, 0, 0) != "8"));
    if (cfg("owner") != (string)gOwner)
    {
        llLinksetDataReset();
        llLinksetDataWriteProtected("cin.owner", (string)gOwner, PASS);
    }
    else if (v != "" && llGetSubString(v, 0, 0) != "8")
    {
        // a 7.x HUD's settings: the friends and the window stay; 8.0 has new keys for the rest
        string fr = cfg("friends");
        string as = cfg("aspect");
        wipe("^cin\\.");
        llLinksetDataWriteProtected("cin.owner", (string)gOwner, PASS);
        if (fr != "") llLinksetDataWriteProtected("cin.friends", fr, PASS);
        if (as != "") llLinksetDataWriteProtected("cin.aspect", as, PASS);
    }
    llLinksetDataWriteProtected("cin.ver", VERSION, PASS);
    if (cfg("firstrun") != "done") gFirst = "start";
    // the scripts start in any order: the ones that read the settings before this wipe read them again (8.0.10:
    // a new owner saw the seller's strip place and bars)
    if (wiped) llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
}

// ---- dialogs ------------------------------------------------------------------------------
// llDialog fills from the bottom-left: rows bottom-first, padded
list order(list b)
{
    while (llGetListLength(b) % 3) b += " ";
    list o = [];
    integer i;
    for (i = llGetListLength(b) - 3; i >= 0; i -= 3) o += llList2List(b, i, i + 2);
    return o;
}

closeMenu()
{
    if (gListen) llListenRemove(gListen);
    gListen = 0;
    gLensL = FALSE;
}

// a page: its buttons now, its words from text.lsl (TXT_ANS opens it)
page(string p, string args, list b)
{
    closeMenu();
    gPage = p;
    gBtn = b;
    gChan = -(integer)(llFrand(1000000000.0) + 1000.0);
    gListen = llListen(gChan, "", gOwner, "");
    gMenuT = llGetUnixTime();
    llMessageLinked(LINK_SET, TXT, p + "|" + args, "ui");
    timer0();
}

string mark(string label, integer on)
{
    if (on) return "● " + label;
    return label;
}

string bare(string m)
{
    if (llGetSubString(m, 0, 1) == "● ") return llGetSubString(m, 2, -1);
    return m;
}

integer mm()
{
    return llRound(12.0 / llTan(llGetCameraFOV() * 0.5));
}

string lensWant()
{
    string l = cfg("lens");
    if (l == "") l = "35";
    return l;
}

menu()
{
    string st = "Your own camera";
    if (gState == "off") st = "Everything off · hold the [12] to come back";
    else if (gShot != "") st = llToUpper(llGetSubString(gShot, 0, 0)) + llGetSubString(gShot, 1, -1);
    if (gLink == "on" || gLink == "shared") st += " · connected";
    if (gLink == "theirs") st += " · watching";
    page("main", st, ["Connect", "Settings", "Help", "Feedback", "Close"]);   // Feedback while in beta (8.0.10)
}

open(string p)
{
    if (p == "settings")
    {
        list b = ["Lens", "Eye line", "Tracking", "Frames & bars", "Vehicles", "Idle start", "Friends", "Look", "Reset", "‹ Back"];
        if (LITE) b = llDeleteSubList(llDeleteSubList(b, 3, 3), 1, 1);   // the free build: no Portrait, no Fixed
        page(p, "", b);
    }
    else if (p == "lens")
    {
        string w = lensWant();
        list bk = ["‹ Back", "Done"];                       // Done: the lens is set, the page goes (8.0.8)
        if (gFirst == "lens") bk = ["Skip"];
        // the classic primes, from wide to normal (8.0.8; 85 mm and longer are portrait lenses, too tight to live in)
        page(p, (string)mm() + "~" + w, [mark("24 mm", w == "24"), mark("28 mm", w == "28"), mark("35 mm", w == "35"),
            mark("40 mm", w == "40"), mark("50 mm", w == "50")] + bk);
        gLensL = TRUE;
    }
    else if (p == "shapes")
    {
        list S = [];
        integer i;
        for (i = 0; i < 4; i++)
        {
            string s = cfg("shape." + llList2String(["tracking", "portrait", "fixed", "scenic"], i));
            if (s == "") s = llList2String(["2.39", "1.85", "1.85", "2.39"], i);
            S += s;
        }
        string bs = cfg("bstyle");
        page(p, llDumpList2String(S, "~") + "~" + llList2String(["black", "dimmed"], bs == "dim"),
            ["Tracking", "Portrait", "Fixed", "Scenic", mark("Black", bs != "dim"), mark("Dimmed", bs == "dim"), "‹ Back"]);
    }
    else if (llGetSubString(p, 0, 5) == "frame:")
    {
        // the frame dialog: this shot's frames from the widest to the tallest, the photo frames for every shot but
        // Tracking (a walking camera wants a cinema frame), the current one marked; the strip's ▭ opens it (8.0.9)
        string s = llGetSubString(p, 6, -1);
        string now = cfg("shape." + s);
        if (now == "") now = llList2String(["2.39", "1.85", "1.85", "2.39"], llListFindList(["tracking", "portrait", "fixed", "scenic"], [s]));
        list F = ["2.39", "2.00", "1.85", "1.66", "3:2", "4:3", "1:1", "4:5", "Full"];
        if (s == "tracking") F = llDeleteSubList(F, 4, 7);
        list b = [];
        integer i;
        for (i = 0; i < llGetListLength(F); i++) b += mark(llList2String(F, i), llToLower(llList2String(F, i)) == now);
        page("frame", s + "~" + now, b + ["‹ Back", "Done"]);
        gPage = p;
    }
    else if (p == "idle")
    {
        string i = cfg("idle");
        if (i == "") i = "5";
        page(p, llList2String(["after 5 min still, or Away", "only when Away", "off"], llListFindList(["5", "away", "off"], [i])),
            [mark("Off", i == "off"), mark("Away", i == "away"), mark("5 min", i == "5"), "‹ Back"]);
    }
    else if (p == "vehicles")
    {
        list V = llParseString2List(cfg("veh"), [";"], []);
        list b = [];
        integer i;
        for (i = 0; i < llGetListLength(V) && i < 9; i++) b += llGetSubString(llList2String(llParseString2List(llList2String(V, i), ["|"], []), 0), 0, 23);
        page(p, llDumpList2String(V, "~"), b + ["‹ Back"]);
    }
    else if (p == "friends")
    {
        closeMenu();                                        // Settings › Friends is sync's (8.0.6: room in this script)
        llMessageLinked(LINK_SET, CMD, "connect|friends", "");
    }
    else if (p == "look")
    {
        string pl = cfg("place");
        string sz = cfg("size");
        if (sz == "") sz = "m";
        string ks = cfg("keys");
        page(p, llList2String(["Top", "Top, lower", "Bottom", "Bottom, higher"], llListFindList(["top", "topl", "bot", "both"], [pl]) * (pl != "")) + "~"
            + llToUpper(sz) + "~" + llList2String(["Soft", "Clear"], ks == "clear"),
            ["Place", mark("S", sz == "s"), mark("M", sz == "m"), mark("L", sz == "l"), mark("Soft", ks != "clear"), mark("Clear", ks == "clear"), "‹ Back"]);
    }
    else if (p == "place")
    {
        string pl = cfg("place");
        if (pl == "") pl = "top";
        page(p, llList2String(["Top", "Top, lower", "Bottom", "Bottom, higher"], llListFindList(["top", "topl", "bot", "both"], [pl])),
            [mark("Top", pl == "top"), mark("Top, lower", pl == "topl"), mark("Bottom", pl == "bot"), mark("Bottom, higher", pl == "both"), "‹ Back"]);
    }
    else if (p == "reset") page(p, "", ["Tips again", "Seats & views", "Everything", "‹ Back"]);
    else if (p == "everything") page(p, "", ["Yes, reset", "‹ Back"]);
    else if (p == "help") page(p, "", ["Guide", "Tips again", "‹ Back"]);
    else if (p == "first") page(p, "", ["Start", "Later"]);
    else if (p == "size") page(p, "", ["Smaller", "Good", "Larger"]);
    else if (p == "inview") page(p, "", ["Yes", "Lower it"]);
    else if (p == "feel")
    {
        integer sn = (cfg("feel") != "smooth");             // Tracking's feel: snappy to steer by (the default, 8.0.8), or smooth
        page(p, llList2String(["Smooth", "Snappy"], sn), [mark("Smooth", !sn), mark("Snappy", sn), "‹ Back"]);
    }
    else if (p == "tour1" || p == "tour2") page(p, "", ["Next ›", "Skip"]);
    else if (p == "tour3") page(p, "", ["Done"]);
    else menu();
}

string up(string p)
{
    if (llListFindList(["lens", "feel", "shapes", "idle", "vehicles", "friends", "look", "reset"], [p]) >= 0) return "settings";
    if (llGetSubString(p, 0, 5) == "frame:") return "shapes";
    if (p == "place") return "look";
    if (p == "everything") return "reset";
    return "main";
}

choose(string m)
{
    string b = bare(m);
    if (b == "Close" || b == "Done" || b == " ") { closeMenu(); return; }
    if (b == "Skip" && gPage == "lens") { closeMenu(); eyeStart(); return; }
    if (b == "‹ Back") { open(up(gPage)); return; }
    if (gPage == "main")
    {
        if (b == "Connect" || b == "Feedback") { closeMenu(); llMessageLinked(LINK_SET, CMD, llList2String(["connect|menu", "feedback"], b == "Feedback"), ""); }
        else if (b == "Settings") open("settings");
        else if (b == "Help") open("help");
    }
    else if (gPage == "settings")
    {
        if (b == "Eye line") { closeMenu(); eyeStart(); }
        else open(llList2String(["lens", "feel", "shapes", "vehicles", "idle", "friends", "look", "reset"],
            llListFindList(["Lens", "Tracking", "Frames & bars", "Vehicles", "Idle start", "Friends", "Look", "Reset"], [b])));
    }
    else if (gPage == "lens")
    {
        set("lens", llGetSubString(b, 0, 1));
        if (gFirst == "lens") { closeMenu(); eyeStart(); return; }
        open("lens");
    }
    else if (gPage == "shapes")
    {
        if (b == "Black" || b == "Dimmed")
        {
            set("bstyle", llList2String(["black", "dim"], b == "Dimmed"));
            open("shapes");
            return;
        }
        open("frame:" + llToLower(b));
    }
    else if (llGetSubString(gPage, 0, 5) == "frame:")
    {
        set("shape." + llGetSubString(gPage, 6, -1), llToLower(b));
        if (b != "Full" && cfg("bars") == "0") set("bars", "1");   // a frame picked is a frame shown
        open(gPage);                                    // the page stays: its snapshot size for the new frame
    }
    else if (gPage == "idle")
    {
        set("idle", llList2String(["off", "away", "5"], llListFindList(["Off", "Away", "5 min"], [b])));
        open("idle");
    }
    else if (gPage == "vehicles")
    {
        list V = llParseString2List(cfg("veh"), [";"], []);
        integer i;
        for (i = llGetListLength(V) - 1; i >= 0; i--)
            if (llGetSubString(llList2String(llParseString2List(llList2String(V, i), ["|"], []), 0), 0, 23) == b) V = llDeleteSubList(V, i, i);
        set("veh", llDumpList2String(V, ";"));
        open("vehicles");
    }
    else if (gPage == "look")
    {
        if (b == "Place") { open("place"); return; }
        if (b == "S" || b == "M" || b == "L") set("size", llToLower(b));
        else set("keys", llToLower(b));
        open("look");
    }
    else if (gPage == "place")
    {
        set("place", llList2String(["top", "topl", "bot", "both"], llListFindList(["Top", "Top, lower", "Bottom", "Bottom, higher"], [b])));
        open("place");
    }
    else if (gPage == "reset")
    {
        if (b == "Tips again") { llLinksetDataDeleteProtected("cin.tips", PASS); closeMenu(); }
        else if (b == "Seats & views")
        {
            wipe("^cin\\.(seat|view|places)");
            llMessageLinked(LINK_SET, CFG_CHANGED, "seats", "");
            closeMenu();
        }
        else if (b == "Everything") open("everything");
    }
    else if (gPage == "everything")
    {
        closeMenu();
        llLinksetDataReset();
        llLinksetDataWriteProtected("cin.owner", (string)gOwner, PASS);
        llLinksetDataWriteProtected("cin.ver", VERSION, PASS);
        llMessageLinked(LINK_SET, CFG_CHANGED, "all", "");
        gFirst = "start";
        first();
    }
    else if (gPage == "help")
    {
        if (b == "Tips again") { llLinksetDataDeleteProtected("cin.tips", PASS); closeMenu(); }
        else if (b == "Guide") { closeMenu(); guide(); }
    }
    else if (gPage == "first")
    {
        llLinksetDataWriteProtected("cin.firstrun", "done", PASS);   // asked once: a re-wear never starts it again (8.0.6)
        if (b == "Start") { gFirst = "lens"; open("lens"); }
        else { closeMenu(); gFirst = "later"; }
    }
    else if (gPage == "size")
    {
        integer i = llListFindList(["s", "m", "l"], [cfg("size")]);
        if (i < 0) i = 1;
        if (b == "Smaller" && i > 0) i--;
        if (b == "Larger" && i < 2) i++;
        set("size", llList2String(["s", "m", "l"], i));
        if (b == "Good") open("inview");
        else open("size");
    }
    else if (gPage == "feel")
    {
        set("feel", llToLower(b));
        open("feel");
    }
    else if (gPage == "inview")
    {
        // taller viewer bars (favourites, navigation) can cover the strip: lower it a step (8.0.6)
        if (b == "Lower it") set("place", llList2String(["topl", "topl", "topl", "both", "both"], llListFindList(["top", "topl", "bot", "both"], [cfg("place")]) + 1));
        if (b == "Yes") open("tour1");
        else open("inview");
    }
    else if (gPage == "tour1") { if (b == "Skip") done(); else open("tour2"); }
    else if (gPage == "tour2") { if (b == "Skip") done(); else open("tour3"); }
    else if (gPage == "tour3") done();
}

guide()
{
    string card = "";
    integer i;
    for (i = llGetInventoryNumber(INVENTORY_NOTECARD) - 1; i >= 0; i--)
        if (llSubStringIndex(llGetInventoryName(INVENTORY_NOTECARD, i), "Read Me") >= 0) card = llGetInventoryName(INVENTORY_NOTECARD, i);
    if (card != "") llGiveInventory(gOwner, card);
}

// ---- the first run ------------------------------------------------------------------------
first()
{
    if (gFirst == "start") open("first");
}

done()
{
    closeMenu();
    gFirst = "";
    llLinksetDataWriteProtected("cin.firstrun", "done", PASS);
    if (!gOpen) strip("open");                              // the controls stay in view (8.0.4: they vanished after the setup)
}

// ---- the eye line: a line on screen, PgUp / PgDn onto your eyes, tap to keep ----------------------------------------
eyeStart()
{
    if (LITE && gFirst == "lens") { eyeEnd(FALSE); return; }            // the free build: no Portrait, no eye line
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2 || !(llGetPermissions() & PERMISSION_TAKE_CONTROLS)) return;
    vector P = llList2Vector(d, 0);
    vector F = llRot2Fwd(llList2Rot(d, 1));
    F.z = 0.0;
    F = llVecNorm(F);
    vector sz = llGetAgentSize(gOwner);
    gTall = sz.z;
    gFeet = P.z - 0.5 * gTall;
    float e = (float)cfg("eye");
    if (e < 0.5 || e > 1.5) e = 0.935;
    float ez = gFeet + e * gTall;
    gEyeCam = P + F * EYE_D;
    gEyeCam.z = ez;
    llMessageLinked(LINK_SET, CMD, "eyecam|" + (string)gEyeCam + "|" + (string)<P.x, P.y, ez>, "");
    gEyeZ = 0.0;                                            // the camera is at your eyes: the line starts in the middle
    gEye = TRUE;
    llTakeControls(CONTROL_UP | CONTROL_DOWN, TRUE, FALSE);
    llMessageLinked(LINK_SET, STRIP, "eye|" + (string)gEyeZ, "");
    note("eyeline", "");
}

eyeEnd(integer keep)
{
    gEye = FALSE;
    llTakeControls(CONTROL_UP | CONTROL_DOWN, FALSE, TRUE);
    llMessageLinked(LINK_SET, STRIP, "eye|off", "");
    llMessageLinked(LINK_SET, CMD, "eyecam|off", "");
    if (keep)
    {
        // the line's screen height back to a height on you: tan of the half-height is gEyeZ / 0.5 of the lens
        float h = gEyeCam.z + (gEyeZ / 0.5) * EYE_D * llTan(llGetCameraFOV() * 0.5);
        set("eye", (string)((h - gFeet) / gTall));
        note("kept", "");
    }
    if (gFirst == "lens" || gFirst == "eye")
    {
        gFirst = "size";
        strip("open");
        open("size");
    }
}

// ---- the strip -------------------------------------------------------------------------------
strip(string a)
{
    if (a == "toggle") gOpen = !gOpen;
    else if (a == "open") gOpen = TRUE;
    else if (a == "close") gOpen = FALSE;
    llMessageLinked(LINK_SET, STRIP, a, "");
}

// ---- gestures -------------------------------------------------------------------------------
// the [12]: the root, its ring and dot (in front of it), and the parts parked behind it while hidden (the strip's, the
// bars'). 8.0.3: a tap often landed on one of those and was lost
integer twelve(integer link)
{
    if (link == 1) return TRUE;
    string n = llGetLinkName(link);
    vector s = llList2Vector(llGetLinkPrimitiveParams(link, [PRIM_SIZE]), 0);
    return (n == "t12 ring" || n == "t12 dot" || s.y < 0.011);
}

onTap()
{
    if (gEye) { eyeEnd(TRUE); return; }
    if (gFirst == "start" || gFirst == "later") { gFirst = "start"; first(); return; }
    menu();
}

onDouble()
{
    if (gEye) return;
    if (gState == "off") return;
    strip("toggle");
}

onLong()
{
    if (gEye) { eyeEnd(FALSE); return; }
    if (gState == "off")
    {
        llMessageLinked(LINK_SET, CMD, "on", "");
        if (gOpenOff) strip("open");
    }
    else
    {
        gOpenOff = gOpen;
        if (gOpen) strip("close");
        llMessageLinked(LINK_SET, CMD, "off", "");
        llMessageLinked(LINK_SET, CMD, "mine", "");
    }
}

timer0()
{
    if (gHeld || gTapN) llSetTimerEvent(0.1);
    else if (gListen || gVerT || gLensL) llSetTimerEvent(1.0);
    else llSetTimerEvent(0.0);
}

// ---- /12 ---------------------------------------------------------------------------------------
command(string m)
{
    list L = llParseString2List(llToLower(llStringTrim(m, STRING_TRIM)), [" "], []);
    string c = llList2String(L, 0);
    string a = llList2String(L, 1);
    if (llListFindList(["tracking", "portrait", "fixed", "scenic"], [c]) >= 0) llMessageLinked(LINK_SET, CMD, "shot|" + c, "");
    else if (c == "bars" || c == "next" || c == "feedback") llMessageLinked(LINK_SET, CMD, c, "");   // feedback: carry's
    else if (c == "off") onLong();
    else if (c == "strip") strip("toggle");
    else if (c == "status") llMessageLinked(LINK_SET, STATUS, "?", "");
    else if (c == "debug") llMessageLinked(LINK_SET, CMD, "debug|" + (string)(a == "on"), "");
    else if (c == "blend") llMessageLinked(LINK_SET, CMD, "blend|" + (string)(a == "on"), "");
    else if (c == "flip") set("flip", llList2String(["1", "0"], cfg("flip") == "1"));
    else if (c == "place" && llListFindList(["top", "topl", "bot", "both"], [a]) >= 0) set("place", a);
    else if (c == "size" && llListFindList(["s", "m", "l"], [a]) >= 0) set("size", a);
    else if (c == "idle" && llListFindList(["off", "away", "5"], [a]) >= 0) set("idle", a);
    else if (c == "connect") llMessageLinked(LINK_SET, CMD, "connect|menu", "");
    else note("commands", "");
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        checkOwner();
        gCmdL = llListen(12, "", gOwner, "");
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_TAKE_CONTROLS | PERMISSION_TRACK_CAMERA);
        gVerT = llGetUnixTime();
        timer0();
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id == NULL_KEY) return;
        gOpen = FALSE;
        gEye = FALSE;
        gState = "wait";
        gShot = "";
        gLensTold = FALSE;
        closeMenu();
        llRequestPermissions(gOwner, PERMISSION_TAKE_CONTROLS | PERMISSION_TRACK_CAMERA);
        if (cfg("firstrun") != "done") gFirst = "start";
        gVerStep = 0;
        gVerT = llGetUnixTime();
        timer0();
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
    }

    control(key id, integer level, integer edge)
    {
        if (!gEye) return;
        float dz = 0.004;                                   // a press (and every repeat): a few pixels
        if (level & CONTROL_UP) gEyeZ += dz;
        if (level & CONTROL_DOWN) gEyeZ -= dz;
        if (gEyeZ > 0.45) gEyeZ = 0.45;
        if (gEyeZ < -0.45) gEyeZ = -0.45;
        llMessageLinked(LINK_SET, STRIP, "eye|" + (string)gEyeZ, "");
    }

    touch_start(integer n)
    {
        if (llDetectedKey(0) != gOwner || !twelve(llDetectedLinkNumber(0))) return;
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
        gFill = 0;
        timer0();
    }

    touch_end(integer n)
    {
        if (llDetectedKey(0) != gOwner || !twelve(llDetectedLinkNumber(0))) return;
        gHeld = FALSE;
        if (gFill) llMessageLinked(LINK_SET, STRIP, "hold|0", "");
        gFill = 0;
        if (gLongDone) { timer0(); return; }
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
        timer0();
    }

    listen(integer ch, string name, key id, string m)
    {
        if (id != gOwner) return;
        if (ch == 12) { command(m); return; }
        gMenuT = llGetUnixTime();
        choose(m);
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == TXT_ANS && id == "ui")
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            string p = llList2String(L, 0);
            if (gListen && (p == gPage || llSubStringIndex(gPage, p + ":") == 0))
                llDialog(gOwner, llDumpList2String(llList2List(L, 1, -1), "|"), order(gBtn), gChan);
        }
        else if (num == UI_STATE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            string was = gState;
            gState = llList2String(L, 0);
            gShot = llList2String(L, 1);
            if (gState == "film" && was != "film" && !gLensTold && llGetPermissions() & PERMISSION_TRACK_CAMERA)
            {
                gLensTold = TRUE;                           // the first shot after you wear it: is your lens on?
                if (mm() < (integer)lensWant() * 0.85) note("lens", (string)mm());
            }
        }
        else if (num == LINKST) gLink = llList2String(llParseStringKeepNulls(str, ["|"], []), 0);
        else if (num == CMD && str == "eyequit" && gEye) eyeEnd(FALSE);   // you walked off: skipped, the old line kept
        else if (num == CMD && str == "menu|settings") open("settings");   // back from sync's Friends page
        else if (num == CMD && str == "frames" && gShot != "" && gState != "wait" && gState != "off") open("frame:" + gShot);
        else if (num == CMD && str == "firstrun") { gFirst = "start"; first(); }
        else if (num == CFG_CHANGED && str == "all" && cfg("firstrun") == "done") gFirst = "";   // carried over: set up
        else if (num == MSG_VER && str != "?")
        {
            if (llListFindList(gVer, [(string)id]) < 0) gVer += [(string)id];
            if (str != VERSION) note("mixed", (string)id);
        }
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/ui] v" + VERSION + " " + gState + " " + gShot + ", strip " + llList2String(["closed", "open"], gOpen)
                + ", first run " + llList2String([gFirst, "done"], gFirst == "") + ", free mem " + (string)llGetFreeMemory());
    }

    timer()
    {
        float now = llGetTime();
        if (gHeld && !gLongDone && !gDbl)
        {
            integer f = (integer)((now - gDown) / LONG_HOLD * 8.0);
            if (f > 8) f = 8;
            if (f != gFill && f > 0)
            {
                gFill = f;                                  // the ring fills as you hold
                llMessageLinked(LINK_SET, STRIP, "hold|" + (string)f, "");
            }
            if (now - gDown >= LONG_HOLD)
            {
                gLongDone = TRUE;
                onLong();
            }
        }
        if (gTapN && now - gTapT > TAP_GAP)
        {
            gTapN = FALSE;
            onTap();
        }
        if (gListen && llGetUnixTime() - gMenuT > 600) closeMenu();
        if (gLensL) note("mm", (string)mm());
        if (gVerT && gVerStep == 0 && llGetUnixTime() - gVerT >= 2)
        {
            gVer = ["ui"];                                  // every script answers with its name
            gVerStep = 1;
            llMessageLinked(LINK_SET, MSG_VER, "?", "ui");
        }
        else if (gVerT && gVerStep == 1 && llGetUnixTime() - gVerT >= 4)
        {
            // which scripts did not answer: amber, and the note says which
            list miss = [];
            integer i;
            list need = llParseString2List(NEED, [" "], []);
            if (LITE) need = llDeleteSubList(need, 6, 8);  // the free build: no tracking, portrait, fixed
            for (i = 0; i < llGetListLength(need); i++) if (llListFindList(gVer, [llList2String(need, i)]) < 0) miss += llList2String(need, i);
            if (miss != [])
            {
                note("missing", llDumpList2String(miss, ", "));
                llMessageLinked(LINK_SET, STRIP, "problem|1", "");
            }
            gVerT = 0;
            gVerStep = 0;
            if (gFirst == "start") note("setup", "");
            else if (cfg("open") != "0") strip("open");    // set up: the strip shows as you left it (8.0.5: it started hidden)
        }
        timer0();
    }
}
