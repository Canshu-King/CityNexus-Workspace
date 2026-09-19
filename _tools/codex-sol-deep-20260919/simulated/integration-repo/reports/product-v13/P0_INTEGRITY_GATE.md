# V13 P0 Integrity Gate

## Result

**PROVEN for the local authoritative replay/synthetic contract.** The gate is
server-owned and is exercised through the live FastAPI API. The local run does
not prove production-scale concurrency or availability of external providers;
those boundaries are called out in the gate matrix.

| P0 item | Contract now enforced | Evidence | Status |
| --- | --- | --- | --- |
| P0-01 execution graph | Predecessor state, current activity, active PlanVersion, terminal-state and wrong-activity checks are validated before mutation. | `test_v13_execution_rejects_illegal_transitions_without_mutation`; terminal/old-plan test. | **PROVEN** |
| P0-02 frozen evidence identity | Evidence carries provider/provenance/capture/expiry/degradation fields and an integrity hash. Preview/accept reject mutation or stale identity. | `test_v13_trip_studio_rejects_mutated_or_expired_frozen_evidence_on_accept`. | **PROVEN** |
| P0-03 one deterministic gate | Trip Studio uses the same authoritative feasibility service for preview and accept; accept re-resolves state before writing. | Missing matrix pair, stale preview, expired evidence and replay tests. | **PROVEN** |
| P0-04 progress preservation | Historical and current execution state, timestamps, current pointer and commitment mapping survive manual edit. | `test_v13_trip_studio_replays_frozen_evidence_and_preserves_progress`. | **PROVEN** |
| P0-05 truthful metrics | Accepted legs, total duration and cost are computed from the frozen route facts and activity dwell; route time is counted once. | Frozen replay test; no-op and authoritative compose tests. | **PROVEN** |
| P0-06 offline convergence | Offline snapshot includes authoritative execution and active PlanVersion state; frontend has one explicit dev/prod SW owner; same-origin dev resources are network-first with cached offline fallback; API/HMR remain uncached; the authoritative stream has bounded disconnect-aware lifetime. | V12/V13 offline API tests, V9 offline browser regression, repeated reload stress, and full Playwright matrix. | **PROVEN locally** |
| P0-07 event to recovery | Replay/fixture signal becomes an Event, Guardian evaluates it, Gateway policy allows bounded recovery, deterministic planning mutates the domain, and projections refresh. | `test_v13_authoritative_predictive_recovery_executes_through_gateway_and_offline_truth`. | **PROVEN locally** |
| P0-08 C4 protection | Mid-trip C4 arrival anchors are created via Journey Inbox, bound to the selected Activity, and remain active through recovery; protected skip is rejected. | `test_v13_mid_trip_c4_is_fixed_and_bound_to_selected_activity_via_inbox_api`; protected-current test. | **PROVEN** |
| P0-09 idempotency/retry | No-op and repeated non-no-op Trip Studio accepts cannot create an unintended second PlanVersion; concurrent same-preview accepts have one winner; process and database compare-and-swap guards reject stale writers; Guardian failures become retryable; an observation pair is reused only when its PlanVersion matches; reset cannot start a new subscription beside a draining process-global worker. | no-op/repeated-accept/concurrent tests, signal-pair reuse test, retryable-failure test, SQLite busy-timeout/WAL runtime boundary, worker-drain stress matrix, full backend regression. | **PROVEN for the local SQLite deployment boundary** |

## Gate semantics

The deterministic layer verifies the post-action Journey: hard schedule and
opening constraints, route/evidence availability, budget/currency, commitment
anchors, provider state, and PlanVersion/evidence identity. It does not attempt
to replace natural-language semantic judgement. AI-originated facts still
enter through server-owned activity and ownership checks, and learned or model
signals cannot enlarge a user's Autonomy Envelope.
