# 09 - Phased Work Packages

The work packages are designed to minimise Codex reasoning quota. Each package has a fixed output and gate. Codex should implement, test and checkpoint; it should not redesign earlier decisions unless a local baseline contradiction is proven.

## WP00 - Baseline reconciliation and safe bootstrap

Goal: connect this blueprint to the real local CityNexus repo without modifying frozen coursework baselines.

Tasks:
- read current v0.4.2 RC3 domain YAML and list all 18 entity names;
- compare exact enum/state names with this implementation proposal;
- read requirements baseline v0.3 only far enough to map MVP capabilities to real requirement IDs;
- record discrepancies in `docs/implementation/domain-reconciliation.md`;
- create `frontend/`, `backend/`, `contracts/`, `data/mock/`, `tests/`, `scripts/` without moving frozen directories;
- copy `api/openapi.yaml` to `contracts/openapi.yaml`;
- create `.env.example` and `.gitignore`.

Gate:
- frozen domain/requirements/Visio files unchanged;
- exact 18 entity list recorded, not guessed;
- application folders created;
- no implementation yet requires internet.

## WP01 - Backend foundation and database

Goal: boot FastAPI with SQLite and seed deterministic mock data.

Tasks:
- FastAPI app factory/main;
- config/settings;
- SQLAlchemy session;
- models/migrations matching reconciled MVP schema;
- health endpoint;
- demo reset/seed script;
- audit/error envelope foundation.

Gate:
- empty DB -> schema -> seed works twice identically;
- `GET /api/v1/health` returns 200;
- DB tests CNX-I-001/002 pass.

## WP02 - Traveler, preferences, journey and constraints

Goal: create a configured Journey ready for planning.

Tasks:
- traveler/preferences CRUD subset;
- Journey create/get/patch;
- hard/soft Constraint add/list/delete;
- money/time validation;
- planning_mode support.

Gate:
- canonical demo journey created via API;
- hard budget/time constraints persisted;
- CNX-I-003 through CNX-I-007 pass.

## WP03 - Discovery and initial planning

Goal: generate multiple deterministic feasible PlanVersions.

Tasks:
- mock CityDataProvider;
- mock MobilityProvider;
- Place/CityService endpoints;
- initial candidate generator;
- deterministic feasibility engine reuse;
- score breakdown;
- select plan operation.

Gate:
- at least two feasible candidates for canonical fixture;
- each candidate has activities, cost, score breakdown;
- plan selection makes Journey PLANNED;
- no AI dependency;
- CNX-I-008 through CNX-I-010 pass.

## WP04 - Booking, order and payment simulation

Goal: create real domain records for commitments without real payment risk.

Tasks:
- mock BookingProvider;
- mock PaymentProvider;
- booking/order endpoints;
- transaction endpoint with idempotency;
- commitment lifecycle updates;
- fixture option for forced provider failure.

Gate:
- canonical river-cruise booking/payment creates an ACTIVE commitment with final demo level LOCKED;
- duplicate transaction key is safe;
- forced failure never creates a false paid commitment;
- CNX-I-011 through CNX-I-013 pass.

## WP05 - Journey execution and JourneyTwin

Goal: start and advance the journey.

Tasks:
- start operation;
- activity lifecycle operations;
- JourneyTwin projection builder/refresher;
- current/next activity and upcoming commitments;
- history/audit basis.

Gate:
- Journey PLANNED -> ACTIVE;
- Twin READY and references active plan/current activity;
- completing activity advances projection;
- CNX-I-014/015 pass.

## WP06 - Event and deterministic replanning core

Goal: implement CityNexus's distinguishing capability.

Tasks:
- context Event endpoints;
- event effect model;
- snapshot + prefix/protected/mutable partition;
- candidate families F0-F4;
- hard feasibility gates;
- exact Contextual Journey Utility Score weights;
- deterministic tie-break;
- plan diff;
- ReplanProposal persistence;
- accept/reject with atomic active-plan swap and stale check.

Gate:
- Tech Art Center closure produces at least one feasible proposal;
- locked 15:30 River Cruise unchanged;
- all eight score components present;
- active plan unchanged until accept;
- acceptance makes new plan ACTIVE and old plan SUPERSEDED;
- CNX-I-016 through CNX-I-023 pass.

## WP07 - AI Copilot and graceful degradation

Goal: add AI value without making it authoritative.

Tasks:
- AIProvider interface;
- deterministic fallback provider;
- optional real provider behind environment configuration only;
- Copilot endpoint;
- explanation polishing consumes structured verified facts;
- provider outage/degraded state.

Gate:
- AI enabled and AI disabled both complete the same core replan;
- AI cannot activate a plan or override a failed hard gate;
- CNX-C-008 and CNX-E-004 pass.

## WP08 - Frontend vertical slice

Goal: make the complete flow demonstrable, not merely API-correct.

Screens:
- Dashboard
- Create Journey
- Candidate Plans
- Active Journey/JourneyTwin
- Booking/payment simulation
- Event injection panel (clearly DEMO ONLY)
- Replan Proposal comparison
- History
- Copilot panel

Gate:
- a user can execute CNX-E-001 and CNX-E-002 without editing the database or using curl;
- mobile-width layout remains usable;
- TypeScript build clean.

## WP09 - E2E, security and submission evidence

Goal: make the demo reproducible and produce evidence for coursework.

Tasks:
- Playwright/API E2E tests;
- stale/idempotency/provider-failure tests;
- requirement implementation status import/update;
- screenshots of working flow;
- demo reset/run script;
- concise architecture and test evidence for PPT/Part 2.

Gate:
- all P0 tests in `tests/test_matrix.csv` pass;
- demo reset + canonical scenario repeatable on clean checkout;
- AI-off scenario passes;
- no secrets committed.

## WP10 - Progressive 138-requirement expansion

Goal: move beyond MVP without destabilising the vertical slice.

Method:
- import actual requirements baseline;
- classify each item IMPLEMENTED / PARTIAL / SIMULATED / PLANNED / OUT_OF_MVP;
- prioritise Must/High and trace-linked gaps;
- add one small requirement batch at a time with tests;
- never claim a requirement is implemented without evidence/test linkage.

Gate for each batch:
- implementation status updated;
- acceptance criteria demonstrably met or status remains PARTIAL;
- existing vertical-slice regression suite stays green.
