# Sharing (5.5): one director, many viewers

`hud/src/cinema_sync.lsl` is the sharing manager. It owns the Share panel, the roster, the protocol and the state shown above the HUD. Core only starts the camera (CMD `sharecam` → Social) and reports every camera it sets (CAMSET 7325). The UI only routes gestures. The free Take 12 Watch (`watch/take12_watch.lsl`) is the viewing half alone. `tools/sim/sync_sim.py` checks both scripts against this document.

## States (per HUD)
| State | Meaning | Above the HUD |
|---|---|---|
| IDLE | not sharing, not viewing | (nothing) |
| LIVE | you direct: your camera is the shared one | `● LIVE · 2` |
| VIEWING | you follow a director's camera | `👁 Pano` (`· looking around (Esc: back)`) |
| INVITED | a director invited you; waits 20 s | `Pano invites you · hold to watch` |

- There is one director per session, and any number of viewers.
- Viewing never runs your own camera, and starting your own camera ends viewing.
- Going live with the camera off starts **Social**.
- Short notices (a join, a leave, "looking around") show for about 4 s, then the state comes back. The state is also restored when the lens or Frame clear their own notices.

## Gestures
- **Tap:** the menu when idle, stop while rolling (unchanged). The tap menu also has 👁 Share.
- **Double-tap:** scenery or next (unchanged). While viewing it means next for everyone; while invited, Watch.
- **Hold:** the **Share panel**, in every state. Inside it, **⋯ More** opens the live menu (photo hold, next, stop, modes, release) or the main menu.

## Panels
```
IDLE      (after a 1.5 s "who" check)
          "Share your view. Near you: Ana, Ben (watching Cleo), Dee (Watch)."
          [🔴 Go live] [👁 Watch Eve] [+ Ana] [+ Dee] [Give Watch] [⋯ More] [Close]
LIVE      "🔴 LIVE · watching: Ana, Dee · looking around: Ben · When someone asks to lead: Ask"
          [Invite more] [Roster] [Lead: Ask] [End live] [⋯ More] [Close]
ROSTER    [Ana] [Ben] [Dee] … [Back]      →  "Ana"  [Pass camera] [Remove] [Back]
VIEWING   "👁 Viewing Pano's camera."  [Ask to lead] [Leave] [⋯ More] [Close]
INVITED   "Pano invites you to watch their camera."  [Watch] [No]
LEAD      (to the director)  "Ana asks to lead the camera."  [Allow] [Decline]
```
- **Go live:** goes live and invites everyone found who is free.
- **+ name:** invites one person (going live first if needed).
- **👁 name:** watches someone who is already live (a pull join).
- **Invite more:** a new check, then the same list with **Invite all**.
- **Lead:** cycles Ask, Always, Never. It is stored in LSD `cin.share_lead`.

## Protocol (channel -7712120, `T12|<what>|…`; replies with `llRegionSayTo`, only the sender's owner counts)
| Message | From → to | Meaning |
|---|---|---|
| `who\|<name>` | asker → region (`llRegionSay`) | who is near? |
| `here\|<T/W>\|<idle/live/view/pend>\|<director>` | anyone within 20 m → asker | Take 12 or Watch, and their state |
| `invite\|<name>` | director → one avatar | an invitation |
| `ack\|1` / `ack\|0` / `busy\|<what>` | invited → director | joined at once (a Watch, or Take 12 with the director in Friends) / asked / busy |
| `join` `leave` `next` `away` `back` `ask` | viewer → director | joined, left, next view (5 s apart), looking around, back, asks to lead |
| `cam\|<pos>\|<focus>\|<lag>` | director → viewers | every camera the director's core sets (cuts and glides) |
| `hb` | director → viewers | heartbeat, every 10 s |
| `lead\|1` / `lead\|0` | director → viewer | you lead now (a request allowed, or Pass camera) / declined |
| `director\|<key>\|<name>` | old director → viewers | the camera passed: follow this one |
| `kick` / `end` | director → viewer(s) | removed / the live view ended |

## The handshakes
- **Push:** Go live or + name sends `invite`, and the invitee answers.
  - A Watch, or Take 12 with the director in its Friends, joins at once with `ack|1` and `join`.
  - Anyone else answers `ack|0` and is INVITED for 20 s: hold › Watch, or a double-tap.
  - Busy people answer `busy`.
  - With no answer in 3 s, the director is told "didn't answer (out of range or HUD off)".
- **Pull view:** someone who sees a live director in their panel taps 👁 name and sends `join`. A director accepts a `join` only while live.
- **Pull lead:** the viewer sends `ask`.
  - **Ask:** an Allow / Decline prompt, declined automatically after 20 s.
  - **Always:** granted at once.
  - **Never:** declined.
  - A second request while one is waiting is declined at once.
  - **On a grant:** the director sends `lead|1` to the new director, `director|…` to everyone else, then becomes a viewer of the new director and stops its own camera. That stop does not end the session.
- **Pass camera** is the same grant, from the roster. **Remove** sends `kick`.

## Edge cases
- **Busy or out of range:** busy answers come back as `busy`. Avatars out of range don't answer and are reported after 3 s.
- **A viewer gone:** every 10 s the director drops viewers who have left the region ("Ana left"). A viewer who takes the HUD off sends `leave`, without touching the camera.
- **The director gone:** a viewer hearing nothing (`cam`/`hb`) for 25 s drops out ("Pano's camera is gone").
- **Teleport:** a region change ends viewing, and ends LIVE.
- **Timeouts:** an invite waits 20 s, a lead request 20 s, the viewer's own request 25 s, a dialog listener 60 s.
- **Rapid toggling:** Go live right after End live (under 2 s) is ignored. Duplicate join, invite and ask messages change nothing.
