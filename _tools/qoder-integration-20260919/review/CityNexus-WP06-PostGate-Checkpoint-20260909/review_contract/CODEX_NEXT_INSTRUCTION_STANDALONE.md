# CODEX — Continue CityNexus After Deterministic WP06 / JourneyTwin v2 Checkpoint

## Non-negotiable user rule

**NO SHA/file/archive hash work.**
Do not calculate, compare, verify, report, or create package/file hash manifests.
Application request fingerprints used for idempotency are legitimate business logic and should remain.

## Do not roll back current work

Work in the current `D:\moodle\CityNexus` tree.
Do not reset to the review ZIP.
Do not discard newer local changes.
Do not remove the Post-WP04 Foundation, deterministic WP06, JourneyTwin v2, provider snapshot boundary, or existing tests just to make a patch apply.

The reviewed checkpoint is substantially good. Continue forward.

---

# Phase A — Merge bounded post-gate hardening

Read:

- `00_INDEPENDENT_REVIEW.md`
- `01_POSTGATE_HARDENING_FINDINGS.md`
- `02_REPLAN_LIFECYCLE_AND_IDEMPOTENCY.md`
- `PATCH_APPLY_NOTES.md`

Then inspect the real current files before editing.

Try the prepared patch only if the current tree is compatible:

`patches/CityNexus_WP06_PostGate_Hardening_and_ProviderPrep_20260909.patch`

Use `git apply --check` first. If it fails because the local code moved forward, do not reset. Merge the equivalent behavior manually using `reference_overlay/` as the semantic reference.

Merge the OpenAPI overlay manually and preserve any newer local contract changes.

Required behavior:

1. replan accept requires valid `Idempotency-Key`;
2. same key + same proposal replays the original success without duplicate audit/state change;
3. same key + different proposal conflicts;
4. accepted trigger Event becomes ACKNOWLEDGED;
5. an Event already handled by an ACCEPTED proposal cannot create another replan;
6. accepting one proposal invalidates sibling PRESENTED proposals for the same superseded base and rejects their candidate PlanVersions;
7. rejecting a proposal retires its CANDIDATE PlanVersion and is audit-idempotent on re-reject;
8. JourneyTwin aggregates degradation from all unresolved DETECTED/ACKNOWLEDGED Events;
9. JourneyTwin is DEGRADED while any such provider degradation remains;
10. replan `estimated_duration_min` is recomputed from proposed Activities;
11. ReplanDiff identity supports `place_id` OR `city_service_id` OR Activity fallback;
12. ReplanDiff protected evidence uses durable C4 semantic/time anchors in addition to `Activity.locked`.

Run all existing tests plus the new hardening tests. Repair integration conflicts; do not delete the foundation.

Do not STOP merely because Phase A becomes green. Continue to Phase B.

---

# Phase B — Establish the first real mobility path without contaminating the gate

Read:

- `03_VALHALLA_SNAPSHOT_NEXT.md`
- `04_ROUTINGPY_REASSESSMENT.md`

Keep the CityNexus-owned `MobilityProvider` abstraction authoritative.

**Do not make routingpy mandatory.** Keep the already-present routingpy adapter as an optional compatibility implementation. Its latest public release is old compared with the current project/Python baseline.

First real path:

```text
ValhallaHTTPMobilityProvider
-> capture_mobility_snapshot()
-> frozen MobilitySnapshot
-> deterministic feasibility/replanning
```

The prepared direct Valhalla HTTP adapter uses the existing `httpx` dependency and supports route + matrix parsing.

Tasks:

1. integrate the prepared `valhalla_http.py` and `snapshot_capture.py` if not already present;
2. keep all default tests network-free with `httpx.MockTransport`;
3. add configuration for an OPTIONAL Valhalla base URL/profile, disabled by default;
4. add an opt-in local provider smoke test, clearly separated from the default suite;
5. if local Valhalla is available, capture real ETA/matrix facts and prove the frozen snapshot passes the same authoritative gate;
6. if setup is expensive or unavailable, do not block the project; preserve mock/frozen fallback.

`pyvalhalla` may be evaluated as an optional local Windows implementation after the HTTP path. Do not force tile-building work into the critical path.

Do not put HTTP/routingpy/pyvalhalla objects inside `evaluate_feasibility()`.

Do not STOP after this if the mandatory network-free gate is green. Continue Phase C.

---

# Phase C — Fix scoring/candidate semantics before OR-Tools and frontend comparison

Read `05_SCORE_AND_CANDIDATE_COUNT_NEXT.md`.

Current P1 defects:

- replan `utility_score` / `score_breakdown` are copied from the base plan;
- replan `candidate_count` accepts 1..5 but currently produces one proposal.

Do not ask an LLM to score plans.

Implement verified deterministic scoring from available facts and the existing weight model. Do not fabricate metrics that are not supported by current data; document neutral/unavailable policy explicitly.

Then give `candidate_count` real semantics using small deterministic candidate families first:

```text
F0 same-slot replacement
F1 optional removal
F2 suffix delay/shift
F3 opportunity-window-compatible replacement
```

Each candidate must pass the same authoritative feasibility gate before scoring/ranking.

Only after deterministic multi-candidate semantics are stable should OR-Tools be activated as an optional advanced candidate generator/optimizer.

OR-Tools is allowed to search. It is not allowed to overrule feasibility.

---

# Phase D — Freeze Event provenance before real context feeds

Read `06_EVENT_PROVENANCE_AND_DEMO_TIME.md`.

Before Open-Meteo/OTP/live provider Events are considered trusted, distinguish at least:

```text
SIMULATED
PROVIDER_VERIFIED
USER_REPORTED
SYSTEM_DERIVED
```

A public client must not be able to forge `provider_key=open-meteo` and have that treated as provider evidence.

The Event Simulator must use explicit deterministic `occurred_at` aligned with the demo Journey/Twin `now`.

Keep the migration bounded. Do not build a generalized event-sourcing platform.

---

# Phase E — Continue planned GitHub integrations

After Phases A-D mandatory gates are green:

1. Open-Meteo context adapter -> freeze verified context/event facts;
2. GraphHopper optional second mobility provider;
3. OpenTripPlanner only after a usable GTFS source is confirmed;
4. OR-Tools optional advanced planner, still behind feasibility;
5. LiteLLM + DeepSeek via `ResilientAIExplanationService`;
6. AI only receives `VerifiedExplanationFacts`, ReasonCodes and evidence;
7. deterministic fallback remains available when AI is absent/fails;
8. React UI: MapLibre + Turf + XState + shadcn/ui;
9. Playwright Golden Scenario after API/UI contracts stabilize;
10. WebAuthn step-up and real payment adapters remain optional/controlled extensions.

Do not make any external provider required for the default coursework demo.

---

# Test/quality rule

Run the existing suite and new tests in the project's normal Windows environment.

The independent Linux review observed that split suites pass but a very large one-process invocation may sometimes reach all dots without returning before harness timeout. Do not treat this as a functional failure without reproducing it locally. If reproduced, centralize `TestClient` lifecycle using explicit fixtures/teardown as described in `07_TEST_HARNESS_CLEANUP.md`.

Keep:

- compileall green;
- Ruff/lint/format green if already installed;
- OpenAPI parse green;
- runtime/formal endpoint operation sets aligned;
- default tests network-free.

---

# Progress behavior

Do not stop simply because one phase is green. Continue through the next bounded phase while the working tree is healthy.

Create a repo-relative checkpoint for GPT review after the next meaningful boundary, ideally after:

- post-gate hardening is integrated;
- first Valhalla provider path is present but optional;
- verified replan scoring/candidate semantics are implemented;
- Event provenance contract is frozen;
- all default tests pass.

The checkpoint must preserve exact repo-relative paths and dependency manifests. No hash manifests.
