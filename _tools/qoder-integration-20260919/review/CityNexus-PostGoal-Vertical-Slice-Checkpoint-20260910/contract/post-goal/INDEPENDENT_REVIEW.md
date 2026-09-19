# Independent GPT Review of 2026-09-10 Goal Output

## Reviewed inputs

- `CityNexus_Complete_Handoff_20260910_v2`
- `CityNexus_Product_GitHub_Masterplan_20260910`
- `CityNexus-WP06-WP07-Road-Prep-GPT-Review-20260910`
- `CityNexus-Overnight-Checkpoint-20260910`

The 2026-09-10 v2 handoff supersedes the older Visio-route-centered handoff. Current project priority is a real backend-connected Golden Scenario and then provider/solver/AI expansion, not more Visio route calibration.

## Independent replay of the overnight checkpoint

From the extracted `backend/`:

```text
python -m pytest -q
149 passed, 1 skipped
```

This independently confirms the checkpoint's total backend self-report.

That aggregate green suite did not cover five previously identified semantic defects. A separate five-test adversarial suite was executed against the original checkpoint and produced five failures, one per defect.

## Defect 1: F3 stale-time semantics

Original behavior in `backend/app/main.py` evaluates `F3_OPPORTUNITY_WINDOW` from the affected Activity's old `start_at` instead of the trigger Event's effective `occurred_at`.

Why it matters: a dynamic recovery candidate can be proved against a time that has already passed. The persisted replacement schedule can then disagree with the OpportunityWindow evidence.

Repair prepared:

- derive `effective_event_time` from `trigger_event.occurred_at`;
- normalize naive simulator input onto Journey schedule timezone;
- choose future C4 anchor relative to Event time;
- evaluate opening hours and F3 window relative to Event time;
- persist F3 replacement start as `window_opens_at + inbound_travel_min` rather than the superseded slot.

## Defect 2: stale C4 `activity_id` after accepted replan

The durable C4 Commitment survives the replan, but `Commitment.activity_id` can still reference an Activity belonging to the superseded PlanVersion. JourneyTwin then exposes a backward pointer.

Repair prepared:

- after proposed PlanVersion becomes active, remap each active C4 Commitment to the semantically corresponding Activity in the new active plan;
- use durable policy evidence (`semantic_key` and `scheduled_start_at`) to locate the preserved C4;
- fail safe with HTTP 409 if an accepted proposal cannot be remapped, because such a state contradicts the authoritative preservation gate.

## Defect 3: frozen MobilitySnapshot cannot enter persisted-plan gate

The lower feasibility layer accepts a mobility provider/snapshot abstraction, but `validate_plan_feasibility()` hardcodes `MockMobilityProvider()`.

Repair prepared:

- add optional `mobility_provider` injection to persisted-plan and selected-plan validators;
- preserve Mock fallback as default;
- test a frozen `MobilitySnapshot` passing through the authoritative gate.

This is necessary groundwork for truthful Valhalla runtime evidence. Merely owning a Valhalla adapter file is not the same thing as using its facts in the decisive gate.

## Defect 4: Open-Meteo time semantics

The adapter uses `datetime.fromisoformat(str(raw_time))`. Open-Meteo can return Unix timestamps, so an integer timestamp is malformed for this parser. The previous `timezone=auto` path also risks timezone-free wall-clock evidence.

Repair prepared:

- request `timezone=UTC` and `timeformat=unixtime`;
- parse numeric timestamps with timezone-aware UTC `datetime.fromtimestamp`;
- retain compatible ISO parsing and explicitly attach UTC to naive ISO fixtures because this adapter now requests UTC.

## Defect 5: traffic delay payload semantics

The canonical traffic mock/event path uses `extra_minutes`, while replan generation reads `delay_minutes` and otherwise defaults to 15.

Repair prepared:

- `TRAFFIC_DELAY`: prefer `extra_minutes`, then `delay_minutes`;
- `SCHEDULE_DELAY`: prefer `delay_minutes`, then `extra_minutes`;
- regression test explicitly proves +25 minutes remains +25.

## Independent repair validation

On a clean copy of the uploaded checkpoint after applying the prepared repair patch:

```text
post-Goal defect tests       5 passed
backend Golden contract      1 passed
focused gate total           6 passed
full backend suite           155 passed, 1 skipped
compileall app tests         PASS
```

A fresh `git apply --check` was also successful against the uploaded checkpoint copy.

Ruff was not rerun by GPT after the final repair patch because Ruff is not installed in this sandbox environment. The uploaded overnight checkpoint reports Ruff PASS before these three source files/two tests were added. Codex must rerun Ruff in the real Windows environment.

## Frontend reality check

The overnight report correctly calls the frontend a "deterministic contract shell", but its Playwright result should not be promoted to backend-connected E2E.

Current `frontend/src/main.tsx`:

- hardcodes current/next Activity;
- hardcodes budget, opportunity window, buffer and commitments;
- hardcodes candidate families, score, evidence and deltas;
- persists accepted UI state in `localStorage`.

Current `frontend/e2e/golden.spec.ts` interacts only with that browser-local shell. It does not call `/api/v1`, does not create a persisted Journey through backend, and reload success is explained by `localStorage`.

Therefore:

```text
Frontend build = real build evidence
Existing Playwright = UI smoke evidence
Backend-connected Golden E2E = NOT YET IMPLEMENTED
```

## Provider / Solver / AI reality check

- **Valhalla**: real HTTP adapter and snapshot foundation exist, but the decisive persisted-plan gate path needs the new injection seam before a frozen runtime snapshot can become authoritative evidence.
- **Open-Meteo**: provider foundation exists; timestamp/timezone repair is required for real payload safety.
- **OR-Tools**: optional adapter/foundation exists. It should not be described as a mature runtime optimizer until actual candidate generation is run in the normal generate → gate → score path with the optional dependency enabled.
- **LiteLLM/DeepSeek**: optional explanation provider/fallback exists. No live model or credential was used in this checkpoint, which is the right default for a deterministic course demo.

## Engineering decision

Do not spend the next Codex cycle on more breadth. Close the semantic repair gate first, then make the existing frontend consume the existing backend contracts. A single real vertical slice is worth far more than a museum of adapter files with impressive nouns and no end-to-end truth.
