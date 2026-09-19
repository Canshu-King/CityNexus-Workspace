# Provider Runtime Gap Analysis

## Evidence found in the real worktree before this gate

Existing foundations were sound but disconnected from product runtime:

- `MobilitySnapshot` and `TravelEstimateFact` already existed.
- `capture_mobility_snapshot()` already supported explicit per-pair fallback.
- `ValhallaHTTPMobilityProvider` already parsed route and matrix responses.
- The deterministic feasibility gate already rejected non-frozen live
  providers and accepted frozen snapshots.

The product Replan/Twin path still had material gaps:

1. `generate_replan()` instantiated `MockMobilityProvider()` directly.
2. F3 travel and copied candidate travel used that mock directly.
3. Replan feasibility did not receive the captured provider reality.
4. `verified_evidence.mobility.provider` was hard-coded to `mock-mobility`.
5. JourneyTwin recomputed its next-C4 travel with a new mock provider.
6. There was no operation id/snapshot id or serialized snapshot evidence.
7. Valhalla product runtime was effectively smoke/foundation only.

The first PRT-01..PRT-08 run against that implementation produced:

```text
6 failed, 2 passed
```

The failures covered missing operation capture/reuse, real provider
provenance, auditable fallback metadata, persisted Twin snapshot evidence and
the end-to-end MockTransport snapshot contract.

## Wiring after this gate

- Replan: real/offline provider -> capture once -> frozen snapshot -> all
  candidates -> feasibility -> proposal evidence.
- Valhalla: opt-in product runtime primary, with pair-level deterministic
  fallback.
- Twin: reads persisted snapshot evidence; no live network on read.
- Failure: explicit unavailable result; no fabricated travel fact.

## Remaining real gaps

- Initial planning and plan-selection revalidation remain mock-backed.
- Valhalla runtime capture is route-per-pair rather than matrix-batched.
- There is no independent MobilitySnapshot persistence table or expiry policy.
- Open-Meteo facts are not yet deterministically mapped to affected Journey
  Activities in product runtime.
- OR-Tools remains a candidate-generator foundation and has not been promoted
  to runtime planning authority.

These are follow-on scope items, not failures of the Provider Runtime Gate.
