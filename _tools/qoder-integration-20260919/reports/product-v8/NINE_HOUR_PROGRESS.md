# CityNexus V8 nine-hour product sprint

Runtime label: `LOCAL_PRODUCT_SPRINT`  
Repository: `D:\moodle\CityNexus`  
GOAL_START: `2026-09-12T12:19:59+08:00`  
TARGET_END: `2026-09-12T21:19:59+08:00`  
Evidence captured: `2026-09-12T15:39+08:00`  
Elapsed engineering time at this checkpoint: approximately `3h 19m`; the report does not claim that nine wall-clock hours elapsed.

## Baseline captured

- Existing V7 final archive preserved at `CityNexus-Adaptive-Traveler-Twin-V7-Final-20260912.zip`.
- Before images: `ui/before/desktop-v7.png` and `ui/before/mobile-v7.png`.
- V7 was a single dense control surface; mobile content was long and operational rather than a focused Journey composition.
- Baseline repository was already dirty with prior V2–V7 artifacts. No reset, clean, checkout, or automatic commit was used.
- Baseline history: `7d22cd0`, `e3b7875`, `072e84f`, `d5236d5`, followed by the pre-existing V7 workspace changes.
- Existing V7 frontend and backend regression paths were kept at `/` and in their original test suites.

## Work log

| Window | Result | Evidence |
|---|---|---|
| 12:20–12:45 | Replayed V7.1 trust fixes: expired Twin evidence, weekday opening hours, explicit foreign currency | `backend/tests/test_v8_stay_mobility.py` |
| 12:45–13:40 | Added multi-day Journey context, arrival/departure anchors, captured accommodation offers, mobility facts, and stay options | `backend/app/stay_mobility.py`, `backend/app/main.py`, schema tables |
| 13:40–14:35 | Added mode-aware bounded CP-SAT, weather re-evaluation, option selection and policy-gated Autopilot recovery | `backend/app/planning/stay_mode_solver.py`, V8 backend tests |
| 14:35–15:25 | Rebuilt the V8 product shell and split the frontend into app, components, stay, mobility, and agent features | `frontend/src/app/`, `frontend/src/components/v8/`, `frontend/src/features/` |
| 15:25–15:39 | Browser flagship, mobile acceptance, DeepSeek smoke, OpenAPI parity, Ruff, build and evidence capture | `frontend/e2e/product-v8.spec.ts`, gate matrix |

## Validation snapshot

- Backend focused V8 + contract tests: `8 passed`.
- Backend final full suite: `330 passed, 2 skipped, 2 warnings`.
- Frontend Playwright: `10 passed` including V7/V6/V5/V4 and the two V8 browser flows.
- Frontend production build: passed; Vite emitted only the existing large-chunk advisory.
- Ruff and compileall: passed after import formatting.
- Native DeepSeek process-only smoke: `VALIDATED_AI`; deterministic post-action gate: `PASS`.
- Hermes, live hotel, live transit, Phoenix export, and model-backed Promptfoo were not configured in this local workspace and remain explicitly external/optional statuses.
- Final archive hygiene: `1,739` ZIP entries, `0` forbidden dependency/cache/database/nested-archive entries, `0` credential-value hits, and fresh-extract focused replay `8 passed`.
- The final browser run was serialized against the shared SQLite server: `10 passed`; the earlier parallel attempt is not used as evidence.
