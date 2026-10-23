// ============================================================================
//  Take 12  -  free.lsl  (v6.4)  - Freehand: you frame it, Take 12 holds it
//  For photographers, of people or of objects. You frame with Second Life's own camera (Alt-orbit, the wheel,
//  Ctrl+0 / Ctrl+8 for the lens, Frame for the format) and hold still for a second: core locks that view (as in Only
//  friends, "Follow my lead"). Esc and walking no longer move it: a tripod. Alt-orbit again and hold still to reframe.
//  The focus is what sits in the middle of your frame (a ray from the camera), so a zoom keeps the picture: the camera
//  dollies along its line by k = tan(old / 2) / tan(new / 2), as in every other camera, and stops short of a wall.
//  Save keeps the locked view (two per region, cin.free.<region>); a double-tap goes from one to the other, or, with
//  none saved, locks the view on screen at once.
//  core -> here: START "free|<fov>", NEXT, STOP, FOVMSG, CAMSET (every camera set, the locks too); CMD "fav" = Save.
//  Checked in tools/sim/free_sim.py.
// ============================================================================

string VERSION = "7.1.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer SHOT       = 7310;   // here -> core  "<cam>|<focus>|<hold 0: no cuts>|10|<subject>"
integer GLIDE      = 7312;   // here -> core  "<cam>|<focus>|<lag>": the dolly when you zoom
integer ACK        = 7313;
integer FOVMSG     = 7318;   // core -> here: your lens changed (radians)
integer UI_STATE   = 7320;   // core -> all  "<state>|<mode>|...": the dolly only while the view is held (rolling)
integer CAMSET     = 7325;   // core -> all  "<pos>|<focus>|<lag>|<lens>": the camera on screen
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;   // ... "fav" = Save; "view|<0/1>" = that saved view (the keys)
integer KEYS       = 7395;   // here -> keys  "free|<saved view in use, -1 none>": the key lit

key     gOwner;
integer gActive;             // Freehand is running
vector  gCam;                // the view held now
vector  gFoc;                // ... and what it is aimed at
float   gFov;                // your lens when it was held
integer gHeld;               // the view is held (core rolling), not being framed
integer gPick = -1;          // the saved view last recalled
float   gTextT;
string  gNote;

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

string slot()
{
    return "free." + llDumpList2String(llParseString2List(llGetRegionName(), [" "], []), "_");
}

list views()
{
    return llParseString2List(cfg(slot()), [";"], []);
}

// the keys (keys.lsl) light the saved view in use
lit()
{
    llMessageLinked(LINK_SET, KEYS, "free|" + (string)gPick, "");
}

// a short notice above the button, read back as Second Life keeps it; tips draws the line again afterwards
show(string s)
{
    llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gNote = llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0);
    gTextT = llGetTime();
    llSetTimerEvent(1.0);
}

// what sits in the middle of your frame: the focus (an object, an avatar, the ground) up to 60 m, else 10 m ahead
vector aim(vector c, rotation r)
{
    vector u = llRot2Fwd(r);
    list h = llCastRay(c, c + u * 60.0, [RC_MAX_HITS, 1]);
    if (llList2Integer(h, -1) > 0) return llList2Vector(h, 1);
    return c + u * 10.0;
}

shot(vector c, vector f)
{
    gCam = c;
    gFoc = f;
    gFov = llGetCameraFOV();
    llMessageLinked(LINK_SET, SHOT, (string)c + "|" + (string)f + "|0|10|" + (string)f, "");
}

// the view on your screen now
here()
{
    vector c = llGetCameraPos();
    shot(c, aim(c, llGetCameraRot()));
}

save()
{
    if (gCam == ZERO_VECTOR) return;
    list v = views() + [(string)gCam + "|" + (string)gFoc];
    if (llGetListLength(v) > 2) v = llDeleteSubList(v, 0, 0);
    llLinksetDataWriteProtected("cin." + slot(), llDumpList2String(v, ";"), PASS);
    gPick = llGetListLength(v) - 1;
    lit();
    show("Saved: View " + llList2String(["A", "B"], gPick) + "\ndouble-tap: your saved views");
}

// double-tap: the next saved view; with none, the view on screen, held at once
recall()
{
    list v = views();
    if (v == [])
    {
        here();
        show("Held");
        return;
    }
    gPick = (gPick + 1) % llGetListLength(v);
    at(gPick);
}

// a saved view (a key, or the double-tap's next one)
at(integer i)
{
    list v = views();
    if (i >= llGetListLength(v))
    {
        show("No View " + llList2String(["A", "B"], i) + " here yet · Save one first");
        return;
    }
    gPick = i;
    lit();
    list p = llParseString2List(llList2String(v, gPick), ["|"], []);
    shot((vector)llList2String(p, 0), (vector)llList2String(p, 1));
    show("View " + llList2String(["A", "B"], gPick));
}

// your lens changed: the same picture, a new perspective. The camera dollies along its line to what you aimed at;
// a wall on the way stops it 0.3 m short (the ray starts half a metre off the subject, not on its surface)
zoom(float nf)
{
    if (!gHeld) return;                                     // framing: the lens is yours; the lock keeps its own
    if (gFov > 0.05 && nf > 0.05 && gCam != ZERO_VECTOR)
    {
        float k = llTan(gFov * 0.5) / llTan(nf * 0.5);
        vector nc = gFoc + (gCam - gFoc) * k;
        vector s = gFoc + llVecNorm(gCam - gFoc) * 0.5;
        list r = llCastRay(s, nc, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
        if (llList2Integer(r, -1) > 0) nc = llList2Vector(r, 1) + llVecNorm(gFoc - nc) * 0.3;
        if (llVecDist(nc, gFoc) > 0.3)
        {
            gCam = nc;
            llMessageLinked(LINK_SET, GLIDE, (string)gCam + "|" + (string)gFoc + "|1.5", "");
        }
    }
    gFov = nf;
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "free");
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id != NULL_KEY) llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == START)
        {
            gActive = (llList2String(llParseString2List(str, ["|"], []), 0) == "free");
            if (!gActive) return;
            llMessageLinked(LINK_SET, ACK, "free", "");
            gPick = -1;
            lit();
            here();                                         // your view as it is: held, no jump
        }
        else if (num == STOP) gActive = FALSE;
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "free");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/free] v" + VERSION + " active " + (string)gActive + ", " + (string)llGetListLength(views())
                + " saved views here, free mem " + (string)llGetFreeMemory());
        else if (!gActive) return;
        else if (num == NEXT)
        {
            if (str == "skip") recall();
            else here();
        }
        else if (num == CAMSET)
        {
            list L = llParseString2List(str, ["|"], []);    // every lock and glide: the view held now
            gCam = (vector)llList2String(L, 0);
            gFoc = (vector)llList2String(L, 1);
            gFov = (float)llList2String(L, 3);
        }
        else if (num == UI_STATE) gHeld = (llGetSubString(str, 0, 7) == "rolling|");
        else if (num == FOVMSG) zoom((float)str);
        else if (num == CMD && str == "fav") save();
        else if (num == CMD && llGetSubString(str, 0, 4) == "view|") at((integer)llGetSubString(str, 5, -1));
    }

    timer()
    {
        if (gTextT > 0.0 && llGetTime() - gTextT > 3.0)
        {
            if (llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0) == gNote) llSetText("", ZERO_VECTOR, 0.0);
            gTextT = 0.0;
        }
        if (gTextT == 0.0) llSetTimerEvent(0.0);
    }
}
