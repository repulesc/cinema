# Tips (5.7.0): cinema_tips.lsl ported, played against a fake HUD - the core's states, the hover text the other
# scripts write, and the clock. Checks: a tip for each camera, two short lines, shown only on a free moment and never
# over another script's text, 20 s apart, each retires after 3 showings, Tips turns itself off (all retired, or 24 in
# all) with one chat line, and turning Tips back on starts from zero.
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
src = open(os.path.join(R, "hud", "src", "cinema_tips.lsl")).read()
ui = open(os.path.join(R, "hud", "src", "cinema_ui.lsl")).read()
core = open(os.path.join(R, "hud", "src", "cinema_core.lsl")).read()
picker = open(os.path.join(R, "hud", "src", "cinema_picker.lsl")).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

def const(name):
    return float(re.search(r'(?:integer|float)\s+' + name + r'\s*=\s*([\d.]+);', src).group(1))
MAXN, ALL, HOLD, LATE, WAIT, GAP = (const(n) for n in ("MAXN", "ALL", "HOLD", "LATE", "WAIT", "GAP"))
TIPS = [t.replace("\\n", "\n") for t in re.findall(r'"((?:[^"\\]|\\.)*)"', re.search(r'list TIPS = \[(.*?)\];', src, re.S).group(1))]
MODES = re.findall(r'"(\w+)"', re.search(r'list MODES = \[(.*?)\];', src).group(1))

# ---- the text: two short lines, one tip per camera ---------------------------------------------------------------
check(len(TIPS) == 12, f"{len(TIPS)} tips (12 expected)")
for t in TIPS[:11]:
    ls = t.split("\n")
    check(len(ls) == 2 and all(0 < len(l) <= 50 for l in ls), f"tip too long or not two lines: {t!r}")
check(len((TIPS[11] + "10 min: the scenery starts by itself").split("\n")[1]) <= 50, "the idle start tip is too long")
for m in MODES:
    check(f'engage("{m}")' in core or f'"{m}"' in core, f"core has no camera '{m}'")
check(MODES == ["scenery", "personal", "social", "friends", "frame"], f"the cameras: {MODES}")
for i, word in enumerate(["Scenery", "Me", "Us", "Only friends", "Still"]):
    check(TIPS[i + 1].startswith(word), f"the tip for {MODES[i]} does not start with the menu name {word}")
check('"tips"' in picker and 'cin.tipn", "0"' in picker, "/77 tips on|off missing, or it does not start from zero")

# ---- the script, in Python ----------------------------------------------------------------------------------------
class Hud:
    def __init__(s, on="1", n="0", afk_on="1", afk_sec="180"):
        s.lsd = {"tips": on, "tipn": n, "afk_on": afk_on, "afk_sec": afk_sec}
        s.text = ""; s.t = 100.0; s.chat = []; s.log = []
        s.st = ""; s.mode = ""; s.want_i = -1; s.wantT = 0; s.shown = ""; s.showT = 0.0; s.lastT = -100.0
        s.rollT = 0.0; s.more = False; s.sat = False; s.sitting = False
        s.load()
    def load(s):
        s.on = s.lsd["tips"] != "0"
        s.n = s.lsd["tipn"].ljust(len(TIPS), "0")
    def seen(s, i): return int(s.n[i])
    def want(s, i):
        if not s.on or s.seen(i) >= MAXN: return
        s.want_i = i; s.wantT = s.t
    def clear(s):
        if s.showT > 0 and s.text == s.shown: s.text = ""
        s.showT = 0.0
    def show(s, i):
        assert s.text == "", "a tip over another script's text"
        s.shown = TIPS[i]
        if i == 11:
            sec = int(s.lsd["afk_sec"]); s.shown += (f"{sec // 60} min" if sec % 60 == 0 else f"{sec} s") + ": the scenery starts by itself"
        s.text = s.shown; s.showT = s.t; s.lastT = s.t; s.want_i = -1
        s.n = s.n[:i] + str(s.seen(i) + 1) + s.n[i + 1:]
        s.lsd["tipn"] = s.n
        s.log.append((s.t, i))
        if all(s.seen(k) >= MAXN for k in range(len(s.n))) or sum(map(int, s.n)) >= ALL:
            s.on = False; s.lsd["tips"] = "0"; s.chat.append("Tips are off now · Help › Tips brings them back.")
    def state(s, st, mode=""):
        if not (st != s.st or (st == "rolling" and mode != s.mode)): return
        rolling = st == "rolling"; idle = st not in ("rolling", "frozen", "peek"); was = s.st in ("rolling", "frozen", "peek")
        s.clear()
        if s.want_i != 0 or not idle: s.want_i = -1
        if rolling and (not was or mode != s.mode):
            s.rollT = s.t; s.more = False; s.sat = False
            if mode in MODES: s.want(MODES.index(mode) + 1)
        elif st == "frozen": s.want(6)
        elif st == "peek": s.want(7)
        elif idle and was:
            s.rollT = 0.0
            if s.seen(8) < MAXN: s.want(8)
            elif st == "armed" and s.lsd["afk_on"] == "1": s.want(11)
        s.st = st; s.mode = mode
    def tick(s):
        now = s.t
        if s.showT > 0 and now - s.showT >= HOLD: s.clear()
        if s.rollT > 0 and s.st == "rolling" and s.want_i < 0 and s.showT == 0:
            if not s.sat and s.mode == "friends" and s.sitting: s.sat = True; s.want(10)
            elif not s.more and now - s.rollT >= 90: s.more = True; s.want(9)
        if s.want_i >= 0:
            if not s.on or now - s.wantT > WAIT: s.want_i = -1
            elif now - s.wantT >= LATE and now - s.lastT >= GAP and s.text == "": s.show(s.want_i)
    def run(s, sec):
        for _ in range(int(sec * 2)):
            s.t += 0.5; s.tick()
    def attach(s):
        s.want(0)

# the port matches the script where it matters
for frag in ['if (gWant != 0 || !idle) gWant = -1;', 'if (rolling && (!was || mode != gMode))', 'cur() == "") show(gWant)',
             'if (gShowT > 0.0 && cur() == gShown) llSetText("", ZERO_VECTOR, 0.0);', 'if (done || all >= ALL)',
             'llInsertString(llDeleteSubString(gN, i, i), i, c)', 'else if (!gMore && now - gRollT >= 90.0)']:
    check(frag in src, f"the script changed, the sim must follow: {frag}")

# 1. worn: the hello tip, through the start-up states; gone after 6 s
h = Hud(); h.attach(); h.state("armed"); h.run(2)
check(h.log and h.log[-1][1] == 0 and h.text.startswith("Take 12"), "no hello tip when worn")
h.run(6); check(h.text == "", "the hello tip did not go away")
# 2. a camera starts: its tip; Photo and back is not a new start; a stop gives the back tip (20 s apart)
h.run(30); h.state("rolling", "scenery"); h.run(2)
check(h.text.startswith("Scenery"), f"no Scenery tip: {h.text!r}")
h.run(20); h.state("frozen", "scenery"); h.run(2); check(h.text.startswith("Photo"), "no Photo tip")
h.run(20); h.state("rolling", "scenery"); h.run(2); check(h.text == "", "resuming a Photo must not tip the camera again")
h.run(20); h.state("armed"); h.run(2); check(h.text.startswith("Your camera is back"), "no back tip")
# 3. two events close together: the second waits for the 20 s gap, and is dropped after 10 s
h.run(30); n0 = len(h.log); h.state("rolling", "personal"); h.run(5); h.state("off"); h.run(12)
check(len(h.log) == n0 + 1 and h.log[-1][1] == 2, "the back tip came too soon after the Me tip, or Me was missing")
check(h.seen(8) == 1, "a dropped tip was counted")
# 4. never over another script's text: LIVE status stays, the tip is dropped and not counted
h.run(30); h.text = "● LIVE · 2 watching\nAna · Ben"; n0 = len(h.log); c3 = h.seen(3)
h.state("rolling", "social"); h.run(15)
check(len(h.log) == n0 and h.text.startswith("● LIVE") and h.seen(3) == c3, "a tip covered the LIVE status")
h.text = ""
# 5. the tip clears only its own text: a notice that replaced it stays
h.run(30); h.state("armed"); h.state("rolling", "frame"); h.run(2); check(h.text.startswith("Still"), "no Still tip")
h.text = "Half length"; h.run(8); check(h.text == "Half length", "the tip cleared Still's framing name")
h.text = ""
# 6. 90 s rolling: the Hold > More tip; sitting in Only friends: W/S
h.run(30); h.state("armed"); h.run(30); h.state("rolling", "friends"); h.run(30); h.sitting = True; h.run(5)
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
check(len(h.log) == n0, "a tip showed while Tips is off")
# 8. idle start tip once the back tip has retired, with the user's own time
h = Hud(n="000000003000", afk_sec="300"); h.state("rolling", "scenery"); h.run(30); h.state("armed"); h.run(3)
check(h.text == "Idle start\nstay idle 5 min: the scenery starts by itself", f"idle start tip: {h.text!r}")
# 9. back on from the menu or /77: every tip from zero
h = Hud(on="0", n="333333333333")
h.lsd["tipn"] = "0"; h.lsd["tips"] = "1"; h.load(); h.state("rolling", "scenery"); h.run(3)
check(h.on and h.text.startswith("Scenery"), "Tips back on did not start from zero")

print(f"tips: {len(TIPS)} tips, each at most {int(MAXN)} times, {int(GAP)} s apart, {int(HOLD)} s on screen, off after {int(ALL)}")
print("tips checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
