# Frozen Evidence Integrity

## Evidence contract

Each authoritative PlanVersion persists an immutable mobility evidence payload
with:

- evidence/snapshot identity;
- provider and provenance (`CAPTURED_PROVIDER_FACTS`, `SEALED_REAL_REPLAY`, or
  explicitly labelled `SYNTHETIC_FIXTURE`);
- capture and expiry times;
- degradation/fallback semantics;
- route facts, mode, geometry, duration, cost and currency;
- a canonical `integrity_hash` over the payload excluding the hash itself.

The V13 normalizer accepts the V12/V13 shape but preserves the provenance
distinction. The authoritative gate verifies the hash, evidence identity,
validity and required origin/destination matrix pairs before accepting a
Trip Studio edit. Accept never recaptures live provider data.

If a matrix contains both replay and synthetic rows, the evidence explicitly
uses `MIXED_PROVIDER_FACTS` with `provenance_components`; it is never promoted
to a full captured-provider claim.

## Falsification tests

1. `test_v13_trip_studio_replays_frozen_evidence_and_preserves_progress`
   mutates all persisted `MobilityFact` rows to absurd duration/cost/provider
   values after capture. Repeated preview has the same preview/evidence IDs and
   original facts; accepted legs do not contain the mutation.
2. `test_v13_trip_studio_rejects_mutated_or_expired_frozen_evidence_on_accept`
   changes a fact and expiry while retaining the snapshot identity. Accept
   returns `TRIP_STUDIO_DETERMINISTIC_GATE_FAILED` and creates no plan.
3. `test_v13_trip_studio_rejects_a_missing_frozen_matrix_pair` removes a route
   pair and recomputes the hash. Preview reports
   `FROZEN_ROUTE_EVIDENCE_MISSING` and accept remains blocked.
4. V10 provider replay tests reject tampering and unlabelled synthetic input;
   provider-runtime tests prove an authoritative gate does not call a live
   router.

## Real-city truth boundary

`data/replay/tianjin_real_snapshot.json` is a captured Tianjin replay:
Nominatim anchor/candidates, Valhalla mobility facts, Open-Meteo weather and
capture metadata are present; the recorded Overpass query had `NO_RESULTS` and
the candidate path is explicitly represented. This is sealed replay evidence,
not a claim of a live network call during this run.

The V13 authoritative composer Golden uses a deterministic synthetic fixture so
the test is repeatable without internet access. It is labelled
`SYNTHETIC_FIXTURE` in evidence and must not be marketed as live production
provider proof.
