// ============================================================================
//  Take 12  -  cinema_sync.lsl  (v5.2)  - Share the view
//  You: long press > Share. Everyone within 20 m who wears the free Take 12 Watch, or Take 12 with you in their Friends,
//  watches at once (anyone else with Take 12 sees "<you> shares a view - double-tap to watch"); their camera follows every cut and glide of
//  yours (core reports each camera as CAMSET). Anyone watching can double-tap to cut for all. Any movement key
//  gives a watcher their own camera back. Share > Give Watch hands the free HUD to someone near you.
//  The same script watches for you when someone else shares.
//  Channel SYNC_CH, messages "T12|<what>|...":
//    offer|<name>  (llRegionSay)      join / leave / next  (watcher -> sharer)      cam|<pos>|<focus>|<lag> / end
// ============================================================================

string VERSION = "5.3.1";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer CAMSET     = 7325;   // core -> sync  "<pos>|<focus>|<lag>"
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer SYNC_CH    = -7712120;   // Take 12 and Take 12 Watch share this channel
float   NEAR       = 20.0;       // m  who is asked
string  WATCH      = "Take 12 Watch";

key     gOwner;
list    gWatchers;           // sharing: the avatars watching you
string  gLastCam;            // the camera on your screen now
key     gHost;               // watching: whose view you follow
key     gOffer;              // the sharer who just asked you
list    gAck;                // who answered your offer: "<name>" (watching) or "<name> (double-tap)"
integer gAckT;               // ... the offer went out at
integer gPendT;              // ... and since when (an offer from someone not in your Friends: double-tap to watch)
string  gPage;               // our own dialog: "share", "give", "offer"
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

// ---- sharing ---------------------------------------------------------------
endShare()
{
    integer i;
    for (i = 0; i < llGetListLength(gWatchers); i++) say(llList2Key(gWatchers, i), "end");
    if (gWatchers != []) show("Sharing ended");
    gWatchers = [];
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
    say(host, "join");
    if (llGetPermissions() & PERMISSION_TAKE_CONTROLS) llTakeControls(831, TRUE, TRUE);   // any movement key: your camera back
    llMessageLinked(LINK_SET, CMD, "watch", "");
    show("Watching " + llKey2Name(host) + "\nany key: your camera · double-tap: next for all");
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
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_CONTROL_CAMERA | PERMISSION_TAKE_CONTROLS);
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
        leave(TRUE, FALSE);                                 // taken off: tell the sharer, or your watchers
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
            integer i;
            for (i = 0; i < llGetListLength(gWatchers); i++) say(llList2Key(gWatchers, i), "cam|" + str);
        }
        else if (num == START)                              // your own camera starts: stop watching
        {
            unpend();
            leave(TRUE, TRUE);
        }
        else if (num == STOP && str != "switch") endShare();
        else if (num == CMD && str == "share")
        {
            llRegionSay(SYNC_CH, "T12|offer|" + llKey2Name(gOwner));     // offered at once
            gAck = [];
            gAckT = llGetUnixTime();
            llSetTimerEvent(1.0);
            string t = "Your view is offered to the people near you who wear Take 12 or Take 12 Watch.";
            if (gWatchers != []) t += "\nWatching now: " + (string)llGetListLength(gWatchers);
            dialog("share", t, ["Give Watch", "Stop sharing", "Close"]);
        }
        else if (num == CMD && str == "scenery" && gHost != NULL_KEY) say(gHost, "next");    // double-tap while watching
        else if (num == CMD && str == "scenery" && gPendT) watch(gOffer);                    // double-tap: watch the offer
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "sync");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/sync] v" + VERSION + " watching you " + (string)llGetListLength(gWatchers) + ", following "
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
            else if (gPage == "give")
            {
                integer i;
                for (i = 0; i < llGetListLength(gNear); i++)
                {
                    key k = llList2Key(gNear, i);
                    if (llGetSubString(llKey2Name(k), 0, 23) == msg)
                    {
                        llGiveInventory(k, WATCH);
                        llOwnerSay("[Take 12] Take 12 Watch given to " + llKey2Name(k) + ". Once they wear it, Share > Offer view.");
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
            if (gHost != NULL_KEY || !near(who)) return;
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
            show("👁 " + llKey2Name(who) + " watches");
            if (gLastCam != "") say(who, "cam|" + gLastCam);
        }
        else if (w == "leave")
        {
            integer i = llListFindList(gWatchers, [who]);
            if (i < 0) return;
            gWatchers = llDeleteSubList(gWatchers, i, i);
            show("👁 " + llKey2Name(who) + " left");
        }
        else if (w == "next")
        {
            if (llListFindList(gWatchers, [who]) >= 0) llMessageLinked(LINK_SET, CMD, "next", "");
        }
        else if (who == gHost && w == "cam" && (llGetPermissions() & PERMISSION_CONTROL_CAMERA))
        {
            float lag = (float)llList2String(L, 4);
            llSetCameraParams([CAMERA_ACTIVE, TRUE, CAMERA_POSITION, (vector)llList2String(L, 2), CAMERA_FOCUS, (vector)llList2String(L, 3),
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
        if (gTextT == 0.0 && gDlgT == 0 && !gPendT && !gAckT) llSetTimerEvent(0.0);
    }
}
