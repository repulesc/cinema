// ============================================================================
//  Take 12  -  portrait.lsl  (8.0)  - Portrait: you standing, composed
//  Me · Us, Close · Medium · Wide (cin.por "<size 0-2>|<who 0 Me / 1 Us>"; Medium and Me the first time).
//    Close   your head to mid-chest, eyes on the upper third, a little headroom
//    Medium  head to waist (the belt line), eyes on the upper third
//    Wide    full length, the feet about 5 % above the bottom, a little air over the head
//  Me: a soft 3/4, about 30° off your face, at eye level (your eye line, cin.eye, from the first run), you on the
//  third that leaves open space in front of your face. Us: the nearest people within 3 m (at most 3 others): with one,
//  a two-shot from the side, waist up, both near a third, the camera about 20° toward your side (your friend's face
//  more open); with more, everyone in the size you chose, from the open side of the group, the upper third between
//  the eye lines; a seated friend gets the room of one size wider. More than 6 people within 10 m: a crowd, no people
//  cuts (the frame holds). Someone joins (2 s within 3 m) or leaves (3 s gone): one cut.
//  It follows you, then settles: walking, the camera glides along with you; a second after you stop, the same framing
//  again where you are. Turned away for 2 s: the same framing from your new front. A wall: the camera moves in (the
//  size word stays: never a cut to another angle). Your zoom: the same framing (a glide, never a cut).
//  The lit tap: Me the other 3/4 side; the two-shot swaps sides inside the 180° line (a second tap crosses it).
//  Every distance scales with your size. The solver (7.x frame.lsl): docs/ARCHITECTURE.md §5.
// ============================================================================

string VERSION = "8.0.8";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer MOVING     = 7306;
integer SHOT       = 7310;
integer GLIDE      = 7312;
integer ACK        = 7313;
integer FOVMSG     = 7318;
integer CFG_CHANGED= 7330;
integer OPTS       = 7340;
integer OPT        = 7341;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;
integer CROP       = 7390;

float   THIRD  = 0.333;              // the upper third line (screen y, +1 the top edge)
float   DMIN   = 1.0;                // m  never closer (faces distort, hair clips)
float   NEAR   = 3.0;                // m  who stands with you
float   CROWD  = 10.0;               // m  ... and more than 6 people within this: a crowd
list    SIZES  = ["CLOSE", "MEDIUM", "WIDE"];

key     gOwner;
integer gOn;                         // Portrait runs
integer gDebug;                      // /12 debug on: each picture's numbers to you (8.0.4)
string  gHit;                        // what the last ray met
integer gHold;                       // paused (you hold the camera, sat down, watching)
integer gSize = 1;
integer gUs;
float   gSide = 1.0;                 // which 3/4 side (Me); the 20° offset's side (two-shot)
float   gCross = 1.0;                // the two-shot: which side of the 180° line
integer gTaps;                       // lit taps in a row (the second one crosses the line)
float   gTapT;
float   gFov = 1.047198;
float   gT = 0.57735;                // the picture's half-height, as a tangent
float   gTs = 1.0;                   // ... a shape wider than the window is a shorter picture
float   gAsp = 1.778;                // the picture's shape (the bars, else the window)
float   gPhi;                        // the tilt from the last solve
list    gWith;                       // who is in the shot
list    gSeen;                       // [key, first seen] candidates
list    gGone;                       // [key, gone since]
vector  gCam;
vector  gFoc;
vector  gAt;                         // where you stood when it was framed
float   gStillT;
integer gWalk;
float   gAwayT;
float   gFovT;
integer gKeys;
integer gCrowd;                      // the sensor: more than 6 people within 10 m
list    gNearK;                      // ... the nearest within 3 m (at most 3)
integer gWaitUs;                     // Us just started with nobody known yet

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

load()
{
    list c = llParseString2List(cfg("por"), ["|"], []);
    if (c != [])
    {
        gSize = (integer)llList2String(c, 0);
        gUs = (integer)llList2String(c, 1);
    }
    if (gSize < 0 || gSize > 2) gSize = 1;
}

opts()
{
    list st = ["", "", "", "", "", ""];
    st = llListReplaceList(st, ["lit"], gSize, gSize);
    st = llListReplaceList(st, ["lit"], 4 + gUs, 4 + gUs);
    llMessageLinked(LINK_SET, OPTS, "portrait|CLOSE,MEDIUM,WIDE,/,ME,US|" + llDumpList2String(st, ","), "");
}

vector dirOf(float a)
{
    return <llCos(a), llSin(a), 0.0>;
}

// ---- the solver (7.x frame.lsl) -----------------------------------------------------------
// camera height zc, horizontal distance D, tilt (down +): height z shows at y = tan(atan((z - zc) / D) + tilt) / t.
// z1 at y1 and z2 at y2: their angle shrinks as D grows, so D is found by bisection; the tilt goes to gPhi.
float solveD(float z1, float y1, float z2, float y2, float zc, float t)
{
    float want = llAtan2(y1 * t, 1.0) - llAtan2(y2 * t, 1.0);
    float lo = 0.05;
    float hi = 400.0;
    if (llAtan2(z1 - zc, hi) - llAtan2(z2 - zc, hi) > want) return -1.0;
    integer i;
    for (i = 0; i < 28; i++)
    {
        float m = (lo + hi) * 0.5;
        if (llAtan2(z1 - zc, m) - llAtan2(z2 - zc, m) > want) lo = m;
        else hi = m;
    }
    hi = (lo + hi) * 0.5;
    gPhi = tiltFor(z1, y1, zc, hi, t);
    return hi;
}

float tiltFor(float z, float y, float zc, float D, float t)
{
    return llAtan2(y * t, 1.0) - llAtan2(z - zc, D);
}

float yOf(float z, float zc, float D, float t)
{
    return llTan(llAtan2(z - zc, D) + gPhi) / t;
}

// how far a camera may go from a to b: the distance to a wall (avatars do not count), 0.3 m short; or the full length
float room(vector a, vector b)
{
    if (b.x < 1.0 || b.x > 255.0 || b.y < 1.0 || b.y > 255.0) return 0.0;
    list r = llCastRay(a, b, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
    gHit = "";
    if (llList2Integer(r, -1) <= 0) return llVecDist(a, b);
    gHit = llKey2Name(llList2Key(r, 0));
    if (llList2Key(r, 0) == NULL_KEY) gHit = "land";
    return llVecDist(a, llList2Vector(r, 1)) - 0.3;
}

// your eye line: a fraction of your height (the first run measures it), from your feet
float eyeFrac()
{
    float e = (float)cfg("eye");
    if (e < 0.5 || e > 1.5) e = 0.935;                  // above 1.0 too: a mesh body or hover height puts the eyes there
    return e;
}

// ---- who is with you ------------------------------------------------------------------------
// [crowd, the nearest within 3 m (at most 3), ...], from the last sensor sweep (8.0.1: never the whole region's list,
// which in a full club is 100 keys and ran close to this script's memory)
list near()
{
    return [gCrowd] + gNearK;
}

// ---- framing ------------------------------------------------------------------------------------
// [cam, focus] or []
list frame()
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2) return [];
    vector P = llList2Vector(d, 0);
    vector F = llRot2Fwd(llList2Rot(d, 1));
    F.z = 0.0;
    if (llVecMag(F) < 0.01) F = <1.0, 0.0, 0.0>;
    F = llVecNorm(F);
    gAt = P;
    if (gUs && llGetListLength(gWith) == 1) return two(P, F);
    if (gUs && gWith != []) return group(P, F);
    vector sz = llGetAgentSize(gOwner);
    float h = sz.z;
    if (h < 0.3) h = 1.8;
    float z0 = P.z - 0.5 * h;
    float ez = z0 + eyeFrac() * h;
    float top = z0 + h;                                 // your head's top: above the eyes, wherever they are (a hover)
    if (ez + 0.08 * h > top) top = ez + 0.08 * h;
    float z1 = ez;
    float y1 = THIRD;
    float z2 = z0 + llList2Float([0.72, 0.52, 0.0], gSize) * h;
    float y2 = llList2Float([-1.0, -1.0, -0.9], gSize);
    if (gSize == 2) { z1 = top; y1 = 0.85; }
    float D = solveD(z1, y1, z2, y2, ez, gT);
    if (D < 0.0) return [];
    float yaw = llAtan2(F.y, F.x);
    vector E = <P.x, P.y, ez>;
    // lead room: you on a third, off the picture's axis by this angle; the camera stands back by 1 / cos of it so
    // your depth along the axis is still D (the size table holds)
    float x = 0.333;
    if (gSize == 2) x = 0.25;
    float th = llAtan2(x * gT * gAsp, 1.0);
    D = D / llCos(th);
    // a soft 3/4 (30°) on your side; else the other side, 60° either side, or square-on: the first with room for the
    // whole shot (8.0.4: only the two 3/4s were tried, and among bushes the camera ended up 1 m from you); if none has,
    // the roomiest, in as far as it must
    list tries = [gSide, -gSide, 2.0 * gSide, -2.0 * gSide, 0.0];
    integer i;
    float best = -1.0;
    float az;
    string dbg;
    for (i = 0; i < 5 && best < 0.9 * D; i++)
    {
        float a = yaw + llList2Float(tries, i) * 0.5236;
        float r = room(E, E + dirOf(a) * D);
        dbg += " " + (string)llRound(llList2Float(tries, i) * 30.0) + "°:" + llGetSubString((string)r, 0, 3) + gHit;
        if (r > best + 0.5 || best < 0.0)
        {
            best = r;
            az = a;
        }
    }
    float Dc = D;
    if (best < D - 0.05)
    {
        Dc = best;                                      // a wall: in as far as it must (the size word stays)
        if (Dc < DMIN) Dc = DMIN;
        gPhi = tiltFor(ez, THIRD, ez, Dc * llCos(th), gT);
    }
    if (yOf(top, ez, Dc * llCos(th), gT) > 0.92) gPhi = tiltFor(top, 0.92, ez, Dc * llCos(th), gT);   // the head never cut
    if (gDebug) llOwnerSay("[Take 12/portrait] " + llList2String(["close", "medium", "wide"], gSize) + " D " + llGetSubString((string)D, 0, 3)
        + " → " + llGetSubString((string)Dc, 0, 3) + ", tried" + dbg + "; eye " + llGetSubString((string)eyeFrac(), 0, 4) + " of "
        + llGetSubString((string)h, 0, 3) + " m, fov " + llGetSubString((string)gFov, 0, 4) + ", t " + llGetSubString((string)gT, 0, 4)
        + ", shape " + llGetSubString((string)gAsp, 0, 3));
    vector cam = E + dirOf(az) * Dc;
    vector V = ZERO_VECTOR - dirOf(az);
    // the open space in front of your face
    if (F * <V.y, -V.x, 0.0> > 0.0) th = -th;
    V = V * llEuler2Rot(<0.0, 0.0, th>);
    vector foc = cam + V * Dc;
    foc.z = cam.z - Dc * llTan(gPhi);
    return [cam, foc];
}

// a two-shot: from the side, both near a third, the camera 20° toward your side (gSide: a swap mirrors it inside the
// same half; gCross: the other side of the line between you)
list two(vector P, vector F)
{
    key k = llList2Key(gWith, 0);
    list d = llGetObjectDetails(k, [OBJECT_POS]);
    if (d == []) return [];
    vector Q = llList2Vector(d, 0);
    vector so = llGetAgentSize(gOwner);
    vector sf = llGetAgentSize(k);
    vector L = Q - P;
    L.z = 0.0;
    float s = llVecMag(L);
    if (s < 0.2) return [];
    L = L / s;
    vector N = <-L.y, L.x, 0.0>;
    if (F * N < 0.0) N = ZERO_VECTOR - N;               // on the side you face
    N = N * gCross;
    integer sit = (llGetAgentInfo(k) & AGENT_SITTING) != 0;
    integer size = gSize + sit;                          // a seated friend: the room of one size wider
    if (size > 2) size = 2;
    float e = eyeFrac();
    float z0a = P.z - 0.5 * so.z;
    float z0b = Q.z - 0.5 * sf.z;
    float eyes = (z0a + e * so.z + z0b + e * sf.z) * 0.5;      // the upper third between the eye lines
    float top = z0a + so.z;
    if (z0b + sf.z > top) top = z0b + sf.z;
    float cut = z0a + llList2Float([0.72, 0.52, 0.0], size) * so.z;
    float c2 = z0b + llList2Float([0.72, 0.52, 0.0], size) * sf.z;
    if (c2 < cut) cut = c2;
    float z1 = eyes;
    float y1 = THIRD;
    if (size == 2) { z1 = top; y1 = 0.85; }
    float D = solveD(z1, y1, cut, llList2Float([-1.0, -1.0, -0.9], size), eyes, gT);
    if (D < 0.0) return [];
    // both near a third across: half the spacing at a third of the half-width
    float Dw = 1.5 * (s * 0.5 + 0.2) / (gT * gAsp);
    if (Dw > D)
    {
        D = Dw;
        gPhi = tiltFor(eyes, THIRD, eyes, D, gT);
    }
    if (yOf(top, eyes, D, gT) > 0.92) gPhi = tiltFor(top, 0.92, eyes, D, gT);   // the taller head never cut
    vector M = (P + Q) * 0.5;
    float tw = 0.349;                                    // 20° toward your side (a swap: toward your friend's)
    if (dirOf(llAtan2(N.y, N.x) + tw) * L > 0.0) tw = -tw;
    float az = llAtan2(N.y, N.x) + gSide * tw;
    vector E = <M.x, M.y, eyes>;
    float r = room(E, E + dirOf(az) * D);
    if (r < 0.8 * D)
    {
        // a wall on this side: the other side of the pair, if it has more room (8.0.6: it moved in, even through it)
        float r2 = room(E, E - dirOf(az) * D);
        if (r2 > r + 0.5) { az += PI; r = r2; }
    }
    float Dc = D;
    if (r < D) Dc = r;
    if (Dc < DMIN) Dc = DMIN;
    vector cam = E + dirOf(az) * Dc;
    vector foc = cam - dirOf(az) * Dc;
    foc.z = cam.z - Dc * llTan(gPhi);
    return [cam, foc];
}

// three or four of you: square-on to the group from its open side, everyone in the chosen size
list group(vector P, vector F)
{
    vector so = llGetAgentSize(gOwner);
    list M = [P];
    list H = [so.z];
    list S = [0];
    integer i;
    for (i = 0; i < llGetListLength(gWith); i++)
    {
        key k = llList2Key(gWith, i);
        list d = llGetObjectDetails(k, [OBJECT_POS]);
        if (d != [])
        {
            vector sz = llGetAgentSize(k);
            M += [llList2Vector(d, 0)];
            H += [sz.z];
            S += [(llGetAgentInfo(k) & AGENT_SITTING) != 0];
        }
    }
    integer n = llGetListLength(M);
    vector C = ZERO_VECTOR;
    float eyes;
    float top = -1000.0;
    float cut = 1000.0;
    integer size = gSize;
    if (llListFindList(S, [1]) >= 0 && size < 2) size++;
    float e = eyeFrac();
    for (i = 0; i < n; i++)
    {
        vector p = llList2Vector(M, i);
        float h = llList2Float(H, i);
        float z0 = p.z - 0.5 * h;
        C += p;
        eyes += z0 + e * h;
        if (z0 + h > top) top = z0 + h;
        float c = z0 + llList2Float([0.72, 0.52, 0.0], size) * h;
        if (c < cut) cut = c;
    }
    C = C / (float)n;
    eyes = eyes / (float)n;
    // the long axis; the camera square-on, on the open side (where you face)
    float best;
    vector A = <1.0, 0.0, 0.0>;
    integer j;
    for (i = 0; i < n; i++)
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
    vector N = <-A.y, A.x, 0.0>;
    if (F * N < 0.0) N = ZERO_VECTOR - N;
    N = N * gCross;
    float az = llAtan2(N.y, N.x) + gSide * 0.17;
    vector u = dirOf(az);
    float z1 = eyes;
    float y1 = THIRD;
    if (size == 2) { z1 = top; y1 = 0.85; }
    float D = solveD(z1, y1, cut, llList2Float([-1.0, -1.0, -0.9], size), eyes, gT);
    if (D < 0.0) return [];
    float kk = gT * gAsp / 1.3;                          // side room: everyone inside, a margin
    for (i = 0; i < n; i++)
    {
        vector o = llList2Vector(M, i) - C;
        o.z = 0.0;
        float need = (llFabs(o * <-u.y, u.x, 0.0>) + 0.35) / kk + o * u;
        if (need > D)
        {
            D = need;
            gPhi = tiltFor(eyes, THIRD, eyes, D, gT);
        }
    }
    if (yOf(top, eyes, D, gT) > 0.92) gPhi = tiltFor(top, 0.92, eyes, D, gT);
    vector E = <C.x, C.y, eyes>;
    float r = room(E, E + u * D);
    if (r < D) D = r;
    if (D < DMIN) D = DMIN;
    vector cam = E + u * D;
    vector foc = cam - u * D;
    foc.z = cam.z - D * llTan(gPhi);
    return [cam, foc];
}

// a new picture: kind cut (you asked) or auto (it decided: the jump-cut rule applies)
shoot(string kind)
{
    list s = frame();
    if (s == [] && gWith != [])
    {
        gWith = [];
        s = frame();
    }
    if (s == []) return;
    gCam = llList2Vector(s, 0);
    gFoc = llList2Vector(s, 1);
    if (kind == "glide") llMessageLinked(LINK_SET, GLIDE, (string)gCam + "|" + (string)gFoc + "|1.0", "");
    else llMessageLinked(LINK_SET, SHOT, (string)gCam + "|" + (string)gFoc + "|" + kind, "");
    gWalk = FALSE;
    gStillT = 0.0;
    gAwayT = 0.0;
}

save()
{
    llLinksetDataWriteProtected("cin.por", (string)gSize + "|" + (string)gUs, PASS);
}

// who is with you, now (Us)
people(float now)
{
    if (!gUs) return;
    list n = near();
    if (llList2Integer(n, 0)) return;                    // a crowd: no people cuts
    n = llList2List(n, 1, 3);
    integer change;
    integer i;
    // someone new near you for 2 s: in
    for (i = 0; i < llGetListLength(n); i++)
    {
        key k = llList2Key(n, i);
        if (llListFindList(gWith, [k]) < 0)
        {
            integer j = llListFindList(gSeen, [k]);
            if (j < 0) gSeen += [k, now];
            else if (now - llList2Float(gSeen, j + 1) >= 2.0) change = TRUE;
        }
    }
    // someone gone for 3 s: out
    for (i = 0; i < llGetListLength(gWith); i++)
    {
        key k = llList2Key(gWith, i);
        if (llListFindList(n, [k]) < 0)
        {
            integer j = llListFindList(gGone, [k]);
            if (j < 0) gGone += [k, now];
            else if (now - llList2Float(gGone, j + 1) >= 3.0) change = TRUE;
        }
        else
        {
            integer j = llListFindList(gGone, [k]);
            if (j >= 0) gGone = llDeleteSubList(gGone, j, j + 1);
        }
    }
    if (change)
    {
        gWith = n;
        gSeen = [];
        gGone = [];
        shoot("auto");
    }
}

start(string why)
{
    gHold = FALSE;
    gWith = [];
    gSide = 1.0;
    gCross = 1.0;
    gWaitUs = FALSE;
    llSensorRemove();
    if (gUs)
    {
        gWith = llList2List(near(), 1, 3);
        gWaitUs = (gWith == []);                         // the first sweep may bring them: a cut then
        llSensorRepeat("", NULL_KEY, AGENT, CROWD, PI, 0.5);   // 16 at most, nearest first: joins stay near 2 s
    }
    gSeen = [];
    gGone = [];
    shoot("cut");
    llSetTimerEvent(0.25);
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        load();
        // your lens: Second Life answers llGetCameraFOV only with this permission (8.0.5: it was never asked, read 0,
        // and every picture was framed for 60°: at a 38 mm lens 1.8 times too close, the head out of the top)
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "portrait");
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
            gOn = (llList2String(L, 0) == "portrait");
            if (!gOn) { llSetTimerEvent(0.0); return; }
            llMessageLinked(LINK_SET, ACK, "portrait", "");
            load();
            gFov = llGetCameraFOV();
            if (gFov < 0.05) gFov = 1.047198;
            gT = llTan(gFov * 0.5) * gTs;
            gTaps = 0;
            opts();
            start(llList2String(L, 1));
        }
        else if (num == CROP)
        {
            list L = llParseString2List(str, ["|"], []);
            float r = (float)llList2String(L, 0);
            float a = (float)llList2String(L, 1);
            if (a < 0.3) a = 1.778;
            gAsp = a;
            gTs = 1.0;
            if (r > 0.0) { gAsp = r; if (r > a) gTs = a / r; }
            gT = llTan(gFov * 0.5) * gTs;
            if (gOn && !gHold) shoot("glide");
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "portrait");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/portrait] v" + VERSION + " " + llList2String(["off", "on"], gOn) + ", " + llList2String(SIZES, gSize)
                + " · " + llList2String(["Me", "Us"], gUs) + ", with " + (string)llGetListLength(gWith) + ", free mem " + (string)llGetFreeMemory());
        else if (!gOn) return;
        else if (num == STOP)
        {
            gOn = FALSE;
            llSetTimerEvent(0.0);
            llSensorRemove();
        }
        else if (num == PAUSE) gHold = TRUE;
        else if (num == RESUME)
        {
            gHold = FALSE;
            shoot("cut");
        }
        else if (num == NEXT)
        {
            // the lit tap: Me the other 3/4 side; the two-shot a swap inside the line, a second tap crosses it
            if (llGetTime() - gTapT < 6.0 && gTaps > 0 && gUs && gWith != []) gCross = -gCross;
            else gSide = -gSide;
            gTaps++;
            gTapT = llGetTime();
            shoot("cut");
        }
        else if (num == OPT)
        {
            list L = llParseStringKeepNulls(str, ["|"], []);
            string w = llList2String(L, 1);
            integer i = llListFindList(SIZES, [w]);
            if (i >= 0) gSize = i;
            else if (w == "ME" || w == "US")
            {
                gUs = (w == "US");
                start("opt");
            }
            save();
            opts();
            if (i >= 0) shoot("cut");
        }
        else if (num == FOVMSG)
        {
            gFov = (float)str;
            gFovT = llGetTime();
        }
        else if (num == MOVING) gKeys = (integer)str;
        else if (num == CMD && llGetSubString(str, 0, 5) == "debug|") gDebug = (integer)llGetSubString(str, 6, -1);
        else if (num == CFG_CHANGED && (str == "eye" || str == "all")) shoot("glide");
    }

    sensor(integer n)
    {
        vector P = llGetPos();
        gCrowd = (n > 6);
        gNearK = [];
        integer i;
        for (i = 0; i < n && llGetListLength(gNearK) < 3; i++)
        {
            vector q = llDetectedPos(i);
            if (llVecDist(<q.x, q.y, 0.0>, <P.x, P.y, 0.0>) <= NEAR && llFabs(q.z - P.z) < 1.5) gNearK += [llDetectedKey(i)];
        }
        if (gWaitUs && gNearK != [] && gOn && !gHold)
        {
            gWaitUs = FALSE;
            gWith = gNearK;
            shoot("cut");
        }
    }

    no_sensor()
    {
        gCrowd = FALSE;
        gNearK = [];
    }

    timer()
    {
        if (gHold) return;
        float t = llGetTime();
        list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT, OBJECT_VELOCITY]);
        if (llGetListLength(d) < 3) return;
        vector P = llList2Vector(d, 0);
        vector v = llList2Vector(d, 2);
        // walking: the camera comes along; a second after you stop, the same framing where you are
        vector m = P - gAt;
        if (llVecMag(<v.x, v.y, 0.0>) > 0.25 || gKeys)
        {
            gWalk = TRUE;
            gStillT = 0.0;
        }
        if (gWalk)
        {
            if (llVecMag(m) > 0.05)
            {
                gCam += m;
                gFoc += m;
                gAt = P;
                llMessageLinked(LINK_SET, GLIDE, (string)gCam + "|" + (string)gFoc + "|0.4", "");
            }
            if (llVecMag(<v.x, v.y, 0.0>) < 0.2 && !gKeys)
            {
                if (gStillT == 0.0) gStillT = t;
                else if (t - gStillT > 1.0) shoot("glide");
            }
            return;
        }
        // your zoom settled: the same framing through it
        if (gFovT > 0.0 && t - gFovT > 0.8)
        {
            gFovT = 0.0;
            gT = llTan(gFov * 0.5) * gTs;
            shoot("glide");
        }
        // turned away for 2 s: the same framing from your new front
        vector F = llRot2Fwd(llList2Rot(d, 1));
        vector toCam = gCam - P;
        toCam.z = 0.0;
        if (llVecMag(toCam) > 0.1 && F * llVecNorm(toCam) < -0.2 && (!gUs || gWith == []))
        {
            if (gAwayT == 0.0) gAwayT = t;
            else if (t - gAwayT > 2.0) shoot("auto");
        }
        else gAwayT = 0.0;
        people(llGetTime());
    }
}
