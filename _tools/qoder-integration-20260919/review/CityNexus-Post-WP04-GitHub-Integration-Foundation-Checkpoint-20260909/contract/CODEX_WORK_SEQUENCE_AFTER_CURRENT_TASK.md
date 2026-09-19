# Exact Codex sequence after the current task

Do not use this until the current WP04 work has stopped at its checkpoint and GPT has externally accepted it.

1. Read `CODEX_AFTER_WP04_START_HERE.md`.
2. Dry-run foundation application:
   `python <package>/scripts/apply_integration_foundation.py D:\moodle\CityNexus`
3. Manually review every reported target. If a newer post-WP04 file exists, merge semantically instead of overwriting.
4. Apply low-conflict foundation only:
   `python <package>/scripts/apply_integration_foundation.py D:\moodle\CityNexus --apply`
5. Run the **entire** existing backend test suite plus foundation tests.
6. If any existing regression occurs, STOP and fix only that integration conflict.
7. Complete WP05 with mocks. STOP at WP05 checkpoint.
8. After external WP05 PASS, complete WP06 Phase A with mocks and ReplanDiff. STOP at deterministic WP06 checkpoint.
9. After external deterministic-WP06 PASS, integrate routingpy + Valhalla and Open-Meteo one provider at a time. Keep fallback tests.
10. Add GraphHopper only as an alternate provider. Add OTP only after GTFS is confirmed.
11. Add OR-Tools behind PlannerAdapter, never instead of the authoritative feasibility gate.
12. WP07: deterministic fallback -> LiteLLM -> DeepSeek. AI-off scenario remains mandatory.
13. WP08: MapLibre + Turf + XState + shadcn/ui, with stable data-testid selectors.
14. WP09: Playwright Golden Scenario.
15. Do not enter the next numbered WP without a checkpoint/review.
16. Do not perform SHA/file/package hash work.
