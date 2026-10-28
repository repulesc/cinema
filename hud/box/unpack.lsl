// ============================================================================
//  Take 12  -  unpack.lsl  (8.2)  - the box
//  A black box: the Take 12 board on its front and back, the name on its sides, the [12] on its lid (the three
//  textures of tools/art/make_box.py). Dropped into a fresh prim with those textures, it makes the box itself: a
//  0.45 x 0.25 x 0.45 m matte box, each texture on its faces, named "Take 12 - Cinematic Camera HUD".
//  Touch it: everything else in it comes to you in one folder, "Take 12 <version>": the HUD, the Read Me, and a Take 12
//  Scenery to give a friend. No menu, nothing else. Touch it again any time for a fresh copy (a broken script, a lost
//  HUD). Only its owner can unpack it; the textures and this script stay in the box.
// ============================================================================

string VERSION = "8.3.0";
string NAME    = "Take 12 - Cinematic Camera HUD";
list   FACES   = ["take12_box_front", "take12_box_side", "take12_box_top"];

// the box's look, once its textures are in it (faces: 0 the lid, 1 and 3 front and back, 2 and 4 the sides)
shape()
{
    if (llGetInventoryType("take12_box_front") != INVENTORY_TEXTURE) return;
    list P = [PRIM_NAME, NAME, PRIM_SIZE, <0.45, 0.25, 0.45>, PRIM_COLOR, ALL_SIDES, <1.0, 1.0, 1.0>, 1.0,
        PRIM_FULLBRIGHT, ALL_SIDES, FALSE, PRIM_GLOW, ALL_SIDES, 0.0,
        PRIM_TEXTURE, 5, TEXTURE_BLANK, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0, PRIM_COLOR, 5, <0.04, 0.04, 0.04>, 1.0];
    list F = [1, "take12_box_front", 3, "take12_box_front", 2, "take12_box_side", 4, "take12_box_side", 0, "take12_box_top"];
    integer i;
    for (i = 0; i < 10; i += 2)
        if (llGetInventoryType(llList2String(F, i + 1)) == INVENTORY_TEXTURE)
            P += [PRIM_TEXTURE, llList2Integer(F, i), llList2String(F, i + 1), <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0];
    llSetLinkPrimitiveParamsFast(LINK_THIS, P);
}

default
{
    state_entry()
    {
        shape();
    }

    changed(integer c)
    {
        if (c & CHANGED_INVENTORY) shape();                 // the textures dropped in: the box shapes itself
    }

    touch_start(integer n)
    {
        key k = llDetectedKey(0);
        if (k != llGetOwner()) return;
        list L = [];
        integer i;
        for (i = 0; i < llGetInventoryNumber(INVENTORY_ALL); i++)
        {
            string s = llGetInventoryName(INVENTORY_ALL, i);
            if (s != llGetScriptName() && llListFindList(FACES, [s]) < 0) L += [s];
        }
        if (L == []) return;
        llGiveInventoryList(k, "Take 12 " + VERSION, L);
        llOwnerSay("Take 12 is in your inventory, in the folder \"Take 12 " + VERSION + "\". Wear the HUD from there.");
    }
}
