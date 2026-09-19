# Pre-WP04 minimal correctness repair checkpoint

Status: PASS  
Date: 2026-09-09  
Contract: `CityNexus_MVP_Implementation_Blueprint_v0.1.zip`  
Instruction applied: `CityNexus_CODEX_Pre_WP04_Minimal_Repair_20260909.md`

## Scope

This checkpoint contains the WP00-WP03 implementation plus only the requested
P0-1/P0-2 repairs and small P1 traceability fixes. WP04 booking/payment,
WP05 execution, WP06 replanning, frontend, AI, Visio and real providers remain
deferred.

## P0-1 — selected-plan feasibility invariant

- `validate_selected_plan_feasibility` is the single read-only guard shared by
  Journey PATCH and HARD constraint creation.
- For a PLANNED Journey with an active SELECTED PlanVersion, the selected plan
  is evaluated against a proposed Journey/constraint snapshot before ORM
  mutation or commit.
- An infeasible proposed budget, time window or HARD rule returns the existing
  422 error envelope and leaves Journey, PlanVersion and constraints unchanged.
- A preserving title/budget/end-time change succeeds without changing the
  PLANNED/SELECTED lifecycle state.

## P0-2 — locked commitment normalization

- The gate uses stable semantic place/service identity rather than a
  PlanVersion-specific Activity UUID.
- ISO or time-only locked starts are normalized once to minutes relative to
  the Journey start, matching generation and persisted selection.
- Canonical `place-river-cruise` at 15:30 passes generation and selection;
  changed time, removed activity and same-time different-place candidates
  fail deterministically.

## P1 incidental fixes

- Candidate generation iterates the raw deterministic template universe,
  gates each candidate, and collects up to the requested count. The later
  feasible 32,000-minor-unit template is returned for a 33,000 budget with
  `candidate_count=1`.
- Generation writes one `plans.generated` audit record per successful batch.
- Requirement ledger evidence records FR-006 as PARTIAL (authentication is
  deferred) and FR-018 as SIMULATED (mock provider only).

## Gate result

- Backend tests: **52 passed**.
- Ruff check: **PASS**.
- Ruff format check: **PASS**.
- Canonical reset and generation: three feasible candidates.
- Canonical selection: Journey `PLANNED`, selected PlanVersion `SELECTED`.
- Locked canonical cruise: preserved by the same feasibility layer during
  generation and persisted selection revalidation.
- No runtime provider is required.

## Reproduce

From the package root with Python 3.12+ and dependencies in
`backend/pyproject.toml`:

```powershell
$env:PYTHONPATH='backend'
python -m pytest -q backend/tests
ruff check backend scripts
ruff format --check backend scripts
```

The authoritative gate is `backend/app/replanning/feasibility.py`; it runs
before candidate persistence and immediately before selection.
