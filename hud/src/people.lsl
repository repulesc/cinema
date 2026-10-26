// ============================================================================
//  Take 12  -  people.lsl  (v4)  - the optional modes
//  personal: composed static shots of you that follow you as you walk.
//  social:   over-the-shoulder pairs and group tableaux of you and the people
//            around you (portrait of you while nobody is near).
//  Shot types: 0 portrait, 1 pair, 2 group, 4 speaker (chat cuts in Social).
//  Started only from the menu / chat, never by AFK.
// ============================================================================

string VERSION = "7.2.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer MOVING     = 7306;
integer SPEAKER    = 7315;
integer SHOT       = 7310;
integer GLIDE      = 7312;   // people -> core: the dolly when you zoom
integer FOVMSG     = 7318;   // core -> cameras: your lens changed (radians)
integer NO_SHOT    = 7311;
integer ACK        = 7313;
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;

float K_EYE_STAND = 0.37;
float K_EYE_SIT   = 0.25;
float BODY_R      = 0.35;
float MARGIN      = 1.3;     // the outermost person ends about 12 % of the screen width from the edge
float STANDOFF    = 0.4;
float R_INT       = 4.5;     // pair radius
float R_GRP       = 8.0;     // group radius
float gBase;                 // s  how long a shot is held (from Pace)
float gMinHold;              // s  shortest time before an event may cut
integer SPK_COOL   = 30;      // s  the same speaker is not cut to again within this

list OFFS = [0.0, 0.436332, -0.436332, 0.872665, -0.872665, 1.396263, -1.396263];
list PHI  = [45.0, -45.0, 135.0, -135.0, 180.0, 0.0];

float   gThetaMax;
float   gSeatEl;                // seated view: how high above you the camera looks down (0 = off)
integer gTrace;
list    gRayOpts;
float   gFov;
float   tanV;
float   tanH;
float   gAlpha;

key     gOwner;
string  gMode;               // "personal" / "social"
integer gActive;
integer gPaused;
integer gWaitFirst;
integer gScanT;
integer gMoveUntil;
string  gPendEvent;
integer gToldAlone;
integer gChatOn;
integer gChat;               // listen handle
key     gSpeaker;
key     gLastSpk;
integer gLastSpkT;

vector  gOP;
float   gOY;
float   gOE;
integer gOSit;
integer gSitAtShot;
float   gSeatR;                 // extra body radius for a close view of someone lying down
integer gLastClose;          // the last group shot was a close one: the next is a wide one
integer gHasN;
integer gNearCnt;
vector  gNPos;
float   gNEye;
list    gGrp;

float   gRoofZ;
float   gFloorZ;
integer gIndoor;
integer gSurveyOK;
vector  gSurveyPos;

float   gSide;
integer gRev;
float   gLastPhi;
vector  gSceneAnchor;

vector  gPFp;
float   gPAz;
float   gPd;
float   gPEye;
float   gPTh;
float   gPLo;                // nearest and furthest camera for this plan
float   gPHi;
float   gVNeed;              // distance the height of the shot needs
list    gMeas;               // who must be fully in the picture (not the over-the-shoulder foreground)
vector  gPAxis;
integer gPCenter;
integer gPType;

integer gHaveShot;
integer gCurType;
integer gFaceOwner;          // you face the camera in this shot (not the over-the-shoulder foreground)
integer gShotT;
vector  gCurCam;
vector  gCurFoc;             // ... and its focus: a zoom moves the camera along this line
vector  gCurV;
integer gGrpAtShot;
vector  gOwnerAtShot;
integer gSweepErr;
integer gSkip;               // this shot was asked for with "next": it must differ from the one on screen

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
    float r = (float)cfg("crop", "0");                      // a Frame format: compose inside it (a wider one is shorter)
    if (r > aspect) tanV *= aspect / r;
    if (r > 0.0) aspect = r;
    tanH = tanV * fmin(aspect, 1.6 + 9.0 * (r > 0.0));      // the format exactly; without one fitted for 16:10, so 16:9 has room to spare
    gAlpha = llAtan2(tanV * aspect * 0.236, 1.0);           // on a golden line, 38.2 % from a side
}

// [status, distance]: 0 clear (full length), 1 hit, <0 error
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
    gOE = gOP.z + (K_EYE_STAND + (K_EYE_SIT - K_EYE_STAND) * gOSit) * sz.z + (float)cfg("fitz", "0");   // + Fit (fit.lsl)
    list c = llParseString2List(cfg("face", ""), ["|"], []);   // 7.2 Show me (fit.lsl): your face, measured, in your own frame
    if (c != [])
    {
        rotation R = llList2Rot(d, 1);
        vector w = gOP + (vector)llList2String(c, 0) * R;
        f = (vector)llList2String(c, 1) * R;
        gOE = gOE - gOP.z + w.z - (K_EYE_STAND + (K_EYE_SIT - K_EYE_STAND) * gOSit) * sz.z;   // the face, + Fit
        gOP = <w.x, w.y, gOP.z>;
        if (f.x * f.x + f.y * f.y > 0.1) gOY = llAtan2(f.y, f.x);     // the way your face looks
    }
    return TRUE;
}

// people: up to 5 nearest others within R_GRP; the nearest within R_INT for pair shots
scan()
{
    gScanT = llGetUnixTime();
    gHasN = FALSE;
    gNearCnt = 0;
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    list tmp = [];
    integer n = llGetListLength(ids);
    integer i;
    for (i = 0; i < n; i++)
    {
        key k = llList2Key(ids, i);
        list d = llGetObjectDetails(k, [OBJECT_POS]);
        if (k != gOwner && llGetListLength(d) > 0)
        {
            vector p = llList2Vector(d, 0);
            float dist = llVecDist(p, gOP);
            if (dist <= R_GRP) tmp += [dist, k, p];
        }
    }
    tmp = llListSort(tmp, 3, TRUE);
    gGrp = [];
    n = llGetListLength(tmp) / 3;
    for (i = 0; i < n && i < 5; i++)
    {
        vector pp = llList2Vector(tmp, i * 3 + 2);
        gGrp += [pp];
        if (llList2Float(tmp, i * 3) <= R_INT)
        {
            gNearCnt++;
            if (!gHasN)
            {
                gHasN = TRUE;
                gNPos = pp;
                vector nsz = llGetAgentSize(llList2Key(tmp, i * 3 + 1));
                gNEye = pp.z + K_EYE_STAND * nsz.z;
            }
        }
    }
}

// floor and ceiling around you (3 rays)
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

// ============================================================================
//  composition
// ============================================================================
float camZ(float eyeRef, float d)
{
    float z = fmax(eyeRef - d * tanV * 0.236, gFloorZ + 0.35);      // the eyes on the golden line, 38.2 % from the top
    if (gOSit && gSeatEl > 0.0) z = eyeRef + d * llTan(gSeatEl);
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
        vector o = llList2Vector(gMeas, i) - gPFp;
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
    // seated: more often; and the longer your lens (mm = 12 / tan(FOV / 2)), the more often, like a camera operator would
    if (spread >= 3.5 || gLastClose || llFrand(1.0) >= 0.55 + 0.25 * gOSit + fclamp((12.0 / llTan(gFov * 0.5) - 35.0) / 120.0, -0.15, 0.3)) return FALSE;
    gVNeed = 0.75 / tanV * MARGIN;
    gPLo = 1.2;
    gPEye += 0.15;                                      // a little headroom for a taller neighbour
    if (gOSit) gSeatR = 0.45;                           // lying down, a head can be 0.8 m from where the avatar stands
    return TRUE;
}

// the camera hangs above the shot when you are seated, so a picture's distance is the slant: stand that much closer
float seatD(float S)
{
    if (!gOSit || gSeatEl <= 0.0) return S;
    float d = S * llCos(gSeatEl);
    float R = fmax(gRoofZ - 0.3 - gPEye, 0.0);
    if (gIndoor && d * llTan(gSeatEl) > R) d = llSqrt(S * S - R * R);   // a low ceiling caps the rise
    return d;
}

// portrait of you, or (pair = TRUE and someone is close) an over-the-shoulder shot
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
        gLastClose = closeView(llVecMag(ax));
        gPd = fclamp(needAt(gPAz), gPLo, gPHi);
        return;
    }
    integer i = (integer)llFrand(6.0);
    if (llFabs(llList2Float(PHI, i) - gLastPhi) < 0.5) i = (i + 1) % 6;
    gLastPhi = llList2Float(PHI, i);
    gPAz = gOY + gLastPhi * DEG_TO_RAD;
    gPd = fclamp(gVNeed, gPLo, gPHi);
}

// group tableau: camera square-on to the group's long axis, on the side you face
integer planG()
{
    list M = [gOP] + gGrp;
    integer n = llGetListLength(M);
    if (n < 3) return FALSE;
    vector C = ZERO_VECTOR;
    integer i;
    integer j;
    for (i = 0; i < n; i++) C += llList2Vector(M, i);
    C = C / (float)n;
    float best = 0.0;
    vector A = <1.0, 0.0, 0.0>;
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
    gPEye = C.z + (gOE - gOP.z);
    gPFp = <C.x, C.y, gPEye>;
    gPAz = llAtan2(Nn.y, Nn.x);
    gPAxis = ZERO_VECTOR;
    gPTh = 0.0;
    gPCenter = TRUE;
    gPType = 2;
    gMeas = M;
    gVNeed = 1.3 / tanV * MARGIN;
    gPLo = 4.0;
    gPHi = 12.0;
    gLastClose = closeView(best);
    gPd = fclamp(needAt(gPAz), gPLo, gPHi);
    return TRUE;
}

// last resort: just behind your head, looking where you look
list shoulderShot()
{
    vector E = <gOP.x, gOP.y, gOE>;
    vector F0 = dirOf(gOY);
    gSide = -gSide;                                     // the other shoulder each time
    vector cam = E - F0 * 0.9 + <F0.y, -F0.x, 0.0> * 0.25 * gSide;
    list r = ray(E, cam);
    if (llList2Integer(r, 0) != 0) return [];
    return [cam, cam + F0 * 10.0, 0];
}

// one candidate camera: [cam, focus] or []
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
    if (gOSit && gSeatEl > 0.0 && r > de * 0.176) foc.z = cam.z - de * llTan(llAtan2(r, de) + llAtan2(tanV * 0.236, 1.0));
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
        float de = seatD(fmax(needAt(az), gPLo));
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

// ============================================================================
//  the cut
// ============================================================================
newScene()
{
    gSceneAnchor = gOP;
    gRev = FALSE;
    gLastPhi = 999.0;
    gSide = 1.0;
    if (llFrand(1.0) < 0.5) gSide = -1.0;
}

// a speaker: cut to them at the next gMinHold, but not the same speaker twice within SPK_COOL
speak(key who)
{
    if (!gActive || !gChatOn || gMode != "social") return;
    if (who == gLastSpk && llGetUnixTime() - gLastSpkT < SPK_COOL) return;
    gSpeaker = who;
    gPendEvent = "speaker";
}

// local chat is only listened to while Social runs with chat cuts on
chatListen()
{
    if (gChat) llListenRemove(gChat);
    gChat = 0;
    if (gActive && gChatOn && gMode == "social") gChat = llListen(0, "", NULL_KEY, "");
}

// a cut to whoever just spoke: [cam, focus, 4] or []
list speakerShot()
{
    integer rv = gRev;
    if (gSpeaker == gOwner)
    {
        if (!gHasN) return [];
        gRev = TRUE;                                   // over the other person's shoulder, facing you
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

nextShot()
{
    if (!gActive || gPaused) return;
    string ev = gPendEvent;
    gPendEvent = "";
    if (!refreshOwner()) return;                    // core covers and asks again
    gSweepErr = FALSE;
    gSeatR = 0.0;
    if (!gSurveyOK || llVecDist(gOP, gSurveyPos) > 2.0) survey();
    list shot = [];
    if (gMode == "social")
    {
        if (ev == "speaker" && gChatOn) shot = speakerShot();
        if (llGetListLength(shot) == 0 && llGetListLength(gGrp) >= 2 && planG()) shot = sweep();
        if (llGetListLength(shot) == 0 && gHasN && !gSweepErr)
        {
            planA(TRUE);
            shot = sweep();
        }
        if (!gHasN && llGetListLength(gGrp) == 0 && !gToldAlone)
        {
            gToldAlone = TRUE;
            tsay("social: nobody within " + (string)llRound(R_GRP) + " m yet - showing you until someone comes");
        }
    }
    if (llGetListLength(shot) == 0 && !gSweepErr)
    {
        planA(FALSE);
        shot = sweep();
        if (llGetListLength(shot) == 0 && !gSweepErr)
        {
            gVNeed = 0.9 / tanV * MARGIN;               // a tight space: a closer, half-length view of you
            gPLo = 1.5;
            shot = sweep();
        }
    }
    if (llGetListLength(shot) == 0 && !gSweepErr) shot = shoulderShot();
    if (llGetListLength(shot) == 0)
    {
        gHaveShot = FALSE;
        llMessageLinked(LINK_SET, NO_SHOT, "none", "");
        return;
    }
    vector cam = llList2Vector(shot, 0);
    vector foc = llList2Vector(shot, 1);
    integer type = llList2Integer(shot, 2);
    float hold = gBase;
    if (type == 2) hold = 1.2 * gBase;                      // a group tableau is held a little longer
    if (type == 4) hold = fmax(14.0, 0.4 * gBase);          // a speaker cut is short (Calm: 18 s)
    hold = hold * (0.85 + 0.3 * llFrand(1.0));
    llMessageLinked(LINK_SET, SHOT, (string)cam + "|" + (string)foc + "|" + (string)hold + "|" + (string)type, "");
    vector v = foc - cam;
    v.z = 0.0;
    gCurV = llVecNorm(v);
    gCurCam = cam;
    gCurFoc = foc;
    gShotT = llGetUnixTime();
    gHaveShot = TRUE;
    gCurType = type;
    gFaceOwner = (llList2Vector(gMeas, 0) == gOP);
    gOwnerAtShot = gOP;
    gSitAtShot = gOSit;
    gGrpAtShot = llGetListLength(gGrp);
    tsay(gMode + ": " + llList2String(["portrait", "pair", "group", "friends group", "speaker"], type) + ", camera " + (string)llRound(llVecDist(cam, gOP)) + " m from you");
}

// is p inside the picture? lateral offset against the frame half-width at p's depth; k = how much of the half-width counts
integer inFrame(vector p, float k)
{
    vector to = p - gCurCam;
    to.z = 0.0;
    if (llVecMag(to) < 0.1) return TRUE;
    float fwd = to * gCurV;
    return (fwd > 0.3 && llFabs(to.x * gCurV.y - to.y * gCurV.x) <= k * tanH * fwd);
}

// is everyone who should be in the picture still clear of the edges? (not the over-the-shoulder foreground)
integer framed()
{
    list L = [];
    if (gCurType == 2) L = gGrp;
    if (gCurType == 0 || gCurType == 2 || gFaceOwner) L += [gOP];
    else if (gHasN) L += [gNPos];
    integer i;
    for (i = 0; i < llGetListLength(L); i++)
    {
        if (!inFrame(llList2Vector(L, i), 0.8)) return FALSE;
    }
    return TRUE;
}

doScan()
{
    if (!gActive || gPaused || !refreshOwner()) return;
    scan();
    if (gWaitFirst)
    {
        gWaitFirst = FALSE;
        newScene();
        nextShot();
        return;
    }
    if (!gHaveShot) return;
    if (llVecDist(gOP, gSceneAnchor) > 3.0)
    {
        newScene();
        gPendEvent = "scene";
    }
    else if (gMode == "social" && llGetListLength(gGrp) > gGrpAtShot) gPendEvent = "arrival";
    else if (gOSit != gSitAtShot) gPendEvent = "seat";          // you sat down or stood up: a calm re-frame
    else if (!framed()) gPendEvent = "frame";          // someone drifted near the edge: re-frame at the next calm moment
    if (llGetListLength(gGrp) < gGrpAtShot) gGrpAtShot = llGetListLength(gGrp);
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
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "people");
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
            gMode = llList2String(L, 0);
            gActive = (gMode == "personal" || gMode == "social");
            if (!gActive)
            {
                llSetTimerEvent(0.0);
                return;
            }
            llMessageLinked(LINK_SET, ACK, gMode, "");
            gFov = (float)llList2String(L, 1);
            loadCfg();
            chatListen();
            gPaused = FALSE;
            gHaveShot = FALSE;
            gSurveyOK = FALSE;
            gPendEvent = "";
            gMoveUntil = 0;
            gToldAlone = FALSE;
            gWaitFirst = TRUE;
            llSetTimerEvent(1.0);
            doScan();
        }
        else if (num == STOP)
        {
            gActive = FALSE;
            chatListen();
            gHaveShot = FALSE;
            gWaitFirst = FALSE;
            llSetTimerEvent(0.0);
        }
        else if (num == FOVMSG)
        {
            // your lens changed: the same picture, a new perspective - the camera dollies along its line to the focus
            float k = tanV;
            gFov = (float)str;
            loadCfg();
            if (!gActive || !gHaveShot) return;
            vector nc = gCurFoc + (gCurCam - gCurFoc) * (k / tanV);
            if (llVecDist(nc, gOP) > 30.0 || llList2Integer(ray(gCurFoc, nc), 0)) nextShot();   // no room: a new shot for this lens
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
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "people");
        else if (num == STATUS && str == "?")
        {
            llOwnerSay("[Take 12/people] v" + VERSION + " active " + (string)gActive + " (" + gMode + "), people near "
                + (string)llGetListLength(gGrp) + ", free mem " + (string)llGetFreeMemory());
        }
        else if (!gActive) return;
        else if (num == NEXT)
        {
            if (gWaitFirst) doScan();
            else
            {
                gSkip = (str == "skip");
                nextShot();
                gSkip = FALSE;
            }
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
            if (gWaitFirst) doScan();
        }
        else if (num == MOVING) gMoveUntil = llGetUnixTime() + 3;
        else if (num == SPEAKER && gMode == "social") speak((key)str);
    }

    listen(integer channel, string name, key id, string msg)
    {
        if (!gActive || gMode != "social" || id == gOwner || llGetAgentSize(id) == ZERO_VECTOR) return;
        list d = llGetObjectDetails(id, [OBJECT_POS]);
        if (llGetListLength(d) == 0 || !refreshOwner()) return;
        if (llVecDist(llList2Vector(d, 0), gOP) <= R_GRP) speak(id);
    }

    timer()
    {
        if (!gActive || gPaused) return;
        integer now = llGetUnixTime();
        if (now - gScanT >= 5) doScan();
        if (!gHaveShot) return;
        integer since = now - gShotT;
        // you are walking: re-frame when you leave the shot or walk on
        if (now < gMoveUntil && since >= 4 && refreshOwner())
        {
            if (!inFrame(gOP, 0.85) || llVecDist(gOP, gOwnerAtShot) > 4.0)
            {
                nextShot();
                return;
            }
        }
        if (gPendEvent != "" && since >= gMinHold) nextShot();
    }
}
