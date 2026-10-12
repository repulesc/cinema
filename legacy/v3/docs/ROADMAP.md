# Cinema HUD: Roadmap

## Phase 1: v3.0.0, everything at once (this delivery)
1. Write the spec (`docs/PRODUCT.md`) and the technical design (`docs/ARCHITECTURE.md`), built from the round-2 quiz.
2. Rewrite the scripts from scratch around the scenery camera:
   - `cinema_core.lsl` owns the camera, the modes, the triggers and exits, the watchdog, and a basic fallback shot for each mode.
   - `cinema_scenery.lsl` is the default mode. It is the drone / wide spot finder (rays, region-bounded, above the roof, reach learning).
   - `cinema_people.lsl` holds the optional Personal (follow-me) and Social (pairs / groups) modes.
   - `cinema_ui.lsl` holds the long-press menu, `/77` commands and settings.
3. Compile-check every script with LSL-PyOptimizer (`tools/lslcheck.sh`, also run in GitHub Actions). Estimate free memory: each script needs ≥ 15 KB.
4. Check the scenery spot geometry with a Python port. The camera must stay inside the region and above the top surface, the view must be unblocked, and the pitch must stay in range.
5. Update the user guide, README and changelog. Push to PR #2.

## Phase 2: in-world verification (you, then me)
1. Install the 4 scripts and set them running. Each prints `ready` with its free memory.
2. Tap: within 2 s the view cuts to a scenery shot. Leave it for a few minutes: shots come from varied directions and heights, and nothing blocks them.
3. Try indoors: the camera should go above the roof.
4. Try *Personal* and *Social* from the menu.
5. Report back: chat lines (`/77 status`, `trace` lines) and anything that looks wrong. I tune the numbers: eye height, drone heights, pitch, distances, hold times. I also learn your viewer's real camera reach (the HUD reports it).

## Phase 3: polish (only what you ask for)
Possible later items: letterbox bars, dip-to-black between far cuts, saving favourite spots, speaker cuts in Social, style presets.
