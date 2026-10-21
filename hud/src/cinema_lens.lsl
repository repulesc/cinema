// ============================================================================
//  Take 12  -  cinema_lens.lsl  (v5.1)  - Follow my lead, in Friends
//  You frame the view with Second Life's own camera (Alt-orbit, the wheel, A/D while seated) and press Esc: core
//  sees the camera still for 1.5 s and sends LEAD. This script keeps what you chose - how close, how high, from where
//  and aimed at what - relative to the group, and hands it to Friends as LENS, so every next cut and variation keeps it.
//  Seated, W/S step closer or wider (they do not move a seated avatar). Long press > Auto, sitting down or standing
//  up go back to the automatic framing.
// ============================================================================

string VERSION = "5.3.0";

integer START      = 7301;
integer STOP       = 7302;
integer SHOT       = 7310;   // friends -> core  "<cam>|<focus>|<hold>|<type>|<subject>" (the subject: where it aimed)
integer GLIDE      = 7312;
integer NUDGE      = 7317;
integer LENS       = 7319;   // lens -> friends  "<distance>|<angle down rad>|<from rad>|<aim>|<cut now>"; distance 0 = automatic
integer LEAD       = 7324;   // core -> lens     "<cam>|<focus>": your own view, held still
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;

key     gOwner;
integer gActive;             // Friends is running
vector  gCam;                // the shot on screen: camera, focus, and the subject it was planned on
vector  gFoc;
vector  gSubj;
float   gS;                  // your lead: distance along the view (0 = automatic), angle down, from where
float   gEl;
float   gAz;
vector  gAim;                // where you aimed, from the subject Friends planned
integer gPrev;               // keys held at the last NUDGE
integer gSit;
vector  gLC;                 // the last view you led with
integer gTold;               // the Esc tip was given (once per rez)
float   gTextT;

show(string s)
{
    llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gTextT = llGetTime();
}

send(integer cut)
{
    llMessageLinked(LINK_SET, LENS, llDumpList2String([gS, gEl, gAz, gAim, cut], "|"), "");
}

// keep camera c looking at q: how far, how high, from where
lead(vector c, vector q)
{
    vector h = c - q;
    gS = llVecDist(c, q);
    gEl = llAtan2(h.z, llVecMag(<h.x, h.y, 0.0>));
    gAz = llAtan2(h.y, h.x);
}

automatic(integer cut)
{
    if (gS == 0.0 && gAim == ZERO_VECTOR) return;
    gS = 0.0;
    gAim = ZERO_VECTOR;
    if (cut) show("Auto");
    send(cut);
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "lens");
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
        if (num == START)
        {
            gActive = (llList2String(llParseString2List(str, ["|"], []), 0) == "friends");
            gPrev = 0;
            if (!gActive) return;
            gSit = llGetAgentInfo(gOwner) & AGENT_SITTING;
            send(FALSE);
            llSetTimerEvent(1.0);
        }
        else if (num == STOP)
        {
            gActive = FALSE;
            llSetText("", ZERO_VECTOR, 0.0);
            llSetTimerEvent(0.0);
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "lens");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/lens] v" + VERSION + " lead " + (string)gS + " m, " + (string)llRound(gEl * RAD_TO_DEG)
                + " deg down, free mem " + (string)llGetFreeMemory());
        else if (!gActive) return;
        else if (num == SHOT)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            gCam = (vector)llList2String(L, 0);
            gFoc = (vector)llList2String(L, 1);
            gSubj = (vector)llList2String(L, 4);
            if (gSubj == ZERO_VECTOR) gSubj = gFoc;
        }
        else if (num == GLIDE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            vector f = (vector)llList2String(L, 1);
            gSubj += f - gFoc;                              // the group moved: its subject with it
            gFoc = f;
            gCam = (vector)llList2String(L, 0);
        }
        else if (num == LEAD)
        {
            // your view: the camera, and the point it looks at nearest the old subject
            list L = llParseStringKeepNulls(str, ["|"], []);
            vector c = (vector)llList2String(L, 0);
            vector q = (vector)llList2String(L, 1);
            if (llVecDist(c, gLC) < 0.05) return;           // the same view again: Esc not pressed yet
            gLC = c;
            gAim += q - gSubj;
            gSubj = q;
            gCam = c;
            gFoc = q;
            lead(c, q);
            show("Your view is kept · Esc to continue");
            if (!gTold) llOwnerSay("[Take 12] Your view is kept: press Esc to carry on. Hold the button > Release to go back.");
            gTold = TRUE;
            send(FALSE);                                    // it is on screen already
        }
        else if (num == NUDGE && gSit)
        {
            integer lv = (integer)str;
            integer k = lv & ~gPrev;
            gPrev = lv;
            if (!(k & (CONTROL_FWD | CONTROL_BACK))) return;
            if (gS == 0.0) lead(gCam, gSubj);               // from the shot on screen
            if (k & CONTROL_FWD) gS = gS * 0.8;
            else gS = gS * 1.25;
            if (gS < 0.6) gS = 0.6;
            if (gS > 25.0) gS = 25.0;
            if (k & CONTROL_FWD) show("Closer");
            else show("Wider");
            send(TRUE);
        }
        else if (num == CMD && str == "auto") { gLC = ZERO_VECTOR; automatic(TRUE); }
        else if (num == CMD && str == "autoq") automatic(FALSE);   // Friends: the group changed
    }

    timer()
    {
        if (gTextT > 0.0 && llGetTime() - gTextT > 3.0)
        {
            gTextT = 0.0;
            llSetText("", ZERO_VECTOR, 0.0);
        }
        integer s = llGetAgentInfo(gOwner) & AGENT_SITTING;
        if (s != gSit)
        {
            gSit = s;                                       // sat down or stood up: automatic again
            automatic(FALSE);
        }
    }
}
