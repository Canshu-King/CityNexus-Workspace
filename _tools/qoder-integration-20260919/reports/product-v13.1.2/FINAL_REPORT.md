# CityNexus V13.1.2 Final Report

## Files changed

- `backend/app/operations/v9.py`
- `backend/app/planning/authoritative_v12.py`
- `backend/tests/test_v13_1_2_structural_anchor_integrity.py`
- `reports/product-v13.1.2/FINAL_REPORT.md`

## Results

- Focused V13.1.2, V13.1.1, V13, V12, and V9 regression: **37 passed, 2
  warnings**.
- Broad backend regression: **377 passed, 2 skipped, 2 warnings**.
- Final ZIP fresh-extract targeted gate: **PASS**, with the same 37-test suite
  executed from the extracted package without hand repair.

## Proven semantics

- ARRIVAL and DEPARTURE reservations are structural by durable
  `anchor_role`/`semantic_node_key`, not by a V9 planner-local `semantic_key`.
  Authoritative compose accepts them without requiring the V9 key in `place_ids`,
  refreshes the concrete V12 structural Place key, and plan selection binds the
  Commitment to that selected structural Activity.
- MID_TRIP without a non-structural semantic target is rejected before durable
  Booking/Commitment creation.
- Unknown anchor roles are rejected before durable state creation.
- Previous V13.1.1 departure-time/origin and truthful solver-provenance fixes are
  preserved.

## Release artifact

`D:\moodle\CityNexus\CityNexus-V13.1.2-Structural-Reservation-Identity-20260913.zip`

The curated archive excludes caches, `.pyc` files, databases, virtual
environments, node_modules, build outputs, and nested historical ZIPs.
