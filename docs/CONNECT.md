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
- **What is shared:** what you see (8.0.6): Take 12's shots, your own camera and an Alt-click look too. Never mouselook,
  never while you watch someone, never while everything is off (core sends CAMSET `-`). Their film stopping sends you
  back to yours ("Ben isn't filming.").
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

## 8.9.0: the Connect review (each found by reading the scripts end to end, each a failing test first)
- **Leave sticks.** Two friends were joined again by themselves 10 s after a Leave. Now the ones you leave are
  remembered (until a new wear): your friends among them don't join you by themselves; asking each other still does.
- **Everything off is off for Connect too.** A hold ended the connection, and friends were joined again 10 s later.
  While core is `off` (sync reads UI_STATE): no `here`, no answer to `who`, `back`, `hi` or `join`, an ask is
  answered `busy`. On again: `here` at once, and friends join again.
- **An older copy stepping aside keeps out of Connect** (it hears nothing). It answered for its owner too, so their
  watchers were told "isn't filming" every second.
- **A watcher gone stops SHARING.** A watcher who took the HUD off, logged off or walked away stayed in the list for up
  to 30 min: SHARING stayed, and the camera went on to them 7 times a second. Now resting removes them.
- **A question waiting comes back.** If another of Connect's pages opened over an ask (the rings tapped when the chime
  sounded), it could not be answered, and everyone else asking was `busy` until a new wear. Now the rings show the
  question again, and it ends by itself after 70 s.
- **A late Yes connects both.** The asker gave up after 20 s while the question stayed open 60 s: a Yes after 20 s
  connected one side only. The asker now waits 70 s.
- **A still shot stays still for the watcher.** Every camera went with the director's position, so the watcher's view
  of a still shot moved as the director shifted. A cut or a glide now goes with `<0,0,0>` as the position: exactly
  where it is. The director's own and moving cameras are carried with them as before.
- **A new frame reaches the watcher at once** (sync asks core for the camera again: `camq`), not at the next shot.
- **An Alt-click close-up of a thing, through another lens.** The watcher moved round the director, not round what the
  picture looks at, so a toy came out four times too small, or from behind it. With the director off the middle of
  the picture (and not in Tracking or Drift), the aim is what the middle looks at (a ray), just before it.
- **20 m is not a note at every step:** a connection rests beyond 22 m once it is near, and comes back within 20 m.
- **The rings while your one friend watches you** say "Ben is watching your film." (it said he wasn't filming).
- **sync started again while you watch:** your own film, not a frozen view.
- **Worn again, rejoined either way:** a heartbeat from someone you were with in the last 30 min rejoins them, so a
  lost `back` (carry may still be starting) costs nothing. carry now says `back` and the newer-version note (room for
  sync).
- **Less chatter:** a watched camera that stands still goes out once a second, not 7 times.

## Messages
Channel `-7712120`, every message `T12|8|<what>|...` (`8` is the protocol generation; a 7.x Take 12 speaks
`T12|<what>|...` and ignores these). `llRegionSayTo` the avatar (all its attachments hear it), except `who`
(`llRegionSay`). Only messages from an avatar's own HUD count (`llGetOwnerKey`).

| Message | From → to | Meaning |
|---|---|---|
| `who\|<ver>\|<lite>` | anyone → region | who wears Take 12 near me? (also a legacy `T12\|who\|<name>` so 7.x answers); only when nobody is known yet (8.2.0) |
| `here\|<ver>\|<lite>` | → region, on wear and every 10 s (8.2.0); → asker; → someone new whose `here` you just heard (8.4.3: both know each other within a second) | I wear Take 12. Kept 25 s by everyone within 20 m: the list opens at once, and the rings count who is near while you are alone. A legacy `T12\|here\|…` marks a 7.x HUD "(old)" |
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
8.9.0: UI_STATE (core → sync) `off|…` keeps Connect out while everything is off; CMD `back` (sync → carry: tell the
ones you were with that you are back) and `newer|<version>` (sync → carry: another version heard, said once if newer);
CMD `camq` (sync → core) when your frame changes while watched.
Dialog words come from `text.lsl` (TXT `connect`, `connected`, `ask`, `addfriend`).
