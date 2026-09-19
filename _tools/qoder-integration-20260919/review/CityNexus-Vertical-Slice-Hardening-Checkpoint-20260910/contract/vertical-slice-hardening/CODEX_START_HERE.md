# Codex Start Here - CityNexus Vertical Slice Hardening

You are continuing the real Windows repository at:

```text
D:\moodle\CityNexus
```

The supplied checkpoint was independently reviewed. Do not restart architecture work and do not blindly replace files.

## Absolute safety rules

Before editing:

```powershell
git status --short
git diff --stat
```

Do not run:

```text
git reset --hard
git checkout -- .
git clean -fd
```

Do not auto-commit unless the user explicitly asks.

Do not edit frozen Domain, Requirements, or Visio baselines in this task.

## Stage 1 - test first, against the REAL current tree

Copy only:

```text
tests/test_vertical_slice_hardening_next.py
```

to:

```text
backend/tests/test_vertical_slice_hardening_next.py
```

Then run:

```powershell
cd D:\moodle\CityNexus\backend
..\.venv\Scripts\python.exe -m pytest -q tests\test_vertical_slice_hardening_next.py
```

Expected against the uploaded checkpoint: **2 failures**.

If the real worktree already gives `2 passed`, do NOT blindly apply the backend implementation patch. Inspect whether equivalent semantics already exist and keep the newer implementation.

## Stage 2 - semantic merge only the missing backend behavior

Required semantics:

1. Project every effective Event instant onto the Journey schedule timezone before local schedule/opening-hour/OpportunityWindow interpretation.
2. F3 recovery origin = authoritative current execution Activity when available; previous-slot origin is only a fallback.
3. Store `origin_key` in F3 Opportunity Window evidence.
4. Strengthen Golden Scenario so the Journey actually progresses to Tech Art before the 13:25 closure.

Reference patch:

```text
patches/02_BACKEND_SEMANTIC_HARDENING.patch
```

Use it as a semantic reference. Apply automatically only if `git apply --check` succeeds against the current tree and there is no newer conflicting implementation.

Run:

```powershell
..\.venv\Scripts\python.exe -m pytest -q `
  tests\test_vertical_slice_hardening_next.py `
  tests\test_backend_connected_golden_contract.py `
  tests\test_post_goal_five_defects.py

..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m compileall -q app tests
..\.venv\Scripts\ruff.exe check app tests
..\.venv\Scripts\ruff.exe format --check app tests
```

Minimum expected backend result after merge, if the real tree still matches this review checkpoint closely:

```text
157 passed, 1 skipped
```

A different higher count is acceptable if all named tests and full suite are green.

## Stage 3 - frontend hardening

Semantically merge the changes in:

```text
patches/03_FRONTEND_VERTICAL_SLICE_HARDENING.patch
```

Required behaviors:

- Add API call to complete an Activity.
- Golden bootstrap advances execution to Tech Art before injecting the closure.
- CAPTURE idempotency key is booking-scoped.
- Replan generation idempotency key is Event-scoped.
- Accept idempotency key is proposal-scoped.
- `amount_minor` is converted to major currency units before display.
- Closure refresh passes `closureOccurredAt` to JourneyTwin.
- Playwright verifies current Activity = Tech Art and verifies F3 `origin_key` and 13:25 local window.

Then run on Windows:

```powershell
cd D:\moodle\CityNexus\frontend
npm run build
npm run test:e2e
```

Do not call the frontend gate PASS from static inspection alone.

## Stage 4 - review package reproducibility repair

The uploaded checkpoint did not replay standalone because expected backend fixture/schema paths were omitted.

The next review package must allow this from a fresh extraction:

```powershell
cd <fresh-extract>\backend
<python> -m pytest -q
```

with no dependency on an older ZIP being present.

At minimum include whatever the current tree actually needs under repository-relative paths, including:

```text
backend/db/schema.sql
backend/data/mock/...  (if current code/tests resolve fixtures there)
```

Do not “fix” this by copying random stale generated DBs into the archive. Package authoritative source fixtures/schema or adjust path ownership coherently.

## Stop Gate

After all of these are green:

```text
new 2-test hardening gate          PASS
old 5-defect gate                  PASS
strengthened backend Golden        PASS
full backend                       PASS
compileall                         PASS
Ruff                               PASS
OpenAPI parity                     PASS
frontend build                     PASS
backend-connected Playwright       PASS
fresh-extract reproducibility      PASS
```

STOP and create the next checkpoint for GPT review.

Do not start OR-Tools, LiteLLM/DeepSeek, broad live Valhalla work, new UI feature sprawl, PPT, or Visio in the same run.

The next provider contract is already prepared in `contracts/NEXT_PROVIDER_GATE.md` so no architecture rediscovery is necessary after this gate freezes.
