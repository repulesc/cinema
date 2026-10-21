# Share the view (5.4, one director at a time): cinema_sync.lsl (Take 12: directing and watching) and
# watch/take12_watch.lsl (the free Watch HUD). Checks that both speak the same protocol, then plays a small region:
# you share, friends with the Watch HUD and with Take 12 follow at once, a Take 12 owner who has not saved you is only
# asked, a stranger 40 m away is never asked; cameras follow; double-taps close together cut once; a watcher looking
# around is reported and comes back; a Take 12 watcher takes over as director and everyone (you too) follows them;
# keys release; the director stopping ends it for all.
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
sync, watch = rd("hud", "src", "cinema_sync.lsl"), rd("watch", "take12_watch.lsl")
core, ui = rd("hud", "src", "cinema_core.lsl"), rd("hud", "src", "cinema_ui.lsl")
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

# ---- the same protocol in both ----------------------------------------------------------------------------------
ch = lambda s: re.search(r"integer SYNC_CH\s*=\s*(-?\d+);", s).group(1)
check(ch(sync) == ch(watch), "the two scripts use different channels")
cam = lambda s: re.sub(r"\s+", " ", re.search(r"llSetCameraParams\(\[CAMERA_ACTIVE.*?\]\);", s, re.S).group(0))
check(cam(sync) == cam(watch), "watchers set the camera differently")
for name, s in (("sync", sync), ("watch", watch)):
    for w in ('"ack|1"', '"join"', '"leave"', '"next"', '"away"', '"back"', 'w == "offer"', 'w == "cam"', 'w == "end"',
              'w == "director"', "key who = llGetOwnerKey(id);", "if (who == gOwner) return;", "NEAR", "PERMISSION_TRACK_CAMERA",
              "if (!gIsAway && d > 0.6)", "else if (gIsAway && d < 0.3)", "gApplyT = llGetTime() + lag + 2.0;"):
        check(w in s, f"{name}: missing {w}")
    check(s.count("llClearCameraParams()") == 1 and "clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;" in s,
          f"{name}: the camera clear must be single and guarded (no clear while the HUD comes off)")
    check("leave(TRUE, FALSE);" in s, f"{name}: taking the HUD off must leave without touching the camera")
check("llDialog" not in watch, "watch: no dialogs, it follows at once")
for w in ('llRegionSay(SYNC_CH, "T12|offer|" + llKey2Name(gOwner));', 'say(who, "ack|0");', 'w == "direct"', 'all("director|"',
          "llGetUnixTime() - gNextT >= NEXT_GAP", "integer NEXT_GAP   = 5;", 'if (gHand) gHand = FALSE;',
          'llMessageLinked(LINK_SET, CMD, "sharecam", "");', 'if (llSubStringIndex(llLinksetDataReadProtected("cin.friends", PASS), (string)who) >= 0)',
          'if (gAck != []) r = "Offered to: " + llDumpList2String(gAck, ", ");', 'if (gPendT && llGetUnixTime() - gPendT > 20) unpend();'):
    check(w in sync, f"sync: missing {w}")
check(core.count("llMessageLinked(LINK_SET, CAMSET,") == 2, "core: CAMSET must be sent from setCam and the glide")
check("if (!gPermOK || gWatch) return;" in core and 'else if (gWatch && gState == ST_IDLE && str == "scenery") return;' in core,
      "core: watching must block the idle start and keep the double-tap")
check('else if (str == "sharecam") { if (gState == ST_IDLE) engage(gMode); }' in core, "core: Share cannot start your camera")
check('"frame", "share", "pace"' in ui and 'b += ["share"];' in ui, "ui: Share must be in the tap menu and the hold menu")

# ---- a small region ---------------------------------------------------------------------------------------------
class Region:
    def __init__(s): s.av = {}
    def region_say(s, frm, msg):
        for k, a in list(s.av.items()):
            if k != frm: a.hear(frm, msg)
    def say_to(s, frm, to, msg):
        if to in s.av: s.av[to].hear(frm, msg)
class Av:
    """one avatar wearing cinema_sync ('take12') or take12_watch ('watch')"""
    def __init__(s, rg, name, pos, kind, friends=()):
        s.rg, s.name, s.pos, s.kind, s.friends = rg, name, pos, kind, set(friends)
        s.sharing = s.cam_on = False; s.watchers, s.away, s.acks, s.cuts, s.next_t = [], [], [], 0, -99
        s.host = s.pending = s.cam = None; s.is_away = False; s.last = None; s.t = 0
        rg.av[name] = s
    def near(s, k): return k in s.rg.av and sum((a - b) ** 2 for a, b in zip(s.rg.av[k].pos, s.pos)) ** 0.5 <= 20.0
    def say(s, k, m): s.rg.say_to(s.name, k, "T12|" + m)
    def all(s, m):
        for w in list(s.watchers): s.say(w, m)
    # the one Share button
    def share(s):
        if s.host: return "watch-dialog"
        if s.pending: s.follow(s.pending); return "joined"
        if s.sharing: return "share-dialog"
        s.sharing = True; s.cam_on = True; s.acks = []
        s.rg.region_say(s.name, "T12|offer|" + s.name)
        return "offered"
    def camset(s, c):
        s.last = c
        s.all("cam|" + c)
    def stop(s):
        s.cam_on = False
        s.all("end"); s.watchers = []; s.away = []; s.sharing = False
    def direct(s):                                    # watching, Share > Direct
        h = s.host; s.say(h, "direct"); s.host = None; s.cam = None
        s.sharing = True; s.cam_on = True
    # watching
    def follow(s, k): s.host, s.pending, s.is_away = k, None, False; s.say(k, "join")
    def key(s):
        if s.host: s.say(s.host, "leave"); s.host = None; s.cam = None
    def double_tap(s):
        if s.host: s.say(s.host, "next")
        elif s.pending: s.follow(s.pending)
    def orbit(s):                                     # Alt-orbit while watching
        if s.host and not s.is_away: s.is_away = True; s.say(s.host, "away")
    def esc(s):
        if s.host and s.is_away: s.is_away = False; s.say(s.host, "back")
    def hear(s, frm, msg):
        if not msg.startswith("T12|") or frm == s.name: return
        L = msg.split("|"); w = L[1]
        if w == "offer":
            if s.host is None and not s.sharing and s.near(frm):
                if s.kind == "watch" or frm in s.friends: s.say(frm, "ack|1"); s.follow(frm)
                else: s.say(frm, "ack|0"); s.pending = frm
        elif w == "ack": s.acks.append(frm + ("" if L[2] == "1" else " (double-tap)"))
        elif w == "join":
            if frm not in s.watchers: s.watchers.append(frm)
            s.sharing = True
            if s.last: s.say(frm, "cam|" + s.last)
        elif w == "leave" and frm in s.watchers: s.watchers.remove(frm); s.away = [a for a in s.away if a != frm]
        elif w == "away" and frm in s.watchers and frm not in s.away: s.away.append(frm)
        elif w == "back" and frm in s.away: s.away.remove(frm)
        elif w == "next" and frm in s.watchers and s.t - s.next_t >= 5: s.next_t = s.t; s.cuts += 1
        elif w == "direct" and frm in s.watchers and s.kind == "take12":
            s.watchers.remove(frm); s.all("director|" + frm); s.watchers = []; s.away = []; s.sharing = False
            s.cam_on = False; s.follow(frm)
        elif w == "director" and frm == s.host: s.follow(L[2])
        elif w == "cam" and frm == s.host: s.cam = "|".join(L[2:])
        elif w == "end" and frm == s.host: s.host = None; s.cam = None

rg = Region()
you = Av(rg, "Pano", (128, 128, 22), "take12")
ana = Av(rg, "Ana", (130, 127, 22), "take12", friends=["Pano"])
ben = Av(rg, "Ben", (126, 131, 22), "watch")
cleo = Av(rg, "Cleo", (127, 126, 22), "take12")          # has Take 12, has not saved you
far = Av(rg, "Stranger", (168, 128, 22), "watch")
you.camset("<1,2,3>|<4,5,6>|0")
check(you.share() == "offered", "Share should offer straight away")
check(ana.host == "Pano" and ben.host == "Pano", "a Watch HUD, or Take 12 with you in its Friends, must follow at once")
check(cleo.host is None and cleo.pending == "Pano", "a Take 12 owner who has not saved you must only be asked")
check(far.host is None and far.pending is None, "someone 40 m away was asked")
check(sorted(you.acks) == ["Ana", "Ben", "Cleo (double-tap)"], f"who got your offer: {you.acks}")
check(ana.cam == "<1,2,3>|<4,5,6>|0" and ben.cam == ana.cam, "watchers do not get the view on screen at once")
check(cleo.share() == "joined" and cleo.host == "Pano", "Cleo's Share button should join the waiting offer")
check(you.share() == "share-dialog", "while sharing, Share shows who watches")
you.camset("<7,8,9>|<1,1,1>|1.5")
check(ana.cam == ben.cam == cleo.cam == "<7,8,9>|<1,1,1>|1.5", "a glide is not followed by everyone")
# two double-taps close together cut once; later ones again
ben.double_tap(); ana.double_tap()
check(you.cuts == 1, f"two double-taps 0 s apart cut {you.cuts} times")
you.t = 6; cleo.double_tap()
check(you.cuts == 2, "a double-tap 6 s later did not cut")
far.say("Pano", "next")
check(you.cuts == 2, "someone not watching could cut")
Av(rg, "Mallory", (129, 129, 22), "take12").say("Ana", "cam|<0,0,0>|<0,0,0>|0")
check(ana.cam == "<7,8,9>|<1,1,1>|1.5", "a camera from someone other than the director was taken")
# looking around
ben.orbit()
check(you.away == ["Ben"], "you are not told that Ben is looking around")
ben.esc()
check(you.away == [], "you are not told that Ben is back")
# Ana takes over: everyone, you too, follows Ana
check(ana.share() == "watch-dialog", "while watching, Share should offer Direct / Leave")
ana.direct()
check(you.host == "Ana" and ben.host == "Ana" and cleo.host == "Ana", f"after Ana directs: {you.host}, {ben.host}, {cleo.host}")
check(sorted(ana.watchers) == ["Ben", "Cleo", "Pano"], f"Ana's watchers: {ana.watchers}")
check(you.sharing is False and you.watchers == [], "the old director must become a watcher")
ana.camset("<5,5,5>|<6,6,6>|0")
check(you.cam == ben.cam == cleo.cam == "<5,5,5>|<6,6,6>|0", "the new director's camera is not followed")
you.camset("<9,9,9>|<9,9,9>|0")
check(ben.cam == "<5,5,5>|<6,6,6>|0", "two cameras fight: the old director still reaches watchers")
# keys release; the director stopping ends it for all
cleo.key()
check(cleo.host is None and "Cleo" not in ana.watchers, "a key does not give a watcher their camera back")
ana.stop()
check(you.host is None and ben.host is None and ana.watchers == [], "the director stopping does not end it for all")
print("share the view: one director; Watch HUDs and friends follow at once, others are asked; double-taps 5 s apart; "
      "looking around reported; Direct hands everyone over; keys release; stopping ends it")
print("sync checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
