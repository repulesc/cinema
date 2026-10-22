# The Marketplace texts and the ad boards (5.8): the listings use the names the product has now, the Features lists
# fit the Marketplace's five slots, the board text matches the listing, and every board exists at its size.
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
art = rd("tools", "art", "make_adboard.py")

# ---- stale words: the cameras are Scenery, Me, Us, Still; hold opens the Share panel ------------------------------
STALE = ["Personal, Social, Friends and Frame", "Hold: the live menu", "Friends mode", "Friends in Frame", "Personal shows", "Social is for",
         "Frame holds", "And Frame:", "Typing in chat does not stop Social"]
for name, text in (("listing", main), ("watch listing", watch)):
    for w in STALE: check(w not in text, f"{name}: stale wording '{w}'")
for w in ("Scenery", "Me shows you", "Us is for", "Still is for", "SHARE THE VIEW", "Take 12 Watch", "Hold: share your view", "Only friends",
          "Your idle time, framed.", "What is new in 5.8"):
    check(w in main, f"listing: missing '{w}'")
for w in ("Take 12 Watch", "free", "Nothing to click", "Double-tap", "do not need Take 12"):
    check(w.lower() in watch.lower(), f"watch listing: missing '{w}'")

# ---- the Marketplace Features list takes five --------------------------------------------------------------------
def block(text, title):
    m = re.search(r"## " + re.escape(title) + r"[^\n]*\n```\n(.*?)\n```", text, re.S)
    return m.group(1) if m else None
for name, text in (("listing", main), ("watch listing", watch)):
    f = block(text, "Features")
    check(f is not None and len([l for l in f.splitlines() if l.strip()]) == 5, f"{name}: the Features list must have exactly 5 lines")
    k = block(text, "Keywords")
    check(k is not None and "\n" not in k.strip() and "take 12" in k, f"{name}: Keywords must be one line, with 'take 12'")
    check(block(text, "Short description") is not None, f"{name}: no short description")

# ---- the plain-text rule: no markdown in the copy-paste blocks --------------------------------------------------
for name, text in (("listing", main), ("watch listing", watch)):
    for b in re.findall(r"```\n(.*?)\n```", text, re.S):
        check("**" not in b and not re.search(r"^#+ ", b, re.M), f"{name}: markdown inside a copy-paste block")

# ---- the boards say what the listing says ------------------------------------------------------------------------
const = lambda n: re.search(r"^" + n + r' = "(.*?)"', art, re.M).group(1)
check(const("TAGLINE") in main, "listing: the boards' tagline is not in the listing")
check("SHARE" in const("NEW") and "NEW" in const("NEW"), "boards: the NEW label must mention sharing")
chips = re.search(r"CHIPS = \[(.*?)\]", art).group(1)
check("Share the view" in chips and "Friends mode" not in chips, f"boards: chips {chips}")
check("Double-tap to start" in const("HOWTO") and "HOLD  share" in art, "boards: the how-to lines")
for w in STALE: check(w not in art, f"board script: stale wording '{w}'")

SIZES = {("hud", "marketing", "adboard_square_1024.png"): (1024, 1024), ("hud", "marketing", "adboard_wide_1024x512.png"): (1024, 512),
         ("hud", "marketing", "adboard_portrait_3x4_768x1024.png"): (768, 1024), ("hud", "marketing", "adboard_landscape_4x3_1024x768.png"): (1024, 768),
         ("hud", "marketing", "adboard_vendor_1024.png"): (1024, 1024), ("hud", "marketing", "adboard_vendor_512.png"): (512, 512),
         ("watch", "marketing", "adboard_watch_1024.png"): (1024, 1024)}
for p, sz in SIZES.items():
    path = os.path.join(R, *p)
    check(os.path.exists(path) and Image.open(path).size == sz, f"board {'/'.join(p)} missing or not {sz}")

print(f"listings: current names, 5 features each, board text matches, {len(SIZES)} boards in place")
print("listing checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
