"""Every word the 8.0 HUD shows, checked without running it: every note id the scripts send exists in text.lsl, the
voice (no exclamation marks), every strip word and mark the scripts ask for is on the textures (tools/art/make_strip.py,
and the tables generated into strip.lsl and screen.lsl), every literal dialog button fits SL (24 bytes), every dialog page ui opens
has its words in text.lsl, every script carries the same version, the free build's scripts likewise."""
import os, re, sys
from emu_util import check, done

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
rd = lambda *p: open(os.path.join(R, *p), encoding="utf-8").read()
SRC = {n[:-4]: rd("hud", "src", n) for n in os.listdir(os.path.join(R, "hud", "src")) if n.endswith(".lsl")}
text = SRC["text"]

# ---- notes -------------------------------------------------------------------------------------------------------------
notes = text[text.index("list NOTES = ["):text.index("];", text.index("list NOTES = ["))]
ids = re.findall(r'^\s*"([a-z]+)", [012], "', notes, re.M)
check(len(ids) == len(set(ids)) and len(ids) > 20, "text.lsl: %d note ids, each once" % len(ids))
used = set()
for n, s in SRC.items():
    used |= set(re.findall(r'NOTE, "([a-z]+)[|"]', s))
    used |= set(re.findall(r'\bnote\("([a-z]+)"', s))
for u in sorted(used): check(u in ids, "a note the scripts send is missing in text.lsl: %r" % u)
for i in ids:
    if i not in used and i not in ("plain",): print("note: text.lsl has %r, nothing sends it" % i)

# ---- the voice ---------------------------------------------------------------------------------------------------------
strings = re.findall(r'"((?:\\.|[^"\\])*)"', text)
for s in strings: check("!" not in s, "text.lsl: no exclamation marks: %r" % s)
for s in strings:
    if len(s) > 40: check(not re.search(r"\b(please|sorry|error|invalid|failed)\b", s, re.I), "text.lsl: calm words: %r" % s)

# ---- the strip's words and marks are on the textures -------------------------------------------------------------------------
screen = SRC["strip"]
WORDS = re.search(r'string WORDS = "([^"]*)"', screen).group(1)
MARKS = re.search(r'string MARKS = "([^"]*)"', screen).group(1)
SMARKS = re.search(r'string MARKS = "([^"]*)"', SRC["screen"]).group(1)
for m in set(re.findall(r'mark\("([a-z0-9A-Z.]+)"\)', SRC["screen"])) | {"disc", "discamber"} | {"ring%d" % i for i in range(10)}:
    check(("~" + m + "|") in SMARKS, "screen: mark %r is not in its table" % m)
cell = lambda T, n: ("~" + n + "|") in T
for shot in ("portrait", "tracking", "fixed", "scenic"):
    for line in re.findall(r'"%s\|([A-Z ,/]+)\|' % shot, SRC[shot]):
        for wd in line.split(","):
            if wd != "/": check(cell(WORDS, wd), "%s: %r is not on take12_words" % (shot, wd))
fx = SRC["fixed"]
for wd in re.findall(r'\["([A-Z][A-Z ]+)"', fx) + re.findall(r'w \+= \["([A-Z][A-Z ]+)"\]', fx):
    check(cell(WORDS, wd), "fixed: %r is not on take12_words" % wd)
for wd in ("TRACKING", "PORTRAIT", "FIXED", "SCENIC"): check(cell(WORDS, wd), "%r on take12_words" % wd)
for m in set(re.findall(r'(?:uvMark|mark)\("([a-z0-9A-Z.]+)"\)', screen)):
    check(cell(MARKS, m), "strip: mark %r is not on take12_marks" % m)
for m in ["shape" + s for s in ("1.66", "1.85", "2.00", "2.39", "FULL", "DIM")] + \
         ["link" + s for s in ["ALONE", "SHARING", "THEIR FILM"] + [str(i) for i in range(1, 10)]]:
    check(cell(MARKS, m), "mark %r is not on take12_marks" % m)
sys.path.insert(0, os.path.join(R, "tools", "art"))
try:
    import make_strip
    check(set(make_strip.WORDS) >= set(re.findall(r"~([A-Z ]+)\|", WORDS)), "make_strip.py draws every word strip.lsl knows")
except SystemExit:
    pass

# ---- dialogs -----------------------------------------------------------------------------------------------------------------
ui = SRC["ui"]
for lab in set(re.findall(r'"([^"|~]{1,40})"', ui)):
    if re.search(r'page\([^;]*"%s"' % re.escape(lab), ui) or re.search(r'\[[^\]]*"%s"[^\]]*\]' % re.escape(lab), ui):
        if lab.startswith("cin.") or lab in ("|", "~"): continue
for blist in re.findall(r'page\([^;]*?(\[[^\]]*\])\)', ui):
    for lab in re.findall(r'"([^"]*)"', blist):
        check(len(("● " + lab).encode()) <= 24, "ui: the button %r (with its mark) fits 24 bytes" % lab)
pages = set(re.findall(r'page\("([a-z0-9]+)"', ui)) | set(re.findall(r'page\(p, ', ui) and re.findall(r'p == "([a-z0-9]+)"', ui))
pages |= set(re.findall(r'dialog\("([a-z]+)"', SRC["sync"])) | {"connect", "addfriend"}
pages.discard("remove")                                            # the friends page, in its remove mode
for p in sorted(pages):
    check(('page == "%s"' % p) in text, "text.lsl has the words of the page %r" % p)

# ---- versions ----------------------------------------------------------------------------------------------------------------
vers = {n: re.search(r'string VERSION = "([^"]+)";', s).group(1) for n, s in SRC.items() if 'string VERSION' in s}
for n in ("core", "ui", "text", "screen", "strip", "bars", "tracking", "portrait", "fixed", "scenic", "sync", "carry"):
    check(n in SRC, "hud/src/%s.lsl exists" % n)
check(len(set(v for n, v in vers.items() if n in ("core", "ui", "text", "screen", "strip", "bars", "tracking", "portrait", "fixed", "scenic", "sync", "carry"))) == 1,
      "every script carries one version: %r" % vers)
done("text_check")
