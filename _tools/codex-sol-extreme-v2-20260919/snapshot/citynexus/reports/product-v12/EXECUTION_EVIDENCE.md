# Live Execution and Unified Surface Evidence

## State machine

V12 exposes server-owned depart, arrive, begin, complete, and skip actions. Each transition validates the current state, records actual timestamps, emits an auditable outcome event, and refreshes the offline projection. The active JourneyTwin derives NOW/NEXT from the same Activity rows.

## Cross-surface proof

The V12 backend test starts the Journey, transitions the protected prefix, reads the offline snapshot, registers a PIC Edge device, and asserts the Edge NOW state equals the offline NOW state. The active plan payload carries the frozen evidence identity and legs used by the existing Map/experience surface.

The browser proof reached the authoritative page, showed frozen evidence, advanced the first Activity through the live action control, performed a Trip Studio edit, accepted a new active PlanVersion, and reloaded to the same server truth.

## Autonomous recovery

`test_v12_autonomous_recovery_uses_preauthorized_envelope` creates a traffic disruption against the current ordinary Activity, configures an AUTONOMOUS envelope with bounded schedule drift and no Commitment management, and verifies a Gateway `ALLOW_AUTO` decision with executed mutation, preserved C4, zero cost delta, and a changed active plan.

Poor GPS/arrival and protected-anchor negative paths remain server-gated; a client cannot assert arrival merely by reporting a local state.
