# Framing › Me (7.0; Frame 4.6, Still 5.x–6.8)

A held, well-composed view for your own snapshots. It follows the product principles (docs/PRODUCT.md): it decides,
you accept or skip; nothing to set; nothing on screen but the framing's name for a moment.

## What it does
- **Subject, automatic:** you, or you and whoever stands within 3 m at about your level (up to 5 people), framed as a
  group. Looked at again at every new framing and when you stop walking; a zoom change keeps the same people.
- **Three framings**, double-tap = next:

| | You | You with others |
|---|---|---|
| Full length | head top at y 0.80 (10 % air), feet at −0.84 (8 %), camera at hip height, 15° round from the nose, centred | tallest head at 0.80, lowest feet at −0.84, camera at 60 % of the mean height |
| Half length | eyes on the golden line (y 0.236, 38.2 % from the top), belt at the bottom, camera at eye level, 30° round, on the golden line across (x 0.236, lead room) | eyes on the golden line, the lowest mid-thigh at the bottom |
| Close | eyes on the golden line, chest at the bottom, camera just above the eyes, 25° round, x 0.2 | eyes on the golden line, the lowest belt at the bottom |

(6.6: the golden line replaced the third, and full length got its air; it was 0.86 / −0.88.) **Inside the Frame format** (`cin.crop` R on your window `cin.aspect` A, written by `crop.lsl`): across, x is a fraction of the format's half-width (aspect R); a format wider than the window is a shorter picture, so the half-height tangent is `tan(FOV/2) · A / R`; groups are fitted to R exactly (16:10 only without a format). `crop` sends `CFG_CHANGED "crop"`, and Still re-frames at once.

- **Held:** no timer cuts, and the camera never moves by itself. **Tap** leaves.
- **7.0: it moves, then holds** (Framing › Me). The movement keys walk you (core passes them on and sends NUDGE).
  While you move, the camera and its focus travel by your step five times a second (a GLIDE), so the picture stays;
  1 s after you let go, once you stand still, it composes the current framing again in front of you (a glide; the
  people near you looked at again). There are no nudges: Freehand is the manual camera, Fit (Page Up / Down) the
  height of your body.
- **The zoom is silent:** the distance follows the viewer's field of view, re-solved 0.8 s after the zoom settles,
  so the picture keeps its size and only the perspective changes. Never closer than 1.2 m: at the wide default
  zoom, Close on a short avatar comes out a little looser. The Read Me has one line on zooming in.
- **Seated:** the eyes from the sitting estimate, each framing a set drop below them.
- **Obstacles:** tried 15° and 30° either side, then from the other side; a group that does not fit becomes just you.

## The maths
Two body heights are fixed to two screen lines. With camera height zc, horizontal distance D and tilt φ, a height z
shows at `y = tan(atan((z − zc) / D) + φ) / tan(FOV / 2)`. The angle between the two anchors shrinks as D grows, so
D is found by bisection (28 steps) and φ follows. Groups: the tallest head never above 0.9, side room for a 16:10
window (or the Frame format) with the 4.4.6 margin (1.3). Checked by `tools/sim/frame_sim.py` (in CI), which also compares the script's
tables with the tested ones.

## Calibration (in-world, once)
Body heights are fractions of `llGetAgentSize().z`: top 1.00, eyes 0.935, shoulders 0.82, chest 0.72, belt 0.56,
mid-thigh 0.38, feet 0. Two snapshots of Half length (a short and a tall shape) show where the eyes really land; the
fractions are corrected from them.

## The lens guide and the slide (5.9)
- **The lens:** each framing names a classic portrait lens (35 mm equivalent, 24 mm frame height): Full length
  50 mm, Half length 85 mm, Close 105 mm. Yours is `12 / tan(FOV / 2)` from the viewer's field of view (60° ≈ 21 mm).
  Frame sends STILL 7381 `"<framing>|<lens>|<yours>"` at every shot and glide, and at once on every FOVMSG, so the
  readout follows the keys live. `tips` shows `○ Me · Close · 105 mm ✓` (within 15 %) or
  `… · 105 mm · now 21 · Ctrl+0` (Ctrl+8 when the lens is too long). A script can read the zoom, never set it; only
  the user can (Ctrl+0 in, Ctrl+8 out, Ctrl+9 back). At the recommended lens every framing keeps its exact lines
  (never pushed back to DMIN). Frame writes no text itself any more: the framing name is in that line.

## The same rule everywhere (6.0)
Since 6.0 every camera follows the zoom with the rule Frame started with: the lens changes the perspective, never
the size. See ARCHITECTURE (FOVMSG) and tools/sim/zoom_sim.py.

## Left out on purpose
Picking another person, landscapes, photo shapes, menus of its own. They live in
`lab/frame-full-4.5.0/`, the starting point for a possible later composition tool.
