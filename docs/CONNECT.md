# Connect (6.8): connect first; whoever films leads

Sharing became **Connect** in 6.8.0. You connect with the people near you. Once connected, **whoever films leads**: start any camera and everyone connected sees it. When nobody films, everyone has their own camera and stays connected.

## Who does what
- **`hud/src/sync.lsl`** is the connection: the protocol, who is connected, and the camera.
- **`hud/src/connect.lsl`** draws its panels (it was `share.lsl` in 6.2–6.7, split out of sync for memory).
  - sync sends `SHARE_UI` with what a panel needs; connect sends the choice back as `SHARE_DO`.
- **`tips`** owns the text above the HUD. sync sends it the state (TEXT 7380, `"<live/view/inv>|<text>"`), and still writes its own short notices directly for about 4 s.
- **Core** only reports every camera it sets (CAMSET 7325). It starts Us when My turn follows a Scenery run (`sharecam`).
- **The free Take 12 Watch** (`watch/take12_watch.lsl`) is the watching half alone: it connects at once, and it never films.
- `tools/sim/sync_sim.py` checks both scripts against this document.

## States (per HUD)
| State | Meaning | Above the HUD |
|---|---|---|
| Not connected | | (nothing) |
| Connected, holding it ("hub") | you film, filmed last, or connected the others | `⇄ You film · Ana, Ben see it` / `⇄ Connected · Ana, Ben` + `nobody films · double-tap: film` / `⇄ Connecting… · nobody has joined yet` |
| Connected, watching | you see the hub's camera | `⇄ Pano films` + `double-tap: next for all`, `· your camera for a moment`, `· looking around (Esc: back)`, `⇄ Connected with Pano` + `nobody films · double-tap: film`, `⇄ Taking the camera…`, `· no signal…` |
| Asked | someone wants to connect; waits 20 s | `Pano wants to connect · double-tap: yes` |

Names carry `(own camera)` or `(no signal)`. Short notices (connected, disconnected, "Ana films now") show for about 4 s, then the state comes back.

## Gestures
- **Hold:** the Connect panel, in every state (Connect is in both tap menus too).
- **Double-tap:**
  - when asked, it says yes;
  - while you watch, it is Next for everyone;
  - when nobody films, it films: it starts your last camera (after Scenery, Us), so you lead.
- **A movement key while watching:** your own camera for a moment (`away`). After 4 s still, the shared view is back at the latest shot (`back`).
- **Keys:**
  - holding it: NEXT · INVITE · DISCONNECT;
  - watching: NEXT · MY TURN · DISCONNECT.

## Panels (connect.lsl)
```
NOT CONNECTED  (after a 1.5 s "who" check)
   "Connect with the people near you. Once connected, whoever films leads: everyone sees that camera.
    Near you: Ana, Ben (Watch), Eve (connected)"
   [+ Everyone] [+ Ana] [+ Ben] [⇄ Join Eve] [Give Watch] [⋯ More] [Close]
HOLDING IT     "⇄ Connected with Ana, Ben (Watch). You film: they see your camera."   [Next | Film] [+ Invite] [× Disconnect] [⋯ More] [Close]
WATCHING       "⇄ Connected with Pano. Pano films: you see their camera."              [My turn] [Next] [× Disconnect] [⋯ More] [Close]
ASKED          "Pano wants to connect with you."                                       [Connect] [No]
DISCONNECT?    (the hub, only Watches left) "Ana and Ben will lose the view."          [Disconnect] [Keep]
```
There are no rosters, lead requests, Pass camera or End live any more: taking a turn is starting a camera, and leaving is Disconnect.

## Protocol (channel -7712120, `T12|<what>|…`; replies with `llRegionSayTo`, only the sender's owner counts)
| Message | From → to | Meaning |
|---|---|---|
| `who\|<name>` | asker → region (`llRegionSay`) | who is near? |
| `here\|<T/W>\|<idle/live/view/pend>\|<hub>` | anyone within 20 m → asker | Take 12 or Watch, and their state |
| `invite\|<name>` | hub → one avatar | "wants to connect" |
| `ack\|1` / `ack\|0` / `busy\|<what>` | asked → hub | connected at once (a Watch, or Take 12 with the hub in Friends) / asked / busy (`connected`, `connected with Eve`) |
| `join` `leave` `next` `away` `back` `ask` | viewer → hub | connected (`join\|W` from a Watch: it can never take the lead), left, next view (5 s apart), own camera / looking around, back, **my camera started**. A `join` to someone no longer holding it is answered with `director\|…` (the lead moved on: follow that one) or `end` |
| `hb` | viewer → hub, hub → viewers | heartbeat, every 10 s |
| `cam\|<pos>\|<focus>\|<lag>\|<lens>` | hub → viewers | every camera the hub's core sets, with its field of view |
| `fmt\|<format>` | hub → viewers | 7.1: the hub's Format (its ratio, 0 = none), on a change and to each viewer that joins. A Take 12 viewer shows it (`crop\|follow <format>`, not saved) and gets its own back when it leaves; the Watch has no bars and ignores it |
| `pause` | hub → viewers | nobody films: viewers get their own camera, still connected. Also sent on `join` while the hub's camera is off |
| `lead\|1` / `lead\|2` / `lead\|0` | hub → viewer | you film now (your camera runs) / you hold it now, nobody films (the hub disconnected) / no (an older hub kept the camera: you film alone, disconnected) |
| `director\|<key>\|<name>` | old hub → viewers | the lead passed: follow this one |
| `kick` / `end` | hub → viewer(s) | removed (older hubs) / disconnected |
| `reset` | anyone → region | 7.1.3: this HUD's scripts just restarted and it knows nobody: a viewer following it leaves at once, a hub drops it from its list (the Watch sends it too) |

## The handshakes
- **Connect:** + name or + Everyone makes you the hub; **no camera is started**. You send `invite`.
  - A Watch, or Take 12 with you in its Friends, connects at once: `ack|1`, then `join`.
  - Anyone else answers `ack|0` and is asked for 20 s. The panel, a hold or a double-tap says yes.
  - With no answer in 3 s: "didn't answer (out of range or HUD off)".
- **Join:** someone near who holds a connection shows as ⇄ Join name, which sends `join`.
- **Whoever films leads:**
  - a viewer whose own camera starts sends `ask`, ignores the hub's `cam` and shows "Taking the camera…";
  - the hub always grants. It sends `lead|1` to them and `director|…` to everyone else, then watches the new hub. Its own camera stops, and that stop is not a pause;
  - **two at once:** the second `ask` reaches a hub that has just handed over and is lost. That viewer then gets `director|…` while still asking, and asks the new hub. The last one to start leads;
  - **no answer in 20 s** (an older Take 12): you film on your own, disconnected.
- **Disconnect:**
  - a viewer sends `leave`, and the others stay;
  - the hub hands the others on to another Take 12: `lead|2` to it (it holds the connection, and no camera starts for it), `director|…` to everyone else;
  - with only Watches left, the hub asks first, then sends `end`.

## Each through their own lens (6.0.1)
- **Lenses differ.** A script can read its viewer's zoom but never set it, and every viewer has their own. So nobody is asked to match a lens.
- **The same picture through your own lens.** Each viewer (Take 12 or the Watch) places the hub's camera on the same line to the same focus. It stands at the distance that gives the same picture size through their own lens:
  - `k = tan(hub/2) / tan(yours/2)`, clamped to 0.2–5;
  - stopped 0.3 m short of a wall.
- **The same code.** `place()` is identical in both scripts; sync_sim checks it, and the geometry.
- **7.1: a note, once.** A Take 12 viewer whose lens differs from the hub's by more than 15 % is told once per connection ("Ana zooms wider · Ctrl+8 to match"): the picture already keeps its size, only the perspective differs.

## Feedback and edge cases
- **Heartbeats:** every viewer sends `hb` every 10 s.
  - "(no signal)" appears after 25 s, and the viewer is dropped after 45 s ("lost the connection").
  - Viewers see "· no signal…" after 15 s and drop out after 25 s ("Pano is gone · disconnected").
- **Leaving:** a viewer who leaves the region is dropped at the next heartbeat check. Taking the HUD off sends `leave` without touching the camera, and a region change disconnects.
- **Rapid toggling:** Connect right after Disconnect (under 2 s) is ignored. Duplicate `join`, `invite` and `ask` change nothing.
- **Your camera stopping** (Stop, a movement key in Scenery, typing) never disconnects anyone: the hub sends `pause` ("Nobody films now · everyone has their own camera").
