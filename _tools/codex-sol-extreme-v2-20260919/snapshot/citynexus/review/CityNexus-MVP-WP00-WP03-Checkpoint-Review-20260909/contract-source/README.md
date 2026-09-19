# CityNexus MVP Implementation Blueprint v0.1

Status: implementation handoff package for Codex, not a replacement for the frozen coursework baselines.

Purpose: remove architecture/design work from Codex's critical path so Codex can spend quota on implementation, integration, debugging and running the local application.

## What this package fixes as implementation decisions

- Architecture: modular monolith.
- Frontend: React + TypeScript + Vite, mobile-first responsive UI.
- Backend: FastAPI + Python 3.12.
- Persistence: SQLite for the coursework MVP, accessed through SQLAlchemy 2.x; design is portable to PostgreSQL later.
- API: REST under `/api/v1`.
- External systems: provider adapters with deterministic mock implementations first.
- AI: provider-pluggable assistant layer; deterministic feasibility remains authoritative.
- Core vertical slice: Create Journey -> Generate Plan -> Select Plan -> Simulate Booking/Payment -> Start Journey -> Detect/Inject Event -> Generate ReplanProposal -> Explain -> User Accepts -> New PlanVersion becomes active.

## Source-derived facts preserved

The package preserves the project facts available in the CityNexus handoff:

- Official coursework project: Project #11, A Smart City Traveler System.
- Product name: CityNexus.
- Product framing: context-aware journey orchestration.
- Bounded contexts: Journey Management; City Discovery; Booking and Commerce; Journey Intelligence.
- Source-backed entities available in the handoff: Traveler, Journey, JourneyTwin, PlanVersion, Activity, Place, CityService, Commitment, Constraint, Event, ReplanProposal, Booking, Order, Transaction, Recommendation, Preference.
- The promoted v0.4.2 RC3 domain reportedly contains 18 core entities, but the handoff does not preserve the names of the two additional entities. This package does not invent them.
- `PlanVersion.planning_mode`: balanced, budget, explore, strict_schedule.
- Replanning hard gates: hard constraints pass; locked commitments are preserved.
- Replanning score weights: commitment preservation .24, stability .18, time reliability .15, preference fit .12, mobility fit .10, budget fit .08, robustness .07, opportunity value .06.
- AI is assistive, not the feasibility authority.
- User confirmation is required before a proposed replan replaces the active plan.
- Core planning must degrade gracefully when AI is unavailable.

## Important boundary

State values, API field names, SQL columns, endpoint shapes, technical infrastructure tables and some lifecycle details in this package are implementation proposals created to turn the source model into an executable MVP. They must not be presented as exact quotations of the frozen domain baseline unless reconciled against the local v0.4.2 YAML.

## Codex entry point

Read only these files first:

1. `CODEX_START_HERE.md`
2. `00_SOURCE_AND_SCOPE.md`
3. `09_WORK_PACKAGES.md`

Then implement the current work package. Do not redesign the architecture before implementation unless a concrete local contradiction is found.
