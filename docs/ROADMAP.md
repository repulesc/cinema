# Take 12: Roadmap (v4)

What we build: `docs/PRODUCT.md`. How: `docs/ARCHITECTURE.md`. v3 is frozen and working in `legacy/v3/`.

## Status
| Phase | What | Who | State |
|---|---|---|---|
| v3.0.0 | Scenery default, Personal and Social | done | ✅ works in-world, frozen in `legacy/v3/` |
| 4.0 · Phase A | Quiz round 3, spec, architecture, roadmap, icon art, legacy split | Opus | ✅ this commit |
| 4.0 · Phase B | Code v4 (milestones B1–B7 below), one release | Sonnet | ✅ coded, checked by compile and sims |
| 4.0 · Phase C | In-world test by the user, then tuning | User, then Sonnet | ⏳ next |
| 4.4.x | Beta polish from in-world tests: indoor mode, quiet chat, calm people cameras, reach learning, people framing, clearer texts | Opus | ⏳ ongoing |
| Frame | A slim, held picture of you (or you and the people with you): Full length, Half length, Close. 4.6.0 (`frame.lsl`). Next: in-world test, body calibration | Opus | ⏳ in-world test |
| Composition tool (later) | A fuller, more serious version, starting from `lab/frame-full-4.5.0/` (subjects, landscapes, photo shapes, lens guidance). Only after Take 12 is out of beta | – | 💤 later |
| Lite | Paused, frozen at 4.4.5. **Resume** once the full version leaves beta: steps in `hud-lite/README.md` | – | ⏸ paused |
| Later | Backlog at the bottom, only on request | – | – |

## Rules for Sonnet (read first)
1. **Work only in `hud/`, `tools/` and `docs/`.** Never edit `legacy/`.
2. After **every** milestone:
   - `bash tools/lslcheck.sh` must show OK for all scripts, each **≥ 15 KB free**;
   - every sim must print ALL PASS.
3. Use the LSL gotchas from v3. Breaking any of these has broken builds before:
   - No variables named after events (`changed`, `touch`, `timer`, …) or `jump`.
   - No member access on a call result (`llList2Vector(l, 0).z`); go through a temp variable.
   - Define a function before it is used. Declare every global.
   - `llDialog` buttons ≤ 24 bytes; an emoji is 3–4 bytes.
4. Every script gets `VERSION = "4.0.0"` and keeps `PASS` the same across scripts.
5. Don't add features that are not in PRODUCT.md. No letterbox, no fades, no window shots.
6. One commit per milestone on `claude/sweet-noether-r09sjj`, with a clear message. Push at the end; CI must be green.

## Phase B: build v4.0.0 (Sonnet), done
All seven milestones are coded in `hud/src/`. Deviations from the plan:
- A sixth script, `picker.lsl`, holds the Friends menu and picker, because `friends` alone came out at 10.5 KB free.
- The favourites case in `scenery_sim.py` was **not** added (only compile-checked).
- B6: the texture default stays "rec" until the user picks a variant on the design board.
- The friends sim found a real fit bug, now fixed (depth-aware fit).

The checklists below are kept as the record of what was specified.

### B1 · Gestures, look and menu (core + ui)
- [ ] Core:
  - remove the touch handlers;
  - add the CMDs `next`, `photo`, `fav`, `friends` (accepting `friends` for now; the worker comes in B5);
  - UI_STATE becomes `state|mode|nextCut` (ARCH §3).
- [ ] UI:
  - the touch decoder (ARCH §4.1);
  - `setLook` with alpha 1.0 / 0.15, the clap offset and no colours (§4.2).
- [ ] UI: table-driven emoji menus with the text fallback, `order()`, and the pages main, live, pace, afk, opts and sub-pages (§4.3). Copy the labels exactly from PRODUCT.md.
- [ ] UI:
  - the first-run welcome dialog;
  - the 60 s listener timeout;
  - the count-agnostic version warning;
  - the commands `pace`, `next`, `photo`, `fav`, `friends`, `emoji`, `cutmode`, `indoors`, `reach relearn`.
- [ ] `tools/sim/tap_test.py` and the CI step.
- **Accept:** lslcheck OK; tap_test ALL PASS; ui ≥ 17 KB and core ≥ 23 KB estimated.

### B2 · Photo hold and favourites
- [ ] Core: FREEZE state, the `photo` toggle, `next` from FREEZE, and the mouselook/teleport pause returning to FREEZE (ARCH §3).
- [ ] Core → scenery FAV; scenery stores and uses favourites (§6.4). UI: Options › Favourites › Clear here / Clear all.
- **Accept:** lslcheck OK. Add a scenery_sim case where a favourite is chosen every 4th cut and skipped when it is out of reach.

### B3 · Room-aware scenery
- [ ] Scenery: the room classifier (§6.2) and `findRoomShot` (§6.3) with the fallback to outdoor logic. Options › Indoors (Auto / Inside / Outside) and `/77 indoors`.
- [ ] Reach regrowth (§6.5).
- [ ] `tools/sim/room_sim.py` with the 6 worlds from §9, and the CI step. *(4.4.0: replaced by `indoor_sim.py`, see ARCHITECTURE §6.2–6.3 and §9.)*
- **Accept:** room_sim ALL PASS, and scenery_sim still ALL PASS. Scenery ≥ 22 KB.

### B4 · Chat cuts in Social
- [ ] People: the `llListen(0)` lifecycle, speaker events, and over-the-shoulder shots toward the speaker (§7).
- [ ] Core: SPEAKER on owner typing in Social and Friends, and no bail (§3).
- **Accept:** people_geometry still ALL PASS. Add a case: the speaker shot keeps the 180-degree side and puts the speaker on screen.

### B5 · Friends mode
- [ ] New `friends.lsl` (§5):
  - the presence scan, `planF`, the glide and snap loop, chat cuts;
  - the Friends page and the picker.
- [ ] Core: GLIDE handling, clearing the lag after a glide, skipping peek while gliding (§3).
- [ ] UI: 💞 Friends → UI_FRIENDS `page`, and `friend list|clear`.
- [ ] `tools/sim/friends_sim.py`, and the CI step.
- **Accept:** friends_sim ALL PASS; friends ≥ 20 KB.

### B6 · Art in the prim
- [ ] Copy the chosen variant from the design board as the default in `tools/art/make_icon.py`, then regenerate `hud/art/`.
- [ ] Write the README build steps: box size, HUD Top Right, the face, repeats and offset (ARCH §8).

### B7 · Docs and release
- [ ] Rewrite the notecard (now `hud/notecard/read_me.txt`) for v4: gestures table, menu tour, the four modes, Photo, Favourites, Indoors and FAQ.
- [ ] Update `README.md` (five scripts, `hud/`, the art), add `CHANGELOG.md` 4.0.0, and add the v4 rows to the `docs/CALIBRATION.md` table.
- [ ] Final run of lslcheck plus all sims, push, and confirm CI is green.

## Phase C: in-world test (user)
Install:
1. Make a fresh prim from the README.
2. Add the six scripts from `hud/src/`.
3. Use **Set Scripts to Running**.
4. Upload `hud/art/take12_icon_sheet_512x256.png` and apply it as the README says.

Then report:

| # | Try | Expect |
|---|---|---|
| 1 | Wear it | The welcome dialog appears once. The button is a crisp pixel clapper, top right, small |
| 2 | Tap | The menu opens after a short beat. Emoji show on the buttons (or set 🔤 Emoji off) |
| 3 | Double-tap | The clapper claps, the button fades out, and the Scenery camera starts |
| 4 | While rolling, double-tap | Next shot |
| 5 | While rolling, tap | Your camera is back and the button is fully visible again |
| 6 | While rolling, long press → 📷 Photo | The shot freezes and the camera stays on it. A tap resumes |
| 7 | Long press → ⭐ Save, twice in different spots. Keep rolling 10+ cuts | Your saved spots come back now and then |
| 8 | Go to a skybox, then Scenery | Corner, centre and you-small views inside the room. The trace says "inside a room" |
| 9 | A house on the ground, then Scenery | Views from outside and above the roof (as v3) |
| 10 | 💞 Friends › ➕ Pick, add one or two people, ▶ Start | The group is framed. Walking: a slow glide. Someone runs off: a snap to a wider shot in about 1 s |
| 11 | Social or Friends: someone talks in local chat | A cut to them within about 6 s (not more often than every 10 s). You typing gives a cut to you, and the camera keeps rolling |
| 12 | `/77 status` | Six lines, one per script, with free memory |

Send the `scenery:` / `friends:` trace lines and anything odd.

**Tuning numbers to watch** (recorded in CALIBRATION.md):
- the tap window of 0.35 s and the long press of 0.8 s;
- the fade of 15 %;
- glide lag 1.5 s and the 0.4 m threshold;
- the snap after 1 s;
- room height caps;
- the chat-cut cooldown of 10 s.

## Critiques and fixes from the v3 review (folded into Phase B)
| # | Issue in v3 | Fix (milestone) |
|---|---|---|
| 1 | The button colour was the only feedback, and it was ugly and visible in snapshots | Alpha fade and clap (B1) |
| 2 | A long press was needed for the menu and nothing else was discoverable | Tap = menu, plus a welcome dialog (B1) |
| 3 | The reach learning only ever shrinks | Regrow 10 % after 20 clean cuts, plus Re-learn (B3) |
| 4 | Typing ended Social, even though chatting is the point of Social | Typing becomes a speaker cut (B4) |
| 5 | Indoors in a skybox, the camera went "above the roof", into the void | Room-aware scenery (B3) |
| 6 | The version warning said "four scripts" | Count-agnostic (B1) |
| 7 | The welcome was a long chat paragraph | A dialog (B1) |
| 8 | "Hold" was a technical word | "Pace" with names (B1) |
| 9 | "Cut mode" was an obscure menu item | Command-only (B1) |

## Later / maybe (only if the user asks)
- Seated-scene awareness: when you sit with friends on a couch, compose for seated eye lines (partly there: `K_EYE_SIT`).
- A per-region memory of the best scenery spots it found itself, beyond the manual favourites.
- An optional "golden hour" bias: prefer west- or east-facing views near sunrise and sunset (`llGetSunDirection`). This is risky; it could be a gimmick.
- A notecard-configured friends list for groups who always meet together.
- A "Cinema Classic" listing of the frozen v3 for buyers who want the simple version.
