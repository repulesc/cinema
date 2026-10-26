// ============================================================================
//  Take 12  -  core.lsl  (v4)
//  Owns the camera. Modes: scenery (default, AFK + double-tap), personal, social, friends, frame, free (Freehand, 6.4)
//  and friends (optional, from the menu). Photo hold (freeze), glide (friends). Triggers, exits, hold timer, Alt-cam peek,
//  pauses, a watchdog with a basic fallback shot per mode, reach verification.
//  All four scripts (core, scenery, people, ui) go in the ROOT prim of the HUD.
// ============================================================================

string VERSION = "7.2.0";
string PASS    = "cinema-1.0-build1";   // protected Linkset-Data password, same in all scripts
integer LITE    = 0;                      // the free Take 12 Scenery build (tools/build_scenery.py) sets this to 1: scenery camera only

integer START      = 7301;   // core -> workers  "<mode>|<fov>"
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer MOVING     = 7306;
integer SHOT       = 7310;   // worker -> core   "<pos>|<focus>|<hold>|<type>"
integer NO_SHOT    = 7311;
integer GLIDE      = 7312;   // friends, frame, people -> core  "<pos>|<focus>" or "<pos>|<focus>|<lag>"
integer ACK        = 7313;
integer REACH_FAIL = 7314;   // core -> scenery  "<asked distance>|<distance the viewer allowed>"
integer SPEAKER    = 7315;   // core -> social / friends  owner key (you started typing)
integer NUDGE      = 7317;   // core -> frame, lens  "<keys held now>|<camera rotation>"
integer FITKEY     = 7396;   // core -> fit  "<Page Up 16 / Page Down 32 held>": Fit (fit.lsl)
integer FIT        = 7397;   // fit -> core  "<dz>": the shot on screen moves dz metres up
integer TRIM       = 7398;   // fit -> core  "<tilt>|<swing>|<slide>": Adjust, put on every shot (7.1)
integer CAMSET     = 7325;   // core -> sync     "<pos>|<focus>|<lag>|<lens>": every camera put on screen (Share the view)
integer LEAD       = 7324;   // core -> lens     "<cam>|<focus>": in Friends, your own view held still (Follow my lead)
integer FOVMSG     = 7318;   // core -> cameras, tips  the viewer's field of view changed (radians): your lens
integer UI_STATE   = 7320;   // core -> ui, tips, keys, fit, crop  "<state>|<mode>|<nextCutUnix>|<why>|<adjust: the keys trim the shot>|<fit: Page Up / Down are Fit's>"
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;   // ui -> core  scenery / social / friends / frame / free / stop / next / grab
integer CTL = 831;           // CONTROL_FWD | BACK | LEFT | RIGHT | ROT_LEFT | ROT_RIGHT | UP | DOWN

float FIRST_WAIT  = 1.5;     // s  wait for the first shot, then cut to a basic shot
float NEXT_WAIT   = 2.5;     // s  wait for the next shot
float BASIC_HOLD  = 20.0;    // s  hold of a basic shot
float PEEK_GRACE  = 2.5;     // s  after a cut, before the camera is checked
list  FB_ANG      = [140.0, -140.0, 40.0, -40.0, 175.0];

integer ST_IDLE  = 0;
integer ST_WAIT  = 1;
integer ST_ROLL  = 2;
integer ST_PAUSE = 3;
integer ST_PEEK  = 4;
integer ST_TEST  = 5;

key     gOwner;
integer gNeed;
integer gSitMask;
integer gPermOK;
integer gState;
string  gMode;                // "scenery" / "personal" / "social" / "friends" / "frame"
string  gWhy;                // "idle": the idle start began this run (shown above the HUD)
float   gFovSent;             // frame: the field of view last reported
integer gType;                // type of the shot on screen
integer gSitBase;
integer gWatch;               // you are watching someone's shared view: no idle start, double-tap cuts for all (sync)
integer gSitCtl;              // the controls were taken seated
integer gFitCtl;              // Page Up / Down are Fit's (a people camera runs, you are not flying)
integer gAdjOn;               // ADJUST: standing, the keys trim the shot instead of walking you (seated they always do)
integer gAdj;                 // the keys trim the shot now (fit.lsl)
integer gHeld;                // Us, Friends: you adjusted this shot, so it is held until Next
vector  gTrim;                // Adjust: <tilt rad, swing rad, slide m>, put on every shot (fit.lsl)
vector  gBaseP;               // the shot as its camera planned it, before Adjust
vector  gBaseF;
float   gFitShift;            // m  Fit moved the shot on screen since its camera planned it (added to that camera's glides)
float   gLeadT;               // friends: your own camera, and since when it is still
vector  gLeadP;
rotation gLeadR;
integer gLastAct;
integer gNoEngageUntil;
integer gIgnoreCtl;
integer gMovSent;
integer gResumeAt;
integer gWorkerOK;            // the mode's worker script answered this session
integer gAsking;
integer gWarned;
integer gVerify;              // first camera check after a cut still pending
integer gFb;
integer gPending;
integer gGlided;              // a glide moved the camera since the last cut
integer gTypeSent;
integer gNextCut;
string  gPauseWhy;
string  gLast;
float   gAskT;
float   gHold;
float   gApplyT;
float   gLastTick;
float   gGlideUntil;
vector  gShotPos;
vector  gShotFoc;
vector  gCamBefore;            // where the viewer had the camera just before the cut
vector  gCamPos;
rotation gCamRot;

integer gAfkOn;
integer gAfkSec;
integer gAfkAway;             // mouse check: also wait for the viewer's Away (it notices the mouse)
integer gPeekOn;
integer gPeekBail;
integer gCutMode;
integer gTrace;

// ============================================================================
string cfg(string k, string d)
{
    string v = llLinksetDataReadProtected("cin." + k, PASS);
    if (v == "") return d;
    return v;
}

loadCfg()
{
    gAfkOn    = (integer)cfg("afk_on", "1");
    string a  = cfg("afk_sec", "180");
    gAfkSec   = (integer)a;
    if (gAfkSec < 30) gAfkSec = 180;
    gAfkAway  = (integer)cfg("afk_away", "1");
    gPeekOn   = (integer)cfg("peek", "1");
    gPeekBail = (integer)cfg("peek_bail", "0");
    gCutMode  = (integer)cfg("cutmode", "0");
    gTrace    = (integer)cfg("trace", "0");
}

setUi(string st)
{
    llMessageLinked(LINK_SET, UI_STATE, st + "|" + gMode + "|" + (string)gNextCut + "|" + gWhy + "|" + (string)gAdj + "|" + (string)gFitCtl, "");
}

string idleUi()
{
    if (gAfkOn) return "armed";
    return "off";
}

vector ownerPos()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS]);
    if (llGetListLength(d) == 0) return ZERO_VECTOR;
    return llList2Vector(d, 0);
}

float clampf(float v, float lo, float hi)
{
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

// ---- camera ------------------------------------------------------------------
// the shot, with Adjust on top: gShotPos / gShotFoc. Swing turns the camera around the focus, slide moves both
// sideways, tilt raises or lowers the focus; a camera that would end up behind a wall stays in front of it.
place(vector p, vector f)
{
    gBaseP = p;
    gBaseF = f;
    if (gTrim != ZERO_VECTOR)
    {
        vector d = (p - f) * llAxisAngle2Rot(<0.0, 0.0, 1.0>, -gTrim.y);
        f += llVecNorm(<0.0, 0.0, 1.0> % d) * gTrim.z;
        p = f + d;
        if (gTrim.y != 0.0 || gTrim.z != 0.0)
        {
            list h = llCastRay(f, p, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
            if (llList2Integer(h, -1) == 1) p = llList2Vector(h, 1) + llVecNorm(f - p) * 0.3;
        }
        f.z += llVecMag(<d.x, d.y, 0.0>) * llTan(gTrim.x);
    }
    gShotPos = p;
    gShotFoc = f;
}

// Adjust starts clean: a new shot in Us / Friends, Next, a new framing or view, the camera stops
untrim()
{
    gTrim = ZERO_VECTOR;
    gHeld = FALSE;
    llMessageLinked(LINK_SET, FITKEY, "r", "");
}

setCam(vector p, vector f)
{
    place(p, f);
    p = gShotPos;
    f = gShotFoc;
    gCamBefore = llGetCameraPos();
    if (gCutMode || gGlided) llClearCameraParams();
    gGlided = FALSE;
    llSetCameraParams([
        CAMERA_ACTIVE, TRUE,
        CAMERA_POSITION, p,
        CAMERA_FOCUS, f,
        CAMERA_POSITION_LOCKED, TRUE,
        CAMERA_FOCUS_LOCKED, TRUE,
        CAMERA_POSITION_LAG, 0.0,
        CAMERA_FOCUS_LAG, 0.0,
        CAMERA_POSITION_THRESHOLD, 0.0,
        CAMERA_FOCUS_THRESHOLD, 0.0
    ]);
    llMessageLinked(LINK_SET, CAMSET, (string)p + "|" + (string)f + "|0|" + (string)llGetCameraFOV(), "");
    gApplyT = llGetTime();
    gVerify = TRUE;
}

// "<pos>|<focus>|<hold>|<type>"
applyShot(string s)
{
    list L = llParseStringKeepNulls(s, ["|"], []);
    gHold = (float)llList2String(L, 2);
    gType = (integer)llList2String(L, 3);
    gFitShift = 0.0;                                // a new shot is planned with Fit already
    if ((gMode == "social" || gMode == "friends") && s != gLast) untrim();   // a new cut (not the same one after a pause): its own picture
    gLast = s;
    gPending = FALSE;
    gAsking = FALSE;
    setCam((vector)llList2String(L, 0), (vector)llList2String(L, 1));
    gNextCut = llGetUnixTime() + llRound(gHold);
    gState = ST_ROLL;
    setUi("rolling");
}

// move the camera on screen, eased by the viewer over the lag (glides: friends, frame, the dolly, Fit)
glide(vector gp, vector gf, float lag)
{
    place(gp, gf);
    llSetCameraParams([CAMERA_POSITION, gShotPos, CAMERA_FOCUS, gShotFoc, CAMERA_POSITION_LAG, lag, CAMERA_FOCUS_LAG, lag]);
    llMessageLinked(LINK_SET, CAMSET, (string)gShotPos + "|" + (string)gShotFoc + "|" + (string)lag + "|" + (string)llGetCameraFOV(), "");
    gGlideUntil = llGetTime() + 3.0;
    gGlided = TRUE;
    list O = llParseStringKeepNulls(gLast, ["|"], []);
    gLast = (string)gp + "|" + (string)gf + "|" + llList2String(O, 2) + "|" + llList2String(O, 3);
}

// first surface found going down at (x, y) from zTop to zBottom; zBottom if none
float surfaceAt(float x, float y, float zTop, float zBottom)
{
    list r = llCastRay(<x, y, zTop>, <x, y, zBottom>, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
    if (llList2Integer(r, -1) != 1) return zBottom;
    vector h = llList2Vector(r, 1);
    return h.z;
}

// basic shot when the mode's worker script is silent:
// scenery = high behind you looking down over your area (outdoors only); otherwise a level portrait orbit
basicShot()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2) return;
    vector P = llList2Vector(d, 0);
    vector F = llRot2Fwd(llList2Rot(d, 1));
    F.z = 0.0;
    if (llVecMag(F) < 0.01) F = <1.0, 0.0, 0.0>;
    F = llVecNorm(F);
    vector cam;
    vector foc;
    // scenery's high view from behind would be outside any building: under a roof (or if the ray is refused) use
    // the close view of you instead, which stays inside
    integer roof = FALSE;
    if (gMode == "scenery")
    {
        list u = llCastRay(P + <0.0, 0.0, 1.0>, P + <0.0, 0.0, 40.0>, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
        roof = (llList2Integer(u, -1) != 0);
    }
    if (gMode == "scenery" && !roof)
    {
        cam = P - F * 15.0;
        cam.x = clampf(cam.x, 3.0, 253.0);
        cam.y = clampf(cam.y, 3.0, 253.0);
        cam.z = surfaceAt(cam.x, cam.y, P.z + 80.0, P.z - 20.0) + 10.0;
        foc = P + F * 10.0;
        foc.z = P.z - 1.0;
    }
    else
    {
        vector sz = llGetAgentSize(gOwner);
        vector E = <P.x, P.y, P.z + 0.37 * sz.z>;
        vector dir = F * llEuler2Rot(<0.0, 0.0, llList2Float(FB_ANG, gFb % 5) * DEG_TO_RAD>);
        gFb++;
        float dist = 3.0;
        list r = llCastRay(E, E + dir * dist, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
        if (llList2Integer(r, -1) == 1) dist = llVecDist(E, llList2Vector(r, 1)) - 0.4;
        if (dist < 1.2) dist = 1.2;
        cam = E + dir * dist;
        cam.z = E.z - dist * 0.19245;              // eye line on the upper third, camera level
        foc = <E.x, E.y, cam.z>;
    }
    applyShot((string)cam + "|" + (string)foc + "|" + (string)BASIC_HOLD + "|9");
}

askWorker(string why)
{
    gAsking = TRUE;
    gAskT = llGetTime();
    if (gWorkerOK) llMessageLinked(LINK_SET, NEXT, why, "");
    else llMessageLinked(LINK_SET, START, gMode + "|" + (string)llGetCameraFOV(), "");
}

// Page Up / Down (UP 16, DOWN 32) belong to Fit while a people camera runs, unless you fly: never a jump. In Freehand
// only while you adjust.
integer fitOK(integer info)
{
    if (gState == ST_IDLE || (info & AGENT_FLYING)) return FALSE;
    if (llListFindList(["personal", "social", "friends", "frame"], [gMode]) >= 0) return TRUE;
    return (gMode == "free" && (gAdjOn || (info & AGENT_SITTING)));
}

// the movement keys: passed on to your avatar (in Framing › Me too, which follows you as you walk; it hears NUDGE).
// 7.1, Adjust: seated (you cannot walk anyway), or standing after ADJUST, all of them are kept back and trim the shot.
// 7.1.1: ONE request. A script holds one set of controls and a second llTakeControls replaces the first (7.0 and
// 7.1.0 took Page Up / Down last, so the movement keys were not taken at all: Adjust walked you, Me never heard
// you walk). Page Up / Down are kept from your avatar by fit.lsl's own request (UI_STATE: Fit is on), not here.
takeCtl(integer pass)
{
    integer info = llGetAgentInfo(gOwner);
    gSitCtl = info & AGENT_SITTING;
    integer was = gFitCtl;
    integer adj = gAdj;
    gFitCtl = fitOK(info);
    gAdj = (gFitCtl && (gAdjOn || gSitCtl));
    llTakeControls(CTL, TRUE, pass && !gAdj);
    if ((was && !gFitCtl) || (adj && !gAdj)) llMessageLinked(LINK_SET, FITKEY, "0", "");   // flying, stopped, walking again while held: let go
    if (gAdj && !adj && gMode == "frame") llMessageLinked(LINK_SET, NUDGE, "0|" + (string)llGetCameraRot(), "");   // Me: no longer walking
    if ((adj != gAdj || was != gFitCtl) && gState != ST_IDLE) setUi(llList2String(["rolling", "peek"], gState == ST_PEEK));
}

// ---- lifecycle ------------------------------------------------------------------
// instant return to the user's own camera
bail(string why)
{
    if (gPermOK) llClearCameraParams();
    gState = ST_IDLE;
    gAsking = FALSE;
    gPending = FALSE;
    gPauseWhy = "";
    gTypeSent = FALSE;
    gLastAct = llGetUnixTime();
    gNoEngageUntil = gLastAct + 10;
    gAdjOn = FALSE;
    untrim();
    llMessageLinked(LINK_SET, STOP, why, "");
    if (gPermOK) takeCtl(TRUE);                     // the keys back to your avatar (Frame, seated friends, Fit)
    setUi(idleUi());
    llSetTimerEvent(2.0);
}

engage(string mode)
{
    if (!gPermOK)
    {
        llOwnerSay("[Take 12] No camera permission yet - re-attach the HUD.");
        llRequestPermissions(gOwner, gNeed);
        return;
    }
    if (gState != ST_IDLE) llMessageLinked(LINK_SET, STOP, "switch", "");
    gMode = mode;
    gWhy = "";
    gState = ST_WAIT;
    gWorkerOK = FALSE;
    gWarned = FALSE;
    gLast = "";
    gType = 0;
    gSitBase = llGetAgentInfo(gOwner) & gSitMask;
    gLastAct = llGetUnixTime();
    gLastTick = llGetTime();
    gFovSent = llGetCameraFOV();
    gAdjOn = FALSE;
    untrim();
    takeCtl(TRUE);
    askWorker("start");
    setUi("rolling");
    if (gTrace) llOwnerSay("[Take 12] " + mode + " camera on");
    llSetTimerEvent(0.5);
}

pause(string why)
{
    gPauseWhy = why;
    gState = ST_PAUSE;
    gResumeAt = llGetUnixTime() + 3;
    llMessageLinked(LINK_SET, PAUSE, why, "");
}

resume()
{
    string why = gPauseWhy;
    gPauseWhy = "";
    llMessageLinked(LINK_SET, RESUME, why, "");
    gState = ST_WAIT;
    if (why != "tp" && gLast != "") applyShot(gLast);
    else if (gWorkerOK)
    {
        gAsking = TRUE;                             // the worker re-frames on RESUME by itself
        gAskT = llGetTime();
    }
    else askWorker("resume");
}

// ============================================================================
idleTick(integer now)
{
    if (!gPermOK || gWatch) return;
    integer info = llGetAgentInfo(gOwner);
    vector cp = llGetCameraPos();
    rotation cr = llGetCameraRot();
    // typing, mouselook or moving / orbiting the camera = the user is present
    if ((info & (AGENT_TYPING | AGENT_MOUSELOOK)) || llVecDist(cp, gCamPos) > 0.5 || llRot2Angle(cr / gCamRot) > 0.1) gLastAct = now;
    gCamPos = cp;
    gCamRot = cr;
    if (!gAfkOn || now < gNoEngageUntil || (info & (AGENT_TYPING | AGENT_MOUSELOOK))) return;
    // no keys, no typing, no camera moved for the chosen time; with the mouse check also the viewer's own Away
    // status, which the viewer clears on any mouse movement (a script cannot see the mouse itself)
    if (now - gLastAct >= gAfkSec && (!gAfkAway || (info & AGENT_AWAY)))
    {
        engage("scenery");
        if (gState != ST_IDLE)
        {
            gWhy = "idle";
            setUi("rolling");
        }
    }
}

activeTick(float dt)
{
    integer info = llGetAgentInfo(gOwner);
    if (info & AGENT_TYPING)
    {
        if (gMode == "scenery" || gMode == "personal") { bail("typing"); return; }
        if (!gTypeSent)
        {
            gTypeSent = TRUE;                       // social / friends: you are part of the scene
            llMessageLinked(LINK_SET, SPEAKER, (string)gOwner, "");
        }
    }
    else gTypeSent = FALSE;
    if (gMode == "scenery" && (info & gSitMask) != gSitBase) { bail("sit"); return; }
    if ((info & AGENT_SITTING) != gSitCtl || fitOK(info) != gFitCtl) takeCtl(TRUE);   // sat down, stood up, took off, landed
    if (info & AGENT_MOUSELOOK)
    {
        if (gState != ST_PAUSE) pause("ml");
        return;
    }
    if (gState == ST_PAUSE)
    {
        if (gPauseWhy == "showme" || (gPauseWhy == "tp" && llGetUnixTime() < gResumeAt)) return;   // Show me: until fit is done
        resume();
    }
    float fv = llGetCameraFOV();                    // the zoom is your lens: every camera keeps its picture for it
    if (llFabs(fv - gFovSent) > 0.004)
    {
        gFovSent = fv;
        llMessageLinked(LINK_SET, FOVMSG, (string)fv, "");
    }

    // worker slow or absent: cover with a basic shot so the camera never sits idle
    if (gAsking && (gState == ST_WAIT || gState == ST_ROLL))
    {
        float wait = NEXT_WAIT;
        if (gState == ST_WAIT) wait = FIRST_WAIT;
        if (llGetTime() - gAskT > wait)
        {
            if (!gWorkerOK && !gWarned)
            {
                gWarned = TRUE;
                llOwnerSay("[Take 12] The " + gMode + " script is not answering, so you get basic shots. Check that it is in this prim and running (Build > Scripts > Set Scripts to Running in Selection) and look at the Script Errors window.");
            }
            basicShot();
        }
    }

    if ((gState == ST_ROLL || gState == ST_PEEK) && llGetTime() - gApplyT > PEEK_GRACE && llGetTime() > gGlideUntil)
    {
        vector cp = llGetCameraPos();
        vector op = ownerPos();
        float want = llVecDist(gShotPos, op);
        if (gVerify)
        {
            // first check after a cut: did the viewer put the camera where we asked? Only a camera that moved
            // (not a stale or minimised viewer), straight out toward the spot but stopped short counts as a reach
            // limit; anything else is you orbiting or Alt-cam, which the peek check below handles.
            gVerify = FALSE;
            float got = llVecDist(cp, op);
            if ((gType == 5 || gType == 6 || gType == 7) && llVecDist(cp, gShotPos) > 3.0 && llVecDist(cp, gCamBefore) > 1.0
                && got > 15.0 && got < 0.9 * want && llVecNorm(cp - op) * llVecNorm(gShotPos - op) > 0.99)
            {
                llMessageLinked(LINK_SET, REACH_FAIL, (string)want + "|" + (string)got, "");
                return;
            }
        }
        else if (gPeekOn || gMode == "friends" || gMode == "free")
        {
            // Alt-cam / orbit: the viewer silently overrides scripted cameras
            integer dev = (llVecDist(cp, gShotPos) > 1.0 + 0.05 * want);
            rotation cr = llGetCameraRot();
            integer own = (gMode == "friends" || gMode == "free");   // your own framing becomes the shot
            // Friends, Freehand: a smaller move, or a turn of the view over about 10 degrees, is you taking the camera too
            if (own && (llVecDist(cp, gShotPos) > 0.3 || llRot2Fwd(cr) * llVecNorm(gShotFoc - gShotPos) < 0.985)) dev = TRUE;
            if (dev && gState == ST_ROLL)
            {
                if (gPeekBail && !own) { bail("camera"); return; }
                gState = ST_PEEK;
                setUi("peek");
                llMessageLinked(LINK_SET, PAUSE, "peek", "");
                gLeadT = llGetTime();
                gLeadP = cp;
                gLeadR = cr;
            }
            else if (dev && own)
            {
                // Follow my lead: your view, still for 1.5 s (Freehand: 1 s), becomes the shot (Esc hands the camera back to it)
                if (llVecDist(cp, gLeadP) > 0.05 || llAngleBetween(cr, gLeadR) > 0.02)
                {
                    gLeadT = llGetTime();
                    gLeadP = cp;
                    gLeadR = cr;
                }
                else if (llGetTime() - gLeadT > 1.5 - 0.5 * (gMode == "free"))
                {
                    list O = llParseStringKeepNulls(gLast, ["|"], []);
                    vector f0 = (vector)llList2String(O, 4);    // the subject Friends aimed at
                    if (f0 == ZERO_VECTOR) f0 = (vector)llList2String(O, 1);
                    vector u = llRot2Fwd(cr);
                    float t = (f0 - cp) * u;
                    if (t < 0.5) t = 0.5;
                    vector f = cp + u * t;
                    if (gMode == "free")
                    {
                        // Freehand: aimed at what sits in the middle of your frame, so a zoom keeps its size (free.lsl)
                        list h = llCastRay(cp, cp + u * 60.0, [RC_MAX_HITS, 1]);
                        f = cp + u * 10.0;
                        if (llList2Integer(h, -1) > 0) f = llList2Vector(h, 1);
                    }
                    untrim();                           // you framed it yourself: Adjust starts from it
                    setCam(cp, f);
                    gVerify = FALSE;
                    gLast = (string)cp + "|" + (string)f + "|" + llList2String(O, 2) + "|" + llList2String(O, 3) + "|" + (string)f;
                    gPending = FALSE;
                    gState = ST_ROLL;
                    setUi("rolling");
                    llMessageLinked(LINK_SET, RESUME, "peek", "");
                    llMessageLinked(LINK_SET, LEAD, (string)cp + "|" + (string)f, "");
                }
            }
            else if (!dev && gState == ST_PEEK)
            {
                gState = ST_ROLL;
                setUi("rolling");
                llMessageLinked(LINK_SET, RESUME, "peek", "");
                if (gPending) applyShot(gLast);
            }
        }
    }

    // hold timer
    if (gState == ST_ROLL && !gAsking && gHold > 0.0 && !gHeld)
    {
        if (dt > 2.0) dt = 2.0;
        gHold -= dt;
        if (gHold <= 0.0) askWorker("hold");
    }
}

// /77 grab: take the camera for 3 s without any worker, report whether the viewer followed
grabTest(float t)
{
    if (t - gApplyT < 3.0) return;
    float off = llVecDist(llGetCameraPos(), gShotPos);
    if (off < 1.0) llOwnerSay("[Take 12] grab test: the viewer FOLLOWED the script camera. Camera control works.");
    else llOwnerSay("[Take 12] grab test: the viewer IGNORED the script camera (" + (string)off + " m off). Press ESC, leave Alt-cam / mouselook, try again.");
    bail("test");
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        gNeed = PERMISSION_TAKE_CONTROLS | PERMISSION_CONTROL_CAMERA | PERMISSION_TRACK_CAMERA;
        gSitMask = AGENT_SITTING | AGENT_ON_OBJECT;
        gState = ST_IDLE;
        gMode = "scenery";
        gLastAct = llGetUnixTime();
        gCamRot = ZERO_ROTATION;
        loadCfg();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "core");
        if (llGetAttached()) llRequestPermissions(gOwner, gNeed);
        else llOwnerSay("[Take 12] Wear me as a HUD (right-click > Attach To HUD).");
        setUi(idleUi());
        llSetTimerEvent(2.0);
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id != NULL_KEY) llRequestPermissions(gOwner, gNeed);
        else
        {
            gPermOK = FALSE;
            gState = ST_IDLE;
            llMessageLinked(LINK_SET, STOP, "detach", "");
        }
    }

    run_time_permissions(integer p)
    {
        gPermOK = ((p & gNeed) == gNeed);
        if (gPermOK)
        {
            takeCtl(TRUE);
            gCamPos = llGetCameraPos();
            gCamRot = llGetCameraRot();
        }
        else llOwnerSay("[Take 12] Camera / control permission was not granted - re-attach the HUD.");
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
        if (c & (CHANGED_TELEPORT | CHANGED_REGION))
        {
            gIgnoreCtl = llGetUnixTime() + 2;       // ghost key event after teleport
            if (gPermOK) llRequestPermissions(gOwner, gNeed);
            if (gState == ST_IDLE) return;
            if (gState == ST_TEST) { bail("tp"); return; }
            llClearCameraParams();
            gLast = "";
            gAdjOn = FALSE;
            pause("tp");
        }
    }

    // instant exit: keep this handler tiny
    control(key id, integer level, integer edge)
    {
        if (!(level | edge)) return;
        integer now = llGetUnixTime();
        if (now < gIgnoreCtl) return;
        if (gState == ST_IDLE)
        {
            gLastAct = now;
            return;
        }
        if (gMode == "scenery" || gState == ST_TEST)
        {
            bail("key");
            return;
        }
        if (gAdj)
        {
            if (edge) llMessageLinked(LINK_SET, FITKEY, (string)(level & CTL), "");   // Adjust: every key trims the shot
            return;
        }
        if (gMode == "free") return;                    // Freehand: a tripod, you walk and it stays
        if (gFitCtl && (edge & 48)) llMessageLinked(LINK_SET, FITKEY, (string)(level & 48), "");
        if (gFitCtl)
        {
            level = level & ~48;                        // Page Up / Down are Fit's, not a nudge or a walk
            edge = edge & ~48;
            if (!(level | edge)) return;
        }
        if (gMode == "frame")
        {
            if (edge) llMessageLinked(LINK_SET, NUDGE, (string)level + "|" + (string)llGetCameraRot(), "");   // Me: you walk, it follows
            return;
        }
        // personal / social: the camera follows you
        if (now != gMovSent)
        {
            gMovSent = now;
            llMessageLinked(LINK_SET, MOVING, "", "");
        }
    }

    timer()
    {
        integer now = llGetUnixTime();
        float t = llGetTime();
        float dt = t - gLastTick;
        gLastTick = t;
        if (gState == ST_IDLE) idleTick(now);
        else if (gState == ST_TEST) grabTest(t);
        else activeTick(dt);
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == SHOT)
        {
            gWorkerOK = TRUE;
            if (gHeld && !gAsking) return;              // Us, Friends: you adjusted this shot; it stays until Next
            if (gState == ST_WAIT || gState == ST_ROLL) applyShot(str);
            else if (gState == ST_PAUSE || gState == ST_PEEK)
            {
                gLast = str;                         // shown when the pause ends
                gPending = TRUE;
                gAsking = FALSE;
            }
        }
        else if (num == GLIDE)
        {
            // friends: slowly move the camera to keep the group framed; frame: nudges and zoom changes; people and
            // friends: the dolly when you zoom. The viewer eases it using the lag ("<pos>|<focus>" or "<pos>|<focus>|<lag>").
            if (gState == ST_ROLL && gMode != "scenery")
            {
                list L = llParseStringKeepNulls(str, ["|"], []);
                vector d = <0.0, 0.0, gFitShift * (gMode != "frame")>;     // Me re-solves with Fit itself
                float lag = 1.5;
                if (llGetListLength(L) > 2) lag = (float)llList2String(L, 2);
                glide((vector)llList2String(L, 0) + d, (vector)llList2String(L, 1) + d, lag);
            }
        }
        else if (num == FIT)
        {
            // Fit: the shot on screen moves up or down at once; the camera script plans its next shot with it
            vector d = <0.0, 0.0, (float)str>;
            gFitShift += d.z;
            if (gState == ST_ROLL && gMode != "scenery") glide(gBaseP + d, gBaseF + d, 0.2);
        }
        else if (num == TRIM)
        {
            // Adjust: tilt, swing, slide on the shot on screen (and every next one); in Us and Friends it holds the shot
            list L = llParseStringKeepNulls(str, ["|"], []);
            gTrim = <(float)llList2String(L, 0), (float)llList2String(L, 1), (float)llList2String(L, 2)>;
            if (gMode == "social" || gMode == "friends")
            {
                gHeld = TRUE;
                gNextCut = 0;
            }
            if (gState == ST_ROLL) glide(gBaseP, gBaseF, 0.15);
        }
        else if (num == NO_SHOT)
        {
            gWorkerOK = TRUE;
            if (gState == ST_WAIT || gState == ST_ROLL) basicShot();
        }
        else if (num == ACK)
        {
            if (str == gMode) gWorkerOK = TRUE;
        }
        else if (num == CFG_CHANGED)
        {
            loadCfg();
            if (gState == ST_IDLE) setUi(idleUi());
        }
        else if (num == CMD)
        {
            if (LITE && (str == "personal" || str == "social" || str == "friends" || str == "frame" || str == "free")) return;
            if (str == "stop")
            {
                if (gState != ST_IDLE) bail("cmd");
            }
            else if (str == "showme|go" && (gState == ST_ROLL || gState == ST_WAIT || gState == ST_PEEK))
            {
                llClearCameraParams();                  // 7.2 Show me (fit.lsl): your own camera, to Alt-click your face
                pause("showme");
            }
            else if (str == "showmeend" && gPauseWhy == "showme")
            {
                gPauseWhy = "tp";                       // framed again from scratch (as after a teleport), with your face known
                gResumeAt = 0;
            }
            else if (str == "adjust")
            {
                if (!gSitCtl) gAdjOn = !gAdjOn;         // ADJUST: the keys trim the shot / walk you (seated they always trim:
                                                        // a tap there must not leave Adjust on for when you stand up)
                takeCtl(TRUE);
            }
            else if (llGetSubString(str, 0, 7) == "framing|" || llGetSubString(str, 0, 4) == "view|") untrim();   // a new framing, a saved view
            else if (str == "grab")
            {
                if (gState == ST_IDLE && gPermOK)
                {
                    gMode = "personal";
                    basicShot();
                    gState = ST_TEST;
                    llOwnerSay("[Take 12] grab test: permissions " + (string)llGetPermissions() + " of " + (string)gNeed + ", camera sent - watch your view.");
                    llSetTimerEvent(0.25);
                }
            }
            else if (str == "watch" || str == "unwatch") gWatch = (str == "watch");
            else if (str == "sharecam") { if (gState == ST_IDLE) engage("social"); }  // My turn after Scenery: Us
            else if (gWatch && gState == ST_IDLE && str == "scenery") return;   // watching: the double-tap cuts for all (sync)
            else if (str == "personal") engage("frame");                // 7.0: Me is Framing › Me (Still's composer, with walking)
            else if (str == "scenery" || str == "social" || str == "friends" || str == "frame" || str == "free") engage(str);
            else if (str == "next")
            {
                if (gState == ST_PEEK)
                {
                    gState = ST_ROLL;                   // you asked for the next shot: the peek pause ends
                    setUi("rolling");
                    llMessageLinked(LINK_SET, RESUME, "peek", "");
                }
                untrim();
                if (gState == ST_ROLL) askWorker("skip");
            }
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "core");
        else if (num == STATUS && str == "?")
        {
            llOwnerSay("[Take 12/core] v" + VERSION + " mode " + gMode + ", state " + (string)gState + " (0 idle,1 waiting,2 rolling,3 paused,4 peek,5 test)"
                + ", permissions " + (string)gPermOK + ", worker answered " + (string)gWorkerOK
                + ", shot type " + (string)gType + ", free mem " + (string)llGetFreeMemory());
        }
    }
}
