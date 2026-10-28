# The box

What a buyer receives: one black box. Touch it, and everything in it arrives in one folder, `Take 12 <version>`.
Touch it again any time for a fresh copy. No menu.

| File | What |
|---|---|
| `unpack.lsl` | Shapes the box (0.45 × 0.25 × 0.45 m, matte), puts the three textures on, names it "Take 12 - Cinematic Camera HUD", and hands everything else to its owner on touch |
| `take12_box_front.png` (1024²) | The front and back: the cinema-black board |
| `take12_box_side.png` (512 × 1024) | The two sides: TAKE 12, upright |
| `take12_box_top.png` (1024 × 512) | The lid: the [12] |

The textures are made by `python3 tools/art/make_box.py`.

## Making it in-world
1. Upload the three PNGs, keeping their names: `take12_box_front`, `take12_box_side`, `take12_box_top`.
2. Rez a box (any prim), and drop the three textures into its contents.
3. Drop `unpack.lsl` in (Build › New Script, paste, save). The box shapes and dresses itself.
4. Drop in what the buyer gets:
   - the Take 12 HUD (copy, no-modify, no-transfer);
   - the notecard "Take 12 - Read Me";
   - "Take 12 Scenery (to give a friend)": the free build, copy and transfer.
5. Set the box's own permissions:
   - copy, no-modify, no-transfer;
   - set unpack.lsl to no-modify.

   Then take it into your inventory: that is the Marketplace item.

Test it once: rez it, touch it, and check the folder.
