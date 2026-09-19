# V8 gate matrix

| Gate | Result | Evidence |
|---|---|---|
| V7_REGRESSION | PASS | Backend full suite and frontend V7/V6/V5/V4 browser suites; V8 frontend run was 10/10 |
| V7_1_TRUST_FIXES | PASS | Focused expiry, weekday-hours, and foreign-currency tests |
| FRONTEND_PRODUCT_SHELL | PASS | Modular Vite + React shell; desktop/mobile screenshots and browser flow |
| DESIGN_SYSTEM | PASS | Shared V8 tokens, semantic states, focus-visible, reduced motion, responsive mobile composition |
| MULTI_DAY_JOURNEY | PASS | Arrival/departure context, party/occupancy, day grouping, overnight stay |
| ACCOMMODATION_PROVIDER | PASS_CAPTURED_REPLAY | Provider abstraction and immutable offer snapshots |
| STAY_INTELLIGENCE | PASS | Journey-impact ranking and inspectable cost/margin/cancellation evidence |
| MULTIMODAL_MOBILITY | PASS_CAPTURED_REPLAY | Five modes, frozen facts, explicit unknown costs and provider status |
| MODE_AWARE_CP_SAT | PASS | Bounded OR-Tools mode selection with deterministic fallback |
| STAY_MODE_JOINT_PLANNING | PASS | Top-K hotel candidates each evaluated with mobility and Journey impact |
| TRIP_STUDIO | PASS | Desktop day timeline, stay details, weather recovery action |
| MOBILE_LIVE_JOURNEY | PASS | Live Journey, Map, AI, Bookings, Me navigation and mobile sheet |
| V8_FLAGSHIP_E2E | PASS | Natural-language mission surface plus browser multi-day/autonomous recovery test |
| NATIVE_DEEPSEEK_MODEL_BACKED | PASS | Fresh process-only `VALIDATED_AI` smoke; deterministic gate passed |
| HERMES_MODEL_BACKED | NOT_RUN_EXTERNAL | No Hermes inference endpoint/credential configured |
| LIVE_HOTEL_PROVIDER | NOT_CONFIGURED | Captured adapter is available; live credential is intentionally not claimed |
| LIVE_TRANSIT_PROVIDER | NOT_CONFIGURED | Captured transit facts are available; live OTP/Valhalla is not configured |
| PHOENIX_TRACE | PASS_LOCAL_OPTIONAL_EXPORTER | Local spans verified; no external Phoenix export |
| PROMPTFOO_EVAL | PASS_LOCAL_DETERMINISTIC_ADAPTER | Preserved V7 local 13/13 adversarial adapter; no model-backed npm claim |
| SECRET_SCAN | PASS | No credential values; only intentional env-name placeholders and provider endpoint literals; final archive excludes TEMP_DEEPSEEK.env |
| FRESH_EXTRACT_REPLAY | PASS | 1,739-entry archive extracted to a clean staging directory; required files present; V8 + OpenAPI focused replay `8 passed` |
