// "Seerose" lake boat -- one-shot texture applier
//
// 1. Upload the PNGs from out/textures (the *_d.png are required; *_n.png normal maps and
//    *_s.png specular maps are optional) and name them exactly like the files, without ".png":
//        hull_d  hull_n  hull_s   interior_d ...   metal_d  (see TEXTURES below)
// 2. Drop the textures AND this script into the boat's contents (Edit > Content).
//    The script applies everything on the root prim and reports what it found or missed.
// 3. When every diffuse texture was found, the script deletes itself (REMOVE_WHEN_DONE).
//    If something is missing, add it and reset the script (Edit > Content > Reset).
//
// Face order on the mesh (same in every LOD):
//    0 hull_planks   1 interior   2 hull_end   3 wood   4 metal

// ---------------------------------------------------------------- TUNE
integer REMOVE_WHEN_DONE = TRUE;   // delete this script after a complete diffuse pass
integer SPEC_GLOSS       = 255;    // 0-255, how glossy the specular maps are (map alpha shapes it)
integer SPEC_ENV         = 0;      // 0-255 environment reflection, keep low for old paint
vector  SPEC_COLOR       = <1.0, 1.0, 1.0>;

// face-ordered base names: diffuse "<base>_d", normal "<base>_n", specular "<base>_s"
list    BASES            = ["hull", "interior", "hull_end", "wood", "metal"];

// ---------------------------------------------------------------- code
integer have(string name)
{
    return llGetInventoryType(name) == INVENTORY_TEXTURE;
}

default
{
    state_entry()
    {
        integer faces = llGetListLength(BASES);
        integer i;
        integer missingDiffuse = 0;
        string  report = "";

        for (i = 0; i < faces; ++i) {
            string base = llList2String(BASES, i);
            string d = base + "_d";
            string n = base + "_n";
            string s = base + "_s";

            if (have(d)) {
                llSetLinkPrimitiveParamsFast(LINK_THIS, [
                    PRIM_COLOR,   i, <1.0, 1.0, 1.0>, 1.0,
                    PRIM_FULLBRIGHT, i, FALSE,
                    PRIM_TEXTURE, i, d, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0
                ]);
                report += "\n  face " + (string)i + "  " + d;
            } else {
                ++missingDiffuse;
                report += "\n  face " + (string)i + "  MISSING " + d;
            }

            if (have(n)) {
                llSetLinkPrimitiveParamsFast(LINK_THIS, [
                    PRIM_NORMAL, i, n, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0
                ]);
                report += " + normal";
            }
            if (have(s)) {
                llSetLinkPrimitiveParamsFast(LINK_THIS, [
                    PRIM_SPECULAR, i, s, <1.0, 1.0, 0.0>, ZERO_VECTOR, 0.0,
                    SPEC_COLOR, SPEC_GLOSS, SPEC_ENV
                ]);
                report += " + specular";
            }
        }

        llOwnerSay("Seerose textures:" + report);

        if (missingDiffuse == 0) {
            llOwnerSay("All 5 faces textured.");
            if (REMOVE_WHEN_DONE) {
                llOwnerSay("Removing this script.");
                llRemoveInventory(llGetScriptName());
            }
        } else {
            llOwnerSay((string)missingDiffuse + " diffuse texture(s) missing. Add them to the boat's contents, then reset this script.");
        }
    }
}
