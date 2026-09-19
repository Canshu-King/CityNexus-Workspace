# CityNexus Sol Deep Mission report

## Outcome

All four deep tracks are complete against a reproducible frozen snapshot. One real P1 product defect, two P2 contract/integration risks and no P0 truth-corruption defect were verified.

### E — Cross-layer behavioral contract reconstruction

Completed. `artifacts/contract_graph.json` traces backend truth through API projection and frontend/UI decisions for Journey, active plans, disruptions, ACK/resolution, proposals, trigger linkage, mobility provenance, bookings, budget evidence and Today/Live/Trips.

The principal mismatch is CX-SOL-001: Live ignored `current_activity_id` and showed fixed array positions. A minimal repro, candidate patch and browser regression are included. ACK versus resolution and budget scope are currently correct. The accepted-proposal/Event dual-resource representation is documented as CX-SOL-002. Missing frontend fact-quality observability is CX-SOL-003.

### F — Model-based/property-based recovery audit

Completed. The deterministic randomized harness executed 5,000 sequences of 80 steps (400,000 transitions) over all twelve requested invariants. No model invariant failed. Focused real-code gates added 81 passing backend tests. The real Live projection defect was shrunk to three activities, two legs and a cursor at the second activity.

Candidate patch verification: frontend full typecheck PASS, production build PASS, targeted Playwright regression PASS.

### G — Semantic merge simulator

Completed. The Git history provided exact baseline/truth/visual/prerequisite/evidence boundaries. `artifacts/symbol_overlap.json` finds seven multi-owner overlap files; reports classify symbol-level behavioral ownership. The current frozen integration was used as a disposable simulated reconciliation, then augmented only inside the output clone with CX-SOL-001 and focused gates.

Recommended semantic order is truth/provider gates, shared lifecycle helpers, prerequisites, visual/IA, cursor patch, focused gates, then screenshot review. The owner should not merge against the moving active working tree without freezing a new SHA.

### H — Failure injection and graceful degradation

Completed. Routing timeout/malformed response, live-provider failure, hard allowlist, physical identity ambiguity, AI/weather degradation, stale proposal, offline/read-only behavior and duplicate action/idempotency are covered by executable or focused existing gates. Booking import and map failure are fully specified; map-tile outage was not externally induced because no deployment/provider target was authorized.

## Findings

- **CX-SOL-001, P1:** Live current/next display used array positions rather than the authoritative cursor. Patch ready and verified.
- **CX-SOL-002, P2:** accepted recovery requires a proposal-to-trigger join while Event remains ACKNOWLEDGED. Current helper is correct but merge-fragile.
- **CX-SOL-003, P2:** backend enforces normalized mobility fact quality, while V8 frontend legs cannot independently observe it. Keep hard decisions server-owned or expose an explicit field.
- **Visual follow-up, owner decision:** existing L2 mobile evidence places the proposal Accept CTA below the fold. This is not a truth defect, but should be addressed after semantic integration.
- **Performance debt, unchanged:** main ~1.127 MB and MapLibre ~1.053 MB minified; MapLibre is already split, main route/features remain candidates for future code splitting.

## Owner action

Review and apply CX-SOL-001 to a freshly frozen integration commit, retain the regression, then run the focused gates listed in `raw/TEST_RESULTS.md`. Preserve Qoder's active uncommitted work; do not use this disposable clone as a merge source without owner review.

## Verdict

CODEX_SOL_DEEP_MISSION_COMPLETE

