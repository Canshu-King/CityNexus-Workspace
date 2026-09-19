# Differential projection oracle

The oracle generated five persisted cursor fixtures and compared authoritative database state with actual Journey experience, Twin, refreshed offline snapshot and execution-clock projections.

| Cursor case | Expected | Result |
|---|---|---|
| absent | pre-execution fallback to first pending | agree |
| first | first is Now, second is Next | agree |
| middle | middle is Now, following is Next | agree |
| final | final is Now, no fabricated Next/leg | agree |
| present but foreign/stale | no Now/Next; explicit stale state | agree |

Result: **5 cases, 0 divergences** in `replay_cases/projection_oracle.json`.

The focused browser gate independently verifies Live UI for the same four visible cases: **4/4 passed**. This specifically kills fixed-index and stale-fallback mutants.
