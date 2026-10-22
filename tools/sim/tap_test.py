# Python port of the touch decoder in hud/src/ui.lsl (touch_start / touch_end / timer).
# Feeds scripted press/release sequences and checks which gesture fires, and when.
TAP_GAP, LONG_HOLD = 0.35, 0.8

class Decoder:
    def __init__(s):
        s.out = []; s.held = s.long_done = s.tap_n = s.dbl = False
        s.down = s.tap_t = 0.0
    def start(s, now):
        if s.tap_n:
            s.tap_n = False
            if now - s.tap_t <= TAP_GAP: s.dbl = True
            else: s.out.append(("tap", now))
        s.down, s.held, s.long_done = now, True, False
    def end(s, now):
        s.held = False
        if s.long_done: return
        if s.dbl: s.dbl = False; s.out.append(("double", now))
        else: s.tap_n, s.tap_t = True, now
    def timer(s, now):
        if s.held and not s.long_done and not s.dbl and now - s.down >= LONG_HOLD:
            s.long_done = True; s.out.append(("long", now))
        if s.tap_n and now - s.tap_t > TAP_GAP:
            s.tap_n = False; s.out.append(("tap", now))

def run(events, until=5.0):
    # events: [(time, "start"|"end")]; timer ticks every 0.1 s like the script
    d = Decoder(); ev = sorted(events); t = 0.0; i = 0
    while t <= until:
        while i < len(ev) and ev[i][0] <= t + 1e-9:
            getattr(d, ev[i][1])(ev[i][0]); i += 1
        d.timer(t); t = round(t + 0.1, 6)
    return [g for g, _ in d.out]

cases = [
    ("single tap",           [(1.0, "start"), (1.1, "end")],                                  ["tap"]),
    ("double tap at 0.2 s",  [(1.0, "start"), (1.1, "end"), (1.3, "start"), (1.4, "end")],    ["double"]),
    ("two taps 0.5 s apart", [(1.0, "start"), (1.1, "end"), (1.6, "start"), (1.7, "end")],    ["tap", "tap"]),
    ("long press 1.0 s",     [(1.0, "start"), (2.0, "end")],                                  ["long"]),
    ("long press then tap",  [(1.0, "start"), (2.0, "end"), (2.5, "start"), (2.6, "end")],    ["long", "tap"]),
    ("triple tap",           [(1.0, "start"), (1.1, "end"), (1.3, "start"), (1.4, "end"), (1.6, "start"), (1.7, "end")], ["double", "tap"]),
]
ok = True
for name, evs, want in cases:
    got = run(evs)
    flag = "ok  " if got == want else "FAIL"
    if got != want: ok = False
    print(f"{flag} {name}: {got}")
print("tap checks: ALL PASS" if ok else "tap checks: FAILED")
raise SystemExit(0 if ok else 1)
