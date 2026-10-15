// ============================================================================
//  Take 12  -  cinema_photo.lsl  (v4.5)  - Photographer mode
//  Composed, HELD framings of you, a person you pick, the group around you, or the landscape. Five framings
//  per subject (A-E), double-tap = next. The movement keys nudge the camera (core forwards them as NUDGE).
//  The lens is the viewer's field of view: it is read live (FOVMSG from core), the framing is re-solved for it,
//  and the line next to the button shows the framing's lens and whether yours matches.
//  Maths: docs/PHOTOGRAPHER.md, checked in tools/sim/photographer_sim.py.
// ============================================================================

string VERSION = "4.5.0";
string PASS    = "cinema-1.0-build1";

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
integer UI_MENU    = 7321;
integer UI_PHOTO   = 7323;
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;

// body heights as a fraction of llGetAgentSize().z, from the feet. CALIBRATE in-world (docs/PHOTOGRAPHER.md)
// index: 0 top, 1 eyes, 2 shoulders, 3 chest, 4 belt, 5 mid-thigh, 6 feet
list  BODY   = [1.0, 0.935, 0.82, 0.72, 0.56, 0.38, 0.0];
float THIRD  = 0.333333;
float DMIN   = 1.2;          // m  never closer (hair clips the camera, faces distort)
float TOPMAX = 0.9;          // the top of a head never above this line
float MARGIN = 1.3;          // groups: side room, as in the people framing
float R_GRP  = 8.0;          // m  the group around you
float R_PICK = 20.0;         // m  the person picker

// portrait: name, lens mm, camera height (fraction), degrees round from the nose, across (x), f1, y1, f2, y2
list PORT = [
    "Environment",        35.0, 0.935, 30.0, 0.236, 0, 0.18,   6, -0.72,
    "Full length",        50.0, 0.50,  15.0, 0.0,   0, 0.86,   6, -0.88,
    "Three-quarter",      50.0, 0.80,  30.0, 0.333, 1, 0.3333, 5, -1.0,
    "Half body",          85.0, 0.935, 30.0, 0.333, 1, 0.3333, 4, -1.0,
    "Head and shoulders", 85.0, 0.98,  25.0, 0.2,   1, 0.3333, 3, -1.0
];
// seated portraits: how far below the eyes each framing cuts (fraction of the standing height)
list SEAT = [0.75, 0.62, 0.5, 0.36, 0.2];
// group: name, lens mm, camera height (fraction of the mean height), rise (m), f1, y1, f2, y2
list GRP = [
    "Group in the place",  35.0, 0.935, 0.0, 0, 0.25,   6, -0.65,
    "Full group",          50.0, 0.60,  0.0, 0, 0.84,   6, -0.86,
    "Three-quarter group", 50.0, 0.80,  0.0, 1, 0.3333, 5, -1.0,
    "Half-body group",     50.0, 0.935, 0.0, 1, 0.3333, 4, -1.0,
    "From above",          35.0, 1.0,   1.6, 0, 0.45,   6, -0.80
];
// landscape: name, lens mm, rise (m), horizon line (y)
list LAND = [
    "Big sky",          24.0, 0.5,  -0.3333,
    "The land",         24.0, 3.0,   0.3333,
    "You in the place", 35.0, 1.0,   0.3333,
    "High view",        24.0, 12.0,  0.85,
    "Far detail",       85.0, 0.5,   0.3333
];
list FMT_N = ["16:9", "4:3", "3:2"];
list FMT_A = [1.7778, 1.3333, 1.5];

key     gOwner;
integer gActive;
integer gEmoji;
string  gSubj = "you";       // you / pick / group / land
key     gPick;
string  gPickName;
integer gIdx;                // framing 0..4 = A..E
integer gFmt;                // photo shape
float   gFov = 1.047198;
float   gSide = 1.0;         // which side of the nose the camera starts on
float   gNDist = 1.0;        // nudges: distance factor, degrees round, metres up
float   gNAz;
float   gNH;
integer gKeys;               // movement keys held
float   gFovT;               // the lens changed at: re-frame when it has settled
string  gName;               // framing on screen
float   gWantMM;
string  gWarn;               // a short note for the status line
float   gPhi;                // tilt from the last solve
integer gListen;
integer gChan;
integer gMenuT;
string  gPage;
integer gPickPg;
list    gPickK;
list    gPickL;

// ============================================================================
string cfg(string k, string d)
{
    string v = llLinksetDataReadProtected("cin." + k, PASS);
    if (v == "") return d;
    return v;
}

vector dirOf(float a)
{
    return <llCos(a), llSin(a), 0.0>;
}

string lb(string e, string t)
{
    if (gEmoji) return e + " " + t;
    return t;
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

// ---- framings ------------------------------------------------------------------
// [cam, focus] for the current subject and framing, or [] (then gWarn says why)
list frame()
{
    float t = llTan(gFov * 0.5);
    float th = t * llList2Float(FMT_A, gFmt);
    gWarn = "";
    key S = gOwner;
    if (gSubj == "pick") S = gPick;
    list d = llGetObjectDetails(S, [OBJECT_POS, OBJECT_ROT]);
    if (llGetListLength(d) < 2)
    {
        gSubj = "you";                                      // the person left: back to you
        S = gOwner;
        d = llGetObjectDetails(S, [OBJECT_POS, OBJECT_ROT]);
        gWarn = "they left";
        if (llGetListLength(d) < 2) return [];
    }
    vector P = llList2Vector(d, 0);
    vector F = llRot2Fwd(llList2Rot(d, 1));
    float yaw = llAtan2(F.y, F.x);
    vector sz = llGetAgentSize(S);
    float h = sz.z;
    if (h < 0.5) h = 1.9;
    float z0 = P.z - 0.5 * h;                               // feet
    vector E = <P.x, P.y, z0 + llList2Float(BODY, 1) * h>;  // eyes

    if (gSubj == "land") return land(P, yaw, E.z, t, th);
    if (gSubj == "group") return group(P, yaw, t, th);

    integer k = gIdx * 9;
    gName = llList2String(PORT, k);
    gWantMM = llList2Float(PORT, k + 1);
    float zc = z0 + llList2Float(PORT, k + 2) * h + gNH;
    float side = llList2Float(PORT, k + 3) * DEG_TO_RAD;
    float x = llList2Float(PORT, k + 4);
    integer f1 = llList2Integer(PORT, k + 5);
    float y1 = llList2Float(PORT, k + 6);
    integer f2 = llList2Integer(PORT, k + 7);
    float y2 = llList2Float(PORT, k + 8);
    float z1 = z0 + llList2Float(BODY, f1) * h;
    float z2 = z0 + llList2Float(BODY, f2) * h;
    if (llGetAgentInfo(S) & AGENT_SITTING)
    {
        // seated: the eyes from the sitting estimate, on the third; the cut a set drop below them
        E.z = P.z + 0.25 * h;
        z1 = E.z;
        y1 = THIRD;
        z2 = E.z - llList2Float(SEAT, gIdx) * h;
        y2 = -1.0;
        zc = E.z + (llList2Float(PORT, k + 2) - 0.935) * 0.5 * h + gNH;
    }
    float D = solveD(z1, y1, z2, y2, zc, t);
    if (D < 0.0) return [];
    D = D * gNDist;
    if (gNDist != 1.0) gPhi = tiltFor(z1, y1, zc, D, t);
    if (D < DMIN)
    {
        D = DMIN;                                           // too wide a lens for this from DMIN: frame looser
        gPhi = tiltFor(E.z, THIRD, zc, D, t);
        if (f1 == 0) gPhi = tiltFor(z1, y1, zc, D, t);
        gWarn = "lens";
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
            if (i > 0) gWarn = "moved round";
            vector V = ZERO_VECTOR - dirOf(az);
            // lead room: the subject sits on the side away from where they look
            float lk = F * <V.y, -V.x, 0.0>;
            if (lk > 0.1) x = -x;
            else if (lk >= -0.1) x = x * gSide;
            V = V * llEuler2Rot(<0.0, 0.0, llAtan2(x * th, 1.0)>);
            vector foc = cam + V * D;
            foc.z = cam.z - D * llTan(gPhi);
            return [cam, foc];
        }
    }
    gWarn = "no room here";
    return [];
}

// you and the people within R_GRP: mixed heights, square-on to the group, side room from the photo shape
list group(vector P, float yaw, float t, float th)
{
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    list M = [P];
    vector ow = llGetAgentSize(gOwner);
    list H = [ow.z];
    integer i;
    for (i = 0; i < llGetListLength(ids) && llGetListLength(M) < 8; i++)
    {
        key k = llList2Key(ids, i);
        list d = llGetObjectDetails(k, [OBJECT_POS]);
        if (k != gOwner && llGetListLength(d) > 0 && llVecDist(llList2Vector(d, 0), P) <= R_GRP)
        {
            vector s = llGetAgentSize(k);
            M += [llList2Vector(d, 0)];
            H += [s.z];
        }
    }
    integer n = llGetListLength(M);
    integer k9 = gIdx * 8;
    gName = llList2String(GRP, k9);
    gWantMM = llList2Float(GRP, k9 + 1);
    if (n < 2)
    {
        gWarn = "nobody near";
        gSubj = "you";
        return [];
    }
    vector C = ZERO_VECTOR;
    float hm = 0.0;
    float top = -1000.0;
    float eyes = 0.0;
    float feet = 1000.0;
    float fz = 0.0;
    for (i = 0; i < n; i++)
    {
        vector p = llList2Vector(M, i);
        float h = llList2Float(H, i);
        float z0 = p.z - 0.5 * h;
        C += p;
        hm += h;
        fz += z0;
        if (z0 + h > top) top = z0 + h;
        if (z0 < feet) feet = z0;
        eyes += z0 + llList2Float(BODY, 1) * h;
    }
    C = C / (float)n;
    hm = hm / (float)n;
    fz = fz / (float)n;
    eyes = eyes / (float)n;
    // the cut: the lowest of everyone's body line (the shortest person sets it)
    integer f1 = llList2Integer(GRP, k9 + 4);
    integer f2 = llList2Integer(GRP, k9 + 6);
    float z1 = top;
    if (f1 == 1) z1 = eyes;
    float z2 = feet;
    if (f2 != 6)
    {
        z2 = 1000.0;
        for (i = 0; i < n; i++)
        {
            vector q = llList2Vector(M, i);
            float hq = llList2Float(H, i);
            float c = q.z - 0.5 * hq + llList2Float(BODY, f2) * hq;
            if (c < z2) z2 = c;
        }
    }
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
    float zc = fz + llList2Float(GRP, k9 + 2) * hm + llList2Float(GRP, k9 + 3) + gNH;
    float D = solveD(z1, llList2Float(GRP, k9 + 5), z2, llList2Float(GRP, k9 + 7), zc, t);
    if (D < 0.0) return [];
    // side room: everyone inside the photo shape with the margin, nearer people counted wider
    float kk = th / MARGIN;
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
    else if (gNDist != 1.0) gPhi = tiltFor(z1, llList2Float(GRP, k9 + 5), zc, D, t);
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
            if (i > 0) gWarn = "moved round";
            vector foc = cam - dirOf(a) * D;
            foc.z = cam.z - D * llTan(gPhi);
            return [cam, foc];
        }
    }
    gWarn = "no room here";
    return [];
}

// the landscape from where you stand, looking where you face: the horizon placed by the tilt alone
list land(vector P, float yaw, float eyeZ, float t, float th)
{
    integer k = gIdx * 4;
    gName = llList2String(LAND, k);
    gWantMM = llList2Float(LAND, k + 1);
    float rise = llList2Float(LAND, k + 2) + gNH;
    float phi = llAtan2(llList2Float(LAND, k + 3) * t, 1.0);
    vector E = <P.x, P.y, eyeZ>;
    vector V = dirOf(yaw + gNAz * DEG_TO_RAD);
    vector cam;
    if (gIdx == 2)
    {
        // you in the place: from behind and to the side, you small on a third
        float a = yaw + PI - gSide * 0.35 + gNAz * DEG_TO_RAD;
        cam = E + dirOf(a) * (10.0 * gNDist) + <0.0, 0.0, rise>;
        V = ZERO_VECTOR - dirOf(a);
        V = V * llEuler2Rot(<0.0, 0.0, gSide * llAtan2(THIRD * th, 1.0)>);
    }
    else cam = E + V * (1.0 + (gNDist - 1.0) * 20.0) + <0.0, 0.0, rise>;
    if (!clear(E, cam))
    {
        list r = llCastRay(E, cam, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
        if (llList2Integer(r, -1) < 1) return [];
        cam = llList2Vector(r, 1) - llVecNorm(cam - E) * 0.5;      // just short of the roof or wall
        gWarn = "lower here";
    }
    vector foc = cam + V * 20.0;
    foc.z = cam.z - 20.0 * llTan(phi);
    return [cam, foc];
}

// ---- on screen -----------------------------------------------------------------
status()
{
    if (!gActive) { llSetText("", ZERO_VECTOR, 0.0); return; }
    integer now = llRound(12.0 / llTan(gFov * 0.5));
    string lens = (string)llRound(gWantMM) + " mm ";
    if (llFabs(now - gWantMM) <= 0.12 * gWantMM) lens += "✓";
    else if (now < gWantMM) lens += "(now " + (string)now + ") Ctrl+0";
    else lens += "(now " + (string)now + ") Ctrl+8";
    string s = llGetSubString("ABCDE", gIdx, gIdx) + " · " + gName + " · " + lens;
    if (gFmt) s += " · " + llList2String(FMT_N, gFmt);
    if (gWarn == "lens") s += "\nlens too wide for this framing: shown looser";
    else if (gWarn != "") s += "\n" + gWarn;
    llSetText(s, <1.0, 1.0, 1.0>, 0.9);
}

// a new framing (cut) or a re-framing of the same one (glide)
shoot(integer cut)
{
    string was = gSubj;
    list s = frame();
    if (llGetListLength(s) == 0 && gSubj != was)
    {
        string w = gWarn;                                   // the subject fell back to you: frame you, keep the note
        s = frame();
        if (gWarn == "") gWarn = w;
    }
    if (llGetListLength(s) == 0)
    {
        status();                                           // the line says why; core covers a cut with its basic shot
        if (cut) llMessageLinked(LINK_SET, NO_SHOT, "photo", "");
        return;
    }
    string c = llList2String(s, 0) + "|" + llList2String(s, 1);
    if (cut) llMessageLinked(LINK_SET, SHOT, c + "|0|" + (string)(20 + gIdx), "");
    else llMessageLinked(LINK_SET, GLIDE, c + "|0.35", "");
    status();
}

resetNudges()
{
    gNDist = 1.0;
    gNAz = 0.0;
    gNH = 0.0;
}

// one step of the keys held (5 per second): W/S closer/further, A/D round, E/C up/down
step()
{
    if (gKeys & CONTROL_FWD) gNDist = gNDist * 0.96;
    if (gKeys & CONTROL_BACK) gNDist = gNDist * 1.04;
    if (gKeys & (CONTROL_ROT_LEFT | CONTROL_LEFT)) gNAz += 3.0;
    if (gKeys & (CONTROL_ROT_RIGHT | CONTROL_RIGHT)) gNAz -= 3.0;
    if (gKeys & CONTROL_UP) gNH += 0.05;
    if (gKeys & CONTROL_DOWN) gNH -= 0.05;
    if (gNDist < 0.4) gNDist = 0.4;
    if (gNDist > 3.0) gNDist = 3.0;
    if (gNH > 3.0) gNH = 3.0;
    if (gNH < -1.5) gNH = -1.5;
    shoot(FALSE);
}

// ---- menu ----------------------------------------------------------------------
list order(list b)
{
    while (llGetListLength(b) % 3) b += " ";
    list o = [];
    integer i;
    for (i = llGetListLength(b) - 3; i >= 0; i -= 3) o += llList2List(b, i, i + 2);
    return o;
}

closeMenu()
{
    if (gListen) llListenRemove(gListen);
    gListen = 0;
    timerSet();
}

openMenu(string page, string text, list b)
{
    if (gListen) llListenRemove(gListen);
    gPage = page;
    gChan = -(integer)(llFrand(1000000000.0) + 1000.0);
    gListen = llListen(gChan, "", gOwner, "");
    gMenuT = llGetUnixTime();
    timerSet();
    llDialog(gOwner, text, order(b), gChan);
}

timerSet()
{
    if (gActive) llSetTimerEvent(0.2);
    else if (gListen) llSetTimerEvent(5.0);
    else llSetTimerEvent(0.0);
}

string subjName()
{
    if (gSubj == "pick") return gPickName;
    if (gSubj == "group") return "the group around you";
    if (gSubj == "land") return "the landscape";
    return "you";
}

mainPage()
{
    string head = "Photographer";
    if (gEmoji) head = "📸 Photographer";
    string text = head + " · subject: " + subjName() + " · shape: " + llList2String(FMT_N, gFmt)
        + "\nDouble-tap: next framing. Keys: W/S closer/further, A/D round, E/C up/down. Tap: leave.";
    string go = lb("▶", "Start");
    if (gActive) go = lb("⏭", "Next");
    openMenu("page", text, [lb("👤", "You"), lb("🎯", "Pick"), lb("👥", "Group"), lb("🏞", "Land"),
        lb("🖼", llList2String(FMT_N, gFmt)), lb("↺", "Reset"), go, lb("⏹", "Stop"), lb("✖", "Close")]);
}

pickPage(integer pg)
{
    list od = llGetObjectDetails(gOwner, [OBJECT_POS]);
    vector me = llList2Vector(od, 0);
    list ids = llGetAgentList(AGENT_LIST_REGION, []);
    list tmp = [];
    integer i;
    for (i = 0; i < llGetListLength(ids); i++)
    {
        key k = llList2Key(ids, i);
        list d = llGetObjectDetails(k, [OBJECT_POS]);
        if (k != gOwner && llGetListLength(d) > 0)
        {
            float dist = llVecDist(llList2Vector(d, 0), me);
            if (dist <= R_PICK) tmp += [dist, k];
        }
    }
    tmp = llListSort(tmp, 2, TRUE);
    integer n = llGetListLength(tmp) / 2;
    if (pg * 9 >= n) pg = 0;
    gPickPg = pg;
    gPickK = [];
    gPickL = [];
    list b = [];
    for (i = pg * 9; i < n && i < pg * 9 + 9; i++)
    {
        key pk = llList2Key(tmp, i * 2 + 1);
        string nm = llGetSubString(llGetUsername(pk), 0, 21);
        gPickK += [pk];
        gPickL += [nm];
        b += [nm];
    }
    while (llGetListLength(b) < 9) b += " ";
    b += [lb("↩", "Back"), " "];
    if (n > pg * 9 + 9) b += [lb("▶", "More")];
    else b += " ";
    string text = "Who do you want to photograph? (people within " + (string)llRound(R_PICK) + " m)";
    if (n == 0) text += "\nNobody is near you right now.";
    openMenu("pick", text, b);
}

// a new subject or shape: start, or re-frame from A
choose()
{
    gIdx = 0;
    resetNudges();
    if (gActive) shoot(TRUE);
    else llMessageLinked(LINK_SET, CMD, "photographer", "");
}

onChoice(string msg)
{
    if (msg == " ") { closeMenu(); return; }
    if (msg == lb("✖", "Close")) { closeMenu(); return; }
    if (gPage == "pick")
    {
        if (msg == lb("↩", "Back")) mainPage();
        else if (msg == lb("▶", "More")) pickPage(gPickPg + 1);
        else
        {
            integer i = llListFindList(gPickL, [msg]);
            closeMenu();
            if (i < 0) return;
            gPick = llList2Key(gPickK, i);
            gPickName = msg;
            gSubj = "pick";
            choose();
        }
        return;
    }
    if (msg == lb("🎯", "Pick")) { pickPage(0); return; }
    if (msg == lb("🖼", llList2String(FMT_N, gFmt)))
    {
        gFmt = (gFmt + 1) % 3;
        llLinksetDataWriteProtected("cin.ph_fmt", (string)gFmt, PASS);
        if (gActive) shoot(FALSE);
        mainPage();
        return;
    }
    closeMenu();
    if (msg == lb("👤", "You")) { gSubj = "you"; choose(); }
    else if (msg == lb("👥", "Group")) { gSubj = "group"; choose(); }
    else if (msg == lb("🏞", "Land")) { gSubj = "land"; choose(); }
    else if (msg == lb("↺", "Reset")) { resetNudges(); if (gActive) shoot(FALSE); }
    else if (msg == lb("▶", "Start")) llMessageLinked(LINK_SET, CMD, "photographer", "");
    else if (msg == lb("⏭", "Next")) llMessageLinked(LINK_SET, CMD, "next", "");
    else if (msg == lb("⏹", "Stop")) llMessageLinked(LINK_SET, CMD, "stop", "");
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        gEmoji = (cfg("emoji", "1") != "0");
        gFmt = (integer)cfg("ph_fmt", "0") % 3;
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "photo");
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
            gActive = (llList2String(L, 0) == "photographer");
            if (!gActive) { status(); timerSet(); return; }
            llMessageLinked(LINK_SET, ACK, "photographer", "");
            gFov = (float)llList2String(L, 1);
            if (gFov < 0.05) gFov = 1.047198;
            gIdx = 0;
            gKeys = 0;
            gFovT = 0.0;
            resetNudges();
            gSide = 1.0;
            if (llFrand(1.0) < 0.5) gSide = -1.0;
            timerSet();
            shoot(TRUE);
        }
        else if (num == STOP)
        {
            gActive = FALSE;
            gKeys = 0;
            status();
            timerSet();
        }
        else if (num == UI_PHOTO && str == "page") mainPage();
        else if (num == CFG_CHANGED) gEmoji = (cfg("emoji", "1") != "0");
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "photo");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/photo] v" + VERSION + " active " + (string)gActive + ", subject " + gSubj + ", framing "
                + llGetSubString("ABCDE", gIdx, gIdx) + ", lens " + (string)llRound(12.0 / llTan(gFov * 0.5)) + " mm, free mem " + (string)llGetFreeMemory());
        else if (!gActive) return;
        else if (num == NEXT)
        {
            if (str == "skip")
            {
                gIdx = (gIdx + 1) % 5;                      // double-tap: the next framing, nudges cleared
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
            status();
        }
    }

    listen(integer channel, string name, key id, string msg)
    {
        if (id != gOwner) return;
        gMenuT = llGetUnixTime();
        onChoice(msg);
    }

    timer()
    {
        if (gListen && llGetUnixTime() - gMenuT > 60) closeMenu();
        if (!gActive) return;
        if (gKeys) step();
        else if (gFovT > 0.0 && llGetTime() - gFovT > 0.8)
        {
            gFovT = 0.0;                                    // the lens settled: same framing, new distance
            shoot(FALSE);
        }
    }
}
