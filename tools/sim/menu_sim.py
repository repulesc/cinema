# The menus (6.1.0: the free Take 12 Scenery build hides the other cameras and sharing, and shows More cameras;
# 5.6.0, 5.7.0: Symbols by default, Help > Read Me / Tips): Scenery / Me / Us / Still on the main page, Pace and Idle start under Options > Timing, the camera
# settings under Options > Camera, the menu style (Plain / Symbols / Color) under Options > Look. Ported from
# ui.lsl: every page fits a dialog (12 buttons), every button has a name, Back goes to the page above, and in
# every menu style the labels on a page are distinct (a choice is matched back by its label).
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ui = open(os.path.join(R, "hud", "src", "ui.lsl")).read()
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
# what each build hides (locked): the full Take 12 only "More cameras"; Take 12 Scenery the other cameras and sharing
lk = ui[ui.index("integer locked(string id)"):]
hide_full = set(re.findall(r'if \(!LITE\) return \(id == "(\w+)"\);', lk[:300]))
hide_free = set(re.findall(r'"(\w+)"', re.search(r'return \(llListFindList\(\[(.*?)\], \[id\]\)', lk).group(1)))
check(hide_full == {"full"}, f"the full build must hide only More cameras: {hide_full}")
check(hide_free >= {"personal", "us", "frame", "share", "favs", "save", "modes"} and not hide_free & {"scenery", "photo", "next", "stop", "opts",
      "timing", "pace", "afk", "camcfg", "indoors", "reach", "look", "help", "readme", "tips", "full", "back", "close"}, f"Take 12 Scenery hides {hide_free}")
check(all(i in items for i in hide_free | hide_full), "a hidden id is not a menu item")
check("ids = b;" in ui[ui.index("list order(list ids)"):ui.index("list order(list ids)") + 400] and "if (!locked(" in ui, "order() must leave out what the build hides")
shown = lambda p, hide: [i for i in pages.get(p, []) if i not in hide]
check(shown("main", hide_full) == ["scenery", "personal", "us", "frame", "share", "opts", "help", "close"], f"main menu: {shown('main', hide_full)}")
check(shown("main", hide_free) == ["scenery", "opts", "full", "help", "close"], f"Take 12 Scenery main menu: {shown('main', hide_free)}")
check(shown("live", hide_free) == ["photo", "next", "stop", "close"] or set(shown("live", hide_free)) == {"photo", "resume", "next", "stop", "close"},
      f"Take 12 Scenery live menu: {shown('live', hide_free)}")
check(pages.get("us") == ["everyone", "onlyfr", "flist", "back"], f"Us page: {pages.get('us')}")
check(pages.get("opts") == ["timing", "camcfg", "look", "favs", "test", "reset", "back"], f"Options: {pages.get('opts')}")
check(pages.get("help") == ["readme", "tips", "back"], f"Help: {pages.get('help')}")
check(pages.get("timing") == ["pace", "afk", "back"], f"Timing: {pages.get('timing')}")
check(set(pages.get("camcfg", [])) >= {"seat", "indoors", "reach", "altcam", "chat", "phantom", "back"}, f"Camera: {pages.get('camcfg')}")
check(pages.get("look", [])[:3] == ["sk0", "sk1", "sk2"] and "stline" in pages.get("look", []), f"Look: {pages.get('look')}")
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
check(up.get("help", "main") == "main", "Help must go back to the main menu")
# the default style is Symbols (the settings step 7 moves the 5.6 Plain default over; a later choice of Plain stays)
check("~skin=1~" in ui and 'if (cfgGet("skin") == "0") cfgWrite("skin", "1");' in ui and "if (v < 7)" in ui, "the menus must default to Symbols")
check("gSkin = 1;" in ui[ui.index('gPage == "reset"'):], "Reset must go back to Symbols")
# Tips: on by default and after the step, and turning them back on starts every tip from zero
check("~tips=1~tipn=0~" in ui and 'cfgWrite("tips", "1");' in ui, "Tips must be on by default")
hp = ui[ui.index('gPage == "help"'):]
check(hp.index('cfgWrite("tipn", "0")') < hp.index('toggle("tips"'), "turning Tips on must reset the counts")
# Seated view: each button saves its own angle (4.8.0-5.8.1 saved the next one: Off was Auto, Lower deleted the key)
m = re.search(r'cfgSet\("seat_deg", llList2String\(\[(.*?)\], llListFindList\(\[(.*?)\], \[id\]\)( \+ 1)?\)\);', ui)
vals, ids = re.findall(r'"(\w*)"', m.group(1)), re.findall(r'"(\w*)"', m.group(2))
off = 1 if m.group(3) else 0
saved = {i: (vals[ids.index(i) + off] if ids.index(i) + off < len(vals) else "") for i in ids}
check(saved == {"off": "0", "auto": "45", "high": "60", "low": "30"}, f"Seated view saves {saved}")
# a click is matched against the labels shown (a menu style changed by chat while a menu is open still works)
check("gLbl = b;" in ui and "llListFindList(gLbl, [msg])" in ui, "idOf must look the click up in the labels on screen")
# the Pick page (picker): a saved friend's label, "✓ " + the username, stays within llDialog's 24 bytes
pk = open(os.path.join(R, "hud", "src", "picker.lsl")).read()
m = re.search(r'string nm = llGetSubString\(llGetUsername\(pk\), 0, (\d+)\);\s*if \(llListFindList\(gFKeys, \[pk\]\) >= 0\) nm = "✓ " \+ llGetSubString\(nm, 0, (\d+)\);', pk)
check(m is not None, "picker: the Pick label is not built as expected")
if m:
    u = "a" * 31                                                          # usernames: up to 31 ASCII characters
    plain, saved_l = u[:int(m.group(1)) + 1], "✓ " + u[:int(m.group(1)) + 1][:int(m.group(2)) + 1]
    check(len(plain.encode()) <= 24 and len(saved_l.encode()) <= 24, f"Pick labels: {len(plain.encode())} / {len(saved_l.encode())} bytes (24 max)")
print(f"menus: {len(pages)} pages, {len(items)} named buttons, all fit, distinct in Plain / Symbols / Color, Back goes up")
print("menu checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
