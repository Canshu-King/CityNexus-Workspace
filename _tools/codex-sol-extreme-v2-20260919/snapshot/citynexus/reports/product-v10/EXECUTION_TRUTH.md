# Execution truth and autonomy boundary

`ExecutionClock` is freezeable and shared by NOW/NEXT, leave-by, Edge C4, offline snapshots, and current Activity selection. Edge C4 uses scheduled Commitment time minus actual clock time, not planned current Activity start. Risk and Autopilot state are derived from persisted Journey/Guardian/enrollment truth.

Offline state is read-only, IndexedDB-backed, and covers the next 24 hours from actual runtime now. Financial actions remain disabled offline. The V9 offline E2E passes after a fresh service-worker-controlled reload.

The Autonomy Envelope remains the authority boundary: reversible low-risk transport changes can execute inside preauthorized budget/loss/drift/type limits; protected durable Commitments require the configured higher policy/confirmation path. Learned preferences influence ranking/objectives/explanations but do not expand budget, payment, Commitment, or autonomy authority.

Notifications now expose a non-secret push capability route. When VAPID and optional `pywebpush` are configured, active subscriptions can receive Web Push; otherwise the event remains an auditable `PUSH_RECORD`/in-app record. No background-GPS claim is made.

The V10 flagship deterministic test proves Inbox text/image drafts, critical-field confirmation, selected-POI composition, non-authoritative web evidence, actual execution-clock output, and push fallback. The browser suite proves the same product remains usable through V5/V6/V8/V9 recovery, mobile UI, offline, and reload.

