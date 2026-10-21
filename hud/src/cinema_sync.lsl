// ============================================================================
//  Take 12  -  cinema_sync.lsl  (v5.4)  - Share the view
//  One director at a time: everyone watching follows one camera, so two cameras never fight.
//  The one Share button (tap menu and hold menu) does what fits the moment:
//    nothing shared yet   starts your camera if needed and offers your view to everyone within 20 m
//    you share            who watches (and who is looking around), Offer again, Stop sharing, Give Watch
//    you watch            Direct (your camera becomes the shared one), Leave
//    an offer is waiting  watch it
//  Watching: the free Take 12 Watch, or Take 12 with the sharer in its Friends, joins at once; anyone else with Take 12
//  sees "<name> shares a view - double-tap to watch". A watcher's double-tap cuts for all (5 s apart). A watcher who
//  orbits their own camera is "looking around" (the director is told); Esc brings them back. Any movement key leaves.
//  Channel SYNC_CH, messages "T12|<what>|...":
//    offer|<name> (llRegionSay)   ack|<1 watching, 0 double-tap>   join  leave  next  away  back  direct   (to the director)
//    cam|<pos>|<focus>|<lag>   director|<key>|<name>   end                                                (to watchers)
// ============================================================================

string VERSION = "5.4.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer CAMSET     = 7325;   // core -> sync  "<pos>|<focus>|<lag>"
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer SYNC_CH    = -7712120;   // Take 12 and Take 12 Watch share this channel
float   NEAR       = 20.0;       // m  who is asked
integer NEXT_GAP   = 5;          // s  two watchers' double-taps close together cut once
string  WATCH      = "Take 12 Watch";

key     gOwner;
integer gSharing;            // you direct
integer gCamOn;              // your own camera runs
integer gHand;               // you just handed the camera over: your stop is not the end
list    gWatchers;           // directing: who watches you
list    gAway;               // ... and who of them is looking around
integer gNextT;              // ... the last "next" asked by a watcher
string  gLastCam;            // the camera on your screen now
key     gHost;               // watching: whose view you follow
vector  gApplied;            // ... the camera last set from it
float   gApplyT;             // ... and until when it may still be moving there
integer gIsAway;             // ... you are looking around on your own
key     gOffer;              // the sharer who just asked you
integer gPendT;              // ... since when (someone not in your Friends: double-tap to watch)
list    gAck;                // who answered your offer
integer gAckT;               // ... the offer went out at
string  gPage;               // our own dialog
list    gNear;               // give: the avatars listed
integer gDlg;
integer gDlgL;
integer gDlgT;
float   gTextT;

show(string s)
{
    llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gTextT = llGetTime();
    llSetTimerEvent(1.0);
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
    llDialog(gOwner, text, b, gDlg);
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
    for (i = 0; i < llGetListLength(ks); i++) n += [llKey2Name(llList2Key(ks, i))];
    return llDumpList2String(n, ", ");
}

// who watches you, and who is looking around
string status()
{
    if (gWatchers == []) return "Your view is shared. Nobody watches yet.";
    string s = "Watching: " + names(gWatchers);
    if (gAway != []) s += "\nLooking around: " + names(gAway);
    return s;
}

drop(key k)
{
    integer i = llListFindList(gWatchers, [k]);
    if (i >= 0) gWatchers = llDeleteSubList(gWatchers, i, i);
    i = llListFindList(gAway, [k]);
    if (i >= 0) gAway = llDeleteSubList(gAway, i, i);
}

// ---- directing -------------------------------------------------------------
offer()
{
    llRegionSay(SYNC_CH, "T12|offer|" + llKey2Name(gOwner));
    gAck = [];
    gAckT = llGetUnixTime();
    llSetTimerEvent(1.0);
}

// your camera becomes the shared one (offer: also ask everyone near; a hand-over brings its watchers by itself)
direct(integer ask)
{
    gSharing = TRUE;
    if (!gCamOn) llMessageLinked(LINK_SET, CMD, "sharecam", "");    // core: your camera, in your last mode
    if (ask) offer();
    show("Sharing your view");
}

endShare()
{
    if (gSharing || gWatchers != []) show("Sharing ended");
    all("end");
    gWatchers = [];
    gAway = [];
    gSharing = FALSE;
}

// ---- watching --------------------------------------------------------------
// an offer nobody took up: the double-tap is yours again
unpend()
{
    if (!gPendT) return;
    gPendT = 0;
    if (gHost == NULL_KEY) llMessageLinked(LINK_SET, CMD, "unwatch", "");
}

watch(key host)
{
    gPendT = 0;
    gHost = host;
    gIsAway = FALSE;
    gApplied = ZERO_VECTOR;
    say(host, "join");
    if (llGetPermissions() & PERMISSION_TAKE_CONTROLS) llTakeControls(831, TRUE, TRUE);   // any movement key: your camera back
    llMessageLinked(LINK_SET, CMD, "watch", "");
    show("Watching " + llKey2Name(host) + "\ndouble-tap: next for all · any key: your camera");
}

leave(integer tell, integer clear)
{
    if (gHost == NULL_KEY) return;
    if (tell) say(gHost, "leave");
    gHost = NULL_KEY;
    // taking the HUD off: Second Life has already withdrawn the camera and gives it back by itself
    clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;
    if (clear && (llGetPermissions() & PERMISSION_CONTROL_CAMERA)) llClearCameraParams();
    if (clear && (llGetPermissions() & PERMISSION_TAKE_CONTROLS)) llTakeControls(831, FALSE, TRUE);   // keys are yours again (the permission stays)
    llMessageLinked(LINK_SET, CMD, "unwatch", "");
    show("Your camera");
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
    }

    attach(key id)
    {
        if (id != NULL_KEY) return;
        leave(TRUE, FALSE);                                 // taken off: tell the director, or your watchers
        endShare();
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
        else if (num == START)                              // your own camera starts: stop watching
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
            else endShare();
        }
        else if (num == CMD && str == "share")              // the one Share button
        {
            if (gHost != NULL_KEY) dialog("watch", "You watch " + llKey2Name(gHost) + "'s view.\nDirect: your camera becomes the shared one.", ["Direct", "Leave", "Close"]);
            else if (gPendT) watch(gOffer);
            else if (gSharing) dialog("share", status(), ["Offer again", "Stop sharing", "Give Watch"]);
            else direct(TRUE);
        }
        else if (num == CMD && str == "scenery" && gHost != NULL_KEY) say(gHost, "next");    // double-tap while watching
        else if (num == CMD && str == "scenery" && gPendT) watch(gOffer);                    // double-tap: watch the offer
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "sync");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/sync] v" + VERSION + " sharing " + (string)gSharing + ", " + status() + ", following "
                + llKey2Name(gHost) + ", free mem " + (string)llGetFreeMemory());
    }

    listen(integer ch, string name, key id, string msg)
    {
        if (ch == gDlg)
        {
            llListenRemove(gDlgL);
            if (gPage == "share")
            {
                if (msg == "Stop sharing") endShare();
                else if (msg == "Offer again") offer();
                else if (msg == "Give Watch")
                {
                    if (llGetInventoryType(WATCH) != INVENTORY_OBJECT)
                    {
                        llOwnerSay("[Take 12] Put the \"" + WATCH + "\" object in the HUD to give it out.");
                        return;
                    }
                    list ids = llGetAgentList(AGENT_LIST_REGION, []);
                    list b = [];
                    gNear = [];
                    integer i;
                    for (i = 0; i < llGetListLength(ids) && llGetListLength(b) < 11; i++)
                    {
                        key k = llList2Key(ids, i);
                        if (k != gOwner && near(k))
                        {
                            gNear += [k];
                            b += [llGetSubString(llKey2Name(k), 0, 23)];
                        }
                    }
                    if (b == []) llOwnerSay("[Take 12] Nobody within " + (string)llRound(NEAR) + " m.");
                    else dialog("give", "Give the free Take 12 Watch to:", b);
                }
            }
            else if (gPage == "watch" && gHost != NULL_KEY)
            {
                if (msg == "Leave") leave(TRUE, TRUE);
                else if (msg == "Direct")
                {
                    say(gHost, "direct");                   // the director hands everyone over to you
                    leave(FALSE, TRUE);
                    direct(FALSE);
                }
            }
            else if (gPage == "give")
            {
                integer i;
                for (i = 0; i < llGetListLength(gNear); i++)
                {
                    key k = llList2Key(gNear, i);
                    if (llGetSubString(llKey2Name(k), 0, 23) == msg)
                    {
                        llGiveInventory(k, WATCH);
                        llOwnerSay("[Take 12] Take 12 Watch given to " + llKey2Name(k) + ". Once they wear it, press Share.");
                        return;
                    }
                }
            }
            return;
        }
        // the share channel: only what an avatar's own HUD says counts
        if (llGetSubString(msg, 0, 3) != "T12|") return;
        key who = llGetOwnerKey(id);
        if (who == gOwner) return;
        list L = llParseStringKeepNulls(msg, ["|"], []);
        string w = llList2String(L, 1);
        if (w == "offer")
        {
            if (gHost != NULL_KEY || gSharing || !near(who)) return;
            gOffer = who;
            // someone in your Friends: their view at once. Anyone else: a double-tap, so no stranger takes your camera
            if (llSubStringIndex(llLinksetDataReadProtected("cin.friends", PASS), (string)who) >= 0)
            {
                say(who, "ack|1");
                watch(who);
            }
            else
            {
                say(who, "ack|0");
                if (!gPendT) llMessageLinked(LINK_SET, CMD, "watch", "");         // core: keep the double-tap for this
                gPendT = llGetUnixTime();
                show(llList2String(L, 2) + " shares a view\ndouble-tap to watch");
            }
        }
        else if (w == "ack")
        {
            if (gAckT) gAck += [llKey2Name(who) + llList2String([" (double-tap)", ""], (integer)llList2String(L, 2))];   // the answers to your offer
        }
        else if (w == "join")
        {
            if (llListFindList(gWatchers, [who]) < 0) gWatchers += [who];
            gSharing = TRUE;
            show(llKey2Name(who) + " watches");
            if (gLastCam != "") say(who, "cam|" + gLastCam);
        }
        else if (w == "leave" && llListFindList(gWatchers, [who]) >= 0)
        {
            drop(who);
            show(llKey2Name(who) + " left");
        }
        else if (w == "away" && llListFindList(gWatchers, [who]) >= 0)
        {
            if (llListFindList(gAway, [who]) < 0) gAway += [who];
            show(llKey2Name(who) + " is looking around");
        }
        else if (w == "back" && llListFindList(gAway, [who]) >= 0)
        {
            integer i = llListFindList(gAway, [who]);
            gAway = llDeleteSubList(gAway, i, i);
            show(llKey2Name(who) + " is back");
        }
        else if (w == "next" && llListFindList(gWatchers, [who]) >= 0 && llGetUnixTime() - gNextT >= NEXT_GAP)
        {
            gNextT = llGetUnixTime();
            llMessageLinked(LINK_SET, CMD, "next", "");
        }
        else if (w == "direct" && llListFindList(gWatchers, [who]) >= 0)
        {
            // a watcher takes over: everyone (you too) now follows their camera
            drop(who);
            all("director|" + (string)who + "|" + llKey2Name(who));
            gWatchers = [];
            gAway = [];
            gSharing = FALSE;
            gHand = gCamOn;
            watch(who);
            show(llKey2Name(who) + " directs now");
            if (gCamOn) llMessageLinked(LINK_SET, CMD, "stop", "");
        }
        else if (who == gHost && w == "director")
        {
            key d = (key)llList2String(L, 2);              // the director changed: follow the new one
            gHost = d;
            gIsAway = FALSE;
            gApplied = ZERO_VECTOR;
            say(d, "join");
            show(llList2String(L, 3) + " directs now");
        }
        else if (who == gHost && w == "cam" && (llGetPermissions() & PERMISSION_CONTROL_CAMERA))
        {
            float lag = (float)llList2String(L, 4);
            gApplied = (vector)llList2String(L, 2);
            gApplyT = llGetTime() + lag + 2.0;
            llSetCameraParams([CAMERA_ACTIVE, TRUE, CAMERA_POSITION, gApplied, CAMERA_FOCUS, (vector)llList2String(L, 3),
                CAMERA_POSITION_LOCKED, TRUE, CAMERA_FOCUS_LOCKED, TRUE, CAMERA_POSITION_LAG, lag, CAMERA_FOCUS_LAG, lag,
                CAMERA_POSITION_THRESHOLD, 0.0, CAMERA_FOCUS_THRESHOLD, 0.0]);
        }
        else if (who == gHost && w == "end") leave(FALSE, TRUE);
    }

    timer()
    {
        if (gPendT && llGetUnixTime() - gPendT > 20) unpend();
        if (gAckT && llGetUnixTime() - gAckT >= 2)
        {
            gAckT = 0;                                      // two seconds: who got your offer
            string r = "Nobody near you wears Take 12 or Take 12 Watch (within " + (string)llRound(NEAR) + " m).";
            if (gAck != []) r = "Offered to: " + llDumpList2String(gAck, ", ");
            llOwnerSay("[Take 12] " + r);
            show(r);
        }
        // watching: did you take your own camera (Alt-orbit)? Esc puts it back on the shared view
        if (gHost != NULL_KEY && gApplied != ZERO_VECTOR && llGetTime() > gApplyT && (llGetPermissions() & PERMISSION_TRACK_CAMERA))
        {
            float d = llVecDist(llGetCameraPos(), gApplied);
            if (!gIsAway && d > 0.6)
            {
                gIsAway = TRUE;
                say(gHost, "away");
                show("Looking around · Esc: back to " + llKey2Name(gHost) + "'s view");
            }
            else if (gIsAway && d < 0.3)
            {
                gIsAway = FALSE;
                say(gHost, "back");
                show("Back with " + llKey2Name(gHost));
            }
        }
        if (gTextT > 0.0 && llGetTime() - gTextT > 5.0 + 3.0 * (gHost != NULL_KEY) + 15.0 * (gPendT != 0))
        {
            gTextT = 0.0;
            llSetText("", ZERO_VECTOR, 0.0);
        }
        if (gDlgT > 0 && llGetUnixTime() - gDlgT > 60)
        {
            gDlgT = 0;
            llListenRemove(gDlgL);
        }
        if (gTextT == 0.0 && gDlgT == 0 && !gPendT && !gAckT && gHost == NULL_KEY) llSetTimerEvent(0.0);
    }
}
