# CityNexus V13.1 Final Report

## Executive result

V13.1 is a release-integrity correction, not a V14 feature expansion. It
fixes the fresh-extract commerce fixture path and establishes canonical
calendar day/night semantics across authoritative planning and stay pricing,
while preserving the V13 authoritative integrity and commitment-centric
recovery contracts.

## Reproduced and fixed

1. **Fresh-extract data-root defect** — WP04 runtime/tests resolved the catalog
   below `backend/data` while the curated archive stored it below `data`; fixed
   both consumers to the repository-level canonical root.
2. **Temporal contradiction** — planner returned 3 days/2 nights while stay
   pricing charged 3 nights for Oct 1 → Oct 4; fixed both to the shared
   calendar shape (4 days/3 nights), and moved the intended 3-day flagship to
   Oct 3 departure.

## Classification policy

- **PROVEN FROM FRESH EXTRACT**: only final ZIP runtime/build/test evidence.
- **PROVEN ONLY IN MAIN WORKTREE**: useful regression evidence before final
  packaging; never used alone as the release gate.
- **PARTIAL**: a bounded local result without the full requested external
  surface.
- **EXTERNAL / NOT CONFIGURED**: DeepSeek, Hermes, Phoenix, and live provider
  services not configured in this process.

## Release artifact

Target archive:
`D:\moodle\CityNexus\CityNexus-V13.1-Release-Integrity-Temporal-Semantics-20260913.zip`

The archive itself passed the fresh-extract runtime gate in
`FRESH_EXTRACT_RUNTIME_GATE.md`: focused backend `73 passed`, full backend
`369 passed, 2 skipped`, fresh production build passed, and fresh Playwright
`16 passed`. The final package contains all six V13.1 reports plus the
preserved V13 evidence set, with no secrets, databases, caches, build outputs,
or nested archives.

## Final classification

- **PROVEN FROM FRESH EXTRACT**: canonical data root, WP04 runtime/tests,
  temporal semantics, full backend regression, production frontend build, and
  full Playwright matrix.
- **PROVEN ONLY IN MAIN WORKTREE**: the pre-package V13.1 focused and frontend
  reruns listed in `FINAL_REGRESSION.md`; they were corroboration, not the
  release gate.
- **PARTIAL**: live external-provider/model integrations remain outside this
  local release-integrity task.
- **EXTERNAL / NOT CONFIGURED**: DeepSeek, Hermes, Phoenix, and live provider
  credentials were not present in the process.
