# The text above the button (5.8.0): tips.lsl ported, played against a fake HUD - the core's states, the
# sharing block from sync, the lens, the short notices other scripts write, and the clock.
# Status line: every camera says its mode and who is in charge, nothing with your own camera, idle start says so,
# "your view" follows the lens, Photo and pause, the mark follows the menu style, Status line off.
# Sharing: LIVE stacks above the status, watching shows only the 👁 block.
# Notices: another script's text is never overwritten, the status comes back once it is cleared.
# Tips (5.7.0): one per camera, short, under the status line, 20 s apart, each retires after 3 showings, Tips turns
# itself off (all retired, or 24 in all) with one chat line, turning Tips back on starts from zero.
import os, re, math, random

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
src = open(os.path.join(R, "hud", "src", "tips.lsl")).read()
ui = open(os.path.join(R, "hud", "src", "ui.lsl")).read()
core = open(os.path.join(R, "hud", "src", "core.lsl")).read()
sync = open(os.path.join(R, "hud", "src", "sync.lsl")).read()
picker = open(os.path.join(R, "hud", "src", "picker.lsl")).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

def const(name):
    return float(re.search(r'(?:integer|float)\s+' + name + r'\s*=\s*([\d.]+);', src).group(1))
MAXN, ALL, HOLD, LATE, WAIT, GAP = (const(n) for n in ("MAXN", "ALL", "HOLD", "LATE", "WAIT", "GAP"))
def strlist(name):
    return [t.replace("\\n", "\n") for t in re.findall(r'"((?:[^"\\]|\\.)*)"', re.search(r'list ' + name + r' = \[(.*?)\];', src, re.S).group(1))]
TIPS, MODES, NAMES, MARKS = strlist("TIPS"), strlist("MODES"), strlist("NAMES"), strlist("MARKS")
ints = lambda name: [int(v) for v in re.findall(r"-?\d+", re.search(r'list ' + name + r' = \[(.*?)\];', src).group(1))]
LO, HI = ints("LO"), ints("HI")
check(list(zip(LO, HI))[:4] == [(0, 28), (35, 50), (24, 50), (35, 85)], f"the suggested lens ranges: {list(zip(LO, HI))}")

# ---- the wiring --------------------------------------------------------------------------------------------------
check('integer TEXT        = 7380;' in src and 'integer TEXT       = 7380;' in sync, "TEXT 7380 must match in tips and sync")
check('st + "|" + gMode + "|" + (string)gNextCut + "|" + gWhy' in core, "core: UI_STATE must carry why")
check(re.search(r'engage\("scenery"\);\s*if \(gState != ST_IDLE\)\s*\{\s*gWhy = "idle";\s*setUi\("rolling"\);', core) is not None,
      "core: the idle start must say so")
check(re.search(r'gMode = mode;\s*gWhy = "";', core) is not None, "core: every other start must clear why")
check("llSetText(ind()" not in sync, "sync must not write its state itself any more (tips does)")
check("~status=1~" in ui and 'toggle("status", "Status line")' in ui, "ui: Status line on by default, toggled in Look")
check('c == "statusline"' in picker, "/77 statusline on|off missing")

# ---- the text: two short lines, one tip per camera; a second line that stands alone ------------------------------
check(len(TIPS) == 14, f"{len(TIPS)} tips (14 expected)")
for t in TIPS[:11] + TIPS[12:]:
    ls = t.split("\n")
    check(len(ls) == 2 and all(0 < len(l) <= 50 for l in ls), f"tip too long or not two lines: {t!r}")
check(len((TIPS[11] + "10 min: the scenery starts by itself").split("\n")[1]) <= 50, "the idle start tip is too long")
for m in MODES:
    check(f'"{m}"' in core, f"core has no camera '{m}'")
check(MODES == ["scenery", "personal", "social", "friends", "frame", "free"], f"the cameras: {MODES}")
check(NAMES == ["Scenery", "Me", "Us", "Only friends", "Still", "Freehand"], f"the status names must be the menu names: {NAMES}")
for i, word in enumerate(NAMES):
    check(TIPS[i + 1 + 7 * (i == 5)].startswith(word), f"the tip for {MODES[i]} does not start with the menu name {word}")   # Freehand: tip 13
for i in (9, 10):
    check(TIPS[i].split("\n")[0].lower().split()[0] in TIPS[i].split("\n")[1].lower(), f"tip {i}: its second line must stand alone")
mk = dict(re.findall(r'~(\w+)\|[^|]*\|([^|]*)\|', ui))
for m, k in zip(["scenery", "personal", "us", "onlyfr", "frame"], MARKS):
    check(mk.get(m) == k, f"the mark for {m} must be the menu's ({mk.get(m)!r} vs {k!r})")
check('"tips"' in picker and 'cin.tipn", "0"' in picker, "/77 tips on|off missing, or it does not start from zero")

# ---- LSL, the parts that bite --------------------------------------------------------------------------------------
def lsl_index(s, a, b):
    n = len(s); return (a + n if a < 0 else a), (b + n if b < 0 else b)
def llGetSubString(s, a, b):                 # start > end (after negative indices): everything EXCEPT the range between
    a, b = lsl_index(s, a, b)
    return s[max(a, 0):b + 1] if a <= b else s[:b + 1] + s[a:]
def llDeleteSubString(s, a, b):
    a, b = lsl_index(s, a, b)
    return s[:max(a, 0)] + s[b + 1:] if a <= b else s[b + 1:a]
def llSetText(t):                            # Second Life keeps at most 254 bytes
    return t.encode("utf-8")[:254].decode("utf-8", "ignore")
check(llGetSubString("|", 1, -1) == "|" and llDeleteSubString("|", 0, 0) == "", "the LSL model is wrong")

# ---- the script, in Python ----------------------------------------------------------------------------------------
ACTIVE = ("rolling", "frozen", "peek")
class Hud:
    def __init__(s, on="1", n="0", afk_on="1", afk_sec="180", status="1", skin="1"):
        s.lsd = {"tips": on, "tipn": n, "afk_on": afk_on, "afk_sec": afk_sec, "status": status, "skin": skin}
        s.text = ""; s.t = 100.0; s.chat = []; s.log = []; s.gtext = ""; s.rate = 0.0; s.tickT = 0.0
        s.st = ""; s.mode = ""; s.why = ""; s.led = False; s.still = ""; s.kind = ""; s.syncb = ""; s.tip = ""; s.last = ""
        s.want_i = -1; s.wantT = 0; s.showT = 0.0; s.lastT = -100.0
        s.rollT = 0.0; s.more = False; s.sat = False; s.sitting = False; s.lens_tip = False; s.fov = math.radians(60)
        s.clapT = 0.0; s.clapEnd = 0.0; s.claps = []; s.shut = False; s.rnd = random.Random(7)
        s.load()
    def load(s):
        s.on = s.lsd["tips"] != "0"; s.stat = s.lsd["status"] != "0"; s.skin = int(s.lsd["skin"])
        s.n = s.lsd["tipn"].ljust(len(TIPS), "0")
    def seen(s, i): return int(s.n[i])
    def want(s, i):
        if not s.on or s.seen(i) >= MAXN: return
        s.want_i = i; s.wantT = s.t
    def free(s): return s.text in ("", s.last)
    def guide(s):
        name, want, now = (s.still.split("|") + ["", "", ""])[:3]; want, now = int(want or 0), int(now or 0)
        g = f"{name} · {want} mm"
        if abs(now - want) * 100 <= 15 * want: return g + " ✓"
        return g + f" · now {now} · " + ("Ctrl+0" if now < want else "Ctrl+8")
    def lens_txt(s, m):
        n = round(12 / math.tan(s.fov / 2)); lo, hi = LO[m], HI[m]
        return f" · {n} mm" + (f" · try {lo} · Ctrl+0" if n < lo else f" · try {hi} · Ctrl+8" if n > hi else " ✓")
    def line(s):
        if s.mode not in MODES or s.st not in ACTIVE: return ""
        if not s.stat and not (s.mode == "frame" and s.st == "rolling"): return ""
        m = MODES.index(s.mode); n = NAMES[m]; k = MARKS[m]; w = "auto"
        if s.mode == "frame" and s.still: w = s.guide()
        elif s.mode == "frame": w = "held"
        elif s.mode == "friends" and s.led: w = "your view"
        elif s.mode == "scenery" and s.why == "idle": w = "started while you were idle"
        if s.st == "frozen": n, k, w = "Photo", "▣", "held"
        elif s.st == "peek": w = "paused · Esc to carry on"
        elif s.mode != "frame": w += s.lens_txt(m)
        if s.skin: n = k + " " + n
        return n + " · " + w
    def draw(s):
        c = s.text
        if c != "" and c != s.last: return
        L = []
        if s.syncb: L.append(s.syncb)
        if s.kind != "view" and s.line(): L.append(s.line())
        if s.tip: L.append(s.tip)
        t = "\n".join(L)
        if t == s.gtext and c == s.last: return
        s.gtext = t; s.text = llSetText(t); s.last = s.text
    def after(s):                            # the script's tick(): draw, then how often the timer runs (0 = stopped)
        s.draw()
        if s.clapEnd > 0: s.rate = 0.25; return
        s.rate = 0.5 if (s.want_i >= 0 or s.showT > 0 or s.clapT > 0) else (1.0 if (s.last != "" or s.rollT > 0 or s.syncb != "") else 0.0)
    def show(s, i):
        assert s.free(), "a tip over another script's text"
        s.tip = TIPS[i]
        if i == 11:
            sec = int(s.lsd["afk_sec"]); s.tip += (f"{sec // 60} min" if sec % 60 == 0 else f"{sec} s") + ": the scenery starts by itself"
        if s.kind != "view" and s.line(): s.tip = s.tip.split("\n")[1]
        s.showT = s.t; s.lastT = s.t; s.want_i = -1
        s.draw()
        s.n = s.n[:i] + str(s.seen(i) + 1) + s.n[i + 1:]
        s.lsd["tipn"] = s.n
        s.log.append((s.t, i))
        if all(s.seen(k) >= MAXN for k in range(len(s.n))) or sum(map(int, s.n)) >= ALL:
            s.on = False; s.lsd["tips"] = "0"; s.chat.append("Tips are off now · Help › Tips brings them back.")
    def state(s, st, mode="", why=""):
        if st != s.st or (st == "rolling" and mode != s.mode):
            rolling = st == "rolling"; idle = st not in ACTIVE; was = s.st in ACTIVE
            s.tip = ""; s.showT = 0.0
            if s.want_i != 0 or not idle: s.want_i = -1
            if rolling and (not was or mode != s.mode):
                s.rollT = s.t; s.more = False; s.sat = False; s.lens_tip = False
                if mode in MODES: s.want(MODES.index(mode) + 1)
            elif st == "frozen": s.want(6)
            elif st == "peek": s.want(7)
            elif idle and was:
                s.rollT = 0.0
                if s.seen(8) < MAXN: s.want(8)
                elif st == "armed" and s.lsd["afk_on"] == "1": s.want(11)
            s.st = st; s.mode = mode
        s.why = why
        if st != "rolling":
            s.clapT = 0.0
            if s.clapEnd > 0: s.shut = False
            s.clapEnd = 0.0
        elif s.clapT == 0.0: s.clapT = s.t
        if mode != "friends": s.led = False
        s.after()
    def lens(s, dist): s.led = dist > 0; s.after()
    def zoom(s, mm): s.fov = 2 * math.atan(12 / mm); s.after()     # START or FOVMSG: your lens
    def still_msg(s, name, want, fov_deg):    # frame: "<framing>|<mm>|<your mm>", your mm = 12 / tan(FOV / 2), rounded
        s.still = f"{name}|{want}|{round(12 / math.tan(math.radians(fov_deg) / 2))}"; s.after()
    def sharing(s, kind, text):              # sync sends "<kind>|<text>"; parsed exactly as the script does
        msg = kind + "|" + text; i = msg.find("|")
        s.kind = llGetSubString(msg, 0, i - 1) if i > 0 else ""
        s.syncb = llDeleteSubString(msg, 0, i)
        s.after()
    def tick(s):
        now = s.t
        if s.clapEnd > 0 and now >= s.clapEnd: s.clapEnd = 0.0; s.shut = False
        elif s.clapT > 0 and now >= s.clapT:
            s.shut = True; s.claps.append(now); s.clapEnd = now + 0.25; s.clapT = now + 8.0 + s.rnd.random() * 4.0
        if s.showT > 0 and now - s.showT >= HOLD: s.tip = ""; s.showT = 0.0
        if s.rollT > 0 and s.st == "rolling" and s.want_i < 0 and s.showT == 0:
            m = MODES.index(s.mode) if s.mode in MODES else -1
            if not s.lens_tip and 0 <= m < 4 and now - s.lastT >= GAP and not s.lens_txt(m).endswith("✓"):
                s.lens_tip = True; s.want(12)
            elif not s.sat and s.mode == "friends" and s.sitting: s.sat = True; s.want(10)
            elif not s.more and now - s.rollT >= 90: s.more = True; s.want(9)
        if s.want_i >= 0:
            if not s.on or now - s.wantT > WAIT: s.want_i = -1
            elif now - s.wantT >= LATE and now - s.lastT >= GAP and s.free(): s.show(s.want_i)
        s.after()
    def run(s, sec):                         # only a running timer ticks
        for _ in range(int(sec * 4)):
            s.t += 0.25
            if s.rate > 0 and s.t - s.tickT >= s.rate - 1e-9: s.tickT = s.t; s.tick()
    def attach(s): s.want(0); s.after()

# the port matches the script where it matters
for frag in ['if (gWant != 0 || !idle) gWant = -1;', 'if (rolling && (!was || mode != gMode))', 'now - gLastT >= GAP && free()) show(gWant);',
             'if (c != "" && c != gLast) return;', 'gSync = llDeleteSubString(str, 0, i);', 'if (i > 0) gKind = llGetSubString(str, 0, i - 1);',
             'if (t == gText && c == gLast) return;', 'gLast = cur();', 'else if (gLast != "" || gRollT > 0.0 || gSync != "") llSetTimerEvent(1.0);', 'if (gKind != "view" && line() != "") L += [line()];', 'if (done || all >= ALL)',
             'llInsertString(llDeleteSubString(gN, i, i), i, c)', 'else if (!gMore && now - gRollT >= 90.0)',
             'else if (gMode == "scenery" && gWhy == "idle") w = "started while you were idle";',
             'else if (gMode == "friends" && gLed) w = "your view";', 'if (llAbs(now - want) * 100 <= 15 * want) return s + " ✓";',
             'if (now < want) return s + " · now " + (string)now + " · Ctrl+0";', 'if (gMode == "frame" && gStill != "") w = guide();',
             'if (!gStat && !(gMode == "frame" && gSt == "rolling")) return "";', 'else if (gMode != "frame") w += lensTxt(m);',
             'if (n < lo) return s + " · try " + (string)lo + " · Ctrl+0";', 'if (n > hi) return s + " · try " + (string)hi + " · Ctrl+8";',
             'float f = (float)llList2String(llParseStringKeepNulls(str, ["|"], []), num == START);',
             'if (!gLensTip && m >= 0 && m < 4 && now - gLastT >= GAP && llGetSubString(lensTxt(m), -1, -1) != "✓")', 'else if (num == STILL) gStill = str;', 'else if (gSt == "peek") w = "paused · Esc to carry on";',
             'if (gKind != "view" && line() != "") gTip = llList2String(llParseString2List(gTip, ["\\n"], []), 1);']:
    check(frag in src, f"the script changed, the sim must follow: {frag}")

# ---- status line -------------------------------------------------------------------------------------------------
h = Hud(on="0")
h.state("armed"); h.run(2); check(h.text == "", f"your own camera must show nothing: {h.text!r}")
h.state("rolling", "scenery"); h.run(1); check(h.text == "◇ Scenery · auto · 21 mm ✓", f"scenery: {h.text!r}")
for k in range(5): h.state("rolling", "scenery"); h.run(30)                     # every cut repeats the state
check(h.text == "◇ Scenery · auto · 21 mm ✓", f"the status line must stay through the cuts: {h.text!r}")
h.state("frozen", "scenery"); h.run(1); check(h.text == "▣ Photo · held", f"photo: {h.text!r}")
h.state("rolling", "scenery"); h.state("peek", "scenery"); h.run(1)
check(h.text == "◇ Scenery · paused · Esc to carry on", f"paused: {h.text!r}")
h.state("off"); h.run(1); check(h.text == "", "the text must go when your camera is back")
h.state("rolling", "scenery"); h.state("rolling", "scenery", "idle"); h.run(1)
check(h.text == "◇ Scenery · started while you were idle · 21 mm ✓", f"idle start: {h.text!r}")
h.state("off"); h.state("rolling", "personal"); h.run(1); check(h.text == "○ Me · auto · 21 mm · try 35 · Ctrl+0", f"Me: {h.text!r}")
h.state("rolling", "social"); h.run(1); check(h.text == "◎ Us · auto · 21 mm · try 24 · Ctrl+0", f"Us: {h.text!r}")
h.state("rolling", "frame"); h.run(1); check(h.text == "□ Still · held", f"Still: {h.text!r}")
# 5.9: Still's lens guide - the framing, its lens, yours, and what to press (only you can zoom)
h.still_msg("Full length", 50, 60); h.run(1)
check(h.text == "□ Still · Full length · 50 mm · now 21 · Ctrl+0", f"Still at the default zoom: {h.text!r}")
h.still_msg("Full length", 50, 27); h.run(1); check(h.text == "□ Still · Full length · 50 mm ✓", f"Still at 50 mm: {h.text!r}")
h.still_msg("Close", 105, 27); h.run(1); check(h.text == "□ Still · Close · 105 mm · now 50 · Ctrl+0", f"Close at 50 mm: {h.text!r}")
h.still_msg("Half length", 85, 9); h.run(1); check(h.text.endswith("85 mm · now 152 · Ctrl+8"), f"a lens too long: {h.text!r}")
h.still_msg("Half length", 85, 18); h.run(1); check(h.text == "□ Still · Half length · 85 mm ✓", f"within 15 %: {h.text!r}")
h.lsd["status"] = "0"; h.load(); h.run(1); check(h.text == "□ Still · Half length · 85 mm ✓", "the lens guide must show with the status line off")
h.lsd["skin"] = "0"; h.load(); h.run(1); check(h.text == "Still · Half length · 85 mm ✓", f"Plain: {h.text!r}")
h.state("rolling", "social"); h.run(1); check(h.text == "", "status off: nothing outside Still")
h.lsd["status"] = "1"; h.lsd["skin"] = "1"; h.load()
h.state("rolling", "friends"); h.run(1); check(h.text == "♡ Only friends · auto · 21 mm · try 35 · Ctrl+0", f"Only friends: {h.text!r}")
h.lens(2.4); h.run(1); check(h.text == "♡ Only friends · your view · 21 mm · try 35 · Ctrl+0", f"your own view: {h.text!r}")
h.lens(0); h.run(1); check(h.text == "♡ Only friends · auto · 21 mm · try 35 · Ctrl+0", "Release must say auto again")
h.lens(2.4); h.state("rolling", "social"); h.run(1); check(h.text == "◎ Us · auto · 21 mm · try 24 · Ctrl+0", "your view must not follow you out of Only friends")
# the mark follows the menu style; Status line off
h.lsd["skin"] = "0"; h.load(); h.run(1); check(h.text == "Us · auto · 21 mm · try 24 · Ctrl+0", f"Plain must have no mark: {h.text!r}")
h.lsd["status"] = "0"; h.load(); h.run(1); check(h.text == "", "Status line off must hide it")
# ---- 6.0: your lens in every camera (Still keeps its own guide; Photo and pause say nothing about it) ----------------
h = Hud(on="0"); h.state("rolling", "social"); h.zoom(35); h.run(1); check(h.text == "◎ Us · auto · 35 mm ✓", f"Us at 35 mm: {h.text!r}")
h.zoom(105); h.run(1); check(h.text == "◎ Us · auto · 105 mm · try 50 · Ctrl+8", f"Us at 105 mm: {h.text!r}")
h.state("rolling", "friends"); h.run(1); check(h.text == "♡ Only friends · auto · 105 mm · try 85 · Ctrl+8", f"Only friends at 105: {h.text!r}")
h.zoom(85); h.run(1); check(h.text == "♡ Only friends · auto · 85 mm ✓", f"Only friends at 85: {h.text!r}")
h.state("rolling", "scenery"); h.run(1); check(h.text == "◇ Scenery · auto · 85 mm · try 28 · Ctrl+8", f"Scenery at 85: {h.text!r}")
h.zoom(24); h.run(1); check(h.text == "◇ Scenery · auto · 24 mm ✓", f"Scenery at 24: {h.text!r}")
h.state("rolling", "personal"); h.zoom(50); h.run(1); check(h.text == "○ Me · auto · 50 mm ✓", f"Me at 50: {h.text!r}")
h.state("frozen", "personal"); h.run(1); check(h.text == "▣ Photo · held", "Photo must not show the lens")
h.state("rolling", "frame"); h.still_msg("Close", 105, 27); h.run(1); check(h.text == "□ Still · Close · 105 mm · now 50 · Ctrl+0", "Still keeps its own guide")
# the lens tip: once per run, when the run starts outside the camera's range, after the camera's own tip
h = Hud(); h.state("armed"); h.run(30); h.state("rolling", "social"); h.run(40)
check([i for _, i in h.log][-2:] == [3, 12], f"the lens tip must follow the Us tip at 21 mm: {h.log}")
h.run(60); check([i for _, i in h.log].count(12) == 1, "the lens tip must come once per run")
h = Hud(); h.zoom(35); h.state("armed"); h.run(30); h.state("rolling", "social"); h.run(60)
check(12 not in [i for _, i in h.log], "no lens tip when the lens is in range")

# ---- the button: a tiny clap while filming (the sheet's clapped frame), still otherwise --------------------------
ui = open(os.path.join(R, "hud", "src", "ui.lsl")).read()
body = lambda src_, name: re.sub(r"\s+", " ", re.search(name + r"\(integer \w+\)\s*\{(.*?)\n\}", src_, re.S).group(1))
check(body(src, "clap").replace("integer k = 2 * gLook + shut;", "").strip() == body(ui, "frame").strip(),
      "tips' clap must draw the sheet exactly as ui's frame()")
for frag in ('else if (gClapT == 0.0) gClapT = llGetTime();   // the camera rolls: a clap now', 'gClapT = now + 8.0 + llFrand(4.0);',
             'gClapEnd = now + 0.25;', 'if (gClapEnd > 0.0) llSetTimerEvent(0.25);', 'str == "look" || str == "face"'):
    check(frag in src, f"tips: missing {frag}")
h = Hud(on="0"); h.state("armed"); h.run(30); check(h.claps == [], "the button must be still with your own camera")
h.state("rolling", "scenery"); h.run(0.25); check(len(h.claps) == 1 and h.shut, "a clap when the camera starts")
h.run(0.5); check(not h.shut, "the clap must last a quarter of a second")
h.run(60); n = len(h.claps); gaps = [b - a for a, b in zip(h.claps, h.claps[1:])]
check(6 <= n <= 9 and all(7.9 <= g <= 12.6 for g in gaps), f"claps every 8-12 s while filming: {n}, gaps {gaps}")
h.state("frozen", "scenery"); n = len(h.claps); h.run(30); check(len(h.claps) == n and not h.shut, "no clap during Photo")
h.state("rolling", "scenery"); h.run(1); check(len(h.claps) == n + 1, "the clap comes back when filming resumes")
h.state("off"); n = len(h.claps); h.run(30); check(len(h.claps) == n and not h.shut, "still again when your camera is back")

# ---- sharing -----------------------------------------------------------------------------------------------------
h = Hud(on="0"); h.state("rolling", "social"); h.sharing("live", "● LIVE · 2 watching\nAna · Ben"); h.run(1)
check(h.text == "● LIVE · 2 watching\nAna · Ben\n◎ Us · auto · 21 mm · try 24 · Ctrl+0", f"live: {h.text!r}")
h.sharing("", ""); h.run(1); check(h.text == "◎ Us · auto · 21 mm · try 24 · Ctrl+0", "End live must leave the status")
h.state("off"); h.sharing("view", "👁 Pano"); h.run(1); check(h.text == "👁 Pano", f"watching: {h.text!r}")
h.sharing("inv", "Pano invites you · hold to watch"); h.state("rolling", "scenery"); h.run(1)
check(h.text == "Pano invites you · hold to watch\n◇ Scenery · auto · 21 mm ✓", f"invited: {h.text!r}")
h.lsd["status"] = "0"; h.load(); h.sharing("live", "● LIVE · nobody watching yet"); h.run(1)
check(h.text == "● LIVE · nobody watching yet", "Status line off must still show sharing")
# the empty block (sync, nothing shared) shows nothing - the stray "|" of 5.8.0/5.8.1
h = Hud(on="0"); h.sharing("", ""); h.run(2); check(h.text == "", f"an empty sharing block must show nothing: {h.text!r}")
h.state("rolling", "scenery"); h.sharing("", ""); h.run(2); check(h.text == "◇ Scenery · auto · 21 mm ✓", f"empty block + status: {h.text!r}")
# watching, while sync's own notice is up: once it clears, the 👁 line comes back (the timer must not stop)
h = Hud(on="0"); h.state("armed"); h.text = "Watching Pano\ndouble-tap: next for all · any key: your camera"
h.sharing("view", "👁 Pano"); h.run(3); check(h.text.startswith("Watching Pano"), "the notice was overwritten")
h.text = ""; h.run(3); check(h.text == "👁 Pano", f"the 👁 line did not come back after the notice: {h.text!r}")
# over 254 bytes Second Life cuts the text short: it must still be ours, and keep updating
h = Hud(); h.state("rolling", "social")
names = ["Anastasia Featherstonehaugh", "Benedetta Montgomery-Smythe", "Cordelia Vanderbilt-Ashford", "Desdemona Throckmorton"]
h.sharing("live", "● LIVE · 9 watching\n" + " · ".join(n + " (looking around)" for n in names) + " · +5")
h.run(3); n1 = len(h.text.encode())
check(len((h.syncb + h.line() + h.tip).encode()) > 254 and n1 <= 254 and h.text.startswith("● LIVE"), f"the long-text case is not long ({n1} bytes)")
h.run(8); h.sharing("live", "● LIVE · 1 watching\nAna"); h.run(2)
check(h.text == "● LIVE · 1 watching\nAna\n◎ Us · auto · 21 mm · try 24 · Ctrl+0", f"after a cut-short text the composer froze: {h.text!r}")

# ---- other scripts' short notices --------------------------------------------------------------------------------
h = Hud(on="0"); h.state("rolling", "friends"); h.run(1)
h.text = "Your view is kept · Esc to continue"; h.lens(2.0); h.run(3)
check(h.text == "Your view is kept · Esc to continue", "the status overwrote the lens notice")
h.text = ""; h.run(1); check(h.text == "♡ Only friends · your view · 21 mm · try 35 · Ctrl+0", f"the status did not come back: {h.text!r}")
h.text = "Ana watches"; h.state("frozen", "friends"); h.run(2); check(h.text == "Ana watches", "a state change overwrote a notice")
h.text = ""; h.run(1); check(h.text == "▣ Photo · held", "the status did not come back after the notice")
# ---- tips --------------------------------------------------------------------------------------------------------
# 1. worn: the hello tip, through the start-up states; gone after 6 s
h = Hud(); h.attach(); h.state("armed"); h.run(2)
check(h.log and h.log[-1][1] == 0 and h.text.startswith("Take 12"), "no hello tip when worn")
h.run(6); check(h.text == "", "the hello tip did not go away")
# 2. a camera starts: its tip under the status line; Photo and back is not a new start; a stop gives the back tip
h.run(30); h.state("rolling", "scenery"); h.run(2)
check(h.text == "◇ Scenery · auto · 21 mm ✓\n" + TIPS[1].split("\n")[1], f"the Scenery tip must sit under the status: {h.text!r}")
h.run(7); check(h.text == "◇ Scenery · auto · 21 mm ✓", "the tip did not go away, or the status went with it")
h.run(13); h.state("frozen", "scenery"); h.run(2); check(h.text == "▣ Photo · held\n" + TIPS[6].split("\n")[1], f"Photo: {h.text!r}")
h.run(20); h.state("rolling", "scenery"); h.run(2); check(h.text == "◇ Scenery · auto · 21 mm ✓", "resuming a Photo must not tip the camera again")
h.run(20); h.state("armed"); h.run(2); check(h.text.startswith("Your camera is back\n"), f"no back tip: {h.text!r}")
# 3. two events close together: the second waits for the 20 s gap, and is dropped after 10 s
h.run(30); n0 = len(h.log); h.state("rolling", "personal"); h.run(5); h.state("off"); h.run(12)
check(len(h.log) == n0 + 1 and h.log[-1][1] == 2, "the back tip came too soon after the Me tip, or Me was missing")
check(h.seen(8) == 1, "a dropped tip was counted")
# 4. a notice on screen holds the tip back: dropped after 10 s, not counted
h.run(30); n0 = len(h.log); c3 = h.seen(3); h.state("rolling", "social"); h.text = "Looking for people near you…"; h.run(15)
check(len(h.log) == n0 and h.seen(3) == c3 and h.text.startswith("Looking"), "a tip covered another script's notice")
h.text = ""
# 5. the tip leaves a notice that replaced it alone
h.run(30); h.state("armed"); h.state("rolling", "frame"); h.run(2); check(h.text.endswith(TIPS[5].split("\n")[1]), "no Still tip")
h.text = "Half length"; h.run(8); check(h.text == "Half length", "the tip cleared Still's framing name")
h.text = ""
# 6. 90 s rolling: the Hold > More tip; sitting in Only friends: W/S
h.run(30); h.state("armed"); h.run(30); h.zoom(50); h.state("rolling", "friends"); h.run(30); h.sitting = True; h.run(5)
check(h.log[-1][1] == 10, "no sitting tip in Only friends")
h.sitting = False; h.run(90); check(h.log[-1][1] == 9, "no Hold › More tip after 90 s")
# 7. each tip retires after 3 showings; Tips turns itself off after 24, with one chat line
h = Hud(n="0" * 12)
for k in range(40):
    h.state("armed"); h.run(25); h.state("rolling", MODES[k % 5]); h.run(25); h.state("frozen", MODES[k % 5]); h.run(25)
    h.state("rolling", MODES[k % 5]); h.run(25); h.state("peek", MODES[k % 5]); h.run(25)
check(max(map(int, h.n)) <= MAXN, f"a tip showed more than {MAXN} times: {h.n}")
check(not h.on and h.lsd["tips"] == "0" and sum(map(int, h.n)) == ALL, f"Tips did not turn off after {ALL}: {h.n}")
check(len(h.chat) == 1, f"the off line must be said once: {h.chat}")
n0 = len(h.log); h.state("armed"); h.run(30); h.state("rolling", "scenery"); h.run(30)
check(len(h.log) == n0 and h.text == "◇ Scenery · auto · 21 mm ✓", "a tip showed while Tips is off, or the status went with them")
# 8. idle start tip once the back tip has retired, with the user's own time
h = Hud(n="000000003000", afk_sec="300"); h.state("rolling", "scenery"); h.run(30); h.state("armed"); h.run(3)
check(h.text == "Idle start\nstay idle 5 min: the scenery starts by itself", f"idle start tip: {h.text!r}")
# 9. back on from the menu or /77: every tip from zero
h = Hud(on="0", n="333333333333")
h.lsd["tipn"] = "0"; h.lsd["tips"] = "1"; h.load(); h.state("rolling", "scenery"); h.run(3)
check(h.on and h.text.endswith(TIPS[1].split("\n")[1]), "Tips back on did not start from zero")

print(f"above the button: a status line for {len(MODES)} cameras, Photo and pause; sharing on top; notices respected; "
      f"{len(TIPS)} tips, each at most {int(MAXN)} times, {int(GAP)} s apart, {int(HOLD)} s on screen, off after {int(ALL)}")
print("text checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
