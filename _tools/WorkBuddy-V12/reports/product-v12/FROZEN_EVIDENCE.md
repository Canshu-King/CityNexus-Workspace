# Frozen Provider Evidence

V12 stores provider reality as part of the plan rather than re-querying providers during selection or deterministic validation.

## Persisted shape

`PlanVersion` carries `mobility_snapshot_id` and `mobility_evidence_json`. The authoritative evidence contains:

- snapshot/operation/capture/expiry identity;
- provider and aggregate provenance;
- complete directed mobility facts for the bounded node set and available modes;
- selected leg facts, with mode/cost/duration/reliability/geometry/cost-status;
- Stay evidence and evidence normalizer version.

`MobilitySnapshot.from_evidence()` replays the full matrix and applies `selected_facts` last, so the original mode decision remains stable while Trip Studio can evaluate alternate frozen matrix edges.

## Selection gate

Selection loads the candidate PlanVersion, checks snapshot identity and expiry, reconstructs the frozen snapshot, and passes it to deterministic feasibility. It does not invoke a runtime provider. Stale or mismatched evidence returns a recomposition-required result.

## Verification

- `backend/tests/test_v12_authoritative_trip_execution.py` mutates a persisted MobilityFact after composition and selects the candidate successfully from its original evidence.
- `pytest -q` passes all 347 backend tests, including provider-runtime and adversarial same-snapshot tests.
- Legacy generic plans retain a single runtime capture operation for compatibility; only the explicit V12 authoritative evidence normalizer is replayed as a full matrix.
