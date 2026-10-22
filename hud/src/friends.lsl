// ============================================================================
//  Take 12  -  friends.lsl  (v4)  - Friends mode
//  You plus the friends you picked (up to 10, within 30 m) in one composed shot.
//  While everyone stays in the frame the camera glides slowly to keep the group
//  framed; if anyone is out of frame for about 1 s it cuts to a wider shot that
//  holds everyone. Chat cuts: whoever of you speaks gets an over-the-shoulder cut.
//  The friends list and picker menu are in picker.lsl.
//  Shot types: 3 friends group, 4 speaker, 0 portrait (nobody near).
//  Started only from the menu / chat, never by AFK.
// ============================================================================

string VERSION = "6.1.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer MOVING     = 7306;
integer SHOT       = 7310;
integer NO_SHOT    = 7311;
integer GLIDE      = 7312;
integer ACK        = 7313;
integer SPEAKER    = 7315;
integer CFG_CHANGED= 7330;
integer CMD        = 7371;
integer FOVMSG     = 7318;   // core -> cameras: your lens changed (radians)
integer LENS       = 7319;   // lens -> friends  gear, angle, Tune aim, round (lens.lsl)
integer MSG_VER    = 7360;
integer STATUS     = 7370;

float K_EYE_STAND = 0.37;
float K_EYE_SIT   = 0.25;
float BODY_R      = 0.35;
float MARGIN      = 1.3;     // the outermost person ends about 12 % of the screen width from the edge
float STANDOFF    = 0.4;
float R_FR        = 30.0;    // friends further than this are not framed
float gBase;                 // s  a fresh angle about this often (from Pace)
float gMinHold;              // s  shortest time before an event may cut
float MAX_DIST    = 25.0;    // m  furthest camera from the group
float GLIDE_MIN   = 0.2;     // m  the group moved this far: glide the camera along   // TUNE in-world
integer SPK_COOL  = 30;

list OFFS = [0.0, 0.436332, -0.436332, 0.872665, -0.872665, 1.396263, -1.396263];
list PHI  = [45.0, -45.0, 135.0, -135.0, 180.0, 0.0];

float   gThetaMax;
float   gSeatEl;                // seated view: how high above you the camera looks down (0 = off)
integer gTrace;
integer gChatOn;
list    gRayOpts;
float   gFov;
float   tanV;
float   tanH;
float   gAlpha;

key     gOwner;
integer gActive;
integer gPaused;
integer gWaitFirst;
integer gScanT;
integer gTick;
integer gMoveUntil;
string  gPendEvent;
integer gToldAlone;
integer gChat;
key     gSpeaker;
key     gLastSpk;
integer gLastSpkT;

list    gFKeys;              // saved friends
vector  gOP;
float   gOY;
float   gOE;
integer gOSit;
integer gSitAtShot;
float   gLed;                // Follow my lead (lens.lsl): your distance along the view, 0 = automatic
float   gLedAz;              // ... from where
integer gLedN;               // ... with this many friends here
vector  gAim;                // ... and where you aimed, from the planned subject
float   gSeatR;                 // extra body radius for a close view of someone lying down
integer gLastClose;          // the last group shot was a close one: the next is a wide one
integer gHasN;
vector  gNPos;
float   gNEye;
list    gGrp;                // saved friends present within R_FR, nearest first (positions)
list    gGrpK;               // ... and their keys
integer gUsedN;              // how many of them the current shot frames

float   gRoofZ;
float   gFloorZ;
integer gIndoor;
integer gSurveyOK;
vector  gSurveyPos;

float   gSide;
integer gRev;
float   gLastPhi;

vector  gPFp;
float   gPAz;
float   gPd;
float   gPEye;
float   gPTh;
float   gPLo;                // nearest and furthest camera for this plan
float   gPHi;
float   gVNeed;              // distance the height of the shot needs
float   gMult;               // > 1: a wider shot (after someone was lost)
list    gMeas;               // who must be fully in the picture (not the over-the-shoulder foreground)
vector  gPAxis;
integer gPCenter;
integer gPType;

integer gHaveShot;
integer gShotT;
vector  gCurCam;
vector  gCurFoc;
vector  gCurV;
vector  gCenter;             // centre of the group at the last shot or glide
integer gPresAtShot;
vector  gOwnerAtShot;
integer gSweepErr;
integer gSkip;               // this shot was asked for with "next": it must differ from the one on screen
integer gOut;                // half-second ticks someone has been out of frame

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

tsay(string s)
{
    if (gTrace) llOwnerSay("[Take 12] " + s);
}

loadCfg()
{
    gThetaMax = (float)cfg("theta_max", "10") * DEG_TO_RAD;
    gSeatEl   = (float)cfg("seat_deg", "45") * DEG_TO_RAD;
    gTrace    = (integer)cfg("trace", "0");
    float pace = (float)cfg("hold", "60");                // the Pace setting also sets the people cameras' rhythm
    gBase = fclamp(0.75 * pace, 20.0, 150.0);               // a shot is held about this long (Calm 60 s: 45 s)
    gMinHold = fmax(12.0, 0.25 * pace);                     // an event (arrival, speaker, left the frame) cuts no sooner than this (Calm: 15 s)
    gChatOn   = (integer)cfg("chat_cuts", "1");
    gRayOpts  = [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1];
    if ((integer)cfg("phantom", "0")) gRayOpts += [RC_DETECT_PHANTOM, TRUE];
    float aspect = (float)cfg("aspect", "1.778");
    if (aspect < 0.5) aspect = 1.778;
    if (gFov < 0.1) gFov = 1.047198;
    tanV = llTan(gFov * 0.5);
    gAlpha = llAtan2(tanV * aspect / 3.0, 1.0);             // rule of thirds on your window
    tanH = tanV * fmin(aspect, 1.6);                        // people are fitted for a 16:10 window: 16:9 has room to spare
}

list ray(vector a, vector b)
{
    a.x = fclamp(a.x, 0.5, 255.5);
    a.y = fclamp(a.y, 0.5, 255.5);
    b.x = fclamp(b.x, 0.5, 255.5);
    b.y = fclamp(b.y, 0.5, 255.5);
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

integer survey()
{
    vector E = <gOP.x, gOP.y, gOE>;
    list u = ray(E, E + <0.0, 0.0, 40.0>);
    list dn = ray(E, E - <0.0, 0.0, 10.0>);
    if (llList2Integer(u, 0) < 0 || llList2Integer(dn, 0) < 0) return FALSE;
    gRoofZ = E.z + llList2Float(u, 1);
    gFloorZ = E.z - llList2Float(dn, 1);
    gIndoor = (llList2Integer(u, 0) == 1 && llList2Float(u, 1) < 12.0);
    gSurveyOK = TRUE;
    gSurveyPos = gOP;
    return TRUE;
}

float camZ(float eyeRef, float d)
{
    float z = fmax(eyeRef - d * tanV / 3.0, gFloorZ + 0.35);
    if ((gOSit || gLed > 0.0) && gSeatEl > 0.0) z = eyeRef + d * llTan(gSeatEl);
    if (gIndoor) z = fmin(z, gRoofZ - 0.3);
    return z;
}

// the view direction of a camera on side az (rule of thirds with lead room unless the plan is centred)
vector viewDir(float az)
{
    vector V = ZERO_VECTOR - dirOf(az);
    if (gPCenter) return V;
    float fs = dirOf(gOY) * <V.y, -V.x, 0.0>;
    float sd = gSide;
    if (fs > 0.2) sd = 1.0;
    else if (fs < -0.2) sd = -1.0;
    return V * llEuler2Rot(<0.0, 0.0, -sd * gAlpha>);
}

// how far back a camera on side az must be so that everyone in gMeas is fully in the picture with the margin,
// each at their real depth (someone nearer the camera looks wider)
float needAt(float az)
{
    vector u = dirOf(az);
    vector V = viewDir(az);
    vector P = <-V.y, V.x, 0.0>;
    float k = tanH / MARGIN;
    float c = k * (ZERO_VECTOR - u) * V;
    float sn = u * P;
    float need = gVNeed;
    integer i;
    for (i = 0; i < llGetListLength(gMeas); i++)
    {
        vector o = llList2Vector(gMeas, i) + gAim - gPFp;
        o.z = 0.0;
        float a = o * P;
        float b = BODY_R + gSeatR - k * (o * V);
        need = fmax(need, fmax((a + b) / (c + sn), (b - a) / (c - sn)));
    }
    return need;
}

// people close together: now and then a close view of faces and shoulders (the caller remembers it, so two in a row never happen)
integer closeView(float spread)
{
    // seated: more often; and the longer your lens (mm = 12 / tanV), the more often, like a camera operator would
    if (spread >= 3.5 || gLastClose || llFrand(1.0) >= 0.55 + 0.25 * gOSit + fclamp((12.0 / tanV - 35.0) / 120.0, -0.15, 0.3)) return FALSE;
    gVNeed = 0.75 / tanV * MARGIN;
    gPLo = 1.2;
    gPEye += 0.15;                                      // a little headroom for a taller neighbour
    if (gOSit) gSeatR = 0.45;                           // lying down, a head can be 0.8 m from where the avatar stands
    return TRUE;
}

// the camera hangs above the shot when you are seated, so a picture's distance is the slant: stand that much closer
float seatD(float S)
{
    if ((!gOSit && gLed == 0.0) || gSeatEl <= 0.0) return S;
    float d = S * llCos(gSeatEl);
    float R = fmax(gRoofZ - 0.3 - gPEye, 0.0);
    if (gIndoor && d * llTan(gSeatEl) > R) d = llSqrt(S * S - R * R);   // a low ceiling caps the rise
    return d;
}

planA(integer pair)
{
    gPAxis = ZERO_VECTOR;
    gPCenter = FALSE;
    gPType = 0;
    gPEye = gOE;
    gPFp = <gOP.x, gOP.y, gOE>;
    gPTh = 0.0;
    if (gOSit) gPTh = 0.0872665;
    gMeas = [gOP];
    gVNeed = 1.3 / tanV * MARGIN;
    gPLo = 2.5;
    gPHi = 3.5;
    gMult = 1.0;
    vector ax = gNPos - gOP;
    ax.z = 0.0;
    if (pair && gHasN && llVecMag(ax) >= 0.3)
    {
        vector A = llVecNorm(ax);
        vector dc = <-A.y, A.x, 0.0> * gSide * 0.819152;      // behind one shoulder, 35 deg, 180-degree-rule side
        if (gRev) dc = dc + A * 0.573576;                    // reverse shot: other shoulder, same side, facing you
        else
        {
            dc = dc - A * 0.573576;
            gMeas = [gNPos];                                 // over your shoulder: they face the camera
        }
        gRev = !gRev;
        dc = llVecNorm(dc);
        gPEye = (gOE + gNEye) * 0.5;
        vector cw = (gOP * 1.5 + gNPos) / 2.5;
        gPFp = <cw.x, cw.y, gPEye>;
        gPAz = llAtan2(dc.y, dc.x);
        gPAxis = A;
        gPType = 1;
        gVNeed = 0.9 / tanV * MARGIN;
        gPHi = 6.5;
        gPd = fclamp(needAt(gPAz), gPLo, gPHi);
        return;
    }
    integer i = (integer)llFrand(6.0);
    if (llFabs(llList2Float(PHI, i) - gLastPhi) < 0.5) i = (i + 1) % 6;
    gLastPhi = llList2Float(PHI, i);
    gPAz = gOY + gLastPhi * DEG_TO_RAD;
    gPd = fclamp(gVNeed, gPLo, gPHi);
}

list tryCand(float az, float de)
{
    vector cc = gPFp + dirOf(az) * de;
    if (cc.x < 1.0 || cc.x > 255.0 || cc.y < 1.0 || cc.y > 255.0) return [];
    vector cam = <cc.x, cc.y, camZ(gPEye, de)>;
    list rr = ray(cam, gPFp);
    integer rs = llList2Integer(rr, 0);
    if (rs < 0) gSweepErr = TRUE;
    if (rs < 0 || (rs == 1 && llList2Float(rr, 1) < llVecDist(cam, gPFp) - 0.8)) return [];
    vector foc = cam + viewDir(az) * de;
    float r = cam.z - gPEye;
    if ((gOSit || gLed > 0.0) && gSeatEl > 0.0 && r > de * 0.176) foc.z = cam.z - de * llTan(llAtan2(r, de) + llAtan2(tanV, 3.0) * (gLed == 0.0));
    else foc.z = cam.z - de * llTan(fclamp(gPTh, 0.0, gThetaMax));
    return [cam, foc];
}

// 7 candidate directions around the plan, the best two verified: [cam, focus, type] or []. Each side gets the
// distance that fits everyone from that side; a side where a wall is closer than that is skipped, never squeezed.
list sweep()
{
    list C = [];
    integer i;
    for (i = 0; i < 7; i++)
    {
        float off = llList2Float(OFFS, i);
        float az = gPAz + off;
        float de = seatD(fmax(needAt(az) * gMult, gPLo));
        vector cc = gPFp + dirOf(az) * de;
        cc.z = camZ(gPEye, de);
        list r = [0, 0.0];
        if (de <= gPHi) r = ray(gPFp, cc);
        integer st = llList2Integer(r, 0);
        if (st < 0)
        {
            gSweepErr = TRUE;
            return [];
        }
        if (de <= gPHi && (st == 0 || llList2Float(r, 1) - STANDOFF >= de))
        {
            float s = 3.0 * fmin(1.0, gPd / de) + 2.0 * llCos(off);
            if (gPAxis != ZERO_VECTOR)
            {
                float lat = dirOf(az) * <-gPAxis.y, gPAxis.x, 0.0>;
                if (lat * gSide > 0.0) s += 1.0;
                else s -= 2.0;
            }
            // "next" asked by you: never the spot already on screen
            if (!gSkip || llVecDist(<cc.x, cc.y, 0.0>, <gCurCam.x, gCurCam.y, 0.0>) > 1.5) C += [s, az, de];
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
        if (llGetListLength(v) > 0) return v + [gPType];
        skip = b;
    }
    return [];
}

// is p inside the picture? lateral offset against the frame half-width at p's depth; k = how much of the half-width counts
integer inFrame(vector p, float k)
{
    vector to = p + gAim - gCurCam;
    to.z = 0.0;
    if (llVecMag(to) < 0.1) return TRUE;
    float fwd = to * gCurV;
    float lat = llFabs(to.x * gCurV.y - to.y * gCurV.x);
    return (fwd > 0.3 && lat <= k * tanH * fwd);
}

// ============================================================================
//  friends list
// ============================================================================
loadFriends()
{
    gFKeys = [];
    list L = llParseString2List(cfg("friends", ""), [";"], []);
    integer i;
    for (i = 0; i < llGetListLength(L); i++)
    {
        gFKeys += [(key)llList2String(llParseString2List(llList2String(L, i), [","], []), 0)];
    }
}


// ============================================================================
//  sensing: saved friends within R_FR, nearest first
// ============================================================================
scan()
{
    gScanT = llGetUnixTime();
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    list tmp = [];
    integer n = llGetListLength(ids);
    integer i;
    for (i = 0; i < n; i++)
    {
        key k = llList2Key(ids, i);
        if (k != gOwner && llListFindList(gFKeys, [k]) >= 0)
        {
            list d = llGetObjectDetails(k, [OBJECT_POS]);
            if (llGetListLength(d) > 0)
            {
                vector p = llList2Vector(d, 0);
                float dist = llVecDist(p, gOP);
                if (dist <= R_FR) tmp += [dist, k, p];
            }
        }
    }
    tmp = llListSort(tmp, 3, TRUE);
    gGrp = [];
    gGrpK = [];
    n = llGetListLength(tmp) / 3;
    for (i = 0; i < n && i < 9; i++)
    {
        gGrp += [llList2Vector(tmp, i * 3 + 2)];
        gGrpK += [llList2Key(tmp, i * 3 + 1)];
    }
    gHasN = (n > 0);
    if (gHasN)
    {
        gNPos = llList2Vector(gGrp, 0);
        vector nsz = llGetAgentSize(llList2Key(gGrpK, 0));
        gNEye = gNPos.z + K_EYE_STAND * nsz.z;
    }
}

// you plus the first cnt friends
vector centroid(integer cnt)
{
    vector C = gOP;
    integer i;
    for (i = 0; i < cnt; i++) C += llList2Vector(gGrp, i);
    return C / (float)(cnt + 1);
}

// group tableau: you plus the first cnt friends (nearest first); the farthest are dropped until it fits within
// MAX_DIST. mult widens the shot (a snap after someone left the frame)
integer planF(float mult, integer cnt)
{
    while (cnt > 0)
    {
        list M = [gOP] + llList2List(gGrp, 0, cnt - 1);
        integer n = cnt + 1;
        vector C = centroid(cnt);
        float best = 0.0;
        vector A = <1.0, 0.0, 0.0>;
        integer i;
        integer j;
        for (i = 0; i < n; i++)
        {
            for (j = i + 1; j < n; j++)
            {
                vector dv = llList2Vector(M, j) - llList2Vector(M, i);
                dv.z = 0.0;
                if (llVecMag(dv) > best)
                {
                    best = llVecMag(dv);
                    A = llVecNorm(dv);
                }
            }
        }
        vector Nn = <-A.y, A.x, 0.0>;
        if (dirOf(gOY) * Nn < 0.0) Nn = ZERO_VECTOR - Nn;
        gPEye = C.z + (gOE - gOP.z) + gAim.z;
        gPFp = <C.x + gAim.x, C.y + gAim.y, gPEye>;
        gPAz = llAtan2(Nn.y, Nn.x);
        if (gLed > 0.0) gPAz = gLedAz;
        gPAxis = ZERO_VECTOR;
        gPTh = 0.0;
        gPCenter = TRUE;
        gPType = 3;
        gMeas = M;
        gVNeed = 1.3 / tanV * MARGIN;
        gPLo = 3.0;
        gPHi = MAX_DIST;
        gMult = mult;
        integer cl = FALSE;
        if (gLed > 0.0)                                 // your lead: your distance, whoever it leaves out
        {
            gMeas = [];
            gVNeed = gLed;
            gPLo = gLed;
        }
        else if (mult == 1.0) cl = closeView(best);     // automatic
        float need = needAt(gPAz) * mult;               // everyone fits, those nearer the camera counted wider
        if (need <= MAX_DIST || cnt == 1)
        {
            gLastClose = cl;
            gPd = fclamp(need, gPLo, MAX_DIST);
            gUsedN = cnt;
            return TRUE;
        }
        cnt--;
    }
    return FALSE;
}

// a cut to whoever just spoke: [cam, focus, 4] or []
list speakerShot()
{
    integer rv = gRev;
    if (gSpeaker == gOwner)
    {
        if (!gHasN) return [];
        gRev = TRUE;                                   // over a friend's shoulder, facing you
    }
    else
    {
        list d = llGetObjectDetails(gSpeaker, [OBJECT_POS]);
        if (llGetListLength(d) == 0) return [];
        gNPos = llList2Vector(d, 0);
        vector nsz = llGetAgentSize(gSpeaker);
        gNEye = gNPos.z + K_EYE_STAND * nsz.z;
        gHasN = TRUE;
        gRev = FALSE;                                  // over your shoulder, facing them
    }
    planA(TRUE);
    list sh = sweep();
    gRev = rv;
    if (llGetListLength(sh) == 0) return [];
    gLastSpk = gSpeaker;
    gLastSpkT = llGetUnixTime();
    return llListReplaceList(sh, [4], 2, 2);
}

speak(key who)
{
    if (!gActive || !gChatOn) return;
    if (who == gLastSpk && llGetUnixTime() - gLastSpkT < SPK_COOL) return;
    gSpeaker = who;
    gPendEvent = "speaker";
}

chatListen()
{
    if (gChat) llListenRemove(gChat);
    gChat = 0;
    if (gActive && gChatOn) gChat = llListen(0, "", NULL_KEY, "");
}

newScene()
{
    gRev = FALSE;
    gLastPhi = 999.0;
    gSide = 1.0;
    if (llFrand(1.0) < 0.5) gSide = -1.0;
}

// ============================================================================
//  the cut
// ============================================================================
nextShot(float mult)
{
    if (!gActive || gPaused) return;
    string ev = gPendEvent;
    gPendEvent = "";
    if (!refreshOwner()) return;                    // core covers and asks again
    gSweepErr = FALSE;
    gSeatR = 0.0;
    if (gLed > 0.0 && llGetListLength(gGrp) != gLedN)
    {
        gLed = 0.0;                                 // someone came or went: automatic again (lens confirms)
        llMessageLinked(LINK_SET, CMD, "autoq", "");
    }
    if (!gSurveyOK || llVecDist(gOP, gSurveyPos) > 2.0) survey();
    list shot = [];
    gUsedN = 0;
    if (ev == "speaker" && gChatOn) shot = speakerShot();
    if (llGetListLength(shot) == 0 && llGetListLength(gGrp) > 0 && planF(mult, llGetListLength(gGrp)))
    {
        shot = sweep();
        integer t;
        for (t = 0; t < 3 && llGetListLength(shot) == 0 && !gSweepErr && gUsedN > 1; t++)
        {
            if (planF(mult, gUsedN - 1)) shot = sweep();     // walls in the way: frame fewer friends, nearest first
        }
    }
    if (llGetListLength(shot) == 0 && !gSweepErr)
    {
        if (llGetListLength(gGrp) == 0 && !gToldAlone)
        {
            gToldAlone = TRUE;
            tsay("friends: none here yet");
        }
        gUsedN = 0;
        planA(FALSE);
        shot = sweep();
        if (llGetListLength(shot) == 0 && !gSweepErr)
        {
            gVNeed = 0.9 / tanV * MARGIN;               // a tight space: a closer, half-length view of you
            gPLo = 1.5;
            shot = sweep();
        }
    }
    if (llGetListLength(shot) == 0)
    {
        gHaveShot = FALSE;
        llMessageLinked(LINK_SET, NO_SHOT, "none", "");
        return;
    }
    vector cam = llList2Vector(shot, 0);
    vector foc = llList2Vector(shot, 1);
    integer type = llList2Integer(shot, 2);
    float hold = gBase * (0.85 + 0.3 * llFrand(1.0));
    if (type == 4) hold = fmax(14.0, 0.4 * gBase);          // a speaker cut is short (Calm: 18 s)
    llMessageLinked(LINK_SET, SHOT, (string)cam + "|" + (string)foc + "|" + (string)hold + "|" + (string)type + "|" + (string)gPFp, "");
    vector v = foc - cam;
    v.z = 0.0;
    gCurV = llVecNorm(v);
    gCurCam = cam;
    gCurFoc = foc;
    gShotT = llGetUnixTime();
    gHaveShot = TRUE;
    gOwnerAtShot = gOP;
    gSitAtShot = gOSit;
    gOut = 0;
    gCenter = centroid(gUsedN);
    gPresAtShot = llGetListLength(gGrp);
    tsay("friends: shot " + (string)type + ", " + (string)(gUsedN + 1) + " in frame");
}

// you and the friends in the shot all within k of the half-width?
integer inFrameAll(float k)
{
    integer all = inFrame(gOP, k);
    integer i;
    for (i = 0; i < gUsedN && i < llGetListLength(gGrp); i++)
    {
        if (!inFrame(llList2Vector(gGrp, i), k)) all = FALSE;
    }
    return all;
}

// every 0.5 s while a friends group shot is on: glide to keep the group framed, pull back gently when someone nears
// the edge, snap to a wider shot if someone is lost
glideTick(integer since)
{
    integer i;
    if (!inFrameAll(0.97))
    {
        gOut++;
        if (gOut >= 2 && since >= 3)
        {
            nextShot(1.3);                          // a wider shot that holds everyone
        }
        return;
    }
    gOut = 0;
    // someone near the edge: glide straight back (same view) until everyone is well inside again, no cut
    float back = 0.0;
    list M = [gOP] + llList2List(gGrp, 0, gUsedN - 1);
    for (i = 0; i < llGetListLength(M); i++)
    {
        vector to = llList2Vector(M, i) - gCurCam;
        to.z = 0.0;
        back = fmax(back, llFabs(to.x * gCurV.y - to.y * gCurV.x) / (0.6 * tanH) - to * gCurV);
    }
    if (back > 0.3 && !inFrameAll(0.8))
    {
        vector bc = gCurCam - gCurV * back;
        if (llVecDist(bc, gCenter) > MAX_DIST || llList2Integer(ray(gCurCam, bc), 0) != 0)
        {
            nextShot(1.3);                          // no room behind the camera: cut to a wider shot
            return;
        }
        gCurCam = bc;
        gCurFoc = gCurFoc - gCurV * back;
        llMessageLinked(LINK_SET, GLIDE, (string)gCurCam + "|" + (string)gCurFoc, "");
        return;
    }
    vector C = centroid(gUsedN);
    vector dl = C - gCenter;
    if (llVecMag(dl) <= GLIDE_MIN) return;
    vector nc = gCurCam + dl;
    vector nf = gCurFoc + dl;
    if (nc.x < 1.0 || nc.x > 255.0 || nc.y < 1.0 || nc.y > 255.0) return;
    list r = ray(gCurCam, nc);
    if (llList2Integer(r, 0) != 0)
    {
        nextShot(1.0);                              // the glide would hit a wall: cut instead
        return;
    }
    llMessageLinked(LINK_SET, GLIDE, (string)nc + "|" + (string)nf, "");
    gCurCam = nc;
    gCurFoc = nf;
    gCenter = C;
}

nextTimer()
{
    if (gActive) llSetTimerEvent(0.5);
    else llSetTimerEvent(0.0);
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
        loadCfg();
        loadFriends();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "friends");
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
            list L = llParseString2List(str, ["|"], []);
            gActive = (llList2String(L, 0) == "friends");
            if (!gActive)
            {
                chatListen();
                nextTimer();
                return;
            }
            llMessageLinked(LINK_SET, ACK, "friends", "");
            gFov = (float)llList2String(L, 1);
            loadCfg();
            loadFriends();
            chatListen();
            gPaused = FALSE;
            gHaveShot = FALSE;
            gSurveyOK = FALSE;
            gPendEvent = "";
            gMoveUntil = 0;
            gToldAlone = FALSE;
            newScene();
            nextTimer();
            if (refreshOwner())
            {
                scan();
                nextShot(1.0);
            }
            else gWaitFirst = TRUE;
        }
        else if (num == STOP)
        {
            gActive = FALSE;
            gHaveShot = FALSE;
            gWaitFirst = FALSE;
            chatListen();
            nextTimer();
        }
        else if (num == LENS)
        {
            list L = llParseString2List(str, ["|"], []);
            gLed = llList2Float(L, 0);
            loadCfg();
            if (gLed > 0.0) gSeatEl = llList2Float(L, 1);
            gLedAz = llList2Float(L, 2);
            gAim = (vector)llList2String(L, 3);
            gLedN = llGetListLength(gGrp);
            if (gActive && gHaveShot && llList2Integer(L, 4)) nextShot(1.0);    // W/S or Auto: now
        }
        else if (num == FOVMSG)
        {
            // your lens changed: the same picture, a new perspective - the camera dollies along its line to the focus
            // (Follow my lead: lens answers the zoom with LENS, which puts back your angle after this loadCfg)
            float k = tanV;
            gFov = (float)str;
            loadCfg();
            if (!gActive || !gHaveShot) return;
            vector nc = gCurFoc + (gCurCam - gCurFoc) * (k / tanV);
            if (llVecDist(nc, gCenter) > MAX_DIST || llList2Integer(ray(gCurFoc, nc), 0)) nextShot(1.0);
            else
            {
                gCurCam = nc;
                llMessageLinked(LINK_SET, GLIDE, (string)gCurCam + "|" + (string)gCurFoc + "|1.5", "");
            }
        }
        else if (num == CFG_CHANGED)
        {
            loadCfg();
            chatListen();
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "friends");
        else if (num == STATUS && str == "?")
        {
            llOwnerSay("[Take 12/friends] v" + VERSION + " active " + (string)gActive + ", here " + (string)llGetListLength(gGrp)
                + ", free mem " + (string)llGetFreeMemory());
        }
        else if (!gActive) return;
        else if (num == NEXT)
        {
            gSkip = (str == "skip");
            nextShot(1.0);
            gSkip = FALSE;
        }
        else if (num == PAUSE) gPaused = TRUE;
        else if (num == RESUME)
        {
            gPaused = FALSE;
            gShotT = llGetUnixTime();
            if (str == "tp")
            {
                gHaveShot = FALSE;
                gSurveyOK = FALSE;
                gWaitFirst = TRUE;
            }
        }
        else if (num == MOVING) gMoveUntil = llGetUnixTime() + 3;
        else if (num == SPEAKER) speak((key)str);
    }

    listen(integer channel, string name, key id, string msg)
    {
        // local chat: a saved friend who is here speaks
        if (!gActive || id == gOwner || llListFindList(gGrpK, [id]) < 0) return;
        speak(id);
    }

    timer()
    {
        if (!gActive || gPaused) { nextTimer(); return; }
        if (!refreshOwner()) return;
        gTick++;
        if ((gTick % 2) == 0 || gWaitFirst) scan();
        if (gWaitFirst)
        {
            gWaitFirst = FALSE;
            newScene();
            nextShot(1.0);
            return;
        }
        if (!gHaveShot) return;
        integer now = llGetUnixTime();
        integer since = now - gShotT;
        if (llGetListLength(gGrp) > gPresAtShot) gPendEvent = "arrival";
        if (gOSit != gSitAtShot) gPendEvent = "seat";               // you sat down or stood up: a calm re-frame
        if (llGetListLength(gGrp) < gPresAtShot) gPresAtShot = llGetListLength(gGrp);
        if (gPType == 3 && gUsedN > 0 && gLed == 0.0)      // led: your view holds; the next cut follows the group
        {
            glideTick(since);
        }
        else if (now < gMoveUntil && since >= 4 && !gOSit && (!inFrame(gOP, 0.85) || llVecDist(gOP, gOwnerAtShot) > 4.0))
        {
            nextShot(1.0);
            return;
        }
        if (gPendEvent != "" && since >= gMinHold) nextShot(1.0);
    }
}
