// ============================================================================
//  Take 12  -  fit.lsl  (v6.7)  - Fit: Page Up / Page Down move the camera up or down
//  Second Life plays poses in the viewer: no script can see where your body really is in a seat, on the ground, in
//  heels. So you show it once, by eye. While a people camera runs (Me, Us, Only friends, Still), core hands this
//  script Page Up / Page Down (E / C; they never make you jump; flying, they fly): a tap moves the camera 5 cm up or
//  down, holding speeds up (10 cm/s at first, 50 cm/s after about 2 s). No script can see Shift, so the hold is the
//  big move. The shot on screen glides at once (FIT to core); every next shot is planned with it (cin.fitz, read
//  by people, friends and frame: they frame as if your eyes were that much higher).
//  6.7.1: Page Up raises the camera (6.7.0 moved you up in the picture, which read as the camera going down); the
//  values are kept under new names (fitc.*), so 6.7.0's start over.
//  Kept per seat (the object you sit on and where on it; the last 20 seats), one for sitting on the ground and one
//  for standing. One key pair, no mode (5.0's Tune per seat needed a mode and more keys, and 5.1 took it out).
//  Checked in tools/sim/fit_sim.py.
// ============================================================================

string VERSION = "6.7.1";
string PASS    = "cinema-1.0-build1";

integer UI_STATE   = 7320;   // core -> all  "<state>|<mode>|..."
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer FITKEY     = 7396;   // core -> here  "<keys held: 16 Page Up, 32 Page Down>"
integer FIT        = 7397;   // here -> core  "<dz>": the shot on screen moves dz metres (next shots read cin.fitz)

float   STEP  = 0.05;        // m  a tap
float   SLOW  = 0.01;        // m  each 0.1 s while held, from 0.4 s ...
float   GROW  = 0.025;       // m  ... plus this per second held ...
float   FAST  = 0.05;        // m  ... up to this (50 cm/s)
float   LIMIT = 1.5;         // m  either way
integer SEATS = 20;

key     gOwner;
string  gCtx;                // "stand", "ground" or the key of the object you sit on
float   gFit;                // m  the camera: + up (Page Up)
integer gKeys;
float   gDownT;              // the key went down at
integer gOn;                 // a people camera runs
string  gNote;
float   gTextT;

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

set(string k, string v)
{
    llLinksetDataWriteProtected("cin." + k, v, PASS);
}

// where you are: standing, on the ground, or on a seat: the object you sit on and where on it, to half a metre (each
// side of a sofa or a bed keeps its own)
string ctx()
{
    integer i = llGetAgentInfo(gOwner);
    if (!(i & AGENT_SITTING)) return "stand";
    if (!(i & AGENT_ON_OBJECT)) return "ground";
    list d = llGetObjectDetails(gOwner, [OBJECT_ROOT, OBJECT_POS]);
    key r = llList2Key(d, 0);
    list o = llGetObjectDetails(r, [OBJECT_POS, OBJECT_ROT]);
    vector v = (llList2Vector(d, 1) - llList2Vector(o, 0)) / llList2Rot(o, 1);
    return (string)r + "@" + (string)llRound(v.x * 2.0) + ":" + (string)llRound(v.y * 2.0);
}

// the fit for where you are now, for the cameras
look()
{
    string c = ctx();
    if (c == gCtx) return;
    gCtx = c;
    gFit = (float)cfg("fitc." + c);
    set("fitz", (string)gFit);
}

// keep it; a seat goes to the end of the list, the oldest seat beyond 20 is forgotten
keep()
{
    set("fitc." + gCtx, (string)gFit);
    if (gCtx == "stand" || gCtx == "ground") return;
    list L = llParseString2List(cfg("fitcseats"), [","], []);
    integer i = llListFindList(L, [gCtx]);
    if (i >= 0) L = llDeleteSubList(L, i, i);
    L += [gCtx];
    if (llGetListLength(L) > SEATS)
    {
        llLinksetDataDeleteProtected("cin.fitc." + llList2String(L, 0), PASS);
        L = llDeleteSubList(L, 0, 0);
    }
    set("fitcseats", llDumpList2String(L, ","));
}

// a step up (+) or down (-): the shot glides, the line above the button says it
move(float d)
{
    float f = gFit + d;
    if (f > LIMIT) f = LIMIT;
    if (f < -LIMIT) f = -LIMIT;
    if (f == gFit) return;
    llMessageLinked(LINK_SET, FIT, (string)(f - gFit), "");
    gFit = f;
    set("fitz", (string)gFit);
    string s = "Fit " + llList2String(["", "+"], gFit > 0.004) + (string)llRound(gFit * 100.0) + " cm";
    if (llRound(gFit * 100.0) == 0) s = "Fit 0 · automatic";
    show(s + " · " + llList2String(["this seat", "standing", "sitting on the ground"], llListFindList(["stand", "ground"], [gCtx]) + 1));
}

// a short notice above the button, read back as Second Life keeps it; tips draws the line again afterwards
show(string s)
{
    llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gNote = llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0);
    gTextT = llGetTime();
}

// fast while a key is held or a notice is up; once a second while a people camera runs (you may sit or stand)
tick()
{
    float t = 0.0;
    if (gOn) t = 1.0;
    if (gKeys || gTextT > 0.0) t = 0.1;
    llSetTimerEvent(t);
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        look();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "fit");
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
        if (num == FITKEY)
        {
            look();
            integer k = (integer)str * gOn;                 // held, paused, Photo: the keys do nothing
            if (k & ~gKeys & 16) move(STEP);              // a new press: one step at once
            if (k & ~gKeys & 32) move(-STEP);
            if (k && !gKeys) gDownT = llGetTime();
            if (!k && gKeys) keep();                        // let go: kept
            gKeys = k;
        }
        else if (num == UI_STATE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            gOn = (llList2String(L, 0) == "rolling" && llListFindList(["personal", "social", "friends", "frame"], [llList2String(L, 1)]) >= 0);
            if (!gOn && gKeys) keep();
            if (!gOn) gKeys = 0;
            look();
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "fit");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/fit] v" + VERSION + " " + gCtx + ": " + (string)llRound(gFit * 100.0) + " cm, "
                + (string)llGetListLength(llParseString2List(cfg("fitcseats"), [","], [])) + " seats kept, free mem " + (string)llGetFreeMemory());
        else return;
        tick();
    }

    timer()
    {
        float h = llGetTime() - gDownT;
        if (gKeys && h > 0.4)
        {
            float v = SLOW + GROW * (h - 0.4);              // held: slow at first for precision, then fast
            if (v > FAST) v = FAST;
            move(v * ((gKeys & 16) > 0) - v * ((gKeys & 32) > 0));
        }
        if (gTextT > 0.0 && llGetTime() - gTextT > 3.0)
        {
            if (llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0) == gNote) llSetText("", ZERO_VECTOR, 0.0);
            gTextT = 0.0;
        }
        if (gOn && !gKeys) look();                          // you sat down, stood up, changed seats
        tick();
    }
}
