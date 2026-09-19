# Fresh Extraction Replay

The archive is intended to be self-contained for deterministic backend review.
The backend payload includes the exact paths consumed by the current source:

```text
backend/db/schema.sql
backend/data/mock/wp04_commerce_catalog.json
backend/data/mock/wp04_city_services_overlay.json
```

The root `data/mock` mirror is included for callers that resolve fixtures from
the repository root. The generated `backend/citynexus.db` is excluded; tests
create and reset their deterministic state.

Replay procedure:

1. Create a new empty extraction directory.
2. Extract this checkpoint ZIP there.
3. From the extracted `backend` directory, run:

```text
..\.venv\Scripts\python.exe -m pytest -q
```

The replay was run against a fresh extraction using the workspace's installed
Python dependencies:

```text
D:\moodle\CityNexus\_fresh_vertical_slice_hardening_replay_archive_20260910\backend
157 passed, 1 skipped, 2 warnings in 20.66s
```

The skipped test is the opt-in live Valhalla smoke test. The fresh extraction
created its own SQLite database during the run; no generated database was
present in the archive.
