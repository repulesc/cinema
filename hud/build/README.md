# Building the Take 12 HUD (8.0)

The HUD is one linked object of 28 prims (the root and 27 parts). A builder script makes it, so nobody has to link
and name parts by hand. HUD prims have no land impact.

1. **Rez a box** on land where you may build. It becomes the root, the [12].
2. **Make the part:** rez a second box, name it `t12 part`, take it into your inventory and drop it into the first
   box's contents.
3. **Drop `hud/build/builder.lsl`** into the first box (New Script, paste, save).
4. **Touch the box** and allow it to link. It rezzes the 27 parts one by one (about a second each), links each one,
   names it (`t12 ring`, `t12 s0`, … `t12 bar3`, `t12 shut`, docs/ARCHITECTURE.md §1) and lays it flat inside the box. When it is
   done it says so, and takes `t12 part` and itself out of the contents. Touching it again on a HUD that misses parts
   adds only the missing ones.
5. **Add the scripts:** the 12 files of `hud/src/` (core, ui, text, screen, strip, bars, tracking, portrait, fixed, scenic,
   sync, carry), each as a new script with the file's name. Optionally a sound for the Connect chime (any sound in the
   contents; Settings › Friends › Chime turns it off).
6. **The textures:** upload `hud/art/take12_words_1024.png` and `hud/art/take12_marks_1024.png` once (name them
   `take12_words` and `take12_marks`) and drop both into the HUD. The screen script keeps their UUIDs in the root's
   description and takes them out of the contents, so the HUD can be given away (full-permission textures are not
   needed in the copy you sell).
7. **Take it and wear it on HUD Top Center.** A note under the [12] says "Tap the [12] to set up."

Notes
- The HUD can be worn on any HUD point: it lays itself out from the point it is on.
- If parts look misplaced after a viewer's HUD zoom, use the viewer's "reset HUD zoom" (the guide says how).
- `/12 status` prints one line per script, with its free memory, and whether the parts and the textures were found.
