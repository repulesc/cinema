// ============================================================================
//  Take 12  -  sync.lsl  (v6.8)  - Connect
//  6.8.0: sharing became Connect. You connect with the people near you; once connected, WHOEVER FILMS LEADS: start
//  any camera and everyone connected sees it; when nobody films, everyone has their own camera, still connected.
//  Hold the HUD button: the Connect panel (connect.lsl draws it), whatever you are doing.
//    NOT CONNECTED  who is near (a quick "who" check), + <name> (connect one), + Everyone, ⇄ Join <connected>, Give Watch
//    CONNECTED      you film / nobody films: Next or Film, + Invite, Disconnect;  watching: My turn, Next, Disconnect
//    ASKED          Connect, No (a double-tap also connects)
//  Under the hood it is still one hub (the "director": whoever filmed last, or who connected the others) and its
//  viewers. A viewer whose own camera starts asks the hub ("ask"), which always hands over ("lead|1", "director|<key>"
//  to everyone): everyone, the hub too, then follows the new one. The hub's Disconnect hands the connection to
//  another Take 12 ("lead|2": you hold it, no camera started) or, with only Watches left, ends it (it asks first).
//  A movement key while watching: your own camera for a moment, then back on the shared view (4 s still).
//  A Take 12 Watch, or Take 12 with you in its Friends, connects at once; anyone else is asked. Above the HUD:
//  "⇄ You film · Ana, Ben see it", "⇄ Ana films", "⇄ Connected · nobody films", "Ana wants to connect".
//  Channel SYNC_CH, messages "T12|<what>|...":
//    who|<name> (llRegionSay) -> here|<T/W>|<idle/live/view/pend>|<director name>
//    invite|<name> -> ack|1 (joined) / ack|0 (asked) / busy|<what>
//    viewer -> director: join leave next away back ask        director -> viewer: cam|<pos>|<focus>|<lag> hb pause
//    lead|<1 you lead / 2 you hold it / 0 no>   director|<key>|<name> (a hand-over) kick end
//  The panels are drawn by connect.lsl (SHARE_UI / SHARE_DO; share.lsl before 6.8). Full description:
//  docs/CONNECT.md. Checked in tools/sim/sync_sim.py.
// ============================================================================

string VERSION = "7.0.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer CAMSET     = 7325;   // core -> sync  "<pos>|<focus>|<lag>|<lens>" (6.0.1: viewers place it through their own lens)
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer TEXT       = 7380;   // sync -> tips  "<live/view/inv or empty>|<the state above the HUD>"
integer SHARE_UI   = 7392;   // sync -> connect: open a panel "<camOn>|<page>|..." (connect.lsl draws the Connect panel)
integer SHARE_DO   = 7393;   // connect -> sync: the choice
integer SYNC_CH    = -7712120;   // Take 12 and Take 12 Watch speak on this channel
float   NEAR       = 20.0;       // m  who is found and asked to connect
integer NEXT_GAP   = 5;          // s  two viewers' double-taps close together cut once
integer WAIT       = 20;         // s  an invitation waits this long
integer GONE       = 25;         // s  no camera and no heartbeat from the director: it is gone
integer QUIET      = 25;         // s  a viewer not heard from this long shows "(no signal)"...
integer LOST       = 45;         // s  ... and this long is dropped
integer gBeatT;              // viewing: your last heartbeat to the director
float   OWN        = 4.0;        // s  still after a movement key while watching: back on the shared view

key     gOwner;
integer gSharing;            // CONNECTED, as the hub: you film, or filmed last, or connected the others
integer gCamOn;              // your own camera runs
integer gHand;               // you just handed the camera over: your stop is not the end
integer gToggleT;            // Connect / Disconnect: repeats within 2 s are ignored
string  gMyMode = "social";  // your last camera (My turn starts it)
list    gWatchers;           // LIVE: who watches you
list    gSeen;               // ... when each was last heard from (their heartbeat), same order as gWatchers
list    gAway;               // ... and who of them is looking around
integer gNextT;              // ... the last "next" asked
integer gHbT;                // ... the last heartbeat and roster check
string  gLastCam;            // the camera on your screen now
list    gInv;                // invited, no answer yet
list    gRes;                // ... the answers
integer gInvT;
key     gHost;               // VIEWING: whose view you follow
vector  gApplied;            // ... the camera last set from it
float   gApplyT;             // ... and until when it may still be moving there
integer gIsAway;             // ... you are looking around on your own
integer gHeld;               // ... the director paused (their camera stopped): their last shot stays
integer gHearT;              // ... the last word from the director
integer gAskT;               // ... your camera started: you asked for the lead, waiting
float   gOwnT;               // ... a movement key: your own camera since (0: following)
key     gOffer;              // INVITED by
integer gPendT;              // ... since
list    gNear;               // the "who" check: [key, "<T/W>~<state>~<director>", ...]
float   gWhoT;               // ... sent at (0 = none running)
float   gTextT;              // a short notice above the HUD, until it gives way to the state again
string  gCam;                // the director's last camera, as sent: re-placed when your own lens changes
float   gMyFov;              // your lens when it was placed
string  gNoteS;              // ... its text
string  gSent;               // the sharing block last sent to tips (TEXT), which shows it above the HUD

// ---- above the HUD: the state, and short notices ------------------------------
// a name, also for someone who has just left the region (llKey2Name is "" then): the last ones seen are remembered
list    gBook;               // [key, name, ...]
string name(key k)
{
    string n = llKey2Name(k);
    integer i = llListFindList(gBook, [k]);
    if (n == "" && i >= 0) return llList2String(gBook, i + 1);
    if (n != "" && i < 0)
    {
        gBook += [k, n];
        if (llGetListLength(gBook) > 40) gBook = llDeleteSubList(gBook, 0, 1);
    }
    return n;
}

// a short name: "Ana Resident" -> "Ana"
string sn(key k)
{
    string n = name(k);
    if (n == "") n = "someone";
    integer i = llSubStringIndex(n, " Resident");
    if (i > 0) n = llGetSubString(n, 0, i - 1);
    return n;
}

string ind()
{
    integer now = llGetUnixTime();
    if (gSharing)
    {
        // who is connected with you, live: names, looking around, no signal
        integer n = llGetListLength(gWatchers);
        if (n == 0) return "⇄ Connecting… · nobody has joined yet";
        list s = [];
        integer i;
        for (i = 0; i < n && i < 4; i++)
        {
            key k = llList2Key(gWatchers, i);
            string t = sn(k);
            if (now - llList2Integer(gSeen, i) > QUIET) t += " (no signal)";
            else if (llListFindList(gAway, [k]) >= 0) t += " (own camera)";
            s += [t];
        }
        string r = llDumpList2String(s, ", ");
        if (n > 4) r += " +" + (string)(n - 4);
        if (!gCamOn) return "⇄ Connected · " + r + "\nnobody films · double-tap: film";
        return "⇄ You film · " + r + " see it";
    }
    if (gHost != NULL_KEY)
    {
        if (gAskT) return "⇄ Taking the camera…";
        if (now - gHearT > 15) return "⇄ " + sn(gHost) + " · no signal…";
        if (gHeld) return "⇄ Connected with " + sn(gHost) + "\nnobody films · double-tap: film";
        if (gOwnT > 0.0) return "⇄ " + sn(gHost) + " films · your camera for a moment";
        if (gIsAway) return "⇄ " + sn(gHost) + " films · looking around (Esc: back)";
        return "⇄ " + sn(gHost) + " films\ndouble-tap: next for all";
    }
    if (gPendT) return sn(gOffer) + " wants to connect · double-tap: yes";
    return "";
}

// the state goes to tips, the one owner of the text above the HUD (with the status line and the tips)
refresh()
{
    string k = "";
    if (gSharing) k = "live";
    else if (gHost != NULL_KEY) k = "view";
    else if (gPendT) k = "inv";
    k += "|" + ind();
    if (k != gSent) llMessageLinked(LINK_SET, TEXT, k, "");
    gSent = k;
    llSetTimerEvent(1.0);
}

// a short notice: the whole text for 4 s, then it gives way (tips draws the state again)
show(string s)
{
    llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gNoteS = llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0);     // as kept (cut short past 254 bytes)
    gTextT = llGetTime();
    llSetTimerEvent(1.0);
}

quiet()
{
    if (gTextT > 0.0 && llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0) == gNoteS) llSetText("", ZERO_VECTOR, 0.0);
    gTextT = 0.0;
    refresh();
}

note(string s)
{
    llOwnerSay("[Take 12] " + s);
    show(s);
}

// the director's camera through YOUR lens: the same line to the same focus, at the distance that gives the same
// picture size (k = tan(theirs / 2) / tan(yours / 2)); a wall on the way stops it 0.3 m short. again: your zoom changed
place(integer again)
{
    list L = llParseStringKeepNulls(gCam, ["|"], []);
    vector p = (vector)llList2String(L, 0);
    vector f = (vector)llList2String(L, 1);
    float lag = (float)llList2String(L, 2);
    float df = (float)llList2String(L, 3);
    gMyFov = llGetCameraFOV();
    if (again) lag = 0.5;
    if (df > 0.05 && gMyFov > 0.05)
    {
        float k = llTan(df * 0.5) / llTan(gMyFov * 0.5);
        if (k < 0.2) k = 0.2;
        if (k > 5.0) k = 5.0;
        vector q = f + (p - f) * k;
        list r = llCastRay(f, q, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
        if (llList2Integer(r, -1) > 0) q = llList2Vector(r, 1) + llVecNorm(f - q) * 0.3;
        p = q;
    }
    gApplied = p;
    gApplyT = llGetTime() + lag + 2.0;
    llSetCameraParams([CAMERA_ACTIVE, TRUE, CAMERA_POSITION, p, CAMERA_FOCUS, f,
        CAMERA_POSITION_LOCKED, TRUE, CAMERA_FOCUS_LOCKED, TRUE, CAMERA_POSITION_LAG, lag, CAMERA_FOCUS_LAG, lag,
        CAMERA_POSITION_THRESHOLD, 0.0, CAMERA_FOCUS_THRESHOLD, 0.0]);
}

say(key k, string m)
{
    llRegionSayTo(k, SYNC_CH, "T12|" + m);
}

all(string m)
{
    integer i;
    for (i = 0; i < llGetListLength(gWatchers); i++) say(llList2Key(gWatchers, i), m);
}

integer near(key k)
{
    list d = llGetObjectDetails(k, [OBJECT_POS]);
    return (llGetListLength(d) > 0 && llVecDist(llList2Vector(d, 0), llGetPos()) <= NEAR);
}

list    gW;                  // the viewers on a Take 12 Watch ("join|W"): they cannot lead
drop(key k)
{
    integer w = llListFindList(gW, [k]);
    if (w >= 0) gW = llDeleteSubList(gW, w, w);
    integer i = llListFindList(gWatchers, [k]);
    if (i >= 0)
    {
        gWatchers = llDeleteSubList(gWatchers, i, i);
        gSeen = llDeleteSubList(gSeen, i, i);
    }
    i = llListFindList(gAway, [k]);
    if (i >= 0) gAway = llDeleteSubList(gAway, i, i);
}

// ---- the panels --------------------------------------------------------------
// ask who is near; the IDLE (or Invite more) panel opens when they have answered
who()
{
    llRegionSay(SYNC_CH, "T12|who|" + name(gOwner));
    gNear = [];
    gWhoT = llGetTime();
    show("Looking for people near you…");
}

// the Connect panel is drawn by connect.lsl: it gets what it needs, when it should open
ui(string page)
{
    llMessageLinked(LINK_SET, SHARE_UI, (string)gCamOn + "|" + page, "");
}

panel()
{
    if (gSharing) ui("live|" + llDumpList2String(gWatchers, ",") + "|" + llDumpList2String(gW, ","));
    else if (gHost != NULL_KEY) ui("view|" + (string)gHost + "|" + (string)gHeld);
    else if (gPendT) ui("inv|" + (string)gOffer);
    else who();
}

// your turn: your last camera (Scenery is the idle double-tap's: Us instead); starting it asks the hub for the lead
film()
{
    string m = gMyMode;
    if (m == "scenery") m = "sharecam";
    llMessageLinked(LINK_SET, CMD, m, "");
}

// a choice in the Connect panel (connect.lsl) or a key (keys.lsl)
act(string s)
{
    list A = llParseString2List(s, ["|"], []);
    string a = llList2String(A, 0);
    key k = (key)llList2String(A, 1);
    if (a == "everyone") golive(TRUE);
    else if (a == "connect")                                // connect one: you hold the connection for them
    {
        golive(FALSE);
        if (gSharing) invite(k);
    }
    else if (a == "join") watch(k);
    else if (a == "who") who();
    else if (a == "film") film();
    else if (a == "next" && gHost != NULL_KEY) say(gHost, "next");
    else if (a == "next") llMessageLinked(LINK_SET, CMD, "next", "");
    else if (a == "disconnect") disconnect();
    else if (a == "end") endlive("Disconnected");
    else if (a == "panel") panel();
    else if (a == "accept" && gPendT) watch(gOffer);
    else if (a == "no") unpend();
    else if (a == "note") note(llList2String(A, 1));
}

// Disconnect: a viewer just leaves; the hub hands the others on to another Take 12, or (only Watches left) asks first
disconnect()
{
    if (gHost != NULL_KEY)
    {
        leave(TRUE, TRUE);
        show("Disconnected");
        return;
    }
    if (!gSharing) return;
    integer i;
    for (i = 0; i < llGetListLength(gWatchers); i++)
        if (llListFindList(gW, [llList2Key(gWatchers, i)]) < 0)
        {
            handOn(llList2Key(gWatchers, i));
            return;
        }
    if (gWatchers == []) endlive("Disconnected");
    else ui("end|" + llDumpList2String(gWatchers, ","));
}

// ---- directing -----------------------------------------------------------------
invite(key k)
{
    if (llListFindList(gInv, [k]) >= 0 || llListFindList(gWatchers, [k]) >= 0) return;
    say(k, "invite|" + name(gOwner));
    gInv += [k];
    gInvT = llGetUnixTime();
}

// you hold the connection (no camera is started: connecting is not filming); with "everyone", all the free people found
// are asked
golive(integer everyone)
{
    if (!gSharing && llGetUnixTime() - gToggleT < 2) return;
    gToggleT = llGetUnixTime();
    gSharing = TRUE;
    gHbT = llGetUnixTime();
    integer i;
    if (everyone)
        for (i = 0; i < llGetListLength(gNear); i += 2)
            if (llList2String(llParseStringKeepNulls(llList2String(gNear, i + 1), ["~"], []), 1) == "idle") invite(llList2Key(gNear, i));
    refresh();
}

endlive(string why)
{
    if (!gSharing && gWatchers == []) return;
    all("end");
    gWatchers = [];
    gSeen = [];
    gAway = [];
    gW = [];
    gSharing = FALSE;
    gToggleT = llGetUnixTime();
    show(why);
    refresh();
}

// whoever films leads: a viewer's camera started, so everyone (you too) follows theirs
grant(key k)
{
    drop(k);
    say(k, "lead|1");
    all("director|" + (string)k + "|" + name(k));
    gWatchers = [];
    gSeen = [];
    gAway = [];
    gW = [];
    gSharing = FALSE;
    gHand = gCamOn;
    watch(k);                                               // (it stops your camera)
    show(sn(k) + " films now");
}

// you leave; another Take 12 holds the connection for the others ("lead|2": no camera is started for them)
handOn(key k)
{
    drop(k);
    say(k, "lead|2");
    all("director|" + (string)k + "|" + name(k));
    gWatchers = [];
    gSeen = [];
    gAway = [];
    gW = [];
    gSharing = FALSE;
    gToggleT = llGetUnixTime();
    show("Disconnected · " + sn(k) + " keeps the others connected");
    refresh();
}

// ---- viewing -------------------------------------------------------------------
// an invite nobody took up: the double-tap is yours again
unpend()
{
    if (!gPendT) return;
    gPendT = 0;
    if (gHost == NULL_KEY) llMessageLinked(LINK_SET, CMD, "unwatch", "");
    refresh();
}

watch(key host)
{
    gPendT = 0;
    gHost = host;
    gHeld = FALSE;
    gCam = "";
    gIsAway = FALSE;
    gAskT = 0;
    gOwnT = 0.0;
    gApplied = ZERO_VECTOR;
    gHearT = llGetUnixTime();
    say(host, "join");
    if (llGetPermissions() & PERMISSION_TAKE_CONTROLS) llTakeControls(831, TRUE, TRUE);   // any movement key: your camera back
    llMessageLinked(LINK_SET, CMD, "watch", "");
    if (gCamOn) llMessageLinked(LINK_SET, CMD, "stop", "");    // viewing never runs your own camera too
    show("Connected with " + sn(host) + "\nwhoever films, the others see it");
}

leave(integer tell, integer clear)
{
    if (gHost == NULL_KEY) return;
    if (tell) say(gHost, "leave");
    gHost = NULL_KEY;
    gHeld = FALSE;
    gCam = "";
    gAskT = 0;
    gOwnT = 0.0;
    // taking the HUD off: Second Life has already withdrawn the camera and gives it back by itself
    clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;
    if (clear && (llGetPermissions() & PERMISSION_CONTROL_CAMERA)) llClearCameraParams();
    if (clear && (llGetPermissions() & PERMISSION_TAKE_CONTROLS)) llTakeControls(831, FALSE, TRUE);   // keys are yours again (the permission stays)
    llMessageLinked(LINK_SET, CMD, "unwatch", "");
    refresh();
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        llListen(SYNC_CH, "", NULL_KEY, "");
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_CONTROL_CAMERA | PERMISSION_TAKE_CONTROLS | PERMISSION_TRACK_CAMERA);
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "sync");
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
        if (c & CHANGED_REGION)                             // a connection does not cross regions
        {
            unpend();
            leave(FALSE, TRUE);
            endlive("Disconnected (new region)");
        }
    }

    attach(key id)
    {
        if (id != NULL_KEY) return;
        leave(TRUE, FALSE);                                 // taken off: tell the director, or your viewers
        endlive("");
    }

    // a movement key while watching: your own camera for a moment (you stay connected); OWN s still and it is back
    control(key id, integer level, integer edge)
    {
        if (gHost == NULL_KEY || gAskT || !(level | edge)) return;     // (taking the camera: it is your own already)
        if (gOwnT == 0.0)
        {
            if (llGetPermissions() & PERMISSION_CONTROL_CAMERA) llClearCameraParams();
            say(gHost, "away");
            gOwnT = llGetTime();
            refresh();
        }
        gOwnT = llGetTime();
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == CAMSET)
        {
            gLastCam = str;
            all("cam|" + str);
        }
        else if (num == START)                              // your own camera starts: watching, it is your turn
        {
            gCamOn = TRUE;
            gMyMode = llList2String(llParseString2List(str, ["|"], []), 0);
            unpend();
            if (gHost != NULL_KEY && !gAskT)
            {
                say(gHost, "ask");                          // the hub hands over: everyone follows you
                gAskT = llGetUnixTime();
                refresh();
            }
        }
        else if (num == STOP && str != "switch")
        {
            // your camera stopping (Stop, a movement key in Scenery, typing) never disconnects: nobody films now, and
            // everyone has their own camera until someone films again. Only Disconnect ends it.
            gCamOn = FALSE;
            if (gHand) gHand = FALSE;                       // you handed the camera on: not the end
            else if (gSharing)
            {
                all("pause");
                show("Nobody films now · everyone has their own camera\ndouble-tap: film again");
            }
        }
        else if (num == CMD && str == "share") panel();     // hold the HUD button, or Connect in the menu
        else if (num == SHARE_DO) act(str);
        else if (num == CMD && str == "scenery" && gHost != NULL_KEY && gHeld) film();       // double-tap, nobody films: you do
        else if (num == CMD && str == "scenery" && gHost != NULL_KEY) say(gHost, "next");    // double-tap while watching
        else if (num == CMD && str == "scenery" && gPendT) watch(gOffer);                    // double-tap: accept the invite
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "sync");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/sync] v" + VERSION + " hub " + (string)gSharing + ", connected with you: " + (string)llGetListLength(gWatchers)
                + ", following " + name(gHost) + ", free mem " + (string)llGetFreeMemory());
    }

    listen(integer ch, string name, key id, string msg)
    {
        // the share channel: only what an avatar's own HUD says counts
        if (llGetSubString(msg, 0, 3) != "T12|") return;
        key who = llGetOwnerKey(id);
        if (who == gOwner) return;
        list L = llParseStringKeepNulls(msg, ["|"], []);
        string w = llList2String(L, 1);
        integer wi = llListFindList(gWatchers, [who]);
        if (wi >= 0) gSeen = llListReplaceList(gSeen, [llGetUnixTime()], wi, wi);   // a viewer's word: still connected
        if (w == "who")
        {
            if (!near(who)) return;
            string st = "idle";
            string d = "";
            if (gSharing) st = "live";
            else if (gHost != NULL_KEY) { st = "view"; d = name(gHost); }
            else if (gPendT) st = "pend";
            say(who, "here|T|" + st + "|" + d);
        }
        else if (w == "here")
        {
            if (gWhoT > 0.0 && llListFindList(gNear, [who]) < 0 && near(who)) gNear += [who, llDumpList2String(llList2List(L, 2, 4), "~")];
        }
        else if (w == "invite")
        {
            if (gSharing) say(who, "busy|connected");
            else if (gHost != NULL_KEY) say(who, "busy|connected with " + sn(gHost));
            else if (near(who))
            {
                // someone in your Friends: connected at once. Anyone else: asked, so no stranger takes your camera
                if (llSubStringIndex(llLinksetDataReadProtected("cin.friends", PASS), (string)who) >= 0)
                {
                    say(who, "ack|1");
                    watch(who);
                }
                else
                {
                    say(who, "ack|0");
                    if (!gPendT) llMessageLinked(LINK_SET, CMD, "watch", "");     // core: keep the double-tap for this
                    gOffer = who;
                    gPendT = llGetUnixTime();
                    quiet();
                }
            }
        }
        else if (w == "ack" || w == "busy")
        {
            integer i = llListFindList(gInv, [who]);
            if (i < 0) return;
            gInv = llDeleteSubList(gInv, i, i);
            if (w == "busy") gRes += [sn(who) + " is busy (" + llList2String(L, 2) + ")"];
            else if (llList2String(L, 2) == "1") gRes += [sn(who) + " connected"];
            else gRes += [sn(who) + " is asked"];
        }
        else if (w == "join")
        {
            if (!gSharing && gHost != NULL_KEY)             // the lead moved on meanwhile: point them to whoever films
            {
                say(who, "director|" + (string)gHost + "|" + name(gHost));
                return;
            }
            if (!gSharing) { say(who, "end"); return; }     // only a held connection can be joined (a late yes after Disconnect)
            if (llList2String(L, 2) == "W" && llListFindList(gW, [who]) < 0) gW += [who];
            if (llListFindList(gWatchers, [who]) < 0)
            {
                gWatchers += [who];
                gSeen += [llGetUnixTime()];
            }
            show(sn(who) + " connected");
            if (!gCamOn) say(who, "pause");                 // nobody films: their own camera, connected
            else if (gLastCam != "") say(who, "cam|" + gLastCam);
        }
        else if (w == "leave" && llListFindList(gWatchers, [who]) >= 0)
        {
            drop(who);
            show(sn(who) + " disconnected");
        }
        else if (w == "away" && llListFindList(gWatchers, [who]) >= 0)
        {
            if (llListFindList(gAway, [who]) < 0) gAway += [who];
            show(sn(who) + " has their own camera");
        }
        else if (w == "back" && llListFindList(gAway, [who]) >= 0)
        {
            integer i = llListFindList(gAway, [who]);
            gAway = llDeleteSubList(gAway, i, i);
            show(sn(who) + " is back");
        }
        else if (w == "next" && llListFindList(gWatchers, [who]) >= 0 && llGetUnixTime() - gNextT >= NEXT_GAP)
        {
            gNextT = llGetUnixTime();
            llMessageLinked(LINK_SET, CMD, "next", "");
        }
        else if (w == "ask" && llListFindList(gWatchers, [who]) >= 0 && llListFindList(gW, [who]) < 0) grant(who);   // their camera started: they lead
        else if (wi >= 0 && w == "hb") return;            // a viewer's heartbeat (seen above)
        else if (who != gHost) return;
        // from the director you follow
        else if (w == "cam" && (llGetPermissions() & PERMISSION_CONTROL_CAMERA))
        {
            gHearT = llGetUnixTime();
            gCam = llDumpList2String(llList2List(L, 2, -1), "|");    // pos | focus | lag | their lens (6.0.1)
            if (gHeld) { gHeld = FALSE; refresh(); }            // someone films again
            if (!gAskT && gOwnT == 0.0) place(FALSE);           // (your own camera, or yours for a moment: kept)
        }
        else if (w == "hb") gHearT = llGetUnixTime();
        else if (w == "pause")
        {
            gHearT = llGetUnixTime();
            gHeld = TRUE;                                   // nobody films: your own camera, still connected
            if (!gAskT && (llGetPermissions() & PERMISSION_CONTROL_CAMERA)) llClearCameraParams();
            refresh();
        }
        else if (w == "lead")
        {
            gAskT = 0;
            string v = llList2String(L, 2);
            string n = sn(gHost);
            if (v == "0")                                   // an older Take 12 kept it: you film on your own
            {
                leave(TRUE, FALSE);
                show(n + " kept the camera (an older Take 12): disconnected");
                return;
            }
            leave(FALSE, v == "2");                         // 1: your camera runs, keep it; 2: you were watching
            if (llGetPermissions() & PERMISSION_TAKE_CONTROLS) llTakeControls(831, FALSE, TRUE);
            gToggleT = 0;
            golive(FALSE);                                  // you hold the connection now
            if (v == "2") show(n + " disconnected · you keep the others connected");
            else show("You film · everyone connected sees it");
        }
        else if (w == "director")
        {
            gHost = (key)llList2String(L, 2);              // the director changed: follow the new one
            gHeld = FALSE;
            if (llListFindList(gBook, [gHost]) < 0) gBook += [gHost, llList2String(L, 3)];
            gIsAway = FALSE;
            gApplied = ZERO_VECTOR;
            gHearT = llGetUnixTime();
            say(gHost, "join");
            if (gAskT) say(gHost, "ask");                   // you started a camera meanwhile: ask the new one
            show(llList2String(L, 3) + " films now");
        }
        else if (w == "kick")
        {
            string n = sn(gHost);
            leave(FALSE, TRUE);
            show(n + " disconnected you");
        }
        else if (w == "end")
        {
            string n = sn(gHost);
            leave(FALSE, TRUE);
            show(n + " disconnected");
        }
    }

    timer()
    {
        integer now = llGetUnixTime();
        if (gWhoT > 0.0 && llGetTime() - gWhoT > 1.5)
        {
            gWhoT = 0.0;                                    // the "who" check is in: the panel
            quiet();
            ui("near|" + (string)gSharing + "|" + llDumpList2String(gWatchers, ",") + "|" + llDumpList2String(gNear, ","));
        }
        if (gInv != [] && now - gInvT >= 3)
        {
            integer i;
            for (i = 0; i < llGetListLength(gInv); i++) gRes += [sn(llList2Key(gInv, i)) + " didn't answer (out of range or HUD off)"];
            gInv = [];
        }
        if (gRes != [] && gInv == [])
        {
            note(llDumpList2String(gRes, " · "));
            gRes = [];
        }
        if (gPendT && now - gPendT > WAIT) unpend();
        if (gAskT && now - gAskT > WAIT)
        {
            gAskT = 0;                                      // no hand-over (an older Take 12): you film on your own
            leave(TRUE, FALSE);
            show("No answer: you film on your own (disconnected)");
        }
        if (gOwnT > 0.0 && llGetTime() - gOwnT > OWN && gHost != NULL_KEY)
        {
            gOwnT = 0.0;                                    // still again: back on the shared view
            say(gHost, "back");
            if (gCam != "" && !gHeld && !gAskT) place(FALSE);
            refresh();
        }
        // directing: a heartbeat, and anyone who has left the region leaves the roster
        if (gSharing && now - gHbT >= 10)
        {
            gHbT = now;
            all("hb");
            integer i;
            for (i = llGetListLength(gWatchers) - 1; i >= 0; i--)
            {
                key k = llList2Key(gWatchers, i);
                if (llGetAgentSize(k) == ZERO_VECTOR)
                {
                    drop(k);
                    show(sn(k) + " disconnected");
                }
                else if (now - llList2Integer(gSeen, i) > LOST)
                {
                    drop(k);
                    show(sn(k) + " lost the connection");
                }
            }
        }
        // viewing: the director gone quiet; your own camera (Alt-orbit) = looking around, Esc brings you back
        if (gHost != NULL_KEY && gCam != "" && llFabs(llGetCameraFOV() - gMyFov) > 0.004) place(TRUE);   // you zoomed: same picture
        if (gHost != NULL_KEY && now - gBeatT >= 10)
        {
            gBeatT = now;
            say(gHost, "hb");                               // your heartbeat: the director sees you are connected
        }
        if (gHost != NULL_KEY)
        {
            if (now - gHearT > GONE)
            {
                string n = sn(gHost);
                leave(FALSE, TRUE);
                show(n + " is gone · disconnected");
            }
            else if (gApplied != ZERO_VECTOR && gOwnT == 0.0 && !gHeld && !gAskT && llGetTime() > gApplyT && (llGetPermissions() & PERMISSION_TRACK_CAMERA))
            {
                float d = llVecDist(llGetCameraPos(), gApplied);
                if (!gIsAway && d > 0.6)
                {
                    gIsAway = TRUE;
                    say(gHost, "away");
                    refresh();
                }
                else if (gIsAway && d < 0.3)
                {
                    gIsAway = FALSE;
                    say(gHost, "back");
                    refresh();
                }
            }
        }
        if (gTextT > 0.0 && llGetTime() - gTextT > 4.0) quiet();       // the notice gives way to the state again
        else refresh();                                                 // keep the state current ("no signal")
        if (ind() == "" && gTextT == 0.0 && gWhoT == 0.0 && gInv == [] && gRes == [])
            llSetTimerEvent(0.0);
    }
}
