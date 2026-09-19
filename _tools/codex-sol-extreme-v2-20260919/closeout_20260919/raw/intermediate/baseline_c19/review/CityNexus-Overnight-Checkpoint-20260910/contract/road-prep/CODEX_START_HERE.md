# CODEX START HERE — WP06 → WP07 Road Prep

## Non-negotiable rules

- If a command/deployment is currently running, let it finish. Do not kill it just to consume this package.
- Do not roll back accepted WP04/WP05/WP06 work.
- Do not calculate or report file/archive/SHA hashes.
- Keep live providers optional. Default tests/demo remain network-free.
- CityNexus Domain, deterministic feasibility, and C4 Commitment remain authoritative.

## Step 1 — Read the requested repair instruction

Read:

`01_WP06_POSTGATE_FOLLOWUP_REPAIR_INSTRUCTION.md`

Then compare the current local working tree with the checkpoint assumptions.

## Step 2 — Use the prepared patch to avoid redoing solved work

Patch:

`patches/WP06_WP07_ROAD_PREP_20260909.patch`

Preferred flow on the real repository root:

```text
patch --dry-run -p1 < WP06_WP07_ROAD_PREP_20260909.patch
```

If clean, apply it. If not clean because the local repo progressed after the checkpoint, **do not reset**. Semantically merge the same changes using `reference_overlay/`.

The prepared patch already covers:
- feasible candidate counting;
- verified Traveler preference fit;
- neutral opportunity score until real evidence exists;
- JourneyTwin upcoming-commitment filtering;
- optional replan-generation idempotency;
- deterministic score-tie ordering;
- four next-stage foundation modules;
- nine regression/foundation tests.

## Step 3 — Gate the merged tree

Run the existing suite plus:

```text
backend/tests/test_wp06_followup_assist.py
backend/tests/test_wp07_foundation_assist.py
```

Keep the canonical golden closure behavior:

```text
Tech Art Center closed
→ Design Library replacement remains a valid/top deterministic candidate
→ River Cruise C4 preserved
```

## Step 4 — Make F3 truthful

Use:

`02_F3_OPPORTUNITY_WINDOW_INTEGRATION.md`

Wire `opportunity_window_family.py` into the candidate generator. Do not call a second same-slot candidate “F3_WINDOW_REPLACEMENT” unless it actually passes OpportunityWindow evidence.

## Step 5 — Real context and mobility, still outside the gate

Read in order:

1. `03_VALHALLA_AND_MOBILITY_SNAPSHOT.md`
2. `04_OPEN_METEO_PROVIDER_VERIFIED_EVENTS.md`

Network/provider output must be frozen before deterministic feasibility consumes it.

## Step 6 — Advanced planner

Read:

`05_ORTOOLS_ADVANCED_CANDIDATES.md`

OR-Tools is an optional candidate generator behind the same gate. Do not replace the authoritative gate.

## Step 7 — AI

Read:

`06_LITELLM_DEEPSEEK_COPILOT.md`

DeepSeek may explain/recommend/parse preferences, but cannot create payment facts, C4 facts, provider facts, or hard-feasibility results.

## Step 8 — Freeze frontend contract and build UI

Read:

`07_FRONTEND_MAP_STATE_CONTRACT.md`

Then use MapLibre + Turf + XState + shadcn/ui. Frontend must consume the already-verified JourneyTwin/ReplanDiff/FeasibilityEnvelope evidence rather than recomputing business truth.

## Step 9 — E2E

Read:

`08_PLAYWRIGHT_GOLDEN_SCENARIO.md`

## Next external review gate

Do not stop after trivial scaffolding. Continue until the gate in `09_NEXT_GATE.md` is met, then package a repo-relative checkpoint for GPT review.
