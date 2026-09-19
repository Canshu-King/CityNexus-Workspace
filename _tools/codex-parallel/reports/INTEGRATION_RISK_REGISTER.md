# Integration risk register

| ID | Risk | Class | Evidence | Severity | Required closure |
| --- | --- | --- | --- | --- | --- |
| R01 | Detached integration HEAD is not a durable release branch | environment | `branch.head (detached)` at `1a8462d` | High | Create named owner branch without rewriting source history; record SHA |
| R02 | Twelve seeded legacy specs still fail due obsolete `/` UI and V8 contract drift | test/product contract | Integration report 34 pass/12 fail | Medium | Owner chooses migrate/archive; do not weaken new truth behavior |
| R03 | Today positive branch exposes four CTAs and duplicate language switch | visual/IA | 32-shot review | High for UX | Product decision and new positive-branch gate |
| R04 | Copilot dock overlaps bottom content; avatar/text overflow | visual/IA | screenshot review | High on Xiaomi | Fix in later authorized frontend pass; phone evidence gate |
| R05 | Live first-view hierarchy and tall empty map push decision state down | visual/IA | screenshot review | Medium | Human/product reconcile, then device check |
| R06 | Live routing not configured or proven | environment/truth | `CITYNEXUS_LIVE_VALHALLA_URL` owner gate | Critical | Normal and fail-closed provider evidence in Xiamen |
| R07 | Coordinate set is not authoritative | routing preflight | only one project-known coordinate; config labels others unverified | High | Owner verifies coordinates before opt-in smoke |
| R08 | Main status docs remain 2026-09-15/V19.2.1 | evidence | old `CURRENT_STATUS`/`TEST_RESULTS` | Medium | Rewrite only after release SHA is frozen |
| R09 | PWA precaches ~2.29 MiB including MapLibre despite dynamic JS split | performance | build log and service-worker output | Medium on mobile | Decide offline-map policy; benchmark before changing precache |
| R10 | Main JS remains ~1.13 MB minified/~334 KB gzip | performance | latest build evidence | Medium | Route/feature lazy boundaries; performance budget |
| R11 | Xiaomi 13 Ultra has not run fresh-device chain | device | no device evidence | Critical | Execute runbook twice on fresh install |
| R12 | Coursework customer agreement, team identities, allocation and project plan absent | coursework | verified assignment brief and repository evidence | Critical for grading | Obtain human data and create final submission PDFs |

No risk is closed merely by this report.
