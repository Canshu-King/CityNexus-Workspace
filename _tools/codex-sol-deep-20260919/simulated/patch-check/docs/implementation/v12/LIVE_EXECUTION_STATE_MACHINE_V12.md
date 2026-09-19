# V12 Live Execution State Machine

The durable Activity state path is:

`NOT_STARTED → EN_ROUTE → ARRIVED → IN_PROGRESS → COMPLETED`

with `SKIPPED` as the explicit terminal alternative and `ACTIVE` retained as the existing Journey-start compatibility state. Each transition writes an actual timestamp (`en_route_at`, `arrived_at`, `started_at_actual`, `completed_at_actual`, or `skipped_at`) and a Journey outcome event. The same server projection is used by JourneyTwin, the offline snapshot, and the PIC Edge snapshot; no client invents a parallel current/next state.

Offline is read-only. Edge actions remain within device authority, while state observation carries the same `execution_truth_id`, current Activity, next Activity, and PlanVersion identity.
