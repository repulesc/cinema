// ============================================================================
//  Cinema HUD  -  cinema_core.lsl  (v3)
//  Owns the camera. Modes: scenery (default, AFK + tap), personal and social
//  (optional, from the menu). Triggers, exits, hold timer, Alt-cam peek,
//  pauses, a watchdog with a basic fallback shot per mode, reach verification.
//  All four scripts (core, scenery, people, ui) go in the ROOT prim of the HUD.
// ============================================================================

string VERSION = "3.0.0";
string PASS    = "cinema-1.0-build1";   // protected Linkset-Data password, same in all scripts

integer START      = 7301;   // core -> workers  "<mode>|<fov>"
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer MOVING     = 7306;
integer SHOT       = 7310;   // worker -> core   "<pos>|<focus>|<hold>|<type>"
integer NO_SHOT    = 7311;
integer ACK        = 7313;
integer REACH_FAIL = 7314;   // core -> scenery  "<distance>"
integer UI_STATE   = 7320;
integer UI_MENU    = 7321;
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;   // ui -> core  scenery / personal / social / stop / grab

float FIRST_WAIT  = 1.5;     // s  wait for the first shot, then cut to a basic shot
float NEXT_WAIT   = 2.5;     // s  wait for the next shot
float BASIC_HOLD  = 20.0;    // s  hold of a basic shot
float PEEK_GRACE  = 2.5;     // s  after a cut, before the camera is checked
float TOUCH_LONG  = 1.0;     // s  long press opens the menu
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
string  gMode;                // "scenery" / "personal" / "social"
integer gType;                // type of the shot on screen
integer gSitBase;
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
integer gTouchSkip;
integer gMenuShown;
integer gPending;
string  gPauseWhy;
string  gLast;
float   gAskT;
float   gHold;
float   gApplyT;
float   gLastTick;
float   gTouchT;
vector  gShotPos;
vector  gCamPos;
rotation gCamRot;

integer gAfkOn;
integer gAfkSec;
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
    string a  = cfg("afk_sec", "90");
    gAfkSec   = (integer)a;
    if (a == "away") gAfkSec = -1;
    gPeekOn   = (integer)cfg("peek", "1");
    gPeekBail = (integer)cfg("peek_bail", "0");
    gCutMode  = (integer)cfg("cutmode", "0");
    gTrace    = (integer)cfg("trace", "1");
}

setUi(string st)
{
    llMessageLinked(LINK_SET, UI_STATE, st, "");
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
setCam(vector p, vector f)
{
    if (gCutMode) llClearCameraParams();
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
    gShotPos = p;
    gApplyT = llGetTime();
    gVerify = TRUE;
}

// "<pos>|<focus>|<hold>|<type>"
applyShot(string s)
{
    list L = llParseStringKeepNulls(s, ["|"], []);
    gHold = (float)llList2String(L, 2);
    gType = (integer)llList2String(L, 3);
    gLast = s;
    gPending = FALSE;
    gAsking = FALSE;
    setCam((vector)llList2String(L, 0), (vector)llList2String(L, 1));
    if (gState != ST_ROLL)
    {
        gState = ST_ROLL;
        setUi("rolling");
    }
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
// scenery = high behind you looking down over your area; people = level portrait orbit
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
    if (gMode == "scenery")
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

// ---- lifecycle ------------------------------------------------------------------
// instant return to the user's own camera
bail(string why)
{
    if (gPermOK) llClearCameraParams();
    gState = ST_IDLE;
    gAsking = FALSE;
    gPending = FALSE;
    gPauseWhy = "";
    gLastAct = llGetUnixTime();
    gNoEngageUntil = gLastAct + 10;
    llMessageLinked(LINK_SET, STOP, why, "");
    setUi(idleUi());
    llSetTimerEvent(2.0);
}

engage(string mode)
{
    if (!gPermOK)
    {
        llOwnerSay("[Cinema] No camera permission yet - re-attach the HUD.");
        llRequestPermissions(gOwner, gNeed);
        return;
    }
    if (gState != ST_IDLE) llMessageLinked(LINK_SET, STOP, "switch", "");
    gMode = mode;
    gState = ST_WAIT;
    gWorkerOK = FALSE;
    gWarned = FALSE;
    gLast = "";
    gType = 0;
    gSitBase = llGetAgentInfo(gOwner) & gSitMask;
    gLastAct = llGetUnixTime();
    gLastTick = llGetTime();
    askWorker("start");
    setUi("rolling");
    if (gTrace) llOwnerSay("[Cinema] " + mode + " camera on");
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
    gState = ST_WAIT;
    llMessageLinked(LINK_SET, RESUME, why, "");
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
    if (!gPermOK) return;
    integer info = llGetAgentInfo(gOwner);
    vector cp = llGetCameraPos();
    rotation cr = llGetCameraRot();
    // typing, mouselook or moving / orbiting the camera = the user is present
    if ((info & (AGENT_TYPING | AGENT_MOUSELOOK)) || llVecDist(cp, gCamPos) > 0.5 || llRot2Angle(cr / gCamRot) > 0.1) gLastAct = now;
    gCamPos = cp;
    gCamRot = cr;
    if (!gAfkOn || now < gNoEngageUntil || (info & (AGENT_TYPING | AGENT_MOUSELOOK))) return;
    if (gAfkSec < 0)
    {
        if (info & AGENT_AWAY) engage("scenery");
    }
    else if (now - gLastAct >= gAfkSec) engage("scenery");
}

activeTick(float dt)
{
    integer info = llGetAgentInfo(gOwner);
    if (info & AGENT_TYPING) { bail("typing"); return; }
    if (gMode == "scenery" && (info & gSitMask) != gSitBase) { bail("sit"); return; }
    if (info & AGENT_MOUSELOOK)
    {
        if (gState != ST_PAUSE) pause("ml");
        return;
    }
    if (gState == ST_PAUSE)
    {
        if (gPauseWhy == "tp" && llGetUnixTime() < gResumeAt) return;
        resume();
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
                llOwnerSay("[Cinema] The " + gMode + " script is not answering, so you get basic shots. Check that it is in this prim and running (Build > Scripts > Set Scripts to Running in Selection) and look at the Script Errors window.");
            }
            basicShot();
        }
    }

    if ((gState == ST_ROLL || gState == ST_PEEK) && llGetTime() - gApplyT > PEEK_GRACE)
    {
        vector cp = llGetCameraPos();
        vector op = ownerPos();
        float want = llVecDist(gShotPos, op);
        if (gVerify)
        {
            // first check after a cut: did the viewer put the camera where we asked?
            gVerify = FALSE;
            if ((gType == 5 || gType == 6) && llVecDist(cp, gShotPos) > 3.0 && llVecDist(cp, op) < 0.8 * want)
            {
                llMessageLinked(LINK_SET, REACH_FAIL, (string)want, "");
                return;
            }
        }
        else if (gPeekOn)
        {
            // Alt-cam / orbit: the viewer silently overrides scripted cameras
            integer dev = (llVecDist(cp, gShotPos) > 1.0 + 0.05 * want);
            if (dev && gState == ST_ROLL)
            {
                if (gPeekBail) { bail("camera"); return; }
                gState = ST_PEEK;
                setUi("peek");
                llMessageLinked(LINK_SET, PAUSE, "peek", "");
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
    if (gState == ST_ROLL && !gAsking && gHold > 0.0)
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
    if (off < 1.0) llOwnerSay("[Cinema] grab test: the viewer FOLLOWED the script camera. Camera control works.");
    else llOwnerSay("[Cinema] grab test: the viewer IGNORED the script camera (" + (string)off + " m off). Press ESC, leave Alt-cam / mouselook, try again.");
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
        llOwnerSay("[Cinema] core v" + VERSION + " ready, free memory " + (string)llGetFreeMemory());
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "core");
        if (llGetAttached()) llRequestPermissions(gOwner, gNeed);
        else llOwnerSay("[Cinema] Wear me as a HUD (right-click > Attach To HUD).");
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
            llTakeControls(CONTROL_FWD | CONTROL_BACK | CONTROL_LEFT | CONTROL_RIGHT
                | CONTROL_ROT_LEFT | CONTROL_ROT_RIGHT | CONTROL_UP | CONTROL_DOWN, TRUE, TRUE);
            gCamPos = llGetCameraPos();
            gCamRot = llGetCameraRot();
        }
        else llOwnerSay("[Cinema] Camera / control permission was not granted - re-attach the HUD.");
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
        // personal / social: the camera follows you
        if (now != gMovSent)
        {
            gMovSent = now;
            llMessageLinked(LINK_SET, MOVING, "", "");
        }
    }

    touch_start(integer n)
    {
        if (llDetectedKey(0) != gOwner) return;
        gMenuShown = FALSE;
        gTouchSkip = (gState != ST_IDLE);
        if (gTouchSkip) bail("tap");                // instant
        gTouchT = llGetTime();
    }

    touch(integer n)
    {
        if (gState != ST_IDLE || gTouchSkip || gMenuShown || llDetectedKey(0) != gOwner) return;
        if (llGetTime() - gTouchT > TOUCH_LONG)
        {
            gMenuShown = TRUE;
            llMessageLinked(LINK_SET, UI_MENU, "", "");
        }
    }

    touch_end(integer n)
    {
        if (llDetectedKey(0) != gOwner || gMenuShown || gTouchSkip || gState != ST_IDLE) return;
        if (llGetTime() - gTouchT > TOUCH_LONG) llMessageLinked(LINK_SET, UI_MENU, "", "");
        else engage("scenery");
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
            if (gState == ST_WAIT || gState == ST_ROLL) applyShot(str);
            else if (gState == ST_PAUSE || gState == ST_PEEK)
            {
                gLast = str;                         // shown when the pause ends
                gPending = TRUE;
                gAsking = FALSE;
            }
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
            if (str == "stop")
            {
                if (gState != ST_IDLE) bail("cmd");
            }
            else if (str == "grab")
            {
                if (gState == ST_IDLE && gPermOK)
                {
                    gMode = "personal";
                    basicShot();
                    gState = ST_TEST;
                    llOwnerSay("[Cinema] grab test: permissions " + (string)llGetPermissions() + " of " + (string)gNeed + ", camera sent - watch your view.");
                    llSetTimerEvent(0.25);
                }
            }
            else if (str == "scenery" || str == "personal" || str == "social") engage(str);
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "core");
        else if (num == STATUS && str == "?")
        {
            llOwnerSay("[Cinema/core] v" + VERSION + " mode " + gMode + ", state " + (string)gState + " (0 idle,1 waiting,2 rolling,3 paused,4 peek,5 test)"
                + ", permissions " + (string)gPermOK + ", worker answered " + (string)gWorkerOK
                + ", shot type " + (string)gType + ", free mem " + (string)llGetFreeMemory());
        }
    }
}
