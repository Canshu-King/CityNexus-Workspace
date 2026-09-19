# WP05-WP09 execution roadmap

## WP05 — Journey execution + JourneyTwin

First finish the existing WP05 contract with mocks only.

Add while doing WP05:
- `JourneyTwinProjection` as a pure projection DTO;
- `FeasibilityEnvelope` fields: next commitment buffer, budget remaining, schedule slack, provider degradation indicators;
- frontend-independent `OpportunityWindow` detector, but do not yet make real provider calls;
- audit events for start/current/complete transitions.

Gate before any real provider:
- PLANNED -> ACTIVE works;
- SELECTED -> ACTIVE is consistent;
- Twin is derived, reproducible and has no independent mutable truth;
- activity advancement refreshes Twin.

## WP06 — deterministic event/replanning core

Phase A, mocks only:
- existing Event/ReplanProposal contract;
- protected commitment partition;
- candidate families;
- deterministic feasibility;
- ReplanDiff;
- FeasibilityEnvelope before/after;
- atomic accept/reject.

Phase B, after Phase A is green:
1. add `routingpy` behind the existing mobility boundary;
2. connect one local/self-hosted or test Valhalla provider first;
3. keep MockMobilityProvider as deterministic fallback;
4. add Open-Meteo as a context provider with explicit attribution/degraded mode;
5. GraphHopper becomes alternative provider only after Valhalla path works;
6. OTP only after a real usable GTFS dataset is confirmed.

Do not let real-provider instability make core replanning tests flaky.

## WP07 — AI Copilot / Journey Intelligence

1. create AIProvider protocol and deterministic fallback;
2. add verified `ReasonCode + Evidence` input contract;
3. add LiteLLM adapter with DeepSeek as configured primary;
4. keep model name/config environment-driven;
5. AI-off and provider-outage scenarios must pass;
6. only after this is stable consider PydanticAI for tool calling.

AI output must never be used as the feasibility result.

## WP08 — frontend vertical slice

Use:
- React/Vite existing direction;
- MapLibre GL JS;
- Turf;
- XState for UI workflow state;
- shadcn/ui for components;
- TanStack Query for server state.

Build these visible differentiators first:
- Active Journey map;
- locked Commitment marker;
- Event marker;
- old route vs new route;
- ReplanDiff panel;
- Opportunity Window card;
- AI/fallback mode badge.

## WP09 — E2E and evidence

Add Playwright only after stable `data-testid` contracts exist.

Golden Scenario:
1. reset demo;
2. open seeded journey;
3. booking/payment -> C4/anchored commitment;
4. start journey;
5. inject Tech Art closure;
6. view replan;
7. verify River Cruise preserved;
8. accept proposal;
9. verify new plan active/history;
10. AI disabled scenario remains functional.
