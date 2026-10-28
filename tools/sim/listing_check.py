# The Marketplace texts and the ad boards (8.0): the listings use the names the product has now (the four shots, the
# strip, the [12]) and nothing it no longer has, every Full description fits the Marketplace's 5000 characters (and
# stays short), the Features lists fit its five slots, the board text matches the listing, every board exists at its
# size, and the boards carry the [12] (the HUD's own disc), not the old clapper.
import os, re, sys
from PIL import Image

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p), encoding="utf-8").read()
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

main = rd("hud", "marketing", "marketplace_listing.md")
free = rd("scenery", "marketing", "marketplace_listing_scenery.md")
LISTINGS = (("listing", main), ("scenery listing", free))
art = rd("tools", "art", "make_adboard.py")

# ---- 8.0: the product's names, and nothing it no longer has -----------------------------------------------------
STALE = ["Framing", "Freehand", "FORMAT", "Whoever films leads", "Take 12 Watch", "golden line", "Adjust", "Show me", "clapper",
         "More cameras", "Me, Us or Friends", "Hold: connect", "Lite"]
for name, text in LISTINGS:
    for w in STALE: check(w not in text, f"{name}: stale wording '{w}'")
for w in ("A cinematic camera for Second Life.", "TRACKING", "PORTRAIT", "FIXED", "SCENIC", "CONNECT", "[12]", "Double-tap",
          "Take 12 Scenery", "What is new in 8.0", "Nothing is recorded"):
    check(w in main, f"listing: missing '{w}'")
for w in ("Take 12 Scenery", "Free", "L$0", "Double-tap", "skybox", "SCENIC", "full Take 12", "In the full Take 12."):
    check(w in free, f"scenery listing: missing '{w}'")
fd = lambda t: re.search(r"## Full description[^\n]*\n```\n(.*?)\n```", t, re.S).group(1)
check(len(fd(main)) <= 1800 and len(fd(free)) <= 1200, f"listings must stay short: {len(fd(main))} / {len(fd(free))} characters")

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
    check(d is not None and len(d) <= 4800, f"{name}: the Full description is {len(d) if d else 0} characters (keep it under 4800)")
    for b in re.findall(r"```\n(.*?)\n```", text, re.S):
        check("**" not in b and not re.search(r"^#+ ", b, re.M), f"{name}: markdown inside a copy-paste block")
        check("!" not in b, f"{name}: the voice is calm (no exclamation marks)")

# ---- the boards say what the listings say, and carry the [12] -----------------------------------------------------
const = lambda n: re.search(r"^" + n + r' = "(.*?)"', art, re.M).group(1)
check(const("TAGLINE") in main, "listing: the boards' line is not in the listing")
fn_, fl = re.search(r'^FREE_NAME, FREE_LINE = "(.*?)", "(.*?)"', art, re.M).groups()
check(fl in free and fn_ == "SCENERY", "the free boards' name (TAKE (12) SCENERY) and line must be in its listing")
check("make_strip.disc(" in art and "12 TAKE" not in art and "make_icon" not in art and "WATCH" not in art, "boards: the [12] disc, no clapper, no Watch")
SIZES = {"adboard_square_1024.png": (1024, 1024), "adboard_wide_1024x512.png": (1024, 512), "adboard_portrait_3x4_768x1024.png": (768, 1024),
         "adboard_landscape_4x3_1024x768.png": (1024, 768), "adboard_vendor_1024.png": (1024, 1024), "adboard_vendor_512.png": (512, 512)}
n = 0
for f, sz in SIZES.items():
    for folder, suf in (("hud", ""), ("scenery", "_scenery")):
        path = os.path.join(R, folder, "marketing", f.replace(".png", suf + ".png"))
        check(os.path.exists(path) and Image.open(path).size == sz, f"board {path} missing or not {sz}")
        n += 1
print(f"listings: 8.0 names, 5 features each, board text matches, {n} boards in place")
print("listing checks:", "ALL PASS" if ok else "FAILURES")
raise SystemExit(0 if ok else 1)
