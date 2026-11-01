#!/usr/bin/env python3
"""Builds the Take 12 Lab (lab/), a separate HUD for trying what may one day become the product, without touching it.

The lab owns only what it tries (lab/src/strip.lsl and lab/src/screen.lsl: the Quiet and Direct pages, 8.8.0 lab 1);
every other script is the product's own, copied here from hud/src unchanged, so the lab never drifts from the product
on anything else. The lab's builder is the product's with the lab's two parts added (t12 tab, the Quiet page's notch;
t12 fold, the key that opens and folds the Direct page) and the root named "Take 12 Lab".

    python3 tools/build_lab.py            write lab/src (the copied scripts), lab/build/builder.lsl and lab/art's copy of
                                          the product's words texture (so lab/art holds every texture the Lab needs)
    python3 tools/build_lab.py --check    fail if they are out of date (CI); a note if the product's strip or screen
                                          changed since the lab took its own (the lab may want the change too)
"""
import hashlib, os, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC, OUT = os.path.join(ROOT, "hud", "src"), os.path.join(ROOT, "lab", "src")
OWN = {"strip.lsl": "fd2838dde1ab84fe7dae4df68f232a416fb75b84",       # the lab's own, forked from these (sha1)
       "screen.lsl": "8c74d84e63b9d35c32868c67b84cc92a126b7e67"}
COPIED = ["core.lsl", "ui.lsl", "text.lsl", "bars.lsl", "tracking.lsl", "portrait.lsl", "fixed.lsl", "scenic.lsl",
          "sync.lsl", "carry.lsl"]
HEADER = "// *** TAKE 12 LAB: the product's own script, copied by tools/build_lab.py from hud/src: do not edit here ***\n"
PARTS = ('"t12 plate", "t12 guide"]', '"t12 plate", "t12 guide", "t12 tab", "t12 fold"]')
NAME = ('PRIM_NAME, "Take 12",', 'PRIM_NAME, "Take 12 Lab",')
BHEAD = "// *** TAKE 12 LAB: the product's builder with the lab's parts, made by tools/build_lab.py: do not edit here ***\n"


def builder():
    s = open(os.path.join(ROOT, "hud", "build", "builder.lsl")).read()
    for a, b in (PARTS, NAME):
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
        print("lab is up to date: %d scripts copied from hud/src, strip and screen its own, the words texture copied" % len(COPIED))
    else:
        for n in extra: os.remove(os.path.join(OUT, n))
        print("wrote %d scripts to lab/src, lab/build/builder.lsl and lab/art/take12_words_1024.png" % len(COPIED))


if __name__ == "__main__":
    main()
