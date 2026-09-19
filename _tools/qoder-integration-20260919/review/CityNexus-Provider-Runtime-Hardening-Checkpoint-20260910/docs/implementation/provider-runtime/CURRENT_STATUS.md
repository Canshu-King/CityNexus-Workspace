# CityNexus Provider Runtime Current Status

Date: 2026-09-10

## Gate result

Provider Runtime Gate implementation is complete in the current worktree. The
authoritative Replan path now captures one operation-scoped frozen mobility
snapshot, reuses it for candidate construction, Opportunity Window evidence,
deterministic feasibility, scoring evidence, and persists the same snapshot in
each ReplanProposal for later audit/read projection.

## Implemented

- One mobility capture per `Generate Replan` operation.
- One immutable `MobilitySnapshot` shared by every candidate in that operation.
- Valhalla is the opt-in real runtime primary when
  `CITYNEXUS_LIVE_VALHALLA_URL` is configured.
- Deterministic mock mobility remains the explicit pair-level fallback for the
  real-provider profile and the primary provider for the offline profile.
- Per-pair provider provenance, degraded status, fallback reason, capture time,
  operation key and snapshot id are persisted in proposal evidence.
- Authoritative feasibility consumes the frozen snapshot and never invokes a
  live provider.
- F3 Opportunity Window inbound/outbound travel consumes that same snapshot.
- Replan candidate `travel_from_prev_min` values consume that same snapshot.
- JourneyTwin can recover the latest persisted mobility snapshot from proposal
  evidence and never invokes live provider capture on a GET/read path.
- Primary plus fallback failure is explicit; no zero-minute or fabricated ETA
  is manufactured by the capture contract.
- PRT-01 through PRT-08 adversarial tests are implemented.

## Partial / simulated boundaries

- Initial Plan generation still uses `MockMobilityProvider`.
- Plan selection revalidation still uses deterministic mock mobility.
- Generic feasibility helpers retain mock mobility as their default when a
  caller does not inject a snapshot.
- JourneyTwin uses persisted snapshot facts when the required OD pair is
  available; otherwise it falls back to deterministic offline mock facts. It
  never performs a live network call during projection.
- Runtime capture currently requests route estimates per unique OD pair. The
  Valhalla matrix adapter exists, but matrix batching is a later performance
  optimisation rather than a correctness dependency.
- MobilitySnapshot evidence currently freezes travel minutes and provenance.
  Distance/shape data are not yet authoritative gate inputs.
- Snapshot persistence is evidence-scoped inside `ReplanProposal.diff_json`,
  not a dedicated snapshot table. This is sufficient for the present
  operation/audit contract and avoids an unnecessary migration in this gate.

## Validation

- PRT-01..PRT-08: 8 passed.
- Provider/Golden/Post-Goal focused gate: 25 passed.
- Full backend: 165 passed, 1 skipped.
- compileall: PASS.
- Ruff check/format: PASS.
- OpenAPI formal/runtime parity: 38/38, missing 0, extra 0.
- Frontend production build: PASS.
- Backend-connected Playwright Golden Scenario: PASS.
- Fresh-extract backend suite, OpenAPI parity, frontend build and Playwright:
  PASS. Playwright accepts `CITYNEXUS_PYTHON` for portable checkpoint replay.

The skipped test is the opt-in live Valhalla smoke when no live endpoint is
configured. The two backend warnings are upstream Starlette/httpx and AnyIO
deprecations and do not block this gate.
