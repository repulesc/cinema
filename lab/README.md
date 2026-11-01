# Take 12 Lab

A separate HUD for trying ideas that may one day become the product, without touching the product. Wear one or the
other, never both: take Take 12 off before wearing the Lab.

**Lab 1: the Quiet and Direct pages** (from 8.8.0).
- **Quiet** is the default page. One short notch at the top, only as wide as its words:
  - the Orbit;
  - the shot that's filming (faint in Auto);
  - the fold key `›`;
  - the frame;
  - the [12];
  - Connect, with the shutter beside it.

  A short prompt (KEEP NEW, UNDO) shows there too while it lasts.
- **Direct** is the product's full strip, with two differences:
  - in Auto, all four shots are there to tap;
  - the shutter sits beside Connect.
- **Moving between them:** tap the shot's name or `›` to open Direct, and `‹` (in the same place) to fold it back. Nothing opens or folds by itself, and the page is kept for the next wear.
- **The notch** has rounded lower corners and keeps its width from shot to shot. Where the film's top bar is at least as tall as the strip (2.39, 2.00), it disappears into the bar.
- **Double-tap** the [12] hides everything but the [12], as in the product.
- **The guide card** shows the Quiet page.

## What is the lab's own
- **Scripts:** only `lab/src/strip.lsl` and `lab/src/screen.lsl` are the lab's. The other ten are the product's own, copied from `hud/src` by `tools/build_lab.py`, so they never drift. CI fails if a copy is stale.
- **Builder:** `lab/build/builder.lsl` is the product's builder with two more parts (`t12 tab`, `t12 fold`) and the root named "Take 12 Lab".
- **Textures:**
  - `lab/art/take12_marks_1024.png` is the product's marks with three more cells: `›`, `‹` and the notch (`tools/art/make_lab.py`);
  - `lab/art/take12_guide_1024.png` is the lab's guide card (`tools/art/make_guide.py`);
  - `lab/art/take12_words_1024.png` is the product's words texture, copied by `tools/build_lab.py` (CI checks it matches).
- **Tests:** `tools/sim/lab_emu.py` runs the real lab scripts. It checks:
  - the pages and the fold key;
  - the notch;
  - KEEP NEW on Quiet;
  - Auto;
  - every window and size with no overlaps;
  - the bottom and the lower places;
  - closed.

## Build it in-world
1. Rez a box. Put `lab/build/builder.lsl` (as a new script) and a blank box named `t12 part` in it, and touch it. It builds "Take 12 Lab" with every part.
2. Add the twelve scripts of `lab/src/`, each as a new script with the file's name.
3. Add the textures. All three are in `lab/art/`:
   - **Words:** `take12_words_1024.png` is the product's own, copied. If you already uploaded `take12_words` for Take 12, drop that copy in; no new upload.
   - **Marks and guide:** upload `take12_marks_1024.png` as `take12_marks_lab` and `take12_guide_1024.png` as `take12_guide_lab`, then drop both in.
   - Any name that starts with `take12_words`, `take12_marks` or `take12_guide` is taken.
4. Optionally add the Read Me.
5. Take Take 12 off, take the Lab and wear it on HUD Top Center.
6. Run the setup once (tap the [12]); it ends on the lab's guide card.
7. `/12 status`: strip says `lab quiet` or `lab direct`, and screen says `lab notch found`.

## If it proves itself
Its two scripts and three cells move into `hud/`, the guide card's Quiet drawing becomes the product's, and `lab/src`,
`lab/build` and `lab/art` are cleared for the next idea.

## Older work kept here (not built, not checked by CI)
- **`frame-full-4.5.0/`**: the full 4.5.0 "Photographer" mode, with four subjects (you, a picked person, a group, the
  landscape), five framings each, photo shapes 16:9 / 4:3 / 3:2, a lens line in mm, and its own menus and person picker.
  Take 12 ships a slim version of it as Frame (`hud/src/frame.lsl`). This is the starting point for a
  possible later, more serious composition tool. `photographer_sim.py` there still runs
  (`python3 lab/frame-full-4.5.0/photographer_sim.py`) and checks its own script.
- **`softkeys/`**: a concept for up to five quiet keys beside the clapper, shown only in a few busy moments (live as
  the director, Freehand, Still), with a mockup (`python3 lab/softkeys/make_mockup.py`). To decide; nothing is built.
