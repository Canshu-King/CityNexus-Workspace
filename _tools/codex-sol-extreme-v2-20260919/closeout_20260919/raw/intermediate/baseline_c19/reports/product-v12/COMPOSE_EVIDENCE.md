# Authoritative Multi-Day Compose Evidence

The V12 planner is bounded CP-SAT composition, not sequential `place_ids` display ordering.

## Scenario

- six arbitrary POIs;
- three days and two nights;
- one Stay candidate with check-in/check-out evidence;
- arrival and departure anchors;
- one imported protected C4 reservation;
- multiple mobility modes and a complete captured mode matrix;
- Top-K complete PlanVersions.

The planner chooses day assignment, order, start/end times, and leg mode within bounded candidate sets. The deterministic gate verifies budget, opening-hours facts, anchor slack, locked commitments, and evidence identity after materialization.

## Evidence

The V12 focused test asserts three complete candidates and twelve activities in the minimum scenario, with at least 100 captured mode facts. The full backend suite also covers solver provenance, candidate persistence, C4 semantic anchors, opening windows, budget, and fallback behavior.

## Result

`AUTHORITATIVE_MULTIDAY_COMPOSE` is PASS. Candidate truth is stored, selected evidence is durable, and Trip Studio accepts from the same evidence rather than silently starting a second provider capture.
