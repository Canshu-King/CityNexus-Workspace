# V15 Test Results

## Focused baseline

Command:

```text
uv run pytest -q tests/test_wp07_foundation_assist.py tests/test_agent_mission_runtime.py
```

Result: `9 passed`.

## V15 focused suite

Command:

```text
uv run pytest -q tests/test_v15_copilot.py
```

Result: `6 passed` before the final hardening, then `12 passed` for the final
focused set:

```text
python -m pytest -q tests/test_v15_copilot.py tests/test_v10_foundations.py
```

The final focused result was `12 passed`.

Coverage includes the intent matrix, hypothetical-vs-current routing, read-only What-If simulation, no Twin/Event mutation, explicit disruption Event creation, and honest fallback labeling.

## V14 convergence reference

Command:

```text
uv run pytest -q tests/test_v15_copilot.py tests/test_v14_grounded_adaptive_recovery.py
```

Result: `7 passed`.

## Broad backend regression

Command:

```text
uv run pytest -q
```

Result: `400 passed, 2 skipped, 2 warnings` in 39.62 seconds.

## Frontend and browser

- `npm run build`: passed; Vite generated the production PWA bundle and reported only the existing >500 kB chunk warning.
- Playwright: generic-city, sealed-plan What-If, Xiapu disruption, Beijing
  high-budget creation, Chinese late-start replan, and no-authoritative-plan
  guidance were exercised. The final Tianjin What-If card showed before/after
  metrics and `SIMULATION ONLY`; the final Beijing screen explained the need to
  select an authoritative PlanVersion.
- Screenshots: `output/playwright/v15-fuzhou-copilot.png`,
  `output/playwright/v15-tianjin-copilot-what-if.png`, and
  `output/playwright/v15-real-user-no-plan-guidance.png`.

## Fresh-extract release gate

The first minimal staging attempt exposed a missing runtime fixture (`data/mock`)
when run outside the worktree. The release was reconciled to include the
required root `data` fixtures, then extracted into a new directory and run
directly from that extracted `backend`:

```text
python -m pytest -q tests/test_v15_copilot.py tests/test_v10_foundations.py
12 passed, 2 warnings
```
