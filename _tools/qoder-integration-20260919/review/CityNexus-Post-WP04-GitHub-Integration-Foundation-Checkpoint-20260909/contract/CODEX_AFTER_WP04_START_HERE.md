# CODEX START HERE — after WP04 external PASS only

## First rule

Do not interrupt the current WP04 work. This package becomes active only after the WP04 checkpoint is externally accepted.

No hash work. Do not calculate or compare SHA/file/package hashes.

## Step 0 — reconcile with the actual post-WP04 repo

Read the real current files first:
- `backend/app/integrations/ports.py`
- `backend/app/core/config.py`
- `backend/app/replanning/feasibility.py`
- WP04 Booking/Payment/Commitment implementation
- current `contracts/openapi.yaml`
- current tests

Then compare with `backend_overlay/`. Do not overwrite a newer WP04 implementation blindly.

## Step 1 — install only the zero/low-conflict foundation

Copy/adapt these first:
- `app/intelligence/reason_codes.py`
- `app/intelligence/opportunity_window.py`
- `app/intelligence/replan_diff.py`
- `app/integrations/provider_status.py`
- pure tests for those modules.

Run the entire existing backend suite. Stop if any regression.

## Step 2 — WP05

Implement Journey execution/JourneyTwin first with mock providers only.
Use the new OpportunityWindow and FeasibilityEnvelope only as derived projection data.
Do not add real networking yet.

STOP at the WP05 gate and checkpoint.

## Step 3 — WP06 deterministic core

Implement the full existing WP06 event/replan contract with mocks.
Use `ReplanDiff` as a persisted/API-visible proposal companion.
Keep locked Commitment preservation inside the authoritative feasibility/policy layer.

Only after mock WP06 is green:
- integrate `routingpy`;
- first real mobility target: local/test Valhalla;
- GraphHopper second;
- OTP only after a valid GTFS source is confirmed;
- integrate Open-Meteo as non-authoritative weather context with fallback.

## Step 4 — OR-Tools

Do not replace the heuristic planner immediately.
Add `ORToolsPlanner` behind a planner adapter, compare outputs, and still run every output through the same deterministic feasibility gate.

## Step 5 — WP07 AI

Add fallback AI first.
Then add LiteLLM adapter and configure DeepSeek via environment variables.
AI receives only verified facts/ReasonCodes for explanations.
AI-off and provider-outage scenarios are mandatory.
Consider PydanticAI only after the simple adapter is stable and tool-calling is actually needed.

## Step 6 — WP08 frontend

Create React/Vite UI using:
- MapLibre GL JS
- Turf
- XState frontend workflows
- shadcn/ui components

Do not move backend rules into XState.
Add stable `data-testid` attributes for Golden Scenario steps from day one.

## Step 7 — WP09

Add Playwright Golden Scenario and screenshots only when the UI contracts are stable.

## Important project reuse rule

Do not import whole Travel-Story or PlacesRecommendation applications. Borrow/adapt the proven patterns and use their underlying open-source building blocks behind CityNexus contracts.
