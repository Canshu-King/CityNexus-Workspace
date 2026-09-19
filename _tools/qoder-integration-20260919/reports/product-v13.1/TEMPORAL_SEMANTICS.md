# V13.1 Canonical Temporal Semantics

## One source of truth

`backend/app/core/temporal.py::derive_journey_temporal_shape` returns an
immutable `JourneyTemporalShape(day_count, night_count)` from the local
calendar dates of the authoritative arrival and departure anchors. It rejects
non-positive windows and preserves the existing one-to-seven-day bounds.

| Arrival → departure | Days | Nights |
| --- | ---: | ---: |
| Oct 1 → Oct 1 | 1 | 0 |
| Oct 1 → Oct 2 | 2 | 1 |
| Oct 1 → Oct 3 | 3 | 2 |
| Oct 1 → Oct 4 | 4 | 3 |

## Consumers aligned

- authoritative compose day/night counts and PlanVersion score/explanation
  metadata;
- accommodation provider `nights`, total price, check-out offset, and
  same-day no-stay behavior;
- authoritative overnight structural Activity count;
- legacy stay-mobility overnight node generation;
- date-grouped Journey UI payloads, which now receive the same canonical
  overnight/date structure without a second count calculation.

The V12 flagship test now uses Oct 1 → Oct 3 for its intended 3-day/2-night
scenario. Oct 1 → Oct 4 is tested as 4 days/3 nights.

## Evidence

The V13.1 focused suite passed `37 passed, 2 warnings` in the current
worktree. Its temporal cases assert PlanVersion explanation counts,
accommodation total = nightly rate × canonical nights, no same-day offer, and
the authoritative overnight Activity count.
