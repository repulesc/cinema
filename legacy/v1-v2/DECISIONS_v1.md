# Design Decisions

These are the answers from the design quiz (four rounds, 16 questions). They override anything in the original brief. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for how each decision is implemented.

| # | Topic | Decision |
|---|---|---|
| 1 | AFK delay | 90 s default; submenu presets 60–600 s + "SL Away" |
| 2 | What ends cinema | Movement keys (AFK sessions), HUD tap, **typing**, **sit/stand**. Alt-cam = peek (option to bail). Mouselook = pause |
| 3 | Manual mode + movement | Social shots (A/B) keep rolling in "director mode". Vista: option, default keeps rolling |
| 4 | Transitions | Hard cut near, dip-to-black far. Dip-to-black ships with the Phase 2 overlay; v1 hard-cuts everywhere |
| 5 | Style | Blend default; Ozu / Jarmusch / Nouvelle Vague presets in the menu |
| 6 | Hold | 20–30 s varied by shot type, menu multiplier (incl. "until event") |
| 7 | Letterbox | Deferred to Phase 2 (optional, can be shelved), with an off switch. v1 = button only |
| 8 | Vertical composition | Thirds by camera height, level camera |
| 9 | Solo scenes | Mostly landscape and pillow shots |
| 10 | Speaker cut | Optional (menu): Off / typing flag / typing + chat listen; default Off |
| 11 | Other avatars | Framed freely, incl. close two-shots |
| 12 | GPU cooldown | After 10 min AFK, favour pillow shots |
| 13 | Phantom objects | Ignored by default, menu toggle |
| 14 | Settings UI | Long-press button → dialog menu, settings stored in Linkset Data |
| 15 | Build approach | All scripts in one delivery, with in-world probe tools for the unknowns |
| 16 | Audience | Give or sell: first-run, notecard, protected settings, owner-change reset, versioning |

## Notes in the user's own words
- **AFK delay:** "90 secs is good start, but we can select more in sub options."
- **Manual mode:** "the social ones shall not end, the scene view … shall also be optional … given options and a well thought out default is a good way here."
- **Letterbox:** "we might have an option to entirely turn this off … this can be a next project and be halted if it is too complex."
- **Speaker cut:** optional.

## Deliberately not chosen
- Ending the cinema on Alt-cam or mouselook. Alt-cam is a *peek* instead, with a menu option to make it end the cinema. Mouselook pauses the cinema and resumes it afterwards.
