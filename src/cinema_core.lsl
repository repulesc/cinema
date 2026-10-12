// ============================================================================
//  Cinema HUD  -  cinema_core.lsl  (v2)
//  Owns the camera: permissions, controls, AFK detection, touch, state machine,
//  apply / release the camera, Alt-cam "peek", the hold timer, and a built-in
//  basic composer so the camera ALWAYS does something even if the director
//  script is missing or not running.
//  All three scripts (core, director, ui) go in the ROOT prim of the HUD.
// ============================================================================

string VERSION = "2.0.0";
string PASS    = "cinema-1.0-build1";   // protected Linkset-Data password, same in all scripts

// ---- link messages -----------------------------------------------------------
integer DIR_START    = 7301;   // core -> director  "afk|<fov>" / "manual|<fov>"
integer DIR_STOP     = 7302;
integer DIR_NEXT     = 7303;   // core -> director  hold expired, send the next shot
integer DIR_PAUSE    = 7304;
integer DIR_RESUME   = 7305;
integer DIR_MOVING   = 7306;
integer DIR_COOLDOWN = 7307;
integer SHOT         = 7310;   // director -> core  "<pos>|<focus>|<hold>|<type>|0"
integer NO_SHOT      = 7311;   // director -> core  nothing usable (core covers)
integer DIR_ACK      = 7313;   // director -> core  "I am alive" (version)
integer UI_STATE     = 7320;
integer UI_MENU      = 7321;
integer CFG_CHANGED  = 7330;
integer MSG_VER      = 7360;
integer STATUS       = 7370;
integer CMD          = 7371;   // ui -> core  start / stop / grab

// ---- tunables -------------------------------------------------------------------
float FIRST_WAIT  = 1.5;       // s  wait for the director's first shot, then use a basic shot
float NEXT_WAIT   = 2.5;       // s  wait for the director's next shot, then use a basic shot
float BASIC_HOLD  = 14.0;      // s  hold of a basic (core) shot
float PEEK_TOL    = 1.0;       // m  camera deviation that counts as "user took the camera"
float PEEK_GRACE  = 1.5;       // s  ignore deviation right after a cut
float TOUCH_LONG  = 1.0;       // s  long press opens the menu
list  FB_ANG      = [140.0, -140.0, 40.0, -40.0, 175.0];   // basic shot angles around you

// ---- states -------------------------------------------------------------------
integer ST_IDLE  = 0;
integer ST_WAIT  = 1;          // started, waiting for the first shot
integer ST_ROLL  = 2;          // a shot is on screen
integer ST_PAUSE = 3;          // mouselook / teleport
integer ST_PEEK  = 4;          // user is Alt-camming
integer ST_TEST  = 5;          // /77 grab test

key     gOwner;
integer gNeed;
integer gSitMask;
integer gPermOK;
integer gState;
integer gManual;
integer gType;                 // type of the shot on screen (4 = empty view, 9 = basic)
integer gSitBase;
integer gLastAct;
integer gNoEngageUntil;
integer gIgnoreCtl;
integer gMovSent;
integer gResumeAt;
integer gCoolSent;
integer gDirOK;                // director acknowledged this session
integer gAsking;               // waiting for a director shot
integer gWarned;
integer gFb;
integer gTouchSkip;
integer gMenuShown;
integer gPending;
string  gPauseWhy;
string  gSrc;                  // "afk" / "manual"
string  gLast;                 // last shot string (re-applied after a pause)
float   gAskT;
float   gHold;
float   gApplyT;
float   gLastTick;
float   gTouchT;
vector  gShotPos;
vector  gCamPos;
rotation gCamRot;

// settings
integer gAfkOn;
integer gAfkSec;
integer gCoolMin;
integer gPeekOn;
integer gPeekBail;
integer gManVistaEnd;
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
    gAfkOn       = (integer)cfg("afk_on", "1");
    string a     = cfg("afk_sec", "90");
    gAfkSec      = (integer)a;
    if (a == "away") gAfkSec = -1;
    gCoolMin     = (integer)cfg("cool_min", "10");
    gPeekOn      = (integer)cfg("peek", "1");
    gPeekBail    = (integer)cfg("peek_bail", "0");
    gManVistaEnd = (integer)cfg("man_vista_end", "0");
    gCutMode     = (integer)cfg("cutmode", "0");
    gTrace       = (integer)cfg("trace", "1");
}

tsay(string s)
{
    if (gTrace) llOwnerSay("[Cinema] " + s);
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

// ---- camera -------------------------------------------------------------------
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
}

// "<pos>|<focus>|<hold>|<type>|0"
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

// built-in basic shot: a level portrait orbit around the owner, wall-checked with one ray
basicShot()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2) return;
    vector P = llList2Vector(d, 0);
    vector F = llRot2Fwd(llList2Rot(d, 1));
    F.z = 0.0;
    if (llVecMag(F) < 0.01) F = <1.0, 0.0, 0.0>;
    F = llVecNorm(F);
    vector sz = llGetAgentSize(gOwner);
    vector E = <P.x, P.y, P.z + 0.37 * sz.z>;
    vector dir = F * llEuler2Rot(<0.0, 0.0, llList2Float(FB_ANG, gFb % 5) * DEG_TO_RAD>);
    gFb++;
    float dist = 3.0;
    list r = llCastRay(E, E + dir * dist, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
    if (llList2Integer(r, -1) == 1) dist = llVecDist(E, llList2Vector(r, 1)) - 0.4;
    if (dist < 1.2) dist = 1.2;
    vector cam = E + dir * dist;
    cam.z = E.z - dist * 0.19245;                  // eye line on the upper third, camera level
    if (cam.x < 1.0) cam.x = 1.0;
    if (cam.x > 255.0) cam.x = 255.0;
    if (cam.y < 1.0) cam.y = 1.0;
    if (cam.y > 255.0) cam.y = 255.0;
    applyShot((string)cam + "|" + (string)<E.x, E.y, cam.z> + "|" + (string)BASIC_HOLD + "|9|0");
}

askDirector(string why)
{
    gAsking = TRUE;
    gAskT = llGetTime();
    if (gDirOK) llMessageLinked(LINK_SET, DIR_NEXT, why, "");
    else llMessageLinked(LINK_SET, DIR_START, gSrc + "|" + (string)llGetCameraFOV(), "");
}

// ---- lifecycle -------------------------------------------------------------------
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
    llMessageLinked(LINK_SET, DIR_STOP, why, "");
    setUi(idleUi());
    llSetTimerEvent(2.0);
}

engage(integer manual)
{
    if (!gPermOK)
    {
        llOwnerSay("[Cinema] No camera permission yet - re-attach the HUD.");
        llRequestPermissions(gOwner, gNeed);
        return;
    }
    gManual = manual;
    gState = ST_WAIT;
    gDirOK = FALSE;
    gWarned = FALSE;
    gCoolSent = FALSE;
    gType = 0;
    gSitBase = llGetAgentInfo(gOwner) & gSitMask;
    if (manual) gLastAct = llGetUnixTime();
    gSrc = "afk";
    if (manual) gSrc = "manual";
    gLastTick = llGetTime();
    askDirector("start");
    setUi("rolling");
    llSetTimerEvent(0.5);
}

pause(string why)
{
    gPauseWhy = why;
    gState = ST_PAUSE;
    gResumeAt = llGetUnixTime() + 3;
    llMessageLinked(LINK_SET, DIR_PAUSE, why, "");
}

resume()
{
    string why = gPauseWhy;
    gPauseWhy = "";
    gState = ST_WAIT;
    llMessageLinked(LINK_SET, DIR_RESUME, why, "");
    if (why != "tp" && gLast != "") applyShot(gLast);
    else if (gDirOK)
    {
        gAsking = TRUE;                 // the director re-frames on DIR_RESUME by itself
        gAskT = llGetTime();
    }
    else askDirector("resume");
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
        if (info & AGENT_AWAY) engage(FALSE);
    }
    else if (now - gLastAct >= gAfkSec) engage(FALSE);
}

activeTick(integer now, float dt)
{
    integer info = llGetAgentInfo(gOwner);
    if (info & AGENT_TYPING) { bail("typing"); return; }
    if ((info & gSitMask) != gSitBase) { bail("sit"); return; }
    if (info & AGENT_MOUSELOOK)
    {
        if (gState != ST_PAUSE) pause("ml");
        return;
    }
    if (gState == ST_PAUSE)
    {
        if (gPauseWhy == "tp" && now < gResumeAt) return;
        resume();
    }

    // director too slow / absent: cover with a basic shot so the camera never sits idle
    if (gAsking && (gState == ST_WAIT || gState == ST_ROLL))
    {
        float wait = NEXT_WAIT;
        if (gState == ST_WAIT) wait = FIRST_WAIT;
        if (llGetTime() - gAskT > wait)
        {
            if (!gDirOK && !gWarned)
            {
                gWarned = TRUE;
                llOwnerSay("[Cinema] The director script is not answering, so you get basic shots. Check that cinema_director is in this prim and Running (Build > Scripts > Set Scripts to Running in Selection), and look at the Script Errors window.");
            }
            basicShot();
        }
    }

    // Alt-cam / orbit: the viewer silently overrides scripted cameras - compare the real camera
    if (gPeekOn && (gState == ST_ROLL || gState == ST_PEEK) && llGetTime() - gApplyT > PEEK_GRACE)
    {
        integer dev = (llVecDist(llGetCameraPos(), gShotPos) > PEEK_TOL);
        if (dev && gState == ST_ROLL)
        {
            if (gPeekBail) { bail("camera"); return; }
            gState = ST_PEEK;
            setUi("peek");
            llMessageLinked(LINK_SET, DIR_PAUSE, "peek", "");
        }
        else if (!dev && gState == ST_PEEK)
        {
            gState = ST_ROLL;
            setUi("rolling");
            llMessageLinked(LINK_SET, DIR_RESUME, "peek", "");
            if (gPending) applyShot(gLast);
        }
    }

    // hold timer
    if (gState == ST_ROLL && !gAsking && gHold > 0.0)
    {
        if (dt > 2.0) dt = 2.0;
        gHold -= dt;
        if (gHold <= 0.0) askDirector("hold");
    }

    if (gCoolMin > 0 && !gCoolSent && now - gLastAct >= gCoolMin * 60)
    {
        gCoolSent = TRUE;
        llMessageLinked(LINK_SET, DIR_COOLDOWN, "1", "");
    }
}

// /77 grab: take the camera for 3 s without the director, report whether the viewer followed
grabTest(float t)
{
    if (gHold == 0.0)
    {
        gHold = 1.0;
        gFb = 0;
        basicShot();
        gState = ST_TEST;
        gApplyT = t;
        llOwnerSay("[Cinema] grab test: permissions " + (string)llGetPermissions() + " of " + (string)gNeed + ", camera sent - watch your view.");
        return;
    }
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
            llMessageLinked(LINK_SET, DIR_STOP, "detach", "");
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
            gIgnoreCtl = llGetUnixTime() + 2;          // ghost key event after teleport
            if (gPermOK) llRequestPermissions(gOwner, gNeed);
            if (gState == ST_IDLE) return;
            if (gState == ST_TEST) { bail("tp"); return; }
            llClearCameraParams();
            gLast = "";
            pause("tp");
        }
    }

    // instant bail-out: keep this handler tiny
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
        if (!gManual || gState == ST_TEST)
        {
            bail("key");
            return;
        }
        // manual session: keep rolling, the director re-frames while you walk
        gLastAct = now;
        if (gManVistaEnd && gType == 4) { bail("move"); return; }
        if (now != gMovSent)
        {
            gMovSent = now;
            llMessageLinked(LINK_SET, DIR_MOVING, "", "");
        }
    }

    touch_start(integer n)
    {
        if (llDetectedKey(0) != gOwner) return;
        gMenuShown = FALSE;
        gTouchSkip = (gState != ST_IDLE);
        if (gTouchSkip) bail("tap");               // instant
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
        else engage(TRUE);
    }

    timer()
    {
        integer now = llGetUnixTime();
        float t = llGetTime();
        float dt = t - gLastTick;
        gLastTick = t;
        if (gState == ST_IDLE) idleTick(now);
        else if (gState == ST_TEST) grabTest(t);
        else activeTick(now, dt);
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == SHOT)
        {
            gDirOK = TRUE;
            if (gState == ST_WAIT || gState == ST_ROLL) applyShot(str);
            else if (gState == ST_PAUSE || gState == ST_PEEK)
            {
                gLast = str;                            // shown when the pause ends
                gPending = TRUE;
                gAsking = FALSE;
            }
        }
        else if (num == NO_SHOT)
        {
            gDirOK = TRUE;
            if (gState == ST_WAIT || gState == ST_ROLL) basicShot();
        }
        else if (num == DIR_ACK)
        {
            gDirOK = TRUE;
            if (gState == ST_WAIT) tsay("on - the director is choosing a shot...");
        }
        else if (num == CFG_CHANGED)
        {
            loadCfg();
            if (gState == ST_IDLE) setUi(idleUi());
        }
        else if (num == CMD)
        {
            if (str == "start" && gState == ST_IDLE) engage(TRUE);
            else if (str == "stop" && gState != ST_IDLE) bail("cmd");
            else if (str == "grab" && gState == ST_IDLE && gPermOK)
            {
                gHold = 0.0;
                gState = ST_TEST;
                llSetTimerEvent(0.25);
                grabTest(llGetTime());
            }
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "core");
        else if (num == STATUS && str == "?")
        {
            llOwnerSay("[Cinema/core] v" + VERSION + " state " + (string)gState + " (0 idle,1 waiting,2 rolling,3 paused,4 peek,5 test)"
                + ", permissions " + (string)gPermOK + ", director answered " + (string)gDirOK
                + ", shot type " + (string)gType + ", free mem " + (string)llGetFreeMemory());
        }
    }
}
