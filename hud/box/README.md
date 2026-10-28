# The box

What a buyer receives: the Take 12 box, worn the classic way. They right-click it in their inventory and choose
**Add** (or Wear): it shows on the screen as a small card, the Take 12 board, puts everything in it into one folder,
`Take 12 <version>`, says so, and takes itself off, back to the inventory. Wear it again any time for a fresh copy.
No menu.

Rezzed in-world it is a black box, 0.45 × 0.25 × 0.45 m, for a store display; its owner's touch unpacks it too.

| File | What |
|---|---|
| `unpack.lsl` | Worn: the card, the folder, then it detaches itself. Rezzed: shapes the box (full bright), puts the three textures on, names it "Take 12 - Cinematic Camera HUD", and unpacks on its owner's touch |
| `take12_box_front.png` (1024²) | The card on the screen; the box's front and back: the cinema-black board |
| `take12_box_side.png` (512 × 1024) | The box's two sides: TAKE 12, upright |
| `take12_box_top.png` (1024 × 512) | The box's lid: the [12] |

The textures are made by `python3 tools/art/make_box.py`.

## Making it in-world
1. Upload the three PNGs, keeping their names: `take12_box_front`, `take12_box_side`, `take12_box_top`.
2. Rez a box (any prim), and drop the three textures into its contents.
3. Drop `unpack.lsl` in (Build › New Script, paste, save). The box shapes and dresses itself: it keeps the three
   textures' UUIDs in its description and takes the textures out of its contents (as the HUD does with its own), so
   what you ship holds only the script and the things it hands over. Upload the textures as full permission, or it
   cannot read their UUIDs and leaves them in.
4. Drop in what the buyer gets:
   - the Take 12 HUD (copy, no-modify, no-transfer);
   - the notecard "Take 12 - Read Me";
   - "Take 12 Scenery (to give a friend)": the free build, copy and transfer.
5. Set the box's own permissions:
   - copy, no-modify, no-transfer;
   - set unpack.lsl to no-modify.
6. Take it into your inventory, then **wear it once on HUD Center** (right-click › Attach to HUD › Center). It unpacks
   to you and takes itself off; from now on it remembers that HUD point, so a buyer's Add puts it on their screen.
   That inventory item is the Marketplace item.

For a store display, rez a copy of it: rezzed, it is the black box again.
