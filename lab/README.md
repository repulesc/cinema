# The new design (built in the lab)

A second Take 12 HUD with the new design, built here without touching the product, and named simply "Take 12".
Wear one or the other, never both.

**Lab 1 and 2: the Quiet and Direct pages, a floating island, a setup that aligns both ways** (from 8.8.0; the island
reworked in 8.10.0).
- **Quiet** is the default page: one floating island, like the current iPhone's. It has round ends, sits 8 px in from
  the screen's edge and is only as wide as its keys. Left to right:
  - **the x** (let go), a small quiet mark at the far left;
  - **the Orbit** (Auto);
  - **the four shots** (TRACKING · PORTRAIT · FIXED · SCENIC), the filming one bright and underlined (faint in Auto);
  - **the [12]**, then **the frame**, **Connect**, **the shutter**;
  - **`›`** at the right end, which opens Direct.
- **The island never changes its shape** from shot to shot, and nothing opens below it. Only a short prompt (KEEP
  NEW, UNDO) joins its left end while it lasts, and Connect's word (a count, SHARING, THEIR FILM) is as wide as it reads.
- **One tap on a shot directs it.** Tapping the lit shot keeps its job (its next view: Portrait's other side, Scenic's
  next view, and so on). In Auto, a tap on a shot is yours from there.
- **The x:** one tap gives you your viewer's camera. Take 12 stays on (the strip, Connect, the bars); the x turns
  bright and the shots quiet. A tap on the x again, or on a shot, takes the camera back: Auto, if Auto was directing.
  It replaces the 0.8 s holds on the lit shot and the Orbit. Nothing takes the camera back by itself (Idle start
  still shows Scenic while you are away, and gives your camera back when you return; the x still remembers).
- **Direct** is the full strip: the same keys edge to edge, the x and the Orbit at the left end, with the running
  shot's options at the right. `‹` sits where `›` was and folds it back.
- **Moving between them:** `›` opens Direct and `‹` folds it back. Nothing opens or folds by itself, and the page is
  kept for the next wear.
- **The island's black:**
  - a lifted black, so it also shows on the film's black bars;
  - its ends are real round shapes (cylinders facing you), so they are round with any texture;

- **The setup:**
  - on the first wear and after Reset › Everything, a tap on the [12] starts it; the guide card shows at its end
    (8.9.1: it came first and got in the setup's way);
  - its very first step aligns the strip (8.9.1): **Up**, **Down** and **Done**, 10 px a step, so you can go back
    (or **Later**); then the lens, the eye line, the size and the picture;
  - the last step asks for the picture: **Cinema** (the film's black bars) or **Full screen** (none);
  - Settings › Screen › Move in and Move out also move 10 px at a time.
- **Double-tap** the [12] hides everything but the [12], as in the product.

## What is the lab's own
- **Scripts:** only strip, screen, ui and text in `lab/src` are the lab's. The other eight are the product's own, copied from `hud/src` by `tools/build_lab.py`, so they never drift. CI fails if a copy is stale.
- **Builder:** `lab/build/builder.lsl` is the product's builder with four more parts (`t12 tab` and `t12 tab2`, the
  island's round ends; `t12 fold`, the `›` key; `t12 free`, the x, 8.10.0). Touched in a HUD that is already built, it
  adds only the parts that are missing.
- **Textures:**
  - `lab/art/take12_marks_1024.png` is the product's marks with four more cells: `›`, `‹`, the island's round end
    and the x (`tools/art/make_lab.py`);
  - `lab/art/take12_guide_1024.png` is the lab's guide card (`tools/art/make_guide.py`);
  - `lab/art/take12_words_1024.png` is the product's words texture, copied by `tools/build_lab.py` (CI checks it matches).
- **Tests:** `tools/sim/lab_emu.py` runs the real lab scripts. It checks:
  - the pages, and `›` and `‹` in the same place;
  - the island: round ends, its middle, floating, holding every key from the x to `›`, the same shape from shot to
    shot, a prompt at its left end;
  - a tap on a shot directs it, the lit shot's tap keeps its job, a hint's outline on the island;
  - the x: let go and take back, in Auto (Auto again), with a shot or the Orbit after it, while watching a friend's
    film (`connect_emu.py review`), after all off, with nothing filming, and on a HUD without the x part;
  - the setup: alignment first, Up and Down, the guide card at its end, Reset › Everything;
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
6. Tap the [12] for the setup; the guide card shows at its end (tap it closed).
7. `/12 status`: strip says `quiet` or `direct`, and screen says `island found`.

**Updating a lab HUD you already built (8.10.0):** put `lab/build/builder.lsl` and `t12 part` in the HUD and touch it
(it adds the x, `t12 free`), upload the new `take12_marks_1024.png` and `take12_guide_1024.png` and drop them in,
replace the twelve scripts, and wear it again. Until the x part is there, the HUD says once what to do.

## If it proves itself
Its two scripts and three cells move into `hud/`, the guide card's Quiet drawing becomes the product's, and `lab/src`,
`lab/build` and `lab/art` are cleared for the next idea.

## Older experiments
The 7.x-era experiments that used to sit here (the full 4.5.0 Photographer mode, the soft keys concept) are now in
`legacy/old-lab/`, so this folder holds only the Lab.
