# V13.1 Cross-Validation Reproduction

## Scope and source of truth

- Authoritative repository: `D:\moodle\CityNexus`
- Starting HEAD: `7d22cd0eb7840121ba42a5ba363e1a4c7ca1a7e7`
- Existing dirty worktree changes were preserved. No reset, clean, rebase,
  commit, or push was performed.
- The Road-Prep candidate patch was read as review evidence and was not applied
  with `git apply`.

## Finding A — fresh-extract data-root defect

The prior V13 release ZIP was extracted to
`D:\moodle\_v131_repro_v13_20260913`. Its layout had
`data/mock/wp04_commerce_catalog.json` but no `backend/data/mock` copy:

`V13_REPRO_LAYOUT root_data=True backend_data=False`

Running the WP04 tests from that fresh extraction failed during collection:

`FileNotFoundError: ...\\backend\\data\\mock\\wp04_commerce_catalog.json`

The independent runtime probe of `app.commerce.service_impl.load_catalog()`
failed with the same missing `backend/data` path. The original worktree had an
untracked duplicate under `backend/data`, which explains why the Windows
worktree regression could appear green while the curated archive was not
runnable.

## Finding B — contradictory temporal semantics

Against the unmodified current worktree, the independent probe for
`2026-10-01T08:00:00+00:00` through `2026-10-04T22:00:00+00:00` returned:

`TEMPORAL_CONTRADICTION planner_days= 3 planner_nights= 2 stay_priced_nights= 3`

The planner treated the departure date as a terminal anchor, while stay
pricing counted the crossed calendar dates. This was a real business-semantic
contradiction, not a test-only mismatch.

## Reconciliation

The final implementation uses the repository-level `data/` tree for both
commerce consumers. It adds `backend/app/core/temporal.py` with the shared
`JourneyTemporalShape` derivation and routes authoritative composition and
stay pricing through it. Same-day Journeys now produce no accommodation
offers. The focused regression also checks accommodation totals and
authoritative overnight Activity count against the same expected night count.

The V12 flagship test now uses Oct 1 → Oct 3 for its intended 3-day/2-night
scenario, rather than redefining the canonical calendar semantics.

## Result

Both supplied findings were independently reproduced and fixed without
weakening the V13 authoritative execution, frozen-evidence, Trip Studio,
commitment, Guardian, or offline contracts.
