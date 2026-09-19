# Architecture delta: CityNexus 2.1 implementation shape

Keep the existing modular monolith and add adapters, not replacement systems.

```text
React + TypeScript + Vite
  |-- MapLibre GL JS ........ rendering only
  |-- Turf .................. client-side spatial helpers
  |-- XState ................ UI workflow state only
  |-- shadcn/ui ............. presentation components
  |
  v
FastAPI /api/v1
  |
  |-- Journey Core
  |     Journey / PlanVersion / Activity / Constraint / Commitment / Event
  |     JourneyTwin = read projection, not second source of truth
  |
  |-- Journey Intelligence
  |     deterministic feasibility
  |     OpportunityWindow detector
  |     FeasibilityEnvelope
  |     ReplanDiff
  |     OR-Tools optional optimizer
  |     verified ReasonCodes
  |
  |-- Provider Ports
  |     CityDiscoveryProvider -> mock / Photon+Overpass
  |     MobilityProvider      -> mock / routingpy -> Valhalla/GH/OTP
  |     ContextEventProvider  -> mock / Open-Meteo / later transit alerts
  |     AIProvider            -> deterministic fallback / LiteLLM -> DeepSeek
  |     PaymentProvider       -> mock / later test adapter
  |     StepUpAuthProvider    -> none / py_webauthn
  |
  v
SQLite MVP -> PostgreSQL only after vertical slice is stable
```

## Non-negotiable boundaries

- `Journey` remains authoritative write model / aggregate root.
- `JourneyTwin` is a projection of current authoritative facts.
- mobility engines return travel facts; they do not choose the Journey plan.
- OTP returns transit possibilities; CityNexus decides whether the Journey remains feasible.
- AI receives verified facts and reason codes; it may explain/rank but not create reality.
- OR-Tools may optimize only within deterministic constraints supplied by CityNexus.
- MapLibre/Turf/XState never implement server business rules.
