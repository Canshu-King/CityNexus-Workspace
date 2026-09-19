# CityNexus V9 Gate Matrix

Observed on 2026-09-12, Asia/Shanghai. `PASS` means the checked-in contract or deterministic/replay path was exercised. `NOT_CONFIGURED`, `NOT_RUN_EXTERNAL`, and `FAILED_BLOCKED` are intentionally not converted to PASS.

| Final label | Result | Evidence |
|---|---|---|
| `V8_REGRESSION` | PASS | Backend `334 passed, 2 skipped`; serialized Playwright `11 passed`, including V5/V6/V8 specs. |
| `CORE_DOMAIN_RECONCILED` | PASS | V9 flagship test verifies selected Stay materializes active PlanVersion, Activities, JourneyLegs and JourneyTwin; prior plan becomes `SUPERSEDED`. |
| `GENERIC_MULTI_DAY` | PASS | Tianjin flagship plus Beijing regression; Beijing does not receive Tianjin POIs. |
| `COMPLETE_MOBILITY_GRAPH` | PASS | Concrete leg rows cover arrival, luggage drop, activity, check-in, stay and departure; each has provider/captured geometry and per-leg mode. |
| `REAL_MAP_ROUTE_EVIDENCE` | PASS | MapLibre sources are populated from backend/provider GeoJSON with WGS84 metadata; static LineString, CSS route and static pins are absent. |
| `AMAP_PROVIDER` | PASS | Amap adapter contract, region routing, GCJ02/WGS84 conversion, and captured/replay normalization tests pass. |
| `AMAP_LIVE` | NOT_CONFIGURED | `AMAP_WEB_KEY` absent; no live claim made. |
| `JOURNEY_INBOX` | PASS | Structured reservation, text ambiguity, confirmation boundary and ICS/text parsing paths are covered. |
| `EXTERNAL_RESERVATION_COMMITMENT` | PASS | Confirmed rail-style import materializes Booking/TransportReservation and protected C4 arrival Commitment. |
| `LIVE_TRANSIT_PROVIDER` | PASS (captured/replay) | Schedule change path records provider freshness, stale status, service alert, Guardian wake-up and deduplicated notification. Live GTFS-RT/OTP is `NOT_CONFIGURED`. |
| `LONG_DISTANCE_ANCHORS` | PASS | Rail/flight/coach/ferry-neutral reservation model and arrival/departure anchors are persisted and reconciled. |
| `LUGGAGE_CHECKIN` | PASS | Flagship orders station → luggage drop → activity → check-in and protects checkout/luggage pickup constraints. |
| `PWA_OFFLINE` | PASS | Manifest, service worker and IndexedDB next-24-hour read-only snapshot; browser offline reload passed. |
| `FOREGROUND_LOCATION` | PASS | Accuracy/timestamp location contract and user marker passed; no background GPS claim. |
| `PUSH_NOTIFICATIONS` | PASS | Push subscription seam and deduplicated high-value NotificationEvent model passed. |
| `EDGE_COMPANION_API` | PASS | Device-scoped token, snapshot, low-risk action and observation endpoints; payment/admin action rejected. |
| `EDGE_COMPANION_SIMULATOR` | PASS | `tools/edge_companion_simulator.py` UART encode/parse and POST path exercised by V9 test. |
| `V9_FLAGSHIP_E2E` | PASS | `test_v9_flagship_real_world_trip_operations_e2e` and browser V9 scenario pass through import → stay/luggage plan → disruption → autonomous recovery → offline → edge → reload. |
| `NATIVE_DEEPSEEK_MODEL_BACKED` | FAILED_BLOCKED | Bounded live smoke returned `FAILED_BLOCKED`; impact provider was `deterministic-fallback`, while the deterministic post-action gate passed. |
| `HERMES_MODEL_BACKED` | NOT_RUN_EXTERNAL | MCP V2 boundary/protocol is tested; Hermes CLI/provider-backed external run was unavailable. |

## Additional verification

- Supplied V9 reality-gap checker: `6 passed / 0 failed`.
- MCP boundary suite: `6 passed`.
- Promptfoo-compatible adversarial pack: `13/13` under `LOCAL_DETERMINISTIC_ADAPTER`; not model-backed.
- Ruff check, Ruff format check, Python compileall, frontend build and `git diff --check`: PASS.
