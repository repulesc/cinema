// ============================================================================
//  Take 12  -  fit.lsl  (v7.1)  - Adjust: the keys trim the shot (and Fit: Page Up / Page Down, the height)
//  7.1: Adjust. Seated the keys always adjust; standing they walk you, until you tap ADJUST (the keys strip, the live
//  menu, /77 adjust). Then core keeps them from your avatar and hands them here (FITKEY, the keys held):
//    W / S (up / down arrows)     tilt the camera up or down            1 degree a tap, up to 15 degrees/s held
//    A / D (left / right arrows)  swing it around you                   3 degrees a tap, up to 45 degrees/s
//    Shift + A / D                slide it sideways                     5 cm a tap, up to 50 cm/s
//    Page Up / Page Down          the height (Fit)                      10 cm a tap, up to 60 cm/s
//  Holding speeds up, full speed after about a second (no script can see Shift on its own, so holding is the big
//  move). Tilt, swing and slide go to core (TRIM), which puts them on every shot: in Me until Full / Half / Close
//  change or the camera stops; in Us and Friends adjusting holds that shot until Next (core resets, FITKEY "r").
//  Fit, the height, is kept per seat (the object you sit on and where on it; the last 20 seats), one for sitting on
//  the ground and one for standing; people, friends and frame read it (cin.fitz) and plan every shot with it. In
//  Freehand the height is for that view only. While a people camera runs, Page Up / Page Down are Fit's even when you
//  walk (they never make you jump; flying, they fly). 7.1.1: this script keeps Page Up / Down from your avatar with
//  its own control request (one script holds one set of controls: core's request is all the movement keys, which
//  it routes here). The Adjust notice stays 6 s and comes back once, 15 s later, until you press a key.
//  Checked in tools/sim/fit_sim.py.
// ============================================================================

string VERSION = "7.1.3";
string PASS    = "cinema-1.0-build1";

integer UI_STATE   = 7320;   // core -> all  "<state>|<mode>|<next cut>|<why>|<adjust>|<fit>"
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer FITKEY     = 7396;   // core -> here  "<keys held>" (Adjust: all of them; else Page Up 16 / Page Down 32), "r": a new shot
integer FIT        = 7397;   // here -> core  "<dz>": the shot on screen moves dz metres (next shots read cin.fitz)
integer TRIM       = 7398;   // here -> core  "<tilt rad>|<swing rad>|<slide m>": Adjust, on every shot

// the four axes: height (Page Up 16 / Page Down 32), tilt (W 1 / S 2), swing (A 256 / D 512), slide (Shift+D 8 / Shift+A 4)
list    UPS   = [16, 1, 256, 8];
list    DOWNS = [32, 2, 512, 4];
list    STEPS = [0.10, 0.017453, 0.05236, 0.05];   // a tap: 10 cm, 1 degree, 3 degrees, 5 cm
list    RATES = [0.6, 0.2618, 0.7854, 0.5];        // held, full speed (per second): 60 cm, 15 degrees, 45 degrees, 50 cm
list    LIMITS= [1.5, 0.43633, 1.309, 1.5];        // either way: 1.5 m, 25 degrees, 75 degrees, 1.5 m
float   RAMP  = 0.3;         // s  a hold starts after this, slow (a fifth of full speed) ...
float   FULL  = 1.0;         // s  ... and runs at full speed from here
integer SEATS = 20;

key     gOwner;
string  gCtx;                // "stand", "ground" or the key of the object you sit on
float   gFit;                // m  the camera: + up (Page Up)
vector  gT;                  // Adjust: <tilt, swing, slide> (+ up, + to your left around you, + to the right)
integer gKeys;
float   gDownT;              // a key went down at
integer gOn;                 // a camera Adjust works in runs
integer gAdj;                // the keys adjust (core: seated, or ADJUST)
integer gFree;               // Freehand: the height is for this view only
integer gTaps;               // the first taps say that a hold is faster
integer gHold48;              // Page Up / Down are kept from your avatar (no jump) by this script's request
integer gWant48;             // ... and should be (UI_STATE)
float   gHelpT;              // Adjust turned on at (0: the help has come back once, or a key was pressed)
string  gNote;
float   gTextT;
float   gTextFor = 3.0;      // s  this notice stays

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
    gFit = 0.0;                                             // Freehand: each view starts level
    if (gFree) return;
    gFit = (float)cfg("fitc." + c);
    set("fitz", (string)gFit);
}

// keep it; a seat goes to the end of the list, the oldest seat beyond 20 is forgotten
keep()
{
    if (gFree) return;
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

// axis a moves by d (+ up, left, right): the shot glides, the line above the button says it
move(integer a, float d)
{
    float lim = llList2Float(LIMITS, a);
    float v = gFit;
    if (a == 1) v = gT.x;
    if (a == 2) v = gT.y;
    if (a == 3) v = gT.z;
    float f = v + d;
    if (f > lim) f = lim;
    if (f < -lim) f = -lim;
    if (f == v) return;
    string s;
    if (a == 0)
    {
        llMessageLinked(LINK_SET, FIT, (string)(f - gFit), "");
        gFit = f;
        if (!gFree) set("fitz", (string)gFit);
        s = "Height " + sgn(gFit * 100.0) + " cm · " + llList2String(["this seat", "standing", "on the ground"], llListFindList(["stand", "ground"], [gCtx]) + 1);
        if (gFree) s = "Height " + sgn(gFit * 100.0) + " cm · this view";
    }
    else
    {
        if (a == 1) gT.x = f;
        if (a == 2) gT.y = f;
        if (a == 3) gT.z = f;
        llMessageLinked(LINK_SET, TRIM, (string)gT.x + "|" + (string)gT.y + "|" + (string)gT.z, "");
        s = "Tilt " + sgn(gT.x * RAD_TO_DEG) + "° · Around " + sgn(gT.y * RAD_TO_DEG) + "° · Side " + sgn(gT.z * 100.0) + " cm";
    }
    if (gTaps < 3 && !gKeys) s += "\nhold: faster";
    show(s);
}

string sgn(float v)
{
    integer i = llRound(v);
    if (i > 0) return "+" + (string)i;
    return (string)i;
}

// a short notice above the button, read back as Second Life keeps it; tips draws the line again afterwards
show(string s)
{
    llSetText(s, <1.0, 1.0, 1.0>, 0.85);
    gNote = llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0);
    gTextT = llGetTime();
    gTextFor = 3.0;
}

// how Adjust works, for a while (6 s, then once more for 4 s after 15 s unless you pressed a key)
help(float t)
{
    show("Adjust · W/S tilt · A/D around · Shift+A/D side · PgUp/PgDn height");
    gTextFor = t;
}

// Page Up / Down: kept from your avatar while they are Fit's, given back otherwise (the permission stays)
hold(integer on)
{
    if (on == gHold48 || !(llGetPermissions() & PERMISSION_TAKE_CONTROLS)) return;
    gHold48 = on;
    if (on) llTakeControls(48, TRUE, FALSE);
    else llTakeControls(48, FALSE, TRUE);
}

// fast while a key is held or a notice is up; once a second while a camera runs (you may sit or stand)
tick()
{
    float t = 0.0;
    if (gOn) t = 1.0;
    if (gKeys || gTextT > 0.0) t = 0.1;                     // (gHelpT: the 1 s tick while a camera runs is enough)
    llSetTimerEvent(t);
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        look();
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_TAKE_CONTROLS);   // an attachment: granted without asking
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "fit");
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id != NULL_KEY) llRequestPermissions(gOwner, PERMISSION_TAKE_CONTROLS);
    }

    run_time_permissions(integer p)
    {
        gHold48 = FALSE;
        hold(gWant48);                                      // re-attached while a camera runs
    }

    // the keys reach core (it routes them here as FITKEY); this request only keeps Page Up / Down from your avatar
    control(key id, integer level, integer edge)
    {
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == FITKEY && str == "r")
        {
            gT = ZERO_VECTOR;                               // a new shot, a new view: Adjust starts clean
            if (gFree) gFit = 0.0;
        }
        else if (num == FITKEY)
        {
            look();
            integer k = (integer)str * gOn;                 // held, paused: the keys do nothing
            if (cfg("trace") == "1") llOwnerSay("[Take 12] keys " + str);   // what the viewer sends (Shift + Page Down?)
            integer a;
            for (a = 0; a < 4; a++)
            {
                if (k & ~gKeys & llList2Integer(UPS, a)) move(a, llList2Float(STEPS, a));   // a new press: one step at once
                if (k & ~gKeys & llList2Integer(DOWNS, a)) move(a, -llList2Float(STEPS, a));
            }
            if (k && !gKeys) gDownT = llGetTime();
            if (k) gHelpT = 0.0;                            // you found the keys: the help does not come back
            if (!k && gKeys)
            {
                keep();                                     // let go: kept
                gTaps++;
            }
            gKeys = k;
        }
        else if (num == UI_STATE)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            string m = llList2String(L, 1);
            gOn = (llList2String(L, 0) == "rolling" && llListFindList(["personal", "social", "friends", "frame", "free"], [m]) >= 0);
            integer adj = (integer)llList2String(L, 4) * gOn;
            gWant48 = (integer)llList2String(L, 5);         // core: a people camera runs (or Freehand, adjusting), not flying
            hold(gWant48);                                  // no jump while Page Up / Down are Fit's
            if (gFree != (m == "free")) gCtx = "";            // Freehand's height is its own; back from it, the seat's again
            gFree = (m == "free");
            if (adj != gAdj && gOn)
            {
                if (adj)
                {
                    help(6.0);
                    gHelpT = llGetTime();
                }
                else
                {
                    show("Walk · the keys move you");
                    gHelpT = 0.0;
                }
            }
            gAdj = adj;
            if (!gOn && gKeys) keep();
            if (!gOn) gKeys = 0;
            look();
        }
        else if (num == CMD && str == "adjust" && gOn && (llGetAgentInfo(gOwner) & AGENT_SITTING)) show("Seated · the keys adjust");
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "fit");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/fit] v" + VERSION + " " + gCtx + ": " + (string)llRound(gFit * 100.0) + " cm, adjust " + (string)gAdj + " "
                + (string)gT + ", " + (string)llGetListLength(llParseString2List(cfg("fitcseats"), [","], [])) + " seats kept, free mem " + (string)llGetFreeMemory());
        else return;
        tick();
    }

    timer()
    {
        float h = llGetTime() - gDownT;
        if (gKeys && h > RAMP)
        {
            float r = 0.2 + 0.8 * (h - RAMP) / (FULL - RAMP);   // held: slow at first for precision, then fast
            if (r > 1.0) r = 1.0;
            integer a;
            for (a = 0; a < 4; a++)
            {
                float v = llList2Float(RATES, a) * 0.1 * r;
                if (gKeys & llList2Integer(UPS, a)) move(a, v);
                if (gKeys & llList2Integer(DOWNS, a)) move(a, -v);
            }
        }
        if (gHelpT > 0.0 && gAdj && llGetTime() - gHelpT > 15.0)
        {
            gHelpT = 0.0;
            help(4.0);                                      // once more, in case you missed it
        }
        if (gTextT > 0.0 && llGetTime() - gTextT > gTextFor)
        {
            if (llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0) == gNote) llSetText("", ZERO_VECTOR, 0.0);
            gTextT = 0.0;
        }
        if (gOn && !gKeys) look();                          // you sat down, stood up, changed seats
        tick();
    }
}
