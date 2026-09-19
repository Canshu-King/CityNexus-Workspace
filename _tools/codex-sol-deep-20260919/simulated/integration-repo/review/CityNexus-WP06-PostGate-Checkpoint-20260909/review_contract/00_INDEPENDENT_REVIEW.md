# CityNexus WP06 / JourneyTwin v2 — Independent Post-Gate Review

Date: 2026-09-09
Reviewed checkpoint: `CityNexus-WP06-JourneyTwin-v2-Checkpoint-20260909(1).zip`

## Review policy

- No SHA/file/archive hash work was performed.
- Existing checkpoint claims were not accepted from README alone; code and tests were inspected independently.
- No live external network provider was required during validation.

## Overall verdict

**The deterministic WP06 + JourneyTwin v2 checkpoint is a substantial PASS for the scope it claims, but it is not yet the final WP06 freeze.**

The checkpoint has moved CityNexus beyond a mock lifecycle: durable JourneyTwin projection, ACTIVE Journey feasibility, deterministic closure/delay/weather recovery, C4 preservation, PRESENTED proposal lifecycle, ReplanDiff, OpportunityWindow, FeasibilityEnvelope, and frozen MobilitySnapshot boundaries are all present.

Independent replay reproduced the original **119 tests as passing** when executed in stable groups. Python `compileall` also passes.

However, adversarial testing found several post-gate state/contract defects that the original 119 tests do not cover. A bounded hardening patch and next-provider foundation have therefore been prepared rather than pushing these defects into the frontend/live-provider phase.

## Confirmed improvements from the prior checkpoint

- JourneyTwin writes are durable within start/activity-completion transactions.
- ACTIVE Journey feasibility-affecting mutations are guarded.
- Runtime replanning is ACTIVE-only.
- Cross-Journey Event use is rejected.
- Accepting a replan remaps current activity to the new PlanVersion.
- Active C4 commitments are projected into authoritative feasibility constraints and revalidated at proposal generation and acceptance.
- Canonical closure recovery replaces Tech Art Center with Design Library while keeping the 15:30 River Cruise anchor.
- Delay/weather deterministic candidate behavior exists.
- Raw live mobility providers are forbidden inside the deterministic gate; frozen MobilitySnapshot facts are accepted.

## New adversarial findings on the unmodified checkpoint

1. **Accepted Event reuse**: the same Event can generate another PRESENTED replan after a proposal was accepted; Event remains DETECTED.
2. **Competing proposals**: accepting one proposal leaves sibling proposals PRESENTED and their candidate PlanVersions CANDIDATE.
3. **Reject leakage**: rejecting a proposal leaves the proposed PlanVersion CANDIDATE.
4. **Accept idempotency contract drift**: formal OpenAPI requires `Idempotency-Key` on replan accept, runtime does not.
5. **Twin degradation memory loss**: provider degradation is read only from the latest Event, so a later unrelated Event hides an unresolved outage.
6. **Twin readiness overclaim**: projection_status remains READY while an unresolved provider degradation exists.
7. **Replan duration metadata drift**: delay recovery can extend the plan while `estimated_duration_min` remains copied from the base plan.
8. **ReplanDiff identity/protection drift**: diff identity ignores service-only activities and protection evidence relies on `Activity.locked` instead of durable C4 facts.
9. **Replan utility score is stale**: `utility_score` and `score_breakdown` are still copied from the base PlanVersion after schedule/content changes.
10. **Replan `candidate_count` is currently ignored**: requests accept 1..5 but runtime still creates one proposal/PlanVersion.
11. **Event provenance is forgeable by API input**: clients can currently provide arbitrary `provider_key`; this must be separated from trusted provider-ingested facts before live providers are enabled.
12. **Demo time can drift**: Event default `occurred_at` uses wall-clock time while the deterministic demo Journey is on a future fixture date unless Event Simulator sends explicit time.

## Severity judgement

### Patch before live provider/frontend freeze

- replan accept idempotency;
- Event handled semantics;
- competing proposal invalidation;
- rejected candidate retirement;
- provider degradation aggregation/status;
- duration recomputation;
- durable C4-aware diff evidence.

### P1 before OR-Tools / AI explanation / frontend contract freeze

- recompute Replan utility score and score breakdown from the proposed plan;
- implement or explicitly revise the `candidate_count` contract;
- separate simulated Event provenance from provider-verified Event provenance;
- make demo Event time explicit/deterministic.

### P2 engineering hygiene

The complete test suite can reach all test dots in one Linux process but sometimes does not return before the review harness timeout. Split suites complete normally. Eight modules use module-global `TestClient(app)` objects. Centralizing TestClient lifecycle is recommended before CI, but this is not treated as a product blocker here.

## Prepared work

A tested post-gate patch is included. It:

- requires and persists idempotent replan acceptance;
- acknowledges a handled Event;
- blocks Event reuse after accepted recovery;
- invalidates competing proposals and rejects their candidate PlanVersions;
- retires candidate PlanVersions on rejection;
- aggregates unresolved provider degradation into JourneyTwin and marks the projection DEGRADED;
- recomputes replan duration metadata;
- uses place/service semantic identity and durable C4 anchors for ReplanDiff protection evidence;
- adds an external-provider-to-frozen-MobilitySnapshot capture boundary;
- adds a thin direct Valhalla HTTP adapter using existing `httpx`;
- adds a resilient real-AI-plus-deterministic-fallback explanation wrapper.

## Independent validation of prepared work

Stable split test runs after the prepared patch:

```text
foundation/core/provider group          43 passed
WP01-WP04 endpoint/contract group       69 passed
WP05/WP06/post-gate group               19 passed
-----------------------------------------------
total                                  131 passed
```

Additional validation:

```text
python -m compileall -q app     PASS
patch --dry-run -p1             PASS on reviewed checkpoint
git apply --check               PASS on reviewed checkpoint
OpenAPI 3.1 parse               PASS
runtime/formal operations       38 / 38 after server-base normalization
live network calls              NONE required
```

Ruff is not installed in the independent Linux review environment, so no new independent Ruff claim is made. The Codex checkpoint itself reports Ruff passing.

## Gate decision

Proceed, but **merge the prepared bounded hardening first in the current working tree**, then continue into the live-provider phase. Do not roll back the existing deterministic WP06/Foundation work.
