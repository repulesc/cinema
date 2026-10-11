// ============================================================================
//  Cinema HUD  -  cinema_director.lsl   (lean build: must fit one 64 KB script)
//  Scene scan, survey, composition maths, raycast sweep, fallback, small grammar.
//  Core owns the camera and the hold timer; this script only answers with
//  SHOT / NO_SHOT and does no work while the cinema is off.
//  Shots: portrait or over-the-shoulder pair (0), pillow shot of the open view (4).
//  The full-featured director (groups, long shots, styles) is in src/future/.
// ============================================================================

string VERSION = "1.1.0";
string PASS    = "cinema-1.0-build1";

integer DIR_START    = 7301;
integer DIR_STOP     = 7302;
integer DIR_NEXT     = 7303;
integer DIR_PAUSE    = 7304;
integer DIR_RESUME   = 7305;
integer DIR_MOVING   = 7306;
integer DIR_COOLDOWN = 7307;
integer SHOT         = 7310;
integer NO_SHOT      = 7311;
integer CFG_CHANGED  = 7330;
integer MSG_VER      = 7360;
integer STATUS       = 7370;

float K_EYE_STAND = 0.37;
float K_EYE_SIT   = 0.25;
float BODY_R      = 0.35;
float MARGIN      = 1.15;
float STANDOFF    = 0.4;
float R_INT       = 4.5;
float MIN_HOLD    = 6.0;

list OFFS = [0.0, 0.436332, -0.436332, 0.872665, -0.872665, 1.396263, -1.396263];
list PHI  = [45.0, -45.0, 135.0, -135.0, 180.0, 0.0];

float   gHoldMul;
integer gCoolMin;
float   gThetaMax;
float   gAspect;
float   gMaxCam;
string  gFovAxis;
integer gTrace;
list    gRayOpts;

float gFov;
float tanV;
float tanH;
float gAlpha;
float gHalfH;

key     gOwner;
integer gActive;
integer gPaused;
integer gManual;
integer gCool;
integer gWaitFirst;
string  gWaitWhy;
integer gScanT;
integer gRetryAt;
integer gErrCount;
integer gMoveUntil;
string  gPendEvent;
integer gPreferA;
integer gSaidFirst;

vector  gOP;
float   gOY;
float   gOE;
integer gOSit;
integer gHasN;
integer gNearCnt;
vector  gNPos;
float   gNEye;

list    gClear;
float   gMaxClear;
float   gRoofZ;
float   gFloorZ;
integer gEnv;
integer gSurveyOK;
vector  gSurveyPos;
integer gLastOpen;

integer gLastCat;
integer gEstablish;
integer gSincePillow;
integer gPillowTarget;
float   gSide;
integer gRev;
float   gLastPhi;
vector  gSceneAnchor;

vector  gPFp;
float   gPAz;
float   gPd;
float   gPdMin;
float   gPEye;
float   gPTh;
vector  gPAxis;

integer gHaveShot;
integer gShotT;
vector  gCurCam;
vector  gCurFocus;
vector  gCurV;
integer gCurArch;
integer gNearAtShot;
vector  gOwnerAtShot;
integer gSweepErr;

// ============================================================================
string cfg(string k, string d)
{
    string v = llLinksetDataReadProtected("cin." + k, PASS);
    if (v == "") return d;
    return v;
}

float fmin(float a, float b)
{
    if (a < b) return a;
    return b;
}

float fmax(float a, float b)
{
    if (a > b) return a;
    return b;
}

float fclamp(float v, float lo, float hi)
{
    return fmax(lo, fmin(v, hi));
}

vector dirOf(float a)
{
    return <llCos(a), llSin(a), 0.0>;
}

vector clampRegion(vector v)
{
    v.x = fclamp(v.x, 0.5, 255.5);
    v.y = fclamp(v.y, 0.5, 255.5);
    if (v.z < 0.5) v.z = 0.5;
    return v;
}

say(string s)
{
    llOwnerSay("[cinema/dir] " + s);
}

tsay(string s)
{
    if (gTrace) llOwnerSay("[cinema/dir] " + s);
}

loadCfg()
{
    gHoldMul  = (float)cfg("hold_mul", "1.0");
    gCoolMin  = (integer)cfg("cool_min", "10");
    gThetaMax = (float)cfg("theta_max", "10") * DEG_TO_RAD;
    gAspect   = (float)cfg("aspect", "1.778");
    gMaxCam   = (float)cfg("maxcam", "45");
    gFovAxis  = cfg("fovaxis", "v");
    gTrace    = (integer)cfg("trace", "1");
    gRayOpts  = [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1];
    if ((integer)cfg("phantom", "0")) gRayOpts += [RC_DETECT_PHANTOM, TRUE];
    if (gFov < 0.1) gFov = 1.047198;
    if (gAspect < 0.5) gAspect = 1.778;
    float t = llTan(gFov * 0.5);
    tanV = t;
    tanH = t * gAspect;
    if (gFovAxis == "h")
    {
        tanH = t;
        tanV = t / gAspect;
    }
    gAlpha = llAtan2(tanH / 3.0, 1.0);
    gHalfH = llAtan2(tanH, 1.0);
}

// ============================================================================
//  rays and scene
// ============================================================================
// [status, distance]: 0 clear (full length), 1 hit, <0 error
list ray(vector a, vector b)
{
    a = clampRegion(a);
    b = clampRegion(b);
    list r = llCastRay(a, b, gRayOpts);
    integer st = llList2Integer(r, -1);
    if (st < 0) return [st, 0.0];
    if (st == 0) return [0, llVecDist(a, b)];
    return [1, llVecDist(a, llList2Vector(r, 1))];
}

integer refreshOwner()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2) return FALSE;
    gOP = llList2Vector(d, 0);
    vector f = llRot2Fwd(llList2Rot(d, 1));
    gOY = llAtan2(f.y, f.x);
    gOSit = ((llGetAgentInfo(gOwner) & AGENT_SITTING) != 0);
    vector sz = llGetAgentSize(gOwner);
    gOE = gOP.z + K_EYE_STAND * sz.z;
    if (gOSit) gOE = gOP.z + K_EYE_SIT * sz.z;
    return TRUE;
}

// nearest other avatar within R_INT, and how many are within R_INT
scan()
{
    gScanT = llGetUnixTime();
    gHasN = FALSE;
    gNearCnt = 0;
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    integer n = llGetListLength(ids);
    integer i;
    float best = R_INT;
    for (i = 0; i < n; i++)
    {
        key k = llList2Key(ids, i);
        list d = llGetObjectDetails(k, [OBJECT_POS]);
        if (k != gOwner && llGetListLength(d) > 0)
        {
            vector p = llList2Vector(d, 0);
            float dist = llVecDist(p, gOP);
            if (dist <= R_INT) gNearCnt++;
            if (dist < best)
            {
                best = dist;
                gNPos = p;
                vector nsz = llGetAgentSize(k);
                gNEye = p.z + K_EYE_STAND * nsz.z;
                gHasN = TRUE;
            }
        }
    }
}

// 8 horizontal rays + up + down
integer survey()
{
    vector E = <gOP.x, gOP.y, gOE>;
    gClear = [];
    gMaxClear = 0.0;
    float tot = 0.0;
    integer i;
    for (i = 0; i < 8; i++)
    {
        list r = ray(E, E + dirOf(i * 0.785398) * 50.0);
        if (llList2Integer(r, 0) < 0) return FALSE;
        float c = llList2Float(r, 1);
        gClear += [c];
        tot += fmin(c, 50.0);
        gMaxClear = fmax(gMaxClear, c);
    }
    list u = ray(E, E + <0.0, 0.0, 40.0>);
    list dn = ray(E, E - <0.0, 0.0, 10.0>);
    if (llList2Integer(u, 0) < 0 || llList2Integer(dn, 0) < 0) return FALSE;
    float roofD = llList2Float(u, 1);
    gRoofZ = E.z + roofD;
    gFloorZ = E.z - llList2Float(dn, 1);
    gEnv = 0;
    if (roofD < 12.0 || tot < 200.0) gEnv = 1;
    if (roofD < 12.0 && tot < 100.0) gEnv = 2;
    gSurveyOK = TRUE;
    gSurveyPos = gOP;
    tsay("survey done: environment " + (string)gEnv + " (0 open, 1 semi, 2 indoor), most open direction " + (string)llRound(gMaxClear) + " m");
    return TRUE;
}

// random open direction (0..7) with clearance >= minClear; -1 if none
integer pickOpenIdx(float minClear)
{
    if (gMaxClear < minClear) return -1;
    list c = [];
    integer i;
    for (i = 0; i < 8; i++)
    {
        if (llList2Float(gClear, i) >= minClear && i != gLastOpen) c += [i];
    }
    if (llGetListLength(c) == 0) return -1;
    gLastOpen = llList2Integer(c, (integer)llFrand(llGetListLength(c)));
    return gLastOpen;
}

// ============================================================================
//  composition (spec 2.2 - 2.8)
// ============================================================================
// camera height: subject eye line on the upper third, camera stays level
float camZ(float eyeRef, float d)
{
    float z = fmax(eyeRef - d * tanV / 3.0, gFloorZ + 0.35);
    if (gEnv == 2) z = fmin(z, gRoofZ - 0.3);
    return z;
}

float fitDist(float spread, float halfH, float lo, float hi)
{
    return fclamp(fmax((spread + BODY_R) / tanH, halfH / tanV) * MARGIN, lo, hi);
}

// plan globals for a portrait (solo) or an over-the-shoulder shot (pair)
planA()
{
    gPAxis = ZERO_VECTOR;
    gPEye = gOE;
    gPFp = <gOP.x, gOP.y, gOE>;
    gPdMin = 2.0;
    gPTh = 0.0;
    if (gOSit) gPTh = 0.0872665;
    vector ax = gNPos - gOP;
    ax.z = 0.0;
    if (gHasN && llVecMag(ax) >= 0.3)
    {
        vector A = llVecNorm(ax);
        vector dc = <-A.y, A.x, 0.0> * gSide * 0.819152;      // behind one shoulder, 35 deg, 180-degree-rule side
        if (gRev) dc = dc + A * 0.573576;                    // reverse shot: other shoulder, same side
        else dc = dc - A * 0.573576;
        gRev = !gRev;
        dc = llVecNorm(dc);
        gPEye = (gOE + gNEye) * 0.5;
        vector cw = (gOP * 1.5 + gNPos) / 2.5;
        gPFp = <cw.x, cw.y, gPEye>;
        gPAz = llAtan2(dc.y, dc.x);
        gPAxis = A;
        gPdMin = 2.5;
        gPd = fitDist(llFabs(ax * <-dc.y, dc.x, 0.0>), 0.9, 2.5, 5.0);
        return;
    }
    integer i = (integer)llFrand(6.0);
    if (llFabs(llList2Float(PHI, i) - gLastPhi) < 0.5) i = (i + 1) % 6;
    gLastPhi = llList2Float(PHI, i);
    gPAz = gOY + gLastPhi * DEG_TO_RAD;
    gPd = fitDist(0.0, 1.3, 2.5, 3.5);
}

// pillow shot: no avatars, lens along the most open direction. [cam, focus, 4] or []
list shotPillow()
{
    float need = 25.0;
    if (gEnv == 2) need = 15.0;
    integer idx = pickOpenIdx(need);
    if (idx < 0) return [];
    vector Dp = dirOf(idx * 0.785398);
    vector E = <gOP.x, gOP.y, gOE>;
    float sgn = gSide;
    integer attempt;
    for (attempt = 0; attempt < 2; attempt++)
    {
        vector cam = <gOP.x, gOP.y, gOE + 0.3> + <Dp.y, -Dp.x, 0.0> * sgn;
        list r = ray(E, cam);
        list f = ray(cam, cam + Dp * 20.0);
        if (llList2Integer(r, 0) < 0 || llList2Integer(f, 0) < 0)
        {
            gSweepErr = TRUE;
            return [];
        }
        if (llList2Integer(r, 0) == 0 && llList2Float(f, 1) >= 12.0)
        {
            vector foc = cam + Dp * 60.0;
            foc.z = cam.z;
            if (gEnv != 2) foc.z = cam.z + 60.0 * tanV / 3.0;     // horizon on the lower third
            return [cam, foc, 4];
        }
        sgn = -sgn;
    }
    return [];
}

// F2: camera just behind the owner's head, looking where they look. [cam, focus, 0] or []
list shoulderShot()
{
    vector E = <gOP.x, gOP.y, gOE>;
    vector F0 = dirOf(gOY);
    vector cam = E - F0 * 0.9 + <F0.y, -F0.x, 0.0> * 0.25;
    list r = ray(E, cam);
    if (llList2Integer(r, 0) < 0) gSweepErr = TRUE;
    if (llList2Integer(r, 0) != 0) return [];
    return [cam, cam + F0 * 10.0, 0];
}

// ============================================================================
//  raycast sweep (spec 3.2 - 3.4)
// ============================================================================
// verify one candidate camera: [cam, focus] or []
list tryCand(float az, float de)
{
    vector cc = gPFp + dirOf(az) * de;
    if (cc.x < 1.0 || cc.x > 255.0 || cc.y < 1.0 || cc.y > 255.0) return [];
    vector cam = <cc.x, cc.y, camZ(gPEye, de)>;
    if (llVecDist(cam, gOP) > gMaxCam) return [];
    list rr = ray(cam, gPFp);
    integer rs = llList2Integer(rr, 0);
    if (rs < 0) gSweepErr = TRUE;
    if (rs < 0 || (rs == 1 && llList2Float(rr, 1) < llVecDist(cam, gPFp) - 0.8)) return [];
    // rule of thirds: subject sits on the side opposite to where they look
    vector V = ZERO_VECTOR - dirOf(az);
    float fs = dirOf(gOY) * <V.y, -V.x, 0.0>;
    float sd = gSide;
    if (fs > 0.2) sd = 1.0;
    else if (fs < -0.2) sd = -1.0;
    vector foc = cam + (V * llEuler2Rot(<0.0, 0.0, -sd * gAlpha>)) * de;
    foc.z = cam.z - de * llTan(fclamp(gPTh, 0.0, gThetaMax));
    return [cam, foc];
}

// 7 candidate azimuths around the plan; best two are verified. [cam, focus, 0] or []
list sweep()
{
    list C = [];
    integer i;
    for (i = 0; i < 7; i++)
    {
        float off = llList2Float(OFFS, i);
        float az = gPAz + off;
        vector cc = gPFp + dirOf(az) * gPd;
        cc.z = camZ(gPEye, gPd);
        list r = ray(gPFp, cc);
        integer st = llList2Integer(r, 0);
        if (st < 0)
        {
            gSweepErr = TRUE;
            return [];
        }
        float de = gPd;
        if (st == 1) de = fmin(gPd, llList2Float(r, 1) - STANDOFF);
        if (de >= 1.2)
        {
            float s = 3.0 * de / gPd + 2.0 * llCos(off);
            if (gPAxis != ZERO_VECTOR)
            {
                float lat = dirOf(az) * <-gPAxis.y, gPAxis.x, 0.0>;
                if (lat * gSide > 0.0) s += 1.0;
                else s -= 2.0;
            }
            C += [s, az, de];
        }
    }
    integer n = llGetListLength(C) / 3;
    integer skip = -1;
    integer rd;
    for (rd = 0; rd < 2; rd++)
    {
        integer b = -1;
        integer j;
        for (j = 0; j < n; j++)
        {
            if (j != skip && (b < 0 || llList2Float(C, j * 3) > llList2Float(C, b * 3))) b = j;
        }
        if (b < 0) return [];
        list v = tryCand(llList2Float(C, b * 3 + 1), llList2Float(C, b * 3 + 2));
        if (gSweepErr) return [];
        if (llGetListLength(v) > 0) return v + [0];
        skip = b;
    }
    return [];
}

// ============================================================================
//  grammar and the cut
// ============================================================================
float holdFor(integer arch)
{
    if (gHoldMul <= 0.0) return 0.0;
    float b = 20.0;
    if (arch == 4) b = 8.0;
    return b * gHoldMul * (0.8 + 0.4 * llFrand(1.0));
}

newScene()
{
    gSceneAnchor = gOP;
    gEstablish = TRUE;
    gRev = FALSE;
    gLastPhi = 999.0;
    gSide = 1.0;
    if (llFrand(1.0) < 0.5) gSide = -1.0;
}

commit(list s)
{
    vector cam = llList2Vector(s, 0);
    vector foc = llList2Vector(s, 1);
    integer arch = llList2Integer(s, 2);
    float hold = holdFor(arch);
    llMessageLinked(LINK_SET, SHOT, (string)cam + "|" + (string)foc + "|" + (string)hold + "|" + (string)arch + "|0", "");
    vector v = foc - cam;
    v.z = 0.0;
    gCurV = llVecNorm(v);
    gCurCam = cam;
    gCurFocus = foc;
    gCurArch = arch;
    gShotT = llGetUnixTime();
    gHaveShot = TRUE;
    gOwnerAtShot = gOP;
    gNearAtShot = gNearCnt;
    gEstablish = FALSE;
    gPreferA = FALSE;
    gPendEvent = "";
    gErrCount = 0;
    gLastCat = 0;
    gSincePillow++;
    if (arch == 4)
    {
        gLastCat = 1;
        gSincePillow = 0;
        gPillowTarget = 4 + (integer)llFrand(3.0);
    }
    if (!gSaidFirst)
    {
        gSaidFirst = TRUE;
        say("first shot: type " + (string)arch + " (0 portrait/pair, 4 empty view), camera " + (string)llRound(llVecDist(cam, gOP)) + " m away");
    }
}

// F4: keep the current composition and give it a fresh hold
extendCurrent()
{
    llMessageLinked(LINK_SET, SHOT, (string)gCurCam + "|" + (string)gCurFocus + "|" + (string)holdFor(gCurArch) + "|" + (string)gCurArch + "|0", "");
    gShotT = llGetUnixTime();
    gOwnerAtShot = gOP;
    gPendEvent = "";
    gPreferA = FALSE;
}

// F5: nothing usable; Core hands the camera back, we retry later
giveUp()
{
    llMessageLinked(LINK_SET, NO_SHOT, "15", "");
    gHaveShot = FALSE;
    gRetryAt = llGetUnixTime() + 15;
    gPreferA = FALSE;
    say("no usable shot here (environment " + (string)gEnv + ", most open direction " + (string)llRound(gMaxClear) + " m) - retrying in 15 s");
}

// ray errors: retry in 3 s; after 3 failures hold the current shot or give up
rayFail()
{
    gErrCount++;
    say("ray error " + (string)gErrCount + "/3");
    if (gErrCount < 3) gRetryAt = llGetUnixTime() + 3;
    else
    {
        gErrCount = 0;
        if (gHaveShot) extendCurrent();
        else giveUp();
    }
}

nextShot(string why)
{
    if (!gActive || gPaused) return;
    gPendEvent = "";
    gRetryAt = 0;
    if (!refreshOwner())
    {
        say("cannot read your avatar position - retrying");
        gRetryAt = llGetUnixTime() + 5;
        return;
    }
    gSweepErr = FALSE;
    if (!gSurveyOK || llVecDist(gOP, gSurveyPos) > 2.0 || why == "start" || why == "resume")
    {
        if (!survey())
        {
            rayFail();
            return;
        }
    }
    // pillow shots (empty view): every few cuts, more often after a long AFK; never the first shot
    integer cat = 0;
    if (!gEstablish && !gPreferA && !gHasN && gLastCat == 0)
    {
        float pp = 0.35;
        if (gCool) pp = 0.8;
        if (gSincePillow >= gPillowTarget || llFrand(1.0) < pp) cat = 1;
    }
    list shot = [];
    integer t;
    for (t = 0; t < 2 && llGetListLength(shot) == 0 && !gSweepErr; t++)
    {
        tsay("trying shot type " + (string)cat + " (0 portrait/pair, 1 empty view)");
        if (cat == 0)
        {
            planA();
            shot = sweep();
        }
        else shot = shotPillow();
        cat = 1 - cat;
    }
    if (!gSweepErr && llGetListLength(shot) == 0) shot = shoulderShot();
    if (gSweepErr)
    {
        gPreferA = FALSE;
        rayFail();
    }
    else if (llGetListLength(shot) > 0) commit(shot);
    else if (gHaveShot) extendCurrent();
    else giveUp();
}

// ============================================================================
//  events
// ============================================================================
integer inFrame(vector p)
{
    vector to = p - gCurCam;
    to.z = 0.0;
    if (llVecMag(to) < 0.1) return TRUE;
    return llAcos(fclamp(llVecNorm(to) * gCurV, -1.0, 1.0)) <= 0.85 * gHalfH;
}

onScan()
{
    if (!gActive || gPaused || !refreshOwner()) return;
    if (gWaitFirst)
    {
        tsay("scan done: " + (string)gNearCnt + " avatar(s) within 4.5 m");
        gWaitFirst = FALSE;
        newScene();
        nextShot(gWaitWhy);
        return;
    }
    if (!gHaveShot) return;
    if (llVecDist(gOP, gSceneAnchor) > 3.0)
    {
        newScene();
        gPendEvent = "scene";
    }
    else if (gNearCnt > gNearAtShot) gPendEvent = "arrival";
    else if (gCurArch != 4 && !inFrame(gOP)) gPendEvent = "frame";
    if (gNearCnt < gNearAtShot) gNearAtShot = gNearCnt;
}

doScan()
{
    if (refreshOwner()) scan();
    onScan();
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        gFov = 1.047198;
        gSide = 1.0;
        gLastPhi = 999.0;
        gLastCat = -1;
        gLastOpen = -1;
        gPillowTarget = 4;
        loadCfg();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "director");
        say("v" + VERSION + " ready, free memory " + (string)llGetFreeMemory() + " bytes");
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
        if (num == DIR_START)
        {
            list L = llParseString2List(str, ["|"], []);
            gManual = (llList2String(L, 0) == "manual");
            gFov = (float)llList2String(L, 1);
            loadCfg();
            gActive = TRUE;
            gPaused = FALSE;
            gHaveShot = FALSE;
            gSurveyOK = FALSE;
            gPreferA = FALSE;
            gPendEvent = "";
            gCool = FALSE;
            gErrCount = 0;
            gRetryAt = 0;
            gMoveUntil = 0;
            gLastCat = -1;
            gLastOpen = -1;
            gSincePillow = 0;
            gPillowTarget = 4 + (integer)llFrand(3.0);
            gSaidFirst = FALSE;
            gWaitFirst = TRUE;
            gWaitWhy = "start";
            llSetTimerEvent(1.0);
            doScan();
        }
        else if (num == DIR_STOP)
        {
            gActive = FALSE;
            gHaveShot = FALSE;
            gWaitFirst = FALSE;
            llSetTimerEvent(0.0);
        }
        else if (num == DIR_NEXT)
        {
            if (!gWaitFirst) nextShot(str);
        }
        else if (num == DIR_PAUSE) gPaused = TRUE;
        else if (num == DIR_RESUME)
        {
            gPaused = FALSE;
            gShotT = llGetUnixTime();
            if (str == "tp")
            {
                gHaveShot = FALSE;
                gSurveyOK = FALSE;
                gWaitFirst = TRUE;
                gWaitWhy = "resume";
            }
            if (gWaitFirst) doScan();
        }
        else if (num == DIR_MOVING) gMoveUntil = llGetUnixTime() + 3;
        else if (num == DIR_COOLDOWN) gCool = (gCoolMin > 0);
        else if (num == CFG_CHANGED) loadCfg();
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "director");
        else if (num == STATUS && str == "?")
        {
            say("v" + VERSION + " active " + (string)gActive + ", paused " + (string)gPaused + ", have shot " + (string)gHaveShot
                + ", free mem " + (string)llGetFreeMemory());
        }
    }

    timer()
    {
        if (!gActive || gPaused) return;
        integer now = llGetUnixTime();
        if (gRetryAt > 0 && now >= gRetryAt)
        {
            nextShot("retry");
            return;
        }
        if (now - gScanT >= 5) doScan();
        if (!gHaveShot) return;
        integer since = now - gShotT;
        // manual session and the owner is walking: re-frame when they leave the shot
        if (gManual && now < gMoveUntil && since >= 2 && gCurArch != 4 && refreshOwner())
        {
            if (!inFrame(gOP) || llVecDist(gOP, gOwnerAtShot) > 4.0)
            {
                gPreferA = TRUE;
                nextShot("moved");
                return;
            }
        }
        if (gPendEvent != "" && since >= MIN_HOLD) nextShot(gPendEvent);
    }
}
