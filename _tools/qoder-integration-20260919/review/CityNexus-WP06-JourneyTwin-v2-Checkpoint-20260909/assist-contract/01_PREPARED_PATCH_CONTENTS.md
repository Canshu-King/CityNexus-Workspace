# What the prepared patch already does

The supplied patch was applied to an independently reconstructed copy of the current checkpoint.

## Repairs

1. Persist JourneyTwin inside the same transaction as start/activity-complete.
2. Extend active-plan feasibility mutation protection to `ACTIVE + ACTIVE` Journeys.
3. Require active Journey/active Plan for Replanning.
4. Require trigger Event ownership and actionable Event state.
5. Present ReplanProposal before acceptance.
6. Remap current execution position onto the proposed PlanVersion during acceptance.
7. Translate durable `C4_Anchored` Commitment policy facts into hard lock constraints.
8. Revalidate the proposed plan immediately before acceptance.
9. Add a deterministic canonical CLOSURE recovery family:
   - Tech Art Center closure
   - deterministic replacement = Design Library
   - River Cruise 15:30 C4 remains unchanged
   - ReplanDiff shows Tech Art removed / Design Library added.
10. Add a frozen `MobilitySnapshot` boundary so real provider outputs can later be consumed deterministically without network calls inside the feasibility gate.

## Added regression tests

11 new tests cover:

- Twin persistence;
- ACTIVE Journey mutation guard;
- ACTIVE-only Replanning;
- cross-Journey Event rejection;
- current-activity remap;
- proposal presentation lifecycle;
- C4 acceptance revalidation;
- canonical closure recovery;
- deterministic closure replacement choice;
- live-router rejection inside the gate;
- frozen real-provider snapshot acceptance.

## Independent patch validation

Against the reconstructed current checkpoint:

```text
before patch: 104 passed
after patch:  115 passed
compileall:    PASS
```

The patch was also tested with `git apply --check` and a clean application to the reconstructed baseline.
