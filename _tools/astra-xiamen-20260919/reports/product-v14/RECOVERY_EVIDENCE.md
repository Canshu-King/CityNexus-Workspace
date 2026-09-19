# Recovery Evidence Record

## Evidence separation

`baseline_plan_evidence` describes the frozen selected PlanVersion and its provider facts at planning time. It is retained as an immutable reference.

`incident_recovery_evidence` is a new record for the disruption. It carries its own evidence ID, event/capture timestamps, provider observation ID, route and cost provenance, mobility snapshot ID, weather evidence, provider capabilities, degraded status, and any baseline reference marker. A recovery cannot present the baseline matrix as current incident reality in the strict grounded path.

## V14 Golden sequence

1. A fully grounded Tianjin journey is composed and selected.
2. Arrival is executed, establishing a real execution state.
3. A sealed Open-Meteo forecast deterioration is captured as a provider-backed weather observation.
4. The server resolves the changed event to an existing Activity and records incident provenance.
5. A separate sealed Valhalla mobility snapshot/reserve supplies grounded alternatives.
6. The deterministic gate checks feasibility, budget, timing, protected anchors, and provider facts.
7. Delegation policy is evaluated; this run presents confirmation because the active policy is advisory.
8. Acceptance creates the child PlanVersion and remaps the departure C4 at the activity end boundary.
9. The accepted child is reflected in JourneyTwin, authoritative execution, offline snapshot, and the UI.

## Observed UI result

The browser surface showed:

- changed Place identity;
- `C4 commitments preserved`;
- baseline evidence ID;
- `valhalla · SEALED_REAL_REPLAY` incident evidence;
- `PASSED · provider facts frozen` deterministic gate;
- `ADVISORY · confirmation required` delegation policy;
- accepted child PlanVersion ID.

The same page reloaded with browser networking offline and rendered `OFFLINE · READ ONLY`, `Your next 24 hours are saved`, and the saved provider freshness timestamp from Dexie/service-worker continuity.

