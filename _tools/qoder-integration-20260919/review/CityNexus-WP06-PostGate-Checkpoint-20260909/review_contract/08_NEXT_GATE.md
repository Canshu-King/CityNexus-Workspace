# Next Gate

The next checkpoint should prove the post-gate hardening and the first provider boundary without making external infrastructure mandatory.

## Mandatory

- all prior checkpoint tests remain green;
- new post-gate hardening regressions pass;
- replan accept requires Idempotency-Key and same-key replay is safe;
- handled Event cannot generate another recovery proposal;
- sibling proposals/PlanVersions are invalidated/rejected when one is accepted;
- rejected proposal retires its candidate PlanVersion;
- JourneyTwin aggregates unresolved provider degradation and reports DEGRADED correctly;
- replan estimated_duration reflects actual proposed plan timing;
- ReplanDiff reports durable C4 protection even if `Activity.locked` is false;
- direct Valhalla adapter and MobilitySnapshot capture are covered with network-free mocks;
- raw live provider remains forbidden inside authoritative feasibility;
- AI primary failure falls back deterministically.

## P1 before frontend comparison freeze

- proposed-plan utility score is recomputed from verified facts;
- `candidate_count` has real semantics or is explicitly revised in contract;
- Event provenance rule is represented in API/data model;
- Event Simulator uses deterministic demo time.

## Live-provider smoke, optional gate

A real local/controlled Valhalla route/matrix smoke may be run after the mandatory gate. Failure to have the service running must not break the default demo/test path.

## Do not regress

- no live provider inside the deterministic gate;
- no AI hard-feasibility authority;
- no payment/C4 inference from LLM output;
- no package/file hash work;
- no rollback of the accepted Post-WP04/WP06 foundation.
