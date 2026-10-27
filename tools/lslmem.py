#!/usr/bin/env python3
"""A rough Mono memory model for an LSL script, fitted on in-world readings (used by tools/lslcheck.sh and the emulator).

Static use (code and constants): ~18 KB base + ~58 B per statement + 2 B per string character + ~30 B for each
element of a constant list (every element is an object). 4.8.0 crashed with "Stack-Heap Collision" in the UI script
while the model, then without the list term, still showed 15 KB free.

Runtime use (8.0.1): what a script builds while it runs. A list costs about 16 B per integer or float, 16 B + 2 B per
character per string or key, 28 B per vector and 32 B per rotation; `L += x` keeps the old list alive while the new one
is built, so a list peaks at about twice its size. 8.0.0's screen.lsl showed 15.7 KB free by the static model alone and
died in-world building a 464-element list (tools/sim/memory_emu.py now measures this on the real scripts).

    python3 tools/lslmem.py <file.lsl>     prints the static estimate; exit 1 under 15 KB free (not for legacy/)
"""
import re, sys

LIMIT = 64 * 1024


def static_used(path):
    """the estimated bytes of a script's code and constants"""
    # keep string literals as they are, drop // comments (a "//" inside a string, such as a URL, is not a comment)
    t = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*', lambda m: m.group(0) if m.group(0)[0] == '"' else '', open(path, encoding="utf-8").read())
    chars = sum(len(x) for x in re.findall(r'"((?:\\.|[^"\\])*)"', t))
    clean = re.sub(r'"(?:\\.|[^"\\])*"', '""', t)
    stmts = clean.count(';')
    elems = sum(m.group(1).count(',') + 1 for m in re.finditer(r'\blist\s+\w+\s*=\s*\[(.*?)\];', clean, re.S) if m.group(1).strip())
    return 18372 + 58.3 * stmts + 2 * chars + 30 * elems, stmts


def value_bytes(v):
    """the runtime cost of one value held in a list or a variable"""
    if isinstance(v, list): return 16 + sum(value_bytes(x) for x in v)
    if isinstance(v, (int, float)): return 16
    if isinstance(v, str): return 16 + 2 * len(v)
    n = len(v) if isinstance(v, tuple) else 0
    return 28 if n == 3 else 32 if n == 4 else 16


if __name__ == "__main__":
    f = sys.argv[1]
    used, stmts = static_used(f)
    free = (LIMIT - used) / 1024
    strict = not f.startswith("legacy/")
    low = free < 15.0
    print(("FAIL  " if low and strict else "OK    ") + f"{f}: {stmts} statements, est. free memory {free:.1f} KB" + ("   <-- under 15 KB" if low else ""))
    sys.exit(1 if low and strict else 0)
