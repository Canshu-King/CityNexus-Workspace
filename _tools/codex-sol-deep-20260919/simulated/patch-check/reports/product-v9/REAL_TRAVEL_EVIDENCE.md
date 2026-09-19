# Real-World Trip Operations Evidence

## Authoritative plan reconciliation

Stay selection is no longer a parallel UI-only choice. The selected option materializes one authoritative `PlanVersion` with:

- the selected accommodation and offer provenance;
- ordered Activities and arrival/departure anchors;
- concrete `JourneyLeg` rows for every consecutive transition;
- provider/captured geometry, CRS, mode, duration, walking, transfers, reliability, weather exposure and cost evidence;
- active/superseded lifecycle;
- the same active plan projection in `JourneyTwin` and the offline/edge snapshots.

The deterministic gate validates the resulting plan after mutation. It does not attempt to replace semantic interpretation of unstructured events.

## Generic city graph

`data/v9/city_operations.json` supplies normalized city operations fixtures. Tianjin and Beijing use separate anchors, hotels and POIs. The planner derives date grouping from the Journey timezone and constructs a real sequence of arrival → luggage handling → activities → check-in/stay → checkout/departure. The Beijing regression explicitly rejects Tianjin attraction leakage.

## Provider truth and uncertainty

Mobility facts carry a provider key, capture/freshness metadata, WGS84 geometry and explicit cost states. `UNKNOWN` paid cost is not treated as zero and blocks autonomous selection outside the envelope. Opening-hour normalization preserves uncertainty. Expired accommodation quotes are rejected as unbookable. Missing realtime is represented as `UNKNOWN_REALTIME`; a stale update is not represented as on-time.

## Flagship scenario

The backend test `backend/tests/test_v9_real_trip_operations.py::test_v9_flagship_real_world_trip_operations_e2e` proves:

1. A multi-day Tianjin Journey is created.
2. A structured rail-style confirmation is imported and confirmed.
3. The reservation becomes a protected `C4_Anchored` arrival Commitment.
4. Luggage is declared before hotel check-in.
5. The selected plan includes luggage drop before activity and check-in.
6. Stay and per-leg mobility evidence are present in the materialized PlanVersion.
7. JourneyTwin points to the same plan.
8. A rain/disruption recovery creates a replacement plan and runs the real deterministic feasibility gate.
9. The old plan is superseded and the new plan is active.
10. Notification events and the read-only offline snapshot are updated.
11. The Edge Companion receives NOW/NEXT/MODE/C4 state and cannot create a booking.

The browser test `frontend/e2e/real-world-trip-operations-v9.spec.ts` adds the traveler-facing proof: Inbox paste, wallet Commitment, stay selection, Live Journey route, navigation, location marker, rain recovery, mobile Now/Next/LeaveBy/Navigate, Chinese navigation seam, standalone manifest, service worker, true browser offline reload and IndexedDB snapshot.

## Six external acceptance gates

The supplied checker initially reproduced six failures. After implementation it returned `6 passed / 0 failed`:

- generic itinerary without a hard-coded Tianjin attraction tuple;
- backend/provider route geometry;
- Stay selection materializing core Journey truth;
- executed deterministic post-action gate;
- unknown monetary cost not optimized as zero;
- removal of version/demo leakage from the traveler UI.

No consumer travel website scraping or coursework work was introduced.
