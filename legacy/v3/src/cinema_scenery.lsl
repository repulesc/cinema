// ============================================================================
//  Cinema HUD  -  cinema_scenery.lsl  (v3)  - the default mode
//  Finds grand, unobstructed views of the place around you and has core cut to
//  them: high drone views looking down over your area, and wide eye-level views
//  along the horizon. People are ignored. The camera stays inside your region
//  and is always placed ABOVE the topmost surface at its spot (never inside a
//  building, outside and above the roof when you are indoors).
//  Shot types: 5 drone, 6 wide.
// ============================================================================

string VERSION = "3.0.0";
string PASS    = "cinema-1.0-build1";

integer START      = 7301;
integer STOP       = 7302;
integer NEXT       = 7303;
integer PAUSE      = 7304;
integer RESUME     = 7305;
integer SHOT       = 7310;
integer NO_SHOT    = 7311;
integer ACK        = 7313;
integer REACH_FAIL = 7314;
integer CFG_CHANGED= 7330;
integer MSG_VER    = 7360;
integer STATUS     = 7370;

float   MIN_DIST   = 20.0;   // m  nearest camera spot
integer N_CAND     = 10;     // candidates per cut (about 2 rays each)

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
    gRayOpts = [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1];
    if ((integer)cfg("phantom", "0")) gRayOpts += [RC_DETECT_PHANTOM, TRUE];
}

tsay(string s)
{
    if (gTrace) llOwnerSay("[Cinema] " + s);
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

// where are we: under a roof? how high is the top of whatever we are in?
context()
{
    list u = ray(gOP + <0.0, 0.0, 1.0>, gOP + <0.0, 0.0, 41.0>);
    gCovered = (llList2Integer(u, 0) == 1);
    gTopZ = surfaceAt(gOP.x, gOP.y, gOP.z + 80.0, gOP.z - 5.0);
    gWater = llWater(ZERO_VECTOR);
    gCtxPos = gOP;
    gCtxOK = TRUE;
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

nextShot()
{
    if (!gActive || gPaused) return;
    list d = llGetObjectDetails(gOwner, [OBJECT_POS]);
    if (llGetListLength(d) == 0) return;               // core covers and asks again
    gOP = llList2Vector(d, 0);
    gErr = FALSE;
    if (!gCtxOK || llVecDist(gOP, gCtxPos) > 10.0) context();
    list s = [];
    if (!gErr) s = findShot(MIN_DIST, 25.0);
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
    vector fl = cam - gOP;
    fl.z = 0.0;
    tsay("scenery: " + llList2String(["drone", "wide"], type - 5) + " view, " + (string)llRound(llVecMag(fl)) + " m away, "
        + (string)llRound(cam.z - gOP.z) + " m above you, hold " + (string)llRound(hold) + " s");
}

// ============================================================================
default
{
    state_entry()
    {
        llOwnerSay("[Cinema] scenery v" + VERSION + " ready, free memory " + (string)llGetFreeMemory());
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
            nextShot();
        }
        else if (num == STOP) gActive = FALSE;
        else if (!gActive)
        {
            if (num == CFG_CHANGED) loadCfg();
            else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "scenery");
            else if (num == STATUS && str == "?") llOwnerSay("[Cinema/scenery] v" + VERSION + " idle, reach " + (string)llRound(gReach) + " m, hold " + (string)llRound(gHold) + " s, free mem " + (string)llGetFreeMemory());
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
            llLinksetDataWriteProtected("cin.reach", (string)llRound(gReach), PASS);
            tsay("your viewer keeps the camera closer than " + (string)llRound(want) + " m - reach is now " + (string)llRound(gReach) + " m");
            nextShot();
        }
        else if (num == CFG_CHANGED) loadCfg();
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "scenery");
        else if (num == STATUS && str == "?")
        {
            llOwnerSay("[Cinema/scenery] v" + VERSION + " active, cuts " + (string)gCuts + ", under a roof " + (string)gCovered
                + ", reach " + (string)llRound(gReach) + " m, hold " + (string)llRound(gHold) + " s, free mem " + (string)llGetFreeMemory());
        }
    }
}
