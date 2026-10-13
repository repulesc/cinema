// ============================================================================
//  Take 12  -  cinema_scenery.lsl  (v4)  - the default mode
//  Finds grand, unobstructed views of the place around you and has core cut to
//  them: high drone views looking down over your area, and wide eye-level views
//  along the horizon. People are ignored. The camera stays inside your region
//  and is always placed ABOVE the topmost surface at its spot (never inside a
//  building). Enclosed in the sky (a skybox)? It stays inside the room instead:
//  corner wides, room-centre views, you small in the room. Saved favourite spots
//  are mixed in. Shot types: 5 drone, 6 wide, 7 favourite, 10 room corner,
//  11 room centre, 12 room "you small".
// ============================================================================

string VERSION = "4.3.0";
string PASS    = "cinema-1.0-build1";
integer LITE    = 0;                  // the Lite build (tools/build_lite.py) sets this to 1: outdoor views only, no favourites

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer SHOT       = 7310;
integer NO_SHOT    = 7311;
integer ACK        = 7313;
integer REACH_FAIL = 7314;
integer FAV        = 7316;
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;

float   MIN_DIST   = 20.0;   // m  nearest camera spot
integer N_CAND     = 10;     // candidates per cut (about 2 rays each)
integer N_ROOM     = 5;      // room-view candidates per cut (about 7 rays each)
list    CLEAR_DIRS = [<1.0, 0.0, 0.0>, <-1.0, 0.0, 0.0>, <0.0, 1.0, 0.0>, <0.0, -1.0, 0.0>, <0.0, 0.0, 1.0>];

float   gHold;               // s  average hold
float   gReach;              // m  furthest camera spot (learned)
integer gTrace;
list    gRayOpts;

key     gOwner;
integer gActive;
integer gPaused;
integer gErr;
vector  gOP;                 // owner position
float   gTopZ;               // topmost surface above/at the owner (roof top when covered)
integer gCovered;            // owner is under a roof
float   gWater;
integer gCtxOK;
vector  gCtxPos;
list    gLastAz;             // azimuths of the last two shots
integer gLastType;
integer gCuts;
integer gReachOk;            // cuts since the last REACH_FAIL
string  gLastFav;
string  gIndoors;            // auto / inside / outside
integer gEnclosed;           // roof and walls around you
integer gInside;             // stay inside the room
float   gFloorZ;
float   gCeilZ;
float   gSpan;               // the longest wall distance
float   gRoomZc;             // height of corner views
vector  gCent;               // centre of the room (from the wall hits)
list    gWallD;              // 8 wall distances, every 45 degrees from +x
list    gWallP;              // the 8 wall hit points
list    gOrd;                // wall indices, longest first
list    gDiag;               // the two longest diagonal wall indices
integer gInsideFails;
integer gToldRoom;

// ============================================================================
string cfg(string k, string d)
{
    string v = llLinksetDataReadProtected("cin." + k, PASS);
    if (v == "") return d;
    return v;
}

loadCfg()
{
    gHold  = (float)cfg("hold", "60");
    gReach = (float)cfg("reach", "100");
    if (gReach < MIN_DIST) gReach = MIN_DIST;
    gTrace = (integer)cfg("trace", "1");
    gIndoors = cfg("indoors", "auto");
    gReachOk = (integer)cfg("reach_ok", "0");
    gCtxOK = FALSE;
    gRayOpts = [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1];
    if ((integer)cfg("phantom", "0")) gRayOpts += [RC_DETECT_PHANTOM, TRUE];
}

tsay(string s)
{
    if (gTrace) llOwnerSay("[Take 12] " + s);
}

float clampf(float v, float lo, float hi)
{
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

vector dirOf(float a)
{
    return <llCos(a), llSin(a), 0.0>;
}

// smallest angle between az and the last shots' directions, as 0..1 (90 deg or more = 1)
float novelty(float az)
{
    integer n = llGetListLength(gLastAz);
    if (n == 0) return 1.0;
    float m = PI;
    integer i;
    for (i = 0; i < n; i++)
    {
        float d = az - llList2Float(gLastAz, i);
        while (d > PI) d -= TWO_PI;
        while (d < -PI) d += TWO_PI;
        if (llFabs(d) < m) m = llFabs(d);
    }
    return clampf(m / PI_BY_TWO, 0.0, 1.0);
}

// [status, distance]: 0 clear (full length), 1 hit, <0 error (sets gErr)
list ray(vector a, vector b)
{
    list r = llCastRay(a, b, gRayOpts);
    integer st = llList2Integer(r, -1);
    if (st < 0)
    {
        gErr = TRUE;
        return [st, 0.0];
    }
    if (st == 0) return [0, llVecDist(a, b)];
    return [1, llVecDist(a, llList2Vector(r, 1))];
}

// topmost surface at (x, y): a ray straight down from zTop; zBottom if nothing is hit
float surfaceAt(float x, float y, float zTop, float zBottom)
{
    list r = ray(<x, y, zTop>, <x, y, zBottom>);
    if (llList2Integer(r, 0) != 1) return zBottom;
    return zTop - llList2Float(r, 1);
}

// where are we: under a roof? how high is the top of whatever we are in? a room?
context()
{
    vector E = <gOP.x, gOP.y, gOP.z + 0.6>;
    list u = ray(gOP + <0.0, 0.0, 1.0>, gOP + <0.0, 0.0, 41.0>);
    gCovered = (llList2Integer(u, 0) == 1);
    gCeilZ = gOP.z + 1.0 + llList2Float(u, 1);
    gTopZ = surfaceAt(gOP.x, gOP.y, gOP.z + 80.0, gOP.z - 5.0);
    gWater = llWater(ZERO_VECTOR);
    gCtxPos = gOP;
    gCtxOK = TRUE;
    // the room: 8 walls around you and the floor under you
    gWallD = [];
    gWallP = [];
    integer nHit = 0;
    integer i;
    for (i = 0; i < 8; i++)
    {
        vector dv = dirOf(i * 0.785398);
        list r = ray(E, E + dv * 60.0);
        float d = llList2Float(r, 1);
        if (llList2Integer(r, 0) == 1) nHit++;
        gWallD += [d];
        gWallP += [<E.x + dv.x * d, E.y + dv.y * d, E.z>];
    }
    list fd = ray(<gOP.x, gOP.y, gOP.z + 0.3>, <gOP.x, gOP.y, gOP.z - 30.0>);
    integer floorless = (llList2Integer(fd, 0) == 0);
    gFloorZ = gOP.z + 0.3 - llList2Float(fd, 1);
    if (floorless) gFloorZ = gOP.z - 1.0;
    gEnclosed = (gCovered && nHit >= 6);
    integer sky = (floorless || gOP.z - llGround(ZERO_VECTOR) > 50.0);
    gInside = (gEnclosed && sky);
    if (gIndoors == "inside") gInside = gEnclosed;
    else if (gIndoors == "outside") gInside = FALSE;
    if (LITE) gInside = FALSE;
    gSpan = 0.0;
    gCent = ZERO_VECTOR;
    list ord = [];
    for (i = 0; i < 8; i++)
    {
        float wd = llList2Float(gWallD, i);
        if (wd > gSpan) gSpan = wd;
        gCent += llList2Vector(gWallP, i) / 8.0;
        ord += [wd, i];
    }
    ord = llListSort(ord, 2, FALSE);
    gOrd = [];
    gDiag = [];
    for (i = 0; i < 8; i++)
    {
        integer wi = llList2Integer(ord, i * 2 + 1);
        gOrd += [wi];
        if ((wi % 2) == 1 && llGetListLength(gDiag) < 2) gDiag += [wi];
    }
    gRoomZc = clampf(gCeilZ - 0.6, gFloorZ + 1.2, gFloorZ + 6.0);
    gInsideFails = 0;
    string t = "outdoors";
    if (gInside) t = "inside a room (" + (string)nHit + "/8 walls, ceiling " + (string)llRound(gCeilZ - gFloorZ) + " m, span " + (string)llRound(gSpan) + " m)";
    else if (gEnclosed) t = "enclosed on the ground: views from outside, above the roof";
    tsay("scenery: " + t);
}

// one pass over N_CAND candidate spots; returns [cam, focus, type, az] of the best or []
list findShot(float minD, float clearMin)
{
    list best = [];
    float bestS = -1000.0;
    float base = llFrand(TWO_PI);
    integer i;
    for (i = 0; i < N_CAND; i++)
    {
        float az = base + i * 0.628319;                     // 36 degrees apart
        float nov = novelty(az);
        if (nov >= 0.44)                                     // at least 40 degrees from the last shots
        {
            float d = minD + llFrand(clampf(gReach - minD, 0.0, 200.0));
            vector c = gOP + dirOf(az) * d;
            c.x = clampf(c.x, 3.0, 253.0);                   // stay inside the region
            c.y = clampf(c.y, 3.0, 253.0);
            vector fl = c - gOP;
            fl.z = 0.0;
            if (llVecMag(fl) >= minD * 0.75)
            {
                // ray A: the topmost surface at the spot - the camera goes above it
                float sZ = surfaceAt(c.x, c.y, clampf(gOP.z, gTopZ, 4000.0) + 80.0, gOP.z - 40.0);
                if (gErr) return [];
                if (sZ <= gOP.z - 39.9) sZ = gOP.z - 1.0;     // nothing below (skybox edge, void): use your level
                if (sZ < gWater) sZ = gWater;
                integer type = 6;
                float h = 2.5 + llFrand(1.5);                // wide eye-level view
                if (llFrand(1.0) < 0.6)
                {
                    type = 5;                                // high drone view
                    h = 10.0 + llFrand(20.0);
                }
                c.z = sZ + h;
                if (gCovered && c.z < gTopZ + 5.0) c.z = gTopZ + 5.0;   // outside and above the roof
                vector foc;
                float pitch = 0.0349;                         // 2 degrees down
                float need = clearMin;
                if (type == 5)
                {
                    // look down over a point of your area (you may end up tiny in the frame)
                    vector T = gOP + <llFrand(30.0) - 15.0, llFrand(30.0) - 15.0, -1.0>;
                    vector hv = T - c;
                    hv.z = 0.0;
                    if (llVecMag(hv) < 1.0) hv = -fl;
                    pitch = clampf(llAtan2(c.z - T.z, llVecMag(hv)), 0.1745, 0.6981);   // 10..40 deg
                    foc = c + llVecNorm(hv) * 30.0;
                    foc.z = c.z - 30.0 * llTan(pitch);
                    need = clampf(0.8 * llVecDist(c, T), 8.0, clearMin);
                }
                else
                {
                    // level view back across your area, up to 60 degrees off
                    foc = c + dirOf(az + PI + (llFrand(2.0) - 1.0) * 1.047198) * 30.0;
                    foc.z = c.z - 30.0 * llTan(pitch);
                }
                // ray B: nothing may block the view
                list r = ray(c, c + llVecNorm(foc - c) * 60.0);
                if (gErr) return [];
                float clear = llList2Float(r, 1);
                if (clear >= need)
                {
                    float s = 3.0 * clear / 60.0 + 2.0 * nov + llFrand(0.5);
                    if (type != gLastType) s += 1.0;
                    if (pitch <= 0.4363) s += 0.5;            // horizon in frame
                    if (s > bestS)
                    {
                        bestS = s;
                        best = [c, foc, type, az];
                    }
                }
            }
        }
    }
    return best;
}

// clear view distance of a room camera, or -1 if it fails a check: in the region, same room as you,
// 0.5 m clearance on 5 sides, and a clear view of at least `need` metres
float roomClear(vector c, vector foc, float need)
{
    if (c.x < 1.0 || c.x > 255.0 || c.y < 1.0 || c.y > 255.0) return -1.0;
    vector E = <gOP.x, gOP.y, gOP.z + 0.6>;
    if (llVecDist(E, c) < 0.5) return -1.0;
    list r = ray(E, c);
    if (llList2Integer(r, 0) == 1 && llList2Float(r, 1) < llVecDist(E, c) - 0.2) return -1.0;
    integer i;
    for (i = 0; i < 5; i++)
    {
        r = ray(c, c + llList2Vector(CLEAR_DIRS, i) * 0.5);
        if (llList2Integer(r, 0) != 0) return -1.0;
    }
    r = ray(c, c + llVecNorm(foc - c) * 60.0);
    if (gErr || llList2Float(r, 1) < need) return -1.0;
    return llList2Float(r, 1);
}

// inside a room: [cam, focus, type, az] or []
list roomShot()
{
    list best = [];
    float bestS = -1000.0;
    integer k;
    for (k = 0; k < N_ROOM; k++)
    {
        float roll = llFrand(1.0);
        integer type = 12;
        if (roll < 0.45) type = 10;
        else if (roll < 0.75) type = 11;
        vector c = ZERO_VECTOR;
        vector foc = ZERO_VECTOR;
        float need = llFabs(gSpan * 0.4);
        if (need < 3.0) need = 3.0;
        vector hv;
        if (type == 10)
        {
            // high in a corner, looking across the room through your area
            integer di = llList2Integer(gDiag, (integer)llFrand(2.0));
            float d = llList2Float(gWallD, di);
            if (d >= 3.0)
            {
                c = <gOP.x, gOP.y, gRoomZc> + dirOf(di * 0.785398) * (d - 0.8);
                vector opp = llList2Vector(gWallP, (di + 4) % 8);
                vector T = opp + (<gOP.x, gOP.y, gFloorZ> - opp) / 3.0;
                hv = T - c;
                hv.z = 0.0;
                float pitch = clampf(llAtan2(c.z - gFloorZ, llVecMag(hv)), 0.2618, 0.7854);
                foc = c + llVecNorm(hv) * 30.0;
                foc.z = c.z - 30.0 * llTan(pitch);
            }
        }
        else if (type == 11)
        {
            // eye level near the middle, looking toward one of the far walls
            c = <gCent.x, gCent.y, gFloorZ + 1.7>;
            hv = llList2Vector(gWallP, llList2Integer(gOrd, (integer)llFrand(3.0))) - c;
            hv.z = 0.0;
            if (llVecMag(hv) < 1.0) hv = dirOf(llFrand(TWO_PI));
            foc = c + llVecNorm(hv) * 30.0;
            foc.z = c.z - 30.0 * 0.0349;
        }
        else
        {
            // from the far side of the room: you, small in the space
            integer wi = llList2Integer(gOrd, (integer)llFrand(2.0));
            float d = llList2Float(gWallD, wi);
            if (d >= 6.0)
            {
                c = <gOP.x, gOP.y, gFloorZ + 2.5> + dirOf(wi * 0.785398) * (d - 0.8);
                foc = gOP;
                need = llVecDist(c, foc) - 1.0;
            }
        }
        if (c != ZERO_VECTOR)
        {
            float clear = roomClear(c, foc, need);
            if (gErr) return [];
            if (clear >= 0.0)
            {
                hv = c - gOP;
                hv.z = 0.0;
                float az = llAtan2(hv.y, hv.x);
                float nov = 1.0;
                if (llVecMag(hv) >= 1.0) nov = novelty(az);
                float s = 3.0 * clear / 60.0 + 2.0 * nov + llFrand(0.5);
                if (type != gLastType) s += 1.0;
                if (s > bestS)
                {
                    bestS = s;
                    best = [c, foc, type, az];
                }
            }
        }
    }
    return best;
}

string favKey()
{
    return "cin.fav." + llDumpList2String(llParseString2List(llGetRegionName(), [" "], []), "_");
}

addFav(string spot)
{
    list L = llParseString2List(llLinksetDataReadProtected(favKey(), PASS), [";"], []);
    L += [spot];
    while (llGetListLength(L) > 8) L = llDeleteSubList(L, 0, 0);
    llLinksetDataWriteProtected(favKey(), llDumpList2String(L, ";"), PASS);
    llOwnerSay("[Take 12] ⭐ spot saved (" + (string)llGetListLength(L) + "/8 here)");
}

// one of the saved favourites that is in reach and has a clear view: [cam, focus, 7, az] or []
list favShot()
{
    list L = llParseString2List(llLinksetDataReadProtected(favKey(), PASS), [";"], []);
    integer n = llGetListLength(L);
    integer i0 = (integer)llFrand((float)n);
    integer j;
    for (j = 0; j < n; j++)
    {
        string f = llList2String(L, (i0 + j) % n);
        if (f != gLastFav)
        {
            list P = llParseString2List(f, ["|"], []);
            vector c = (vector)llList2String(P, 0);
            vector foc = (vector)llList2String(P, 1);
            vector h = c - gOP;
            h.z = 0.0;
            if (llVecMag(h) <= gReach + 20.0 && c.x > 1.0 && c.x < 255.0 && c.y > 1.0 && c.y < 255.0 && c != foc)
            {
                list r = ray(c, c + llVecNorm(foc - c) * 10.0);
                if (gErr) return [];
                if (llList2Integer(r, 0) == 0)
                {
                    gLastFav = f;
                    return [c, foc, 7, llAtan2(h.y, h.x)];
                }
            }
        }
    }
    return [];
}

string kindName(integer t)
{
    if (t == 5) return "drone";
    if (t == 6) return "wide";
    if (t == 7) return "favourite";
    if (t == 10) return "room corner";
    if (t == 11) return "room centre";
    return "room, you small";
}

nextShot()
{
    if (!gActive || gPaused) return;
    list d = llGetObjectDetails(gOwner, [OBJECT_POS]);
    if (llGetListLength(d) == 0) return;               // core covers and asks again
    gOP = llList2Vector(d, 0);
    gErr = FALSE;
    if (!gCtxOK || llVecDist(gOP, gCtxPos) > 10.0) context();
    list s = [];
    if (!LITE && !gErr && gCuts % 4 == 3) s = favShot();
    if (llGetListLength(s) == 0 && !gErr && gInside)
    {
        s = roomShot();
        if (llGetListLength(s) == 0)
        {
            gInsideFails++;
            if (gInsideFails == 3 && !gToldRoom)
            {
                gToldRoom = TRUE;
                tsay("scenery: this room is too small for room views, using views from outside");
            }
        }
        else gInsideFails = 0;
    }
    if (llGetListLength(s) == 0 && !gErr) s = findShot(MIN_DIST, 25.0);
    if (llGetListLength(s) == 0 && !gErr) s = findShot(15.0, 12.0);   // relaxed second pass
    if (llGetListLength(s) == 0)
    {
        if (gErr) tsay("scenery: ray error, basic shot for now");
        else tsay("scenery: no clear view found here, basic shot for now");
        gLastAz = [];
        llMessageLinked(LINK_SET, NO_SHOT, "none", "");
        return;
    }
    vector cam = llList2Vector(s, 0);
    integer type = llList2Integer(s, 2);
    float hold = gHold * (0.75 + 0.5 * llFrand(1.0));
    llMessageLinked(LINK_SET, SHOT, (string)cam + "|" + (string)llList2Vector(s, 1) + "|" + (string)hold + "|" + (string)type, "");
    gLastAz = [llList2Float(s, 3)] + llList2List(gLastAz, 0, 0);
    gLastType = type;
    gCuts++;
    if (type >= 5 && type <= 7)
    {
        // reach regrowth: 20 clean cuts in a row and the reach grows by 10 % (up to 100 m)
        gReachOk++;
        if (gReachOk >= 20 && gReach < 100.0)
        {
            gReach = clampf(gReach * 1.1, MIN_DIST, 100.0);
            gReachOk = 0;
            llLinksetDataWriteProtected("cin.reach", (string)llRound(gReach), PASS);
            llLinksetDataWriteProtected("cin.reach_ok", "0", PASS);
        }
    }
    vector fl = cam - gOP;
    fl.z = 0.0;
    tsay("scenery: " + kindName(type) + " view, " + (string)llRound(llVecMag(fl)) + " m away, "
        + (string)llRound(cam.z - gOP.z) + " m above you, hold " + (string)llRound(hold) + " s");
}

// ============================================================================
default
{
    state_entry()
    {
        llOwnerSay("[Take 12] scenery v" + VERSION + " ready, free memory " + (string)llGetFreeMemory());
        gOwner = llGetOwner();
        gLastType = -1;
        loadCfg();
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "scenery");
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
            gActive = (llList2String(llParseString2List(str, ["|"], []), 0) == "scenery");
            if (!gActive) return;
            llMessageLinked(LINK_SET, ACK, "scenery", "");
            loadCfg();
            gPaused = FALSE;
            gCtxOK = FALSE;
            gLastAz = [];
            gLastType = -1;
            gCuts = 0;
            gToldRoom = FALSE;
            nextShot();
        }
        else if (num == STOP) gActive = FALSE;
        else if (!gActive)
        {
            if (num == CFG_CHANGED) loadCfg();
            else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "scenery");
            else if (num == STATUS && str == "?") llOwnerSay("[Take 12/scenery] v" + VERSION + " idle, reach " + (string)llRound(gReach) + " m, hold " + (string)llRound(gHold) + " s, free mem " + (string)llGetFreeMemory());
        }
        else if (num == NEXT) nextShot();
        else if (num == PAUSE) gPaused = TRUE;
        else if (num == RESUME)
        {
            gPaused = FALSE;
            if (str == "tp")
            {
                gCtxOK = FALSE;
                gLastAz = [];
                nextShot();
            }
        }
        else if (num == REACH_FAIL)
        {
            // the viewer did not put the camera that far: learn a shorter reach and cut again
            float want = (float)str;
            gReach = clampf(0.8 * want, MIN_DIST, gReach);
            gReachOk = 0;
            llLinksetDataWriteProtected("cin.reach", (string)llRound(gReach), PASS);
            llLinksetDataWriteProtected("cin.reach_ok", "0", PASS);
            tsay("your viewer keeps the camera closer than " + (string)llRound(want) + " m - reach is now " + (string)llRound(gReach) + " m");
            nextShot();
        }
        else if (num == FAV && !LITE) addFav(str);
        else if (num == CFG_CHANGED) loadCfg();
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "scenery");
        else if (num == STATUS && str == "?")
        {
            llOwnerSay("[Take 12/scenery] v" + VERSION + " active, cuts " + (string)gCuts + ", under a roof " + (string)gCovered + ", inside-mode " + (string)gInside
                + ", reach " + (string)llRound(gReach) + " m, hold " + (string)llRound(gHold) + " s, free mem " + (string)llGetFreeMemory());
        }
    }
}
