# CityNexus Post-Goal Repair + Vertical Slice Prep

Date: 2026-09-10
Purpose: give Codex a mechanically verifiable next step without making it rediscover the post-Goal defects or waste local model quota.

## 0. Authority and safety

Work in the user's real repository:

```text
D:\moodle\CityNexus\
```

The repository may be dirty and may contain changes newer than this bundle. Therefore this bundle is **not** a blind overwrite package.

Before changing anything:

```powershell
git status --short
git diff --stat
```

Do **not** run any destructive cleanup or rollback command, including:

```text
git reset --hard
git checkout -- .
git clean -fd
```

Do not auto-commit unless the user explicitly authorizes a commit.
Do not reopen Visio routing work. Do not modify frozen Domain/Requirements/Visio baselines unless a current software contract proves it necessary.

## 1. What independent GPT review found

The uploaded overnight checkpoint independently replays at:

```text
149 passed
1 skipped
```

However, the five post-Goal adversarial tests fail against that original checkpoint. The failures are semantic, not cosmetic:

1. `F3_OPPORTUNITY_WINDOW` uses the superseded Activity slot time instead of the effective Event time.
2. After `Accept Replan`, an active C4 Commitment can keep an `activity_id` from the superseded PlanVersion.
3. The persisted-plan authoritative gate cannot receive an injected frozen `MobilitySnapshot` because `validate_plan_feasibility()` hardcodes `MockMobilityProvider`.
4. Open-Meteo's adapter cannot safely parse the real Unix timestamp form and uses unsafe timezone semantics.
5. `TRAFFIC_DELAY` ignores canonical `extra_minutes`, so an explicit `25` can collapse to default `15`.

The current frontend is also not a backend-connected Golden Scenario. It uses hardcoded journey facts and `localStorage` to persist accepted UI state. Existing Playwright therefore proves a UI smoke path, not end-to-end domain integration.

## 2. What this bundle already prepared

`patches/POST_GOAL_5_DEFECTS_AND_GOLDEN_GATE_20260910.patch` contains:

- fixes for all five defects above;
- `backend/tests/test_post_goal_five_defects.py`;
- `backend/tests/test_backend_connected_golden_contract.py`.

The patch was validated on a fresh copy of the uploaded overnight checkpoint:

```text
git apply --check = PASS
focused post-Goal tests = 6 passed
full backend suite = 155 passed, 1 skipped
python -m compileall -q app tests = PASS
```

The six focused tests mean five defect-specific tests plus one backend-connected Golden Scenario contract test.

Important: these results prove the patch against the uploaded review copy. They do **not** prove the user's current Windows worktree is identical.

## 3. First execution gate in the real Windows repo

### Step A. Detect whether the real tree already contains the fixes

Copy only these two files from `reference_overlay/backend/tests/` into the real repo's `backend/tests/` if they do not already exist, or semantically merge them if equivalent tests already exist:

```text
test_post_goal_five_defects.py
test_backend_connected_golden_contract.py
```

Then from `D:\moodle\CityNexus\backend` run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_post_goal_five_defects.py tests\test_backend_connected_golden_contract.py
```

Decision:

- If `6 passed`: the real tree already satisfies the repair gate. **Do not apply the implementation patch.** Continue to Step C.
- If only some tests fail: inspect the current implementation and semantically merge only the missing behavior. Do not overwrite newer work.
- If all relevant tests fail and current code matches the checkpoint closely: run patch preflight from repo root.

### Step B. Patch preflight and semantic merge

From `D:\moodle\CityNexus`:

```powershell
git apply --check <PATH_TO_BUNDLE>\patches\POST_GOAL_5_DEFECTS_AND_GOLDEN_GATE_20260910.patch
```

If preflight passes cleanly, apply it:

```powershell
git apply <PATH_TO_BUNDLE>\patches\POST_GOAL_5_DEFECTS_AND_GOLDEN_GATE_20260910.patch
```

If preflight does not pass, **do not force it**. Use the patch and `reference_overlay/backend/app/` as semantic reference and edit only the five affected behaviors in the current files.

### Step C. Required backend regression gate

From `backend\`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_post_goal_five_defects.py tests\test_backend_connected_golden_contract.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app tests
.\.venv\Scripts\ruff.exe check app tests
.\.venv\Scripts\ruff.exe format --check app tests
```

Use the repository's existing OpenAPI exact-match validation and require formal/runtime `38/38` unless the current repo intentionally added or removed an API operation. If operation count changed, review the actual contract diff instead of forcing the historical number.

Do not report the post-Goal repair gate as complete unless the five specific tests pass, even if total pytest count is green.

## 4. Backend Golden Scenario gate

The new backend contract test deliberately proves this sequence through real FastAPI endpoints and persisted domain state:

```text
reset demo
→ generate plan
→ select plan
→ create River Cruise booking
→ CAPTURE payment
→ durable C4 Commitment
→ start Journey
→ inject Tech Art Center closure at 13:25
→ generate multiple ReplanProposals
→ verify F3 uses Event time
→ verify hard constraints + C4 preservation
→ accept proposal
→ old PlanVersion SUPERSEDED
→ new PlanVersion ACTIVE
→ remap durable C4 activity_id into new active plan
→ reload JourneyTwin
→ verify Twin still references the active-plan C4 Activity
```

This is the first real vertical-slice proof. Keep it green while doing frontend work.

## 5. Next engineering task: make the frontend real

Do not add another dozen screens. Replace fake state with API-backed state.

The current `frontend/src/main.tsx` must stop treating these as domain truth:

```text
hardcoded current/next activity
hardcoded budget/slack
hardcoded C4 list
hardcoded replan score/diff
localStorage accepted-plan state
```

`localStorage` may store UI-only preferences or a recoverable `journey_id`, but it must not be the authority for accepted PlanVersion, Commitment, feasibility, Event, or Replan state.

Use the semantic scaffolds under `future_scaffold/frontend/` as starting material, not as blindly verified production code:

```text
src/api/citynexus.ts
src/demo/goldenScenario.ts
src/state/journeyModeMachine.ts
e2e/backend-golden.spec.ts
vite.proxy.fragment.ts
playwright.multi-server.fragment.ts
```

These files were prepared against the uploaded API contracts. Their npm build was not independently completed in GPT's sandbox because dependency installation timed out. Codex must compile and adapt them in the actual frontend.

## 6. Frontend integration target

The UI should render from backend responses in this order:

```text
JourneyTwin
ReplanProposal.diff
ReplanProposal.score_breakdown
FeasibilityEnvelope
provider degradation/provenance
active PlanVersion / Activity data
```

Recommended orchestration:

```text
XState = UI workflow authority only
Backend = domain authority
```

Suggested UI workflow:

```text
idle
→ bootstrapping
→ ready
→ generatingReplan
→ comparing
→ accepting / rejecting
→ ready
→ error/retry
```

MapLibre/Turf remain presentation helpers. They must not decide feasibility.

## 7. Backend-connected Playwright acceptance gate

The next Playwright test is not allowed to pass solely because the browser remembers `localStorage`.

It must start/point to a real local FastAPI backend and prove at minimum:

```text
1. browser bootstraps a real demo Journey through API
2. UI displays current JourneyTwin facts returned by backend
3. UI injects/records closure Event through backend
4. UI loads multiple backend-generated ReplanProposals
5. UI shows protected River Cruise C4 and verified deltas/evidence
6. UI accepts a proposal through backend
7. page reloads
8. browser GETs JourneyTwin again
9. recovered ACTIVE plan and C4 state still come from persisted backend state
```

Do not hardcode expected numeric score `0.84` as proof of truth. Assert semantic evidence and backend-returned values.

## 8. Only after the real frontend Golden Scenario passes

Then move to the optional provider/solver/AI queue, in this order:

```text
A. wire one sourced/frozen MobilitySnapshot into the authoritative gate call path
B. bounded Valhalla runtime smoke / fallback proof
C. bounded Open-Meteo runtime smoke / provider recovery proof
D. OR-Tools real candidate generation, still followed by authoritative feasibility
E. LiteLLM/DeepSeek explanation over verified facts, deterministic fallback retained
```

Do not make any live provider mandatory for the course demo.

## 9. Stop conditions

Stop and produce a review checkpoint when all of these are true:

```text
Post-Goal five defects: PASS
Backend Golden Scenario contract: PASS
Full backend regression: PASS
compileall: PASS
Ruff: PASS
OpenAPI contract: PASS
Frontend build: PASS
Backend-connected Playwright Golden Scenario: PASS
No localStorage domain truth
No destructive Git operation
No mandatory live network dependency
```

At that point report exact evidence and changed files. Do not jump to Visio polish or broad new feature work in the same run.
