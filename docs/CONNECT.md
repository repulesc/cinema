# Connect (8.0): two equal cameras

The script is `hud/src/sync.lsl`; it is checked on the real scripts by `tools/sim/connect_emu.py` (scenarios and a
fuzzer on two and three HUDs, with lost messages).

## What people see
- **Finding people:** Dialog › Connect, or the strip's Connect key while alone: everyone within 20 m who wears Take 12
  (up to 9; friends marked ★, a 7.x Take 12 as "(old)"). A tap asks them: "Ana wants to share films." Yes / No. A No
  shows as "Ben didn't answer." (never a rejection). Your **Friends** (Settings › Friends) join without being asked. A
  soft chime (the HUD's own sound, heard only by you; Settings › Friends › Chime) when someone asks or joins.
- **Two equal cameras:** everyone keeps filming their own shot. With one other person the Connect key **flips**
  between your film and theirs; with more it opens their names (and My film, Invite, Leave).
- **The strip:** two linked rings and the count (dim while nobody you could watch is filming), **SHARING** while
  someone watches your film, **THEIR FILM** while you watch someone's. The [12]'s dot is white while connected and
  glows softly while your film is shared. No red, no "on air": it is a social feature.
- **One director per pair:** while you watch someone you film for nobody; your watchers go back to their own film and
  your key dims for them.
- **Privacy:** only Take 12's shots are shared. Your own camera, an Alt-click look, mouselook, flying and Fixed while you
  frame are never sent (core sends CAMSET `-`). Their film stopping sends you back to yours ("Ben isn't filming.").
- **Their picture through your lens:** the camera is placed on the same line to the same focus, at the distance that
  keeps the picture's size for your lens; the watcher's bars show the director's shape.
- **Apart:** beyond 20 m (or another region) a connection **rests**: the count drops, "Ben is out of reach."; close
  again it comes back by itself ("Ben is back."). Rested 30 min, it ends. 3 s without a word from the one you watch:
  "Ben left." and your own film. A re-worn Take 12 says `back` to the people it was with in the last 30 min
  (`cin.peers`) and they rejoin.
- **Leaving:** Dialog › Connect › Leave, or a hold (everything off). An older copy stepping aside (carry) leaves too.
- **The free Take 12 Scenery** connects and watches; it never films for others (its key reads as not filming).
- **Updates:** meeting a newer Take 12 shows "A newer Take 12 is out. Ask the store for a new copy." once per version.

## 8.2.0: smoother, quicker, clearer
- **Who is near is known:** each HUD says `here` every 10 s, so Connect lists people at once (no 1.5–3 s wait) and an
  empty list is never false. Settings › Friends › Add lists people already connected too (8.1 said "Nobody near
  you").
- **Friends connect by themselves:** two people who have each other as friends connect quietly when near.
- **One list, one state each:** `Ana · filming`, `Ben · watching your film`, `Cy · away`. Tap a name: **Watch**, or
  **Show my film** (a friend watches at once, anyone else is asked), or **My film** while you watch them.
- **Smooth:** the shared view no longer steps 4 times a second; it moves 20 times a second with the director.
- **Mended:** a heartbeat from someone who thinks you are connected, when you are not, is answered `bye`.

## Messages
Channel `-7712120`, every message `T12|8|<what>|...` (`8` is the protocol generation; a 7.x Take 12 speaks
`T12|<what>|...` and ignores these). `llRegionSayTo` the avatar (all its attachments hear it), except `who`
(`llRegionSay`). Only messages from an avatar's own HUD count (`llGetOwnerKey`).

| Message | From → to | Meaning |
|---|---|---|
| `who\|<ver>\|<lite>` | anyone → region | who wears Take 12 near me? (also a legacy `T12\|who\|<name>` so 7.x answers); only when nobody is known yet (8.2.0) |
| `here\|<ver>\|<lite>` | → region, on wear and every 10 s (8.2.0); → asker | I wear Take 12. Kept 25 s by everyone within 20 m: the list opens at once, and the rings count who is near while you are alone. A legacy `T12\|here\|…` marks a 7.x HUD "(old)" |
| `ask\|<ver>` | → one person | share films? (a friend, or someone already connected, answers `yes` at once) |
| `ask\|<ver>\|auto` · `join\|<ver>` | → a friend near you, and their answer | 8.2.0: two friends connect by themselves; the asked one joins only if the asker is their friend too, and never shows a question |
| `show` | → a peer | 8.2.0: "watch my film": a friend watches at once, anyone else is asked (Watch / No) |
| `yes\|<ver>` · `no` · `busy` | → asker | the answer; `busy`: already answering someone else's ask |
| `add\|<key>` | the inviter → both | the new person and everyone already connected meet: one group |
| `hb\|<flags>` | → every peer, every second | 1: I film (shareable); 2: I watch someone; 8: I watch **you**. It mends lost messages: a director adds a watcher it missed (or drops one that left), a watcher whose director stopped filming goes back to its own film |
| `watch` · `unwatch` | watcher → director | I watch your film / no longer |
| `cam\|<pos>\|<focus>\|<lag>\|<fov>\|<shape>\|<where I am>` | director → watchers, about 7 a second while it moves | the camera on my screen (lag 0: a cut; negative: my live camera), my shape, and (8.2.0) my position: the watcher's core keeps the camera relative to me and eases it 20 times a second between updates, so it is smooth and walks with me |
| `pause` | director → watchers | I stopped filming (or I watch someone): back to your own film |
| `bye` | → every peer | I leave |
| `back\|<ver>` · `hi\|<ver>` | a re-worn HUD → recent peers, and the answer | rejoin within 30 min |

A legacy `T12|invite` gets `T12|busy|on a newer Take 12`, so a 7.x user sees why nothing happens.

## Link messages
CAMSET (core → sync) `<pos>|<focus>|<lag>|<fov>` while filming, `-` when not; CROP (bars → all) gives the shape sent
with `cam`; LINKST (sync → screen, ui) `<alone/on/shared/theirs/dim>|<count>|<name>`; CMD `watch|<key>` / `unwatch`
(sync → core), `bars|follow <shape>` / `bars|follow` (sync → bars), `connect` (the strip's key), `connect|menu`
(Dialog › Connect, `/12 connect`), `connect|addfriend` (Settings › Friends › Add), `off` / `standby` (leave).
Dialog words come from `text.lsl` (TXT `connect`, `connected`, `ask`, `addfriend`).
