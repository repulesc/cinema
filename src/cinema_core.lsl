// ============================================================================
//  Cinema HUD  -  cinema_core.lsl
//  Permissions, controls, AFK detection, state machine, camera apply/clear,
//  touch handling (tap = toggle, long-press = menu) and in-world probes.
//
//  All three scripts (core, director, ui) live in the ROOT prim of the HUD.
//  Design: docs/ARCHITECTURE.md   (section numbers below refer to it)
// ============================================================================

string VERSION = "1.0.2";
string PASS    = "cinema-1.0-build1";   // protected Linkset-Data password, same in all 3 scripts

// ---- link message numbers (section 6.2) ------------------------------------
integer DIR_START    = 7301;   // core -> director   "afk|<fov>" / "manual|<fov>"
integer DIR_STOP     = 7302;   // core -> director   reason
integer DIR_NEXT     = 7303;   // core -> director   hold / invalid / retry
integer DIR_PAUSE    = 7304;   // core -> director   ml / tp / peek
integer DIR_RESUME   = 7305;   // core -> director   ml / tp / peek
integer DIR_MOVING   = 7306;   // core -> director   (manual session, owner is moving)
integer DIR_COOLDOWN = 7307;   // core -> director   "1"
integer SHOT         = 7310;   // director -> core   "<pos>|<focus>|<hold>|<arch>|<fade>"
integer NO_SHOT      = 7311;   // director -> core   retry seconds
integer END_SESSION  = 7312;   // director -> core   reason (director asks core to bail)
integer UI_STATE     = 7320;   // core -> ui         off / armed / rolling / peek / noshot
integer UI_MENU      = 7321;   // core -> ui         (long press)
integer CFG_CHANGED  = 7330;   // ui -> all          key name
integer PROBE        = 7350;   // ui -> core         cut / campos / dist / fov
integer MSG_VER      = 7360;   // all                version string ("?" = please announce)
integer STATUS       = 7370;   // anyone -> all      "?" = every script prints one status line
integer CMD          = 7371;   // ui -> core         start / stop

// ---- tunables (docs/CALIBRATION.md) -----------------------------------------
float PEEK_TOL     = 0.3;      // m   camera deviation that counts as "user took the camera"
float PEEK_GRACE   = 1.5;      // s   ignore deviation right after a shot was applied
float ENGAGE_WAIT  = 5.0;      // s   no shot after this long -> "noshot"
integer CTL_IGNORE = 2;        // s   ignore control() after teleport (ghost FWD+BACK)
integer RESUME_TP  = 3;        // s   resume delay after teleport / region change
float TOUCH_LONG   = 1.0;      // s   long-press threshold

// ---- states -----------------------------------------------------------------
integer ST_IDLE    = 0;
integer ST_ENGAGING= 1;
integer ST_ROLLING = 2;
integer ST_PAUSED  = 3;
integer ST_PEEK    = 4;
integer ST_NOSHOT  = 5;
integer ST_PROBE   = 6;

integer SRC_AFK    = 0;
integer SRC_MANUAL = 1;

// ---- runtime ----------------------------------------------------------------
key     gOwner;
integer gNeedPerms;
integer gSitMask;
integer gPermOK;
integer gState;
integer gSource;
integer gArch;               // 0 A, 1 B, 2 C1, 3 C2a, 4 C2b
integer gSitBase;
integer gLastAct;            // unix time of last user activity
integer gNoEngageUntil;
integer gIgnoreCtl;
integer gMovSent;
integer gEngageT;
integer gResumeAt;
integer gCoolSent;
integer gHaveShot;
integer gHoldInf;
integer gPending;           // a shot arrived while paused/peeking
integer gTouchSkip;
integer gMenuShown;
string  gPauseWhy;
string  gLastPacked;
float   gHold;
float   gApplyT;
float   gLastTick;
float   gTouchT;
vector  gShotPos;
vector  gCamPos;
rotation gCamRot;

// ---- probe ------------------------------------------------------------------
string  gProbe;
integer gProbeStep;
float   gProbeT;
float   gProbeMax;
vector  gProbeA;
vector  gProbeB;
vector  gProbeEye;
vector  gProbeFwd;
list    gProbeDist;

// ---- cached settings (docs/ARCHITECTURE.md 6.3) ------------------------------
integer gAfkOn;
integer gAfkSec;             // -1 = use SL "Away"
integer gCoolMin;
integer gPeekOn;
integer gPeekBail;
integer gManVistaEnd;
integer gCutMode;
integer gDebug;
integer gTrace;
integer gReportCam;

// ============================================================================
//  helpers
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
    if (a == "away") gAfkSec = -1;
    else gAfkSec = (integer)a;
    gCoolMin     = (integer)cfg("cool_min", "10");
    gPeekOn      = (integer)cfg("peek", "1");
    gPeekBail    = (integer)cfg("peek_bail", "0");
    gManVistaEnd = (integer)cfg("man_vista_end", "0");
    gCutMode     = (integer)cfg("cutmode", "0");
    gDebug       = (integer)cfg("debug", "0");
    gTrace       = (integer)cfg("trace", "1");
}

dbg(string s)
{
    if (gDebug) llOwnerSay("[cinema/core] " + s);
}

// progress messages for testing (setting cin.trace, default on)
tsay(string s)
{
    if (gTrace) llOwnerSay("[Cinema] " + s);
}

vector ownerPos()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS]);
    if (llGetListLength(d) == 0) return ZERO_VECTOR;
    return llList2Vector(d, 0);
}

vector clampRegion(vector v)
{
    if (v.x < 1.0) v.x = 1.0;
    if (v.x > 255.0) v.x = 255.0;
    if (v.y < 1.0) v.y = 1.0;
    if (v.y > 255.0) v.y = 255.0;
    if (v.z < 0.5) v.z = 0.5;
    return v;
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

requestPerms()
{
    llRequestPermissions(gOwner, gNeedPerms);
}

// ---- camera ------------------------------------------------------------------
setCam(vector p, vector f)
{
    if (gCutMode) llClearCameraParams();   // forces a hard cut if lag 0 still glides (probe a)
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

// "<pos>|<focus>|<hold>|<arch>|<fade>"
applyShot(string packed)
{
    list L = llParseStringKeepNulls(packed, ["|"], []);
    vector p = (vector)llList2String(L, 0);
    vector f = (vector)llList2String(L, 1);
    gHold    = (float)llList2String(L, 2);
    gArch    = (integer)llList2String(L, 3);
    // fade flag (L 4) is reserved for the optional overlay (phase 2)
    gHoldInf = (gHold <= 0.0);
    gLastPacked = packed;
    gHaveShot = TRUE;
    gPending = FALSE;
    gReportCam = TRUE;
    setCam(p, f);
    tsay("shot received: type " + (string)gArch + " (0 portrait/pair, 1 group, 2 long, 3 behind you, 4 empty view), camera "
        + (string)llRound(llVecDist(p, ownerPos())) + " m from you, hold " + (string)llRound(gHold) + " s");
    if (gState != ST_ROLLING)
    {
        gState = ST_ROLLING;
        setUi("rolling");
    }
}

// ---- lifecycle ---------------------------------------------------------------
// bail() is the instant return to the user's own camera. First statement clears.
bail(string why)
{
    if (gPermOK) llClearCameraParams();
    gState = ST_IDLE;
    gHaveShot = FALSE;
    gPending = FALSE;
    gProbe = "";
    gPauseWhy = "";
    gLastAct = llGetUnixTime();
    gNoEngageUntil = gLastAct + 10;
    llMessageLinked(LINK_SET, DIR_STOP, why, "");
    setUi(idleUi());
    llSetTimerEvent(2.0);
    dbg("bail: " + why);
}

engage(integer src)
{
    if (!gPermOK)
    {
        llOwnerSay("[Cinema] Camera permissions not granted yet. Re-attach the HUD.");
        requestPerms();
        return;
    }
    integer now = llGetUnixTime();
    gSource = src;
    gState = ST_ENGAGING;
    gEngageT = now;
    gHaveShot = FALSE;
    gPending = FALSE;
    gCoolSent = FALSE;
    gArch = 0;
    gSitBase = llGetAgentInfo(gOwner) & gSitMask;
    if (src == SRC_MANUAL) gLastAct = now;
    float fov = llGetCameraFOV();
    if (fov < 0.1) fov = 1.047198;
    string s = "afk";
    if (src == SRC_MANUAL) s = "manual";
    gLastTick = llGetTime();
    llMessageLinked(LINK_SET, DIR_START, s + "|" + (string)fov, "");
    setUi("rolling");
    llSetTimerEvent(0.5);
    tsay("started (" + s + ") - waiting for the director to pick a shot...");
    dbg("engage: " + s + "  free mem " + (string)llGetFreeMemory());
}

pause(string why)
{
    gPauseWhy = why;
    gState = ST_PAUSED;
    if (why == "tp") gResumeAt = llGetUnixTime() + RESUME_TP;
    llMessageLinked(LINK_SET, DIR_PAUSE, why, "");
    dbg("pause: " + why);
}

resume()
{
    string why = gPauseWhy;
    gPauseWhy = "";
    if (why == "tp")
    {
        // camera was cleared on teleport: ask for a fresh shot (director re-surveys)
        gState = ST_ENGAGING;
        gEngageT = llGetUnixTime();
        gHaveShot = FALSE;
        setUi("rolling");
    }
    else
    {
        if (gHaveShot) applyShot(gLastPacked);     // re-apply (mouselook ignored it)
        else gState = ST_ENGAGING;
        gEngageT = llGetUnixTime();
    }
    llMessageLinked(LINK_SET, DIR_RESUME, why, "");
    dbg("resume: " + why);
}

integer camDeviates()
{
    float d = llVecDist(llGetCameraPos(), gShotPos);
    float tol = PEEK_TOL + 0.03 * llVecDist(gShotPos, ownerPos());   // far shots: looser
    return d > tol;
}

// ============================================================================
//  probes (docs/CALIBRATION.md a, c, d, e)
// ============================================================================
pSay(string s)
{
    llOwnerSay("[Cinema probe] " + s);
}

endProbe()
{
    llClearCameraParams();
    gProbe = "";
    gState = ST_IDLE;
    gLastAct = llGetUnixTime();
    gNoEngageUntil = gLastAct + 10;
    setUi(idleUi());
    llSetTimerEvent(2.0);
}

startProbe(string kind)
{
    if (!gPermOK)
    {
        pSay("camera permission not granted yet - re-attach the HUD.");
        return;
    }
    if (gState != ST_IDLE)
    {
        pSay("stop the cinema first (tap the button), then run the probe.");
        return;
    }
    if (kind == "fov")
    {
        float f = llGetCameraFOV();
        pSay("llGetCameraFOV() = " + (string)f + " rad = " + (string)(f * RAD_TO_DEG)
            + " deg. Default is 1.047 (60 deg). The HUD assumes this is the VERTICAL fov"
            + " (setting cin.fovaxis = v). If shots look cropped at the sides, try h.");
        return;
    }
    if (kind == "grab")
    {
        pSay("permissions held " + (string)llGetPermissions() + ", needed " + (string)gNeedPerms
            + ", attach point " + (string)llGetAttached() + " (0 = not attached)");
    }
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) == 0) return;
    vector P = llList2Vector(d, 0);
    vector fwd = llRot2Fwd(llList2Rot(d, 1));
    fwd.z = 0.0;
    if (llVecMag(fwd) < 0.01) fwd = <1.0, 0.0, 0.0>;
    gProbeFwd = llVecNorm(fwd);
    gProbeEye = P + <0.0, 0.0, 0.6>;
    gProbe = kind;
    gProbeStep = 0;
    gProbeT = llGetTime();
    gState = ST_PROBE;
    llSetTimerEvent(0.25);
    pSay("started '" + kind + "'. Do not touch the movement keys (they cancel the probe).");
}

probeTick()
{
    float t = llGetTime();
    if (gProbe == "cut")
    {
        vector left = <-gProbeFwd.y, gProbeFwd.x, 0.0>;
        if (gProbeStep == 0)
        {
            gProbeA = gProbeEye + gProbeFwd * 4.0;
            gProbeB = gProbeEye + left * 4.0;
            setCam(gProbeA, gProbeEye);
            gProbeStep = 1;
            gProbeT = t;
        }
        else if (gProbeStep == 1)
        {
            if (t - gProbeT >= 1.5)
            {
                pSay("camera A reads " + (string)llVecDist(llGetCameraPos(), gProbeA) + " m from the requested spot.");
                setCam(gProbeB, gProbeEye);       // jump 5.6 m sideways
                gProbeStep = 2;
                gProbeT = t;
            }
        }
        else
        {
            float dist = llVecDist(llGetCameraPos(), gProbeB);
            float el = t - gProbeT;
            if (dist < 0.4)
            {
                if (el <= 0.6) pSay("result: CUT - the camera jumped instantly (" + (string)el + " s). cutmode can stay 0.");
                else pSay("result: GLIDE - the camera took about " + (string)el + " s. Set Options > Cut mode to 'clear first' and probe again.");
                endProbe();
            }
            else if (el > 4.0)
            {
                pSay("result: camera never reached B (still " + (string)dist + " m away). If llGetCameraPos does not follow scripted cameras this is meaningless - check by eye.");
                endProbe();
            }
        }
        return;
    }
    if (gProbe == "grab")
    {
        if (gProbeStep == 0)
        {
            gProbeA = gProbeEye + gProbeFwd * 4.0;
            setCam(gProbeA, gProbeEye);
            gProbeStep = 1;
            gProbeT = t;
            pSay("camera request sent: 4 m in front of you, looking at you. Watch your view...");
        }
        else if (t - gProbeT >= 2.5)
        {
            float goff = llVecDist(llGetCameraPos(), gProbeA);
            if (goff < 1.0) pSay("result: the viewer FOLLOWED the script camera (off by " + (string)goff + " m). Grabbing works; the problem is elsewhere (director).");
            else pSay("result: the viewer IGNORED the script camera (still " + (string)goff + " m from the requested spot). Press ESC, leave Alt-cam / mouselook, check your viewer's camera / Move & View preferences, then repeat /9 grab.");
            endProbe();
        }
        return;
    }
    if (gProbe == "campos")
    {
        if (gProbeStep == 0)
        {
            gProbeA = gProbeEye + gProbeFwd * 4.0;
            setCam(gProbeA, gProbeEye);
            gProbeMax = 0.0;
            gProbeStep = 1;
            gProbeT = t;
            pSay("ALT+drag (orbit) your camera now for 12 seconds...");
        }
        else
        {
            float dev = llVecDist(llGetCameraPos(), gProbeA);
            if (dev > gProbeMax) gProbeMax = dev;
            if (t - gProbeT > 12.0)
            {
                if (gProbeMax > 0.5) pSay("result: llGetCameraPos FOLLOWS Alt-cam (max deviation " + (string)gProbeMax + " m). Peek detection works.");
                else pSay("result: max deviation only " + (string)gProbeMax + " m. Either you did not orbit, or llGetCameraPos does not follow Alt-cam. If you did orbit: Options > Alt-cam > Ignore.");
                endProbe();
            }
        }
        return;
    }
    if (gProbe == "dist")
    {
        integer i = gProbeStep / 2;
        if (i >= llGetListLength(gProbeDist))
        {
            pSay("distance probe finished. If the largest distances were reached, type /9 far on (long shots) and /9 maxcam <metres>.");
            endProbe();
            return;
        }
        float want = llList2Float(gProbeDist, i);
        if ((gProbeStep % 2) == 0)
        {
            vector P = gProbeEye - <0.0, 0.0, 0.6>;
            vector c = <128.0, 128.0, 0.0> - <P.x, P.y, 0.0>;
            vector dir = gProbeFwd;
            if (llVecMag(c) > 1.0) dir = llVecNorm(c);
            gProbeA = clampRegion(gProbeEye + dir * want);
            setCam(gProbeA, gProbeEye);
            gProbeT = t;
            gProbeStep++;
        }
        else if (t - gProbeT >= 2.5)
        {
            vector P2 = gProbeEye - <0.0, 0.0, 0.6>;
            pSay("requested " + (string)llVecDist(gProbeA, P2) + " m: camera reads "
                + (string)llVecDist(llGetCameraPos(), P2) + " m from you.");
            gProbeStep++;
        }
        return;
    }
    endProbe();
}

// ============================================================================
//  timer ticks
// ============================================================================
idleTick(integer now)
{
    if (!gPermOK) return;
    integer info = llGetAgentInfo(gOwner);
    if (info & AGENT_TYPING) gLastAct = now;
    if (info & AGENT_MOUSELOOK) gLastAct = now;
    // user orbiting / walking moves the camera: that is presence too
    vector cp = llGetCameraPos();
    rotation cr = llGetCameraRot();
    if (llVecDist(cp, gCamPos) > 0.5 || llRot2Angle(cr / gCamRot) > 0.1) gLastAct = now;
    gCamPos = cp;
    gCamRot = cr;

    if (!gAfkOn) return;
    if (now < gNoEngageUntil) return;
    if (info & (AGENT_TYPING | AGENT_MOUSELOOK)) return;
    if (gAfkSec < 0)
    {
        if (info & AGENT_AWAY) engage(SRC_AFK);
    }
    else if (now - gLastAct >= gAfkSec) engage(SRC_AFK);
}

activeTick(integer now, float dt)
{
    integer info = llGetAgentInfo(gOwner);
    if (info & AGENT_TYPING) { bail("typing"); return; }
    if ((info & gSitMask) != gSitBase) { bail("sit"); return; }

    if (info & AGENT_MOUSELOOK)
    {
        if (gState != ST_PAUSED) pause("ml");
        return;
    }
    if (gState == ST_PAUSED)
    {
        if (gPauseWhy == "ml") resume();
        else if (gPauseWhy == "tp" && now >= gResumeAt) resume();
        else return;
    }

    if (gReportCam && gHaveShot && gState == ST_ROLLING && llGetTime() - gApplyT > PEEK_GRACE)
    {
        gReportCam = FALSE;
        float off = llVecDist(llGetCameraPos(), gShotPos);
        if (off < 1.0) tsay("camera check: your view IS at the requested spot (off by " + (string)off + " m).");
        else tsay("camera check: your view is " + (string)off + " m away from the requested spot - the viewer may be ignoring the script camera (press ESC, leave Alt-cam / mouselook).");
    }

    // Alt-cam / orbit: the viewer silently ignores scripted params, so compare the real camera
    if (gPeekOn && gHaveShot && (gState == ST_ROLLING || gState == ST_PEEK) && llGetTime() - gApplyT > PEEK_GRACE)
    {
        integer dev = camDeviates();
        if (dev && gState == ST_ROLLING)
        {
            if (gPeekBail) { bail("camera"); return; }
            gState = ST_PEEK;
            setUi("peek");
            llMessageLinked(LINK_SET, DIR_PAUSE, "peek", "");
        }
        else if (!dev && gState == ST_PEEK)
        {
            gState = ST_ROLLING;
            setUi("rolling");
            if (gPending) applyShot(gLastPacked);
            llMessageLinked(LINK_SET, DIR_RESUME, "peek", "");
        }
    }

    if (gState == ST_ENGAGING && now - gEngageT > ENGAGE_WAIT)
    {
        gState = ST_NOSHOT;
        setUi("noshot");
        llOwnerSay("[Cinema] no shot from the director after " + (string)llRound(ENGAGE_WAIT) + " s. Is cinema_director.lsl in this prim and running? Type /9 status.");
    }

    if (gState == ST_ROLLING && !gHoldInf)
    {
        if (dt > 2.0) dt = 2.0;
        gHold -= dt;
        if (gHold <= 0.0)
        {
            gHoldInf = TRUE;       // wait for director's answer
            llMessageLinked(LINK_SET, DIR_NEXT, "hold", "");
        }
    }

    if (gCoolMin > 0 && !gCoolSent && now - gLastAct >= gCoolMin * 60)
    {
        gCoolSent = TRUE;
        llMessageLinked(LINK_SET, DIR_COOLDOWN, "1", "");
    }
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        gNeedPerms = PERMISSION_TAKE_CONTROLS | PERMISSION_CONTROL_CAMERA | PERMISSION_TRACK_CAMERA;
        gSitMask = AGENT_SITTING | AGENT_ON_OBJECT;
        gProbeDist = [10.0, 25.0, 45.0, 60.0];
        gState = ST_IDLE;
        gPermOK = FALSE;
        gHaveShot = FALSE;
        gLastAct = llGetUnixTime();
        gLastTick = llGetTime();
        gCamPos = ZERO_VECTOR;
        gCamRot = ZERO_ROTATION;
        loadCfg();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "core");
        if (llGetAttached() != 0) requestPerms();
        else llOwnerSay("[Cinema] Wear me as a HUD (right-click > Attach To HUD) so I can control your camera.");
        setUi(idleUi());
        llSetTimerEvent(2.0);
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id != NULL_KEY)
        {
            gOwner = id;
            requestPerms();
        }
        else
        {
            // camera params are cleared by the server on detach
            gPermOK = FALSE;
            gState = ST_IDLE;
            gHaveShot = FALSE;
            llMessageLinked(LINK_SET, DIR_STOP, "detach", "");
        }
    }

    run_time_permissions(integer p)
    {
        if ((p & gNeedPerms) == gNeedPerms)
        {
            gPermOK = TRUE;
            llTakeControls(CONTROL_FWD | CONTROL_BACK | CONTROL_LEFT | CONTROL_RIGHT
                | CONTROL_ROT_LEFT | CONTROL_ROT_RIGHT | CONTROL_UP | CONTROL_DOWN, TRUE, TRUE);
            gCamPos = llGetCameraPos();
            gCamRot = llGetCameraRot();
            if (gState == ST_IDLE) setUi(idleUi());
        }
        else
        {
            gPermOK = FALSE;
            llOwnerSay("[Cinema] Camera / control permissions were not granted. Re-attach the HUD.");
        }
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
        if (c & (CHANGED_TELEPORT | CHANGED_REGION))
        {
            gIgnoreCtl = llGetUnixTime() + CTL_IGNORE;
            if (gPermOK) requestPerms();
            if (gState == ST_IDLE) return;
            if (gState == ST_PROBE) { bail("tp"); return; }
            llClearCameraParams();
            gHaveShot = FALSE;
            pause("tp");
        }
    }

    // ---- instant bail-out: keep this handler tiny ------------------------
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
        if (gSource == SRC_AFK || gState == ST_PROBE)
        {
            bail("key");
            return;
        }
        // manual session ("director mode"): social shots keep rolling
        gLastAct = now;
        if (gManVistaEnd && gHaveShot && gArch >= 2)
        {
            bail("move");
            return;
        }
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
        if (gState != ST_IDLE)
        {
            bail("tap");              // instant: do not wait for touch_end
            gTouchSkip = TRUE;
            return;
        }
        gTouchSkip = FALSE;
        gTouchT = llGetTime();
    }

    // while the button is held: open the menu as soon as the long-press time is reached
    touch(integer n)
    {
        if (llDetectedKey(0) != gOwner) return;
        if (gState != ST_IDLE || gTouchSkip || gMenuShown) return;
        if (llGetTime() - gTouchT > TOUCH_LONG)
        {
            gMenuShown = TRUE;
            llMessageLinked(LINK_SET, UI_MENU, "", "");
        }
    }

    touch_end(integer n)
    {
        if (llDetectedKey(0) != gOwner) return;
        if (gMenuShown)
        {
            gMenuShown = FALSE;      // the menu already opened while held
            return;
        }
        if (gTouchSkip)
        {
            gTouchSkip = FALSE;
            return;
        }
        if (gState != ST_IDLE) return;
        if (llGetTime() - gTouchT > TOUCH_LONG)
        {
            llMessageLinked(LINK_SET, UI_MENU, "", "");
            return;
        }
        engage(SRC_MANUAL);
    }

    timer()
    {
        integer now = llGetUnixTime();
        float t = llGetTime();
        float dt = t - gLastTick;
        gLastTick = t;
        if (gState == ST_IDLE) idleTick(now);
        else if (gState == ST_PROBE) probeTick();
        else activeTick(now, dt);
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == SHOT)
        {
            if (gState == ST_ENGAGING || gState == ST_ROLLING || gState == ST_NOSHOT)
            {
                applyShot(str);
            }
            else if (gState == ST_PAUSED || gState == ST_PEEK)
            {
                gLastPacked = str;           // applied when the pause ends
                gHaveShot = TRUE;
                gPending = TRUE;
                list L = llParseStringKeepNulls(str, ["|"], []);
                gArch = (integer)llList2String(L, 3);
                gHold = (float)llList2String(L, 2);
                gHoldInf = (gHold <= 0.0);
            }
        }
        else if (num == NO_SHOT)
        {
            if (gState == ST_ROLLING || gState == ST_ENGAGING || gState == ST_NOSHOT)
            {
                if (gState != ST_NOSHOT && gPermOK) llClearCameraParams();   // F5: hand the camera back
                gState = ST_NOSHOT;
                gHaveShot = FALSE;
                setUi("noshot");
            }
        }
        else if (num == END_SESSION)
        {
            if (gState != ST_IDLE) bail(str);
        }
        else if (num == CFG_CHANGED)
        {
            loadCfg();
            if (gState == ST_IDLE) setUi(idleUi());
        }
        else if (num == PROBE)
        {
            startProbe(str);
        }
        else if (num == MSG_VER)
        {
            if (str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "core");
        }
        else if (num == STATUS)
        {
            if (str == "?")
            {
                llOwnerSay("[Cinema/core] v" + VERSION + " state " + (string)gState + " (0 idle,1 engaging,2 rolling,3 paused,4 peek,5 noshot,6 probe)"
                    + ", source " + (string)gSource + " (0 afk,1 manual), permissions ok " + (string)gPermOK + " (held " + (string)llGetPermissions() + " of " + (string)gNeedPerms + ")"
                    + ", shot " + (string)gHaveShot + ", attached " + (string)llGetAttached()
                    + ", free mem " + (string)llGetFreeMemory());
            }
        }
        else if (num == CMD)
        {
            if (str == "start")
            {
                if (gState == ST_IDLE) engage(SRC_MANUAL);
                else llOwnerSay("[Cinema] already running (state " + (string)gState + ").");
            }
            else if (str == "stop")
            {
                if (gState != ST_IDLE) bail("cmd");
            }
            else if (str == "grab")
            {
                startProbe("grab");
            }
        }
    }
}
