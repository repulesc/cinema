// ============================================================================
//  Take 12  -  share.lsl  (v6.2)  - the Share panel (the menus of sync)
//  6.2.0: split out of sync.lsl, which ran out of memory ("Stack-Heap Collision" on hold). sync keeps the sharing
//  itself (the protocol, the roster, the camera); this script only draws its panels and hands the choice back.
//    sync -> here  SHARE_UI "<camOn>|<page>|..."  (what the panel needs to know, when it should open)
//      live|<lead 0-2>|<watchers,>|<looking around,>|<on a Watch,>    view|<host>|<asked>    inv|<from>
//      near|<live>|<watchers,>|<key,T~idle~director,...>              lead|<asker>      end|<watching> (End live asks)
//    here -> sync  SHARE_DO "golive" "invite|<key>" "watch|<key>" "who" "endask" "end" "lead" "panel" "pass|<key>" "kick|<key>"
//      "allow" "decline" "leave" "ask" "accept" "no" "note|<text>"
//  Give Watch (the free viewer HUD, from the HUD's contents) is all here. Checked in tools/sim/sync_sim.py.
// ============================================================================

string VERSION = "6.7.1";
string PASS    = "cinema-1.0-build1";

integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer SHARE_UI   = 7392;   // sync -> here: open a panel
integer SHARE_DO   = 7393;   // here -> sync: the choice
float   NEAR       = 20.0;   // m  who can be given a Watch
string  WATCH      = "Take 12 Watch";
list    LEADS      = ["Ask", "Always", "Never"];

key     gOwner;
integer gCamOn;              // your own camera runs (⋯ More opens the live menu then)
string  gPage;
list    gBtn;                // [label, key, ...]: the people on the buttons
list    gWatchers;           // the last live panel's: for the roster
list    gW;                  // ... who of them is on a Take 12 Watch (cannot lead)
key     gSel;                // the roster: the viewer picked
integer gDlg;
integer gDlgL;
integer gDlgT;

// at most m bytes (a dialog button: 24, a dialog text: 512); emoji are 4 bytes, "·" 2
string fit(string s, integer m)
{
    if (llStringLength(s) > m) s = llGetSubString(s, 0, m - 1);
    while (llStringLength(llStringToBase64(s)) * 3 / 4 - 2 > m) s = llDeleteSubString(s, -1, -1);
    return s;
}

string name(key k)
{
    string n = llKey2Name(k);
    if (n == "") n = "someone";
    return n;
}

// a short name: "Ana Resident" -> "Ana"
string sn(key k)
{
    string n = name(k);
    integer i = llSubStringIndex(n, " Resident");
    if (i > 0) n = llGetSubString(n, 0, i - 1);
    return n;
}

string names(list ks)
{
    list n = [];
    integer i;
    for (i = 0; i < llGetListLength(ks); i++) n += [name(llList2Key(ks, i))];
    return llDumpList2String(n, ", ");
}

list keys(string csv)
{
    return llParseString2List(csv, [","], []);
}

// a label in the menu style chosen in Options > Look: Plain (words), Symbols (a quiet mark), Color (emoji)
string lb(string e, string m, string t)
{
    integer k = (integer)llLinksetDataReadProtected("cin.skin", PASS);
    if (k == 2) return e + " " + t;
    if (k == 1) return m + " " + t;
    return t;
}

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

dialog(string page, string text, list b)
{
    gPage = page;
    llListenRemove(gDlgL);
    gDlg = -1000000 - (integer)llFrand(1000000.0);
    gDlgL = llListen(gDlg, "", gOwner, "");
    gDlgT = llGetUnixTime();
    llDialog(gOwner, fit(text, 500), b, gDlg);
    llSetTimerEvent(5.0);
}

go(string s)
{
    llMessageLinked(LINK_SET, SHARE_DO, s, "");
}

integer near(key k)
{
    list d = llGetObjectDetails(k, [OBJECT_POS]);
    return (llGetListLength(d) > 0 && llVecDist(llList2Vector(d, 0), llGetPos()) <= NEAR);
}

// ---- the panels --------------------------------------------------------------
open(list P)
{
    gCamOn = (integer)llList2String(P, 0);
    string p = llList2String(P, 1);
    string more = lb("⋯", "⋯", "More");
    if (p == "live")
    {
        integer lead = (integer)llList2String(P, 2);
        gWatchers = keys(llList2String(P, 3));
        list away = keys(llList2String(P, 4));
        gW = keys(llList2String(P, 5));
        string t = lb("🔴", "●", "LIVE") + " · ";
        if (gWatchers == []) t += "nobody watches yet";
        else t += "watching: " + names(gWatchers);
        if (away != []) t += "\nlooking around: " + names(away);
        t += "\nWhen someone asks to lead: " + llList2String(LEADS, lead);
        dialog("live", t, ["Invite more", "Roster", "Lead: " + llList2String(LEADS, lead), "End live", more, "Close"]);
    }
    else if (p == "view")
    {
        string t = "Viewing " + name((key)llList2String(P, 2)) + "'s camera.";
        if ((integer)llList2String(P, 3)) t += "\nYou asked to lead; waiting for an answer.";
        dialog("view", t, ["Ask to lead", "Leave", more, "Close"]);
    }
    else if (p == "inv") dialog("invited", name((key)llList2String(P, 2)) + " invites you to watch their camera.", ["Watch", "No"]);
    else if (p == "end")                                    // End live asks first: never by accident (6.5)
    {
        integer n = (integer)llList2String(P, 2);
        string t = "End the live view?\nNobody watches yet.";
        if (n == 1) t = "End the live view for the person watching?\nThey get their own camera back.";
        if (n > 1) t = "End the live view for " + (string)n + " people?\nThey get their own camera back.";
        dialog("end", t, ["End live", "Keep"]);
    }
    else if (p == "lead") dialog("lead", name((key)llList2String(P, 2)) + " asks to lead the camera.\nEveryone would then watch theirs.", ["Allow", "Decline"]);
    else if (p == "near")
    {
        integer live = (integer)llList2String(P, 2);
        list watchers = keys(llList2String(P, 3));
        list N = llParseStringKeepNulls(llList2String(P, 4), [","], []);
        gBtn = [];
        list b = [lb("🔴", "●", "Go live")];
        if (live) b = ["Invite all"];
        list desc = [];
        integer i;
        for (i = 0; i + 1 < llGetListLength(N); i += 2)
        {
            key k = (key)llList2String(N, i);
            list I = llParseStringKeepNulls(llList2String(N, i + 1), ["~"], []);
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
                if (st == "live" && !live) { b += [wl]; btn(wl, k); }
                else if (st == "idle" && llListFindList(watchers, [(string)k]) < 0) { b += [al]; btn(al, k); }
            }
        }
        string t = "Share your view.";
        if (live) t = "Invite more people.";
        if (desc == []) t += "\nNobody near you wears Take 12 or Take 12 Watch yet.";
        else t += "\nNear you: " + llDumpList2String(desc, ", ");
        t += "\n+ name: invite one";
        dialog("near", t, b + ["Give Watch", more, "Close"]);
    }
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
    if (b == []) { go("panel"); return; }
    dialog("roster", "Who watches you. Pick someone to pass the camera or remove them.", b + ["Back"]);
}

giveList()
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
    if (b == []) go("note|Nobody within " + (string)llRound(NEAR) + " m.");
    else dialog("give", "Give the free Take 12 Watch to:", b);
}

choose(string msg)
{
    if (msg == lb("⋯", "⋯", "More"))
    {
        if (gCamOn) llMessageLinked(LINK_SET, CMD, "livemenu", "");
        else llMessageLinked(LINK_SET, CMD, "mainmenu", "");
        return;
    }
    if (msg == "Close") return;
    key k = btnKey(msg);
    if (gPage == "near")
    {
        if (msg == lb("🔴", "●", "Go live") || msg == "Invite all") go("golive");
        else if (msg == "Give Watch") giveList();
        else if (k == NULL_KEY) return;
        else if (llGetSubString(msg, 0, 0) == "+") go("invite|" + (string)k);   // invite one: you go live for them
        else go("watch|" + (string)k);                                         // a live director near you: watch them
    }
    else if (gPage == "live")
    {
        if (msg == "Invite more") go("who");
        else if (msg == "Roster") roster();
        else if (msg == "End live") go("endask");
        else if (llGetSubString(msg, 0, 4) == "Lead:") go("lead");
    }
    else if (gPage == "roster")
    {
        if (msg == "Back") { go("panel"); return; }
        gSel = k;
        if (gSel == NULL_KEY) return;
        if (llListFindList(gW, [(string)gSel]) >= 0) dialog("person", name(gSel) + " (Take 12 Watch: cannot lead)", ["Remove", "Back"]);
        else dialog("person", name(gSel), ["Pass camera", "Remove", "Back"]);
    }
    else if (gPage == "person")
    {
        if (msg == "Pass camera") go("pass|" + (string)gSel);
        else if (msg == "Remove") go("kick|" + (string)gSel);
        else roster();
    }
    else if (gPage == "end" && msg == "End live") go("end");
    else if (gPage == "lead") go(llList2String(["decline", "allow"], msg == "Allow"));
    else if (gPage == "view") go(llList2String(["leave", "ask"], msg == "Ask to lead"));
    else if (gPage == "invited") go(llList2String(["no", "accept"], msg == "Watch"));
    else if (gPage == "give" && k != NULL_KEY)
    {
        llGiveInventory(k, WATCH);
        go("note|Take 12 Watch given to " + name(k) + ". Once they wear it, hold your button > Go live.");
    }
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "share");
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
        if (num == SHARE_UI) open(llParseStringKeepNulls(str, ["|"], []));
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "share");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/share] v" + VERSION + " free mem " + (string)llGetFreeMemory());
    }

    listen(integer ch, string name, key id, string msg)
    {
        llListenRemove(gDlgL);
        gDlgT = 0;
        llSetTimerEvent(0.0);
        choose(msg);
    }

    timer()
    {
        if (gDlgT && llGetUnixTime() - gDlgT > 60)
        {
            llListenRemove(gDlgL);
            gDlgT = 0;
        }
        if (!gDlgT) llSetTimerEvent(0.0);
    }
}
