# Semantic Merge Record

The hardening package was read as the implementation contract. Its supplied
tests were copied first and run against the current tree. The backend and
frontend patch intent was then merged into the existing implementation so the
current provider, evidence, scoring, and JourneyTwin code remained intact.

Backend changes are limited to the replan boundary and its Golden Scenario:

- Parse the Event occurrence timestamp and project it into
  `ZoneInfo(journey.timezone)`, with the Journey start timestamp as a safe
  timezone fallback when a development timezone name is unavailable.
- Select the source activity by `journey.current_activity_id`; retain the
  previous sequence activity only when that pointer cannot be resolved.
- Carry the selected activity's stable semantic key into F3 evidence as
  `origin_key`.
- Complete the Golden Scenario prefix until Tech Art is the current activity
  before injecting the 13:25 closure.

Frontend changes reuse the existing API and XState flow:

- `completeActivity` is called for the Golden Scenario prefix.
- CAPTURE, replan generation, and replan acceptance keys are scoped to the
  booking, Event, and proposal respectively.
- `amount_minor` is converted using the currency's Intl fraction scale before
  display.
- Closure refresh passes the closure occurrence timestamp to `/twin`.
- Playwright checks the authoritative current activity, budget, F3 evidence,
  and local-time window.

The package's reproducibility finding was addressed by carrying
`backend/db/schema.sql` and the backend-relative WP04 fixtures into the
checkpoint. Root `data/mock` is also retained because existing callers resolve
the shared fixture set from both repository-relative locations.
