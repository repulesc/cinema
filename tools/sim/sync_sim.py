# Connect (6.8.0; sharing before): sync.lsl (Take 12) and watch/take12_watch.lsl (the free Watch HUD). First the two
# scripts must speak the same protocol; then a small region plays the whole flow: the "who" check (busy, out of range,
# Watch HUD), Connect (no camera is started) with a friend and a Watch HUD connected at once while a stranger with
# Take 12 is only asked (accept / expire), no-answer reporting, a join on a connection, next 5 s apart, looking around;
# WHOEVER FILMS LEADS: a viewer's camera starting takes the lead (and two at once: the last one leads), nobody filming
# gives everyone their own camera, a movement key gives yours for a moment; Disconnect (a viewer, the hub handing on to
# another Take 12, the hub with only Watches left: it asks), an older hub that keeps the camera, heartbeat drops, a
# viewer leaving the region, rapid Connect / Disconnect, a late yes after Disconnect.
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
sync, watch = rd("hud", "src", "sync.lsl"), rd("watch", "take12_watch.lsl")
share = rd("hud", "src", "connect.lsl")    # the Connect panel (share.lsl 6.2-6.7, split out of sync for memory)
core, ui = rd("hud", "src", "core.lsl"), rd("hud", "src", "ui.lsl")
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

# ---- the same protocol in both ------------------------------------------------------------------------------------
ch = lambda s: re.search(r"integer SYNC_CH\s*=\s*(-?\d+);", s).group(1)
check(ch(sync) == ch(watch), "the two scripts use different channels")
cam = lambda s: re.sub(r"\s+", " ", re.search(r"llSetCameraParams\(\[CAMERA_ACTIVE.*?\]\);", s, re.S).group(0))
check(cam(sync) == cam(watch), "viewers set the camera differently")
# 6.0.1: each viewer places the director's camera through their OWN lens (same picture, own perspective)
import math
place = lambda src: re.search(r"\nplace\(integer again\)\n\{.*?\n\}\n", src, re.S)
check(place(sync) is not None and place(watch) is not None and place(sync).group(0) == place(watch).group(0),
      "sync and the Watch must place the camera with the same code")
core_src = open(os.path.join(R, "hud", "src", "core.lsl")).read()
check(core_src.count('"|" + (string)llGetCameraFOV(), "");') == 2, "core: CAMSET must carry the director's lens at both sites")
for src_, nm in ((sync, "sync"), (watch, "watch")):
    for frag in ('gCam = llDumpList2String(llList2List(L, 2, -1), "|");', "place(FALSE);",
                 'if (gHost != NULL_KEY && gCam != "" && llFabs(llGetCameraFOV() - gMyFov) > 0.004) place(TRUE);'):
        check(frag in src_, f"{nm}: missing {frag}")
def py_place(p, f, df, mf, wall=None):
    if df > 0.05 and mf > 0.05:
        k = max(0.2, min(5.0, math.tan(df / 2) / math.tan(mf / 2)))
        q = tuple(fi + (pi - fi) * k for pi, fi in zip(p, f))
        if wall is not None and math.dist(f, q) > wall:            # a wall `wall` m from the focus, on the line
            u = tuple((qi - fi) / math.dist(f, q) for qi, fi in zip(q, f))
            q = tuple(fi + ui * (wall - 0.3) for fi, ui in zip(f, u))
        return q
    return p
fov = lambda mm: 2 * math.atan(12.0 / mm)
size = lambda c, f, mm: (1.8 / math.dist(c, f)) / (2 * math.tan(fov(mm) / 2))
P, F = (120.0, 100.0, 27.0), (126.0, 104.0, 25.5)                # the director at 85 mm (backed off by 6.0's dolly)
for mine in (21, 35, 50, 85, 105):
    q = py_place(P, F, fov(85), fov(mine))
    check(abs(size(q, F, mine) - size(P, F, 85)) < 1e-9, f"viewer at {mine} mm: not the director's picture size")
    d0 = [b - a for a, b in zip(P, F)]; d1 = [b - a for a, b in zip(q, F)]
    check(max(abs(x / math.dist(P, F) - y / math.dist(q, F)) for x, y in zip(d0, d1)) < 1e-9, f"viewer at {mine} mm: off the director's line")
q = py_place(P, F, fov(50), fov(105), wall=9.0)                 # a longer lens than the director's: further back, a wall
check(abs(math.dist(q, F) - 8.7) < 1e-9, "a wall must stop the viewer's camera 0.3 m short")
for frag in ("if (k < 0.2) k = 0.2;", "if (k > 5.0) k = 5.0;", "llVecNorm(f - q) * 0.3"):
    check(frag in sync and frag in watch, f"the placement must keep {frag}")
check(py_place(P, F, 0.0, fov(21)) == P, "a camera without the lens (an older director) is applied as it is")
for name, s in (("sync", sync), ("watch", watch)):
    for w in ('w == "who"', '"here|', 'w == "invite"', '"busy|connected with "', '"ack|1"', '"join', '"leave"', '"next"', '"away"',
              '"back"', 'w == "cam"', 'w == "hb"', 'w == "director"', 'w == "kick"', 'w == "end"', "key who = llGetOwnerKey(id);",
              "if (who == gOwner) return;", "else if (who != gHost) return;", "PERMISSION_TRACK_CAMERA", "CHANGED_REGION",
              "if (!gIsAway && d > 0.6)", "else if (gIsAway && d < 0.3)", "gApplyT = llGetTime() + lag + 2.0;", "GONE"):
        check(w in s, f"{name}: missing {w}")
    check("clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;" in s
          and all("PERMISSION_CONTROL_CAMERA" in l for l in s.splitlines() if "llClearCameraParams()" in l),
          f"{name}: every camera clear must be guarded (no clear without the permission, none while the HUD comes off)")
check('say(who, "here|T|"' in sync and 'say(who, "here|W|"' in watch, "the who reply must say Take 12 or Watch")
# continuous feedback (5.5.0): viewers send a heartbeat; the director lists who is connected, live
check('say(gHost, "hb");' in sync and 'say(gHost, "hb");' in watch, "viewers must send a heartbeat")
for w in ("integer QUIET      = 25;", "integer LOST       = 45;", 't += " (no signal)";', 't += " (own camera)";',
          '" lost the connection"', "if (wi >= 0) gSeen = llListReplaceList(gSeen, [llGetUnixTime()], wi, wi);",
          'return "⇄ " + sn(gHost) + " · no signal…";'):
    check(w in sync, f"sync: missing {w}")
check('s = "⇄ " + gHostN + " · no signal…";' in watch, "watch: no signal is not shown")
# 5.8.2: a Watch says so when it joins (it cannot lead), and keeps the director's name (llKey2Name is "" once they left)
check('say(gHost, "join|W");' in watch and 'gHostN = n;' in watch, "watch: join|W / the kept name")
check('if (llList2String(L, 2) == "W" && llListFindList(gW, [who]) < 0) gW += [who];' in sync
      and 'llListFindList(gW, [who]) < 0) grant(who);' in sync and 'llDumpList2String(gW, ",")' in sync,
      "sync: a Watch cannot take the lead (it has no camera)")
check('if (gCamOn) llMessageLinked(LINK_SET, CMD, "stop", "");    // viewing never runs your own camera too' in sync, "sync: watching must stop your own camera")
check('llDialog(gOwner, fit(text, 500), b, gDlg);' in share and share.count("fit(") >= 5, "connect: dialog text and person labels must be cut to their byte limits")
# the panels live in connect.lsl (share.lsl 6.2-6.7); sync only says what to show and acts on the choice
check("llDialog" not in sync and "llListen(SYNC_CH" in sync, "sync: no dialogs of its own any more (memory)")
for page in ('ui("live|"', 'ui("view|"', 'ui("inv|"', 'ui("end|"', 'ui("near|"'):
    check(page in sync, f"sync: missing {page}")
for page in ('p == "live"', 'p == "view"', 'p == "inv"', 'p == "end"', 'p == "near"'):
    check(page in share, f"connect: no panel for {page}")
for gone in ("lead|<0-2>", "Roster", "Pass camera", "Ask to lead", "LEADS", "End live"):
    check(gone not in share, f"connect: '{gone}' is gone (whoever films leads)")
DO = re.findall(r'go\("(\w+)', share) + re.findall(r'go\(llList2String\(\["(\w+)", "(\w+)"\]', share)
DO = set(x for d in DO for x in (d if isinstance(d, tuple) else (d,)))
for d in DO:
    check(f'a == "{d}"' in sync, f"sync: connect asks for '{d}', sync does not act on it")
check('else if (num == SHARE_DO) act(str);' in sync and 'if (num == SHARE_UI) open(' in share, "the two halves must be wired")
def fit(s, m):     # share's fit(), ported: llStringToBase64 length * 3 / 4 - 2 is never over the true byte count
    import base64
    s = s[:m]
    while len(base64.b64encode(s.encode())) * 3 // 4 - 2 > m: s = s[:-1]
    return s
for t in ("a" * 30, "👁 " + "é" * 20, "◉ Watch " + "Анастасия Resident", "x" * 24, "✓" * 9):
    check(len(fit(t, 24).encode()) <= 24 and (len(t.encode()) > 24 or fit(t, 24) == t), f"connect: fit() cut {t!r} wrong")
check('gNoteS = llList2String(llGetPrimitiveParams([PRIM_TEXT]), 0);' in sync, "sync: a notice must be read back (254-byte cut)")
check("llKey2Name(" not in sync.replace("string n = llKey2Name(k);", ""), "sync: names must go through name() (kept after someone left)")
check("llDialog" not in watch and '"ask"' not in watch, "watch: no dialogs, and it cannot lead")
for w in ('llRegionSay(SYNC_CH, "T12|who|"', 'say(k, "invite|"', 'say(who, "ack|0");', 'say(who, "busy|connected");',
          'if (!gSharing) { say(who, "end"); return; }', "llGetUnixTime() - gNextT >= NEXT_GAP", "integer NEXT_GAP   = 5;",
          "integer WAIT       = 20;", "integer GONE       = 25;", 'if (gHand) gHand = FALSE;', 'say(k, "lead|1");', 'say(k, "lead|2");',
          'all("director|"', 'all("hb");', "if (llGetAgentSize(k) == ZERO_VECTOR)", 'if (m == "scenery") m = "sharecam";',
          "if (!gSharing && llGetUnixTime() - gToggleT < 2) return;", "didn't answer (out of range or HUD off)",
          'if (llSubStringIndex(llLinksetDataReadProtected("cin.friends", PASS), (string)who) >= 0)',
          "llGetPrimitiveParams([PRIM_TEXT])", 'if (n == 0) return "⇄ Connecting… · nobody has joined yet";',
          'if (!gCamOn) say(who, "pause");', 'if (gAskT) say(gHost, "ask");', 'say(gHost, "ask");',
          # the state goes to tips (the one owner of the text above the HUD), short notices stay here
          'integer TEXT       = 7380;', 'if (gSharing) k = "live";', 'else if (gHost != NULL_KEY) k = "view";',
          'if (k != gSent) llMessageLinked(LINK_SET, TEXT, k, "");', '== gNoteS) llSetText("", ZERO_VECTOR, 0.0);'):
    check(w in sync, f"sync: missing {w}")
for gone in ("cin.share_lead", "gLeadAsk", "list    LEADS", '"sharecam", "");    // core: Social'):
    check(gone not in sync, f"sync: '{gone}' is gone (whoever films leads; connecting starts no camera)")
check(core.count("llMessageLinked(LINK_SET, CAMSET,") == 2, "core: CAMSET must be sent from setCam and the glide")
check('else if (str == "sharecam") { if (gState == ST_IDLE) engage("social"); }' in core, "core: My turn after Scenery starts Us")
check("if (!gPermOK || gWatch) return;" in core and 'else if (gWatch && gState == ST_IDLE && str == "scenery") return;' in core,
      "core: viewing must block the idle start and keep the double-tap")
check('onLong()\n{\n    if (LITE) onTap();                                      // Take 12 Scenery: no sharing\n    else llMessageLinked(LINK_SET, CMD, "share", "");\n}' in ui
      and "integer LITE    = 0;" in ui, "ui: hold must open the Connect panel, always (the free Take 12 Scenery has no Connect)")
check('if (num == CMD && (str == "livemenu" || str == "mainmenu")) openMenu(llGetSubString(str, 0, -5));' in ui, "ui: ⋯ More cannot open the menus")
check('b = ["framing", "free", "share",' in ui and 'b += ["next", "stop", "share", "modes", "close"];' in ui and '|| id == "share") llMessageLinked(LINK_SET, CMD, id, "");' in ui,
      "ui: Connect is in both menus (tap always opens a menu; hold is only a shortcut)")
# 6.3: tap always opens a menu (main when idle, live while a camera runs); the hold shows a clap when it has taken
check('openMenu(llList2String(["main", "live"], gUiState != "idle"));' in ui and 'llMessageLinked(LINK_SET, CMD, "stop", "")' not in ui[ui.index("onTap()"):ui.index("onDouble()")],
      "ui: a tap must open a menu, never stop the camera")
check("frame(2 * gLook + 1);" in ui and "if (gLongDone) { frame(2 * gLook); nextTimer(); return; }" in ui, "ui: the hold must clap when it takes, and open again on release")

# ---- a small region (the logic of both scripts, ported) -----------------------------------------------------------
class Region:
    def __init__(s): s.av = {}; s.t = 100
    def region_say(s, frm, msg):
        for k, a in list(s.av.items()):
            if k != frm and a.region: a.hear(frm, msg)
    def say_to(s, frm, to, msg):
        if to in s.av and s.av[to].region and s.av[frm].region and not s.av[to].dead and not s.av[frm].dead: s.av[to].hear(frm, msg)
    def tick(s, dt):
        for _ in range(dt): s.t += 1; [a.timer() for a in list(s.av.values())]
class Av:
    """one avatar: kind 'T' (Take 12, sync) or 'W' (Take 12 Watch). screen: what their camera shows now
    ('own' = their own camera, else the camera string they follow, or their own scripted camera when filming)"""
    def __init__(s, rg, name, pos, kind, friends=(), old=False):
        s.rg, s.name, s.pos, s.kind, s.friends, s.region, s.old = rg, name, pos, kind, set(friends), True, old
        s.dead = False; s.seen = {}; s.beat_t = 0
        s.sharing = s.cam_on = s.hand = False; s.toggle_t = -99
        s.watchers, s.away, s.inv, s.res, s.notes, s.near_list = [], [], [], [], [], None
        s.next_t, s.hb_t, s.inv_t, s.cuts = -99, 0, 0, 0
        s.host = s.offer = s.cam = None; s.pend_t = s.ask_t = 0; s.is_away = False; s.hear_t = 0; s.last = None; s.wset = set()
        s.held = False; s.own_t = 0; s.screen = "own"; s.asked_end = False
        rg.av[name] = s
    def near(s, k): return k in s.rg.av and sum((a - b) ** 2 for a, b in zip(s.rg.av[k].pos, s.pos)) ** 0.5 <= 20.0
    def say(s, k, m): s.rg.say_to(s.name, k, "T12|" + m)
    def all(s, m):
        for w in list(s.watchers): s.say(w, m)
    # ---- holding the connection ---------------------------------------------------------------------------------
    def who(s):
        s.near_list = []; s.rg.region_say(s.name, "T12|who|" + s.name)
        return [(k, i) for k, i in s.near_list]
    def invite(s, k):
        if k in s.inv or k in s.watchers: return
        s.inv.append(k); s.inv_t = s.rg.t; s.say(k, "invite|" + s.name)
    def golive(s, everyone):                          # Connect: no camera is started
        if not s.sharing and s.rg.t - s.toggle_t < 2: return False
        s.toggle_t = s.rg.t; s.sharing = True; s.hb_t = s.rg.t
        if everyone:
            for k, info in (s.near_list or []):
                if info.split("|")[1] == "idle": s.invite(k)
        return True
    def connect(s, k): s.golive(False); s.invite(k) if s.sharing else None
    def endlive(s):
        if not s.sharing and not s.watchers: return
        s.all("end"); s.watchers = []; s.away = []; s.wset = set(); s.sharing = False; s.toggle_t = s.rg.t
    def grant(s, k):                                  # whoever films leads
        if k in s.watchers: s.watchers.remove(k)
        s.say(k, "lead|1"); s.all("director|%s|%s" % (k, k))
        s.watchers = []; s.away = []; s.wset = set(); s.sharing = False
        s.hand = s.cam_on
        s.watch(k)
    def hand_on(s, k):
        if k in s.watchers: s.watchers.remove(k)
        s.say(k, "lead|2"); s.all("director|%s|%s" % (k, k))
        s.watchers = []; s.away = []; s.wset = set(); s.sharing = False; s.toggle_t = s.rg.t
    def disconnect(s):
        if s.host: s.leave(); return "left"
        if not s.sharing: return None
        for k in s.watchers:
            if k not in s.wset: s.hand_on(k); return "handed on"
        if not s.watchers: s.endlive(); return "ended"
        s.asked_end = True; return "asks"            # only Watches left: the panel asks first
    def start_camera(s):                              # any camera: START
        s.cam_on = True; s.screen = "mine"; s.pend_t = 0
        if s.host and not s.ask_t: s.ask_t = s.rg.t; s.say(s.host, "ask")
    def stop_camera(s):                               # STOP: nobody films (a hub), or just your camera
        s.cam_on = False
        if s.hand: s.hand = False
        elif s.sharing: s.all("pause"); s.screen = "own"
        if not s.host: s.screen = "own"
    def camset(s, c): s.last = c; s.all("cam|" + c)
    # ---- connected with someone ---------------------------------------------------------------------------------
    def watch(s, k):
        s.pend_t = 0; s.host = k; s.is_away = False; s.ask_t = 0; s.own_t = 0; s.held = False; s.hear_t = s.rg.t
        s.say(k, "join|W" if s.kind == "W" else "join")
        if s.cam_on: s.stop_camera()                  # watching never runs your own camera too
    def leave(s, tell=True, clear=True):
        if s.host is None: return
        if tell: s.say(s.host, "leave")
        s.host = None; s.cam = None; s.held = False; s.ask_t = 0; s.own_t = 0
        if clear: s.screen = "mine" if s.cam_on else "own"
    def follow(s):
        if s.host and s.cam and not s.held and not s.ask_t and not s.own_t: s.screen = s.cam
    def double_tap(s):
        if s.host and s.held and s.kind == "T": s.start_camera()     # nobody films: you do
        elif s.host: s.say(s.host, "next")
        elif s.pend_t: s.watch(s.offer)
    def key(s):                                       # a movement key while connected: your camera for a moment
        if s.host and not s.own_t: s.say(s.host, "away"); s.screen = "own"
        if s.host: s.own_t = s.rg.t
    def orbit(s):
        if s.host and not s.is_away: s.is_away = True; s.say(s.host, "away")
    def esc(s):
        if s.host and s.is_away: s.is_away = False; s.say(s.host, "back")
    def ind(s):                                       # the text above the hub's HUD
        if not s.sharing: return ""
        if not s.watchers: return "⇄ Connecting… · nobody has joined yet"
        n = [k + (" (no signal)" if s.rg.t - s.seen.get(k, 0) > 25 else (" (own camera)" if k in s.away else "")) for k in s.watchers[:4]]
        return ("⇄ You film · %s see it" if s.cam_on else "⇄ Connected · %s\nnobody films · double-tap: film") % ", ".join(n)
    def timer(s):
        t = s.rg.t
        if s.dead: return
        if s.host and t - s.beat_t >= 10: s.beat_t = t; s.say(s.host, "hb")
        if s.inv and t - s.inv_t >= 3: s.res += [k + " didn't answer" for k in s.inv]; s.inv = []
        if s.pend_t and t - s.pend_t > 20: s.pend_t = 0
        if s.ask_t and t - s.ask_t > 20: s.ask_t = 0; s.leave(True, False); s.notes.append("No answer: you film on your own")
        if s.own_t and t - s.own_t > 4 and s.host: s.own_t = 0; s.say(s.host, "back"); s.follow()
        if s.sharing and t - s.hb_t >= 10:
            s.hb_t = t; s.all("hb")
            for k in list(s.watchers):
                if not s.rg.av[k].region: s.watchers.remove(k); s.notes.append(k + " disconnected")
                elif t - s.seen.get(k, 0) > 45: s.watchers.remove(k); s.notes.append(k + " lost the connection")
        if s.host and t - s.hear_t > 25: s.notes.append(s.host + " is gone"); s.host = None; s.cam = None; s.screen = "own"
    def hear(s, frm, msg):
        if not msg.startswith("T12|") or frm == s.name: return
        L = msg.split("|"); w = L[1]
        if frm in s.watchers: s.seen[frm] = s.rg.t
        if w == "hb" and frm in s.watchers: return
        if w == "who":
            if not s.near(frm): return
            st, d = "idle", ""
            if s.sharing: st = "live"
            elif s.host: st, d = "view", s.host
            elif s.pend_t: st = "pend"
            s.say(frm, "here|%s|%s|%s" % (s.kind, st, d))
        elif w == "here":
            if s.near_list is not None and s.near(frm): s.near_list.append((frm, "|".join(L[2:5])))
        elif w == "invite":
            if s.sharing: s.say(frm, "busy|connected")
            elif s.host: s.say(frm, "busy|connected with " + s.host)
            elif s.near(frm):
                if s.kind == "W" or frm in s.friends: s.say(frm, "ack|1"); s.watch(frm)
                else: s.say(frm, "ack|0"); s.offer = frm; s.pend_t = s.rg.t
        elif w in ("ack", "busy"):
            if frm not in s.inv: return
            s.inv.remove(frm)
            s.res.append(frm + (" is busy (" + L[2] + ")" if w == "busy" else (" connected" if L[2] == "1" else " is asked")))
        elif w == "join":
            if not s.sharing and s.host: s.say(frm, "director|%s|%s" % (s.host, s.host)); return   # the lead moved on
            if not s.sharing: s.say(frm, "end"); return
            if len(L) > 2 and L[2] == "W": s.wset.add(frm)
            if frm not in s.watchers: s.watchers.append(frm); s.seen[frm] = s.rg.t
            if not s.cam_on: s.say(frm, "pause")
            elif s.last: s.say(frm, "cam|" + s.last)
        elif w == "leave" and frm in s.watchers: s.watchers.remove(frm); s.away = [a for a in s.away if a != frm]
        elif w == "away" and frm in s.watchers and frm not in s.away: s.away.append(frm)
        elif w == "back" and frm in s.away: s.away.remove(frm)
        elif w == "next" and frm in s.watchers and s.rg.t - s.next_t >= 5: s.next_t = s.rg.t; s.cuts += 1
        elif w == "ask" and frm in s.watchers and frm not in s.wset:
            if s.old: s.say(frm, "lead|0")            # an older hub (Ask / Never) keeps the camera
            else: s.grant(frm)
        elif frm != s.host: return
        elif w == "cam": s.hear_t = s.rg.t; s.cam = "|".join(L[2:]); s.held = False; s.follow()
        elif w == "hb": s.hear_t = s.rg.t
        elif w == "pause":
            s.hear_t = s.rg.t; s.held = True
            if not s.ask_t: s.screen = "own"          # nobody films: your own camera, still connected
        elif w == "lead":
            s.ask_t = 0
            if L[2] == "0": s.leave(True, False); s.notes.append(frm + " kept the camera"); return
            s.leave(False, L[2] == "2"); s.toggle_t = -99; s.golive(False)
            s.notes.append("You film" if L[2] == "1" else frm + " disconnected · you keep the others connected")
        elif w == "director":
            s.host = L[2]; s.held = False; s.is_away = False; s.hear_t = s.rg.t; s.say(s.host, "join|W" if s.kind == "W" else "join")
            if s.ask_t: s.say(s.host, "ask")          # you started a camera meanwhile: ask the new one
        elif w == "kick": s.notes.append(s.host + " disconnected you"); s.leave(False)
        elif w == "end": s.notes.append(s.host + " disconnected"); s.leave(False)

# the port must follow the scripts it claims to
for frag in ('else if (w == "ask" && llListFindList(gWatchers, [who]) >= 0 && llListFindList(gW, [who]) < 0) grant(who);',
             'if (!gCamOn) say(who, "pause");', 'if (gAskT) say(gHost, "ask");', 'if (gHost != NULL_KEY && !gAskT)',
             'leave(FALSE, v == "2");', 'if (v == "0")', 'else if (num == CMD && str == "scenery" && gHost != NULL_KEY && gHeld) film();',
             'if (!gAskT && gOwnT == 0.0) place(FALSE);', 'if (gCam != "" && !gHeld && !gAskT) place(FALSE);',
             'if (!gAskT && (llGetPermissions() & PERMISSION_CONTROL_CAMERA)) llClearCameraParams();',
             'if (llListFindList(gW, [llList2Key(gWatchers, i)]) < 0)', 'else ui("end|" + llDumpList2String(gWatchers, ","));',
             'say(who, "director|" + (string)gHost + "|" + name(gHost));'):
    check(frag in sync, f"sync: the port is stale: {frag}")
for frag in ('if (gOwnT == 0.0) place(FALSE);', 'if (llGetPermissions() & PERMISSION_CONTROL_CAMERA) llClearCameraParams();',
             'gOwnT = 0.0;                                     // still again: back on the shared view', '"Disconnected"'):
    check(frag in watch, f"watch: the port is stale: {frag}")

rg = Region()
you = Av(rg, "Pano", (128, 128, 22), "T")
ana = Av(rg, "Ana", (130, 127, 22), "T", friends=["Pano"])
ben = Av(rg, "Ben", (126, 131, 22), "W")
cleo = Av(rg, "Cleo", (127, 126, 22), "T")                 # Take 12, has not saved you
dee = Av(rg, "Dee", (125, 125, 22), "T")                   # busy: connected with Eve
eve = Av(rg, "Eve", (124, 126, 22), "T")
far = Av(rg, "Faraway", (168, 128, 22), "W")
eve.golive(False); dee.watch("Eve")
# hold > the panel: who is near
found = dict(you.who())
check(set(found) == {"Ana", "Ben", "Cleo", "Dee", "Eve"}, f"who check found {sorted(found)}")
check(found["Ben"].startswith("W|idle") and found["Dee"] == "T|view|Eve" and found["Eve"].startswith("T|live"), f"who check states: {found}")
check("Faraway" not in found, "someone 40 m away was listed")
# + Everyone: connects with the free only, and starts no camera
check(you.golive(True), "Connect did nothing")
check(not you.cam_on and you.screen == "own", "connecting must not start a camera")
check(sorted(you.watchers) == ["Ana", "Ben"], f"connected at once: {you.watchers}")
check(ana.held and ana.screen == "own" and ben.held, "connected, nobody films: everyone keeps their own camera")
check("Connected · Ana, Ben" in you.ind() and "nobody films" in you.ind(), f"the hub's line: {you.ind()!r}")
check(cleo.pend_t and cleo.host is None, "a Take 12 owner who has not saved you must only be asked")
check(dee.host == "Eve" and "Dee" not in you.watchers, "someone connected with Eve was taken away")
check(sorted(you.res) == ["Ana connected", "Ben connected", "Cleo is asked"], f"results: {you.res}")
# Cleo says yes with a double-tap
cleo.double_tap()
check("Cleo" in you.watchers and cleo.held, "a double-tap on the question must connect")
# you film: everyone connected sees it
you.start_camera(); you.camset("<1,2,3>|<4,5,6>|0")
check(ana.screen == ben.screen == cleo.screen == "<1,2,3>|<4,5,6>|0" and not ana.held, "the hub's camera is not seen by all")
check(you.ind() == "⇄ You film · Ana, Ben, Cleo see it", f"the hub's line: {you.ind()!r}")
# next: 5 s apart
n0 = you.cuts
ben.double_tap(); ana.double_tap()
check(you.cuts == n0 + 1, "two double-taps together must cut once")
rg.tick(6); cleo.double_tap()
check(you.cuts == n0 + 2, "a double-tap 6 s later must cut")
far.say("Pano", "next")
check(you.cuts == n0 + 2, "someone not connected could cut")
Av(rg, "Mallory", (129, 129, 22), "T").say("Ana", "cam|<0,0,0>|<0,0,0>|0")
check(ana.screen == "<1,2,3>|<4,5,6>|0", "a camera from someone other than the hub was taken")
# a movement key while connected: your camera for a moment, then the shared view again (with the latest shot)
ana.key(); you.camset("<2,2,2>|<3,3,3>|0")
check(ana.screen == "own" and "Ana" in you.away and ana.host == "Pano", "a movement key must give your own camera, still connected")
check("Ana (own camera)" in you.ind(), f"the hub must see it: {you.ind()!r}")
rg.tick(3); ana.key(); rg.tick(3)
check(ana.screen == "own", "still moving: still your own camera")
rg.tick(3)
check(ana.screen == "<2,2,2>|<3,3,3>|0" and "Ana" not in you.away, "4 s still: back on the shared view, at the latest shot")
# looking around (orbit) and Esc
ben.orbit(); check("Ben" in you.away, "looking around not reported")
ben.esc(); check("Ben" not in you.away, "back not reported")
# WHOEVER FILMS LEADS: Ana starts a camera; everyone, the hub too, follows Ana
ana.start_camera()
check(ana.sharing and you.host == "Ana" and ben.host == "Ana" and cleo.host == "Ana", "Ana's camera must take the lead for everyone")
check(sorted(ana.watchers) == ["Ben", "Cleo", "Pano"] and not you.sharing and not you.cam_on, f"after the turn: {ana.watchers}")
ana.camset("<5,5,5>|<6,6,6>|0")
check(you.screen == ben.screen == cleo.screen == "<5,5,5>|<6,6,6>|0", "the new filmer is not followed")
you.camset("<9,9,9>|<9,9,9>|0")
check(ben.screen == "<5,5,5>|<6,6,6>|0", "two cameras fight: the old hub still reaches the others")
# a Watch cannot take the lead (it has no camera); its "ask" would be ignored
ben.say("Ana", "ask"); check(ana.sharing and ben.host == "Ana", "a Watch must never take the lead")
# two start at once: Pano's turn reaches Ana first; Cleo's ask (in flight) is then put to Pano: the last one leads
cleo.cam_on = True; cleo.ask_t = rg.t; cleo.screen = "mine"            # her "ask" went to Ana and was lost in the change
you.start_camera()
check(cleo.sharing and you.host == "Cleo" and ana.host == "Cleo" and ben.host == "Cleo",
      f"two cameras at once: the last one leads (hub {[a.name for a in rg.av.values() if a.sharing]})")
# Cleo stops: nobody films; everyone has their own camera, still connected; a double-tap from Ana films
cleo.stop_camera()
check(ana.held and you.held and ana.screen == "own" and ben.screen == "own" and you.host == "Cleo", "nobody films: own cameras, still connected")
ana.double_tap()
check(ana.sharing and cleo.host == "Ana" and you.host == "Ana", "a double-tap when nobody films must start your camera and lead")
# Disconnect: a viewer leaves; the others stay
check(you.disconnect() == "left" and "Pano" not in ana.watchers and you.host is None, "a viewer's Disconnect")
check(cleo.host == "Ana" and ben.host == "Ana", "one leaving must not disconnect the others")
# the hub disconnects: another Take 12 keeps the others connected, and no camera starts for them
ana.stop_camera(); r = ana.disconnect()
check(r == "handed on" and cleo.sharing and not cleo.cam_on and ben.host == "Cleo" and ben.held and ana.host is None and not ana.sharing,
      f"the hub's Disconnect must hand on ({r}; hub {[a.name for a in rg.av.values() if a.sharing]})")
check(any("you keep the others connected" in n for n in cleo.notes), "the new hub must be told")
# the hub with only Watches left: it asks first, then ends it for them
r = cleo.disconnect()
check(r == "asks" and cleo.sharing and ben.host == "Cleo", "with only Watches left, Disconnect must ask first")
cleo.endlive()
check(ben.host is None and ben.notes[-1] == "Cleo disconnected", "confirmed: the Watch is told")
# rapid Connect / Disconnect; a late yes after Disconnect
rg.tick(2)
check(you.golive(False) and not you.cam_on, "connect again")
you.endlive(); check(not you.golive(False), "Connect right after Disconnect must be ignored")
rg2 = Region()
p = Av(rg2, "Pia", (128, 128, 22), "T"); q = Av(rg2, "Quin", (129, 128, 22), "T"); w = Av(rg2, "Wim", (127, 128, 22), "W")
p.connect("Wim"); p.invite("Quin")
check(w.host == "Pia" and "Wim" in p.wset, "a Watch must be known as one")
p.endlive(); rg2.tick(3); q.double_tap()
check(q.host is None and q.notes[-1] == "Pia disconnected", f"a late yes after Disconnect must be told: {q.notes}")
q.start_camera(); rg2.tick(2); p.connect("Quin"); q.double_tap()
check(q.host == "Pia" and not q.cam_on, "connecting with a hub stops your own camera (you watch)")
# an older hub (Ask / Never lead) answers lead|0: you film on your own, disconnected
o = Av(rg2, "Olde", (128, 129, 22), "T", old=True); o.golive(False); o.invite("Quin")
q.leave(); o.invite("Quin"); q.double_tap(); q.start_camera()
check(q.host is None and q.cam_on and "Olde kept the camera" in q.notes, "an older hub keeping the camera: you film alone")
# heartbeat drops, a viewer leaving the region, the hub vanishing
rg3 = Region()
h = Av(rg3, "Hal", (128, 128, 22), "T"); i_ = Av(rg3, "Ivy", (129, 128, 22), "T", friends=["Hal"]); j_ = Av(rg3, "Jo", (127, 128, 22), "W")
h.golive(False); h.invite("Ivy"); h.invite("Jo"); h.start_camera(); h.camset("<1,1,1>|<1,1,1>|0")
i_.dead = True; rg3.tick(26)
check("Ivy (no signal)" in h.ind() and "Jo (no signal)" not in h.ind(), f"26 s without a word: {h.ind()!r}")
rg3.tick(30)
check("Ivy" not in h.watchers and "Ivy lost the connection" in h.notes, "after 46 s: dropped")
j_.region = False; rg3.tick(10)
check("Jo" not in h.watchers and "Jo disconnected" in h.notes, "a viewer who left the region stays connected")
rg4 = Region()
a4 = Av(rg4, "Ari", (128, 128, 22), "T"); b4 = Av(rg4, "Bo", (129, 128, 22), "W")
a4.connect("Bo"); a4.region = False; rg4.tick(26)
check(b4.host is None and "Ari is gone" in b4.notes, "connected with a vanished hub must drop out")
print("connect: who check, Connect without a camera, at once / asked, expiry, next 5 s apart, your camera for a moment, "
      "whoever films leads (two at once: the last), nobody films: own cameras, Disconnect (leave, hand on, ask), "
      "an older hub, heartbeat drops, rapid toggles, a late yes")
print("sync checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
