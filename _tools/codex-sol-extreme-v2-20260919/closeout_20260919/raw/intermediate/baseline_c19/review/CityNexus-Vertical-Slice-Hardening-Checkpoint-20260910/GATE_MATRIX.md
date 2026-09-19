# Vertical Slice Hardening Gate Matrix

| Gate | Evidence | Result |
| --- | --- | --- |
| Supplied hardening tests | `backend/tests/test_vertical_slice_hardening_next.py`, 2 passed | PASS |
| Existing Golden + five-defect tests | targeted run, 8 passed | PASS |
| Full backend regression | 157 passed, 1 skipped, 2 upstream warnings | PASS |
| Python compile | `compileall -q app tests` | PASS |
| Ruff lint | `ruff check app tests` | PASS |
| Ruff format | `ruff format --check app tests`, 99 files formatted | PASS |
| OpenAPI parity | formal 38, runtime 38, missing 0, extra 0 | PASS |
| Frontend production build | Vite build | PASS |
| Backend-connected browser gate | `npm run test:e2e`, 1 passed | PASS |
| Fresh extraction replay | schema and backend-relative fixtures included; result recorded in `REPRODUCIBILITY.md` | PASS |
| Default network policy | offline Mock path; live Valhalla smoke remains opt-in | PASS |
| Scope stop | no provider-runtime breadth, OR-Tools, LiteLLM/DeepSeek, or WP05 | PASS |
