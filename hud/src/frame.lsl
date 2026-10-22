// ============================================================================
//  Take 12  -  frame.lsl  (v4.6)  - Frame
//  A held, well-composed view of you, or of you and whoever stands right next to you. Three framings:
//  Full length, Half length, Close. Double-tap = next. The movement keys nudge the camera (core forwards them as
//  NUDGE; you stand still meanwhile): W/S closer/further, A/D round you, E/C up/down, and Shift + A/D (the strafe
//  keys, CONTROL_LEFT/RIGHT) slides you left or right in the picture. The distance follows the viewer's zoom
//  (FOVMSG from core). The lens guide: each framing has a classic portrait lens; STILL tells cinema tips the
//  framing, that lens and yours (35 mm equivalent, 12 / tan(FOV / 2)), and the status line shows them. A script can
//  read the zoom, only you can change it (Ctrl+0 in, Ctrl+8 out, Ctrl+9 back). This script writes no text itself.
//  Maths: docs/FRAME.md, checked in tools/sim/frame_sim.py. The fuller version is kept in lab/frame-full-4.5.0/.
// ============================================================================

string VERSION = "6.0.0";

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer RESUME     = 7305;
integer SHOT       = 7310;
integer NO_SHOT    = 7311;
integer GLIDE      = 7312;
integer ACK        = 7313;
integer NUDGE      = 7317;
integer FOVMSG     = 7318;
integer STILL      = 7381;   // frame -> tips  "<framing>|<recommended mm>|<your mm>"
integer MSG_VER    = 7360;
integer STATUS     = 7370;

// body heights as a fraction of llGetAgentSize().z, from the feet. CALIBRATE in-world (docs/FRAME.md)
// index: 0 top, 1 eyes, 2 shoulders, 3 chest, 4 belt, 5 mid-thigh, 6 feet
list  BODY   = [1.0, 0.935, 0.82, 0.72, 0.56, 0.38, 0.0];
float THIRD  = 0.333333;
float DMIN   = 1.2;          // m  never closer (hair clips the camera, faces distort)
float TOPMAX = 0.9;          // the top of a head never above this line
float MARGIN = 1.3;          // groups: side room, as in the people framing
float FIT    = 1.6;          // fitted for a 16:10 window, so 16:9 has room to spare
float R_NEAR = 3.0;          // m  who stands with you is in the picture
list  NAMES  = ["Full length", "Half length", "Close"];
list  LENSES = [50, 85, 105]; // mm (35 mm equivalent): the classic lens for each framing
float SLIDE  = 0.6;          // Shift + A/D: you at most this far from the centre (screen units, edge = 1)

// you: camera height (fraction), degrees round from the nose, across (x), f1, y1, f2, y2
list PORT = [
    0.50,  15.0, 0.0,   0, 0.86,   6, -0.88,
    0.935, 30.0, 0.333, 1, 0.3333, 4, -1.0,
    0.98,  25.0, 0.2,   1, 0.3333, 3, -1.0
];
list SEAT = [0.62, 0.36, 0.2];   // seated: how far below the eyes each framing cuts (fraction of the height)
// you and the people next to you: camera height (fraction of the mean height), f1, y1, f2, y2
list GRP = [
    0.60,  0, 0.84,   6, -0.86,
    0.80,  1, 0.3333, 5, -1.0,
    0.935, 1, 0.3333, 4, -1.0
];

key     gOwner;
integer gActive;
integer gIdx;                // 0 Full length, 1 Half length, 2 Close
list    gWith;               // who stood with you at the cut (keys)
float   gFov = 1.047198;
float   gSide = 1.0;
float   gNDist = 1.0;        // nudges: distance factor, degrees round, metres up
float   gNAz;
float   gNH;
float   gNX;                 // Shift + A/D: you slid across the picture (+ right)
integer gKeys;               // movement keys held
float   gFovT;               // the zoom changed at: re-frame when it has settled
float   gPhi;                // tilt from the last solve

// ============================================================================
vector dirOf(float a)
{
    return <llCos(a), llSin(a), 0.0>;
}

// ---- the solver ----------------------------------------------------------------
// camera height zc, horizontal distance D, tilt (down +): height z shows at y = tan(atan((z - zc) / D) + tilt) / t.
// Put z1 at y1 and z2 at y2: their angle shrinks as D grows, so D is found by bisection; the tilt goes to gPhi.
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

// the tilt that puts height z at screen y from D away
float tiltFor(float z, float y, float zc, float D, float t)
{
    return llAtan2(y * t, 1.0) - llAtan2(z - zc, D);
}

// where height z shows on screen
float yOf(float z, float zc, float D, float t)
{
    return llTan(llAtan2(z - zc, D) + gPhi) / t;
}

// nothing solid between a and b (avatars do not count), and b inside the region
integer clear(vector a, vector b)
{
    if (b.x < 1.0 || b.x > 255.0 || b.y < 1.0 || b.y > 255.0) return FALSE;
    list r = llCastRay(a, b, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
    return (llList2Integer(r, -1) == 0);
}

// who stands with you right now (within R_NEAR, about your level)
list nearby(vector P)
{
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    list w = [];
    integer i;
    for (i = 0; i < llGetListLength(ids) && llGetListLength(w) < 5; i++)
    {
        key k = llList2Key(ids, i);
        list d = llGetObjectDetails(k, [OBJECT_POS]);
        if (k != gOwner && llGetListLength(d) > 0)
        {
            vector q = llList2Vector(d, 0);
            if (llVecDist(<q.x, q.y, 0.0>, <P.x, P.y, 0.0>) <= R_NEAR && llFabs(q.z - P.z) < 1.5) w += [k];
        }
    }
    return w;
}

// ---- framings ------------------------------------------------------------------
// [cam, focus] for the current framing, or []
list frame()
{
    float t = llTan(gFov * 0.5);
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2) return [];
    vector P = llList2Vector(d, 0);
    vector F = llRot2Fwd(llList2Rot(d, 1));
    float yaw = llAtan2(F.y, F.x);
    if (llGetListLength(gWith)) return group(P, yaw, t);

    vector sz = llGetAgentSize(gOwner);
    float h = sz.z;
    if (h < 0.5) h = 1.9;
    float z0 = P.z - 0.5 * h;                               // feet
    vector E = <P.x, P.y, z0 + llList2Float(BODY, 1) * h>;  // eyes
    integer k = gIdx * 7;
    float zc = z0 + llList2Float(PORT, k) * h + gNH;
    float side = llList2Float(PORT, k + 1) * DEG_TO_RAD;
    float x = llList2Float(PORT, k + 2);
    float y1 = llList2Float(PORT, k + 4);
    float y2 = llList2Float(PORT, k + 6);
    float z1 = z0 + llList2Float(BODY, llList2Integer(PORT, k + 3)) * h;
    float z2 = z0 + llList2Float(BODY, llList2Integer(PORT, k + 5)) * h;
    if (llGetAgentInfo(gOwner) & AGENT_SITTING)
    {
        // seated: the eyes from the sitting estimate, on the third; the cut a set drop below them
        E.z = P.z + 0.25 * h;
        z1 = E.z;
        y1 = THIRD;
        z2 = E.z - llList2Float(SEAT, gIdx) * h;
        y2 = -1.0;
        zc = E.z + (llList2Float(PORT, k) - 0.935) * 0.5 * h + gNH;
    }
    float D = solveD(z1, y1, z2, y2, zc, t);
    if (D < 0.0) return [];
    D = D * gNDist;
    if (gNDist != 1.0) gPhi = tiltFor(z1, y1, zc, D, t);
    if (D < DMIN)
    {
        D = DMIN;                                           // a wide zoom: from DMIN, a little looser
        gPhi = tiltFor(E.z, THIRD, zc, D, t);
        if (gIdx == 0) gPhi = tiltFor(z1, y1, zc, D, t);
    }
    // the side round the nose: the start side, then 15 and 30 degrees either way, then the other side
    list tries = [0.0, 0.2618, -0.2618, 0.5236, -0.5236, -2.0 * gSide * side];
    integer i;
    for (i = 0; i < 6; i++)
    {
        float az = yaw + gSide * side + gNAz * DEG_TO_RAD + llList2Float(tries, i);
        vector cam = <P.x, P.y, zc> + dirOf(az) * D;
        if (clear(E, cam))
        {
            vector V = ZERO_VECTOR - dirOf(az);
            // lead room: you sit on the side away from where you look
            float lk = F * <V.y, -V.x, 0.0>;
            if (lk > 0.1) x = -x;
            else if (lk >= -0.1) x = x * gSide;
            x += gNX;                                       // Shift + A/D: where you asked to be
            V = V * llEuler2Rot(<0.0, 0.0, llAtan2(x * t * FIT, 1.0)>);
            vector foc = cam + V * D;
            foc.z = cam.z - D * llTan(gPhi);
            return [cam, foc];
        }
    }
    return [];
}

// you and the people with you: mixed heights, square-on to the group, side room for the window
list group(vector P, float yaw, float t)
{
    vector ow = llGetAgentSize(gOwner);
    list M = [P];
    list H = [ow.z];
    integer i;
    for (i = 0; i < llGetListLength(gWith); i++)
    {
        key k = llList2Key(gWith, i);
        list d = llGetObjectDetails(k, [OBJECT_POS]);
        if (llGetListLength(d) > 0)
        {
            vector s = llGetAgentSize(k);
            M += [llList2Vector(d, 0)];
            H += [s.z];
        }
    }
    integer n = llGetListLength(M);
    integer k5 = gIdx * 5;
    vector C = ZERO_VECTOR;
    float hm = 0.0;
    float fz = 0.0;
    float top = -1000.0;
    float eyes = 0.0;
    float z2 = 1000.0;
    integer f2 = llList2Integer(GRP, k5 + 3);
    for (i = 0; i < n; i++)
    {
        vector p = llList2Vector(M, i);
        float h = llList2Float(H, i);
        float z0 = p.z - 0.5 * h;
        C += p;
        hm += h;
        fz += z0;
        if (z0 + h > top) top = z0 + h;
        eyes += z0 + llList2Float(BODY, 1) * h;
        float c = z0 + llList2Float(BODY, f2) * h;          // the cut: the lowest of everyone's line
        if (c < z2) z2 = c;
    }
    C = C / (float)n;
    hm = hm / (float)n;
    fz = fz / (float)n;
    eyes = eyes / (float)n;
    float z1 = top;
    if (llList2Integer(GRP, k5 + 1) == 1) z1 = eyes;
    // square-on to the group's long axis, on the side you face
    float best = 0.0;
    vector A = <1.0, 0.0, 0.0>;
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
    if (dirOf(yaw) * Nn < 0.0) Nn = ZERO_VECTOR - Nn;
    float az = llAtan2(Nn.y, Nn.x) + gNAz * DEG_TO_RAD;
    vector u = dirOf(az);
    float zc = fz + llList2Float(GRP, k5) * hm + gNH;
    float D = solveD(z1, llList2Float(GRP, k5 + 2), z2, llList2Float(GRP, k5 + 4), zc, t);
    if (D < 0.0) return [];
    // side room: everyone inside the frame with the margin, nearer people counted wider
    float kk = t * FIT / MARGIN;
    float Dl = 0.0;
    for (i = 0; i < n; i++)
    {
        vector o = llList2Vector(M, i) - C;
        o.z = 0.0;
        float need = (llFabs(o * <-u.y, u.x, 0.0>) + 0.35) / kk + o * u;
        if (need > Dl) Dl = need;
    }
    D = D * gNDist;
    if (Dl > D)
    {
        D = Dl;                                             // the width decides: eyes on the third instead
        gPhi = tiltFor(eyes, THIRD, zc, D, t);
    }
    else if (gNDist != 1.0) gPhi = tiltFor(z1, llList2Float(GRP, k5 + 2), zc, D, t);
    if (D < DMIN) D = DMIN;
    if (yOf(top, zc, D, t) > TOPMAX) gPhi = tiltFor(top, TOPMAX, zc, D, t);     // the tallest head is never cut
    vector EC = <C.x, C.y, eyes>;
    list tries = [0.0, 0.2618, -0.2618, 0.5236, -0.5236];
    for (i = 0; i < 5; i++)
    {
        float a = az + llList2Float(tries, i);
        vector cam = <C.x, C.y, zc> + dirOf(a) * D;
        if (clear(EC, cam))
        {
            vector foc = cam - dirOf(a) * D * llEuler2Rot(<0.0, 0.0, llAtan2(gNX * t * FIT, 1.0)>);
            foc.z = cam.z - D * llTan(gPhi);
            return [cam, foc];
        }
    }
    return [];
}

// ---- the lens guide (shown by cinema tips in the status line) ---------------------
lens()
{
    llMessageLinked(LINK_SET, STILL, llList2String(NAMES, gIdx) + "|" + llList2String(LENSES, gIdx) + "|"
        + (string)llRound(12.0 / llTan(gFov * 0.5)), "");
}

// a new framing (cut: who is with you is looked at again) or the same one re-placed (glide)
shoot(integer cut)
{
    if (cut)
    {
        list d = llGetObjectDetails(gOwner, [OBJECT_POS]);
        if (llGetListLength(d)) gWith = nearby(llList2Vector(d, 0));
    }
    list s = frame();
    if (llGetListLength(s) == 0 && llGetListLength(gWith))
    {
        gWith = [];                                         // no room for the group here: just you
        s = frame();
    }
    if (llGetListLength(s) == 0)
    {
        if (cut) llMessageLinked(LINK_SET, NO_SHOT, "frame", "");   // core covers it with its basic shot
        return;
    }
    string c = llList2String(s, 0) + "|" + llList2String(s, 1);
    if (cut)
    {
        llMessageLinked(LINK_SET, SHOT, c + "|0|" + (string)(20 + gIdx), "");
        lens();
    }
    else llMessageLinked(LINK_SET, GLIDE, c + "|0.35", "");
}

resetNudges()
{
    gNDist = 1.0;
    gNAz = 0.0;
    gNH = 0.0;
    gNX = 0.0;
}

// one step of the keys held (5 per second): W/S closer/further, A/D round, E/C up/down,
// Shift + A/D (Second Life sends them as strafe, CONTROL_LEFT/RIGHT) across the picture
step()
{
    if (gKeys & CONTROL_FWD) gNDist = gNDist * 0.96;
    if (gKeys & CONTROL_BACK) gNDist = gNDist * 1.04;
    if (gKeys & CONTROL_ROT_LEFT) gNAz += 3.0;
    if (gKeys & CONTROL_ROT_RIGHT) gNAz -= 3.0;
    if (gKeys & CONTROL_LEFT) gNX -= 0.02;
    if (gKeys & CONTROL_RIGHT) gNX += 0.02;
    if (gNX > SLIDE) gNX = SLIDE;
    if (gNX < -SLIDE) gNX = -SLIDE;
    if (gKeys & CONTROL_UP) gNH += 0.05;
    if (gKeys & CONTROL_DOWN) gNH -= 0.05;
    if (gNDist < 0.4) gNDist = 0.4;
    if (gNDist > 3.0) gNDist = 3.0;
    if (gNH > 3.0) gNH = 3.0;
    if (gNH < -1.5) gNH = -1.5;
    shoot(FALSE);
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "frame");
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
            gActive = (llList2String(L, 0) == "frame");
            if (!gActive) { llSetTimerEvent(0.0); return; }
            llMessageLinked(LINK_SET, ACK, "frame", "");
            gFov = (float)llList2String(L, 1);
            if (gFov < 0.05) gFov = 1.047198;
            gIdx = 0;
            gKeys = 0;
            gFovT = 0.0;
            resetNudges();
            gSide = 1.0;
            if (llFrand(1.0) < 0.5) gSide = -1.0;
            llSetTimerEvent(0.2);
            shoot(TRUE);
        }
        else if (num == STOP)
        {
            gActive = FALSE;
            gKeys = 0;
            llSetTimerEvent(0.0);
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "frame");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/frame] v" + VERSION + " active " + (string)gActive + ", " + llList2String(NAMES, gIdx)
                + ", with " + (string)llGetListLength(gWith) + ", lens " + (string)llRound(12.0 / llTan(gFov * 0.5)) + " mm, free mem " + (string)llGetFreeMemory());
        else if (!gActive) return;
        else if (num == NEXT)
        {
            if (str == "skip")
            {
                gIdx = (gIdx + 1) % 3;                      // double-tap: the next framing, nudges cleared
                resetNudges();
            }
            shoot(TRUE);
        }
        else if (num == RESUME && str == "tp") shoot(TRUE);
        else if (num == NUDGE)
        {
            gKeys = (integer)str;
            if (gKeys) step();
        }
        else if (num == FOVMSG)
        {
            gFov = (float)str;
            gFovT = llGetTime();
            lens();                                         // the readout follows your zoom at once
        }
    }

    timer()
    {
        if (gKeys) step();
        else if (gFovT > 0.0 && llGetTime() - gFovT > 0.8)
        {
            gFovT = 0.0;                                    // the zoom settled: same framing, new distance
            shoot(FALSE);
        }
    }
}
