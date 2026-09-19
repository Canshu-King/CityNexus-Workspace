# CityNexus Vertical Slice Checkpoint - Independent GPT Review

Date: 2026-09-10
Reviewed input: `CityNexus-PostGoal-Repair-Vertical-Slice-Checkpoint-20260910.zip`

## Executive verdict

This checkpoint is a major improvement and the frontend is now materially backend-connected. The previous five Post-Goal defects are repaired in the supplied source, and after reconstructing omitted repository support files the backend independently reproduces the claimed `155 passed, 1 skipped` result.

External acceptance is **CONDITIONAL / HARDENING_REQUIRED**, not because the vertical slice is fake, but because two additional backend semantic defects and several demo/frontend correctness gaps were found by adversarial review.

Do not expand into OR-Tools, LiteLLM/DeepSeek, or broad live-provider work before this hardening gate is merged and replayed on the real Windows worktree.

## What is genuinely good now

The checkpoint has crossed an important boundary:

- React calls real `/api/v1` endpoints rather than inventing accepted Plan/C4/Replan state locally.
- Golden bootstrap performs backend reset, plan generation/selection, booking, CAPTURE, C4 formation, and Journey start.
- Closure/replan/accept are backend operations.
- Reload restores JourneyTwin from backend state.
- `localStorage` contains only the Journey reconnect identifier, not authoritative domain truth.
- Playwright observes backend Event/Replan/Accept/Twin traffic.
- The original five Post-Goal semantic tests pass.

This means the frontend is no longer merely a hardcoded UI smoke shell.

## Independent replay

The uploaded review ZIP is not completely self-contained for backend replay. Running pytest from the extracted `backend` directory initially failed because repository-relative support files were omitted from the expected locations, notably:

- `backend/db/schema.sql`
- `backend/data/mock/wp04_commerce_catalog.json`
- `backend/data/mock/wp04_city_services_overlay.json`

The ZIP contains mock files under root `data/mock`, but current backend tests/services resolve some fixtures relative to `backend/data/mock`. After restoring only these unchanged support files from the prior checkpoint into the review copy, independent replay produced:

```text
155 passed, 1 skipped
```

So the test claim is credible, while the review-package reproducibility needs repair.

## New backend semantic defect A - F3 starts from stale route origin

### Current checkpoint behavior

F3 Opportunity Window computes inbound recovery travel from the activity immediately preceding the disrupted slot.

That is not always the traveler's authoritative execution position.

In the real Golden Scenario, after the traveler has progressed to Tech Art Center and the venue closes at 13:25, the traveler is already at Tech Art. Recovery travel must therefore originate at Tech Art, not Central Food Hall simply because Food Hall has the previous sequence number.

### Adversarial result on original checkpoint

The new test fails. The old evidence does not even expose an `origin_key`, and manual comparison showed the inbound estimate came from the previous slot rather than the current execution activity.

### Prepared repair

Use `journey.current_activity_id` as the primary recovery origin, with previous-slot fallback only when execution position is unavailable. Persist `origin_key` in F3 evidence so the decision can be audited.

## New backend semantic defect B - aware UTC Event not projected onto Journey-local schedule

### Current checkpoint behavior

The previous Post-Goal fix repaired naive Event timestamps by inheriting a schedule offset, but an already-aware UTC timestamp remains UTC.

That is dangerous because F3 also evaluates local opening-hour strings. A real provider may correctly supply an absolute UTC Event instant, while the Journey schedule is `+08:00`. Comparing instants is legal, but interpreting local opening hours on the UTC wall-clock is semantically wrong.

### Adversarial result on original checkpoint

For an Event at:

```text
2026-10-10T05:25:00+00:00
```

which is the same instant as:

```text
2026-10-10T13:25:00+08:00
```

F3 disappeared from the candidate set in the original checkpoint.

### Prepared repair

Normalize every effective Event instant onto the Journey schedule timezone before F3/opening-hour/OpportunityWindow logic. The repaired F3 evidence reports:

```text
window_opens_at = 2026-10-10T13:25:00+08:00
```

## Golden Scenario realism gap - execution pointer did not reach the disruption

The existing backend and frontend Golden flow starts the Journey and then immediately injects a closure at Tech Art Center at 13:25. After `start`, however, the current execution pointer is initially the first 09:00 activity.

That demonstrates API wiring, but not convincing journey continuity.

The strengthened Golden Scenario now completes the prefix activities until `current_activity_id == Tech Art Center` before the 13:25 closure is injected. This makes the replan causally consistent with the story being demonstrated.

## Frontend correctness gap - minor money units shown as major units

Backend monetary values are explicitly minor units (`amount_minor`). The checkpoint's `formatMoney` sends the integer directly to `Intl.NumberFormat` as a major-unit amount.

Example: `13000` minor CNY should display as approximately `¥130`, not `¥13,000`.

The supplied frontend hardening patch converts minor units according to the currency's fraction digits before formatting.

## Frontend idempotency risk

The checkpoint uses Journey-based idempotency keys for operations whose request identity is narrower:

- CAPTURE key should be booking-specific.
- Replan accept key should be proposal-specific.
- Replan generation should be Event-specific.

A second booking or second disruption within the same Journey could otherwise reuse a key for a different request signature and correctly trigger backend conflict behavior.

The supplied frontend hardening changes these keys to booking/event/proposal scope.

## Frontend time-projection consistency

After injecting the 13:25 closure, the checkpoint reloads JourneyTwin without a `now` value. JourneyTwin then derives time from the current activity start. That can make the UI show a 13:20 Opportunity Window while the replan evidence correctly starts at 13:25.

The hardening patch refreshes Twin with the explicit closure Event time.

## Prepared validation after GPT backend repair

Targeted:

```text
3 passed
```

This includes:

- F3 current-execution origin test
- aware UTC -> Journey-local F3 test
- strengthened backend-connected Golden Scenario

Full backend:

```text
157 passed, 1 skipped
```

Compileall:

```text
PASS
```

The frontend edits in this assist package were **not independently rebuilt here** because a complete npm dependency installation was unavailable in this sandbox. Codex must run `npm run build` and `npm run test:e2e` on the real Windows worktree after semantic merge.

## Provider/runtime truth after this checkpoint

Do not yet claim that Valhalla drives authoritative runtime replanning.

The project has good foundations:

- `ValhallaHTTPMobilityProvider`
- `capture_mobility_snapshot`
- `MobilitySnapshot`
- deterministic gate rejection of non-frozen live providers

But product runtime still contains direct `MockMobilityProvider()` usage in selection, JourneyTwin buffer calculation, and replan generation, while proposal evidence still reports `provider: mock-mobility`.

Therefore the next provider milestone is not “install Valhalla.” It is to create one sourced/frozen MobilitySnapshot outside the gate and pass the same frozen evidence through replan generation, feasibility, scoring/diff evidence, and projection where applicable.

## Decision

Current checkpoint status:

```text
POST-GOAL FIVE DEFECTS         PASS
BACKEND-CONNECTED UI           PASS in supplied checkpoint evidence
ORIGINAL BACKEND REGRESSION    155 passed / 1 skipped after fixture reconstruction
NEW HARDENING TESTS            FAIL 2/2 on original checkpoint
GPT BACKEND HARDENING          157 passed / 1 skipped
GPT FRONTEND HARDENING         PREPARED, WINDOWS BUILD/E2E REQUIRED
EXTERNAL FREEZE                NOT YET
```

Merge this hardening first, replay the real Windows gates, package a self-contained review checkpoint, then stop for external review.
