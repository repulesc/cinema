# Guards the Lite build: hud-lite/src must be hud/src with ONLY the LITE switch (and the notecard name) changed,
# the generated header added, and every id the UI locks must be a real menu item (so a lock can't go stale).
import os, re, difflib
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)
for n in ("cinema_core.lsl", "cinema_ui.lsl", "cinema_scenery.lsl"):
    full, lite = rd("hud", "src", n).splitlines(), rd("hud-lite", "src", n).splitlines()
    check(lite[0].startswith("// *** LITE BUILD"), f"{n}: generated header missing")
    expect = []
    for l in full:                                   # the full source with only the two documented substitutions
        if l.startswith("integer LITE    = 0;"): l = l.replace("= 0;", "= 1;", 1)
        if n == "cinema_ui.lsl" and l.startswith('string NOTECARD = "Take 12 - Read Me";'): l = l.replace("Take 12 - Read Me", "Take 12 Lite - Read Me", 1)
        expect.append(l)
    check(lite[1:] == expect, f"{n}: differs from the full source beyond the LITE switch / notecard name")
ui = rd("hud", "src", "cinema_ui.lsl")
locked = re.search(r'return \(llListFindList\(\[(.*?)\], \[id\]\)', ui).group(1)
ids = re.findall(r'"(\w+)"', locked)
items = set(re.findall(r'"(\w+)", "[^"]*", "[^"]+"', ui[ui.index("list ITEMS"):ui.index("list PACE_IDS")]))
for i in ids: check(i in items, f"locked id '{i}' is not a menu item")
for must in ("personal", "social", "friends", "save", "look"): check(must in ids, f"'{must}' should be locked in Lite")
for free in ("scenery", "photo", "next", "stop", "pace", "afk", "altcam", "reach", "emoji", "fade", "th0"): check(free not in ids, f"'{free}' must stay available in Lite")
print(f"lite: {len(ids)} locked items, 3 generated scripts match the full source")
print("lite checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
