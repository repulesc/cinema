// ============================================================================
//  Cinema HUD  -  cinema_director.lsl
//  The "brains": scene scan, environment survey, composition maths, raycast
//  candidate selection, fallbacks and the editing grammar (what to shoot next,
//  how long to hold, when to cut early).
//
//  Core (cinema_core.lsl) owns the camera and the hold timer; this script only
//  answers with SHOT / NO_SHOT messages. It does no work while the cinema is off.
//  Lives in the ROOT prim with cinema_core and cinema_ui.
//  Design: docs/ARCHITECTURE.md  (section numbers below refer to it)
// ============================================================================

string VERSION = "1.0.1";
string PASS    = "cinema-1.0-build1";      // same in all 3 scripts

// ---- link message numbers (section 6.2) ------------------------------------
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

// ---- calibration constants (docs/CALIBRATION.md) ---------------------------
float K_EYE_STAND  = 0.37;     // eye height as a fraction of avatar height, above its centre
float K_EYE_SIT    = 0.25;
float BODY_R       = 0.35;     // half body width used when fitting the frame
float MARGIN       = 1.15;     // breathing room around the subjects
float STANDOFF     = 0.4;      // gap kept between camera and an obstacle
float R_INT        = 4.5;      // "intimate" radius
float R_ENS        = 10.0;     // ensemble radius
float LINK_D       = 3.5;      // single-link cluster distance
float W_OWN        = 1.5;      // owner weight in a pair centroid
float MIN_HOLD     = 6.0;      // seconds before an event may cut
float SURVEY_RANGE = 50.0;
float SCAN_SEC     = 5.0;
integer MAX_AV     = 12;

// plan flags
integer FL_ENS    = 1;         // ensemble: owner-occlusion test + member rays
integer FL_CENTER = 2;         // no rule-of-thirds yaw
integer FL_RAISED = 4;         // camera a bit above the heads, looks down 6 deg
integer FL_FIXED  = 8;         // camera height from the ground below it (long shot)
integer FL_FADE   = 16;        // far cut: dip-to-black if an overlay exists

// candidate azimuth offsets: 0, +-25, +-50, +-80 degrees
list OFFS = [0.0, 0.436332, -0.436332, 0.872665, -0.872665, 1.396263, -1.396263];

// ---- settings cache ---------------------------------------------------------
integer gStyle;                // 0 blend, 1 ozu, 2 jarmusch, 3 nouvelle vague
float   gHoldMul;
integer gCoolMin;
integer gSpeaker;
integer gPhantom;
float   gThetaMax;
float   gAspect;
float   gMaxCam;
string  gFovAxis;
integer gDebug;
integer gFarOk;               // long shots (25-45 m) allowed once the distance probe passed
list    gRayOpts;

// ---- lens ---------------------------------------------------------------------
float gFov;
float tanV;
float tanH;
float gAlpha;                  // thirds offset angle
float gHalfH;                  // half horizontal fov

// ---- session ------------------------------------------------------------------
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
integer gJump;
key     gFocusKey;
list    gPrevTyp;
integer gListen;

// ---- owner, avatars, members -------------------------------------------------
vector  gOP;
float   gOY;
float   gOE;
integer gOSit;
list    gAv;                   // stride 5: key, pos, yaw, eyeZ, flags (1 sitting, 2 typing)
list    gMem;                  // stride 3: pos, yaw, eyeZ   (owner first)
vector  gC;
float   gMeanEye;
integer gAnySit;

// ---- survey -------------------------------------------------------------------
list    gClear;
float   gMaxClear;
float   gRoofZ;
float   gFloorZ;
float   gOpen;
integer gEnv;                  // 0 exterior, 1 semi, 2 interior
integer gSurveyOK;
vector  gSurveyPos;
integer gCutsSinceSurvey;
integer gLastOpen;
float   gWater;

// ---- grammar state ------------------------------------------------------------
integer gLastCat;              // 0 A, 1 B, 2 C1, 3 C2, -1 none yet
integer gEstablish;
integer gSincePillow;
integer gPillowTarget;
float   gSide;                 // 180-degree-rule side, +1 / -1
integer gRev;
float   gLastAz;
float   gLastPhi;
float   gBaseD;
vector  gSceneAnchor;
string  gSceneSig;
string  gSigPend;
integer gSigCount;

// ---- current shot ---------------------------------------------------------------
integer gSaidFirst;
integer gHaveShot;
integer gShotT;
vector  gCurCam;
vector  gCurFocus;
vector  gCurV;
integer gCurArch;
integer gNearAtShot;
vector  gOwnerAtShot;

// ---- ray bookkeeping ------------------------------------------------------------
integer gRays;
integer gSweepErr;

// ============================================================================
//  small helpers
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
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

float wrapPi(float a)
{
    while (a > PI) a -= TWO_PI;
    while (a < -PI) a += TWO_PI;
    return a;
}

float angDiff(float a, float b)
{
    return llFabs(wrapPi(a - b));
}

vector dirOf(float a)
{
    return <llCos(a), llSin(a), 0.0>;
}

float azOf(vector v)
{
    return llAtan2(v.y, v.x);
}

vector clampRegion(vector v)
{
    if (v.x < 0.5) v.x = 0.5;
    if (v.x > 255.5) v.x = 255.5;
    if (v.y < 0.5) v.y = 0.5;
    if (v.y > 255.5) v.y = 255.5;
    if (v.z < 0.5) v.z = 0.5;
    return v;
}

dbg(string s)
{
    if (gDebug) llOwnerSay("[cinema/dir] " + s);
}

// always printed (important events and failures)
say(string s)
{
    llOwnerSay("[cinema/dir] " + s);
}

updateLens()
{
    float t = llTan(gFov * 0.5);
    if (gFovAxis == "h")
    {
        tanH = t;
        tanV = t / gAspect;
    }
    else
    {
        tanV = t;
        tanH = t * gAspect;
    }
    gAlpha = llAtan2(tanH / 3.0, 1.0);
    gHalfH = llAtan2(tanH, 1.0);
}

setupListen()
{
    if (gListen) llListenRemove(gListen);
    gListen = 0;
    if (gActive && gSpeaker == 2) gListen = llListen(0, "", NULL_KEY, "");
}

loadCfg()
{
    string s = cfg("style", "blend");
    gStyle = 0;
    if (s == "ozu") gStyle = 1;
    else if (s == "jarmusch") gStyle = 2;
    else if (s == "nv") gStyle = 3;
    gHoldMul  = (float)cfg("hold_mul", "1.0");
    gCoolMin  = (integer)cfg("cool_min", "10");
    gSpeaker  = (integer)cfg("speaker", "0");
    gPhantom  = (integer)cfg("phantom", "0");
    gThetaMax = (float)cfg("theta_max", "10") * DEG_TO_RAD;
    gAspect   = (float)cfg("aspect", "1.778");
    if (gAspect < 0.5) gAspect = 1.778;
    gMaxCam   = (float)cfg("maxcam", "45");
    gFovAxis  = cfg("fovaxis", "v");
    gDebug    = (integer)cfg("debug", "0");
    gFarOk    = (integer)cfg("far_ok", "0");
    gRayOpts  = [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1];
    if (gPhantom) gRayOpts += [RC_DETECT_PHANTOM, TRUE];
    if (gFov < 0.1) gFov = 1.047198;
    updateLens();
    setupListen();
}

// weighted random index; -1 if every weight is zero
integer pickW(list w)
{
    float tot = 0.0;
    integer n = llGetListLength(w);
    integer i;
    for (i = 0; i < n; i++) tot += llList2Float(w, i);
    if (tot <= 0.0) return -1;
    float r = llFrand(tot);
    for (i = 0; i < n; i++)
    {
        float wi = llList2Float(w, i);
        r -= wi;
        if (r < 0.0 && wi > 0.0) return i;
    }
    for (i = n - 1; i >= 0; i--)
    {
        if (llList2Float(w, i) > 0.0) return i;
    }
    return -1;
}

string packShot(vector p, vector f, float hold, integer arch, integer fade)
{
    return (string)p + "|" + (string)f + "|" + (string)hold + "|" + (string)arch + "|" + (string)fade;
}

// ============================================================================
//  rays (section 3)
// ============================================================================
// returns [status, distance]: status 0 = clear (distance = full length), 1 = hit, <0 = error
list ray(vector a, vector b)
{
    a = clampRegion(a);
    b = clampRegion(b);
    list r = llCastRay(a, b, gRayOpts);
    gRays++;
    integer st = llList2Integer(r, -1);
    if (st < 0) return [st, 0.0];
    if (st == 0) return [0, llVecDist(a, b)];
    return [1, llVecDist(a, llList2Vector(r, 1))];
}

// surface height below (x,y), searched from zRef+20 down to zRef-40
float groundAt(float x, float y, float zRef)
{
    list r = ray(<x, y, zRef + 20.0>, <x, y, zRef - 40.0>);
    integer st = llList2Integer(r, 0);
    if (st < 0)
    {
        gSweepErr = TRUE;
        return zRef;
    }
    if (st == 1) return zRef + 20.0 - llList2Float(r, 1);
    return zRef - 40.0;
}

// ============================================================================
//  scene: owner, avatars, members, clusters
// ============================================================================
integer refreshOwner()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2) return FALSE;
    gOP = llList2Vector(d, 0);
    vector f = llRot2Fwd(llList2Rot(d, 1));
    gOY = llAtan2(f.y, f.x);
    gOSit = ((llGetAgentInfo(gOwner) & AGENT_SITTING) != 0);
    vector sz = llGetAgentSize(gOwner);
    float h = sz.z;
    if (h < 0.5) h = 1.8;
    if (gOSit) gOE = gOP.z + K_EYE_SIT * h;
    else gOE = gOP.z + K_EYE_STAND * h;
    return TRUE;
}

integer countNear()
{
    integer n = llGetListLength(gAv) / 5;
    integer c = 0;
    integer i;
    for (i = 0; i < n; i++)
    {
        if (llVecDist(llList2Vector(gAv, i * 5 + 1), gOP) <= R_INT) c++;
    }
    return c;
}

// indices (into gAv) of up to 2 avatars close to the owner; a speaker is put first
list nearIdx()
{
    list r = [];
    integer n = llGetListLength(gAv) / 5;
    integer i;
    for (i = 0; i < n && llGetListLength(r) < 2; i++)
    {
        if (llVecDist(llList2Vector(gAv, i * 5 + 1), gOP) <= R_INT) r += [i];
    }
    if (gFocusKey != NULL_KEY)
    {
        integer fx = llListFindList(gAv, [gFocusKey]);
        if (fx >= 0 && (fx % 5) == 0)
        {
            fx = fx / 5;
            integer at = llListFindList(r, [fx]);
            if (at >= 0) r = llDeleteSubList(r, at, at);
            r = [fx] + r;
            if (llGetListLength(r) > 2) r = llList2List(r, 0, 1);
        }
    }
    return r;
}

// single-link cluster seeded with the owner (indices into gAv, max 5 others)
list clusterIdx()
{
    list inC = [];
    integer n = llGetListLength(gAv) / 5;
    integer grew = TRUE;
    integer pass = 0;
    integer i;
    while (grew && pass < 4 && llGetListLength(inC) < 5)
    {
        grew = FALSE;
        pass++;
        for (i = 0; i < n && llGetListLength(inC) < 5; i++)
        {
            if (llListFindList(inC, [i]) == -1)
            {
                vector p = llList2Vector(gAv, i * 5 + 1);
                if (llVecDist(p, gOP) <= R_ENS)
                {
                    integer linked = (llVecDist(p, gOP) <= LINK_D);
                    integer j = 0;
                    integer m = llGetListLength(inC);
                    while (!linked && j < m)
                    {
                        vector q = llList2Vector(gAv, llList2Integer(inC, j) * 5 + 1);
                        if (llVecDist(p, q) <= LINK_D) linked = TRUE;
                        j++;
                    }
                    if (linked)
                    {
                        inC += [i];
                        grew = TRUE;
                    }
                }
            }
        }
    }
    return inC;
}

// fills gMem (owner + listed avatars), gC (centroid), gMeanEye, gAnySit
setMembers(list idx)
{
    gMem = [gOP, gOY, gOE];
    vector sum = gOP;
    float eyeSum = gOE;
    gAnySit = gOSit;
    integer n = llGetListLength(idx);
    integer i;
    for (i = 0; i < n; i++)
    {
        integer j = llList2Integer(idx, i);
        vector p = llList2Vector(gAv, j * 5 + 1);
        float e = llList2Float(gAv, j * 5 + 3);
        gMem += [p, llList2Float(gAv, j * 5 + 2), e];
        sum += p;
        eyeSum += e;
        if (llList2Integer(gAv, j * 5 + 4) & 1) gAnySit = TRUE;
    }
    float cnt = 1.0 + n;
    gMeanEye = eyeSum / cnt;
    sum = sum / cnt;
    gC = <sum.x, sum.y, gMeanEye>;
}

string sceneSig()
{
    list ks = [];
    integer n = llGetListLength(gAv) / 5;
    integer i;
    for (i = 0; i < n; i++)
    {
        if (llVecDist(llList2Vector(gAv, i * 5 + 1), gOP) <= R_ENS) ks += [(string)llList2Key(gAv, i * 5)];
    }
    return llDumpList2String(llListSort(ks, 1, TRUE), ",");
}

// average of cos(angle between member facing and the direction to a camera at azimuth az)
float facingScore(float az)
{
    vector c = dirOf(az);
    integer n = llGetListLength(gMem) / 3;
    float s = 0.0;
    integer i;
    for (i = 0; i < n; i++) s += dirOf(llList2Float(gMem, i * 3 + 1)) * c;
    if (n < 1) return 0.0;
    return s / n;
}

// TRUE if another member stands between the camera and the owner (within 4 degrees)
integer ownerOccl(vector cam)
{
    integer n = llGetListLength(gMem) / 3;
    if (n < 2) return FALSE;
    vector to = llList2Vector(gMem, 0) - cam;
    to.z = 0.0;
    float dO = llVecMag(to);
    if (dO < 0.1) return FALSE;
    vector uo = to / dO;
    integer i;
    for (i = 1; i < n; i++)
    {
        vector tm = llList2Vector(gMem, i * 3) - cam;
        tm.z = 0.0;
        float dm = llVecMag(tm);
        if (dm > 0.1 && dm < dO)
        {
            if ((tm / dm) * uo > 0.9976) return TRUE;
        }
    }
    return FALSE;
}

// ============================================================================
//  survey (section 3.1): 8 horizontal rays + up + down
// ============================================================================
integer survey()
{
    vector E = <gOP.x, gOP.y, gOE>;
    gClear = [];
    gMaxClear = 0.0;
    float tot = 0.0;
    integer i;
    for (i = 0; i < 8; i++)
    {
        list r = ray(E, E + dirOf(i * 0.785398) * SURVEY_RANGE);
        if (llList2Integer(r, 0) < 0) return FALSE;
        float c = llList2Float(r, 1);
        gClear += [c];
        tot += fmin(c, SURVEY_RANGE);
        if (c > gMaxClear) gMaxClear = c;
    }
    list u = ray(E, E + <0.0, 0.0, 40.0>);
    if (llList2Integer(u, 0) < 0) return FALSE;
    float roofD = 40.0;
    if (llList2Integer(u, 0) == 1) roofD = llList2Float(u, 1);
    gRoofZ = E.z + roofD;
    list dn = ray(E, E - <0.0, 0.0, 10.0>);
    if (llList2Integer(dn, 0) < 0) return FALSE;
    if (llList2Integer(dn, 0) == 1) gFloorZ = E.z - llList2Float(dn, 1);
    else gFloorZ = E.z - 10.0;
    gOpen = tot / 400.0;
    if (roofD < 12.0 && gOpen < 0.25) gEnv = 2;
    else if (roofD < 12.0 || gOpen < 0.5) gEnv = 1;
    else gEnv = 0;
    gSurveyOK = TRUE;
    gSurveyPos = gOP;
    gCutsSinceSurvey = 0;
    dbg("survey: env " + (string)gEnv + ", open " + (string)gOpen + ", maxclear " + (string)gMaxClear
        + ", roof " + (string)roofD + ", floor " + (string)gFloorZ);
    return TRUE;
}

// random open direction (index 0..7) among those with decent clearance; -1 if none
integer pickOpenIdx(float minClear)
{
    if (gMaxClear < minClear) return -1;
    list c = [];
    integer i;
    for (i = 0; i < 8; i++)
    {
        float ci = llList2Float(gClear, i);
        if (ci >= minClear && ci >= 0.6 * gMaxClear && i != gLastOpen) c += [i];
    }
    if (llGetListLength(c) == 0)
    {
        for (i = 0; i < 8; i++)
        {
            float cj = llList2Float(gClear, i);
            if (cj >= minClear && cj >= 0.6 * gMaxClear) c += [i];
        }
    }
    if (llGetListLength(c) == 0) return -1;
    integer pick = llList2Integer(c, (integer)llFrand(llGetListLength(c)));
    gLastOpen = pick;
    return pick;
}

// ============================================================================
//  composition maths (section 2)
// ============================================================================
// 2.4  vertical composition by camera HEIGHT: eye line on the upper third, camera stays level
float camZ(float eyeRef, float d, integer fl)
{
    float z;
    if (fl & FL_RAISED) z = eyeRef + 0.4;
    else
    {
        z = eyeRef - d * tanV / 3.0;
        if (gStyle == 1) z -= 0.25;       // Ozu: lower still
    }
    z = fmax(z, gFloorZ + 0.35);
    if (gEnv == 2) z = fmin(z, gRoofZ - 0.3);
    return z;
}

// 2.3  distance at which the members (spread about gC, seen along V) fit the frame
float fitDist(vector V, float halfH, float lo, float hi)
{
    vector R = <V.y, -V.x, 0.0>;
    float hw = 0.0;
    integer n = llGetListLength(gMem) / 3;
    integer i;
    for (i = 0; i < n; i++)
    {
        float w = llFabs((llList2Vector(gMem, i * 3) - gC) * R);
        if (w > hw) hw = w;
    }
    hw += BODY_R;
    float dW = hw / tanH;
    float dH = halfH / tanV;
    return fclamp(fmax(dW, dH) * MARGIN, lo, hi);
}

// +1 if the subject (owner) faces the right of the view, -1 left; scene side when frontal/rear
float thirdsSide(vector V)
{
    vector R = <V.y, -V.x, 0.0>;
    float s = dirOf(gOY) * R;
    if (llFabs(s) < 0.2) return gSide;
    if (s > 0.0) return 1.0;
    return -1.0;
}

// 2.2 + 2.5  camera at azimuth az / distance deff / height cz, level (or theta down), subject on a third.
// Note: the thirds yaw is -side*alpha so the subject sits on the side OPPOSITE to where they look.
list buildShot(list P, float az, float deff, float cz)
{
    float theta = llList2Float(P, 5);
    integer fl = llList2Integer(P, 9);
    vector Fp = llList2Vector(P, 0);
    vector cam = Fp + dirOf(az) * deff;
    cam.z = cz;
    vector V = ZERO_VECTOR - dirOf(az);
    vector V2 = V;
    if (!(fl & FL_CENTER)) V2 = V * llEuler2Rot(<0.0, 0.0, -thirdsSide(V) * gAlpha>);
    float th = fclamp(theta, 0.0, gThetaMax);
    vector foc = cam + V2 * deff;
    foc.z = cz - deff * llTan(th);
    return [cam, foc];
}

// ============================================================================
//  shot plans: [Fp, az0, d, dMin, eyeRef, theta, arch, wFace, axis, flags]
// ============================================================================
list phiList()
{
    if (gStyle == 1) return [0.0, 180.0, 45.0, -45.0];
    if (gStyle == 2) return [180.0, 0.0, 135.0, -135.0];
    if (gStyle == 3) return [45.0, -45.0, 135.0, -135.0];
    return [45.0, -45.0, 135.0, -135.0, 180.0, 0.0];
}

list phiWeights()
{
    if (gStyle == 1) return [4.0, 2.0, 1.0, 1.0];
    if (gStyle == 2) return [4.0, 3.0, 1.0, 1.0];
    if (gStyle == 3) return [1.0, 1.0, 1.0, 1.0];
    return [3.0, 3.0, 3.0, 3.0, 2.0, 1.0];
}

// 2.7  group framing around gC (members already set)
list planGroup(integer arch, float dLo, float dHi, float halfH, integer isEns)
{
    integer n = llGetListLength(gMem) / 3;
    float sxx = 0.0;
    float syy = 0.0;
    float sxy = 0.0;
    integer i;
    for (i = 0; i < n; i++)
    {
        vector p = llList2Vector(gMem, i * 3);
        float dx = p.x - gC.x;
        float dy = p.y - gC.y;
        sxx += dx * dx;
        syy += dy * dy;
        sxy += dx * dy;
    }
    sxx = sxx / n;
    syy = syy / n;
    sxy = sxy / n;
    float sm = sxx + syy;
    float hd = (sxx - syy) * 0.5;
    float df = 2.0 * llSqrt(hd * hd + sxy * sxy);
    float an = 0.0;
    if (sm > 0.01) an = df / sm;
    integer fl = 0;
    if (isEns) fl = FL_ENS;
    if (gStyle == 2) fl = fl | FL_CENTER;
    float th = 0.0;
    if (gAnySit) th = 0.0872665;
    float az0 = 0.0;
    if (an > 0.35)
    {
        // row / line: shoot along the normal of the principal axis, towards the side people face
        float tp = 0.5 * llAtan2(2.0 * sxy, sxx - syy);
        float a1 = tp + PI_BY_TWO;
        float a2 = a1 + PI;
        if (facingScore(a1) >= facingScore(a2)) az0 = a1;
        else az0 = a2;
    }
    else
    {
        // ring / blob: most open direction, preferring the side people face; raised camera
        float bs = -100.0;
        for (i = 0; i < 8; i++)
        {
            float azc = i * 0.785398;
            float sc = fmin(llList2Float(gClear, i), dHi) / dHi + 0.5 * facingScore(azc);
            if (sc > bs)
            {
                bs = sc;
                az0 = azc;
            }
        }
        fl = fl | FL_RAISED;
        th = 0.104720;      // 6 degrees
    }
    float d = fitDist(ZERO_VECTOR - dirOf(az0), halfH, dLo, dHi);
    return [<gC.x, gC.y, gMeanEye>, az0, d, dLo, gMeanEye, th, arch, 1.0, ZERO_VECTOR, fl];
}

// 2.6  intimate: solo portrait / over-the-shoulder two-shot / three-shot
list planA()
{
    list ni = nearIdx();
    integer k = llGetListLength(ni);
    float th = 0.0;
    if (k >= 2)
    {
        setMembers(ni);
        return planGroup(0, 3.0, 6.0, 0.9, FALSE);
    }
    if (k == 1)
    {
        integer i1 = llList2Integer(ni, 0);
        vector p1 = llList2Vector(gAv, i1 * 5 + 1);
        vector ax = p1 - gOP;
        ax.z = 0.0;
        if (llVecMag(ax) >= 0.3)
        {
            setMembers(ni);
            vector cw = (gOP * W_OWN + p1) / (W_OWN + 1.0);
            gC = <cw.x, cw.y, gMeanEye>;
            vector A = llVecNorm(ax);
            vector N = <-A.y, A.x, 0.0>;
            // camera behind one shoulder on the scene side (180-degree rule); reverse shot = other shoulder, same side
            vector dc = N * gSide * 0.819152;      // cos 35
            if (gRev) dc = dc + A * 0.573576;      // sin 35
            else dc = dc - A * 0.573576;
            gRev = !gRev;
            dc = llVecNorm(dc);
            float dP = fitDist(ZERO_VECTOR - dc, 0.9, 2.5, 5.0);
            if (gAnySit) th = 0.0872665;
            integer flP = 0;
            if (gStyle == 2) flP = FL_CENTER;
            return [<gC.x, gC.y, gMeanEye>, azOf(dc), dP, 2.5, gMeanEye, th, 0, 0.5, A, flP];
        }
    }
    // solo portrait
    setMembers([]);
    list phis = phiList();
    list ws = phiWeights();
    integer np = llGetListLength(phis);
    integer ip;
    float phi = 0.0;
    float dS = 0.0;
    if (gJump && gLastPhi < 900.0)
    {
        // Ozu axial cut / Nouvelle Vague jump cut: same angle, closer
        phi = gLastPhi;
        float jf = 0.6;
        if (gStyle == 3) jf = 0.75;
        dS = fmax(1.6, gBaseD * jf);
    }
    else
    {
        for (ip = 0; ip < np; ip++)
        {
            if (llFabs(llList2Float(phis, ip) - gLastPhi) < 0.5) ws = llListReplaceList(ws, [0.0], ip, ip);
        }
        ip = pickW(ws);
        if (ip < 0) ip = 0;
        phi = llList2Float(phis, ip);
    }
    gJump = FALSE;
    float az0 = gOY + phi * DEG_TO_RAD;
    if (dS <= 0.0)
    {
        dS = fitDist(ZERO_VECTOR - dirOf(az0), 1.3, 2.5, 3.5);
        if (gStyle == 2) dS = dS * 1.2;
        gBaseD = dS;
    }
    gLastPhi = phi;
    if (gOSit) th = 0.0872665;
    integer flS = 0;
    if (gStyle == 2) flS = FL_CENTER;
    return [<gOP.x, gOP.y, gOE>, az0, dS, 2.0, gOE, th, 0, 0.0, ZERO_VECTOR, flS];
}

// 2.7  social ensemble tableau
list planB()
{
    list ci = clusterIdx();
    if (llGetListLength(ci) < 2) return [];
    setMembers(ci);
    return planGroup(1, 6.0, 14.0, 1.3, TRUE);
}

// 2.8  variant 2 = long shot (figure in landscape), 3 = Rueckenfigur (camera behind owner, looking out)
list planC(integer variant)
{
    if (!gSurveyOK) return [];
    integer fc = 0;
    if (gStyle == 2) fc = FL_CENTER;
    setMembers([]);
    if (variant == 2)
    {
        if (gEnv == 2) return [];
        float cap = fmin(45.0, gMaxCam - 1.0);
        if (cap < 25.0) return [];
        integer idx = pickOpenIdx(27.0);
        if (idx < 0) return [];
        float hi = fmin(cap, llList2Float(gClear, idx) - 2.0);
        if (hi < 25.0) return [];
        float dC = 25.0 + llFrand(hi - 25.0);
        return [<gOP.x, gOP.y, gOE>, idx * 0.785398, dC, 25.0, gOE, 0.0, 2, 0.0, ZERO_VECTOR, FL_FIXED | FL_FADE | fc];
    }
    integer id2 = pickOpenIdx(15.0);
    if (id2 < 0) return [];
    return [<gOP.x, gOP.y, gOE>, id2 * 0.785398 + PI, 3.0, 2.0, gOE, 0.0, 3, 0.0, ZERO_VECTOR, fc];
}

// 2.8 C2b  pillow shot: no avatars, lens along the most open direction (also the GPU cooldown shot)
list shotPillow()
{
    if (!gSurveyOK) return [];
    float need = 25.0;
    if (gEnv == 2) need = 15.0;
    integer idx = pickOpenIdx(need);
    if (idx < 0) return [];
    vector Dopen = dirOf(idx * 0.785398);
    vector Rd = <Dopen.y, -Dopen.x, 0.0>;
    vector E = <gOP.x, gOP.y, gOE>;
    integer attempt;
    float sgn = gSide;
    for (attempt = 0; attempt < 2; attempt++)
    {
        vector cam = <gOP.x, gOP.y, gOE + 0.3> + Rd * sgn;
        list r = ray(E, cam);
        integer st = llList2Integer(r, 0);
        if (st < 0)
        {
            gSweepErr = TRUE;
            return [];
        }
        if (st == 0)
        {
            list f = ray(cam, cam + Dopen * 20.0);
            if (llList2Integer(f, 0) < 0)
            {
                gSweepErr = TRUE;
                return [];
            }
            if (llList2Integer(f, 0) == 0 || llList2Float(f, 1) >= 12.0)
            {
                vector foc = cam + Dopen * 60.0;
                foc.z = cam.z;
                if (gEnv != 2) foc.z = cam.z + 60.0 * tanV / 3.0;     // horizon on the lower third
                return [cam, foc, 4, 0, gLastAz];
            }
        }
        sgn = -sgn;
    }
    return [];
}

// ============================================================================
//  sweep + verify (sections 3.2 - 3.4)
// ============================================================================
// stride 4: score, az, deff, strict-valid
integer bestOf(list C, integer needValid, integer skip)
{
    integer n = llGetListLength(C) / 4;
    integer b = -1;
    float bs = -1000.0;
    integer i;
    for (i = 0; i < n; i++)
    {
        if (i != skip)
        {
            if (!needValid || llList2Integer(C, i * 4 + 3))
            {
                float s = llList2Float(C, i * 4);
                if (b < 0 || s > bs)
                {
                    b = i;
                    bs = s;
                }
            }
        }
    }
    return b;
}

// hard checks + soft penalty for one candidate; returns [cam, focus, penalty] or []
list verify(list P, float az, float deff)
{
    vector Fp = llList2Vector(P, 0);
    float eyeRef = llList2Float(P, 4);
    integer fl = llList2Integer(P, 9);
    vector cc = Fp + dirOf(az) * deff;
    if (cc.x < 1.0 || cc.x > 255.0 || cc.y < 1.0 || cc.y > 255.0) return [];
    float cz;
    if (fl & FL_FIXED)
    {
        cz = fmax(gFloorZ + 1.6, groundAt(cc.x, cc.y, gOP.z) + 1.6);
        if (gSweepErr) return [];
    }
    else
    {
        cz = camZ(eyeRef, deff, fl);
        if (cz - gFloorZ < 1.0)
        {
            // low camera: make sure we are not inside a floor prim
            list g = ray(<cc.x, cc.y, cz>, <cc.x, cc.y, cz - 0.35>);
            integer gs = llList2Integer(g, 0);
            if (gs < 0)
            {
                gSweepErr = TRUE;
                return [];
            }
            if (gs == 1) cz = cz - llList2Float(g, 1) + 0.35;
        }
    }
    if (llFabs(cz - gWater) < 3.0 && cz < gWater + 0.3) cz = gWater + 0.3;
    if (gEnv == 2 && !(fl & FL_FIXED)) cz = fmin(cz, gRoofZ - 0.3);
    vector cam = <cc.x, cc.y, cz>;
    if (llVecDist(cam, gOP) > gMaxCam) return [];

    // reverse ray: camera -> subject (hits within 0.8 m of the subject are its own furniture)
    list rr = ray(cam, Fp);
    integer rs = llList2Integer(rr, 0);
    if (rs < 0)
    {
        gSweepErr = TRUE;
        return [];
    }
    if (rs == 1 && llList2Float(rr, 1) < llVecDist(cam, Fp) - 0.8) return [];

    float pen = 0.0;
    if (fl & FL_ENS)
    {
        // line of sight to the two farthest members: soft penalty
        integer nm = llGetListLength(gMem) / 3;
        integer m1 = -1;
        integer m2 = -1;
        float d1 = -1.0;
        float d2 = -1.0;
        integer mi;
        for (mi = 1; mi < nm; mi++)
        {
            float dm = llVecDist(llList2Vector(gMem, mi * 3), cam);
            if (dm > d1)
            {
                m2 = m1;
                d2 = d1;
                m1 = mi;
                d1 = dm;
            }
            else if (dm > d2)
            {
                m2 = mi;
                d2 = dm;
            }
        }
        list ms = [m1, m2];
        integer q;
        for (q = 0; q < 2; q++)
        {
            integer mm = llList2Integer(ms, q);
            if (mm >= 0)
            {
                vector mp = llList2Vector(gMem, mm * 3);
                mp.z = llList2Float(gMem, mm * 3 + 2);
                list mr = ray(cam, mp);
                integer ms2 = llList2Integer(mr, 0);
                if (ms2 < 0)
                {
                    gSweepErr = TRUE;
                    return [];
                }
                if (ms2 == 1 && llList2Float(mr, 1) < llVecDist(cam, mp) - 0.5) pen += 1.0;
            }
        }
    }
    list sh = buildShot(P, az, deff, cz);
    return sh + [pen];
}

// returns [cam, focus, arch, fade, az] or []   (gSweepErr set on ray errors)
list sweep(list P)
{
    vector Fp = llList2Vector(P, 0);
    float az0 = llList2Float(P, 1);
    float d = llList2Float(P, 2);
    float dMin = llList2Float(P, 3);
    float eyeRef = llList2Float(P, 4);
    integer arch = llList2Integer(P, 6);
    float wF = llList2Float(P, 7);
    vector axis = llList2Vector(P, 8);
    integer fl = llList2Integer(P, 9);
    float need = fmax(0.7 * dMin, 1.2);
    float z0 = camZ(eyeRef, d, fl);
    if (fl & FL_FIXED) z0 = gOE;

    list C = [];
    integer anyStrict = FALSE;
    integer i;
    for (i = 0; i < 7; i++)
    {
        float off = llList2Float(OFFS, i);
        float az = az0 + off;
        vector cc = Fp + dirOf(az) * d;
        vector ccFlat = <cc.x, cc.y, gOP.z>;
        float dOwn = llVecDist(ccFlat, gOP);
        if (cc.x > 1.0 && cc.x < 255.0 && cc.y > 1.0 && cc.y < 255.0 && dOwn <= gMaxCam)
        {
            cc.z = z0;
            list r = ray(Fp, cc);
            integer st = llList2Integer(r, 0);
            if (st < 0)
            {
                gSweepErr = TRUE;
                return [];
            }
            float deff = d;
            if (st == 1) deff = llList2Float(r, 1) - STANDOFF;
            if (deff > d) deff = d;
            if (deff >= 1.2)
            {
                float s = 3.0 * fmin(deff / d, 1.0) + 2.0 * llCos(off) + 1.5 * fmin(angDiff(az, gLastAz) / 1.047198, 1.0);
                if (wF > 0.0) s += wF * facingScore(az);
                if (axis != ZERO_VECTOR)
                {
                    vector nrm = <-axis.y, axis.x, 0.0>;
                    float lat = dirOf(az) * nrm;
                    if (lat * gSide > 0.0) s += 1.0;
                    else s -= 2.0;
                }
                if ((fl & FL_ENS) && ownerOccl(Fp + dirOf(az) * deff)) s -= 2.0;
                integer ok = (deff >= need);
                if (ok) anyStrict = TRUE;
                C += [s, az, deff, ok];
            }
        }
    }
    if (llGetListLength(C) == 0) return [];

    // best two candidates, verified in rank order; stop early on a clean one
    list bestR = [];
    float bestV = -1000.0;
    integer cur = bestOf(C, anyStrict, -1);
    integer tn = 0;
    while (cur >= 0 && tn < 2)
    {
        float cSc = llList2Float(C, cur * 4);
        float cAz = llList2Float(C, cur * 4 + 1);
        float cDe = llList2Float(C, cur * 4 + 2);
        list v = verify(P, cAz, cDe);
        if (gSweepErr) return [];
        if (llGetListLength(v) > 0)
        {
            float pen = llList2Float(v, 2);
            float val = cSc - pen;
            if (llGetListLength(bestR) == 0 || val > bestV)
            {
                bestV = val;
                integer fd = 0;
                if (fl & FL_FADE) fd = 1;
                bestR = [llList2Vector(v, 0), llList2Vector(v, 1), arch, fd, cAz];
            }
            if (pen == 0.0) tn = 2;
        }
        if (tn < 2) cur = bestOf(C, anyStrict, cur);
        tn++;
    }
    return bestR;
}

// ============================================================================
//  fallback ladder (section 3.5)   level 2 = shoulder, 3 = high corner
// ============================================================================
list fallbackShot(integer level)
{
    vector E = <gOP.x, gOP.y, gOE>;
    if (level == 2)
    {
        vector F0 = dirOf(gOY);
        vector R0 = <F0.y, -F0.x, 0.0>;
        vector cam2 = E - F0 * 0.9 + R0 * 0.25;
        list r2 = ray(E, cam2);
        integer s2 = llList2Integer(r2, 0);
        if (s2 < 0)
        {
            gSweepErr = TRUE;
            return [];
        }
        if (s2 == 1) return [];
        return [cam2, cam2 + F0 * 10.0, 0, 0, gLastAz];
    }
    integer best = 0;
    integer i;
    for (i = 1; i < 8; i++)
    {
        if (llList2Float(gClear, i) > llList2Float(gClear, best)) best = i;
    }
    float d = fmin(llList2Float(gClear, best) - 0.4, 3.0);
    if (d < 1.2) return [];
    vector dir = dirOf(best * 0.785398);
    vector cam3 = E + dir * d;
    cam3.z = fmin(gRoofZ - 0.3, gOE + 1.0);
    float dz = cam3.z - gOE;
    float pitch = 0.0;
    if (dz > 0.0) pitch = fmin(llAtan2(dz, d), 0.261799);       // up to 15 degrees
    vector foc3 = cam3 + (ZERO_VECTOR - dir) * d;
    foc3.z = cam3.z - d * llTan(pitch);
    list r3 = ray(cam3, E);
    integer s3 = llList2Integer(r3, 0);
    if (s3 < 0)
    {
        gSweepErr = TRUE;
        return [];
    }
    if (s3 == 1 && llList2Float(r3, 1) < llVecDist(cam3, E) - 0.8) return [];
    return [cam3, foc3, 0, 0, gLastAz];
}

// ============================================================================
//  editing grammar (section 4.4)
// ============================================================================
float holdFor(integer arch)
{
    if (gHoldMul <= 0.0) return 0.0;             // hold until an event
    float b = 20.0;
    if (arch == 1) b = 25.0;
    else if (arch == 2) b = 18.0;
    else if (arch >= 3) b = 8.0;
    float sm = 1.0;
    if (gStyle == 1) sm = 1.2;
    else if (gStyle == 2) sm = 1.6;
    else if (gStyle == 3) sm = 0.6;
    return b * sm * gHoldMul * (0.8 + 0.4 * llFrand(1.0));
}

newPillowTarget()
{
    integer lo = 4;
    integer hi = 6;
    if (gStyle == 1) { lo = 3; hi = 4; }
    else if (gStyle == 2) { lo = 6; hi = 8; }
    else if (gStyle == 3) { lo = 8; hi = 10; }
    gPillowTarget = lo + (integer)llFrand(hi - lo + 1);
}

newScene()
{
    gSceneAnchor = gOP;
    gSceneSig = sceneSig();
    gSigPend = "";
    gSigCount = 0;
    gEstablish = TRUE;
    gRev = FALSE;
    gLastPhi = 999.0;
    if (llFrand(1.0) < 0.5) gSide = 1.0;
    else gSide = -1.0;
}

string archName(integer a)
{
    if (a == 0) return "A";
    if (a == 1) return "B-ensemble";
    if (a == 2) return "C1-long";
    if (a == 3) return "C2-rueckenfigur";
    return "C2-pillow";
}

// shot = [cam, focus, arch, fade, az]
commit(list s)
{
    vector cam = llList2Vector(s, 0);
    vector foc = llList2Vector(s, 1);
    integer arch = llList2Integer(s, 2);
    integer fade = llList2Integer(s, 3);
    float az = llList2Float(s, 4);
    integer now = llGetUnixTime();
    if (arch == 2) fade = 1;
    if (gHaveShot && llVecDist(cam, gCurCam) > 20.0) fade = 1;
    float hold = holdFor(arch);
    llMessageLinked(LINK_SET, SHOT, packShot(cam, foc, hold, arch, fade), "");
    vector v = foc - cam;
    v.z = 0.0;
    if (llVecMag(v) > 0.01) gCurV = llVecNorm(v);
    gCurCam = cam;
    gCurFocus = foc;
    gCurArch = arch;
    gShotT = now;
    gHaveShot = TRUE;
    gLastAz = az;
    gOwnerAtShot = gOP;
    gNearAtShot = countNear();
    integer cat = arch;
    if (arch >= 3) cat = 3;
    gLastCat = cat;
    gCutsSinceSurvey++;
    if (arch == 4)
    {
        gSincePillow = 0;
        newPillowTarget();
    }
    else gSincePillow++;
    gEstablish = FALSE;
    gPreferA = FALSE;
    gFocusKey = NULL_KEY;
    gPendEvent = "";
    gErrCount = 0;
    if (!gSaidFirst)
    {
        gSaidFirst = TRUE;
        say("first shot: " + archName(arch) + ", camera " + (string)llRound(llVecDist(cam, gOP)) + " m away, hold "
            + (string)llRound(hold) + " s");
    }
    dbg(archName(arch) + "  hold " + (string)llRound(hold) + " s  rays " + (string)gRays
        + "  dist " + (string)llRound(llVecDist(cam, gOP)) + " m" + "  fade " + (string)fade
        + "  free mem " + (string)llGetFreeMemory());
}

// F4: keep the current composition and give it a fresh hold
extendCurrent()
{
    llMessageLinked(LINK_SET, SHOT, packShot(gCurCam, gCurFocus, holdFor(gCurArch), gCurArch, 0), "");
    gShotT = llGetUnixTime();
    gOwnerAtShot = gOP;
    gPendEvent = "";
    gPreferA = FALSE;
    dbg("F4: holding current shot");
}

giveUp()
{
    // F5: nothing usable. Core hands the default camera back and we try again later.
    llMessageLinked(LINK_SET, NO_SHOT, "15", "");
    gHaveShot = FALSE;
    gRetryAt = llGetUnixTime() + 15;
    gPreferA = FALSE;
    say("no usable shot found (tried all archetypes and fallbacks) - retrying in 15 s. env " + (string)gEnv
        + " (0 open,1 semi,2 interior), avatars seen " + (string)(llGetListLength(gAv) / 5) + ", max clearance " + (string)gMaxClear + " m");
}

// ray errors: keep the current shot, retry in 3 s; after 3 failures fall back to F4
rayFail()
{
    gErrCount++;
    if (gErrCount >= 3)
    {
        gErrCount = 0;
        if (gHaveShot)
        {
            extendCurrent();
        }
        else giveUp();
    }
    else gRetryAt = llGetUnixTime() + 3;
    say("ray error (" + (string)gErrCount + "/3) - retrying");
}

// weights [A, B, C1, C2] for the current scene
list ctxWeights(integer nNear, integer total, integer norepeat)
{
    list w;
    if (gPreferA || gFocusKey != NULL_KEY) return [100.0, 0.0, 0.0, 0.0];
    if (total >= 4) w = [30.0, 45.0, 10.0, 15.0];
    else if (total >= 2 || nNear >= 1) w = [55.0, 20.0, 10.0, 15.0];
    else if (gEnv == 2) w = [45.0, 0.0, 0.0, 55.0];
    else w = [15.0, 0.0, 30.0, 55.0];
    if (total < 3) w = llListReplaceList(w, [0.0], 1, 1);
    if (gEnv == 2 || !gFarOk || gMaxClear < 27.0 || gMaxCam < 26.0) w = llListReplaceList(w, [0.0], 2, 2);
    if (gMaxClear < 15.0) w = llListReplaceList(w, [0.0], 3, 3);
    if (gCool)
    {
        // long AFK: favour empty sky / sea (lighter on the GPU)
        w = [llList2Float(w, 0) * 0.5, llList2Float(w, 1) * 0.5, llList2Float(w, 2) * 0.7, llList2Float(w, 3) * 2.5];
    }
    if (gEstablish && norepeat && (llList2Float(w, 1) > 0.0 || llList2Float(w, 2) > 0.0))
    {
        w = [0.0, llList2Float(w, 1), llList2Float(w, 2), 0.0];
    }
    if (norepeat && gLastCat >= 0)
    {
        // never the same archetype twice, except A shot / reverse shot
        if (!(gLastCat == 0 && (nNear >= 1 || total >= 2))) w = llListReplaceList(w, [0.0], gLastCat, gLastCat);
    }
    return w;
}

integer chooseArch(list tried, integer nNear, integer total)
{
    integer pass;
    for (pass = 0; pass < 2; pass++)
    {
        list w = ctxWeights(nNear, total, pass == 0);
        integer i;
        integer nt = llGetListLength(tried);
        for (i = 0; i < nt; i++)
        {
            integer t = llList2Integer(tried, i);
            w = llListReplaceList(w, [0.0], t, t);
        }
        integer pk = pickW(w);
        if (pk >= 0) return pk;
    }
    return -1;
}

list tryArch(integer a)
{
    list P = [];
    if (a == 0) P = planA();
    else if (a == 1) P = planB();
    else if (a == 2) P = planC(2);
    else
    {
        // C2: pillow shot or Rueckenfigur
        integer wantPillow = (gSincePillow >= gPillowTarget) || (llFrand(1.0) < 0.6);
        list sp;
        if (wantPillow)
        {
            sp = shotPillow();
            if (gSweepErr) return [];
            if (llGetListLength(sp) > 0) return sp;
        }
        P = planC(3);
        if (llGetListLength(P) == 0 && !wantPillow) return shotPillow();
    }
    if (llGetListLength(P) == 0) return [];
    return sweep(P);
}

// ============================================================================
//  the cut: choose, compose, verify, send
// ============================================================================
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
    gRays = 0;
    gSweepErr = FALSE;
    if (!gSurveyOK || llVecDist(gOP, gSurveyPos) > 2.0 || gCutsSinceSurvey >= 6 || why == "start" || why == "resume")
    {
        if (!survey())
        {
            rayFail();
            return;
        }
    }
    integer nNear = countNear();
    integer total = 1 + llGetListLength(clusterIdx());

    // Ozu axial cut / Nouvelle Vague jump cut: same solo angle again, closer
    integer doJump = FALSE;
    if ((gStyle == 1 || gStyle == 3) && gLastCat == 0 && nNear == 0 && !gEstablish && !gPreferA && gLastPhi < 900.0 && llFrand(1.0) < 0.3) doJump = TRUE;
    gJump = doJump;

    list shot = [];
    list tried = [];
    integer tries = 0;
    integer a;
    // Ozu punctuation: a pillow shot every few cuts
    if (!doJump && gSincePillow >= gPillowTarget && gMaxClear >= 15.0 && !gPreferA && gFocusKey == NULL_KEY && !gEstablish)
    {
        tried += [3];
        shot = tryArch(3);
        tries++;
    }
    while (llGetListLength(shot) == 0 && tries < 3 && !gSweepErr)
    {
        if (doJump) a = 0;
        else a = chooseArch(tried, nNear, total);
        doJump = FALSE;
        if (a < 0) tries = 99;
        else
        {
            tried += [a];
            shot = tryArch(a);
            tries++;
        }
    }
    gJump = FALSE;
    if (!gSweepErr && llGetListLength(shot) == 0) shot = fallbackShot(2);
    if (!gSweepErr && llGetListLength(shot) == 0) shot = fallbackShot(3);
    if (gSweepErr)
    {
        gPreferA = FALSE;
        rayFail();
        return;
    }
    if (llGetListLength(shot) == 0)
    {
        // F4 (current shot still fine?) or F5
        if (gHaveShot)
        {
            list rc = ray(<gOP.x, gOP.y, gOE>, gCurCam);
            integer rcs = llList2Integer(rc, 0);
            if (rcs == 0 || (rcs == 1 && llList2Float(rc, 1) >= llVecDist(<gOP.x, gOP.y, gOE>, gCurCam) - 0.8))
            {
                extendCurrent();
                return;
            }
        }
        giveUp();
        return;
    }
    commit(shot);
}

// ============================================================================
//  scene events (section 4.4)
// ============================================================================
integer inFrame(vector p)
{
    vector to = p - gCurCam;
    to.z = 0.0;
    if (llVecMag(to) < 0.1) return TRUE;
    float c = fclamp(llVecNorm(to) * gCurV, -1.0, 1.0);
    return llAcos(c) <= 0.85 * gHalfH;
}

// new typers near us => speaker cut (typing flag only)
checkTypers()
{
    if (gSpeaker < 1) return;
    list typNow = [];
    integer n = llGetListLength(gAv) / 5;
    integer i;
    for (i = 0; i < n; i++)
    {
        key k = llList2Key(gAv, i * 5);
        if (llGetAgentInfo(k) & AGENT_TYPING)
        {
            typNow += [k];
            if (llListFindList(gPrevTyp, [k]) == -1 && llVecDist(llList2Vector(gAv, i * 5 + 1), gOP) <= R_ENS)
            {
                gFocusKey = k;
                gPendEvent = "speaker";
            }
        }
    }
    gPrevTyp = typNow;
}

onScan()
{
    gScanT = llGetUnixTime();
    if (!gActive || gPaused) return;
    if (!refreshOwner()) return;
    if (gWaitFirst)
    {
        gWaitFirst = FALSE;
        newScene();
        nextShot(gWaitWhy);
        return;
    }
    if (!gHaveShot) return;

    // scene change: group membership changed (stable for two scans) or the owner walked off
    string sig = sceneSig();
    integer sceneChanged = FALSE;
    if (sig != gSceneSig)
    {
        if (sig == gSigPend) gSigCount++;
        else
        {
            gSigPend = sig;
            gSigCount = 1;
        }
        if (gSigCount >= 2) sceneChanged = TRUE;
    }
    else
    {
        gSigPend = "";
        gSigCount = 0;
    }
    if (llVecDist(gOP, gSceneAnchor) > 3.0) sceneChanged = TRUE;

    integer nNear = countNear();
    string ev = "";
    if (sceneChanged)
    {
        newScene();
        ev = "scene";
    }
    else if (nNear > gNearAtShot) ev = "arrival";
    else if (gCurArch != 4 && !inFrame(gOP)) ev = "frame";
    if (nNear < gNearAtShot) gNearAtShot = nNear;
    if (ev != "") gPendEvent = ev;
}

// Avatar scan. A HUD's own position is in HUD space, so llSensor is unreliable here;
// use the region agent list instead (max 100) and keep the nearest MAX_AV within 20 m.
startScan()
{
    gScanT = llGetUnixTime();
    if (!refreshOwner())
    {
        onScan();
        return;
    }
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    list tmp = [];                       // stride 6: dist, key, pos, yaw, eyeZ, flags
    integer n = llGetListLength(ids);
    integer i;
    for (i = 0; i < n; i++)
    {
        key k = llList2Key(ids, i);
        if (k != gOwner)
        {
            list d = llGetObjectDetails(k, [OBJECT_POS, OBJECT_ROT]);
            if (llGetListLength(d) >= 2)
            {
                vector pos = llList2Vector(d, 0);
                float dist = llVecDist(pos, gOP);
                vector sz = llGetAgentSize(k);
                if (dist <= 20.0 && sz != ZERO_VECTOR)
                {
                    integer inf = llGetAgentInfo(k);
                    integer fl = 0;
                    float ke = K_EYE_STAND;
                    if (inf & AGENT_SITTING)
                    {
                        fl += 1;
                        ke = K_EYE_SIT;
                    }
                    if (inf & AGENT_TYPING) fl += 2;
                    vector fwd = llRot2Fwd(llList2Rot(d, 1));
                    tmp += [dist, k, pos, llAtan2(fwd.y, fwd.x), pos.z + ke * sz.z, fl];
                }
            }
        }
    }
    tmp = llListSort(tmp, 6, TRUE);
    gAv = [];
    n = llGetListLength(tmp) / 6;
    for (i = 0; i < n && i < MAX_AV; i++) gAv += llList2List(tmp, i * 6 + 1, i * 6 + 5);
    onScan();
}

stopAll()
{
    gActive = FALSE;
    gPaused = FALSE;
    gHaveShot = FALSE;
    gWaitFirst = FALSE;
    gRetryAt = 0;
    gPendEvent = "";
    gPreferA = FALSE;
    gJump = FALSE;
    gFocusKey = NULL_KEY;
    gSurveyOK = FALSE;
    gAv = [];
    gMem = [];
    gClear = [];
    gPrevTyp = [];
    llSetTimerEvent(0.0);
    if (gListen) llListenRemove(gListen);
    gListen = 0;
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
        gActive = FALSE;
        loadCfg();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "director");
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
            if (gFov < 0.1) gFov = 1.047198;
            stopAll();
            gActive = TRUE;
            loadCfg();
            gCool = FALSE;
            gErrCount = 0;
            gMoveUntil = 0;
            gLastCat = -1;
            gLastAz = 0.0;
            gLastOpen = -1;
            gSincePillow = 0;
            newPillowTarget();
            gWater = llWater(ZERO_VECTOR);
            gSaidFirst = FALSE;
            gWaitFirst = TRUE;
            gWaitWhy = "start";
            startScan();
            llSetTimerEvent(1.0);
            setupListen();
        }
        else if (num == DIR_STOP)
        {
            stopAll();
        }
        else if (num == DIR_NEXT)
        {
            if (!gWaitFirst) nextShot(str);
        }
        else if (num == DIR_PAUSE)
        {
            gPaused = TRUE;
        }
        else if (num == DIR_RESUME)
        {
            gPaused = FALSE;
            if (str == "tp")
            {
                // new region / position: forget geometry, rescan, re-survey, new establishing shot
                gHaveShot = FALSE;
                gSurveyOK = FALSE;
                gWater = llWater(ZERO_VECTOR);
                gWaitFirst = TRUE;
                gWaitWhy = "resume";
                startScan();
            }
            else
            {
                gShotT = llGetUnixTime();
                if (gWaitFirst) startScan();
            }
        }
        else if (num == DIR_MOVING)
        {
            gMoveUntil = llGetUnixTime() + 3;
        }
        else if (num == DIR_COOLDOWN)
        {
            if (gCoolMin > 0) gCool = TRUE;
        }
        else if (num == CFG_CHANGED)
        {
            loadCfg();
        }
        else if (num == MSG_VER)
        {
            if (str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "director");
        }
        else if (num == STATUS)
        {
            if (str == "?")
            {
                say("v" + VERSION + " active " + (string)gActive + ", paused " + (string)gPaused + ", waiting first scan " + (string)gWaitFirst
                    + ", have shot " + (string)gHaveShot + ", env " + (string)gEnv + ", avatars seen " + (string)(llGetListLength(gAv) / 5)
                    + ", last category " + (string)gLastCat + ", long shots " + (string)gFarOk + ", free mem " + (string)llGetFreeMemory());
            }
        }
    }

    listen(integer channel, string name, key id, string msg)
    {
        if (!gActive || gPaused || gSpeaker != 2) return;
        if (id == gOwner) return;
        integer ix = llListFindList(gAv, [id]);
        if (ix >= 0 && (ix % 5) == 0)
        {
            gFocusKey = id;
            gPendEvent = "speaker";
        }
    }

    timer()
    {
        if (!gActive || gPaused) return;
        integer now = llGetUnixTime();
        if (gRetryAt > 0 && now >= gRetryAt)
        {
            gRetryAt = 0;
            nextShot("retry");
            return;
        }
        float iv = SCAN_SEC;
        if (llGetRegionTimeDilation() < 0.8) iv = SCAN_SEC * 2.0;
        if (now - gScanT >= iv) startScan();
        if (!gHaveShot) return;
        checkTypers();
        integer since = now - gShotT;
        // director mode: manual session and the owner is walking - re-frame when they leave the shot
        if (gManual && now < gMoveUntil && since >= 2 && gCurArch != 4)
        {
            if (refreshOwner())
            {
                if (!inFrame(gOP) || llVecDist(gOP, gOwnerAtShot) > 4.0)
                {
                    gPreferA = TRUE;
                    nextShot("moved");
                    return;
                }
            }
        }
        if (gPendEvent != "" && since >= MIN_HOLD)
        {
            string ev = gPendEvent;
            nextShot(ev);
        }
    }
}
