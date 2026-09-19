# GitHub/project integration after deterministic WP06 is green

The installed foundation modules are intentionally mostly unused at runtime right now. Wire them one capability at a time.

## Mobility

- `routingpy`: client abstraction.
- Valhalla: first real road/walk/bike/matrix target.
- GraphHopper: alternate provider after Valhalla works.
- OpenTripPlanner: transit-only provider after GTFS is available.

Never pass a live routing client directly into feasibility. Freeze results into MobilitySnapshot first.

## Context

- Open-Meteo: weather context/event facts.
- Convert verified provider facts into Event/ContextSnapshot.
- Weather is context, not permission to invent hard closure unless policy maps it to a deterministic rule.

## Optimisation

- OR-Tools behind PlannerAdapter.
- Start by selecting among already feasible deterministic candidate families.
- Later model time windows/selection variables.
- Every result still goes through the same feasibility gate.

## AI

- LiteLLM + DeepSeek only after deterministic ReplanDiff is meaningful.
- First real use: `explain_replan(diff, verified_facts)`.
- Keep deterministic fallback.
- No AI-generated ETA/opening/payment/C4 facts.

## Frontend

After APIs stabilize:

- MapLibre: map/rendering;
- Turf: spatial calculations;
- XState: UI workflow only;
- shadcn/ui: components;
- Playwright: Golden Scenario.
