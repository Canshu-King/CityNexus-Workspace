# V13 External Findings Reproduction

Runtime label: `V13_LOCAL_REPLAY_AND_SYNTHETIC_AUTONOMOUS_GOLDEN`  
Repository: `D:\moodle\CityNexus`  
Starting HEAD: `7d22cd0eb7840121ba42a5ba363e1a4c7ca1a7e7`

This report records the independent V12 review hypotheses as engineering
findings. A finding is marked fixed only where the live API and a regression
test demonstrate the invariant; a provider or deployment claim is not inferred
from a local deterministic fixture.

| Finding | Reproduction | Result | Evidence |
| --- | --- | --- | --- |
| A. Execution state machine was client-enforced | Sent `arrive`, `begin`, and `complete` while the current activity was `ACTIVE`; repeated and backward transitions were also sent. | **REPRODUCED / FIXED.** The server rejects illegal transitions with `409 INVALID_ACTIVITY_TRANSITION` without mutation. The authoritative path requires `ACTIVE -> EN_ROUTE -> ARRIVED -> IN_PROGRESS -> COMPLETED`; `SKIPPED` is terminal and policy-protected. | `backend/app/main.py`; `test_v13_execution_rejects_illegal_transitions_without_mutation`; terminal/old-plan coverage in the same suite. |
| B. Trip Studio could use mutable MobilityFact rows | Persisted a plan, mutated every underlying `MobilityFact` to duration `9999`, an absurd cost, and a new provider, then previewed and accepted the same reorder. | **REPRODUCED / FIXED.** Preview and accept use the persisted evidence snapshot and retain the original leg facts. | `backend/app/main.py`; `test_v13_trip_studio_replays_frozen_evidence_and_preserves_progress`. |
| C. Trip Studio gate was weaker than authoritative feasibility | Removed one frozen route pair and attempted preview/accept. | **REPRODUCED / FIXED.** Preview and accept share the authoritative deterministic gate; missing evidence, identity, expiry, hash, anchor, timing, budget, and feasibility failures block mutation. | `_trip_studio_authoritative_gate()`; `test_v13_trip_studio_rejects_a_missing_frozen_matrix_pair`; mutated/expired evidence test. |
| D. Active Trip Studio accept could reset progress | Completed the first activity, reordered only future activities, and accepted. | **REPRODUCED / FIXED.** Completed status, execution timestamps, current activity, current state, historical prefix, and commitment remapping survive the new PlanVersion. | `_trip_studio_context()` / accept path; `test_v13_trip_studio_replays_frozen_evidence_and_preserves_progress`. |
| E. Accepted manual plan metrics could be stale | Accepted a reordered plan after mutating live mobility facts. | **REPRODUCED / FIXED.** New legs and total duration/cost are materialized from frozen facts and recomputed before persistence; route duration is not double-counted. | Authoritative Trip Studio materialization; frozen replay test and no-op test. |
| F. Browser offline cache could lag server truth | Exercised the authoritative browser flow through accept, offline snapshot, reload, and the dev service-worker path. | **REPRODUCED / FIXED for the supported local flow.** Development now registers `/sw.js`, production registers `/v10-sw.js`; the accepted PlanVersion and execution projection converge in the API/offline/browser checks. A multi-device offline conflict simulation remains outside this local campaign. | `frontend/src/main.tsx`; `v13-authoritative-integrity.spec.ts`; `test_v12_authoritative_compose_same_evidence_execute_studio_and_edge`. |

## Additional adversarial runtime findings

These were discovered after A–F were green and are counted separately from
the external review hypotheses:

- Repeated navigation exposed a dual-worker race: Vite PWA auto-registered
  `dev-sw.js` while the application registered `/sw.js`. The automatic dev
  registration was removed; one explicit worker now owns the development path.
- Removing that duplicate initially exposed an offline-module gap. The
  explicit worker now caches same-origin Vite resources network-first and
  falls back to those resources offline, while API and HMR requests remain
  uncached.
- Full-sequence Guardian hydration could display persisted `PLANNING` after
  the server had completed the run. Single-flight refresh now settles bounded
  in-progress runs against server truth.
- A process-global Guardian worker could outlive a reset when its in-flight
  cycle exceeded the previous join window. The reset boundary now waits up to
  a bounded 30-second minimum before a new subscription can start.

All four additional findings have repeated browser or focused regression
evidence; none is marketed as a live-provider or multi-device guarantee.

## Interpretation boundary

These fixes establish server-owned integrity for the V13 authoritative path.
They do not claim that an unconfigured DeepSeek/Hermes endpoint, Phoenix
collector, or live provider network was exercised. The current V13 evidence is
labelled explicitly as captured replay or synthetic fixture in the relevant
PlanVersion evidence payloads and in `GATE_MATRIX.md`.
