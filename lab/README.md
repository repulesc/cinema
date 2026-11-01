# The new design (built in the lab)

A second Take 12 HUD with the new design, built here without touching the product, and named simply "Take 12".
Wear one or the other, never both.

**Lab 1 and 2: the Quiet and Direct pages, a floating island, a setup that aligns both ways** (from 8.8.0).
- **Quiet** is the default page: a floating island, like the current iPhone's. It has round ends, sits 8 px in from the screen's edge, is centred on the [12] and is only as wide as its keys.
  - **Left of the [12]:** the Orbit, the shot that's filming (faint in Auto) and the fold key `›`.
  - **Right of the [12]:** the frame, Connect and the shutter.
  - **While you hold the camera,** the last shot shows faintly in its place; tap it to take it back.
  - **A short prompt** (KEEP NEW, UNDO) shows there too while it lasts.
- **Direct** is the full strip, with three differences from the product:
  - in Auto, all four shots are there to tap;
  - the frame and Connect sit right of the [12];
  - the shutter sits beside Connect.
- **Moving between them:** tap the shot's name or `›` to open Direct, and `‹` (in the same place) to fold it back. Nothing opens or folds by itself, and the page is kept for the next wear.
- **The island's black:**
  - a lifted black, so it also shows on the film's black bars;
  - its ends are real round shapes (cylinders facing you), so they are round with any texture;

- **The setup:**
  - the guide card shows first, on the first wear and after Reset › Everything;
  - the alignment step has **Up**, **Down** and **Done**, 10 px a step, so you can go back;
  - the last step asks for the picture: **Cinema** (the film's black bars) or **Full screen** (none);
  - Settings › Screen › Move in and Move out also move 10 px at a time.
- **Double-tap** the [12] hides everything but the [12], as in the product.

## What is the lab's own
- **Scripts:** only strip, screen, ui and text in `lab/src` are the lab's. The other eight are the product's own, copied from `hud/src` by `tools/build_lab.py`, so they never drift. CI fails if a copy is stale.
- **Builder:** `lab/build/builder.lsl` is the product's builder with three more parts (`t12 tab` and `t12 tab2`, the island's round ends; `t12 fold`).
- **Textures:**
  - `lab/art/take12_marks_1024.png` is the product's marks with three more cells: `›`, `‹` and the island's round end (`tools/art/make_lab.py`);
  - `lab/art/take12_guide_1024.png` is the lab's guide card (`tools/art/make_guide.py`);
  - `lab/art/take12_words_1024.png` is the product's words texture, copied by `tools/build_lab.py` (CI checks it matches).
- **Tests:** `tools/sim/lab_emu.py` runs the real lab scripts. It checks:
  - the pages and the fold key;
  - the island: round ends, its middle, centred, floating, balanced, holding every key;
  - the last shot while you hold the camera;
  - the setup: the guide first, Up and Down, Reset › Everything;
  - KEEP NEW on Quiet;
  - Auto;
  - every window and size with no overlaps;
  - the bottom and the lower places;
  - closed.

## Build it in-world
1. Rez a box. Put `lab/build/builder.lsl` (as a new script) and a blank box named `t12 part` in it, and touch it. It builds the HUD with every part.
2. Add the twelve scripts of `lab/src/`, each as a new script with the file's name.
3. Add the textures. All three are in `lab/art/`:
   - **Words:** `take12_words_1024.png` is the product's own, copied. If you already uploaded `take12_words` for Take 12, drop that copy in; no new upload.
   - **Marks and guide:** upload `take12_marks_1024.png` as `take12_marks_lab` and `take12_guide_1024.png` as `take12_guide_lab`, then drop both in.
   - Any name that starts with `take12_words`, `take12_marks` or `take12_guide` is taken.
4. Optionally add the Read Me.
5. Take the old Take 12 off, take this one and wear it on HUD Top Center.
6. The guide card shows; tap it closed, then tap the [12] for the setup.
7. `/12 status`: strip says `quiet` or `direct`, and screen says `island found`.

## If it proves itself
Its two scripts and three cells move into `hud/`, the guide card's Quiet drawing becomes the product's, and `lab/src`,
`lab/build` and `lab/art` are cleared for the next idea.

## Older experiments
The 7.x-era experiments that used to sit here (the full 4.5.0 Photographer mode, the soft keys concept) are now in
`legacy/old-lab/`, so this folder holds only the Lab.
