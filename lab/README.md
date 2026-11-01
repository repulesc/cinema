# Take 12 Lab

A separate HUD for trying ideas that may one day become the product, without touching the product. Wear one or the
other, never both: take Take 12 off before wearing the Lab.

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
  - its ends are two discs and its middle a black part, so the ends stay round at any width;
  - where the film's top bar is taller than the island (2.39, 2.00), the island sits inside the bar and only its keys show;
  - with a thin bar (1.85) it touches the bar.
- **The setup:**
  - the guide card shows first, on the first wear and after Reset › Everything;
  - the alignment step has **Up**, **Down** and **Done**, 10 px a step, so you can go back;
  - Settings › Screen › Move in and Move out also move 10 px at a time.
- **Double-tap** the [12] hides everything but the [12], as in the product.

## What is the lab's own
- **Scripts:** only strip, screen, ui and text in `lab/src` are the lab's. The other eight are the product's own, copied from `hud/src` by `tools/build_lab.py`, so they never drift. CI fails if a copy is stale.
- **Builder:** `lab/build/builder.lsl` is the product's builder with three more parts (`t12 tab` and `t12 tab2`, the island's ends; `t12 fold`) and the root named "Take 12 Lab".
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
1. Rez a box. Put `lab/build/builder.lsl` (as a new script) and a blank box named `t12 part` in it, and touch it. It builds "Take 12 Lab" with every part.
2. Add the twelve scripts of `lab/src/`, each as a new script with the file's name.
3. Add the textures. All three are in `lab/art/`:
   - **Words:** `take12_words_1024.png` is the product's own, copied. If you already uploaded `take12_words` for Take 12, drop that copy in; no new upload.
   - **Marks and guide:** upload `take12_marks_1024.png` as `take12_marks_lab` and `take12_guide_1024.png` as `take12_guide_lab`, then drop both in.
   - Any name that starts with `take12_words`, `take12_marks` or `take12_guide` is taken.
4. Optionally add the Read Me.
5. Take Take 12 off, take the Lab and wear it on HUD Top Center.
6. Run the setup once (tap the [12]); it ends on the lab's guide card.
7. `/12 status`: strip says `lab quiet` or `lab direct`, and screen says `lab island found`.

**Updating a Lab built before lab 2:**
1. Put the builder (`lab/build/builder.lsl`) and `t12 part` back in the Lab HUD and touch it. It adds only the missing part, `t12 tab2`.
2. Replace the lab's four own scripts: strip, screen, ui and text, from `lab/src`.
3. Upload `take12_marks_1024.png` and `take12_guide_1024.png` from `lab/art` again, and drop them in.

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
