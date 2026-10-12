// ============================================================================
//  Cinema HUD  -  cinema_friends.lsl  (v4)  - Friends mode
//  You plus the friends you picked (up to 10, within 30 m) in one composed shot.
//  While everyone stays in the frame the camera glides slowly to keep the group
//  framed; if anyone is out of frame for about 1 s it cuts to a wider shot that
//  holds everyone. Chat cuts: whoever of you speaks gets an over-the-shoulder cut.
//  The friends list and picker menu are in cinema_picker.lsl.
//  Shot types: 3 friends group, 4 speaker, 0 portrait (nobody near).
//  Started only from the menu / chat, never by AFK.
// ============================================================================

string VERSION = "4.0.1";
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
integer MSG_VER    = 7360;
integer STATUS     = 7370;

float K_EYE_STAND = 0.37;
float K_EYE_SIT   = 0.25;
float BODY_R      = 0.35;
float MARGIN      = 1.15;
float STANDOFF    = 0.4;
float R_FR        = 30.0;    // friends further than this are not framed
float MIN_HOLD    = 6.0;
float HOLD        = 25.0;    // s  a fresh angle about this often
float MAX_DIST    = 25.0;    // m  furthest camera from the group
float GLIDE_MIN   = 0.2;     // m  the group moved this far: glide the camera along   // TUNE in-world
integer SPK_COOL  = 10;

list OFFS = [0.0, 0.436332, -0.436332, 0.872665, -0.872665, 1.396263, -1.396263];
list PHI  = [45.0, -45.0, 135.0, -135.0, 180.0, 0.0];

float   gThetaMax;
integer gTrace;
integer gChatOn;
list    gRayOpts;
float   gFov;
float   tanV;
float   tanH;
float   gAlpha;
float   gHalfH;

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
list    gFNames;
vector  gOP;
float   gOY;
float   gOE;
integer gOSit;
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
float   gPdMin;
float   gPEye;
float   gPTh;
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
integer gOut;                // half-second ticks someone has been out of frame
integer gGlides;
integer gSnaps;

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
    if (gTrace) llOwnerSay("[Cinema] " + s);
}

loadCfg()
{
    gThetaMax = (float)cfg("theta_max", "10") * DEG_TO_RAD;
    gTrace    = (integer)cfg("trace", "1");
    gChatOn   = (integer)cfg("chat_cuts", "1");
    gRayOpts  = [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1];
    if ((integer)cfg("phantom", "0")) gRayOpts += [RC_DETECT_PHANTOM, TRUE];
    float aspect = (float)cfg("aspect", "1.778");
    if (aspect < 0.5) aspect = 1.778;
    if (gFov < 0.1) gFov = 1.047198;
    tanV = llTan(gFov * 0.5);
    tanH = tanV * aspect;
    gAlpha = llAtan2(tanH / 3.0, 1.0);
    gHalfH = llAtan2(tanH, 1.0);
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
    if (gIndoor) z = fmin(z, gRoofZ - 0.3);
    return z;
}

float fitDist(float spread, float halfH, float lo, float hi)
{
    return fclamp(fmax((spread + BODY_R) / tanH, halfH / tanV) * MARGIN, lo, hi);
}

planA(integer pair)
{
    gPAxis = ZERO_VECTOR;
    gPCenter = FALSE;
    gPType = 0;
    gPEye = gOE;
    gPFp = <gOP.x, gOP.y, gOE>;
    gPdMin = 2.0;
    gPTh = 0.0;
    if (gOSit) gPTh = 0.0872665;
    vector ax = gNPos - gOP;
    ax.z = 0.0;
    if (pair && gHasN && llVecMag(ax) >= 0.3)
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
        gPType = 1;
        gPd = fitDist(llFabs(ax * <-dc.y, dc.x, 0.0>), 0.9, 2.5, 5.0);
        return;
    }
    integer i = (integer)llFrand(6.0);
    if (llFabs(llList2Float(PHI, i) - gLastPhi) < 0.5) i = (i + 1) % 6;
    gLastPhi = llList2Float(PHI, i);
    gPAz = gOY + gLastPhi * DEG_TO_RAD;
    gPd = fitDist(0.0, 1.3, 2.5, 3.5);
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
    vector V = ZERO_VECTOR - dirOf(az);
    if (!gPCenter)
    {
        // rule of thirds with lead room: you sit on the side opposite to where you look
        float fs = dirOf(gOY) * <V.y, -V.x, 0.0>;
        float sd = gSide;
        if (fs > 0.2) sd = 1.0;
        else if (fs < -0.2) sd = -1.0;
        V = V * llEuler2Rot(<0.0, 0.0, -sd * gAlpha>);
    }
    vector foc = cam + V * de;
    foc.z = cam.z - de * llTan(fclamp(gPTh, 0.0, gThetaMax));
    return [cam, foc];
}

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
        if (de >= fmax(0.6 * gPdMin, 1.2))
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
        if (llGetListLength(v) > 0) return v + [gPType];
        skip = b;
    }
    return [];
}

// is p inside the picture? lateral offset against the frame half-width at p's depth; k = how much of the half-width counts
integer inFrame(vector p, float k)
{
    vector to = p - gCurCam;
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
    gFNames = [];
    list L = llParseString2List(cfg("friends", ""), [";"], []);
    integer i;
    for (i = 0; i < llGetListLength(L); i++)
    {
        list P = llParseString2List(llList2String(L, i), [","], []);
        gFKeys += [(key)llList2String(P, 0)];
        gFNames += [llList2String(P, 1)];
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

// group tableau: you plus the friends that fit within MAX_DIST (the farthest are dropped until it fits)
// mult widens the shot (a snap after someone left the frame)
integer planF(float mult)
{
    integer cnt = llGetListLength(gGrp);
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
        // distance so that everyone fits, counting that those nearer the camera than the centre look wider
        float need = 1.3 / tanV * MARGIN;
        for (i = 0; i < n; i++)
        {
            vector off = llList2Vector(M, i) - C;
            need = fmax(need, (llFabs(off * A) + BODY_R) * MARGIN / tanH + off * Nn);
        }
        need = need * mult;
        if (need <= MAX_DIST || cnt == 1)
        {
            gPEye = C.z + (gOE - gOP.z);
            gPFp = <C.x, C.y, gPEye>;
            gPAz = llAtan2(Nn.y, Nn.x);
            gPd = fclamp(need, 3.0, MAX_DIST);
            gPdMin = 3.0;
            gPAxis = ZERO_VECTOR;
            gPTh = 0.0;
            gPCenter = TRUE;
            gPType = 3;
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
    if (!gSurveyOK || llVecDist(gOP, gSurveyPos) > 2.0) survey();
    list shot = [];
    gUsedN = 0;
    if (ev == "speaker" && gChatOn) shot = speakerShot();
    if (llGetListLength(shot) == 0 && llGetListLength(gGrp) > 0 && planF(mult)) shot = sweep();
    if (llGetListLength(shot) == 0 && !gSweepErr)
    {
        if (llGetListLength(gGrp) == 0 && !gToldAlone)
        {
            gToldAlone = TRUE;
            tsay("friends: none of your saved friends are within " + (string)llRound(R_FR) + " m - showing you until they come");
        }
        gUsedN = 0;
        planA(FALSE);
        shot = sweep();
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
    float hold = HOLD * (0.8 + 0.4 * llFrand(1.0));
    if (type == 4) hold = 10.0;
    llMessageLinked(LINK_SET, SHOT, (string)cam + "|" + (string)foc + "|" + (string)hold + "|" + (string)type, "");
    vector v = foc - cam;
    v.z = 0.0;
    gCurV = llVecNorm(v);
    gCurCam = cam;
    gCurFoc = foc;
    gShotT = llGetUnixTime();
    gHaveShot = TRUE;
    gOwnerAtShot = gOP;
    gOut = 0;
    gCenter = centroid(gUsedN);
    gPresAtShot = llGetListLength(gGrp);
    tsay("friends: " + llList2String(["portrait", "pair", "group", "friends group", "speaker"], type) + " (" + (string)(gUsedN + 1)
        + " in frame), camera " + (string)llRound(llVecDist(cam, gOP)) + " m from you");
}

// every 0.5 s while a friends group shot is on: glide to keep the group framed, snap if someone is lost
glideTick(integer since)
{
    integer all = inFrame(gOP, 0.97);
    integer i;
    for (i = 0; i < gUsedN && i < llGetListLength(gGrp); i++)
    {
        if (!inFrame(llList2Vector(gGrp, i), 0.97)) all = FALSE;
    }
    if (!all)
    {
        gOut++;
        if (gOut >= 2 && since >= 3)
        {
            gSnaps++;
            nextShot(1.3);                          // a wider shot that holds everyone
        }
        return;
    }
    gOut = 0;
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
    gGlides++;
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
        llOwnerSay("[Cinema] friends v" + VERSION + " ready, free memory " + (string)llGetFreeMemory());
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
            gGlides = 0;
            gSnaps = 0;
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
        else if (num == CFG_CHANGED)
        {
            loadCfg();
            chatListen();
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "friends");
        else if (num == STATUS && str == "?")
        {
            llOwnerSay("[Cinema/friends] v" + VERSION + " active " + (string)gActive + ", saved " + (string)llGetListLength(gFKeys) + ", here "
                + (string)llGetListLength(gGrp) + ", glides " + (string)gGlides + ", snaps " + (string)gSnaps + ", free mem " + (string)llGetFreeMemory());
        }
        else if (!gActive) return;
        else if (num == NEXT) nextShot(1.0);
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
        else if (llGetListLength(gGrp) < gPresAtShot) gPresAtShot = llGetListLength(gGrp);
        if (gPType == 3 && gUsedN > 0)
        {
            glideTick(since);
        }
        else if (now < gMoveUntil && since >= 2 && (!inFrame(gOP, 0.85) || llVecDist(gOP, gOwnerAtShot) > 4.0))
        {
            nextShot(1.0);
            return;
        }
        if (gPendEvent != "" && since >= MIN_HOLD) nextShot(1.0);
    }
}
