// ============================================================================
//  Take 12  -  connect.lsl  (v6.8)  - the Connect panel (the menus of sync)
//  6.8.0: sharing became Connect (this was share.lsl, split out of sync.lsl in 6.2 for memory). sync keeps the
//  connection itself (the protocol, who is connected, the camera); this script only draws its panels and hands the
//  choice back. Whoever films leads, so there is no director to set up, no roster, no lead requests.
//    sync -> here  SHARE_UI "<camOn>|<page>|..."  (what the panel needs to know, when it should open)
//      live|<connected,>|<on a Watch,>    view|<host>|<nobody films>    inv|<from>
//      near|<hub>|<connected,>|<key,T~idle~host,...>    end|<connected,> (Disconnect, only Watches left: asks)
//    here -> sync  SHARE_DO "everyone" "connect|<key>" "join|<key>" "who" "film" "next" "disconnect" "end" "panel"
//      "accept" "no" "note|<text>"
//  Give Watch (the free viewer HUD, from the HUD's contents) is all here. Checked in tools/sim/sync_sim.py.
// ============================================================================

string VERSION = "7.1.2";
string PASS    = "cinema-1.0-build1";

integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer SHARE_UI   = 7392;   // sync -> here: open a panel
integer SHARE_DO   = 7393;   // here -> sync: the choice
float   NEAR       = 20.0;   // m  who can be given a Watch
string  WATCH      = "Take 12 Watch";

key     gOwner;
integer gCamOn;              // your own camera runs (⋯ More opens the live menu then)
string  gPage;
list    gBtn;                // [label, key, ...]: the people on the buttons
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

list keys(string csv)
{
    return llParseString2List(csv, [","], []);
}

// a label: a quiet mark and the word (7.0: the one menu style)
string lb(string e, string m, string t)
{
    return m + " " + t;                                     // 7.0: one quiet menu style (the marks)
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
// who is connected, in words: "Ana, Ben (Watch)"
string who(list ks, list w)
{
    list n = [];
    integer i;
    for (i = 0; i < llGetListLength(ks); i++)
    {
        string t = sn(llList2Key(ks, i));
        if (llListFindList(w, [llList2String(ks, i)]) >= 0) t += " (Watch)";
        n += [t];
    }
    return llDumpList2String(n, ", ");
}

open(list P)
{
    gCamOn = (integer)llList2String(P, 0);
    string p = llList2String(P, 1);
    string more = lb("⋯", "⋯", "More");
    string inv = lb("➕", "+", "Invite");
    string dis = "Disconnect";                              // no mark: × is Close
    if (p == "live")                                        // you hold the connection
    {
        list c = keys(llList2String(P, 2));
        string t = "⇄ Connected";
        if (c == []) t += "\nNobody has joined yet: they are asked.";
        else t += " with " + who(c, keys(llList2String(P, 3))) + ".";
        if (gCamOn) t += "\nYou film: they see your camera.";
        else t += "\nNobody films. Start any camera (or Film) and they all see it.";
        dialog("live", t + "\nWhoever films leads: when one of them starts a camera, you see theirs.",
            [llList2String(["Film", "Next"], gCamOn), inv, dis, more, "Close"]);
    }
    else if (p == "view")                                   // connected with someone
    {
        string h = sn((key)llList2String(P, 2));
        string t = "⇄ Connected with " + h + ".";
        if ((integer)llList2String(P, 3)) t += "\nNobody films: you have your own camera.";
        else t += "\n" + h + " films: you see their camera. Any movement key: yours for a moment.";
        dialog("view", t + "\nMy turn: you film, and everyone connected sees yours.", ["My turn", "Next", dis, more, "Close"]);
    }
    else if (p == "inv")
        dialog("invited", sn((key)llList2String(P, 2)) + " wants to connect with you.\nConnected, you see the camera of whoever films; "
            + "you keep your own when nobody does. A double-tap also says yes.", ["Connect", "No"]);
    else if (p == "end")                                    // the last Take 12 leaves the Watches: never by accident
        dialog("end", "Disconnect?\n" + who(keys(llList2String(P, 2)), keys(llList2String(P, 2))) + " will lose the view.", ["Disconnect", "Keep"]);
    else if (p == "near")
    {
        integer hub = (integer)llList2String(P, 2);
        list connected = keys(llList2String(P, 3));
        list N = llParseStringKeepNulls(llList2String(P, 4), [","], []);
        gBtn = [];
        list b = [];
        list desc = [];
        integer i;
        for (i = 0; i + 1 < llGetListLength(N); i += 2)
        {
            key k = (key)llList2String(N, i);
            list I = llParseStringKeepNulls(llList2String(N, i + 1), ["~"], []);
            string st = llList2String(I, 1);
            string d = sn(k);
            if (llList2String(I, 0) == "W") d += " (Watch)";
            if (st == "live") d += " (connected)";
            else if (st == "view") d += " (connected with " + llList2String(I, 2) + ")";
            desc += [d];
            if (llGetListLength(b) < 8)
            {
                string jl = fit(lb("⇄", "⇄", "Join") + " " + sn(k), 24);
                string al = fit("+ " + sn(k), 24);
                if (st == "live" && !hub) { b += [jl]; btn(jl, k); }
                else if (st == "idle" && llListFindList(connected, [(string)k]) < 0) { b += [al]; btn(al, k); }
            }
        }
        string t = "Connect with the people near you. Once connected, whoever films leads: everyone sees that camera.";
        if (hub) t = "Invite more people to your connection.";
        if (desc == []) t += "\nNobody near you wears Take 12 or Take 12 Watch yet: Give Watch gives them the free viewer.";
        else t += "\nNear you: " + llDumpList2String(desc, ", ") + "\n+ name: connect with them";
        if (b != []) b = ["+ Everyone"] + b;
        dialog("near", t, b + ["Give Watch", more, "Close"]);
    }
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
    if (msg == "Close" || msg == "Keep") return;
    key k = btnKey(msg);
    if (msg == lb("➕", "+", "Invite")) go("who");
    else if (msg == "Disconnect") go(llList2String(["disconnect", "end"], gPage == "end"));
    else if (msg == "Film" || msg == "My turn") go("film");
    else if (msg == "Next") go("next");
    else if (gPage == "near")
    {
        if (msg == "+ Everyone") go("everyone");
        else if (msg == "Give Watch") giveList();
        else if (k == NULL_KEY) return;
        else if (llGetSubString(msg, 0, 0) == "+") go("connect|" + (string)k);   // connect with one: you hold it for them
        else go("join|" + (string)k);                                          // someone near is connected: join them
    }
    else if (gPage == "invited") go(llList2String(["no", "accept"], msg == "Connect"));
    else if (gPage == "give" && k != NULL_KEY)
    {
        llGiveInventory(k, WATCH);
        go("note|Take 12 Watch given to " + sn(k) + ". Once they wear it, hold your button > + " + sn(k) + ".");
    }
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "connect");
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
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "connect");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/connect] v" + VERSION + " free mem " + (string)llGetFreeMemory());
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
