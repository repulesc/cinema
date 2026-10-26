# The menus (7.0.0: one product). The main page has six doors: Framing, Freehand, Connect, Scenery, Format,
# Settings (and Help, Close; the free Take 12 Scenery: Scenery, Settings, More cameras, Help, Close). 7.1: Framing
# starts the last one used at once (Me the first time); the live menu switches Me / Us / Friends and has Adjust, and
# leaves Next out when the keys strip (which has it) is linked; Scenery its own settings (idle start, indoors, reach); Settings: Pace, Look, Camera, Test cam,
# Reset. One quiet menu style (a mark and a word). Ported from ui.lsl: every page fits a dialog (12 buttons), every
# button has a name, Back goes to the page above, the labels on a page are distinct and fit 24 bytes.
import os, re

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ui = open(os.path.join(R, "hud", "src", "ui.lsl")).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

items = {}
for e in re.search(r'string ITEMS = "(.*?)";', ui).group(1).strip("~").split("~"):
    i, mk, t = e.split("|")
    items[i] = (mk, t)
def label(i):
    if i not in items: return i
    mk, t = items[i]
    return t if mk == "" else mk + " " + t

# the pages and their buttons, as openMenu builds them
body = ui[ui.index("openMenu(string page)"):ui.index("toggle(string k")]
pages = {}
for m in re.finditer(r'page == "(\w+)"\)\s*\{(.*?)\n    \}', body, re.S):
    bl = re.findall(r'b (?:\+)?= \[(.*?)\];', m.group(2))
    ids = []
    for x in bl: ids += re.findall(r'"([^"]*)"', x)
    pages[m.group(1)] = ids
# what each build hides (locked): the full Take 12 only "More cameras"; Take 12 Scenery all but the scenery camera
lk = ui[ui.index("integer locked(string id)"):]
hide_full = set(re.findall(r'if \(!LITE\) return \(id == "(\w+)"\);', lk[:300]))
hide_free = set(re.findall(r'"(\w+)"', re.search(r'return \(llListFindList\(\[(.*?)\], \[id\]\)', lk).group(1)))
check(hide_full == {"full"}, f"the full build must hide only More cameras: {hide_full}")
check(hide_free >= {"framing", "free", "share", "crop", "save", "modes", "release", "me", "us", "friends", "flist", "adjust"} and not hide_free & {"scenery", "start", "next", "stop", "opts",
      "pace", "afk", "camcfg", "indoors", "reach", "look", "help", "readme", "tips", "full", "back", "close"}, f"Take 12 Scenery hides {hide_free}")
check(all(i in items for i in hide_free | hide_full), "a hidden id is not a menu item")
check("ids = b;" in ui[ui.index("list order(list ids)"):ui.index("list order(list ids)") + 400] and "if (!locked(" in ui, "order() must leave out what the build hides")
shown = lambda p, hide: [i for i in pages.get(p, []) if i not in hide]
# ---- the shape of the product ----------------------------------------------------------------------------------
check(shown("main", hide_full) == ["framing", "free", "share", "scenery", "crop", "opts", "help", "close"], f"main menu: {shown('main', hide_full)}")
check([label(i) for i in shown("main", hide_full)[:6]] == ["○ Framing", "✥ Freehand", "⇄ Connect", "◇ Scenery", "◰ Format", "≡ Settings"],
      f"the six doors: {[label(i) for i in shown('main', hide_full)]}")
check(shown("main", hide_free) == ["scenery", "opts", "full", "help", "close"], f"Take 12 Scenery main menu: {shown('main', hide_free)}")
check("framing" not in pages, "7.1: no Framing page, the door starts a camera")
check('if (id == "framing") id = cfgGet("fwho");' in ui and 'if (id == "") id = "frame";' in ui
      and 'cfgGet("fwho") != gUiMode) cfgWrite("fwho", gUiMode);' in ui, "ui: Framing starts the last one used (Me the first time)")
check(pages.get("scenery") == ["start", "afk", "indoors", "reach", "sfmt", "back"], f"Scenery: {pages.get('scenery')}")
check('else if (id == "sfmt") { closeMenu(); llMessageLinked(LINK_SET, CMD, "cropsc", ""); }' in ui, "ui: Scenery > Format opens Scenery's own Format (7.2)")
check(pages.get("opts") == ["pace", "look", "camcfg", "test", "reset", "back"], f"Settings: {pages.get('opts')}")
check(pages.get("camcfg") == ["seat", "altcam", "chat", "phantom", "back"], f"Camera: {pages.get('camcfg')}")
check(pages.get("look") == ["th0", "th1", "th2", "stline", "size", "trace", "back"], f"Look: {pages.get('look')}")
check(pages.get("help") == ["readme", "tips", "back"], f"Help: {pages.get('help')}")
check(shown("live", hide_full) == ["save", "me", "us", "friends", "adjust", "showme", "flist", "release", "next", "stop", "share", "modes", "close"], f"live menu: {shown('live', hide_full)}")
# per camera (the page's branches): Freehand, Me / Us, Friends, each one dialog
def live_for(mode, strip=False):
    fr = mode in ("frame", "social", "friends")
    b = (["save"] if mode == "free" else []) + (["me", "us", "friends"] if fr else []) + (["adjust"] if fr or mode == "free" else [])
    b += ["showme"] if fr else []
    b += ["flist", "release"] if mode == "friends" else []
    b += ["next"] if mode == "scenery" or not strip else []
    return b + ["stop", "share", "modes", "close"]
LIVE_MAX = max(len(live_for(m)) for m in ("free", "frame", "social", "friends", "scenery"))
check(LIVE_MAX <= 12 and len(live_for("friends")) == 12, f"each live menu fits a dialog: {[len(live_for(m)) for m in ('free', 'frame', 'social', 'friends', 'scenery')]}")
check('if (fr) b += ["showme"];' in ui and '|| id == "showme") llMessageLinked(LINK_SET, CMD, id, "");' in ui and "~showme||Show me~" in ui, "ui: Show me in the Framing live menus (7.2)")
lv = ui[ui.index('else if (page == "live")'):ui.index('else if (page == "pace")')]
check('if (fr) b += ["me", "us", "friends"];' in lv and 'if (fr || gUiMode == "free") b += ["adjust"];' in lv and 'if (gUiMode == "scenery" || !strip()) b += ["next"];' in lv,
      "ui: the live menu: Me / Us / Friends in Framing, Adjust in Framing and Freehand, Next only without the keys strip (and in Scenery)")
check('if (llGetLinkName(i) == "Take 12 keys") return TRUE;' in ui, "ui: the keys strip is found by its name (keys.lsl names it)")
check(all(f'"{x}"' in lv for x in ("save", "flist", "release")), "the live menu has Save, the Friends list and Release")
check('return "● " + llList2String(p, 1);' in ui, "ui: the camera running and Adjust on carry a dot in the live menu")
check(shown("live", hide_free) == ["next", "stop", "close"], f"Take 12 Scenery live menu: {shown('live', hide_free)}")
# 7.0 cuts: no Photo, no menu styles, no Scenery favourites
for gone in ("photo", "resume", "sk0", "sk1", "sk2", "favs", "here", "timing", "personal", "frame", "everyone", "onlyfr"):
    check(gone not in items, f"'{gone}' is gone in 7.0")
check("gSkin" not in ui and "cfgSet(\"skin\"" not in ui, "ui: one menu style")
# Framing's three: Me runs the Framing composer (frame), Us people (social), Friends friends
check('llList2String(["frame", "social", "friends"], llListFindList(["me", "us", "friends"], [id]))' in ui, "ui: Framing › Me / Us / Friends start frame / social / friends")
check('if (id == "start") { closeMenu(); llMessageLinked(LINK_SET, CMD, "scenery", ""); }' in ui, "ui: Scenery › Start")
check('if (id == "free" || id == "share" || id == "crop" || id == "frame" || id == "social" || id == "friends")' in ui, "ui: Framing, Freehand, Connect and Format start from the main menu")
# ---- every page fits, every button has a name, labels distinct and within 24 bytes ----------------------------------
for p, ids in pages.items():
    check(len(ids) <= 12 or p == "live", f"{p}: {len(ids)} buttons (a dialog holds 12)")   # live: per camera, above
    for i in ids:
        check(i in items, f"{p}: '{i}' has no name in ITEMS")
    labels = [label(i) for i in ids]
    check(len(set(labels)) == len(labels), f"{p}: two buttons look the same: {labels}")
    check(all(len(l.encode('utf-8')) <= 24 for l in labels), f"{p}: a label is longer than 24 bytes")
check(all(not re.search(r"[\U0001F300-\U0001FAFF]", label(i)) for i in items), "a colour emoji in the menus (one quiet style)")
# Back goes to the page above
up = {}
for grp, parent in re.findall(r'llSubStringIndex\("~([\w~]+)~", "~" \+ p \+ "~"\) >= 0\) return "(\w+)";', ui):
    for p in grp.split("~"): up[p] = parent
check(all(up.get(p) == "scenery" for p in ("afk", "indoors", "reach")), "Scenery's settings must go back to Scenery")
check(all(up.get(p) == "camcfg" for p in ("seat", "altcam", "chat")), "camera settings must go back to Camera")
check(all(up.get(p) == "opts" for p in ("pace", "camcfg", "look", "reset")), "Settings groups must go back to Settings")
check(all(up.get(p, "main") == "main" for p in ("help", "framing", "scenery", "opts")), "the doors must go back to the main menu")
# Tips: on by default, and turning them back on starts every tip from zero
check("~tips=1~tipn=0~" in ui and 'cfgWrite("tips", "1");' in ui, "Tips must be on by default")
hp = ui[ui.index('gPage == "help"'):]
check(hp.index('cfgWrite("tipn", "0")') < hp.index('toggle("tips"'), "turning Tips on must reset the counts")
# Seated view: each button saves its own angle
m = re.search(r'cfgSet\("seat_deg", llList2String\(\[(.*?)\], llListFindList\(\[(.*?)\], \[id\]\)( \+ 1)?\)\);', ui)
vals, ids = re.findall(r'"(\w*)"', m.group(1)), re.findall(r'"(\w*)"', m.group(2))
off = 1 if m.group(3) else 0
saved = {i: (vals[ids.index(i) + off] if ids.index(i) + off < len(vals) else "") for i in ids}
check(saved == {"off": "0", "auto": "45", "high": "60", "low": "30"}, f"Seated view saves {saved}")
check("gLbl = b;" in ui and "llListFindList(gLbl, [msg])" in ui, "idOf must look the click up in the labels on screen")
# the Pick page (picker): a saved friend's label, "✓ " + the username, stays within llDialog's 24 bytes
pk = open(os.path.join(R, "hud", "src", "picker.lsl")).read()
m = re.search(r'string nm = llGetSubString\(llGetUsername\(pk\), 0, (\d+)\);\s*if \(llListFindList\(gFKeys, \[pk\]\) >= 0\) nm = "✓ " \+ llGetSubString\(nm, 0, (\d+)\);', pk)
check(m is not None, "picker: the Pick label is not built as expected")
if m:
    u = "a" * 31
    plain, saved_l = u[:int(m.group(1)) + 1], "✓ " + u[:int(m.group(1)) + 1][:int(m.group(2)) + 1]
    check(len(plain.encode()) <= 24 and len(saved_l.encode()) <= 24, f"Pick labels: {len(plain.encode())} / {len(saved_l.encode())} bytes (24 max)")
n = sum(len(v) for v in pages.values())
print(f"menus: {len(pages)} pages, {len(items)} named buttons; the main page {len(shown('main', hide_full))} buttons, all fit and are distinct, Back goes up")
print("menu checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
