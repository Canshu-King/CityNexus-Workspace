# CityNexus WP06 Post-Gate Checkpoint

Date: 2026-09-09

## Scope completed

- Applied the supplied post-gate lifecycle/idempotency patch after a clean `git apply --check`.
- Semantically merged the OpenAPI deltas without replacing newer contract content.
- Preserved the accepted Post-WP04 Foundation, WP06 deterministic gate, and JourneyTwin v2.
- Added offline-safe Valhalla HTTP route/matrix support and external-to-frozen MobilitySnapshot capture.
- Added deterministic replan candidate families F0-F3, bounded by `candidate_count` and gated before presentation.
- Recomputed plan/proposal utility scores from persisted, verified candidate facts.
- Added durable Event provenance and blocked public clients from forging provider-verified/system evidence.
- Replaced wall-clock Event occurrence fallback with deterministic Journey/activity time; explicit simulator time remains preferred.

## STOP Gate result

PASS. No WP07 work or mandatory live provider/solver dependency was started.

- Default suite: 133 passed, 1 skipped, 2 dependency deprecation warnings.
- Optional skip: live Valhalla smoke test, because `CITYNEXUS_LIVE_VALHALLA_URL` was not configured.
- Ruff lint: pass.
- Ruff format check: pass (88 files already formatted).
- Python compileall: pass.
- OpenAPI 3.1 parse: pass.
- Runtime/formal operations: 38/38 exact match.
- Required network calls: none.

## Review focus

Independent review should verify proposal acceptance/rejection terminality and idempotency, unresolved degradation projection, C4-aware diff evidence, F0-F3 candidate distinctness and gating, fresh score evidence, provenance anti-forgery, and the provider-to-snapshot boundary.

The two warnings are upstream TestClient/AnyIO deprecations already present in the environment. The single skipped test is explicitly opt-in and does not affect the deterministic gate.

The packaged snapshot was replayed independently with an isolated temporary SQLite file and reproduced `133 passed, 1 skipped`.
