// ============================================================================
//  Take 12  -  unpack.lsl  (8.4)  - the box
//  The box you wear (8.4.0, the classic way): Add or Wear it from your inventory and it shows on your screen as a small
//  card, the Take 12 board, while everything else in it goes to you in one folder, "Take 12 <version>": the HUD, the
//  Read Me, and a Take 12 Scenery to give a friend. Then it takes itself off, back to your inventory; wear it again
//  any time for a fresh copy (a broken script, a lost HUD). No menu.
//  Rezzed in-world it is the black box (a store display): the Take 12 board on its front and back, the name on its
//  sides, the [12] on its lid (tools/art/make_box.py), 0.45 x 0.25 x 0.45 m, matte; its owner's touch unpacks it too.
//  It shapes itself for wherever it is, once the three textures are in it. The textures and this script stay in it.
// ============================================================================

string VERSION = "8.4.0";
string NAME    = "Take 12 - Cinematic Camera HUD";
list   FACES   = ["take12_box_front", "take12_box_side", "take12_box_top"];

// worn: a card on the screen; rezzed: the box (faces: 0 the lid, 1 and 3 front and back, 2 and 4 the sides)
shape()
{
    if (llGetInventoryType("take12_box_front") != INVENTORY_TEXTURE) return;
    list P = [PRIM_NAME, NAME, PRIM_COLOR, ALL_SIDES, <1.0, 1.0, 1.0>, 1.0, PRIM_GLOW, ALL_SIDES, 0.0];
    if (llGetAttached())
    {
        // every side shows the board, so whichever faces you on the HUD is right
        llSetLinkPrimitiveParamsFast(LINK_THIS, P + [PRIM_SIZE, <0.02, 0.22, 0.22>, PRIM_POS_LOCAL, ZERO_VECTOR,
            PRIM_FULLBRIGHT, ALL_SIDES, TRUE, PRIM_TEXTURE, ALL_SIDES, "take12_box_front", <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0]);
        return;
    }
    P += [PRIM_SIZE, <0.45, 0.25, 0.45>, PRIM_FULLBRIGHT, ALL_SIDES, FALSE,
        PRIM_TEXTURE, 5, TEXTURE_BLANK, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0, PRIM_COLOR, 5, <0.04, 0.04, 0.04>, 1.0];
    list F = [1, "take12_box_front", 3, "take12_box_front", 2, "take12_box_side", 4, "take12_box_side", 0, "take12_box_top"];
    integer i;
    for (i = 0; i < 10; i += 2)
        if (llGetInventoryType(llList2String(F, i + 1)) == INVENTORY_TEXTURE)
            P += [PRIM_TEXTURE, llList2Integer(F, i), llList2String(F, i + 1), <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0];
    llSetLinkPrimitiveParamsFast(LINK_THIS, P);
}

// everything in it but this script and the textures, to its owner in one folder
integer unpack()
{
    list L = [];
    integer i;
    for (i = 0; i < llGetInventoryNumber(INVENTORY_ALL); i++)
    {
        string s = llGetInventoryName(INVENTORY_ALL, i);
        if (s != llGetScriptName() && llListFindList(FACES, [s]) < 0) L += [s];
    }
    if (L == []) return FALSE;
    llGiveInventoryList(llGetOwner(), "Take 12 " + VERSION, L);   // (Second Life pauses the script 3 s: the card stays)
    llOwnerSay("Take 12 is in your inventory, in the folder \"Take 12 " + VERSION + "\". Wear the HUD from there.");
    return TRUE;
}

default
{
    state_entry()
    {
        shape();
    }

    on_rez(integer p)
    {
        shape();                                            // worn or rezzed: its look for there
    }

    changed(integer c)
    {
        if (c & CHANGED_INVENTORY) shape();                 // the textures dropped in: it shapes itself
    }

    attach(key id)
    {
        if (id == NULL_KEY) return;
        shape();
        llSetText("Unpacking Take 12 …", <1.0, 1.0, 1.0>, 1.0);
        unpack();
        llSetText("", ZERO_VECTOR, 0.0);
        llRequestPermissions(llGetOwner(), PERMISSION_ATTACH);   // granted at once to the wearer
    }

    run_time_permissions(integer p)
    {
        if ((p & PERMISSION_ATTACH) && llGetAttached()) llDetachFromAvatar();   // back to your inventory
    }

    touch_start(integer n)
    {
        if (llDetectedKey(0) != llGetOwner() || llGetAttached()) return;
        unpack();
    }
}
