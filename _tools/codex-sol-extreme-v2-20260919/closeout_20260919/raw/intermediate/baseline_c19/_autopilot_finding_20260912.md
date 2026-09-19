# Finding: Guardian model-path records the wrong `proposal_id` in mutation evidence

Date: 2026-09-12
Reproduced on: `D:\moodle\CityNexus` @ `backend/`, isolated DB `backend/_autopilot_iso.db`, port 8001
Repro scripts: `_autopilot_flow.py` (real model), `_demo_flow.py` (manual replan path)
Severity: audit-traceability defect on the autonomous mutation path. No incorrect domain
mutation was applied — the plan change itself was correct.

## Summary

When the Guardian recovers through the **configured Agent runtime** (the model path,
`evidence.inference.controller == "configured_agent_runtime"`), the persisted
`GuardianRun.proposal_id` and `evidence.mutation.proposal_id` are taken from the
**`request_replan`** step instead of the **`accept_replan`** step.

Result: the audit record names a proposal that was later INVALIDATED and never applied,
while the model actually accepted a different proposal. The model's own
`reasoning_summary` names the correct proposal, so the structured evidence and the
narrative disagree.

## Reproduction

Clean `demo/reset`, `CITYNEXUS_AI_ENABLED=true` + real DeepSeek credential,
`CITYNEXUS_SOLVER=v2`. Mission command:

> 游船和晚餐别动，优先室内、少走路，最多多花五十元，允许自动调整。

Provider fixture flipped to `DISRUPTED` (`heavy-rain-and-delay`). The autopilot recovered
with no manual scan and no new prompt: `action_status=EXECUTED`, `trigger_kind=REACTIVE`,
`solver.kind=ORTOOLS_CP_SAT_V2`, `policy.decision=ALLOW_AUTO`.

Model-chosen tool order (8 steps, differs from the 3 steps the existing test asserts):

```
inspect_journey -> inspect_twin -> list_replans -> search_city_services(q="indoor")
-> request_replan -> list_replans -> accept_replan -> inspect_twin
```

Proposals generated in that run:

| proposal | status | score | removed | added | cost_delta |
|---|---|---|---|---|---|
| `911fc84d` | INVALIDATED | 0.71016 | skyline-dinner, tech-art | city-park x2 | -15000 |
| `170e32cd` | INVALIDATED | 0.70792 | skyline-dinner, tech-art | city-park, design-library | -13000 |
| `12c7e886` | INVALIDATED | 0.70792 | skyline-dinner, tech-art | city-park, design-library | -13000 |
| `8981a2b7` | INVALIDATED | 0.67148 | tech-art | city-park | -5000 |
| `12113e6b` | **ACCEPTED** | 0.66924 | tech-art | design-library | -3000 |

The model correctly rejected the three highest-scoring proposals because they removed the
protected `place-skyline-dinner`, and rejected `8981a2b7` because it added an outdoor
`place-city-park` against the "优先室内" instruction.

Persisted evidence, however:

```
guardian_runs.proposal_id                                  = 911fc84d-3ca5-4980-b54d-5720ae84f447   <-- INVALIDATED
evidence.mutation = {executed: true, proposal_id: 911fc84d-...}                                    <-- INVALIDATED
agent_run_steps[5] request_replan  -> result.proposal.id   = 911fc84d-3ca5-4980-b54d-5720ae84f447
agent_run_steps[7] accept_replan   -> arguments.proposal_id = 12113e6b-0199-49b4-994b-2921487169ea  <-- actually applied
agent_run_steps[7] accept_replan   -> result.decision      = ALLOW_AUTO, executed: true
```

`evidence.solver.objective.cost_delta_minor` is likewise `-15000` (the rejected proposal)
while the accepted proposal's delta is `-3000`. The active plan after recovery does
contain `place-design-library`, confirming `12113e6b` is what was actually applied.

## Root cause

`backend/app/agent/guardian.py`, model path (`_model_recovery`), around lines 220-247:

```python
request_step = next((s for s in reversed(tool_steps) if s.get("tool_name") == "request_replan"), None)
accept_step  = next((s for s in reversed(tool_steps) if s.get("tool_name") == "accept_replan"), None)
request_result = request_step.get("result") if request_step else {}
proposal_payload = request_result.get("proposal") if isinstance(request_result, dict) else None
if isinstance(proposal_payload, dict) and proposal_payload.get("id"):
    run.proposal_id = str(proposal_payload["id"])          # <-- taken from REQUEST
    ...
if accept_step is not None and isinstance(accept_step.get("result"), dict):
    accepted = accept_step["result"]
    ...
    evidence["mutation"] = {
        "executed": bool(accepted.get("executed")),
        "proposal_id": run.proposal_id,                    # <-- reuses the REQUEST id
    }
```

The `accept_replan` step's own `arguments.proposal_id` is never read. `tool_steps` entries
do carry `arguments` (`app/agent/runtime.py` lines 234 and 410), so the correct value is
available at that point.

## Why the existing gates missed it

`backend/tests/test_v5_autopilot.py` asserts
`agent_runtime.provider_key == "citynexus-guardian"`, i.e. it exercises only the
deterministic fallback path, where `_deterministic_recovery` sets `mutation.proposal_id`
from the proposal it actually accepts and is therefore self-consistent. No test asserted
`mutation.proposal_id == accept_replan.arguments.proposal_id` on the model path, and the
model path requires a live credential so it is not part of the offline suite.

## Fix (APPLIED 2026-09-12 02:44, verified)

Changed `backend/app/agent/guardian.py` in `_model_recovery` only. The recorded
proposal id is now resolved from the **accept** step's own argument, falling back
to the request step's result when the model never accepted anything. Solver
evidence is loaded once from whichever proposal id won.

```python
    request_result = request_step.get("result") if request_step else {}
    proposal_payload = request_result.get("proposal") if isinstance(request_result, dict) else None
    if isinstance(proposal_payload, dict) and proposal_payload.get("id"):
        run.proposal_id = str(proposal_payload["id"])
    accept_arguments = accept_step.get("arguments") if accept_step else None
    if isinstance(accept_arguments, dict) and accept_arguments.get("proposal_id"):
        # The model may accept a proposal other than the first one it generated,
        # for example when a higher-scoring candidate breaks a protected
        # commitment. The audit record must name the proposal actually applied,
        # so the accept step's own argument wins over the request step's result.
        run.proposal_id = str(accept_arguments["proposal_id"])
    if run.proposal_id is not None:
        proposal = session.get(ReplanProposal, run.proposal_id)
        if proposal is not None:
            diff = json.loads(proposal.diff_json or "{}")
            evidence["solver"] = diff.get("verified_evidence", {}).get("generator")
```

`evidence["mutation"]["proposal_id"]` and the `PROPOSAL_PRESENTED` branch already
read `run.proposal_id`, so they inherit the corrected value without further edits.
The deterministic fallback path (`_deterministic_recovery`) was already correct and
was not touched.

### Verification

- New gate `backend/tests/test_guardian_model_evidence.py` stubs the configured
  Agent runtime, requests proposal A, accepts proposal B, and asserts that
  `GuardianRun.proposal_id`, `evidence.mutation.proposal_id` and `evidence.solver`
  all describe B.
- On the unfixed code the gate fails exactly as expected:
  `AssertionError: GuardianRun.proposal_id must name the accepted proposal, not the
  first generated one`.
- With the fix: gate passes. `test_guardian_model_evidence.py`,
  `test_v5_autopilot.py`, `test_guardian_v4.py`, `test_gpt_v5_mission_authority.py`
  -> **10 passed**.
- `ruff check` and `ruff format --check` pass on both changed files.

### Caveat

`backend/` is not tracked by git, so this change exists only in the working tree
and cannot be recovered with `git checkout`. Re-verify the two `accept_arguments`
lines are still present before packaging, because other agents edit this file
concurrently.

---

# Finding 2 (secondary, NOT fixed): `predictive._future` is a dead filter

Date: 2026-09-12
Reproduced on: isolated DB `backend/_future_check.db`, script `backend/_future_check.py`
Severity: latent correctness issue. **No user-visible defect demonstrated yet.**
Ownership: **unknown.** No older copy of `predictive.py` exists anywhere in the
workspace (not in `backend/`, not in any `*.zip` review package), so this cannot be
attributed to Codex or to earlier work.

## What it does

`backend/app/agent/predictive.py` lines 68-72:

```python
def _future(activity: Activity, journey: Journey) -> bool:
    try:
        return _dt(activity.end_at) >= _dt(journey.start_at)
    except ValueError:
        return True
```

Used once, line 204:

```python
future_activities = [item for item in activities if _future(item, journey)]
```

The comparison is against **`journey.start_at`**, not "now". For a journey that is
already running, every activity in the active plan ends after the journey start, so
the predicate is `True` for all of them. `_future` never filters anything.

## Empirical evidence

`backend/_future_check.py` marks one activity `COMPLETED` through the API, then builds
a resilience snapshot:

```
activity statuses: {... '3a58c470-...': 'COMPLETED', 'abe4e842-...': 'ACTIVE',
                    '61e3096d-...': 'PLANNED', '98af0be5-...': 'PLANNED',
                    '74f10240-...': 'PLANNED', '2cbb2a5d-...': 'PLANNED'}
journey.start_at     : 2026-10-10T09:00:00+08:00
counted as 'future'  : 6 of 6
completed still counted: True
snapshot status      : STABLE
activity_risks count : 6   <-- includes the COMPLETED activity
```

## Impact — bounded, so far

- `activity_risks` carries extra entries for already-completed activities. Each gets
  `risk_score: 0` unless it is outdoor **and** a forecast risk exists, so the
  top-line `risk_score` (28 in the run above) and `status` (`STABLE`) did not change.
- `weather_exposure` / `single_point` only test `any(item["outdoor"] ...)`, so extra
  zero-risk rows cannot move them.
- `target_activity_id` is `max(activity_risks, key=risk_score)`. When every risk is 0,
  `max` returns the **first** row — i.e. the earliest activity, which is the most likely
  to be `COMPLETED`. But `recommendation.action` only becomes `PREEMPTIVE_REPLAN` when
  `forecast_risk >= threshold and risk_event is not None`, and in that branch outdoor
  rows carry `risk >= 70` and win the `max`. So a stale target can only surface while
  the action is `CONTINUE_MONITORING`, where `target_activity_id` is informational.
- Line 264 shows the author was aware and compensated locally:
  `mutable_count = sum(1 for item in future_activities if not item.locked and item.status
  not in {"COMPLETED", "CANCELLED"})`.

## Not yet resolved

Whether a high-risk scenario can push a stale completed activity into the *top-line*
score or into the recommendation. Not tested. The `except ValueError: return True`
branch is also untested; returning `True` on unparseable timestamps is a defensible
"fail open" choice for a risk filter, but it is undocumented.

Suggested direction (do not apply blind — `predictive.py` is being edited concurrently):
rename to reflect the actual semantics, or compare against the snapshot's `_now()`
and exclude `status in {"COMPLETED", "CANCELLED"}`.
