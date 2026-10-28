// ============================================================================
//  Take 12  -  builder.lsl  (8.0)  - builds the HUD object (not shipped)
//  Rez a box, put this script and one blank box named "t12 part" in its contents, and touch it. It asks to link,
//  rezzes the parts one by one, links each to the box, names it, and lays it flat in the box; the box becomes the
//  root, "Take 12". When every part is there it takes "t12 part" and itself out of the contents. Touching it again on
//  a HUD that misses parts adds only the missing ones. Then add the scripts of hud/src, drop the two textures in,
//  take it and wear it on HUD Top Center (hud/build/README.md).
// ============================================================================

list    PARTS = ["t12 ring", "t12 dot", "t12 band", "t12 s0", "t12 s1", "t12 s2", "t12 s3", "t12 box", "t12 halo",
                 "t12 o0", "t12 o1", "t12 o2", "t12 o3", "t12 o4", "t12 o5", "t12 sep", "t12 u0", "t12 u1", "t12 u2",
                 "t12 shape", "t12 link", "t12 note", "t12 bar0", "t12 bar1", "t12 bar2", "t12 bar3", "t12 shut"];
string  PART  = "t12 part";

key     gOwner;
list    gTodo;                      // the parts still to make
key     gNew = NULL_KEY;            // the part just rezzed, waiting to be linked

// the parts the HUD has not got yet
list missing()
{
    list m = [];
    integer i;
    for (i = 0; i < llGetListLength(PARTS); i++)
    {
        integer have = FALSE;
        integer j;
        for (j = 2; j <= llGetNumberOfPrims(); j++) if (llGetLinkName(j) == llList2String(PARTS, i)) have = TRUE;
        if (!have) m += llList2List(PARTS, i, i);
    }
    return m;
}

next()
{
    if (gTodo == [])
    {
        llSetLinkPrimitiveParamsFast(LINK_ROOT, [PRIM_NAME, "Take 12", PRIM_TYPE, PRIM_TYPE_BOX, PRIM_HOLE_DEFAULT,
            <0.0, 1.0, 0.0>, 0.0, ZERO_VECTOR, <1.0, 1.0, 0.0>, ZERO_VECTOR, PRIM_SIZE, <0.01, 0.04, 0.04>,
            PRIM_ROTATION, ZERO_ROTATION, PRIM_COLOR, ALL_SIDES, <1.0, 1.0, 1.0>, 1.0]);
        llOwnerSay("Built: " + (string)llGetNumberOfPrims() + " parts. Now add the scripts of hud/src, drop take12_words and "
            + "take12_marks in, take it and wear it on HUD Top Center.");
        if (llGetInventoryType(PART) == INVENTORY_OBJECT) llRemoveInventory(PART);
        llRemoveInventory(llGetScriptName());
        return;
    }
    llRezObject(PART, llGetPos() + <0.0, 0.0, 0.4>, ZERO_VECTOR, ZERO_ROTATION, 0);
}

default
{
    state_entry()
    {
        gOwner = llGetOwner();
        llOwnerSay("Take 12 builder: put a blank box named \"" + PART + "\" in this box's contents, then touch it.");
    }

    touch_start(integer n)
    {
        if (llDetectedKey(0) != gOwner) return;
        if (llGetInventoryType(PART) != INVENTORY_OBJECT)
        {
            llOwnerSay("Put a blank box named \"" + PART + "\" in the contents first.");
            return;
        }
        llRequestPermissions(gOwner, PERMISSION_CHANGE_LINKS);
    }

    run_time_permissions(integer p)
    {
        if (!(p & PERMISSION_CHANGE_LINKS))
        {
            llOwnerSay("The builder needs to link the parts: touch it again and allow it.");
            return;
        }
        gTodo = missing();
        llOwnerSay("Making " + (string)llGetListLength(gTodo) + " parts (about a second each)…");
        next();
    }

    object_rez(key id)
    {
        gNew = id;
        llCreateLink(id, TRUE);
    }

    changed(integer c)
    {
        if (!(c & CHANGED_LINK) || gNew == NULL_KEY) return;
        integer i;
        for (i = 2; i <= llGetNumberOfPrims(); i++)
            if (llGetLinkKey(i) == gNew)
            {
                llSetLinkPrimitiveParamsFast(i, [PRIM_NAME, llList2String(gTodo, 0), PRIM_DESC, "", PRIM_TYPE, PRIM_TYPE_BOX,
                    PRIM_HOLE_DEFAULT, <0.0, 1.0, 0.0>, 0.0, ZERO_VECTOR, <1.0, 1.0, 0.0>, ZERO_VECTOR,
                    PRIM_POS_LOCAL, <0.002, 0.0, 0.0>, PRIM_ROT_LOCAL, ZERO_ROTATION, PRIM_SIZE, <0.01, 0.01, 0.01>,
                    PRIM_TEXTURE, ALL_SIDES, TEXTURE_BLANK, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0,
                    PRIM_COLOR, ALL_SIDES, <1.0, 1.0, 1.0>, 0.0, PRIM_FULLBRIGHT, ALL_SIDES, TRUE]);
                gTodo = llDeleteSubList(gTodo, 0, 0);
                gNew = NULL_KEY;
                next();
                return;
            }
    }
}
