// ============================================================================
//  Take 12  -  picker.lsl  (v4)  - the Friends page and friend picker
//  Menu page: Start / Pick / Clear. Picker: people within 20 m, one button each,
//  tap a name to add or remove (up to 10 friends, saved in protected Linkset Data
//  as "key,name;key,name;..."). Starting Friends mode is CMD "friends" to core;
//  the camera work is in friends.lsl.
//  Also the chat commands (/77 ...): they moved here from ui.lsl in 5.6.0 to give the menus room.
// ============================================================================

string VERSION = "6.8.0";
string PASS    = "cinema-1.0-build1";

integer UI_MENU    = 7321;
integer UI_FRIENDS = 7322;
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;

float   R_PICK = 20.0;       // picker range (m)
integer MAX_F  = 10;

key     gOwner;
integer gEmoji;
integer gCmdChan;
integer gCmdListen;
list    gFKeys;
list    gFNames;
integer gListen;
integer gChan;
integer gMenuT;
string  gPage;
integer gPickPg;
list    gPickK;
list    gPickL;

// ============================================================================
string cfg(string k, string d)
{
    string v = llLinksetDataReadProtected("cin." + k, PASS);
    if (v == "") return d;
    return v;
}

loadFriends()
{
    gFKeys = [];
    gFNames = [];
    gEmoji = (cfg("skin", "0") == "2");                 // emoji only in the Color menu style
    list L = llParseString2List(cfg("friends", ""), [";"], []);
    integer i;
    for (i = 0; i < llGetListLength(L); i++)
    {
        list P = llParseString2List(llList2String(L, i), [","], []);
        gFKeys += [(key)llList2String(P, 0)];
        gFNames += [llList2String(P, 1)];
    }
}

saveFriends()
{
    list L = [];
    integer i;
    for (i = 0; i < llGetListLength(gFKeys); i++) L += [(string)llList2Key(gFKeys, i) + "," + llList2String(gFNames, i)];
    llLinksetDataWriteProtected("cin.friends", llDumpList2String(L, ";"), PASS);
}

string lb(string e, string t)
{
    if (gEmoji) return e + " " + t;
    return t;
}

// top row first, like on screen; llDialog wants the bottom row first
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
    llSetTimerEvent(0.0);
}

openMenu(string page, string text, list b)
{
    closeMenu();
    gPage = page;
    gChan = -(integer)(llFrand(1000000000.0) + 1000.0);
    gListen = llListen(gChan, "", gOwner, "");
    gMenuT = llGetUnixTime();
    llSetTimerEvent(5.0);
    llDialog(gOwner, text, order(b), gChan);
}

// saved friends that are in the region right now
integer hereNow()
{
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    integer n = 0;
    integer i;
    for (i = 0; i < llGetListLength(gFKeys); i++)
    {
        if (llListFindList(ids, [llList2Key(gFKeys, i)]) >= 0) n++;
    }
    return n;
}

friendsPage()
{
    loadFriends();
    string head = "Friends";
    if (gEmoji) head = "💞 Friends";
    string text = head + " · " + (string)llGetListLength(gFKeys) + " saved · " + (string)hereNow() + " here now\n";
    if (llGetListLength(gFKeys) == 0) text += "Nobody yet: use Pick to choose from the people near you.";
    else text += llGetSubString(llDumpList2String(gFNames, ", "), 0, 380);
    openMenu("page", text, [lb("▶", "Start"), lb("➕", "Pick"), lb("➖", "Remove"), lb("🗑", "Clear"), lb("↩", "Back"), lb("✖", "Close")]);
}

pickMenu(integer pg)
{
    loadFriends();
    list od = llGetObjectDetails(gOwner, [OBJECT_POS]);
    vector me = llList2Vector(od, 0);
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    list tmp = [];
    integer i;
    for (i = 0; i < llGetListLength(ids); i++)
    {
        key k = llList2Key(ids, i);
        list d = llGetObjectDetails(k, [OBJECT_POS]);
        if (k != gOwner && llGetListLength(d) > 0)
        {
            float dist = llVecDist(llList2Vector(d, 0), me);
            if (dist <= R_PICK) tmp += [dist, k];
        }
    }
    tmp = llListSort(tmp, 2, TRUE);
    integer n = llGetListLength(tmp) / 2;
    if (pg * 9 >= n) pg = 0;
    gPickPg = pg;
    gPickK = [];
    gPickL = [];
    list b = [];
    for (i = pg * 9; i < n && i < pg * 9 + 9; i++)
    {
        key pk = llList2Key(tmp, i * 2 + 1);
        string nm = llGetSubString(llGetUsername(pk), 0, 21);
        if (llListFindList(gFKeys, [pk]) >= 0) nm = "✓ " + llGetSubString(nm, 0, 18);    // a label is at most 24 bytes
        gPickK += [pk];
        gPickL += [nm];
        b += [nm];
    }
    while (llGetListLength(b) < 9) b += " ";
    b += [lb("✔", "Done"), " "];
    if (n > pg * 9 + 9) b += [lb("▶", "More")];
    else b += " ";
    string text = "Pick friends (people within " + (string)llRound(R_PICK) + " m)\n✓ = saved, tap a name to add or remove.\n"
        + (string)llGetListLength(gFKeys) + " of " + (string)MAX_F + " saved";
    if (n == 0) text += "\nNobody is near you right now.";
    openMenu("pick", text, b);
}

// saved friends, one button each (also those who are not here): tap a name to remove just that one
removeMenu(integer pg)
{
    loadFriends();
    integer n = llGetListLength(gFNames);
    if (n == 0)
    {
        llOwnerSay("[Take 12] Your friends list is empty.");
        friendsPage();
        return;
    }
    if (pg * 9 >= n) pg = 0;
    gPickPg = pg;
    gPickL = [];
    list b = [];
    integer i;
    for (i = pg * 9; i < n && i < pg * 9 + 9; i++)
    {
        string nm = llGetSubString(llList2String(gFNames, i), 0, 21);
        gPickL += [nm];
        b += [nm];
    }
    while (llGetListLength(b) < 9) b += " ";
    b += [lb("✔", "Done"), " "];
    if (n > pg * 9 + 9) b += [lb("▶", "More")];
    else b += " ";
    openMenu("remove", "Remove a friend\nTap a name to remove just that person.\n" + (string)n + " of " + (string)MAX_F + " saved", b);
}

onChoice(string msg)
{
    if (msg == " ") { closeMenu(); return; }
    if (msg == lb("✖", "Close")) { closeMenu(); return; }
    if (gPage == "page")
    {
        if (msg == lb("▶", "Start")) { closeMenu(); llMessageLinked(LINK_SET, CMD, "friends", ""); }
        else if (msg == lb("➕", "Pick")) pickMenu(0);
        else if (msg == lb("➖", "Remove")) removeMenu(0);
        else if (msg == lb("🗑", "Clear")) openMenu("clear", "Remove all saved friends?", [lb("✔", "Yes, clear"), lb("↩", "Back")]);
        else if (msg == lb("↩", "Back")) { closeMenu(); llMessageLinked(LINK_SET, UI_MENU, "us", ""); }
    }
    else if (gPage == "clear")
    {
        if (msg == lb("✔", "Yes, clear"))
        {
            gFKeys = [];
            gFNames = [];
            saveFriends();
        }
        friendsPage();
    }
    else if (gPage == "remove")
    {
        if (msg == lb("✔", "Done")) friendsPage();
        else if (msg == lb("▶", "More")) removeMenu(gPickPg + 1);
        else
        {
            integer j = llListFindList(gPickL, [msg]);
            if (j >= 0)
            {
                integer at = gPickPg * 9 + j;
                gFKeys = llDeleteSubList(gFKeys, at, at);
                gFNames = llDeleteSubList(gFNames, at, at);
                saveFriends();
            }
            removeMenu(gPickPg);
        }
    }
    else if (gPage == "pick")
    {
        if (msg == lb("✔", "Done")) friendsPage();
        else if (msg == lb("▶", "More")) pickMenu(gPickPg + 1);
        else
        {
            integer i = llListFindList(gPickL, [msg]);
            if (i >= 0)
            {
                key k = llList2Key(gPickK, i);
                integer at = llListFindList(gFKeys, [k]);
                if (at >= 0)
                {
                    gFKeys = llDeleteSubList(gFKeys, at, at);
                    gFNames = llDeleteSubList(gFNames, at, at);
                }
                else if (llGetListLength(gFKeys) >= MAX_F) llOwnerSay("[Take 12] Friends list is full (" + (string)MAX_F + "). Remove someone first.");
                else
                {
                    gFKeys += [k];
                    gFNames += [llGetUsername(k)];
                }
                saveFriends();
            }
            pickMenu(gPickPg);
        }
    }
}

// ============================================================================
// ============================================================================
//  chat commands: /77 <command>
// ============================================================================
set(string k, string v)
{
    llLinksetDataWriteProtected("cin." + k, v, PASS);
    llMessageLinked(LINK_SET, CFG_CHANGED, k, "");
}

say(string s)
{
    llOwnerSay("[Take 12] " + s);
}

help()
{
    say("Commands on /" + (string)gCmdChan + ": scenery me us friends still connect crop size stop next photo menu status pace reach indoors face skin tips statusline trace chan reset (details: Read Me).");
}

onCommand(string msg)
{
    list a = llParseString2List(llToLower(llStringTrim(msg, STRING_TRIM)), [" "], []);
    string c = llList2String(a, 0);
    string v = llList2String(a, 1);
    integer n = (integer)v;
    integer m = llListFindList(["me", "us", "still", "connect"], [c]);  // the menu names work too
    if (m >= 0) c = llList2String(["personal", "social", "frame", "share"], m);
    if (llListFindList(["scenery", "personal", "social", "friends", "frame", "share", "stop", "next", "photo", "fav", "grab"], [c]) >= 0)
        llMessageLinked(LINK_SET, CMD, c, "");
    else if (c == "crop") llMessageLinked(LINK_SET, CMD, "crop|" + v, "");          // Frame: 4:5, off, flip, back (crop)
    else if (c == "size") llMessageLinked(LINK_SET, CMD, "size|" + v, "");          // the button: s, m, l (keys)
    else if (c == "menu" || c == "reset") llMessageLinked(LINK_SET, UI_MENU, llList2String(["main", "reset"], c == "reset"), "");
    else if (c == "status")
    {
        say("commands on /" + (string)gCmdChan);
        llMessageLinked(LINK_SET, STATUS, "?", "");
    }
    else if ((c == "pace" || c == "hold") && n >= 10 && n <= 600) { set("hold", (string)n); say("Pace: about " + v + " s per view"); }
    else if (c == "reach" && (v == "relearn" || (n >= 20 && n <= 250)))
    {
        if (v == "relearn") v = cfg("reach_set", "100");
        set("reach_set", v);
        set("reach", v);
        set("reach_ok", "0");
        say("Scenery reach: " + v + " m");
    }
    else if (c == "indoors" && (v == "auto" || v == "inside" || v == "outside")) { set("indoors", v); say("Indoors: " + v); }
    else if (c == "face" && (v == "all" || (v == (string)n && n >= 0 && n < llGetNumberOfSides())))
    {
        if (v == "all") n = -1;
        set("face", (string)n);
        say("Picture face: " + v);
    }
    else if (c == "friend" && v == "list") llMessageLinked(LINK_SET, UI_FRIENDS, "list", "");
    else if (c == "friend" && v == "clear") llMessageLinked(LINK_SET, UI_FRIENDS, "clear", "");
    else if (c == "skin" && llListFindList(["plain", "symbols", "color"], [v]) >= 0)
    {
        set("skin", (string)llListFindList(["plain", "symbols", "color"], [v]));
        say("Menu style: " + v);
    }
    else if (c == "tips" && (v == "on" || v == "off"))
    {
        if (v == "on") llLinksetDataWriteProtected("cin.tipn", "0", PASS);   // every tip from the start
        set("tips", (string)(v == "on"));
        say("Tips: " + v);
    }
    else if (c == "statusline" && (v == "on" || v == "off")) { set("status", (string)(v == "on")); say("Status line: " + v); }
    else if ((c == "trace" || c == "cutmode") && (v == "on" || v == "off")) { set(c, (string)(v == "on")); say(c + ": " + v); }
    else if (c == "chan" && n > 0 && n != 9)
    {
        set("cmd_chan", (string)n);
        gCmdChan = n;
        llListenRemove(gCmdListen);
        gCmdListen = llListen(gCmdChan, "", gOwner, "");
        say("Commands now on /" + v);
    }
    else help();
}

default
{
    state_entry()
    {
        gOwner = llGetOwner();
        loadFriends();
        gCmdChan = (integer)cfg("cmd_chan", "77");
        if (gCmdChan <= 0) gCmdChan = 77;
        gCmdListen = llListen(gCmdChan, "", gOwner, "");
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "picker");
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
        if (num == UI_FRIENDS)
        {
            if (str == "page") friendsPage();
            else if (str == "pick") pickMenu(0);
            else if (str == "list")
            {
                loadFriends();
                llOwnerSay("[Take 12] Friends (" + (string)llGetListLength(gFKeys) + "/" + (string)MAX_F + "): " + llDumpList2String(gFNames, ", "));
            }
            else if (str == "clear")
            {
                gFKeys = [];
                gFNames = [];
                saveFriends();
                llOwnerSay("[Take 12] Friends list cleared.");
            }
        }
        else if (num == CFG_CHANGED)
        {
            loadFriends();
            integer ch = (integer)cfg("cmd_chan", "77");
            if (ch > 0 && ch != gCmdChan)                   // Reset puts it back to 77
            {
                gCmdChan = ch;
                llListenRemove(gCmdListen);
                gCmdListen = llListen(gCmdChan, "", gOwner, "");
            }
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "picker");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/picker] v" + VERSION + " saved friends " + (string)llGetListLength(gFKeys) + ", free mem " + (string)llGetFreeMemory());
    }

    listen(integer channel, string name, key id, string msg)
    {
        if (id != gOwner) return;
        if (channel == gCmdChan) { onCommand(msg); return; }
        gMenuT = llGetUnixTime();
        onChoice(msg);
    }

    timer()
    {
        if (gListen && llGetUnixTime() - gMenuT > 60) closeMenu();
        if (!gListen) llSetTimerEvent(0.0);
    }
}
