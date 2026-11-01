#!/usr/bin/env python3
"""Builds the Take 12 Lab (lab/), a separate HUD for trying what may one day become the product, without touching it.

The lab owns only what it tries (lab/src/strip.lsl and screen.lsl: the Quiet and Direct pages, lab 1, and the island,
lab 2; ui.lsl and text.lsl: the setup's alignment in fine steps and the guide card first, lab 2);
every other script is the product's own, copied here from hud/src unchanged, so the lab never drifts from the product
on anything else. The lab's builder is the product's with the lab's two parts added (t12 tab, the Quiet page's notch;
t12 fold, the key that opens and folds the Direct page). Nothing the wearer sees says "lab": it is built here, not named so.

    python3 tools/build_lab.py            write lab/src (the copied scripts), lab/build/builder.lsl and lab/art's copy of
                                          the product's words texture (so lab/art holds every texture the Lab needs)
    python3 tools/build_lab.py --check    fail if they are out of date (CI); a note if the product's strip or screen
                                          changed since the lab took its own (the lab may want the change too)
"""
import hashlib, os, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC, OUT = os.path.join(ROOT, "hud", "src"), os.path.join(ROOT, "lab", "src")
OWN = {"strip.lsl": "1a50dc6717d5e67cb1024eb317e095ade05c4917",       # the lab's own, forked from these (sha1)
       "screen.lsl": "1a574faefab3816857f2677418e64171ce8999de",
       "ui.lsl": "8109659aa9336f7f5e77ff2e117d4f7933c44f10",           # lab 2: the setup's alignment and the guide first
       "text.lsl": "4c4cb604a2bb30626e51e382535f90a18160179d"}
COPIED = ["core.lsl", "bars.lsl", "tracking.lsl", "portrait.lsl", "fixed.lsl", "scenic.lsl",
          "sync.lsl", "carry.lsl"]
HEADER = "// *** TAKE 12 LAB: the product's own script, copied by tools/build_lab.py from hud/src: do not edit here ***\n"
PARTS = ('"t12 plate", "t12 guide"]', '"t12 plate", "t12 guide", "t12 tab", "t12 fold", "t12 tab2"]')
BHEAD = "// *** TAKE 12 LAB: the product's builder with the lab's parts, made by tools/build_lab.py: do not edit here ***\n"


def builder():
    s = open(os.path.join(ROOT, "hud", "build", "builder.lsl")).read()
    for a, b in (PARTS,):
        assert s.count(a) == 1, "builder.lsl: expected exactly one %r" % a
        s = s.replace(a, b)
    return BHEAD + s


def main():
    check = "--check" in sys.argv
    want = {os.path.join(OUT, n): HEADER + open(os.path.join(SRC, n)).read() for n in COPIED}
    want[os.path.join(ROOT, "lab", "build", "builder.lsl")] = builder()
    words = open(os.path.join(ROOT, "hud", "art", "take12_words_1024.png"), "rb").read()
    want[os.path.join(ROOT, "lab", "art", "take12_words_1024.png")] = words      # the Lab's words: the product's own
    bad = []
    for path, text in want.items():
        mode = "b" if isinstance(text, bytes) else ""
        if check:
            if not os.path.exists(path) or open(path, "r" + mode).read() != text: bad.append(os.path.relpath(path, ROOT))
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w" + mode).write(text)
    extra = sorted(set(os.listdir(OUT)) - set(COPIED) - set(OWN))
    for n, sha in OWN.items():
        if not os.path.exists(os.path.join(OUT, n)): bad.append("lab/src/" + n + " (missing)")
        if hashlib.sha1(open(os.path.join(SRC, n), "rb").read()).hexdigest() != sha:
            print("note: hud/src/%s changed since the lab took its own copy; lab/src/%s may want the change too" % (n, n))
    if check:
        bad += ["lab/src/" + n + " (not the lab's)" for n in extra]
        if bad: print("lab is out of date, run python3 tools/build_lab.py:", ", ".join(bad)); raise SystemExit(1)
        print("lab is up to date: %d scripts copied from hud/src, strip, screen, ui and text its own, the words texture copied" % len(COPIED))
    else:
        for n in extra: os.remove(os.path.join(OUT, n))
        print("wrote %d scripts to lab/src, lab/build/builder.lsl and lab/art/take12_words_1024.png" % len(COPIED))


if __name__ == "__main__":
    main()
