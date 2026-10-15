# Photographer mode (design stage): the composition maths, checked, and the mock-up page drawn from the same maths.
#
# A preset says WHERE body features land in the frame (e.g. "eyes on the upper third, frame bottom at mid-thigh"),
# from WHICH camera height and side, with WHICH lens. The camera distance and tilt are then solved for the avatar's
# height and the viewer's real field of view, so the framing is the same on a 1.6 m and a 2.3 m avatar and at any
# FOV. Only the perspective changes with the lens - that is the photographer's choice (see docs/PHOTOGRAPHER.md).
#
# Screen coordinates: x, y in -1..+1 of the chosen photo format (16:9, 3:2 or 4:3 cut out of a 16:9 window), y up.
#   python3 tools/sim/photographer_sim.py               checks only
#   python3 tools/sim/photographer_sim.py --html FILE   also writes the mock-up page
import math, sys

# ---- body model: heights as a fraction of llGetAgentSize().z, from the feet (standing) ---- CALIBRATE in-world
BODY = dict(top=1.0, eyes=0.935, chin=0.87, shoulders=0.82, chest=0.72, elbow=0.63, waist=0.60, belt=0.56,
            hip=0.52, midthigh=0.38, knee=0.285, shin=0.15, feet=0.0)
# half-widths (m) of a stand-in figure at those heights, for drawing and for the side margins (scaled by height/1.9)
WIDTH = [(1.0, 0.0), (0.985, 0.07), (0.935, 0.095), (0.88, 0.08), (0.855, 0.065), (0.82, 0.21), (0.72, 0.18),
         (0.60, 0.15), (0.52, 0.18), (0.38, 0.15), (0.285, 0.11), (0.04, 0.08), (0.0, 0.09)]
FORMATS = {"16:9": 16 / 9, "3:2": 3 / 2, "4:3": 4 / 3}
WINDOW = 16 / 9                                   # assumed window; the format is cut out of its middle
PHI = 1 - 2 * 0.381966                            # golden-section line, as x or y (0.236 from the centre)
THIRD = 1 / 3

def fov_of_mm(mm): return 2 * math.atan(12.0 / mm)          # vertical FOV of a full-frame lens (24 mm high)
def mm_of_fov(f): return 12.0 / math.tan(f / 2)

# ---- presets ----------------------------------------------------------------------------------------------------
# anchors: two (feature, y) pairs that fix size and position. cam: camera height, as a fraction of the height.
# side: degrees round from the subject's nose (0 = straight on, 30 = three-quarter). x: where the subject's centre
# line sits (0 centre, +-THIRD, +-PHI; the sign is chosen so the subject looks INTO the frame: lead room).
PORTRAIT = [
    dict(id="A", name="Environment", look="editorial", mm=35, cam=0.935, side=30, x=PHI,
         anchors=[("top", 0.18), ("feet", -0.72)]),
    dict(id="B", name="Full length", look="fashion", mm=50, cam=0.50, side=15, x=0.0,
         anchors=[("top", 0.86), ("feet", -0.88)]),
    dict(id="C", name="Three-quarter", look="classic", mm=50, cam=0.80, side=30, x=THIRD,
         anchors=[("eyes", THIRD), ("midthigh", -1.0)]),
    dict(id="D", name="Half body", look="classic", mm=85, cam=0.935, side=30, x=THIRD,
         anchors=[("eyes", THIRD), ("belt", -1.0)]),
    dict(id="E", name="Head and shoulders", look="beauty", mm=85, cam=0.98, side=25, x=0.2,
         anchors=[("eyes", THIRD), ("chest", -1.0)]),
]
GROUP = [
    dict(id="A", name="Group in the place", mm=35, cam=0.935, anchors=[("top", 0.25), ("feet", -0.65)]),
    dict(id="B", name="Full group", mm=50, cam=0.60, anchors=[("top", 0.84), ("feet", -0.86)]),
    dict(id="C", name="Three-quarter group", mm=50, cam=0.80, anchors=[("eyes", THIRD), ("midthigh", -1.0)]),
    dict(id="D", name="Half-body group", mm=50, cam=0.935, anchors=[("eyes", THIRD), ("belt", -1.0)]),
    dict(id="E", name="From above", mm=35, cam=1.0, rise=1.6, anchors=[("top", 0.45), ("feet", -0.80)]),
]
LANDSCAPE = [
    dict(id="A", name="Big sky", mm=24, rise=0.5, horizon=-THIRD),
    dict(id="B", name="The land", mm=24, rise=3.0, horizon=THIRD),
    dict(id="C", name="You in the place", mm=35, rise=0.0, horizon=THIRD, you=(-THIRD, -0.45)),
    dict(id="D", name="High view", mm=24, rise=12.0, horizon=0.85),
    dict(id="E", name="Far detail", mm=85, rise=0.5, horizon=THIRD),
]

# ---- the solver (this is what cinema_photo.lsl will do) ---------------------------------------------------------
def solve_vertical(z1, y1, z2, y2, zc, fov):
    """camera at height zc, horizontal distance D, tilt phi (down +): put height z1 at screen y1 and z2 at y2.
    a(z) = atan((z - zc) / D) is the elevation of z; on screen y = tan(a + phi) / tan(fov/2). Bisection on D."""
    t = math.tan(fov / 2)
    want = math.atan(y1 * t) - math.atan(y2 * t)            # the angle the two features must span
    span = lambda D: math.atan((z1 - zc) / D) - math.atan((z2 - zc) / D)
    lo, hi = 0.05, 400.0
    if span(hi) > want: return None                          # cannot get far enough
    for _ in range(60):                                      # LSL: 24 rounds are plenty (1 mm)
        mid = (lo + hi) / 2
        if span(mid) > want: lo = mid
        else: hi = mid
    D = (lo + hi) / 2
    phi = math.atan(y1 * t) - math.atan((z1 - zc) / D)
    return D, phi

DMIN = 1.2          # m: never closer (mesh hair clips the camera, and the face distorts badly below this)
TOP_MAX = 0.9       # the top of the head never above this line (5 % of the frame height above it)

def tilt_for(z, y, zc, D, fov):
    """tilt that puts height z at screen y, camera D away horizontally"""
    return math.atan(y * math.tan(fov / 2)) - math.atan((z - zc) / D)

def place(preset, h, fov, fmt, kind="portrait"):
    """camera distance and tilt for one person of height h (feet at z = 0). Returns (D, tilt, zc, lens_short):
    lens_short = the lens is too wide for this framing from DMIN, so it is framed looser (eyes still on the
    third, or the top anchor kept) and the status line asks for the preset's lens."""
    zc = preset["cam"] * h + preset.get("rise", 0.0)
    (f1, y1), (f2, y2) = preset["anchors"]
    sol = solve_vertical(BODY[f1] * h, y1, BODY[f2] * h, y2, zc, fov)
    if sol is None: return None
    D, phi = sol
    if D >= DMIN: return D, phi, zc, False
    zk, yk = (BODY["eyes"] * h, THIRD) if "eyes" in (f1, f2) else (BODY[f1] * h, y1)
    return DMIN, tilt_for(zk, yk, zc, DMIN, fov), zc, True

def project(z, half_w, D, phi, zc, fov, fmt, xoff=0.0):
    """screen (x, y) of a point at height z on the subject's centre line, and the half-width there"""
    t = math.tan(fov / 2); th = t * FORMATS[fmt]
    dz = z - zc
    # rotate into the camera: forward = horizontal distance tilted by phi
    fwd = D * math.cos(phi) - dz * math.sin(phi)
    up = D * math.sin(phi) + dz * math.cos(phi)
    return xoff, up / (fwd * t), half_w / (fwd * th)

# ---- checks -----------------------------------------------------------------------------------------------------
ok = True
def check(c, msg):
    global ok
    if not c: ok = False; print("FAIL", msg)

def width_at(fr, h):
    for (a, wa), (b, wb) in zip(WIDTH, WIDTH[1:]):
        if b <= fr <= a: return (wb + (wa - wb) * (fr - b) / (a - b)) * h / 1.9
    return 0.0

HEIGHTS = (1.55, 1.75, 1.95, 2.15, 2.35)                     # SL avatars are often 2.0-2.2 m tall
FOVS = [fov_of_mm(m) for m in (21, 24, 35, 50, 85, 105)]     # 21 mm = the viewer's default 60 degrees
report = []
for p in PORTRAIT:
    dists = []
    for h in HEIGHTS:
        for fov in FOVS:
            for fmt in FORMATS:
                s = place(p, h, fov, fmt)
                check(s is not None, f"portrait {p['id']}: no solution at h {h}, {math.degrees(fov):.0f} deg")
                if s is None: continue
                D, phi, zc, short = s
                for f, y in p["anchors"]:                    # the anchors land where the preset says
                    if short and f != "eyes": continue       # looser on purpose: only the eye line is kept
                    _, yy, _ = project(BODY[f] * h, 0, D, phi, zc, fov, fmt)
                    check(abs(yy - y) < 0.01 or (short and f == "top"), f"portrait {p['id']}: {f} at {yy:.3f}, wanted {y}")
                if short: check(mm_of_fov(fov) < p["mm"], f"portrait {p['id']}: lens tip at {mm_of_fov(fov):.0f} mm although wider than needed")
                _, ytop, _ = project(h, 0, D, phi, zc, fov, fmt)
                check(ytop <= 0.97, f"portrait {p['id']}: head cut (top at {ytop:.2f}) h {h} {math.degrees(fov):.0f} deg")
                _, ye, _ = project(BODY["eyes"] * h, 0, D, phi, zc, fov, fmt)
                if p["id"] in "CDE":
                    check(abs(ye - THIRD) < 0.01, f"portrait {p['id']}: eye line off the third ({ye:.3f})")
                # the widest part of the body (shoulders) stays inside the format, with the subject at its x
                _, _, ws = project(BODY["shoulders"] * h, width_at(BODY["shoulders"], h), D, phi, zc, fov, fmt)
                check(abs(p["x"]) + ws <= 0.9, f"portrait {p['id']}: shoulders reach the edge in {fmt} (h {h})")
                check(abs(math.degrees(phi)) <= 25, f"portrait {p['id']}: tilt {math.degrees(phi):.0f} deg is too steep")
                if fmt == "16:9" and abs(h - 1.95) < 0.01: dists.append((round(mm_of_fov(fov)), D, math.degrees(phi), short))
    report.append((p, dists))

# group: three to five people of mixed height side by side; heights 1.7-2.3 m; the tallest sets the top, the
# shortest sets the bottom cut, everyone's eyes are checked against the cut and the frame edges
import random
rng = random.Random(3)
for g in GROUP:
    for trial in range(60):
        n = rng.randint(3, 5)
        hs = [rng.uniform(1.7, 2.3) for _ in range(n)]
        hi_, lo_ = max(hs), min(hs)
        (f1, y1), (f2, y2) = g["anchors"]
        z1 = BODY[f1] * (hi_ if f1 in ("top",) else sum(hs) / n)
        z2 = BODY[f2] * lo_ if f2 != "feet" else 0.0
        zc = g["cam"] * sum(hs) / n + g.get("rise", 0.0)
        fov = fov_of_mm(g["mm"])
        sol = solve_vertical(z1, y1, z2, y2, zc, fov)
        check(sol is not None, f"group {g['id']}: no solution")
        D, phi = sol
        top = max(hs)                                         # mixed heights: the tallest head is never cut
        if math.tan(math.atan((top - zc) / D) + phi) / math.tan(fov / 2) > TOP_MAX:
            D, phi = solve_vertical(top, TOP_MAX, z2, y2, zc, fov)
        for h in hs:
            _, yt, _ = project(h, 0, D, phi, zc, fov, "16:9")
            _, ye, _ = project(BODY["eyes"] * h, 0, D, phi, zc, fov, "16:9")
            check(yt <= 0.97, f"group {g['id']}: a head is cut ({yt:.2f})")
            check(ye > y2 + 0.3, f"group {g['id']}: someone's eyes too near the bottom cut")

# landscape: the horizon is a direction, so its place on screen depends only on the tilt
for l in LANDSCAPE:
    fov = fov_of_mm(l["mm"])
    phi = math.atan(l["horizon"] * math.tan(fov / 2))       # tilt down that puts the horizon at y
    check(abs(math.tan(phi) / math.tan(fov / 2) - l["horizon"]) < 1e-9, f"landscape {l['id']}: horizon misplaced")

print("Photographer presets (a 1.95 m avatar, 16:9): lens -> camera distance and tilt")
for p, dists in report:
    row = "  ".join(f"{mm:>3} mm {D:5.2f} m {ph:+5.1f}{'*' if sh else ' '}" for mm, D, ph, sh in dists)
    print(f"  {p['id']} {p['name']:<19} {row}")
print("  (* = lens too wide for this framing: framed looser from 1.2 m, and the status line asks for the lens)")
print("photographer checks:", "ALL PASS" if ok else "FAILURES")

# ---- mock-up page -----------------------------------------------------------------------------------------------
def svg_portrait(p, h, fov, fmt, w=300):
    s = place(p, h, fov, fmt)
    D, phi, zc, short = s
    ar = FORMATS[fmt]; H = w / ar
    sx = lambda x: (x + 1) / 2 * w
    sy = lambda y: (1 - y) / 2 * H
    out = [f'<svg viewBox="0 0 {w} {H:.1f}" width="{w}" height="{H:.0f}" role="img" aria-label="{p["name"]}">',
           f'<rect class="sky" x="0" y="0" width="{w}" height="{H:.1f}"/>']
    # ground line: where the floor (z = 0) far away would be = the horizon of the floor plane at eye level of camera
    t = math.tan(fov / 2)
    yh = math.tan(phi) / t
    if -1 < yh < 1: out.append(f'<rect class="ground" x="0" y="{sy(yh):.1f}" width="{w}" height="{H - sy(yh):.1f}"/>')
    elif yh >= 1: out.append(f'<rect class="ground" x="0" y="0" width="{w}" height="{H:.1f}"/>')
    for g in (THIRD, -THIRD):
        out.append(f'<line class="grid" x1="{sx(g):.1f}" y1="0" x2="{sx(g):.1f}" y2="{H:.1f}"/>')
        out.append(f'<line class="grid" x1="0" y1="{sy(g):.1f}" x2="{w}" y2="{sy(g):.1f}"/>')
    # the figure, sampled at many heights, with perspective per height
    pts_l, pts_r = [], []
    steps = 80
    xo = p["x"]
    for i in range(steps + 1):
        fr = 1.0 - i / steps
        _, y, hw = project(fr * h, width_at(fr, h), D, phi, zc, fov, fmt)
        pts_l.append((sx(xo - hw), sy(y))); pts_r.append((sx(xo + hw), sy(y)))
    poly = pts_l + pts_r[::-1]
    out.append('<polygon class="fig" points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in poly) + '"/>')
    _, ye, _ = project(BODY["eyes"] * h, 0, D, phi, zc, fov, fmt)
    out.append(f'<circle class="eye" cx="{sx(xo):.1f}" cy="{sy(ye):.1f}" r="2.2"/>')
    out.append("</svg>")
    return "".join(out), D, math.degrees(phi), zc

def html(path):
    rows = []
    for p in PORTRAIT:
        cells = []
        for h in (1.75, 2.15):
            for fmt in ("16:9", "4:3"):
                sv, D, ph, zc = svg_portrait(p, h, fov_of_mm(p["mm"]), fmt, w=230)
                cells.append(f'<figure>{sv}<figcaption>{h:.2f} m avatar · {fmt}<br>camera {D:.1f} m away, '
                             f'{zc:.2f} m high, tilt {ph:+.0f}°</figcaption></figure>')
        sv, D, ph, zc = svg_portrait(p, 1.95, fov_of_mm(21), "16:9", w=230)
        if place(p, 1.95, fov_of_mm(21), "16:9")[3]:
            cap = (f'viewer default (≈21 mm) is too wide here: framed looser from {D:.1f} m, and the line above the '
                   f'button asks for {p["mm"]} mm')
        else:
            cap = (f'viewer default (≈21 mm): same framing, but the camera is only {D:.1f} m away, so perspective is '
                   f'stronger (this flat stand-in cannot show it)')
        cells.append(f'<figure class="warn">{sv}<figcaption>{cap}</figcaption></figure>')
        anchors = "; ".join(f"{f} on {('upper third' if abs(y - THIRD) < 1e-6 else f'y {y:+.2f}')}" for f, y in p["anchors"])
        rows.append(f'''<section><header><span class="id">{p["id"]}</span><div><h2>{p["name"]}</h2>
<p>{p["look"]} · lens {p["mm"]} mm · camera at {int(p["cam"] * 100)} % of the height · {p["side"]}° round from the nose ·
{"centred" if p["x"] == 0 else ("on the golden line" if abs(p["x"] - PHI) < 1e-6 else "on a third")}, looking into the frame</p>
<p class="small">{anchors}</p></div></header><div class="row">{"".join(cells)}</div></section>''')
    lens = "".join(f"<tr><td>{p['id']} {p['name']}</td>" + "".join(
        (f"<td>{place(p, 1.95, fov_of_mm(m), '16:9')[0]:.1f} m" + (" *" if place(p, 1.95, fov_of_mm(m), '16:9')[3] else "") + "</td>") for m in (21, 35, 50, 85)) + "</tr>" for p in PORTRAIT)
    grp = "".join(f"<li><b>{g['id']} {g['name']}</b> · {g['mm']} mm</li>" for g in GROUP)
    land = "".join(f"<li><b>{l['id']} {l['name']}</b> · {l['mm']} mm · horizon "
                   f"{'on the lower third' if l['horizon'] < 0 else ('on the upper third' if abs(l['horizon'] - THIRD) < 1e-6 else 'near the top')}</li>" for l in LANDSCAPE)
    doc = f'''<title>Photographer Presets</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* layout: one column of preset cards, each a row of computed frames that scrolls sideways on its own */
:root{{--bg:#f3f2ee;--fg:#1b1d22;--muted:#61646d;--card:#ffffff;--line:#dfddd6;--sky:#cddcea;--ground:#d8ccb2;--fig:#2c3646;--eye:#e0474c;--grid:rgba(20,22,30,.32);--warn:#9a4a1c;
--display:"Instrument Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#131418;--fg:#ebebee;--muted:#9c9ea8;--card:#1c1d22;--line:#2d2f36;--sky:#2a3a4b;--ground:#4b4334;--fig:#e9e3d5;--eye:#ff7b7f;--grid:rgba(255,255,255,.34);--warn:#e7a072;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#131418;--fg:#ebebee;--muted:#9c9ea8;--card:#1c1d22;--line:#2d2f36;--sky:#2a3a4b;--ground:#4b4334;--fig:#e9e3d5;--eye:#ff7b7f;--grid:rgba(255,255,255,.34);--warn:#e7a072;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 var(--display)}}
main{{max-width:1240px;margin:0 auto;padding-block:24px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
h1{{font-size:26px;margin:0 0 4px;text-wrap:balance}}h2{{font-size:18px;margin:0;text-wrap:balance}}
p{{margin:4px 0}}.small{{font-size:13px;color:var(--muted)}}.lead{{color:var(--muted);max-width:70ch}}code{{font-family:var(--mono);font-size:13px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:18px 0;min-width:0}}
header{{display:flex;gap:14px;align-items:flex-start}}header>div{{min-width:0}}.id{{font:500 22px/1 var(--mono);background:var(--fg);color:var(--bg);border-radius:6px;padding:8px 11px}}
.row{{display:flex;gap:12px;overflow-x:auto;padding-top:12px}}figure{{margin:0;flex:0 0 auto}}figcaption{{font-size:12px;color:var(--muted);margin-top:4px;max-width:230px;font-variant-numeric:tabular-nums}}
.warn figcaption{{color:var(--warn)}}svg{{display:block;border-radius:4px;border:1px solid var(--line);max-width:100%;height:auto}}
.sky{{fill:var(--sky)}}.ground{{fill:var(--ground)}}.fig{{fill:var(--fig)}}.eye{{fill:var(--eye)}}.grid{{stroke:var(--grid);stroke-width:1;stroke-dasharray:3 3;fill:none}}
.tablewrap{{overflow-x:auto}}table{{border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}}td,th{{border-bottom:1px solid var(--line);padding:6px 12px;text-align:left}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(280px,100%),1fr));gap:18px}}.cols section{{margin:0}}ul{{margin:6px 0;padding-left:20px}}
</style><main>
<h1>Photographer: portrait presets A–E</h1>
<p class="lead">Each frame is computed by the same maths the HUD will use (<code>tools/sim/photographer_sim.py</code>): the preset fixes where body
features land, and the camera distance and tilt follow from the avatar's height and the lens. Dashed lines are the thirds; the red dot is the eye
line. The figure is a stand-in, with real perspective. For each preset: two avatar heights, two photo shapes, and the same framing at the
viewer's default lens for comparison.</p>
{"".join(rows)}
<section><h2>Why the lens matters</h2><p class="small">Camera distance for the same framing on a 1.95 m avatar. The viewer's default view is about
21 mm. Close framings at 21 mm put the camera very near the face: big nose, small ears. 85 mm keeps a natural face.</p>
<div class="tablewrap"><table><tr><th>Preset</th><th>21 mm (default)</th><th>35 mm</th><th>50 mm</th><th>85 mm</th></tr>{lens}</table></div></section>
<div class="cols"><section><h2>Group presets (spec only, drawn next round)</h2><ul>{grp}</ul><p class="small">Tallest head sets the top, shortest person
sets the bottom cut, side margins from the 4.4.6 framing (at least 12 % of the frame width).</p></section>
<section><h2>Landscape presets (spec only)</h2><ul>{land}</ul><p class="small">The horizon is placed by the tilt alone, exactly on the line.</p></section></div>
</main>'''
    open(path, "w").write(doc)

if "--html" in sys.argv:
    html(sys.argv[sys.argv.index("--html") + 1])
    print("mock-up page written")
raise SystemExit(0 if ok else 1)
