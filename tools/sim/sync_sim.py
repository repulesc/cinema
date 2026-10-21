# Share the view (5.2): cinema_sync.lsl (in Take 12, sharing and watching) and watch/take12_watch.lsl (the free
# Watch HUD). Checks that both speak the same protocol, then plays a small region: you share, a friend with Take 12
# and a friend with the Watch HUD accept, a stranger 40 m away is never asked, cameras follow, a watcher's
# double-tap cuts for all, keys release, and stopping your camera ends it for everyone.
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sync = open(os.path.join(R, "hud", "src", "cinema_sync.lsl")).read()
watch = open(os.path.join(R, "watch", "take12_watch.lsl")).read()
core = open(os.path.join(R, "hud", "src", "cinema_core.lsl")).read()
ui = open(os.path.join(R, "hud", "src", "cinema_ui.lsl")).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

# ---- the same protocol in both --------------------------------------------------------------------------------------
ch = lambda s: re.search(r"integer SYNC_CH\s*=\s*(-?\d+);", s).group(1)
check(ch(sync) == ch(watch), "the two scripts use different channels")
camparams = lambda s: re.sub(r"\s+", " ", re.search(r"llSetCameraParams\(\[CAMERA_ACTIVE.*?\]\);", s, re.S).group(0))
check(camparams(sync) == camparams(watch), "watchers set the camera differently")
for w in ('say(host, "join");', 'say(gHost, "leave");', 'say(gHost, "next");', 'w == "offer"', 'w == "cam"', 'w == "end"',
          "key who = llGetOwnerKey(id);", "if (who == gOwner) return;", "float   NEAR       = 20.0;"):
    check(w in sync, f"sync: missing {w}")
for w in ('say(gHost, "join");', 'say(gHost, "leave");', 'say(gHost, "next");', 'w == "offer"', 'w == "cam"', 'w == "end"',
          "key who = llGetOwnerKey(id);", "if (who == gOwner) return;", "float   NEAR    = 20.0;"):
    check(w in watch, f"watch: missing {w}")
check('llRegionSay(SYNC_CH, "T12|offer|" + llKey2Name(gOwner));' in sync, "sync: the offer is not region-wide")
check(sync.count("llRegionSayTo(k, SYNC_CH") == 1 and watch.count("llRegionSayTo(k, SYNC_CH") == 1, "replies must go to one avatar")
# core reports every camera; watching blocks the idle start and turns the double-tap into "next for all"
check(core.count("llMessageLinked(LINK_SET, CAMSET,") == 2, "core: CAMSET must be sent from setCam and the glide")
check("if (!gPermOK || gWatch) return;" in core, "core: idle start while watching")
check('else if (gWatch && gState == ST_IDLE && str == "scenery") return;' in core, "core: double-tap while watching starts scenery")
check('b += ["share"];' in ui and 'llMessageLinked(LINK_SET, CMD, "share", "")' in ui, "ui: Share is not in the live menu")
check('unpend();\n            leave(TRUE, TRUE);' in sync and 'else if (num == STOP && str != "switch") endShare();' in sync,
      "sync: own camera / stop handling changed")

# taking a HUD off: Second Life has already withdrawn the camera, so the camera is never cleared on detach (5.2.1:
# "trying to clear camera parameters but PERMISSION_CONTROL_CAMERA permission not set")
for name, s_ in (("sync", sync), ("watch", watch)):
    check(s_.count("llClearCameraParams()") == 1, f"{name}: the camera is cleared in more than one place")
    check("clear = clear && llGetAttached() && llGetPermissionsKey() == gOwner;" in s_, f"{name}: the camera clear is not guarded")
    check("leave(TRUE, FALSE);" in s_, f"{name}: detaching must leave without touching the camera")
check("if (id == NULL_KEY) leave(TRUE, FALSE);" in watch, "watch: detach handling changed")

check('if (llSubStringIndex(llLinksetDataReadProtected("cin.friends", PASS), (string)who) >= 0)\n            {\n                say(who, "ack|1");\n                watch(who);' in sync,
      "sync: friends must watch at once")
check('else if (num == CMD && str == "scenery" && gPendT) watch(gOffer);' in sync, "sync: double-tap does not accept an offer")
check("llDialog" not in watch, "watch: no dialog any more, the view switches at once")
check('if (gPendT && llGetUnixTime() - gPendT > 20) unpend();' in sync, "sync: an offer must expire after 20 s")
check('say(who, "ack|1");' in sync and 'say(who, "ack|0");' in sync and 'say(gHost, "ack|1");' in watch, "who got the offer is not reported back")
check('if (gAck != []) r = "Offered to: " + llDumpList2String(gAck, ", ");' in sync and "Nobody near you wears Take 12 or Take 12 Watch" in sync, "sync: the offer summary is missing")
# ---- a small region ---------------------------------------------------------------------------------------------
class Region:
    def __init__(s): s.av = {}; s.out = []
    def region_say(s, frm, msg):
        for k, a in s.av.items():
            if k != frm: a.hear(frm, msg)
    def say_to(s, frm, to, msg):
        if to in s.av: s.av[to].hear(frm, msg)
class Av:
    """one avatar wearing cinema_sync (kind 'take12') or take12_watch (kind 'watch')"""
    def __init__(s, rg, name, pos, kind, friends=()):
        s.rg, s.name, s.pos, s.kind, s.friends, s.pending = rg, name, pos, kind, set(friends), None
        s.watchers, s.host, s.offer, s.cam, s.next_asked, s.last, s.acks = [], None, None, None, 0, None, []
        rg.av[name] = s
    def near(s, k): return k in s.rg.av and sum((a - b) ** 2 for a, b in zip(s.rg.av[k].pos, s.pos)) ** 0.5 <= 20.0
    def say(s, k, m): s.rg.say_to(s.name, k, "T12|" + m)
    # sharer side (Take 12 only)
    def share(s): s.acks = []; s.rg.region_say(s.name, "T12|offer|" + s.name)
    def camset(s, c):
        s.last = c
        for w in s.watchers: s.say(w, "cam|" + c)
    def stop(s):
        for w in s.watchers: s.say(w, "end")
        s.watchers = []
    # watcher side
    def join(s, k): s.host, s.pending = k, None; s.say(k, "join")
    def expire(s): s.pending = None                      # 20 s without a double-tap
    def key(s):
        if s.host: s.say(s.host, "leave"); s.host = None; s.cam = None
    def double_tap(s):
        if s.host: s.say(s.host, "next")
        elif s.pending: s.join(s.pending)
    def hear(s, frm, msg):
        if not msg.startswith("T12|") or frm == s.name: return
        L = msg.split("|"); w = L[1]
        if w == "offer":
            if s.host is None and s.near(frm):
                s.offer = frm
                # the Watch HUD, or Take 12 with you in its Friends: at once; anyone else: a double-tap
                if s.kind == "watch" or frm in s.friends: s.say(frm, "ack|1"); s.join(frm)
                else: s.say(frm, "ack|0"); s.pending = frm
        elif w == "ack": s.acks.append(frm + ("" if L[2] == "1" else " (double-tap)"))
        elif w == "join" and s.kind == "take12":
            if frm not in s.watchers: s.watchers.append(frm)
            if s.last: s.say(frm, "cam|" + s.last)
        elif w == "leave" and frm in s.watchers: s.watchers.remove(frm)
        elif w == "next" and frm in s.watchers: s.next_asked += 1
        elif w == "cam" and frm == s.host: s.cam = "|".join(L[2:])
        elif w == "end" and frm == s.host: s.host = None; s.cam = None

rg = Region()
you = Av(rg, "Pano", (128, 128, 22), "take12")
ana = Av(rg, "Ana", (130, 127, 22), "take12", friends=["Pano"])
cleo = Av(rg, "Cleo", (127, 126, 22), "take12")              # has Take 12, has not saved you
ben = Av(rg, "Ben", (126, 131, 22), "watch")
far = Av(rg, "Stranger", (168, 128, 22), "watch")
you.camset("<1,2,3>|<4,5,6>|0")
you.share()
check(ana.host == "Pano" and ben.host == "Pano", "a Watch HUD, or Take 12 with you in its Friends, must watch at once")
check(cleo.host is None and cleo.pending == "Pano", "a Take 12 owner who has not saved you must be asked (double-tap), not taken over")
check(far.offer is None, "someone 40 m away was asked")
check(sorted(you.acks) == ["Ana", "Ben", "Cleo (double-tap)"], f"your offer summary: {you.acks}")
check(you.offer is None, "you were asked about your own view")
check(you.watchers == ["Ana", "Ben"], f"watchers: {you.watchers}")
cleo.expire(); cleo.double_tap()
check(cleo.host is None and you.next_asked == 0, "an ignored offer must leave the double-tap free again")
check(ana.cam == "<1,2,3>|<4,5,6>|0" and ben.cam == ana.cam, "a new watcher does not get the view on screen at once")
you.camset("<7,8,9>|<1,1,1>|1.5")
check(ana.cam == ben.cam == "<7,8,9>|<1,1,1>|1.5", "a glide is not followed")
ben.double_tap(); ana.double_tap()
check(you.next_asked == 2, "a watcher's double-tap does not cut for all")
you.share(); cleo.double_tap()
check(cleo.host == "Pano" and "Cleo" in you.watchers, "a double-tap on the offer does not join")
check(cleo.cam == "<7,8,9>|<1,1,1>|1.5", "a late joiner does not get the view on screen")
far.say("Pano", "next")
check(you.next_asked == 2, "someone not watching could cut")
Av(rg, "Mallory", (129, 129, 22), "take12").say("Ana", "cam|<0,0,0>|<0,0,0>|0")
check(ana.cam == "<7,8,9>|<1,1,1>|1.5", "a camera from someone else than the sharer was taken")
ana.key()
check(you.watchers == ["Ben", "Cleo"] and ana.host is None, "a key does not give a watcher their camera back")
you.stop()
check(ben.host is None and cleo.host is None and you.watchers == [], "stopping your camera does not end sharing")
print("share the view: offers reach 20 m only; Watch HUDs and friends watch at once, others on a double-tap; watchers follow cuts and glides; their double-tap cuts for all; "
      "keys release; stopping ends it")
print("sync checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
