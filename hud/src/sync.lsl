// ============================================================================
//  Take 12  -  sync.lsl  (8.0)  - Connect: two equal cameras
//  Everyone connected films with their own shot; anyone can watch anyone's film. With one other person the strip's
//  Connect key flips between your film and theirs; with more, it opens their names. You find people in Dialog ›
//  Connect (within 20 m, wearing Take 12): a tap asks them ("Ana wants to share films", Yes / No); your Friends
//  (Settings › Friends) join without being asked. A soft chime (the HUD's sound, only you hear it; Settings ›
//  Friends › Chime) when someone asks or joins. The strip: the linked rings and a count, SHARING while someone watches
//  your film, THEIR FILM while you watch; the [12]'s dot is white when connected and glows softly when shared.
//  One director per pair: while you watch someone you film for nobody (your watchers go back to their own film).
//  Only Take 12's shots are shared (core's CAMSET; your own camera, Alt-click looks and mouselook never are): their
//  film stopping sends you back to yours ("Ben isn't filming."). Beyond 20 m a connection rests (the count drops) and
//  comes back by itself; 3 s without a word from the one you watch is "Ben left"; 30 min apart and it ends. Leave
//  (or a hold: everything off) ends it. A re-worn Take 12 rejoins the ones it was with in the last 30 min.
//  A 7.x Take 12 shows as "(old)" and never connects. Meeting a newer Take 12: "A newer Take 12 is out." once.
//  Channel SYNC_CH, "T12|8|<what>|...", llRegionSayTo (who: llRegionSay). docs/CONNECT.md.
// ============================================================================

string VERSION = "8.0.1";
string PASS    = "cinema-1.0-build1";
integer LITE   = 0;                 // the free Take 12 Scenery build: it can watch, never film for others

integer UI_STATE   = 7320;
integer CAMSET     = 7325;
integer LINKST     = 7342;
integer NOTE       = 7344;
integer TXT        = 7346;
integer TXT_ANS    = 7347;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer CROP       = 7390;
integer SYNC_CH    = -7712120;
float   NEAR       = 20.0;          // m  who can be asked; beyond it a connection rests
float   GONE       = 3.0;           // s  no word from the one you watch
float   QUIET      = 10.0;          // s  no word from a peer: it rests
integer APART      = 1800;          // s  rested this long, it ends
integer WAIT       = 20;            // s  an ask waits this long

key     gOwner;
list    gP;                         // the people connected: keys
list    gPN;                        // ... their short names
list    gPF;                        // ... their film (1 filming, 2 watching someone)
list    gPT;                        // ... heard from at (llGetTime)
list    gPR;                        // ... in reach (1), resting (0)
list    gPA;                        // ... apart since (unix, 0 near)
list    gW;                         // who watches your film
key     gHost = NULL_KEY;           // whose film you watch
string  gCam;                       // their last camera
integer gFilm;                      // your film is shareable now (core: CAMSET)
string  gLast;                      // your last camera, for a new watcher
string  gShape = "0";               // your shape (bars: CROP)
string  gFollowed;                  // their shape on your bars
list    gInv;                       // asked, no answer yet: [key, unix]
key     gAsk = NULL_KEY;            // asking you
integer gAskT;
list    gNear;                      // the scan: [key, "8" / "old", lite]
float   gScanT;
string  gScan;                      // connect / addfriend
integer gChan;
integer gLh;
integer gDlgT;
string  gPage;
list    gBtn;
list    gBtnK;
string  gSent;
integer gBeat;
integer gSaveT;
integer gDebug;

// ---- names ---------------------------------------------------------------------------
string sn(key k)
{
    integer i = llListFindList(gP, [k]);
    string n = llKey2Name(k);
    if (n == "" && i >= 0) return llList2String(gPN, i);
    if (n == "") return "someone";
    integer j = llSubStringIndex(n, " Resident");
    if (j > 0) n = llGetSubString(n, 0, j - 1);
    return n;
}

note(string id, key k)
{
    llMessageLinked(LINK_SET, NOTE, id + "|" + sn(k), "");
}

dbg(string s)
{
    if (gDebug) llOwnerSay("[T12 sync " + (string)(llGetUnixTime() % 1000) + "] " + s);
}

say(key k, string m)
{
    llRegionSayTo(k, SYNC_CH, "T12|8|" + m);
    if (llGetSubString(m, 0, 1) != "hb" && llGetSubString(m, 0, 2) != "cam") dbg("→ " + sn(k) + ": " + m);
}

integer near(key k)
{
    list d = llGetObjectDetails(k, [OBJECT_POS]);
    return (d != [] && llVecDist(llList2Vector(d, 0), llGetPos()) <= NEAR);
}

integer vnum(string v)
{
    list L = llParseString2List(v, ["."], []);
    return (integer)llList2String(L, 0) * 10000 + (integer)llList2String(L, 1) * 100 + (integer)llList2String(L, 2);
}

// a newer Take 12 met: say it once per version
newer(string v)
{
    if (vnum(v) <= vnum(VERSION) || vnum(v) <= vnum(llLinksetDataReadProtected("cin.newer", PASS))) return;
    llLinksetDataWriteProtected("cin.newer", v, PASS);
    llMessageLinked(LINK_SET, NOTE, "newer", "");
}

chime()
{
    string s = llGetInventoryName(INVENTORY_SOUND, 0);
    if (s != "" && llLinksetDataReadProtected("cin.chime", PASS) != "0") llPlaySound(s, 0.5);
}

integer friend(key k)
{
    return (llSubStringIndex(llLinksetDataReadProtected("cin.friends", PASS), (string)k) >= 0);
}

// ---- the strip: the Connect key and the [12]'s dot ------------------------------------
integer reach()
{
    integer n;
    integer i;
    for (i = 0; i < llGetListLength(gP); i++) n += llList2Integer(gPR, i);
    return n;
}

// the one other person you can flip to (-1: none, or more than one)
integer one()
{
    if (reach() != 1) return -1;
    return llListFindList(gPR, [1]);
}

refresh()
{
    integer n = reach();
    string s = "on|" + (string)n + "|";
    if (gP == []) s = "alone|0|";
    else if (gHost != NULL_KEY) s = "theirs|" + (string)n + "|" + sn(gHost);
    else if (gW != []) s = "shared|" + (string)n + "|";
    else if (n == 0 || (one() >= 0 && !(llList2Integer(gPF, one()) & 1))) s = "dim|" + (string)n + "|";
    if (s == gSent) return;
    gSent = s;
    llMessageLinked(LINK_SET, LINKST, s, "");
}

// who you were with, and when: a re-worn Take 12 rejoins them within 30 min
save()
{
    integer now = llGetUnixTime();
    list R = [];
    integer i;
    for (i = 0; i < llGetListLength(gP); i++) R += [llList2String(gP, i) + "=" + (string)now];
    if (R == []) llLinksetDataDeleteProtected("cin.peers", PASS);
    else llLinksetDataWriteProtected("cin.peers", llDumpList2String(R, ";"), PASS);
    gSaveT = now;
}

integer recent(key k)
{
    list R = llParseString2List(llLinksetDataReadProtected("cin.peers", PASS), [";"], []);
    integer i;
    for (i = 0; i < llGetListLength(R); i++)
    {
        list kv = llParseString2List(llList2String(R, i), ["="], []);
        if ((key)llList2String(kv, 0) == k && llGetUnixTime() - (integer)llList2String(kv, 1) < APART) return TRUE;
    }
    return FALSE;
}

// ---- people --------------------------------------------------------------------------
add(key k)
{
    if (k == gOwner || k == NULL_KEY) return;
    integer i = llListFindList(gP, [k]);
    if (i >= 0)
    {
        gPT = llListReplaceList(gPT, [llGetTime()], i, i);
        return;
    }
    if (llGetListLength(gP) >= 8) return;
    gP += [k];
    gPN += [sn(k)];
    gPF += [0];
    gPT += [llGetTime()];
    gPR += [near(k)];
    gPA += [0];
    save();
    refresh();
}

drop(key k)
{
    integer i = llListFindList(gP, [k]);
    if (i >= 0)
    {
        gP = llDeleteSubList(gP, i, i);
        gPN = llDeleteSubList(gPN, i, i);
        gPF = llDeleteSubList(gPF, i, i);
        gPT = llDeleteSubList(gPT, i, i);
        gPR = llDeleteSubList(gPR, i, i);
        gPA = llDeleteSubList(gPA, i, i);
    }
    i = llListFindList(gW, [k]);
    if (i >= 0) gW = llDeleteSubList(gW, i, i);
    if (k == gHost) mine(TRUE, TRUE);
    save();
    refresh();
}

// Leave, or everything off: the connection ends for you
leave()
{
    integer i;
    for (i = 0; i < llGetListLength(gP); i++) say(llList2Key(gP, i), "bye");
    if (gHost != NULL_KEY) mine(TRUE, TRUE);
    gP = [];
    gPN = [];
    gPF = [];
    gPT = [];
    gPR = [];
    gPA = [];
    gW = [];
    save();
    refresh();
}

// ---- watching ----------------------------------------------------------------------------
watch(key k)
{
    if (gHost != NULL_KEY && gHost != k) say(gHost, "unwatch");
    gHost = k;
    gCam = "";
    say(k, "watch");
    integer i;
    for (i = 0; i < llGetListLength(gW); i++) say(llList2Key(gW, i), "pause");   // one director per pair
    gW = [];
    llMessageLinked(LINK_SET, CMD, "watch|" + (string)k, "");
    note("theirs", k);
    refresh();
}

// back to your own film. clear: the camera is yours to set again (not when core already starts a new shot)
mine(integer clear, integer tellCore)
{
    if (gHost == NULL_KEY) return;
    if (llListFindList(gP, [gHost]) >= 0) say(gHost, "unwatch");
    gHost = NULL_KEY;
    gCam = "";
    if (clear && (llGetPermissions() & PERMISSION_CONTROL_CAMERA)) llClearCameraParams();
    if (gFollowed != "") llMessageLinked(LINK_SET, CMD, "bars|follow", "");
    gFollowed = "";
    if (tellCore) llMessageLinked(LINK_SET, CMD, "unwatch", "");
    refresh();
}

// their camera through YOUR lens: the same line to the same focus at the distance that keeps the picture size
place()
{
    list L = llParseStringKeepNulls(gCam, ["|"], []);
    vector p = (vector)llList2String(L, 0);
    vector f = (vector)llList2String(L, 1);
    float lag = (float)llList2String(L, 2);
    float df = (float)llList2String(L, 3);
    float my = llGetCameraFOV();
    if (df > 0.05 && my > 0.05)
    {
        float k = llTan(df * 0.5) / llTan(my * 0.5);
        if (k < 0.2) k = 0.2;
        if (k > 5.0) k = 5.0;
        vector q = f + (p - f) * k;
        list r = llCastRay(f, q, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
        if (llList2Integer(r, -1) > 0) q = llList2Vector(r, 1) + llVecNorm(f - q) * 0.3;
        p = q;
    }
    if (lag > 0.0 && lag < 0.3) lag = 0.3;                  // between their updates the camera eases; a cut stays a cut
    if (lag > 3.0) lag = 3.0;
    if (llGetPermissions() & PERMISSION_CONTROL_CAMERA)
        llSetCameraParams([CAMERA_ACTIVE, TRUE, CAMERA_POSITION, p, CAMERA_FOCUS, f, CAMERA_POSITION_LOCKED, TRUE,
            CAMERA_FOCUS_LOCKED, TRUE, CAMERA_POSITION_LAG, lag, CAMERA_FOCUS_LAG, lag, CAMERA_POSITION_THRESHOLD, 0.0,
            CAMERA_FOCUS_THRESHOLD, 0.0]);
    string s = llGetSubString(llList2String(L, 4), 0, 3);   // "2.39", or 0: no bars
    if ((float)s == 0.0) s = "full";
    if (s != gFollowed)
    {
        gFollowed = s;
        llMessageLinked(LINK_SET, CMD, "bars|follow " + s, "");
    }
}

// ---- dialogs --------------------------------------------------------------------------
dialog(string page, string args, list labels, list keys)
{
    gPage = page;
    gBtn = labels;
    gBtnK = keys;
    if (gLh) llListenRemove(gLh);
    gChan = -100000 - (integer)llFrand(900000000.0);
    gLh = llListen(gChan, "", gOwner, "");
    gDlgT = llGetUnixTime();
    llMessageLinked(LINK_SET, TXT, page + "|" + args, "sync");
}

// the people near you who wear Take 12: asked, then listed 1.5 s later
scan(string why)
{
    gScan = why;
    gNear = [];
    gScanT = llGetTime();
    llRegionSay(SYNC_CH, "T12|8|who|" + VERSION + "|" + (string)LITE);
    llRegionSay(SYNC_CH, "T12|who|" + llKey2Name(gOwner));   // a 7.x Take 12 answers this: "(old)"
}

listNear()
{
    gScanT = 0.0;
    list b = [];
    list k = [];
    integer i;
    for (i = 0; i < llGetListLength(gNear) && llGetListLength(b) < 9; i += 3)
    {
        key p = llList2Key(gNear, i);
        string n = llGetSubString(sn(p), 0, 17);
        if (llList2String(gNear, i + 1) == "old") n += " (old)";
        else if (friend(p)) n = "★ " + n;
        if (llListFindList(gP, [p]) < 0 && llListFindList(b, [n]) < 0)
        {
            b += [n];
            k += [p];
        }
    }
    if (b == [])
    {
        llMessageLinked(LINK_SET, NOTE, "nobody", "");
        return;
    }
    dialog(gScan, llDumpList2String(b, ", "), b + ["Close"], k);
}

connected()
{
    list b = [];
    list k = [];
    list names = [];
    integer i;
    for (i = 0; i < llGetListLength(gP); i++)
    {
        key p = llList2Key(gP, i);
        string n = llGetSubString(sn(p), 0, 17);
        string s = n;
        if (!llList2Integer(gPR, i)) s += " (away)";
        else if (p == gHost) s += " (watching)";
        else if (!(llList2Integer(gPF, i) & 1)) s += " (not filming)";
        names += [s];
        if (llList2Integer(gPR, i) && p != gHost && (llList2Integer(gPF, i) & 1) && llGetListLength(b) < 8)
        {
            b += [n];
            k += [p];
        }
    }
    if (gHost != NULL_KEY) { b += ["My film"]; k += [NULL_KEY]; }
    dialog("connected", llDumpList2String(names, ", "), b + ["Invite", "Leave", "Close"], k);
}

// the strip's Connect key: alone, find people; with one, flip between your film and theirs; with more, their names
tapKey()
{
    if (gP == []) { scan("connect"); return; }
    if (gHost != NULL_KEY && reach() <= 1)
    {
        mine(TRUE, TRUE);
        llMessageLinked(LINK_SET, NOTE, "mine", "");
        return;
    }
    if (reach() > 1) { connected(); return; }
    integer o = one();
    if (o < 0) { note("away", llList2Key(gP, 0)); return; }
    key k = llList2Key(gP, o);
    if (llList2Integer(gPF, o) & 1) watch(k);
    else note("notfilming", k);
}

choose(string b)
{
    integer i = llListFindList(gBtn, [b]);
    key k = NULL_KEY;
    if (i >= 0 && i < llGetListLength(gBtnK)) k = llList2Key(gBtnK, i);
    string p = gPage;
    llListenRemove(gLh);
    gLh = 0;
    if (b == "Close" || i < 0) return;
    if (p == "ask")
    {
        key a = gAsk;
        gAsk = NULL_KEY;
        if (b == "Yes" && a != NULL_KEY)
        {
            say(a, "yes|" + VERSION);
            add(a);
            note("with", a);
        }
        else if (a != NULL_KEY) say(a, "no");
    }
    else if (p == "connect")
    {
        if (llSubStringIndex(b, " (old)") > 0) { note("old", k); return; }
        if (k == NULL_KEY) return;
        say(k, "ask|" + VERSION);
        gInv += [k, llGetUnixTime()];
        note("asked", k);
    }
    else if (p == "addfriend" && llSubStringIndex(b, " (old)") < 0)
    {
        string f = llLinksetDataReadProtected("cin.friends", PASS);
        if (!friend(k))
        {
            list F = llParseString2List(f, [";"], []) + [(string)k + "," + llKey2Name(k)];
            llLinksetDataWriteProtected("cin.friends", llDumpList2String(llList2List(F, -20, -1), ";"), PASS);
        }
        note("friend", k);
    }
    else if (p == "connected")
    {
        if (b == "Leave") leave();
        else if (b == "Invite") scan("connect");
        else if (b == "My film") { mine(TRUE, TRUE); llMessageLinked(LINK_SET, NOTE, "mine", ""); }
        else if (k != NULL_KEY) watch(k);
    }
}

// ---- the tick ---------------------------------------------------------------------------------
tick()
{
    float t = llGetTime();
    integer now = llGetUnixTime();
    if (gScanT > 0.0 && t - gScanT > 1.5) listNear();
    if (gLh && now - gDlgT > 60)
    {
        llListenRemove(gLh);
        gLh = 0;
        if (gPage == "ask" && gAsk != NULL_KEY) say(gAsk, "no");
        gAsk = NULL_KEY;
    }
    integer i;
    for (i = llGetListLength(gInv) - 2; i >= 0; i -= 2)
        if (now - llList2Integer(gInv, i + 1) > WAIT)
        {
            note("noanswer", llList2Key(gInv, i));
            gInv = llDeleteSubList(gInv, i, i + 1);
        }
    if (gP == []) return;
    // a word to everyone connected every second: whether you film, and whether you watch someone
    // (and 8: "I watch you", so a lost watch, unwatch or pause is mended within a second)
    for (i = llGetListLength(gP) - 1; i >= 0; i--)
    {
        key k = llList2Key(gP, i);
        say(k, "hb|" + (string)(gFilm + 2 * (gHost != NULL_KEY) + 8 * (k == gHost)));
        integer r = (near(k) && t - llList2Float(gPT, i) < QUIET);
        if (r != llList2Integer(gPR, i))
        {
            gPR = llListReplaceList(gPR, [r], i, i);
            if (r) { gPA = llListReplaceList(gPA, [0], i, i); note("back", k); }
            else
            {
                gPA = llListReplaceList(gPA, [now], i, i);
                if (k == gHost) mine(TRUE, TRUE);
                note("away", k);
            }
            refresh();
        }
        if (!r && now - llList2Integer(gPA, i) > APART) drop(k);
    }
    if (gHost != NULL_KEY)
    {
        i = llListFindList(gP, [gHost]);
        if (i >= 0 && t - llList2Float(gPT, i) > GONE)
        {
            key h = gHost;
            mine(TRUE, TRUE);
            note("left", h);
        }
    }
    if (now - gSaveT > 60) save();
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        llListen(SYNC_CH, "", NULL_KEY, "");
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_CONTROL_CAMERA | PERMISSION_TRACK_CAMERA);
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "sync");
        refresh();
        llSetTimerEvent(1.0);
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id == NULL_KEY) return;
        // a clean start; the ones you were with in the last 30 min are told you are back
        llRequestPermissions(gOwner, PERMISSION_CONTROL_CAMERA | PERMISSION_TRACK_CAMERA);
        list R = llParseString2List(llLinksetDataReadProtected("cin.peers", PASS), [";"], []);
        integer i;
        for (i = 0; i < llGetListLength(R); i++)
        {
            list kv = llParseString2List(llList2String(R, i), ["="], []);
            if (llGetUnixTime() - (integer)llList2String(kv, 1) < APART) say((key)llList2String(kv, 0), "back|" + VERSION);
        }
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER)
        {
            llLinksetDataDeleteProtected("cin.peers", PASS);
            llResetScript();
        }
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == CAMSET)
        {
            integer was = gFilm;
            gFilm = (str != "-" && !LITE && gHost == NULL_KEY);
            if (gFilm)
            {
                gLast = str + "|" + gShape;
                integer i;
                for (i = 0; i < llGetListLength(gW); i++) say(llList2Key(gW, i), "cam|" + gLast);
            }
            else if (was)
            {
                integer i;
                for (i = 0; i < llGetListLength(gW); i++) say(llList2Key(gW, i), "pause");
                gW = [];
                refresh();
            }
        }
        else if (num == CROP) gShape = llList2String(llParseString2List(str, ["|"], []), 0);
        else if (num == TXT_ANS && id == "sync" && gLh)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            if (llList2String(L, 0) == gPage) llDialog(gOwner, llDumpList2String(llList2List(L, 1, -1), "|"), gBtn, gChan);
        }
        else if (num == CMD)
        {
            if (str == "connect") tapKey();
            else if (str == "connect|menu")
            {
                if (gP == []) scan("connect");
                else connected();
            }
            else if (str == "connect|addfriend") scan("addfriend");
            else if (str == "off" || str == "standby") leave();   // everything off (or an older copy stepping aside) ends it
            else if (str == "mine") mine(FALSE, FALSE);     // core starts a shot of yours: it sets the camera
            else if (llGetSubString(str, 0, 5) == "debug|") gDebug = (integer)llGetSubString(str, 6, -1);
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "sync");
        else if (num == STATUS && str == "?")
        {
            string s = "";
            integer i;
            for (i = 0; i < llGetListLength(gP); i++)
                s += " " + llList2String(gPN, i) + "(" + llList2String(["away", "near"], llList2Integer(gPR, i)) + ", film "
                    + (string)llList2Integer(gPF, i) + ", " + (string)llRound(llGetTime() - llList2Float(gPT, i)) + " s)";
            if (s == "") s = " nobody";
            string h = "nobody";
            if (gHost != NULL_KEY) h = sn(gHost);
            llOwnerSay("[Take 12/sync] v" + VERSION + " connected:" + s + "; watching " + h + ", watched by "
                + (string)llGetListLength(gW) + ", filming " + (string)gFilm + ", free mem " + (string)llGetFreeMemory());
        }
    }

    listen(integer ch, string name, key id, string msg)
    {
        if (ch == gChan) { choose(msg); return; }
        if (llGetSubString(msg, 0, 3) != "T12|") return;
        key who = llGetOwnerKey(id);
        if (who == gOwner) return;
        list L = llParseStringKeepNulls(msg, ["|"], []);
        if (llList2String(L, 1) != "8")
        {
            // a 7.x Take 12: listed as "(old)", never connected
            string w7 = llList2String(L, 1);
            if (w7 == "here" && gScanT > 0.0 && near(who) && llListFindList(gNear, [who]) < 0) gNear += [who, "old", 0];
            else if (w7 == "invite") llRegionSayTo(who, SYNC_CH, "T12|busy|on a newer Take 12");
            return;
        }
        string w = llList2String(L, 2);
        string a = llList2String(L, 3);
        integer pi = llListFindList(gP, [who]);
        if (pi >= 0) gPT = llListReplaceList(gPT, [llGetTime()], pi, pi);
        if (w != "hb" && w != "cam") dbg("← " + sn(who) + ": " + llGetSubString(msg, 6, 60));
        if (w == "who" || w == "here" || w == "ask" || w == "yes" || w == "back" || w == "hi") newer(a);
        if (w == "who")
        {
            if (near(who)) say(who, "here|" + VERSION + "|" + (string)LITE);
        }
        else if (w == "here")
        {
            if (gScanT > 0.0 && near(who) && llListFindList(gNear, [who]) < 0) gNear += [who, "8", (integer)llList2String(L, 4)];
        }
        else if (w == "ask")
        {
            if (pi >= 0) { say(who, "yes|" + VERSION); return; }
            if (!near(who)) return;
            if (friend(who))
            {
                say(who, "yes|" + VERSION);                 // your Friends join without being asked
                add(who);
                chime();
                note("with", who);
            }
            else if (gAsk != NULL_KEY && gAsk != who) say(who, "busy");
            else
            {
                gAsk = who;
                gAskT = llGetUnixTime();
                chime();
                dialog("ask", sn(who), ["Yes", "No"], [who, who]);
            }
        }
        else if (w == "yes" || w == "no" || w == "busy")
        {
            integer i = llListFindList(gInv, [who]);
            if (i < 0 || i % 2) return;
            gInv = llDeleteSubList(gInv, i, i + 1);
            if (w == "busy") { note("busy", who); return; }
            if (w == "no") { note("noanswer", who); return; }   // a quiet No: never a rejection on screen
            // everyone already connected meets the new one: one group
            for (i = 0; i < llGetListLength(gP); i++)
            {
                key c = llList2Key(gP, i);
                say(c, "add|" + (string)who);
                say(who, "add|" + (string)c);
            }
            add(who);
            chime();
            note("with", who);
        }
        else if (w == "add" && pi >= 0)
        {
            key k = (key)a;
            if (llListFindList(gP, [k]) < 0 && k != gOwner) { add(k); note("with", k); }
        }
        else if (w == "back")
        {
            if (pi >= 0 || recent(who)) { say(who, "hi|" + VERSION); add(who); }
        }
        else if (w == "hi")
        {
            if (pi < 0 && recent(who)) { add(who); note("back", who); }
        }
        else if (pi < 0) return;
        // from someone connected
        else if (w == "hb")
        {
            integer f = (integer)a;
            if (f != llList2Integer(gPF, pi))
            {
                gPF = llListReplaceList(gPF, [f], pi, pi);
                refresh();
            }
            integer wi = llListFindList(gW, [who]);
            if ((f & 8) && wi < 0)                          // they watch you, and their "watch" was lost
            {
                if (LITE || !gFilm || gHost != NULL_KEY) say(who, "pause");
                else
                {
                    gW += [who];
                    if (gLast != "") say(who, "cam|" + gLast);
                    refresh();
                }
            }
            else if (!(f & 8) && wi >= 0)                   // their "unwatch" was lost
            {
                gW = llDeleteSubList(gW, wi, wi);
                refresh();
            }
            if (who == gHost && !(f & 1))                   // the one you watch stopped filming (a lost "pause")
            {
                mine(TRUE, TRUE);
                note("notfilming", who);
            }
        }
        else if (w == "watch")
        {
            if (LITE || !gFilm || gHost != NULL_KEY) { say(who, "pause"); return; }
            if (llListFindList(gW, [who]) < 0) gW += [who];
            if (gLast != "") say(who, "cam|" + gLast);
            note("watching", who);
            refresh();
        }
        else if (w == "unwatch")
        {
            integer i = llListFindList(gW, [who]);
            if (i >= 0) gW = llDeleteSubList(gW, i, i);
            refresh();
        }
        else if (w == "bye")
        {
            if (who == gHost) note("left", who);
            drop(who);
        }
        else if (who != gHost) return;
        // from the one you watch
        else if (w == "cam")
        {
            gCam = llDumpList2String(llList2List(L, 3, -1), "|");
            place();
        }
        else if (w == "pause")
        {
            gPF = llListReplaceList(gPF, [0], pi, pi);
            mine(TRUE, TRUE);
            note("notfilming", who);
        }
    }

    timer()
    {
        tick();
    }
}
