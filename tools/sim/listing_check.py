# The Marketplace texts and the ad boards (5.8, 6.1: the free Take 12 Scenery): the listings use the names the product
# has now, every Full description fits the Marketplace's 5000 characters, the Features lists fit its five slots, the
# board text matches the listing, and every board exists at its size.
import os, re, sys
from PIL import Image

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(R, "tools", "art"))
rd = lambda *p: open(os.path.join(R, *p)).read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

main, watch = rd("hud", "marketing", "marketplace_listing.md"), rd("watch", "marketing", "marketplace_listing_watch.md")
free = rd("scenery", "marketing", "marketplace_listing_scenery.md")
LISTINGS = (("listing", main), ("watch listing", watch), ("scenery listing", free))
art = rd("tools", "art", "make_adboard.py")

# ---- stale words: the cameras are Scenery, Me, Us, Still; hold opens the Share panel ------------------------------
STALE = ["Personal, Social, Friends and Frame", "Hold: the live menu", "Friends mode", "Friends in Frame", "Personal shows", "Social is for",
         "Frame holds", "And Frame:", "Typing in chat does not stop Social"]
for name, text in LISTINGS:
    for w in STALE: check(w not in text, f"{name}: stale wording '{w}'")
for w in ("Scenery", "Me shows you", "Us is for", "Still is for", "CONNECT", "Take 12 Watch", "Hold: connect", "whoever films leads", "Only friends",
          "Your idle time, framed.", "What is new in 6.0", "YOUR LENS"):
    check(w in main, f"listing: missing '{w}'")
for w in ("Take 12 Watch", "free", "Nothing to click", "Double-tap", "do not need Take 12"):
    check(w.lower() in watch.lower(), f"watch listing: missing '{w}'")
for w in ("Take 12 Scenery", "Free", "L$0", "More cameras", "Double-tap", "skybox", "Idle start", "Photo hold", "full Take 12"):
    check(w in free, f"scenery listing: missing '{w}'")
for w in ("Lite", "Hold: share", "Hold: connect", "SHARE THE VIEW", "three looks"):
    check(w not in free, f"scenery listing: says '{w}' (it has no sharing, and the name Lite is not used)")
check("Take 12 Scenery" in main, "listing: the full Take 12 should name its free companion")

# ---- the Marketplace Features list takes five --------------------------------------------------------------------
def block(text, title):
    m = re.search(r"## " + re.escape(title) + r"[^\n]*\n```\n(.*?)\n```", text, re.S)
    return m.group(1) if m else None
for name, text in LISTINGS:
    f = block(text, "Features")
    check(f is not None and len([l for l in f.splitlines() if l.strip()]) == 5, f"{name}: the Features list must have exactly 5 lines")
    k = block(text, "Keywords")
    check(k is not None and "\n" not in k.strip() and "take 12" in k, f"{name}: Keywords must be one line, with 'take 12'")
    check(block(text, "Short description") is not None, f"{name}: no short description")
    d = block(text, "Full description")
    # the Marketplace takes 5000 characters; keep some room for the (you) fields
    check(d is not None and len(d) <= 4800, f"{name}: the Full description is {len(d) if d else 0} characters (the Marketplace takes 5000; keep it under 4800)")

# ---- the plain-text rule: no markdown in the copy-paste blocks --------------------------------------------------
for name, text in LISTINGS:
    for b in re.findall(r"```\n(.*?)\n```", text, re.S):
        check("**" not in b and not re.search(r"^#+ ", b, re.M), f"{name}: markdown inside a copy-paste block")

# ---- the boards say what the listing says ------------------------------------------------------------------------
const = lambda n: re.search(r"^" + n + r' = "(.*?)"', art, re.M).group(1)
check(const("TAGLINE") in main, "listing: the boards' tagline is not in the listing")
check("LENS" in const("NEW") and "NEW" in const("NEW"), "boards: the NEW label must name the newest feature (6.0: your lens)")
check("Your lens" in re.search(r"CHIPS = \[(.*?)\]", art).group(1), "boards: a chip for the lens")
chips = re.search(r"CHIPS = \[(.*?)\]", art).group(1)
check("Connect" in chips and "Share the view" not in chips and "Friends mode" not in chips, f"boards: chips {chips}")
check("Double-tap to start" in const("HOWTO") and 'HOLD  " + ("photo" if FREE else "connect")' in art, "boards: the how-to lines")
fchips = re.search(r"FREE_CHIPS = \[(.*?)\]", art).group(1)
check(all(c in fchips for c in ("Drone views", "Skybox rooms", "Idle start", "Photo hold")) and "Connect" not in fchips, f"free boards: chips {fchips}")
check('FULL_ONLY = ("CONNECT",)' in art, "free boards: only the Share view is dimmed (rooms are in the free build)")
check("Lite" not in art and "LITE" not in art, "board script: the name Lite is not used")
for w in STALE: check(w not in art, f"board script: stale wording '{w}'")

SIZES = {("hud", "marketing", "adboard_square_1024.png"): (1024, 1024), ("hud", "marketing", "adboard_wide_1024x512.png"): (1024, 512),
         ("hud", "marketing", "adboard_portrait_3x4_768x1024.png"): (768, 1024), ("hud", "marketing", "adboard_landscape_4x3_1024x768.png"): (1024, 768),
         ("hud", "marketing", "adboard_vendor_1024.png"): (1024, 1024), ("hud", "marketing", "adboard_vendor_512.png"): (512, 512),
         ("watch", "marketing", "adboard_watch_1024.png"): (1024, 1024)}
for (a, b, n), sz in list(SIZES.items()):
    if a == "hud": SIZES[("scenery", "marketing", n.replace(".png", "_scenery.png"))] = sz
SIZES[("scenery", "art", "take12_scenery_icon_128.png")] = (128, 128)
check("icon.draw_scenery(True) if FREE" in art and 'ptext(im, (x, y), "SCENERY", sc' in art, "free boards: the Scenery clapper and the TAKE 12 / SCENERY title")
for p, sz in SIZES.items():
    path = os.path.join(R, *p)
    check(os.path.exists(path) and Image.open(path).size == sz, f"board {'/'.join(p)} missing or not {sz}")

print(f"listings: current names, 5 features each, board text matches, {len(SIZES)} boards in place")
print("listing checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
