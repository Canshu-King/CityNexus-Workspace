# Codex Start Here - quota-saving instructions

Your job is implementation, not architecture discovery.

## Do not spend quota on

- redesigning the product scope;
- reopening the Visio routing research;
- microservices;
- a real payment gateway;
- a real booking provider;
- production OAuth before the vertical slice works;
- choosing a different frontend/backend stack;
- replacing deterministic feasibility with an LLM;
- inventing the two missing v0.4.2 domain entities;
- rewriting these specifications into another specification.

## Mandatory first action in the local repo

Perform a read-only reconciliation against the actual current files:

- current promoted domain model v0.4.2 RC3;
- requirements baseline v0.3;
- current use-case baseline.

Use `tools/reconcile_domain.py` if helpful. The goal is only to detect naming/enum mismatches. If the local domain contains two entities absent from this blueprint, record them in `docs/implementation/domain-reconciliation.md` and decide whether the MVP needs them now. Do not change the frozen source baseline.

## Architecture is fixed for MVP

- React + TypeScript + Vite frontend.
- FastAPI backend.
- SQLite + SQLAlchemy.
- REST `/api/v1`.
- Modular monolith.
- Mock provider adapters first.
- Deterministic planning/replanning core.
- Optional AI adapter for semantic recommendation/explanation.

## Implementation order

Use `09_WORK_PACKAGES.md`. Do not skip gates.

The first useful demo must execute this exact vertical slice:

1. Create a traveler/journey.
2. Add time, budget, preference and hard/soft constraints.
3. Generate at least two feasible PlanVersion candidates from mock city data.
4. Select one plan.
5. Simulate a booking and a successful payment, creating a commitment.
6. Start the journey and expose JourneyTwin.
7. Inject a disruption event affecting a future activity.
8. Generate a ReplanProposal deterministically.
9. Demonstrate that a locked commitment is preserved.
10. Show score breakdown and deterministic explanation.
11. Accept the proposal.
12. Activate the new PlanVersion and supersede the old one.
13. If AI adapter is disabled, the same core flow still succeeds.

## Stop conditions

At the end of each work package:

- run tests;
- write a short checkpoint in `docs/implementation/checkpoints/WPxx.md`;
- do not move on while the package gate is red.

Do not wait to implement all 138 requirements before creating the demo. Track all requirements using `IMPLEMENTATION_STATUS_TEMPLATE.csv` and progressively move items from PLANNED to PARTIAL/SIMULATED/IMPLEMENTED.
