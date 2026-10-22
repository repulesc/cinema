# The menus (5.6.0): Scenery / Me / Us / Still on the main page, Pace and Idle start under Options > Timing, the camera
# settings under Options > Camera, the menu style (Plain / Symbols / Color) under Options > Look. Ported from
# cinema_ui.lsl: every page fits a dialog (12 buttons), every button has a name, Back goes to the page above, and in
# every menu style the labels on a page are distinct (a choice is matched back by its label).
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ui = open(os.path.join(R, "hud", "src", "cinema_ui.lsl")).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

items = {}
for e in re.search(r'string ITEMS = "(.*?)";', ui).group(1).strip("~").split("~"):
    i, em, mk, t = e.split("|")
    items[i] = (em, mk, t)
def label(i, skin):
    if i not in items: return i
    em, mk, t = items[i]
    m = mk if skin == 1 else em
    return t if skin == 0 or m == "" else m + " " + t

# the pages and their buttons, as openMenu builds them
body = ui[ui.index("openMenu(string page)"):ui.index("toggle(string k")]
pages = {}
for m in re.finditer(r'page == "(\w+)"\)\s*\{(.*?)\n    \}', body, re.S):
    bl = re.findall(r'b (?:\+)?= \[(.*?)\];', m.group(2))
    ids = []
    for x in bl: ids += re.findall(r'"([^"]*)"', x)
    pages[m.group(1)] = ids
check(pages.get("main") == ["scenery", "personal", "us", "frame", "share", "opts", "help", "close"], f"main menu: {pages.get('main')}")
check(pages.get("us") == ["everyone", "onlyfr", "flist", "back"], f"Us page: {pages.get('us')}")
check(pages.get("opts") == ["timing", "camcfg", "look", "favs", "test", "reset", "back"], f"Options: {pages.get('opts')}")
check(pages.get("timing") == ["pace", "afk", "back"], f"Timing: {pages.get('timing')}")
check(set(pages.get("camcfg", [])) >= {"seat", "indoors", "reach", "altcam", "chat", "phantom", "back"}, f"Camera: {pages.get('camcfg')}")
check(pages.get("look", [])[:3] == ["sk0", "sk1", "sk2"], f"Look: {pages.get('look')}")
for p, ids in pages.items():
    check(len(ids) <= 12, f"{p}: {len(ids)} buttons (a dialog holds 12)")
    for i in ids:
        check(i in items, f"{p}: '{i}' has no name in ITEMS")
    for skin in (0, 1, 2):
        labels = [label(i, skin) for i in ids]
        check(len(set(labels)) == len(labels), f"{p}, style {skin}: two buttons look the same: {labels}")
        check(all(len(l.encode('utf-8')) <= 24 for l in labels), f"{p}, style {skin}: a label is longer than 24 bytes")
# names on the main page: plain words, the ones people asked for
check([label(i, 0) for i in pages["main"][:4]] == ["Scenery", "Me", "Us", "Still"], "the mode names are not Scenery / Me / Us / Still")
check(all(not re.search(r"[\U0001F300-\U0001FAFF]", label(i, 0) + label(i, 1)) for i in items), "Plain or Symbols shows a colour emoji")
# Back goes to the page above
up = {}
for grp, parent in re.findall(r'llSubStringIndex\("~([\w~]+)~", "~" \+ p \+ "~"\) >= 0\) return "(\w+)";', ui):
    for p in grp.split("~"): up[p] = parent
check(up.get("pace") == "timing" and up.get("afk") == "timing", "Pace / Idle start must go back to Timing")
check(all(up.get(p) == "camcfg" for p in ("seat", "indoors", "reach", "altcam", "chat")), "camera settings must go back to Camera")
check(all(up.get(p) == "opts" for p in ("timing", "camcfg", "look", "favs", "reset")), "Options groups must go back to Options")
# the default style is Plain, for everyone (the settings step 6)
check("~skin=0~" in ui and 'cfgWrite("skin", "0");' in ui and "if (v < 6)" in ui, "the menus must default to Plain")
print(f"menus: {len(pages)} pages, {len(items)} named buttons, all fit, distinct in Plain / Symbols / Color, Back goes up")
print("menu checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
