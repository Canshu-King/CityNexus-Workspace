# WP03 correctness repair checkpoint

Status: PASS  
Date: 2026-09-09  
Instruction applied: `CityNexus_CODEX_WP03_Repair_Instruction_20260909.md`

## Scope

Only the requested WP03 repair was applied. WP04, WP05, WP06, AI, frontend,
Visio and real network providers remain deferred.

## P0 repairs

- `app.replanning.feasibility.evaluate_feasibility` is the authoritative,
  side-effect-free deterministic gate. It calls the package reference
  invariants and additionally enforces active HARD constraints, budget,
  `JOURNEY_END_BY`, journey boundaries, non-overlap, catalog open intervals,
  service availability and mock mobility gaps.
- Generation runs the gate before scoring or persisting a candidate.
- Selection reloads the Journey, active constraints, current mock catalog and
  mobility context, then reruns the same gate. An infeasible stale candidate
  returns 422 and leaves Journey and PlanVersion state unchanged.
- Initial lifecycle now follows `CANDIDATE -> SELECTED` and `DRAFT -> PLANNED`.
  WP05's later `SELECTED -> ACTIVE` transition remains untouched.
- Duplicate preference keys in one PUT request return deterministic 422 rather
  than a database integrity error.

## P1 repairs

- ORM metadata now declares the Journey cross-table FKs, PlanVersion parent FK,
  and the SQL unique constraints for preferences, places, city services,
  plan versions and activities.
- Journey updates, preference replacement, constraint deletion and plan
  selection write audit records with before/after evidence where applicable.
- `JourneyCreate.planning_mode` is persisted and becomes the default for a
  later generate request; the Journey response exposes the selected mode.

## Regression evidence

The expanded suite covers complete schema/index creation, stricter budget and
end-time constraints, closed places, insufficient mobility gaps, independent
candidate gate checks, stale selection rejection without mutation, selected-plan
state consistency, duplicate preference validation, ORM metadata alignment and
mutation audit records.

Gate command from the repository root:

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe -m pytest -q backend/tests
.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend scripts
.venv/Scripts/ruff.exe format --check --config backend/pyproject.toml backend scripts
```

Result: 41 tests passed; Ruff check and format checks passed. The canonical
mock demo still produces three feasible candidates, and canonical selection
leaves the Journey `PLANNED` with the selected PlanVersion reference.
