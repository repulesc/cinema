// ============================================================================
//  Take 12  -  unpack.lsl  (8.4)  - the box
//  The box you wear (8.4.0, the classic way): Add or Wear it from your inventory and it shows on your screen as a small
//  card, the Take 12 board, while everything else in it goes to you in one folder, "Take 12 <version>": the HUD, the
//  Read Me, and a Take 12 Scenery to give a friend. Then it takes itself off, back to your inventory; wear it again
//  any time for a fresh copy (a broken script, a lost HUD). No menu.
//  Rezzed in-world it is the black box (a store display): the Take 12 board on its front and back, the name on its
//  sides, the [12] on its lid (tools/art/make_box.py), 0.45 x 0.25 x 0.45 m, full bright (worn and rezzed); its owner's touch unpacks it too.
//  It shapes itself for wherever it is, once the three textures are in it: it keeps their UUIDs in its description and
//  takes the textures out of its contents (as the HUD does), so only the script stays with what it hands over.
// ============================================================================

string VERSION = "8.9.0";
string NAME    = "Take 12 - Cinematic Camera HUD";
list   FACES   = ["take12_box_front", "take12_box_side", "take12_box_top"];

// the textures dropped in become UUIDs kept in the description ("f <uuid>;s <uuid>;t <uuid>": a description holds only
// 127 characters, and three full names with their UUIDs were cut off: the lid went missing), and leave the contents
// (like the HUD's own textures), so the box can be given away without them
string tag(string n)
{
    return llGetSubString(n, 12, 12);                         // take12_box_front / side / top: f, s, t
}

adopt()
{
    integer i;
    for (i = 0; i < 3; i++)
    {
        string n = llList2String(FACES, i);
        key k = NULL_KEY;                                   // (not full permission: no key, it stays and is used by name)
        if (llGetInventoryType(n) == INVENTORY_TEXTURE) k = llGetInventoryKey(n);
        if (k != NULL_KEY)
        {
            list D = llParseString2List(llGetObjectDesc(), [";"], []);
            integer j;
            for (j = llGetListLength(D) - 1; j >= 0; j--)
                if (llGetSubString(llList2String(D, j), 0, 1) == tag(n) + " " || llSubStringIndex(llList2String(D, j), "take12_box") == 0)
                    D = llDeleteSubList(D, j, j);            // (the long form of 8.4.0 goes: it was cut at 127 characters)
            llSetObjectDesc(llDumpList2String(D + [tag(n) + " " + (string)k], ";"));
            llRemoveInventory(n);
        }
    }
}

// a texture by its kept UUID, else by its name in the contents, else blank
string tex(string n)
{
    list D = llParseString2List(llGetObjectDesc(), [";"], []);
    integer j;
    for (j = 0; j < llGetListLength(D); j++)
        if (llGetSubString(llList2String(D, j), 0, 1) == tag(n) + " ") return llGetSubString(llList2String(D, j), 2, -1);
    if (llGetInventoryType(n) == INVENTORY_TEXTURE) return n;
    return "";
}

// worn: a card on the screen; rezzed: the box (faces: 0 the lid, 1 and 3 front and back, 2 and 4 the sides)
shape()
{
    string front = tex("take12_box_front");
    if (front == "") return;
    list P = [PRIM_NAME, NAME, PRIM_COLOR, ALL_SIDES, <1.0, 1.0, 1.0>, 1.0, PRIM_GLOW, ALL_SIDES, 0.0];
    if (llGetAttached())
    {
        // every side shows the board, so whichever faces you on the HUD is right
        llSetLinkPrimitiveParamsFast(LINK_THIS, P + [PRIM_SIZE, <0.02, 0.22, 0.22>, PRIM_POS_LOCAL, ZERO_VECTOR,
            PRIM_FULLBRIGHT, ALL_SIDES, TRUE, PRIM_TEXTURE, ALL_SIDES, front, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0]);
        return;
    }
    P += [PRIM_SIZE, <0.45, 0.25, 0.45>, PRIM_FULLBRIGHT, ALL_SIDES, TRUE,
        PRIM_TEXTURE, 5, TEXTURE_BLANK, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0, PRIM_COLOR, 5, <0.04, 0.04, 0.04>, 1.0];
    list F = [1, "take12_box_front", 3, "take12_box_front", 2, "take12_box_side", 4, "take12_box_side", 0, "take12_box_top"];
    integer i;
    for (i = 0; i < 10; i += 2)
    {
        string t = tex(llList2String(F, i + 1));
        if (t != "") P += [PRIM_TEXTURE, llList2Integer(F, i), t, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0];
    }
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
        adopt();
        shape();
    }

    on_rez(integer p)
    {
        shape();                                            // worn or rezzed: its look for there (by the kept UUIDs)
    }

    changed(integer c)
    {
        if (c & CHANGED_INVENTORY)
        {
            adopt();                                        // the textures dropped in: their UUIDs kept, the textures out
            shape();
        }
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
