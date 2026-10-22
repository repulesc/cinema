// ============================================================================
//  Take 12  -  sync.lsl  (v5.5)  - the sharing manager
//  Hold the HUD button: the Share panel, whatever you are doing. One director at a time; any number of viewers.
//    IDLE      who is near (a quick "who" check), Go live, + <name> (invite one), Watch <live director>, Give Watch
//    LIVE      who watches / looks around, Invite more, Roster (Pass camera, Remove), Lead: Ask/Always/Never, End live
//    VIEWING   Ask to lead, Leave
//    INVITED   Watch, No (a double-tap also watches)
//  Go live with the camera off starts Social. A Take 12 Watch, or Take 12 with you in its Friends, joins an invite at
//  once; anyone else is asked. Above the HUD the state stays visible: "● LIVE · 2", "👁 Pano", "Pano invites you".
//  Channel SYNC_CH, messages "T12|<what>|...":
//    who|<name> (llRegionSay) -> here|<T/W>|<idle/live/view/pend>|<director name>
//    invite|<name> -> ack|1 (joined) / ack|0 (asked) / busy|<what>
//    viewer -> director: join leave next away back ask        director -> viewer: cam|<pos>|<focus>|<lag> hb lead|<1/0>
//    director|<key>|<name> (a hand-over) kick end
//  Full description: docs/SHARING.md. Checked in tools/sim/sync_sim.py.
// ============================================================================

string VERSION = "6.0.1";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer CAMSET     = 7325;   // core -> sync  "<pos>|<focus>|<lag>|<lens>" (6.0.1: viewers place it through their own lens)
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer TEXT       = 7380;   // sync -> tips  "<live/view/inv or empty>|<the state above the HUD>"
integer SYNC_CH    = -7712120;   // Take 12 and Take 12 Watch share this channel
float   NEAR       = 20.0;       // m  who is found and invited
integer NEXT_GAP   = 5;          // s  two viewers' double-taps close together cut once
integer WAIT       = 20;         // s  an invite or a lead request waits this long
integer GONE       = 25;         // s  no camera and no heartbeat from the director: it is gone
integer QUIET      = 25;         // s  a viewer not heard from this long shows "(no signal)"...
integer LOST       = 45;         // s  ... and this long is dropped
integer gBeatT;              // viewing: your last heartbeat to the director
string  WATCH      = "Take 12 Watch";
list    LEADS      = ["Ask", "Always", "Never"];

key     gOwner;
integer gSharing;            // LIVE: you direct
integer gCamOn;              // your own camera runs
integer gHand;               // you just handed the camera over: your stop is not the end
integer gToggleT;            // Go live / End live: repeats within 2 s are ignored
list    gWatchers;           // LIVE: who watches you
list    gSeen;               // ... when each was last heard from (their heartbeat), same order as gWatchers
list    gAway;               // ... and who of them is looking around
integer gNextT;              // ... the last "next" asked
integer gHbT;                // ... the last heartbeat and roster check
string  gLastCam;            // the camera on your screen now
integer gLead;               // 0 Ask, 1 Always, 2 Never
key     gLeadAsk;            // a viewer asking to lead
integer gLeadT;
list    gInv;                // invited, no answer yet
list    gRes;                // ... the answers
integer gInvT;
key     gHost;               // VIEWING: whose view you follow
vector  gApplied;            // ... the camera last set from it
float   gApplyT;             // ... and until when it may still be moving there
integer gIsAway;             // ... you are looking around on your own
integer gHearT;              // ... the last word from the director
integer gAskT;               // ... your own lead request, waiting
key     gOffer;              // INVITED by
integer gPendT;              // ... since
list    gNear;               // the "who" check: [key, "<T/W>|<state>|<director>", ...]
float   gWhoT;               // ... sent at (0 = none running)
string  gPage;               // our own dialog
list    gBtn;                // ... [label, key, ...]
key     gSel;                // roster: the viewer picked
integer gDlg;
integer gDlgL;
integer gDlgT;
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

// at most m bytes (a dialog button: 24, a dialog text: 512); emoji are 4 bytes, "·" 2
string fit(string s, integer m)
{
    if (llStringLength(s) > m) s = llGetSubString(s, 0, m - 1);
    while (TRUE)
    {
        string b = llStringToBase64(s);
        integer n = llStringLength(b) * 3 / 4 - (llGetSubString(b, -1, -1) == "=") - (llGetSubString(b, -2, -1) == "==");
        if (n <= m) return s;
        s = llDeleteSubString(s, -1, -1);
    }
    return s;
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
        // who is connected to your camera, live: names, looking around, no signal
        integer n = llGetListLength(gWatchers);
        if (n == 0) return "● LIVE · nobody watching yet";
        list s = [];
        integer i;
        for (i = 0; i < n && i < 4; i++)
        {
            key k = llList2Key(gWatchers, i);
            string t = sn(k);
            if (now - llList2Integer(gSeen, i) > QUIET) t += " (no signal)";
            else if (llListFindList(gAway, [k]) >= 0) t += " (looking around)";
            s += [t];
        }
        string r = "● LIVE · " + (string)n + " watching\n" + llDumpList2String(s, " · ");
        if (n > 4) r += " · +" + (string)(n - 4);
        return r;
    }
    if (gHost != NULL_KEY)
    {
        if (now - gHearT > 15) return "👁 " + sn(gHost) + " · no signal…";
        if (gIsAway) return "👁 " + sn(gHost) + " · looking around (Esc: back)";
        return "👁 " + sn(gHost);
    }
    if (gPendT) return name(gOffer) + " invites you · hold to watch";
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

dialog(string page, string text, list b)
{
    gPage = page;
    llListenRemove(gDlgL);
    gDlg = -1000000 - (integer)llFrand(1000000.0);
    gDlgL = llListen(gDlg, "", gOwner, "");
    gDlgT = llGetUnixTime();
    llDialog(gOwner, fit(text, 500), b, gDlg);
    llSetTimerEvent(1.0);
}

integer near(key k)
{
    list d = llGetObjectDetails(k, [OBJECT_POS]);
    return (llGetListLength(d) > 0 && llVecDist(llList2Vector(d, 0), llGetPos()) <= NEAR);
}


string names(list ks)
{
    list n = [];
    integer i;
    for (i = 0; i < llGetListLength(ks); i++) n += [name(llList2Key(ks, i))];
    return llDumpList2String(n, ", ");
}

// a label in the menu style chosen in Options > Look: Plain (words), Symbols (a quiet mark), Color (emoji)
string lb(string e, string m, string t)
{
    integer k = (integer)llLinksetDataReadProtected("cin.skin", PASS);
    if (k == 2) return e + " " + t;
    if (k == 1) return m + " " + t;
    return t;
}

// a button for a person: the label, and who it stands for
btn(string label, key k)
{
    gBtn += [label, k];
}

key btnKey(string label)
{
    integer i = llListFindList(gBtn, [label]);
    if (i < 0) return NULL_KEY;
    return llList2Key(gBtn, i + 1);
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

panelNear()
{
    gBtn = [];
    list b = [];
    list desc = [];
    if (gSharing) b = ["Invite all"];
    else b = [lb("🔴", "●", "Go live")];
    integer i;
    for (i = 0; i < llGetListLength(gNear); i += 2)
    {
        key k = llList2Key(gNear, i);
        list I = llParseStringKeepNulls(llList2String(gNear, i + 1), ["|"], []);
        string st = llList2String(I, 1);
        string d = name(k);
        if (llList2String(I, 0) == "W") d += " (Watch)";
        if (st == "live") d += " (live)";
        else if (st == "view") d += " (watching " + llList2String(I, 2) + ")";
        desc += [d];
        if (llGetListLength(b) < 9)
        {
            string wl = fit(lb("👁", "◉", "Watch") + " " + sn(k), 24);
            if ((integer)llLinksetDataReadProtected("cin.skin", PASS)) wl = fit(lb("👁", "◉", sn(k)), 24);
            string al = fit("+ " + sn(k), 24);
            if (st == "live" && !gSharing) { b += [wl]; btn(wl, k); }
            else if (st == "idle" && llListFindList(gWatchers, [k]) < 0) { b += [al]; btn(al, k); }
        }
    }
    string t = "Share your view.";
    if (gSharing) t = "Invite more people.";
    if (desc == []) t += "\nNobody near you wears Take 12 or Take 12 Watch yet.";
    else t += "\nNear you: " + llDumpList2String(desc, ", ");
    t += "\n+ name: invite one";
    dialog("near", t, b + ["Give Watch", lb("⋯", "⋯", "More"), "Close"]);
}

panel()
{
    if (gSharing)
    {
        string t = lb("🔴", "●", "LIVE") + " · ";
        if (gWatchers == []) t += "nobody watches yet";
        else t += "watching: " + names(gWatchers);
        if (gAway != []) t += "\nlooking around: " + names(gAway);
        t += "\nWhen someone asks to lead: " + llList2String(LEADS, gLead);
        dialog("live", t, ["Invite more", "Roster", "Lead: " + llList2String(LEADS, gLead), "End live", lb("⋯", "⋯", "More"), "Close"]);
    }
    else if (gHost != NULL_KEY)
    {
        string t = "Viewing " + name(gHost) + "'s camera.";
        if (gAskT) t += "\nYou asked to lead; waiting for an answer.";
        dialog("view", t, ["Ask to lead", "Leave", lb("⋯", "⋯", "More"), "Close"]);
    }
    else if (gPendT) dialog("invited", name(gOffer) + " invites you to watch their camera.", ["Watch", "No"]);
    else who();
}

roster()
{
    gBtn = [];
    list b = [];
    integer i;
    for (i = 0; i < llGetListLength(gWatchers) && i < 11; i++)
    {
        key k = llList2Key(gWatchers, i);
        string l = fit(sn(k), 24);
        b += [l];
        btn(l, k);
    }
    if (b == []) { panel(); return; }
    dialog("roster", "Who watches you. Pick someone to pass the camera or remove them.", b + ["Back"]);
}

// ---- directing -----------------------------------------------------------------
invite(key k)
{
    if (llListFindList(gInv, [k]) >= 0 || llListFindList(gWatchers, [k]) >= 0) return;
    say(k, "invite|" + name(gOwner));
    gInv += [k];
    gInvT = llGetUnixTime();
}

// your camera becomes the shared one; with "everyone", all the free people found are invited
golive(integer everyone)
{
    if (!gSharing && llGetUnixTime() - gToggleT < 2) return;
    gToggleT = llGetUnixTime();
    gSharing = TRUE;
    gHbT = llGetUnixTime();
    if (!gCamOn) llMessageLinked(LINK_SET, CMD, "sharecam", "");    // core: Social
    integer i;
    if (everyone)
        for (i = 0; i < llGetListLength(gNear); i += 2)
            if (llList2String(llParseStringKeepNulls(llList2String(gNear, i + 1), ["|"], []), 1) == "idle") invite(llList2Key(gNear, i));
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
    if (gLeadAsk != NULL_KEY) say(gLeadAsk, "lead|0");
    gLeadAsk = NULL_KEY;
    show(why);
    refresh();
}

// hand the camera to a viewer: everyone (you too) follows them
grant(key k)
{
    gLeadAsk = NULL_KEY;
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
    show(name(k) + " leads now");
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
    gCam = "";
    gIsAway = FALSE;
    gAskT = 0;
    gApplied = ZERO_VECTOR;
    gHearT = llGetUnixTime();
    say(host, "join");
    if (llGetPermissions() & PERMISSION_TAKE_CONTROLS) llTakeControls(831, TRUE, TRUE);   // any movement key: your camera back
    llMessageLinked(LINK_SET, CMD, "watch", "");
    if (gCamOn) llMessageLinked(LINK_SET, CMD, "stop", "");    // viewing never runs your own camera too
    show("Watching " + name(host) + "\ndouble-tap: next for all · any key: your camera");
}

leave(integer tell, integer clear)
{
    if (gHost == NULL_KEY) return;
    if (tell) say(gHost, "leave");
    gHost = NULL_KEY;
    gCam = "";
    gAskT = 0;
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
        gLead = llListFindList(LEADS, [llLinksetDataReadProtected("cin.share_lead", PASS)]);
        if (gLead < 0) gLead = 0;
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
        if (c & CHANGED_REGION)                             // sharing does not cross regions
        {
            unpend();
            leave(FALSE, TRUE);
            endlive("Sharing ended (new region)");
        }
    }

    attach(key id)
    {
        if (id != NULL_KEY) return;
        leave(TRUE, FALSE);                                 // taken off: tell the director, or your viewers
        endlive("");
    }

    control(key id, integer level, integer edge)
    {
        if (edge & level) leave(TRUE, TRUE);
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == CAMSET)
        {
            gLastCam = str;
            all("cam|" + str);
        }
        else if (num == START)                              // your own camera starts: stop viewing
        {
            gCamOn = TRUE;
            unpend();
            leave(TRUE, TRUE);
        }
        else if (num == STOP && str != "switch")
        {
            gCamOn = FALSE;
            gLastCam = "";
            if (gHand) gHand = FALSE;                       // you handed the camera on: not the end
            else endlive("Live view ended");
        }
        else if (num == CMD && str == "share") panel();     // hold the HUD button
        else if (num == CMD && str == "scenery" && gHost != NULL_KEY) say(gHost, "next");    // double-tap while viewing
        else if (num == CMD && str == "scenery" && gPendT) watch(gOffer);                    // double-tap: accept the invite
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "sync");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/sync] v" + VERSION + " live " + (string)gSharing + ", watching you: " + names(gWatchers)
                + ", following " + name(gHost) + ", lead " + llList2String(LEADS, gLead) + ", free mem " + (string)llGetFreeMemory());
    }

    listen(integer ch, string name, key id, string msg)
    {
        if (ch == gDlg)
        {
            llListenRemove(gDlgL);
            gDlgT = 0;
            if (msg == lb("⋯", "⋯", "More"))
            {
                if (gCamOn) llMessageLinked(LINK_SET, CMD, "livemenu", "");
                else llMessageLinked(LINK_SET, CMD, "mainmenu", "");
            }
            else if (gPage == "near")
            {
                if (msg == lb("🔴", "●", "Go live")) golive(TRUE);
                else if (msg == "Invite all") golive(TRUE);
                else if (msg == "Give Watch")
                {
                    if (llGetInventoryType(WATCH) != INVENTORY_OBJECT)
                    {
                        llOwnerSay("[Take 12] Put the \"" + WATCH + "\" object in the HUD to give it out.");
                        return;
                    }
                    list ids = llGetAgentList(AGENT_LIST_REGION, []);
                    list b = [];
                    gBtn = [];
                    integer i;
                    for (i = 0; i < llGetListLength(ids) && llGetListLength(b) < 11; i++)
                    {
                        key k = llList2Key(ids, i);
                        if (k != gOwner && near(k))
                        {
                            string l = fit(sn(k), 24);
                            b += [l];
                            btn(l, k);
                        }
                    }
                    if (b == []) note("Nobody within " + (string)llRound(NEAR) + " m.");
                    else dialog("give", "Give the free Take 12 Watch to:", b);
                }
                else
                {
                    key k = btnKey(msg);
                    if (k == NULL_KEY) return;
                    if (llGetSubString(msg, 0, 0) == "+")   // invite one: you go live for them
                    {
                        golive(FALSE);
                        if (gSharing) invite(k);
                    }
                    else watch(k);                          // a live director near you: watch them
                }
            }
            else if (gPage == "live")
            {
                if (msg == "Invite more") who();
                else if (msg == "Roster") roster();
                else if (msg == "End live") endlive("Live view ended");
                else if (llGetSubString(msg, 0, 4) == "Lead:")
                {
                    gLead = (gLead + 1) % 3;
                    llLinksetDataWriteProtected("cin.share_lead", llList2String(LEADS, gLead), PASS);
                    panel();
                }
            }
            else if (gPage == "roster")
            {
                if (msg == "Back") { panel(); return; }
                gSel = btnKey(msg);
                if (llListFindList(gW, [gSel]) >= 0) dialog("person", name(gSel) + " (Take 12 Watch: cannot lead)", ["Remove", "Back"]);
                else if (gSel != NULL_KEY) dialog("person", name(gSel), ["Pass camera", "Remove", "Back"]);
            }
            else if (gPage == "person" && llListFindList(gWatchers, [gSel]) >= 0)
            {
                if (msg == "Pass camera") grant(gSel);
                else if (msg == "Remove")
                {
                    say(gSel, "kick");
                    drop(gSel);
                    show(name(gSel) + " removed");
                    refresh();
                }
                else roster();
            }
            else if (gPage == "lead" && gLeadAsk != NULL_KEY)
            {
                if (msg == "Allow" && llListFindList(gWatchers, [gLeadAsk]) >= 0) grant(gLeadAsk);
                else
                {
                    say(gLeadAsk, "lead|0");
                    gLeadAsk = NULL_KEY;
                }
            }
            else if (gPage == "view" && gHost != NULL_KEY)
            {
                if (msg == "Leave") leave(TRUE, TRUE);
                else if (msg == "Ask to lead" && !gAskT)
                {
                    say(gHost, "ask");
                    gAskT = llGetUnixTime();
                    show("Asked " + name(gHost) + " to lead…");
                }
            }
            else if (gPage == "invited" && gPendT)
            {
                if (msg == "Watch") watch(gOffer);
                else unpend();
            }
            else if (gPage == "give")
            {
                key k = btnKey(msg);
                if (k == NULL_KEY) return;
                llGiveInventory(k, WATCH);
                note("Take 12 Watch given to " + name(k) + ". Once they wear it, hold your button > Go live.");
            }
            return;
        }
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
            if (gWhoT > 0.0 && llListFindList(gNear, [who]) < 0 && near(who)) gNear += [who, llDumpList2String(llList2List(L, 2, 4), "|")];
        }
        else if (w == "invite")
        {
            if (gSharing) say(who, "busy|live");
            else if (gHost != NULL_KEY) say(who, "busy|watching " + name(gHost));
            else if (near(who))
            {
                // someone in your Friends: their view at once. Anyone else: asked, so no stranger takes your camera
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
            if (w == "busy") gRes += [name(who) + " is busy (" + llList2String(L, 2) + ")"];
            else if (llList2String(L, 2) == "1") gRes += [name(who) + " watches"];
            else gRes += [name(who) + " is asked"];
        }
        else if (w == "join")
        {
            if (!gSharing) { say(who, "end"); return; }     // only a live view can be joined (a late "Watch" after End live)
            if (llList2String(L, 2) == "W" && llListFindList(gW, [who]) < 0) gW += [who];
            if (llListFindList(gWatchers, [who]) < 0)
            {
                gWatchers += [who];
                gSeen += [llGetUnixTime()];
            }
            show(name(who) + " watches");
            if (gLastCam != "") say(who, "cam|" + gLastCam);
        }
        else if (w == "leave" && llListFindList(gWatchers, [who]) >= 0)
        {
            drop(who);
            show(name(who) + " left");
        }
        else if (w == "away" && llListFindList(gWatchers, [who]) >= 0)
        {
            if (llListFindList(gAway, [who]) < 0) gAway += [who];
            show(name(who) + " is looking around");
        }
        else if (w == "back" && llListFindList(gAway, [who]) >= 0)
        {
            integer i = llListFindList(gAway, [who]);
            gAway = llDeleteSubList(gAway, i, i);
            show(name(who) + " is back");
        }
        else if (w == "next" && llListFindList(gWatchers, [who]) >= 0 && llGetUnixTime() - gNextT >= NEXT_GAP)
        {
            gNextT = llGetUnixTime();
            llMessageLinked(LINK_SET, CMD, "next", "");
        }
        else if (w == "ask" && llListFindList(gWatchers, [who]) >= 0)
        {
            if (gLeadAsk != NULL_KEY || gLead == 2) say(who, "lead|0");   // Never, or someone else is already asking
            else if (gLead == 1) grant(who);
            else
            {
                gLeadAsk = who;
                gLeadT = llGetUnixTime();
                dialog("lead", name(who) + " asks to lead the camera.\nEveryone would then watch theirs.", ["Allow", "Decline"]);
            }
        }
        else if (wi >= 0 && w == "hb") return;            // a viewer's heartbeat (seen above)
        else if (who != gHost) return;
        // from the director you follow
        else if (w == "cam" && (llGetPermissions() & PERMISSION_CONTROL_CAMERA))
        {
            gHearT = llGetUnixTime();
            gCam = llDumpList2String(llList2List(L, 2, -1), "|");    // pos | focus | lag | their lens (6.0.1)
            place(FALSE);
        }
        else if (w == "hb") gHearT = llGetUnixTime();
        else if (w == "lead")
        {
            gAskT = 0;
            if (llList2String(L, 2) != "1")
            {
                show(name(gHost) + " keeps the lead");
                return;
            }
            leave(FALSE, TRUE);                             // you lead now: your camera, everyone follows it
            golive(FALSE);
            show("You lead now");
        }
        else if (w == "director")
        {
            gHost = (key)llList2String(L, 2);              // the director changed: follow the new one
            if (llListFindList(gBook, [gHost]) < 0) gBook += [gHost, llList2String(L, 3)];
            gIsAway = FALSE;
            gApplied = ZERO_VECTOR;
            gHearT = llGetUnixTime();
            say(gHost, "join");
            show(llList2String(L, 3) + " leads now");
        }
        else if (w == "kick")
        {
            string n = name(gHost);
            leave(FALSE, TRUE);
            show(n + " stopped sharing with you");
        }
        else if (w == "end")
        {
            string n = name(gHost);
            leave(FALSE, TRUE);
            show(n + " ended the live view");
        }
    }

    timer()
    {
        integer now = llGetUnixTime();
        if (gWhoT > 0.0 && llGetTime() - gWhoT > 1.5)
        {
            gWhoT = 0.0;                                    // the "who" check is in: the panel
            quiet();
            panelNear();
        }
        if (gInv != [] && now - gInvT >= 3)
        {
            integer i;
            for (i = 0; i < llGetListLength(gInv); i++) gRes += [name(llList2Key(gInv, i)) + " didn't answer (out of range or HUD off)"];
            gInv = [];
        }
        if (gRes != [] && gInv == [])
        {
            note(llDumpList2String(gRes, " · "));
            gRes = [];
        }
        if (gPendT && now - gPendT > WAIT) unpend();
        if (gLeadAsk != NULL_KEY && now - gLeadT > WAIT)
        {
            say(gLeadAsk, "lead|0");                        // no answer: declined
            gLeadAsk = NULL_KEY;
        }
        if (gAskT && now - gAskT > WAIT + 5)
        {
            gAskT = 0;
            show("No answer to your lead request");
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
                    show(name(k) + " left");
                }
                else if (now - llList2Integer(gSeen, i) > LOST)
                {
                    drop(k);
                    show(name(k) + " lost connection");
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
                string n = name(gHost);
                leave(FALSE, TRUE);
                show(n + "'s camera is gone");
            }
            else if (gApplied != ZERO_VECTOR && llGetTime() > gApplyT && (llGetPermissions() & PERMISSION_TRACK_CAMERA))
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
        if (gDlgT > 0 && now - gDlgT > 60)
        {
            gDlgT = 0;
            llListenRemove(gDlgL);
        }
        if (ind() == "" && gTextT == 0.0 && gWhoT == 0.0 && gInv == [] && gRes == [] && gDlgT == 0 && gLeadAsk == NULL_KEY)
            llSetTimerEvent(0.0);
    }
}
