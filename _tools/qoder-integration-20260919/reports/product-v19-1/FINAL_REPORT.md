# CityNexus V19.1 EAC Convergence

Date: 2026-09-15

V19.1 implementation is complete for the capability evidence and live UX slice. The authoritative V19 tree was preserved; EAC reference patches were ported semantically.

Delivered:

- conservative local capability extraction with clause-local negation and rumor handling;
- deterministic canonicalization with hard accessibility invariants;
- requirement-scoped accessibility evidence and mapping/list OSM tag normalization;
- route-level step-free evidence remains `NEEDS_LIVE_EVIDENCE` without provider proof;
- `PUT /capabilities` replaces the full desired set;
- `POST /capabilities/confirm` upserts only submitted items and preserves prior active items;
- REST/toilet constraints use continuous-span `interval_min` semantics;
- runtime OpenAPI parity test and frontend runtime-card styling;
- production build and browser smoke evidence at desktop and 390x844 mobile viewport.

Native Hermes remains unavailable in this environment. Runtime status reported `hermes_native_gateway.ready=false`, `configured=false`, and `native_mcp_proven=false`; no Connected claim is made.
