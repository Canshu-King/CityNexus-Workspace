# CityNexus Weather Runtime Hardening Checkpoint

Date: 2026-09-10

Weather Runtime Hardening local gate: **PASS**.

External freeze status: **PENDING REVIEW**.

The six adversarial defects WRH-01 through WRH-06 are fixed in the real repository. The runtime now rejects malformed Open-Meteo hourly arrays, records provider capture time separately from forecast validity, makes a future forecast actionable at capture time, clears an active weather event only from successful exact-scope bucket coverage, refreshes evidence on a stable Event identity, and gives Replan the latest provider capture time as its decision clock.

The server-owned trigger remains `POST /api/v1/journeys/{journey_id}/weather/refresh`. It accepts no trusted weather facts from the client. GET/Twin, feasibility evaluation, Replan candidate gating, and read/projection endpoints do not call Open-Meteo.

Weather attribution remains deterministic and owns `affected_activity_id`. Provider output, AI, and the solver do not choose it. Durable C4 Commitments remain reality authority and cannot be silently destroyed by Replan.

No scheduler, background worker, database redesign, generic event-sourcing rewrite, or OR-Tools mutation was added.
