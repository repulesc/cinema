// ============================================================================
//  Take 12  -  fixed.lsl  (8.0)  - Fixed: your own framing, kept
//  You frame with Second Life's own camera (Alt-click, orbit, the wheel) and Take 12 keeps it. Nothing is guessed.
//  Standing: View A · View B per place (region + parcel). An empty view hands you your camera ("Frame it, Take 12
//  keeps it."): once you have moved it and it holds still for 1 s, it is kept by itself. A kept view is never replaced
//  silently: Alt-click away from it (core: held) and hold still 1 s, and KEEP NEW lights for 5 s; a tap replaces it,
//  ignoring it was just a look (the lit tap brings the kept view back). Walking off, the shot comes along and settles
//  at the same angle on you where you stop (ray-checked); a zoom dollies the camera so the framing stays.
//  Seated: each piece of furniture keeps a view per spot (where on it you sit, to about half a metre, and your facing),
//  in the furniture's own frame (it may be moved); sitting on the ground, per place and spot (about 2 m). A new spot
//  is a new "Frame it". The least used furniture is forgotten past SEATS. FORGET SEAT forgets this spot (UNDO for
//  3 s); LET GO marks a vehicle (its name and creator in cin.veh) and Take 12 lets go every time you sit on it;
//  TAKE BACK unmarks it. Standing up: core goes back to the shot you had before you sat (this one: the place's view).
//  LSD: view.<place> "<A>~<B>~<ground spots…>", places (LRU), seat.<object> "<spot>~<spot>…", seats (LRU), veh.
//  A view: "<cam>|<focus>|<where you were>|<your facing°>|<lens>" (a seat's in the furniture's frame).
// ============================================================================

string VERSION = "8.5.8";
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
integer FOLLOW     = 7314;
integer ACK        = 7313;
integer FOVMSG     = 7318;
integer CAMSET     = 7325;
integer OPTS       = 7340;
integer OPT        = 7341;
integer NOTE       = 7344;
integer TIP        = 7345;
integer MSG_VER    = 7360;
integer STATUS     = 7370;
integer CMD        = 7371;

integer SEATS      = 48;            // pieces of furniture kept (each up to SPOTS spots)
integer SPOTS      = 4;
integer PLACES     = 20;
integer GSPOTS     = 4;             // ground sits per place

key     gOwner;
integer gOn;
string  gHold;                      // paused: held / watch / eye / veh / tp ... ("" filming)
string  gCtx;                       // "stand", "ground", or the furniture's key
integer gPick;                      // standing: View A 0 / B 1
integer gSpot = -1;                 // seated: the spot's index in its list (-1: none kept)
integer gFree;                      // your own camera: nothing kept here yet
integer gVeh;                       // a marked vehicle: Take 12 let go
vector  gCam;                       // the view on screen
vector  gFoc;
float   gFov;
vector  gAt;                        // where you were when it was placed (walking follows from here)
integer gWalk;
integer gKeys;
float   gStillT;
float   gCtxT;                      // the place where you are changed at
string  gCtxNew;
vector  gSpotL;                     // where you sit (in the furniture's frame; on the ground, in the region)
vector  gRel0;                      // framing: the camera as it was handed to you, in your frame
vector  gDir0;
float   gFreeT;
vector  gLastC;
rotation gLastR;
float   gCamStillT;
vector  gNewC;                      // KEEP NEW: the framing it would keep
vector  gNewF;
float   gNewT;
string  gUndo;                      // FORGET SEAT: the view it forgot, for 3 s
float   gUndoT;

string cfg(string k)
{
    return llLinksetDataReadProtected("cin." + k, PASS);
}

set(string k, string v)
{
    if (v == "") llLinksetDataDeleteProtected("cin." + k, PASS);
    else llLinksetDataWriteProtected("cin." + k, v, PASS);
}

// two decimals is a centimetre: the views stay small in Linkset Data
string f2(float x)
{
    if (x < 0.0) x -= 0.005;
    else x += 0.005;
    string s = (string)x;
    return llGetSubString(s, 0, llSubStringIndex(s, ".") + 2);
}

string v2(vector v)
{
    return "<" + f2(v.x) + "," + f2(v.y) + "," + f2(v.z) + ">";
}

// a key goes to the end of its index; past max the first is forgotten (and returned). Done on the string, never as a
// list: 48 furniture keys as a list (and its copy) is a lot of this script's memory (8.0.1)
string lru(string idx, string item, integer max)
{
    string L = cfg(idx);
    if (L != "") L = "," + L;
    L += ",";                                           // ",a,b," (or "," when empty)
    integer i = llSubStringIndex(L, "," + item + ",");
    if (i >= 0) L = llDeleteSubString(L, i + 1, i + llStringLength(item) + 1);
    L += item + ",";
    integer n = -1;                                     // entries: the commas less one
    string T = L;
    integer k = llSubStringIndex(T, ",");
    while (k >= 0)
    {
        n++;
        T = llDeleteSubString(T, 0, k);
        k = llSubStringIndex(T, ",");
    }
    string out = "";
    if (n > max)
    {
        k = llSubStringIndex(llDeleteSubString(L, 0, 0), ",");
        out = llGetSubString(L, 1, k);
        L = llDeleteSubString(L, 1, k + 1);
    }
    set(idx, llGetSubString(L, 1, -2));
    return out;
}

string place()
{
    vector P = llList2Vector(llGetObjectDetails(gOwner, [OBJECT_POS]), 0);
    string p = (string)llList2Key(llGetParcelDetails(P, [PARCEL_DETAILS_ID]), 0);
    return llDumpList2String(llParseString2List(llGetRegionName(), [" "], []), "_") + "." + llGetSubString(p, 0, 7);
}

float yaw(rotation r)
{
    vector f = llRot2Fwd(r);
    return llAtan2(f.y, f.x) * RAD_TO_DEG;
}

float dyaw(float a, float b)
{
    float d = a - b;
    while (d > 180.0) d -= 360.0;
    while (d < -180.0) d += 360.0;
    return llFabs(d);
}

// where you are: standing, on the ground, or the furniture's key
string ctx()
{
    integer i = llGetAgentInfo(gOwner);
    if (!(i & AGENT_SITTING)) return "stand";
    key r = llList2Key(llGetObjectDetails(gOwner, [OBJECT_ROOT]), 0);
    if (!(i & AGENT_ON_OBJECT) || r == gOwner || r == NULL_KEY) return "ground";
    return (string)r;
}

// the furniture's frame: [pos, rot]
list frameOf()
{
    return llGetObjectDetails((key)gCtx, [OBJECT_POS, OBJECT_ROT]);
}

// the views kept here: the furniture's spots, or the place's "<A>~<B>~<ground…>"
list views()
{
    if (gCtx == "stand" || gCtx == "ground") return llParseStringKeepNulls(cfg("view." + place()), ["~"], []);
    return llParseString2List(cfg("seat." + gCtx), ["~"], []);
}

keepViews(list V)
{
    if (gCtx == "stand" || gCtx == "ground")
    {
        string p = place();
        set("view." + p, llDumpList2String(slots(V), "~"));
        string gone = lru("places", p, PLACES);
        if (gone != "") set("view." + gone, "");
        return;
    }
    set("seat." + gCtx, llDumpList2String(V, "~"));
    if (V == []) return;
    string gone = lru("seats", gCtx, SEATS);
    if (gone != "") set("seat." + gone, "");
}

// this spot's view in the list (the nearest within half a metre and 45°; on the ground 2 m and 60°), or -1
integer spotOf(list V)
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    vector P = llList2Vector(d, 0);
    float y = yaw(llList2Rot(d, 1));
    integer first = 0;
    float near = 0.5;
    float turn = 45.0;
    if (gCtx == "ground") { first = 2; near = 2.0; turn = 60.0; }
    else
    {
        list o = frameOf();
        P = (P - llList2Vector(o, 0)) / llList2Rot(o, 1);
        y -= yaw(llList2Rot(o, 1));
    }
    integer best = -1;
    integer i;
    for (i = first; i < llGetListLength(V); i++)
    {
        list e = llParseString2List(llList2String(V, i), ["|"], []);
        float dd = llVecDist(P, (vector)llList2String(e, 2));
        if (e != [] && dd < near && dyaw(y, (float)llList2String(e, 3)) < turn)
        {
            near = dd;
            best = i;
        }
    }
    return best;
}

// the view to show here: [cam, focus] or [] (nothing kept)
list recall()
{
    list V = views();
    string e;
    if (gCtx == "stand") e = llList2String(V, gPick);
    else
    {
        gSpot = spotOf(V);
        if (gSpot >= 0) e = llList2String(V, gSpot);
    }
    if (e == "") return [];
    list E = llParseString2List(e, ["|"], []);
    vector c = (vector)llList2String(E, 0);
    vector f = (vector)llList2String(E, 1);
    float fv = (float)llList2String(E, 4);
    if (gCtx == "stand")
    {
        // the same angle on you, where you are now: turned with you, ray-checked
        list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
        vector P = llList2Vector(d, 0);
        vector P0 = (vector)llList2String(E, 2);
        rotation t = llEuler2Rot(<0.0, 0.0, (yaw(llList2Rot(d, 1)) - (float)llList2String(E, 3)) * DEG_TO_RAD>);
        c = P + (c - P0) * t;
        f = P + (f - P0) * t;
    }
    else if (gCtx != "ground")
    {
        list o = frameOf();
        c = llList2Vector(o, 0) + c * llList2Rot(o, 1);
        f = llList2Vector(o, 0) + f * llList2Rot(o, 1);
    }
    // kept with another lens: the camera moves along its line so the picture stays
    float now = llGetCameraFOV();
    if (fv > 0.05 && now > 0.05 && llFabs(fv - now) > 0.01) c = f + (c - f) * (llTan(fv * 0.5) / llTan(now * 0.5));
    return [clear(c, f), f];
}

// never behind a wall: the camera stops 0.3 m short of one
vector clear(vector c, vector f)
{
    vector s = f + llVecNorm(c - f) * 0.5;
    list r = llCastRay(s, c, [RC_REJECT_TYPES, RC_REJECT_AGENTS, RC_MAX_HITS, 1]);
    if (llList2Integer(r, -1) > 0) c = llList2Vector(r, 1) + llVecNorm(f - c) * 0.3;
    return c;
}

// what sits in the middle of your frame: the focus (up to 60 m, else 10 m ahead)
vector aim(vector c, rotation r)
{
    vector u = llRot2Fwd(r);
    list h = llCastRay(c, c + u * 60.0, [RC_MAX_HITS, 1]);
    if (llList2Integer(h, -1) > 0) return llList2Vector(h, 1);
    return c + u * 10.0;
}

// keep the framing on screen for where you are (in the slot shown, or a new spot)
keep(vector c, vector f)
{
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT]);
    vector P = llList2Vector(d, 0);
    float y = yaw(llList2Rot(d, 1));
    float fv = llGetCameraFOV();
    list V = views();
    if (gCtx != "stand" && gCtx != "ground")
    {
        list o = frameOf();
        vector O = llList2Vector(o, 0);
        rotation R = llList2Rot(o, 1);
        c = (c - O) / R;
        f = (f - O) / R;
        P = (P - O) / R;
        y -= yaw(R);
    }
    string e = v2(c) + "|" + v2(f) + "|" + v2(P) + "|" + (string)llRound(y) + "|" + llGetSubString((string)fv, 0, 4);
    if (gCtx == "stand") V = llListReplaceList(slots(V), [e], gPick, gPick);
    else if (gSpot >= 0) V = llListReplaceList(V, [e], gSpot, gSpot);
    else
    {
        if (gCtx == "ground")
        {
            V = slots(V) + [e];
            if (llGetListLength(V) > 2 + GSPOTS) V = llDeleteSubList(V, 2, 2);
        }
        else
        {
            V += [e];
            if (llGetListLength(V) > SPOTS) V = llDeleteSubList(V, 0, 0);
        }
        gSpot = llGetListLength(V) - 1;
    }
    keepViews(V);
}

// a place's list always starts with View A and View B (empty or not)
list slots(list V)
{
    while (llGetListLength(V) < 2) V += [""];
    return V;
}

// the strip: the words for where you are
opts()
{
    list w;
    list s;
    if (gNewT > 0.0)
    {
        w = ["KEEP NEW", "/"];
        s = ["accent", ""];
    }
    if (gCtx == "stand")
    {
        w += ["VIEW A", "VIEW B"];
        s += [llList2String(["", "lit"], gPick == 0), llList2String(["", "lit"], gPick == 1)];
    }
    else
    {
        string fs = "";
        if (gSpot < 0) fs = "dim";
        if (gUndo != "") w += ["UNDO"];
        else w += ["FORGET SEAT"];
        if (gUndo != "") s += ["accent"];
        else s += [fs];
        if (gCtx != "ground")
        {
            if (gVeh) { w += ["TAKE BACK"]; s += ["lit"]; }
            else { w += ["LET GO"]; s += [""]; }
        }
    }
    llMessageLinked(LINK_SET, OPTS, "fixed|" + llDumpList2String(w, ",") + "|" + llDumpList2String(s, ","), "");
}

// walking: the viewer's own follow camera from where the shot stands, at its distance and height, on its side (180:
// it keeps whatever side it is on), eased by the viewer every frame. 8.4.3: the shot stepped a locked camera along
// with you a few times a second, and Second Life does not ease a locked camera: walking was choppy
trail(vector P)
{
    vector d = gCam - <P.x, P.y, gFoc.z>;
    float h = llVecMag(<d.x, d.y, 0.0>);
    float D = llVecMag(d);
    if (D < 0.6) D = 0.6;
    if (D > 10.0) D = 10.0;
    llMessageLinked(LINK_SET, FOLLOW, (string)D + "|" + (string)(llAtan2(d.z, h) * RAD_TO_DEG) + "|<0.0, 0.0, "
        + (string)(gFoc.z - P.z) + ">|0.0|0.6|0.3|180", "");
}

// the view for where you are: a cut to it, or your own camera to frame it
show(string kind)
{
    gNewT = 0.0;
    list v = recall();
    gWalk = FALSE;
    gAt = llList2Vector(llGetObjectDetails(gOwner, [OBJECT_POS]), 0);
    if (v == [])
    {
        gFree = TRUE;
        gFreeT = llGetTime();
        gRel0 = ZERO_VECTOR;
        llMessageLinked(LINK_SET, NO_SHOT, "free", "");
        llMessageLinked(LINK_SET, NOTE, "frameit", "");
    }
    else
    {
        gFree = FALSE;
        gCam = llList2Vector(v, 0);
        gFoc = llList2Vector(v, 1);
        gFov = llGetCameraFOV();
        llMessageLinked(LINK_SET, SHOT, (string)gCam + "|" + (string)gFoc + "|" + kind, "");
    }
    opts();
}

// where you sit: in the furniture's frame (it may move, a vehicle), or on the ground in the region
vector spot()
{
    vector P = llList2Vector(llGetObjectDetails(gOwner, [OBJECT_POS]), 0);
    if (gCtx == "stand" || gCtx == "ground") return P;
    list o = frameOf();
    return (P - llList2Vector(o, 0)) / llList2Rot(o, 1);
}

// where you are changed: the view for it (a marked vehicle lets go)
arrive()
{
    gCtx = ctx();
    gCtxNew = gCtx;
    gSpotL = spot();
    gSpot = -1;
    gUndo = "";
    gVeh = FALSE;
    if (gCtx != "stand" && gCtx != "ground" && marked())
    {
        gVeh = TRUE;
        opts();
        if (gHold != "veh") llMessageLinked(LINK_SET, CMD, "letgo|veh", "");
        return;
    }
    show("cut");
}

integer marked()
{
    list d = llGetObjectDetails((key)gCtx, [OBJECT_NAME, OBJECT_CREATOR]);
    return (llSubStringIndex(";" + cfg("veh") + ";", ";" + llList2String(d, 0) + "|" + llList2String(d, 1) + ";") >= 0);
}

// the camera: has it been framed (moved off the camera you were handed) and held still for a second?
integer framed(float t, integer still, float need)
{
    vector c = llGetCameraPos();
    rotation r = llGetCameraRot();
    if (llVecDist(c, gLastC) > 0.03 || llAngleBetween(r, gLastR) > 0.02 || !still) gCamStillT = t;
    gLastC = c;
    gLastR = r;
    return (t - gCamStillT >= need);
}

tick()
{
    float t = llGetTime();
    list d = llGetObjectDetails(gOwner, [OBJECT_POS, OBJECT_ROT, OBJECT_VELOCITY]);
    if (llGetListLength(d) < 3) return;
    vector P = llList2Vector(d, 0);
    rotation R = llList2Rot(d, 1);
    vector v = llList2Vector(d, 2);
    integer still = (llVecMag(<v.x, v.y, 0.0>) < 0.1 && !gKeys);
    // sat down, changed seats or spots on one, stood up: the view for where you are, once it has settled
    string c = ctx();
    if (c == gCtx && c != "stand" && llVecDist(spot(), gSpotL) > 0.5 + 1.5 * (c == "ground"))
    {
        gCtx = "~";                                         // another spot (multi-pose furniture): as a new seat
        gCtxNew = "";
    }
    if (c != gCtx)
    {
        if (c != gCtxNew) { gCtxNew = c; gCtxT = t; }
        else if (t - gCtxT > 1.0)
        {
            if (gHold == "held") llMessageLinked(LINK_SET, CMD, "shot|fixed", "");   // the shot comes back
            else if (gHold == "" || gHold == "veh") arrive();
            return;
        }
    }
    if (gUndoT > 0.0 && t - gUndoT > 3.0)
    {
        gUndoT = 0.0;
        gUndo = "";
        opts();
    }
    if (gNewT > 0.0 && t - gNewT > 5.0)
    {
        gNewT = 0.0;
        opts();
    }
    if (gHold == "held")
    {
        // you took the camera from a kept view: KEEP NEW once it holds still on a new framing
        if (framed(t, still, 1.0) && gNewT == 0.0 && (llVecDist(gLastC, gCam) > 0.3 || llRot2Fwd(gLastR) * llVecNorm(gFoc - gCam) < 0.996))
        {
            if (llVecDist(gLastC, gNewC) > 0.05)
            {
                gNewC = gLastC;
                gNewF = aim(gLastC, gLastR);
                gNewT = t;
                opts();
            }
        }
        return;
    }
    if (gHold != "") return;
    if (gFree)
    {
        // your own camera: what it shows a second after you start is "as handed"; framed away from that and still, kept
        vector rel = (llGetCameraPos() - P) / R;
        vector dir = llRot2Fwd(llGetCameraRot()) / R;
        integer f = framed(t, still, 1.0);
        if (gRel0 == ZERO_VECTOR)
        {
            if (t - gFreeT >= 0.5 && t - gCamStillT >= 0.5) { gRel0 = rel; gDir0 = dir; }   // the camera as handed to you
            return;
        }
        if (f && (llVecDist(rel, gRel0) > 0.4 || dir * gDir0 < 0.985))
        {
            keep(gLastC, aim(gLastC, gLastR));
            llMessageLinked(LINK_SET, TIP, "kept", "");
            show("keep");
        }
        return;
    }
    if (gCtx != "stand") return;
    // walking off: the shot comes along, and a second after you stop it settles at the same angle on you
    vector m = P - gAt;
    if (!still)
    {
        if (!gWalk) trail(P);                               // the follow camera, smooth (8.4.3)
        gWalk = TRUE;
        gStillT = 0.0;
    }
    if (!gWalk) return;
    if (llVecMag(m) > 0.05)
    {
        gCam += m;
        gFoc += m;
        gAt = P;
    }
    if (still)
    {
        if (gStillT == 0.0) gStillT = t;
        else if (t - gStillT > 1.0)
        {
            gStillT = 0.0;
            show("auto");
        }
    }
}

// your lens changed: the same picture. The camera dollies along its line to the focus (stopping short of a wall)
zoom(float nf)
{
    if (gFree || gHold != "" || gCam == ZERO_VECTOR || gFov < 0.05 || nf < 0.05)
    {
        gFov = nf;
        return;
    }
    vector nc = clear(gFoc + (gCam - gFoc) * (llTan(gFov * 0.5) / llTan(nf * 0.5)), gFoc);
    gFov = nf;
    if (llVecDist(nc, gFoc) < 0.3) return;
    gCam = nc;
    llMessageLinked(LINK_SET, GLIDE, (string)gCam + "|" + (string)gFoc + "|1.5", "");
}

option(string w)
{
    if (w == "VIEW A" || w == "VIEW B")
    {
        gPick = (w == "VIEW B");
        if (gHold == "held") llMessageLinked(LINK_SET, CMD, "shot|fixed", "");   // the shot back, at that view
        else show("cut");
    }
    else if (w == "KEEP NEW" && gNewT > 0.0)
    {
        keep(gNewC, gNewF);
        gNewT = 0.0;
        llMessageLinked(LINK_SET, NOTE, "kept", "");
        if (gHold == "held") llMessageLinked(LINK_SET, CMD, "shot|fixed", "");   // core takes it back: the new view
        else show("keep");
    }
    else if (w == "FORGET SEAT" && gSpot >= 0)
    {
        list V = views();
        gUndo = llList2String(V, gSpot);
        V = llDeleteSubList(V, gSpot, gSpot);
        keepViews(V);
        gSpot = -1;
        gUndoT = llGetTime();
        llMessageLinked(LINK_SET, NOTE, "forgot", "");
        if (gHold == "held") llMessageLinked(LINK_SET, CMD, "shot|fixed", "");
        else show("cut");
    }
    else if (w == "UNDO" && gUndo != "")
    {
        list V = views();
        if (gCtx == "ground") V = slots(V);
        V += [gUndo];
        keepViews(V);
        gUndo = "";
        gUndoT = 0.0;
        show("cut");
    }
    else if (w == "LET GO" && gCtx != "stand" && gCtx != "ground")
    {
        list d = llGetObjectDetails((key)gCtx, [OBJECT_NAME, OBJECT_CREATOR]);
        string me = llList2String(d, 0) + "|" + llList2String(d, 1);
        list V = [me] + llParseString2List(cfg("veh"), [";"], []);        // newest first (Settings › Vehicles)
        set("veh", llDumpList2String(llList2List(V, 0, 19), ";"));
        gVeh = TRUE;
        opts();
        llMessageLinked(LINK_SET, NOTE, "letgo", "");
        llMessageLinked(LINK_SET, CMD, "letgo|veh", "");
    }
    else if (w == "TAKE BACK" && gVeh)
    {
        list d = llGetObjectDetails((key)gCtx, [OBJECT_NAME, OBJECT_CREATOR]);
        list V = llParseString2List(cfg("veh"), [";"], []);
        integer i = llListFindList(V, [llList2String(d, 0) + "|" + llList2String(d, 1)]);
        if (i >= 0) V = llDeleteSubList(V, i, i);
        set("veh", llDumpList2String(V, ";"));
        gVeh = FALSE;
        llMessageLinked(LINK_SET, NOTE, "takeback", "");
        llMessageLinked(LINK_SET, CMD, "takeback", "");
        opts();
    }
}

// ============================================================================
default
{
    state_entry()
    {
        gOwner = llGetOwner();
        if (llGetAttached()) llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
        llMessageLinked(LINK_SET, MSG_VER, VERSION, "fixed");
    }

    on_rez(integer p)
    {
        llResetScript();
    }

    attach(key id)
    {
        if (id != NULL_KEY) llRequestPermissions(gOwner, PERMISSION_TRACK_CAMERA);
    }

    changed(integer c)
    {
        if (c & CHANGED_OWNER) llResetScript();
    }

    link_message(integer sender, integer num, string str, key id)
    {
        if (num == START)
        {
            gOn = (llList2String(llParseString2List(str, ["|"], []), 0) == "fixed");
            if (!gOn) { llSetTimerEvent(0.0); return; }
            llMessageLinked(LINK_SET, ACK, "fixed", "");
            gHold = "";
            gNewT = 0.0;
            gKeys = 0;
            arrive();
            llSetTimerEvent(0.5);
        }
        else if (num == MSG_VER && str == "?") llMessageLinked(LINK_SET, MSG_VER, VERSION, "fixed");
        else if (num == STATUS && str == "?")
            llOwnerSay("[Take 12/fixed] v" + VERSION + " " + llList2String(["off", "on"], gOn) + ", " + gCtx + ", "
                + llList2String(["a kept view", "your own camera (frame it)"], gFree) + ", " + (string)((llStringLength(cfg("seats")) + 1) / 37)
                + " seats and " + (string)llGetListLength(llParseString2List(cfg("places"), [","], [])) + " places kept, LSD free "
                + (string)llLinksetDataAvailable() + ", free mem " + (string)llGetFreeMemory());
        else if (!gOn) return;
        else if (num == STOP)
        {
            gOn = FALSE;
            gNewT = 0.0;
            llSetTimerEvent(0.0);
        }
        else if (num == PAUSE)
        {
            gHold = str;
            gNewC = ZERO_VECTOR;
            if (str == "veh") { gVeh = TRUE; opts(); }
        }
        else if (num == RESUME)
        {
            string was = gHold;
            gHold = "";
            if (was == "held" && gCtx == ctx()) show("cut");
            else arrive();
        }
        else if (num == NEXT)
        {
            gNewT = 0.0;                                     // the lit tap: back to the kept view
            show("cut");
        }
        else if (num == OPT) option(llList2String(llParseStringKeepNulls(str, ["|"], []), 1));
        else if (num == CAMSET && str != "-" && llGetSubString(llList2String(llParseString2List(str, ["|"], []), 2), 0, 0) != "-")
        {
            list L = llParseString2List(str, ["|"], []);       // a shot on screen (not your own camera: a negative lag)
            gCam = (vector)llList2String(L, 0);
            gFoc = (vector)llList2String(L, 1);
            gFov = (float)llList2String(L, 3);
        }
        else if (num == FOVMSG) zoom((float)str);
        else if (num == MOVING) gKeys = (integer)str;
    }

    timer()
    {
        tick();
    }
}
