// ============================================================================
//  Take 12  -  text.lsl  (8.0)  - every word you read
//  The notes (3 s, in Second Life's own floating text on the part "t12 note", just under the strip): NOTE "<id>|<arg>".
//  Important ones also go once to your chat (a viewer may hide floating text on HUDs). The tips: a key's first three
//  uses show one line (TIP "<word>"; counted in cin.tips; Settings › Reset › Tips again clears them). The dialog
//  bodies: ui asks TXT "<page>|<args, ~>" and gets TXT_ANS "<page>|<text>" (ui keeps the button labels, which are its
//  ids). Every text on every part is cleared at attach: yesterday's words never come back (7.2's login glitch).
//  Voice: calm, short, second person, no jargon, no exclamation marks (tools/sim/text_check.py checks it).
// ============================================================================

string VERSION = "8.0.0";
string PASS    = "cinema-1.0-build1";
integer LITE   = 0;               // the free Take 12 Scenery build (tools/build_scenery.py) sets this to 1

integer UI_STATE = 7320;
integer CFG_CHANGED = 7330;
integer NOTE    = 7344;
integer TIP     = 7345;
integer TXT     = 7346;
integer TXT_ANS = 7347;
integer MSG_VER = 7360;
integer STATUS  = 7370;

float   SHOW    = 3.0;            // s  a note stays this long

// notes: id, important (also in chat), the words (%: the argument)
list NOTES = [
    "setup", 1, "Tap the [12] to set up.",
    "frameit", 0, "Frame it, Take 12 keeps it.",
    "kept", 0, "Kept.",
    "forgot", 0, "Seat forgotten. UNDO brings it back.",
    "letgo", 0, "Take 12 lets go on this vehicle.",
    "takeback", 0, "Take 12 films here again.",
    "with", 0, "% is with you.",
    "watching", 0, "% is watching your film.",
    "theirs", 0, "You're watching %'s film.",
    "mine", 0, "Your own film again.",
    "notfilming", 0, "% isn't filming.",
    "left", 0, "% left.",
    "back", 0, "% is back.",
    "away", 0, "% is out of reach.",
    "asks", 0, "% wants to share films.",
    "asked", 0, "% is asked.",
    "busy", 0, "% is busy.",
    "noanswer", 0, "% didn't answer.",
    "old", 0, "%'s Take 12 is older. A new copy fixes it.",
    "nobody", 0, "Nobody near you wears Take 12.",
    "newer", 1, "A newer Take 12 is out. Ask the store for a new copy.",
    "moved", 1, "Moved. You can take off the old one.",
    "older", 1, "An older Take 12 is worn too. Take it off.",
    "missing", 1, "A Take 12 script is missing: %. A new copy fixes it.",
    "full", 0, "In the full Take 12.",
    "lens", 0, "Lens % mm. Ctrl+0 zooms in.",
    "mm", 0, "% mm",
    "eyeline", 0, "PgUp / PgDn: the line on your eyes. Tap the [12] to keep it.",
    "snapshot", 0, "The bars are on your screen, not in snapshots: set the snapshot size to your shape.",
    "flying", 0, "Flying: your own camera until you land.",
    "texture", 1, "% is kept and taken out of the contents: the HUD can be given away.",
    "plain", 0, "%"
];

// tips: a key's first three uses
list TIPS = [
    "TRACKING", "Tracking follows you. Tap it again: back behind you.",
    "PORTRAIT", "Portrait frames you standing. Us adds the people near you.",
    "FIXED", "Fixed keeps your own framing. Alt-click to frame it.",
    "SCENIC", "Scenic shows the place. It also starts when you're away.",
    "CLOSE", "How much of you is in the picture.",
    "ME", "Us adds the people near you.",
    "SHOULDER", "Three ways to follow you.",
    "L", "The side of the picture you walk on.",
    "VIEW A", "Two kept views for this place.",
    "FORGET SEAT", "Forget this seat's view.",
    "kept", "Kept. Alt-click away and KEEP NEW replaces it.",
    "LET GO", "Take 12 lets go every time you sit on this vehicle.",
    "DRIFT", "How far the views go.",
    "shape", "The bars on or off. Each shot's shape: Settings.",
    "link", "Share films with people near you."
];
list SAME = ["MEDIUM", "CLOSE", "WIDE", "CLOSE", "US", "ME", "FILM", "SHOULDER", "CLASSIC", "SHOULDER", "R", "L",
             "VIEW B", "VIEW A", "NEAR", "DRIFT", "ROOM", "DRIFT", "FAR", "DRIFT"];

// the main dialog's rotating tip line
list HINTS = ["Double-tap the [12] for the strip.", "Hold the [12]: everything off, hold again: back.",
              "Tap a lit shot again for its other angle.", "Alt-click in Fixed: Take 12 keeps your framing.",
              "Settings › Look › Place moves the strip to the bottom."];

key     gOwner;
integer gNote;                    // the note part's link (0: none, then the root)
float   gShownT;                  // a note shows since (0: none)
string  gShown;
integer gHint;

// ============================================================================
integer link()
{
    integer i;
    for (i = 2; i <= llGetNumberOfPrims(); i++) if (llGetLinkName(i) == "t12 note") return i;
    return LINK_ROOT;
}

// every text on every part: gone (at attach, at a reset)
clearAll()
{
    integer i;
    integer n = llGetNumberOfPrims();
    if (n == 1) llSetText("", ZERO_VECTOR, 0.0);
    for (i = 1; i <= n; i++) llSetLinkPrimitiveParamsFast(i, [PRIM_TEXT, "", ZERO_VECTOR, 0.0]);
    gShownT = 0.0;
    gShown = "";
}

string fill(string s, string a)
{
    integer i = llSubStringIndex(s, "%");
    while (i >= 0)
    {
        s = llInsertString(llDeleteSubString(s, i, i), i, a);
        i = llSubStringIndex(s, "%");
        if (a != "" && llSubStringIndex(a, "%") >= 0) i = -1;   // an argument with a % in it: once
    }
    return s;
}

show(string s)
{
    if (!gNote) gNote = link();
    llSetLinkPrimitiveParamsFast(gNote, [PRIM_TEXT, s, <1.0, 1.0, 1.0>, 1.0]);
    gShown = s;
    gShownT = llGetTime();
    llSetTimerEvent(0.5);
}

note(string id, string arg)
{
    integer i = llListFindList(NOTES, [id]);
    if (i < 0 || i % 3) return;
    string s = fill(llList2String(NOTES, i + 2), arg);
    show(s);
    if (llList2Integer(NOTES, i + 1)) llOwnerSay("[Take 12] " + s);
}

// a key's first three uses: its tip (words that share one tip count together)
tip(string w)
{
    integer j = llListFindList(SAME, [w]);
    if (j >= 0 && j % 2 == 0) w = llList2String(SAME, j + 1);
    integer i = llListFindList(TIPS, [w]);
    if (i < 0 || i % 2) return;
    string c = llLinksetDataReadProtected("cin.tips", PASS);
    list L = llParseString2List(c, [";"], []);
    integer k;
    integer n = 0;
    for (k = 0; k < llGetListLength(L); k++)
    {
        list kv = llParseString2List(llList2String(L, k), [":"], []);
        if (llList2String(kv, 0) == w)
        {
            n = (integer)llList2String(kv, 1);
            L = llDeleteSubList(L, k, k);
            k = 99;
        }
    }
    if (n >= 3) return;
    L += [w + ":" + (string)(n + 1)];
    llLinksetDataWriteProtected("cin.tips", llDumpList2String(L, ";"), PASS);
    show(llList2String(TIPS, i + 1));
}

// ---- dialog bodies ---------------------------------------------------------------
string body(string page, list a)
{
    string a0 = llList2String(a, 0);
    string a1 = llList2String(a, 1);
    string a2 = llList2String(a, 2);
    string a3 = llList2String(a, 3);
    if (page == "main")
    {
        gHint = (gHint + 1) % llGetListLength(HINTS);
        string t = "Take 12\n" + a0;
        if (LITE) t = "Take 12 Scenery\n" + a0;
        return t + "\nTip: " + llList2String(HINTS, gHint);
    }
    if (page == "settings") return "Settings";
    if (page == "lens") return "Lens\nNow: " + a0 + " mm. Cinema lens: " + a1 + " mm.\nZoom in with your viewer (Ctrl+0) until it says " + a1 + ".";
    if (page == "eye") return "Eye line\nA line shows on your screen: PgUp / PgDn move it onto your eyes, then tap the [12].\nEsc or a hold keeps the old one.";
    if (page == "shapes") return "Shapes & bars\nTracking " + a0 + " · Portrait " + a1 + "\nFixed " + a2 + " · Scenic " + a3 + " · Bars: " + llList2String(a, 4);
    if (page == "shape") return a0 + "'s shape\nNow: " + a1;
    if (page == "vehicles")
    {
        if (a0 == "") return "Vehicles\nNone marked. On a vehicle's seat, LET GO marks it.";
        return "Vehicles\nTake 12 lets go when you sit on these. Tap one to unmark it.";
    }
    if (page == "idle") return "Idle start\nScenic starts by itself when you are idle.\nNow: " + a0;
    if (page == "friends") return "Friends\nYour friends connect without being asked.\n" + a0 + "\nChime: " + a1;
    if (page == "addfriend") return "Add a friend\nPeople near you who wear Take 12.";
    if (page == "look") return "Look\nPlace: " + a0 + " · Size: " + a1 + " · Keys: " + a2;
    if (page == "place") return "Place\nWhere the strip sits. Lower and higher clear taller viewer bars.\nNow: " + a0;
    if (page == "reset") return "Reset\nTips again: every first-time tip.\nSeats & views: every kept framing.\nEverything: like new.";
    if (page == "everything") return "Reset everything?\nSettings, seats, views and friends are wiped, and the first run starts again.";
    if (page == "help") return "Help\nTracking follows you. Portrait frames you standing.\nFixed keeps your own framing. Scenic shows the place.\nTap: this menu. Double-tap: the strip. Hold: all off.";
    if (page == "connect")
    {
        if (a0 == "") return "Connect\nNobody near you wears Take 12.";
        return "Connect\nTap a name to share films. They'll be asked.";
    }
    if (page == "connected") return "Connected\n" + a0 + "\nTap a name to watch their film.";
    if (page == "ask") return a0 + " wants to share films.";
    if (page == "size") return "Easy to read?\nThe strip at the top of your screen.";
    if (page == "first") return "Welcome to Take 12\nA one-minute setup: your lens, your eye line and the size of the strip.";
    if (page == "tour1") return "The strip\nDouble-tap the [12]: the four shots and their options. Tap a shot to start it.";
    if (page == "tour2") return "Connect\nThe linked rings share films with people near you.";
    if (page == "tour3") return "Off\nHold the [12]: everything off. Hold again: back as it was.";
    return page;
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        gNote = link();
        clearAll();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "text");
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id != NULL_KEY)
        {
            gNote = link();
            clearAll();
        }
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
        if (c & CHANGED_LINK) gNote = link();
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == NOTE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            note(llList2String(L, 0), llDumpList2String(llList2List(L, 1, -1), "|"));
        }
        else if (num == TIP) tip(str);
        else if (num == TXT)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            string p = llList2String(L, 0);
            llMessageLinked(LINK_SET, TXT_ANS, p + "|" + body(p, llParseStringKeepNulls(llList2String(L, 1), ["~"], [])), id);
        }
        else if (num == CFG_CHANGED && str == "all") gNote = link();
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "text");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/text] v" + VERSION + " note part " + (string)gNote + ", tips " + llLinksetDataReadProtected("cin.tips", PASS)
                + ", free mem " + (string)llGetFreeMemory());
    }

    timer()
    {
        if (gShownT > 0.0 && llGetTime() - gShownT >= SHOW)
        {
            list t = llGetLinkPrimitiveParams(gNote, [PRIM_TEXT]);
            if (llList2String(t, 0) == gShown) llSetLinkPrimitiveParamsFast(gNote, [PRIM_TEXT, "", ZERO_VECTOR, 0.0]);
            gShownT = 0.0;
        }
        if (gShownT == 0.0) llSetTimerEvent(0.0);
    }
}
