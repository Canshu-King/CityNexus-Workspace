# Frontend Contract Freeze: MapLibre + Turf + XState + shadcn/ui

Do not let the frontend recompute domain truth.

## Pages to build first

1. Journey Dashboard
2. Plan Comparison
3. Journey Mode
4. Replan Comparison
5. Demo Event Simulator
6. AI Explanation panel

## Authoritative data sources

- Journey/Plan status -> backend API;
- map marker/activity status -> active PlanVersion;
- protected commitments -> JourneyTwin/ReplanDiff;
- old/new route metrics -> ReplanDiff + frozen mobility evidence;
- opportunity window -> JourneyTwin context;
- risk/degradation -> FeasibilityEnvelope/JourneyTwin;
- AI text -> explanation only.

## MapLibre layers

- active plan route;
- superseded/base route in comparison mode;
- Activity markers;
- C4 lock marker;
- disruption marker;
- replacement/add/remove visual distinction;
- current Activity/current position if available.

Use Turf only for frontend spatial presentation helpers such as bounds/buffer/distance. Turf is not the authoritative routing engine.

## XState

Use XState for UI orchestration only:

```text
loading
→ ready
→ eventDetected
→ generatingReplan
→ comparing
→ accepting
→ ready
```

Backend Journey/Replan state remains authoritative.

## Required test IDs

See `future_scaffold/frontend/src/contracts/testIds.ts` and the Playwright skeleton.
