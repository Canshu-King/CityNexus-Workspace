# CityNexus MVP WP00-WP03 checkpoint review package

Date: 2026-09-09  
Contract: `CityNexus_MVP_Implementation_Blueprint_v0.1.zip`

This package records the completed WP00 baseline reconciliation and the only
implementation scope authorized for this checkpoint: WP01 backend/database,
WP02 traveler/journey/preferences/constraints, and WP03 discovery/initial
planning. Visio, frontend vertical-slice, booking/payment, execution, event
replanning, and AI work remain deferred to their later work packages.

## Gate result

`backend/tests`: 33 passed; Ruff check: PASS; Ruff format check: PASS; package
blueprint validator: PASS. The four frozen source hashes and copied OpenAPI/SQL
hash equality checks are recorded in `implementation/docs/checkpoints/`.

Run locally from the implementation root with Python 3.12+:

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe -m pytest -q backend/tests
.venv/Scripts/python.exe scripts/reset_demo.py
```

The API is available with `uvicorn app.main:app --app-dir backend` and has no
runtime network dependency; all CityNexus data used here is fixture-backed.
