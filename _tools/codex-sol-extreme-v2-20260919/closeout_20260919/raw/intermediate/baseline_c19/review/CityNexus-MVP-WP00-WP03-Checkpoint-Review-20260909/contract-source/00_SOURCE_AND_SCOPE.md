# 00 - Source and Scope Contract

## A. Facts derived from the existing CityNexus project material

### Official scope

CityNexus implements the coursework option **Project #11 - A Smart City Traveler System**.

### Product intent

CityNexus is a context-aware journey orchestration platform. It should maintain an executable journey before and during travel, react to events, protect real-world commitments and explain changes.

### Core journey chain

Traveler -> Create Journey -> add time/budget/preferences/constraints -> verified city/mobility/booking/context data -> deterministic feasibility -> recommendation/personalisation -> PlanVersion -> user selection -> booking/order/payment -> Commitment -> execute Journey -> JourneyTwin -> Event -> ReplanProposal -> preserve commitments -> re-score -> explain -> user confirmation -> activate new PlanVersion.

### Bounded contexts

1. Journey Management
2. City Discovery
3. Booking and Commerce
4. Journey Intelligence

### Source-backed entity names available in the handoff

Traveler; Journey; JourneyTwin; PlanVersion; Activity; Place; CityService; Commitment; Constraint; Event; ReplanProposal; Booking; Order; Transaction; Recommendation; Preference.

The promoted v0.4.2 RC3 reportedly has 18 core entities. The handoff explicitly says the names of the two additional entities were not preserved. This blueprint therefore does not invent those names.

### Planning modes

- balanced
- budget
- explore
- strict_schedule

### Replanning business rules

- Hard constraints are non-negotiable.
- Locked commitments must be preserved.
- Reality is evaluated before recommendation.
- User confirmation is required.
- Replanning must be explainable.
- Core planning must degrade gracefully if AI is unavailable.

### Contextual Journey Utility Score

| Component | Weight |
|---|---:|
| commitment preservation | 0.24 |
| stability | 0.18 |
| time reliability | 0.15 |
| preference fit | 0.12 |
| mobility fit | 0.10 |
| budget fit | 0.08 |
| robustness | 0.07 |
| opportunity value | 0.06 |

Weights sum to 1.00.

## B. Implementation decisions introduced by this blueprint

These are engineering choices for the MVP, not claims that the frozen domain YAML used these exact technical representations.

- Modular monolith instead of microservices.
- SQLite for the local demo.
- SQLAlchemy ORM and Alembic migrations.
- JSON columns represented as TEXT/JSON through SQLAlchemy so SQLite works locally.
- UUID identifiers represented as strings.
- REST API under `/api/v1`.
- Mock adapters for all external providers during the first vertical slice.
- Explicit technical audit/provider-call tables, which are infrastructure records and not new domain entities.
- Lifecycle enums in `05_STATE_MACHINES.md` are implementation proposals and must be reconciled with the current local domain YAML if that YAML already defines exact enum names.

## C. MVP completion definition

The MVP is complete when a clean local checkout can run one end-to-end disruption scenario with no network dependency:

- create journey;
- generate/select plan;
- create simulated booking/payment commitment;
- start journey;
- inject a disruption;
- produce a feasible replan preserving a locked commitment;
- accept it and activate a new plan version;
- inspect JourneyTwin and history;
- repeat with AI disabled and still complete the core flow.

The 138-requirement baseline remains the long-term implementation target. MVP completion does not imply all 138 requirements are fully implemented.
