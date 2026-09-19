# CityNexus WP06 → WP07 Road-Prep Assist

Date: 2026-09-09
Baseline reviewed: `CityNexus-WP06-PostGate-Checkpoint-20260909.zip`

This package is designed to reduce Codex work after the current WP06 checkpoint. It contains:

- the requested WP06 follow-up repair instruction;
- a prepared repo-relative patch implementing the low-risk parts of that repair;
- regression tests for the new behavior;
- pure reference modules for real Opportunity Window evidence, Open-Meteo weather snapshots, deterministic candidate ranking, and AI Copilot mutation boundaries;
- exact next-stage contracts for Valhalla, Open-Meteo, OR-Tools, LiteLLM/DeepSeek, frontend map/state work, and Playwright.

## Important safety rule

Do not stop or roll back a newer local working tree just to apply this package. If Codex has changed the same files since the checkpoint, use the patch as a semantic reference and merge the same behavior into the current files.

No SHA/file/archive integrity work is required.

## Prepared patch behavior

The patch already implements:

1. `candidate_count` counts feasible candidates rather than truncating raw candidates before the feasibility gate;
2. `preference_fit` uses persisted positive Traveler interest preferences instead of similarity to the disrupted Place;
3. fake duration-derived `opportunity_value` is removed and falls back to the documented neutral value until real OpportunityWindow evidence is wired;
4. completed/past commitments are excluded from JourneyTwin `upcoming_commitments` projection;
5. Replan generation supports optional `Idempotency-Key` replay/conflict protection without breaking existing callers;
6. exact-score ties preserve deterministic generation order instead of using random UUIDs;
7. reference foundations for real F3 Opportunity Window, weather snapshots, deterministic candidate ranking, and Copilot mutation safety are added.

## Validation performed

- Patch dry-run on the supplied checkpoint baseline: PASS.
- Patch application on a fresh copy: PASS.
- Focused patched suite: 21 PASS.
- Original checkpoint tests were split because the review environment sometimes leaves module-global `TestClient` processes alive after progress reaches 100%.
- Independently completed groups total the original 133 PASS + 1 skipped baseline; the five new WP06 follow-up tests pass, and four new WP07 foundation tests pass.
- Python compile check: PASS.

Start with `CODEX_START_HERE.md`.
