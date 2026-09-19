# CityNexus V8 TravelerTwin Evidence

## Result

The V8 TravelerTwin path is present and inspectable across the backend, API, planning layer, and frontend Control Tower. It distinguishes user-provided `EXPLICIT` preferences from inferred `LEARNED_SOFT` evidence, keeps the learned layer reversible, and does not allow learned evidence to expand money, commitment, or autonomy authority.

## Evidence model

- Explicit preferences are read from the persisted `preferences` records and surfaced with `source=EXPLICIT`.
- Learned evidence is stored in `traveler_preference_evidence`, materialized into `traveler_twin_snapshots`, and surfaced with `source=LEARNED_SOFT`.
- Evidence carries a dimension, direction, strength/confidence, explanation, provenance, status, creation time, and optional expiry.
- Expired active evidence is excluded from planning and marked expired during the active-evidence refresh path.
- Conflicts resolve in favor of explicit user preference; the snapshot records the resolution as `EXPLICIT overrides LEARNED_SOFT`.
- Learned evidence can be cleared independently through the TravelerTwin API; explicit preferences remain intact.

## Reflect → Learn lifecycle

The Journey Reflect endpoints expose the actual plan/replan timeline, disruption history, cost summary, and feedback hook. `POST /api/v1/journeys/{journey_id}/reflect/process` records the processing event and updates the TravelerTwin snapshot through the existing learning path. `GET /api/v1/travelers/{traveler_id}/traveler-twin` returns the inspectable snapshot, while `DELETE /api/v1/travelers/{traveler_id}/traveler-twin/learned` clears only learned soft evidence.

## Planning integration

`planning_preference_items()` is consumed by stay and mobility planning. Learned soft dimensions participate in POI/stay ranking, mobility scoring, CP-SAT soft objectives, and Journey-impact explanations. They remain soft inputs: hard arrival/departure margins, protected commitments, budget, loss, and authority-envelope checks are evaluated independently by deterministic gates and Delegation Policy.

## Product evidence

- The V8 Traveler Twin surface is available in the desktop navigation and presents explicit preferences, learned soft preferences, confidence/evidence counts, conflicts, and the authority boundary.
- The frontend Control Tower regression test is `frontend/e2e/product-hardening.spec.ts`, test `TravelerTwin Control Tower renders persisted evidence and authority boundary`.
- The V8 browser flow covers the Traveler Twin destination through the mobile `Me` surface and the desktop Intelligence/Traveler Twin navigation.
- Backend implementation: `backend/app/execution/traveler_twin.py`.
- API implementation: `backend/app/main.py` TravelerTwin and Reflect routes.
- Persistence contract: `backend/db/schema.sql` tables `traveler_preference_evidence` and `traveler_twin_snapshots`.
- Planning integration: `backend/app/stay_mobility.py` and `backend/app/planning/stay_mode_solver.py`.

## Boundary

This evidence is based on the local captured/replay implementation and regression suite. It does not claim an external Hermes inference run or external live-provider learning feed. The V8 reports preserve those as explicit non-configured boundaries.
