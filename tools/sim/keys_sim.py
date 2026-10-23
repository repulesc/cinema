# The soft keys (6.5.0, keys.lsl) and the safer live view. One strip prim shows a row of the key atlas
# (hud/art/take12_keys_1024.png; 7.1: two columns of ten rows, for ADJUST) with repeats and offsets; the touch
# position says which key. Checked here:
# every row's window lands exactly on its keys, a touch maps to the key under it, each key's action is answered by
# the script it goes to, the strip sits beside the button; and Connect (6.8): your camera stopping never disconnects,
# Disconnect asks first when only Watches would be left, and both HUDs show that nobody films.
import os, re, sys
from PIL import Image

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p)).read()
keys, core, sync, share, free, frame = (rd("hud", "src", n) for n in ("keys.lsl", "core.lsl", "sync.lsl", "connect.lsl", "free.lsl", "frame.lsl"))
watch = rd("watch", "take12_watch.lsl")
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(R, "tools", "art"))
import make_keys as mk
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

# ---- the atlas and keys.lsl agree -------------------------------------------------------------------------------
ROWS = [int(x) for x in re.search(r"list    ROWS = \[([0-9, ]+)\];", keys).group(1).split(",")]
check(ROWS == [len(r[1]) for r in mk.ROWS], f"keys.lsl ROWS {ROWS} != the atlas rows")
check(max(ROWS) <= 5, "five keys at most")
CW = float(re.search(r"float   CW    = ([0-9.]+);", keys).group(1)); RH = float(re.search(r"float   RH    = ([0-9.]+);", keys).group(1))
check(abs(CW - mk.CW / mk.W) < 1e-9 and abs(RH - mk.CH / mk.H) < 1e-9, "the cell size in keys.lsl must match the atlas")
PER = int(re.search(r"integer PER   = (\d+);", keys).group(1))
check(PER == mk.PER and mk.COL == mk.W // 2 and mk.PER * mk.CH <= mk.H and 2 * mk.PER >= len(ROWS), "two columns of ten rows hold every row")
im = Image.open(os.path.join(R, "hud", "art", "take12_keys_1024.png")).convert("RGBA")
check(im.size == (mk.W, mk.H) == (1024, 1024), f"the atlas is {im.size}")
W, H = im.size
check("<n * CW, RH, 0.0>, <(r / PER) * 0.5 + n * CW * 0.5 - 0.5, 0.5 - (r % PER + 0.5) * RH, 0.0>" in keys, "keys.lsl: the repeats / offsets")
for r, n in enumerate(ROWS):
    ru, rv = n * CW, RH
    ou, ov = (r // PER) * 0.5 + n * CW * 0.5 - 0.5, 0.5 - (r % PER + 0.5) * RH
    u0, u1 = ou + 0.5 - ru / 2, ou + 0.5 + ru / 2          # Second Life: the window is centred at offset + 0.5
    v0, v1 = ov + 0.5 - rv / 2, ov + 0.5 + rv / 2          # v up from the bottom of the image
    box = (round(u0 * W), round((1 - v1) * H), round(u1 * W), round((1 - v0) * H))
    x0, y0 = (r // PER) * mk.COL, (r % PER) * mk.CH
    check(box == (x0, y0, x0 + n * mk.CW, y0 + mk.CH), f"row {r}: the window {box} misses its keys")
    for i in range(n):                                     # each key cell holds a key; the next cell is empty
        cell = im.crop((x0 + i * mk.CW, y0, x0 + (i + 1) * mk.CW, y0 + mk.CH))
        check(cell.getchannel("A").getbbox() is not None, f"row {r}, key {i}: empty")
    if n < 6:
        check(im.crop((x0 + n * mk.CW, y0, x0 + (n + 1) * mk.CW, y0 + mk.CH)).getchannel("A").getbbox() is None, f"row {r}: a stray key")
    # a touch: the key under it
    for i in range(n):
        for f in (0.02, 0.5, 0.98):
            s = (i + f) / n
            check(min(int(s * n), n - 1) == i, f"row {r}: a touch at {s:.3f} is not key {i}")
check("integer k = (integer)(st.x * llList2Integer(ROWS, gRow));" in keys and "if (st.x < 0.0) return;" in keys, "keys.lsl: the touch")

# ---- which keys, when ----------------------------------------------------------------------------------------------
names = [r[0] for r in mk.ROWS]
check(names == ["live", "watch", "free", "freeA", "freeB", "free+", "freeA+", "freeB+", "full", "half", "close", "full+", "half+", "close+",
                 "group", "group+"], f"atlas rows {names} (7.1: ADJUST off / on)")
for frag in ('if (gShare == "live") return 0;', 'if (gShare == "view") return 1;',
             'if (on && gMode == "free") return 3 + gPick + 3 * gAdj;', 'if (gSt == "rolling" && gMode == "frame") return 8 + gStill + 3 * gAdj;',
             'if (on && (gMode == "social" || gMode == "friends")) return 14 + gAdj;', "return -1;", "gAdj = (integer)llList2String(L, 4);"):
    check(frag in keys, f"keys.lsl: pick() no longer reads {frag}")
# a port of pick(): each state shows the row whose lit keys say it
def pick(mode, sub, adj):
    if mode == "free": return 3 + sub + 3 * adj
    if mode == "frame": return 8 + sub + 3 * adj
    return 14 + adj
for mode, subs, want in (("free", (-1, 0, 1), (None, "A", "B")), ("frame", (0, 1, 2), ("FULL", "HALF", "CLOSE")), ("social", (0,), (None,))):
    for sub, w in zip(subs, want):
        for adj in (0, 1):
            lit = set(mk.ROWS[pick(mode, sub, adj)][2])
            check(lit == {x for x in (w, "ADJUST" if adj else None) if x}, f"{mode} {sub} adjust {adj}: row {pick(mode, sub, adj)} lights {lit}")
check(all("ADJUST" in r[1] for r in mk.ROWS[2:]) and all(r[1][-1] == "ADJUST" for r in mk.ROWS[2:]), "ADJUST, last, on every camera row")

# ---- every key's action is answered ----------------------------------------------------------------------------
acts = {"LIVE": re.search(r'string  LIVE = "([^"]+)";', keys).group(1), "FREE": re.search(r'string  FREE = "([^"]+)";', keys).group(1),
        "STIL": re.search(r'string  STIL = "([^"]+)";', keys).group(1), "WATCH": re.search(r'string  WTCH = "([^"]+)";', keys).group(1),
        "GRP": re.search(r'string  GRP  = "([^"]+)";', keys).group(1)}
check(acts["LIVE"] == "C:next;S:who;S:disconnect" and acts["WATCH"] == "C:scenery;S:film;S:disconnect", f"keys.lsl: the Connect keys {acts}")
check('string row = llList2String([LIVE, WTCH, FREE, FREE, FREE, FREE, FREE, FREE, STIL, STIL, STIL, STIL, STIL, STIL, GRP, GRP], gRow);' in keys, "keys.lsl: each row's actions")
rowact = ["LIVE", "WTCH", "FREE", "FREE", "FREE", "FREE", "FREE", "FREE", "STIL", "STIL", "STIL", "STIL", "STIL", "STIL", "GRP", "GRP"]
check(all(len({"WTCH": acts["WATCH"]}.get(a, acts.get(a, "")).split(";")) == ROWS[i] for i, a in enumerate(rowact)), "every key on a row has an action")
for name, row in acts.items():
    n = len(row.split(";"))
    check(n in ROWS, f"{name}: {n} actions")
    for a in row.split(";"):
        kind, what = a[0], a[2:]
        if kind == "S":
            check(f'a == "{what}"' in sync, f"sync does not act on '{what}' (key {name})")
        elif what == "adjust":
            check('else if (str == "adjust")' in core and "gAdjOn = !gAdjOn;" in core, "core does not act on 'adjust'")
        elif what in ("next", "photo", "stop"):
            check(f'str == "{what}"' in core, f"core does not act on '{what}'")
        elif what == "scenery":
            check('else if (num == CMD && str == "scenery" && gHost != NULL_KEY) say(gHost, "next");' in sync, "a viewer's NEXT must cut for all")
        elif what == "fav":
            check('if (num == CMD && str == "fav") save();' in free.replace("else if (num == CMD && str == \"fav\")", "if (num == CMD && str == \"fav\")"), "free.lsl: SAVE")
        elif what.startswith("view|"):
            check('llGetSubString(str, 0, 4) == "view|") at((integer)llGetSubString(str, 5, -1));' in free, "free.lsl: VIEW A / B")
        elif what.startswith("framing|"):
            check('llGetSubString(str, 0, 7) == "framing|")' in frame, "frame.lsl: FULL / HALF / CLOSE")
        else:
            check(False, f"unknown action {a}")
check('llMessageLinked(LINK_SET, KEYS, "free|" + (string)gPick, "");' in free, "free.lsl: lights the view in use")
# 7.1.2: a HUD you can give away: the atlas by its UUID, saved in the strip's description
tx = keys[keys.index("string texture()"):keys.index("// a key: the action in its row")]
check("key k = llGetInventoryKey(TEX);" in tx and 'llSetLinkPrimitiveParamsFast(gLink, [PRIM_DESC, d]);' in tx and "if (k != NULL_KEY" in tx
      and tx.index('if (llGetSubString(d, 0, 11) == TEX + " ") return llGetSubString(d, 12, -1);') < tx.index("if (llGetInventoryType(TEX) == INVENTORY_TEXTURE) return TEX;"),
      "keys.lsl: the texture's UUID is saved in the strip's description (full permissions) and used first")
check(len("take12_keys ") == 12 and "string tex = texture();" in keys and "llGetLinkPrimitiveParams(gLink, [PRIM_TEXTURE, 0])" not in keys,
      "keys.lsl: no texture by name from the contents once the UUID is kept (and no face read, which a next owner cannot)")
check('"missing: add take12_keys once", "saved"' in keys, "keys.lsl: /77 status says whether the texture is saved")
check('else if (num == STILL)' in keys and '"Full length", "Half length", "Close"' in keys, "keys.lsl: Still's framing")

# ---- the strip: beside the button, never on it; Frame's bars leave it alone --------------------------------------
check("vector off = <0.0, sy * (b * 0.5 + 0.004 + w * 0.5), 0.0>;" in keys and "float h = 1.2 * b;" in keys, "keys.lsl: the strip's place, 1.2 times the button's height")
# 6.7.1 Size: Small / Medium / Large, the keys with the button, never on it
SIZES = [float(x) for x in re.search(r"list    EDGES  = \[([0-9., ]+)\];", keys).group(1).split(",")]
check(SIZES == [0.04, 0.06, 0.08], f"sizes {SIZES}")
for b in SIZES:
    h = 1.2 * b
    for n in (3, 4, 5):
        w = n * h * 0.791667
        right_edge = (b * 0.5 + 0.004 + w * 0.5) - w / 2
        check(right_edge > b / 2, f"{n} keys overlap the {b} button")
check('if (cfg("size") == "") size(1);' in keys and "llSetScale(<s.x, e, e>);" in keys and 'llLinksetDataWriteProtected("cin.size", (string)i, PASS);' in keys,
      "keys.lsl: Size scales the button (Medium when never set) and keeps it")
check('else if (num == CMD && str == "size") menu();' in keys and 'size(llListFindList(["s", "m", "l"], [llGetSubString(str, 5, 5)]));' in keys
      and 'if (msg == "‹ Back") llMessageLinked(LINK_SET, UI_MENU, "look", "");' in keys, "keys.lsl: the Size menu and /77 size")
ui = rd("hud", "src", "ui.lsl")
check('"stline", "size", "trace", "back"' in ui and 'else if (id == "size") llMessageLinked(LINK_SET, CMD, "size", "");' in ui and "~size|" in ui,
      "ui: Options > Look > Size, drawn by keys.lsl")
check('else if (c == "size") llMessageLinked(LINK_SET, CMD, "size|" + v, "");' in rd("hud", "src", "picker.lsl"), "picker: /77 size")
check('if (llSubStringIndex(m, "keys") >= 0) gLink = i;' in keys and 'string  STRIP = "Take 12 keys";' in keys
      and "if (!gLink && llGetNumberOfPrims() >= 6) gLink = f;" in keys and "PRIM_NAME, STRIP" in keys, "keys.lsl: finds its strip by name, or the box Frame leaves")
check('llSubStringIndex(m, "keys") < 0' in rd("hud", "src", "crop.lsl"), "crop.lsl must not take the strip as a bar")
# 6.6: a strip linked before it was named (or named Take 12 Keys, or taken as a fifth Frame box before 6.6): crop and keys
# must never claim the same box. A port of both scans over the link names.
def crop_scan(names):
    bars = []
    for n in (0, 1):
        for i, m in enumerate(names, 2):
            m = m.lower()
            if len(bars) < 4 and (m == "take 12 frame") == (n == 0) and "keys" not in m: bars.append(i)
    return bars
def keys_scan(names):
    link = f = nf = 0
    for i, m in enumerate(names, 2):
        m = m.lower()
        if "keys" in m: link = i
        else:
            if m == "take 12 frame": nf += 1
            if m != "take 12 frame" or nf > 4: f = i
    return link or (f if len(names) + 1 >= 6 else 0)
F, K, O = "Take 12 frame", "Take 12 keys", "Object"
CASES = {"built as asked": [F, F, F, F, K], "strip linked first, named later": [O, F, F, F, F], "a new build, nothing named": [O] * 5,
         "Take 12 Keys": [F, "Take 12 Keys", F, F, F], "taken as a fifth bar before 6.6": [F] * 5, "no strip": [F] * 4}
for what, names in CASES.items():
    b, k = crop_scan(names), keys_scan(names)
    check(len(b) == 4 and k not in b, f"{what}: bars {b}, strip {k}")
    check((k > 0) == (len(names) >= 5), f"{what}: strip {k}")

# ---- Connect: a camera stop never disconnects; the last Take 12 leaving the Watches asks first ---------------------
stop = sync[sync.index("else if (num == STOP && str != \"switch\")"):sync.index("else if (num == CMD && str == \"share\")")]
check("endlive(" not in stop and 'all("pause");' in stop, "sync: your camera stopping must never disconnect")
check('else ui("end|" + llDumpList2String(gWatchers, ","));' in sync and 'p == "end"' in share and '["Disconnect", "Keep"]' in share,
      "Disconnect with only Watches left must ask first, in the panel and on the key")
check('if (!gCamOn) return "⇄ Connected · " + r + "\\nnobody films · double-tap: film";' in sync, "the hub sees that nobody films")
for name, s_ in (("sync", sync), ("watch", watch)):
    check('w == "pause"' in s_ and 'gHeld = TRUE;' in s_ and "nobody films" in s_, f"{name}: connected, nobody films must show")
check("gHeld = FALSE;" in watch[watch.index('w == "cam"'):watch.index('w == "hb"')], "watch: the next camera follows again")
print(f"keys: {len(ROWS)} rows of at most {max(ROWS)} keys, windows exact, touches map, every action answered; a stop never disconnects, Disconnect asks")
print("keys checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
