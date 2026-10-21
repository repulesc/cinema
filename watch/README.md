# Take 12 Watch (free)

A one-prim HUD for friends who don't own Take 12. While it is worn, someone near them who shares their Take 12 view (long press › Share › Offer view) can be watched with one tap.

- **Watch:** tap Watch in the dialog. The camera then follows the sharer's cuts.
- **Next view:** double-tap the HUD to cut to the next view for everyone watching.
- **Leave:** a single tap or any movement key gives you your own camera back.

**To make it:**
1. Create a small box and put `take12_watch.lsl` in it.
2. Give it a simple texture and attach it as a HUD.
3. Name the object **Take 12 Watch**. Set it to copy and transfer, no modify.
4. Put a copy in the Take 12 HUD's contents, so Share › Give Watch can hand it out.

Protocol: the same as `hud/src/cinema_sync.lsl` (channel -7712120, `T12|…` messages). `tools/sim/sync_sim.py` checks that the two match.
