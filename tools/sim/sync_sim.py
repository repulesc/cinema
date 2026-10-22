# Sharing (5.5, protocol v2): cinema_sync.lsl (the sharing manager in Take 12) and watch/take12_watch.lsl (the free
# Watch HUD). First the two scripts must speak the same protocol; then a small region plays the whole flow:
# the "who" check (busy, out of range, Watch HUD), Go live inviting only the free, a friend and a Watch HUD joining at
# once while a stranger with Take 12 is only asked (accept / expire), no-answer reporting, a pull join on a live
# director, next 5 s apart, looking around, Ask / Always / Never lead with the 20 s auto-decline, Pass camera,
# Remove, a director gone quiet (heartbeat), a viewer leaving the region, rapid Go live / End live, duplicates.
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
sync, watch = rd("hud", "src", "cinema_sync.lsl"), rd("watch", "take12_watch.lsl")
core, ui = rd("hud", "src", "cinema_core.lsl"), rd("hud", "src", "cinema_ui.lsl")
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

# ---- the same protocol in both ------------------------------------------------------------------------------------
ch = lambda s: re.search(r"integer SYNC_CH\s*=\s*(-?\d+);", s).group(1)
check(ch(sync) == ch(watch), "the two scripts use different channels")
cam = lambda s: re.sub(r"\s+", " ", re.search(r"llSetCameraParams\(\[CAMERA_ACTIVE.*?\]\);", s, re.S).group(0))
check(cam(sync) == cam(watch), "viewers set the camera differently")
for name, s in (("sync", sync), ("watch", watch)):
    for w in ('w == "who"', '"here|', 'w == "invite"', '"busy|watching "', '"ack|1"', '"join"', '"leave"', '"next"', '"away"',
              '"back"', 'w == "cam"', 'w == "hb"', 'w == "director"', 'w == "kick"', 'w == "end"', "key who = llGetOwnerKey(id);",
              "if (who == gOwner) return;", "else if (who != gHost) return;", "PERMISSION_TRACK_CAMERA", "CHANGED_REGION",
              "if (!gIsAway && d > 0.6)", "else if (gIsAway && d < 0.3)", "gApplyT = llGetTime() + lag + 2.0;", "GONE"):
        check(w in s, f"{name}: missing {w}")
    check(s.count("llClearCameraParams()") == 1 and "clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;" in s,
          f"{name}: the camera clear must be single and guarded (no clear while the HUD comes off)")
check('say(who, "here|T|"' in sync and 'say(who, "here|W|"' in watch, "the who reply must say Take 12 or Watch")
# continuous feedback (5.5.0): viewers send a heartbeat; the director lists who is connected, live
check('say(gHost, "hb");' in sync and 'say(gHost, "hb");' in watch, "viewers must send a heartbeat")
for w in ("integer QUIET      = 25;", "integer LOST       = 45;", 't += " (no signal)";', 't += " (looking around)";',
          '" watching\\n"', '" lost connection"', "if (wi >= 0) gSeen = llListReplaceList(gSeen, [llGetUnixTime()], wi, wi);",
          'return "👁 " + sn(gHost) + " · no signal…";'):
    check(w in sync, f"sync: missing {w}")
check('s = "👁 " + llKey2Name(gHost) + " · no signal…";' in watch, "watch: no signal is not shown")
check("llDialog" not in watch and '"ask"' not in watch, "watch: no dialogs, and it cannot lead")
for w in ('llRegionSay(SYNC_CH, "T12|who|"', 'say(k, "invite|"', 'say(who, "ack|0");', 'say(who, "busy|live");',
          'if (!gSharing) return;                          // only a live view can be joined', 'if (gLeadAsk != NULL_KEY || gLead == 2) say(who, "lead|0");',
          "llGetUnixTime() - gNextT >= NEXT_GAP", "integer NEXT_GAP   = 5;", "integer WAIT       = 20;", "integer GONE       = 25;",
          'if (gHand) gHand = FALSE;', 'llMessageLinked(LINK_SET, CMD, "sharecam", "");', 'say(k, "lead|1");', 'say(gLeadAsk, "lead|0");',
          'all("director|"', 'say(gSel, "kick");', 'all("hb");', "if (llGetAgentSize(k) == ZERO_VECTOR)",
          "if (!gSharing && llGetUnixTime() - gToggleT < 2) return;", 'list    LEADS      = ["Ask", "Always", "Never"];',
          'llLinksetDataWriteProtected("cin.share_lead"', "didn't answer (out of range or HUD off)",
          'if (llSubStringIndex(llLinksetDataReadProtected("cin.friends", PASS), (string)who) >= 0)',
          "llGetPrimitiveParams([PRIM_TEXT])", 'return "● LIVE · nobody watching yet";',
          # 5.8: the state goes to cinema_tips (the one owner of the text above the HUD), short notices stay here
          'integer TEXT       = 7380;', 'if (gSharing) k = "live";', 'else if (gHost != NULL_KEY) k = "view";',
          'if (k != gSent) llMessageLinked(LINK_SET, TEXT, k, "");', '== gNoteS) llSetText("", ZERO_VECTOR, 0.0);'):
    check(w in sync, f"sync: missing {w}")
check(core.count("llMessageLinked(LINK_SET, CAMSET,") == 2, "core: CAMSET must be sent from setCam and the glide")
check('else if (str == "sharecam") { if (gState == ST_IDLE) engage("social"); }' in core, "core: Go live must start Social")
check("if (!gPermOK || gWatch) return;" in core and 'else if (gWatch && gState == ST_IDLE && str == "scenery") return;' in core,
      "core: viewing must block the idle start and keep the double-tap")
check('onLong()\n{\n    llMessageLinked(LINK_SET, CMD, "share", "");\n}' in ui, "ui: hold must open the Share panel, always")
check('if (num == CMD && (str == "livemenu" || str == "mainmenu")) openMenu(llGetSubString(str, 0, -5));' in ui, "ui: ⋯ More cannot open the menus")
check('"frame", "share", "opts"' in ui and 'b += ["share"];' not in ui, "ui: Share stays in the tap menu, leaves the live menu")

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
    """one avatar: kind 'T' (Take 12, cinema_sync) or 'W' (Take 12 Watch)"""
    def __init__(s, rg, name, pos, kind, friends=()):
        s.rg, s.name, s.pos, s.kind, s.friends, s.region = rg, name, pos, kind, set(friends), True
        s.dead = False; s.seen = {}; s.beat_t = 0      # dead: the HUD stops (crashed, detached without a word)
        s.sharing = s.cam_on = s.hand = False; s.toggle_t = -99
        s.watchers, s.away, s.inv, s.res, s.notes, s.near_list = [], [], [], [], [], None
        s.next_t, s.hb_t, s.inv_t, s.cuts, s.lead, s.lead_ask, s.lead_t = -99, 0, 0, 0, 0, None, 0
        s.host = s.offer = s.cam = None; s.pend_t = s.ask_t = 0; s.is_away = False; s.hear_t = 0; s.last = None
        rg.av[name] = s
    def near(s, k): return k in s.rg.av and sum((a - b) ** 2 for a, b in zip(s.rg.av[k].pos, s.pos)) ** 0.5 <= 20.0
    def say(s, k, m): s.rg.say_to(s.name, k, "T12|" + m)
    def all(s, m):
        for w in list(s.watchers): s.say(w, m)
    # ---- director -----------------------------------------------------------------------------------------------
    def who(s):
        s.near_list = []; s.rg.region_say(s.name, "T12|who|" + s.name)
        return [(k, i) for k, i in s.near_list]
    def invite(s, k):
        if k in s.inv or k in s.watchers: return
        s.inv.append(k); s.inv_t = s.rg.t; s.say(k, "invite|" + s.name)   # (the script records it right after sending)
    def golive(s, everyone):
        if not s.sharing and s.rg.t - s.toggle_t < 2: return False
        s.toggle_t = s.rg.t; s.sharing = True; s.cam_on = True; s.hb_t = s.rg.t
        if everyone:
            for k, info in (s.near_list or []):
                if info.split("|")[1] == "idle": s.invite(k)
        return True
    def endlive(s):
        if not s.sharing and not s.watchers: return
        s.all("end"); s.watchers = []; s.away = []; s.sharing = False; s.toggle_t = s.rg.t
        if s.lead_ask: s.say(s.lead_ask, "lead|0"); s.lead_ask = None
    def grant(s, k):
        s.lead_ask = None
        if k in s.watchers: s.watchers.remove(k)
        s.say(k, "lead|1"); s.all("director|%s|%s" % (k, k))
        s.watchers = []; s.away = []; s.sharing = False; s.cam_on = False
        s.watch(k)
    def camset(s, c): s.last = c; s.all("cam|" + c)
    def answer_lead(s, allow):
        if allow and s.lead_ask in s.watchers: s.grant(s.lead_ask)
        elif s.lead_ask: s.say(s.lead_ask, "lead|0"); s.lead_ask = None
    def remove(s, k): s.say(k, "kick"); s.watchers.remove(k)
    # ---- viewer -------------------------------------------------------------------------------------------------
    def watch(s, k):
        s.pend_t = 0; s.host = k; s.is_away = False; s.ask_t = 0; s.hear_t = s.rg.t; s.say(k, "join")
    def leave(s, tell=True):
        if s.host is None: return
        if tell: s.say(s.host, "leave")
        s.host = None; s.cam = None
    def ask(s):
        if s.host and not s.ask_t: s.say(s.host, "ask"); s.ask_t = s.rg.t
    def double_tap(s):
        if s.host: s.say(s.host, "next")
        elif s.pend_t: s.watch(s.offer)
    def orbit(s):
        if s.host and not s.is_away: s.is_away = True; s.say(s.host, "away")
    def esc(s):
        if s.host and s.is_away: s.is_away = False; s.say(s.host, "back")
    def ind(s):                                       # the text above the director's HUD
        if not s.sharing: return ""
        if not s.watchers: return "● LIVE · nobody watching yet"
        n = []
        for k in s.watchers[:4]:
            n.append(k + (" (no signal)" if s.rg.t - s.seen.get(k, 0) > 25 else (" (looking around)" if k in s.away else "")))
        return "● LIVE · %d watching\n%s" % (len(s.watchers), " · ".join(n))
    def timer(s):
        t = s.rg.t
        if s.dead: return
        if s.host and t - s.beat_t >= 10: s.beat_t = t; s.say(s.host, "hb")
        if s.inv and t - s.inv_t >= 3: s.res += [k + " no answer" for k in s.inv]; s.inv = []
        if s.pend_t and t - s.pend_t > 20: s.pend_t = 0
        if s.lead_ask and t - s.lead_t > 20: s.say(s.lead_ask, "lead|0"); s.lead_ask = None
        if s.sharing and t - s.hb_t >= 10:
            s.hb_t = t; s.all("hb")
            for k in list(s.watchers):
                if not s.rg.av[k].region: s.watchers.remove(k); s.notes.append(k + " left")
                elif t - s.seen.get(k, 0) > 45: s.watchers.remove(k); s.notes.append(k + " lost connection")
        if s.ask_t and t - s.ask_t > 25: s.ask_t = 0
        if s.host and t - s.hear_t > 25: s.notes.append(s.host + "'s camera is gone"); s.host = None; s.cam = None
    def hear(s, frm, msg):
        if not msg.startswith("T12|") or frm == s.name: return
        L = msg.split("|"); w = L[1]
        if frm in s.watchers: s.seen[frm] = s.rg.t          # a viewer's word: still connected
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
            if s.sharing: s.say(frm, "busy|live")
            elif s.host: s.say(frm, "busy|watching " + s.host)
            elif s.near(frm):
                if s.kind == "W" or frm in s.friends: s.say(frm, "ack|1"); s.watch(frm)
                else: s.say(frm, "ack|0"); s.offer = frm; s.pend_t = s.rg.t
        elif w in ("ack", "busy"):
            if frm not in s.inv: return
            s.inv.remove(frm)
            s.res.append(frm + (" busy (" + L[2] + ")" if w == "busy" else (" watches" if L[2] == "1" else " is asked")))
        elif w == "join":
            if not s.sharing: return
            if frm not in s.watchers: s.watchers.append(frm); s.seen[frm] = s.rg.t
            if s.last: s.say(frm, "cam|" + s.last)
        elif w == "leave" and frm in s.watchers: s.watchers.remove(frm); s.away = [a for a in s.away if a != frm]
        elif w == "away" and frm in s.watchers and frm not in s.away: s.away.append(frm)
        elif w == "back" and frm in s.away: s.away.remove(frm)
        elif w == "next" and frm in s.watchers and s.rg.t - s.next_t >= 5: s.next_t = s.rg.t; s.cuts += 1
        elif w == "ask" and frm in s.watchers:
            if s.lead_ask is not None or s.lead == 2: s.say(frm, "lead|0")
            elif s.lead == 1: s.grant(frm)
            else: s.lead_ask, s.lead_t = frm, s.rg.t
        elif frm != s.host: return
        elif w == "cam": s.hear_t = s.rg.t; s.cam = "|".join(L[2:])
        elif w == "hb": s.hear_t = s.rg.t
        elif w == "lead":
            s.ask_t = 0
            if L[2] == "1": s.leave(False); s.golive(False); s.notes.append("You lead now")
            else: s.notes.append(s.host + " keeps the lead")
        elif w == "director": s.watch(L[2])
        elif w == "kick": s.notes.append(s.host + " stopped sharing with you"); s.leave(False)
        elif w == "end": s.notes.append(s.host + " ended the live view"); s.leave(False)

rg = Region()
you = Av(rg, "Pano", (128, 128, 22), "T")
ana = Av(rg, "Ana", (130, 127, 22), "T", friends=["Pano"])
ben = Av(rg, "Ben", (126, 131, 22), "W")
cleo = Av(rg, "Cleo", (127, 126, 22), "T")                 # Take 12, has not saved you
dee = Av(rg, "Dee", (125, 125, 22), "T")                   # busy: watching Eve
eve = Av(rg, "Eve", (124, 126, 22), "T")
far = Av(rg, "Faraway", (168, 128, 22), "W")
eve.golive(False); dee.watch("Eve")
# hold > the panel: who is near
found = dict(you.who())
check(set(found) == {"Ana", "Ben", "Cleo", "Dee", "Eve"}, f"who check found {sorted(found)}")
check(found["Ben"].startswith("W|idle") and found["Dee"] == "T|view|Eve" and found["Eve"].startswith("T|live"),
      f"who check states: {found}")
check("Faraway" not in found, "someone 40 m away was listed")
# Go live: invites the free only
you.camset("<1,2,3>|<4,5,6>|0")
check(you.golive(True), "Go live did nothing")
check(sorted(you.watchers) == ["Ana", "Ben"], f"instant joiners: {you.watchers}")
check(cleo.pend_t and cleo.host is None, "a Take 12 owner who has not saved you must only be asked")
check(dee.host == "Eve" and "Dee" not in you.watchers, "a busy viewer was taken away from Eve")
check(sorted(you.res) == ["Ana watches", "Ben watches", "Cleo is asked"], f"invite results: {you.res}")
check(ana.cam == "<1,2,3>|<4,5,6>|0", "a joiner does not get the view on screen at once")
# rapid toggling: End live, then Go live again at once is ignored, two seconds later works
you.endlive()
check(you.watchers == [] and ana.host is None and ben.host is None, "End live did not end it for all")
check(not you.golive(True), "Go live right after End live must be ignored")
rg.tick(2); you.who()
check(you.golive(True) and sorted(you.watchers) == ["Ana", "Ben"], "Go live again did not bring them back")
# Cleo's invite: expires, then a new one is accepted with a double-tap
rg.tick(21)
check(cleo.pend_t == 0, "an invite must expire after 20 s")
you.res = []; you.invite("Cleo"); cleo.double_tap()
check("Cleo" in you.watchers, "a double-tap on an invite does not join")
# someone out of range does not answer: reported after 3 s
you.res = []; you.invite("Faraway"); rg.tick(3)
check(you.res == ["Faraway no answer"], f"no-answer report: {you.res}")
# a pull join on a live director (Dee leaves Eve and watches Eve? no: Dee watches Pano from the panel)
dee.leave(); dee.watch("Pano")
check("Dee" in you.watchers, "a pull join on a live director failed")
# next: 5 s apart
you.camset("<7,8,9>|<1,1,1>|1.5"); n0 = you.cuts
ben.double_tap(); ana.double_tap()
check(you.cuts == n0 + 1, "two double-taps together must cut once")
rg.tick(6); cleo.double_tap()
check(you.cuts == n0 + 2, "a double-tap 6 s later must cut")
far.say("Pano", "next")
check(you.cuts == n0 + 2, "someone not watching could cut")
Av(rg, "Mallory", (129, 129, 22), "T").say("Ana", "cam|<0,0,0>|<0,0,0>|0")
check(ana.cam == "<7,8,9>|<1,1,1>|1.5", "a camera from someone other than the director was taken")
# looking around
ben.orbit(); check(you.away == ["Ben"], "looking around not reported")
ben.esc(); check(you.away == [], "back not reported")
# lead requests: Ask (decline, then the 20 s auto-decline), Never, Always
ana.ask(); check(you.lead_ask == "Ana", "Ask: no prompt")
you.answer_lead(False); check(ana.notes[-1] == "Pano keeps the lead" and ana.host == "Pano", "Decline must keep the lead")
ana.ask(); cleo.ask()
check(you.lead_ask == "Ana" and cleo.notes[-1] == "Pano keeps the lead", "only one lead request at a time; the second is declined")
rg.tick(21)
check(you.lead_ask is None and ana.notes[-1] == "Pano keeps the lead", "an unanswered lead request must be declined after 20 s")
you.lead = 2; cleo.ask(); check(cleo.notes[-1] == "Pano keeps the lead", "Never must decline")
# Remove
you.remove("Dee")
check("Dee" not in you.watchers and dee.host is None and dee.notes[-1] == "Pano stopped sharing with you", "Remove failed")
# Always: Ana takes over, everyone (you too) follows Ana
you.lead = 1; ana.ask()
check(ana.sharing and you.host == "Ana" and ben.host == "Ana" and cleo.host == "Ana", "Always must hand everyone to Ana")
check(sorted(ana.watchers) == ["Ben", "Cleo", "Pano"] and not you.sharing, f"after the hand-over: {ana.watchers}")
ana.camset("<5,5,5>|<6,6,6>|0")
check(you.cam == ben.cam == cleo.cam == "<5,5,5>|<6,6,6>|0", "the new director is not followed")
you.camset("<9,9,9>|<9,9,9>|0")
check(ben.cam == "<5,5,5>|<6,6,6>|0", "two cameras fight: the old director still reaches viewers")
# Pass camera from the roster: Ana passes to Cleo
ana.grant("Cleo")
check(cleo.sharing and you.host == "Cleo" and ben.host == "Cleo" and ana.host == "Cleo", "Pass camera failed")
# continuous feedback: Cleo directs; Ana and Ben send heartbeats; Pano's HUD dies silently (still in the region)
check(cleo.ind() == "● LIVE · 3 watching\nPano · Ben · Ana" or set(cleo.ind().split("\n")[1].split(" · ")) == {"Pano", "Ben", "Ana"},
      f"the director's live list: {cleo.ind()!r}")
ben.orbit()
check("Ben (looking around)" in cleo.ind(), f"looking around not in the live list: {cleo.ind()!r}")
ben.esc()
you.dead = True; rg.tick(26)
check("Pano (no signal)" in cleo.ind() and "Ana (no signal)" not in cleo.ind() and "Ben (no signal)" not in cleo.ind(),
      f"after 26 s without a word from Pano: {cleo.ind()!r}")
rg.tick(30)
check("Pano" not in cleo.watchers and "Pano lost connection" in cleo.notes and sorted(cleo.watchers) == ["Ana", "Ben"],
      f"after 46 s: {cleo.watchers}, {cleo.notes[-1:]}")
you.dead = False; you.host = None
# a viewer leaves the region: dropped at the next heartbeat check
ben.region = False; rg.tick(10)
check("Ben" not in cleo.watchers and "Ben left" in cleo.notes, "a viewer who left the region stays in the roster")
# the director goes quiet (logged off): viewers drop out after 25 s
cleo.region = False; rg.tick(26)
check(ana.host is None and ana.notes[-1] == "Cleo's camera is gone", "viewers of a vanished director must drop out")
print("sharing: who check, Go live (free only), instant / asked joins, expiry, no-answer, pull join, next 5 s apart, "
      "looking around, Ask / Always / Never lead with auto-decline, Remove, Pass camera, heartbeat drops, rapid toggles")
print("sync checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
