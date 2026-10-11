# Calibration & In-World Probe Log

Fill this in after running **Menu → Options → Probe** with **Debug** on. These values decide the `cin.cutmode`, `cin.maxcam` and `cin.fovaxis` settings.

## Platform probes (the SL wiki leaves these open)
| Probe | Question | Firestorm result | Official viewer result | Setting adjusted |
|---|---|---|---|---|
| a | Does lag 0 / threshold 0 give a clean cut (no glide)? | | | `cutmode` |
| b | Does `llClearCameraParams` snap back or ease back? | | | — |
| c | Does `llGetCameraPos` follow Alt-orbit? (peek detection) | | | `peek_bail` |
| d | Max distance from avatar to locked camera (10 / 25 / 45 / 60 m) | | | `maxcam` |
| e | Is `llGetCameraFOV` the vertical FOV? | | | `fovaxis` |
| f | What does ESC do while rolling? | | | — |

## Composition constants
| Constant | Initial | Calibrated | Notes |
|---|---|---|---|
| K_EYE_STAND | 0.37 | | eye height factor of avatar bbox height |
| K_EYE_SIT | 0.25 | | |
| BODY_R | 0.35 m | | |
| MARGIN | 1.15 | | |
| THETA_MAX | 10° | | |
| STANDOFF | 0.4 m | | gap kept from walls |
| R_INT | 4.5 m | | intimate radius |
| R_ENS | 10 m | | ensemble radius |
| LINK | 3.5 m | | cluster link distance |
| W_OWN | 1.5 | | owner weight in centroid |
| MIN_HOLD | 6 s | | |
| SURVEY_RANGE | 50 m | | |
| VISTA | 25–45 m | | |
| PEEK_TOL | 0.3 m | | |

## Test matrix log
| # | Scenario | Date | Result | Notes |
|---|---|---|---|---|
| 1 | Open field, solo | | | |
| 2 | Small room with ceiling | | | |
| 3 | Sofa with a friend | | | |
| 4 | Club crowd | | | |
| 5 | Skybox / region border / teleport | | | |
| 6 | Activity policy (§4.2) | | | |
| 7 | 10 min AFK cooldown | | | |
| 8 | Give copy to alt (first run) | | | |
