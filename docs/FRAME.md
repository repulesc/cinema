# Frame (4.6)

A held, well-composed view for your own snapshots. It follows the product principles (docs/PRODUCT.md): it decides,
you accept or skip; nothing to set; nothing on screen but the framing's name for a moment.

## What it does
- **Subject, automatic:** you, or you and whoever stands within 3 m at about your level (up to 5 people), framed as a
  group. Looked at again at every new framing; a nudge or a zoom change keeps the same people.
- **Three framings**, double-tap = next:

| | You | You with others |
|---|---|---|
| Full length | head top at y 0.86, feet at −0.88, camera at hip height, 15° round from the nose, centred | tallest head at 0.84, lowest feet at −0.86, camera at 60 % of the mean height |
| Half length | eyes on the upper third, belt at the bottom, camera at eye level, 30° round, on a third (lead room) | eyes on the third, the lowest mid-thigh at the bottom |
| Close | eyes on the upper third, chest at the bottom, camera just above the eyes, 25° round | eyes on the third, the lowest belt at the bottom |

- **Held:** no timer cuts, and the camera never moves by itself. **Tap** leaves.
- **Movement keys nudge** (you stand still meanwhile): W/S closer or further, A/D round, E/C higher or lower with
  the tilt re-solved. The next framing clears the nudges.
- **The zoom is silent:** the distance follows the viewer's field of view, re-solved 0.8 s after the zoom settles,
  so the picture keeps its size and only the perspective changes. Never closer than 1.2 m: at the wide default
  zoom, Close on a short avatar comes out a little looser. The Read Me has one line on zooming in.
- **Seated:** the eyes from the sitting estimate, each framing a set drop below them.
- **Obstacles:** tried 15° and 30° either side, then from the other side; a group that does not fit becomes just you.

## The maths
Two body heights are fixed to two screen lines. With camera height zc, horizontal distance D and tilt φ, a height z
shows at `y = tan(atan((z − zc) / D) + φ) / tan(FOV / 2)`. The angle between the two anchors shrinks as D grows, so
D is found by bisection (28 steps) and φ follows. Groups: the tallest head never above 0.9, side room for a 16:10
window with the 4.4.6 margin (1.3). Checked by `tools/sim/frame_sim.py` (in CI), which also compares the script's
tables with the tested ones.

## Calibration (in-world, once)
Body heights are fractions of `llGetAgentSize().z`: top 1.00, eyes 0.935, shoulders 0.82, chest 0.72, belt 0.56,
mid-thigh 0.38, feet 0. Two snapshots of Half length (a short and a tall shape) show where the eyes really land; the
fractions are corrected from them.

## Left out on purpose
Picking another person, landscapes, photo shapes, lens advice on screen, menus of its own. They live in
`lab/frame-full-4.5.0/`, the starting point for a possible later composition tool.
