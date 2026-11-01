#!/usr/bin/env bash
# Compile-check LSL scripts with LSL-PyOptimizer (a full LSL parser + type checker),
# then print a rough Mono memory estimate per script.
#   usage: tools/lslcheck.sh [files...]      (default: hud/src, hud/build, the box (hud/box), the free Take 12 Scenery in scenery/src, the lab's own scripts, and legacy/v3/src)
# 8.0: a script of hud/src, hud/build or scenery/src with less than 15 KB free (by the estimate) fails the check: every
# script keeps real headroom for the server's own use and for the next change (legacy/v3 is frozen and only warned).
set -u
DIR="${LSLOPT_DIR:-$HOME/.cache/lsl-pyoptimizer}"
if [ ! -f "$DIR/main.py" ]; then
    git clone -q --depth 1 https://github.com/Sei-Lisa/LSL-PyOptimizer "$DIR" || { echo "cannot fetch LSL-PyOptimizer"; exit 2; }
fi
files=("$@")
[ ${#files[@]} -eq 0 ] && files=(hud/src/*.lsl hud/build/*.lsl hud/box/*.lsl scenery/src/*.lsl lab/src/strip.lsl lab/src/screen.lsl lab/build/*.lsl legacy/v3/src/*.lsl)
rc=0
for f in "${files[@]}"; do
    if python3 "$DIR/main.py" -O clear -o /dev/null "$f"; then
        # the memory model (static: code and constants) lives in tools/lslmem.py, shared with the emulator's runtime check
        python3 -I "$(dirname "$0")/lslmem.py" "$f" || rc=1
    else
        echo "FAIL  $f"
        rc=1
    fi
done
exit $rc
