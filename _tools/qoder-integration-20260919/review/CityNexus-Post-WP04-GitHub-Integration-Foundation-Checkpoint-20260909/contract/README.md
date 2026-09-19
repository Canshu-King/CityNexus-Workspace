# CityNexus Post-WP04 GitHub Integration Foundation

Purpose: prepare the code and contracts that Codex can integrate after the current WP04 Booking/Payment/Commitment checkpoint passes external review.

This package is deliberately **not** a request to interrupt WP04. It is a low-conflict foundation for WP05-WP09 and progressive real-provider adoption.

## Hard rules

1. Do not start this package until WP04 receives an external PASS.
2. Do not reopen frozen coursework/Visio baselines.
3. Do not replace the CityNexus domain with third-party project models.
4. Third-party projects live behind CityNexus provider/solver/UI boundaries.
5. Real providers are disabled by default; mock/deterministic flows remain the regression baseline.
6. AI is never authoritative for hard feasibility, payment, commitment strength, or plan activation.
7. No SHA/file/package hash work is required.
8. Do not add every dependency at once. Adopt by work-package gate.

## What is already prepared

- provider capability/degradation contracts;
- routingpy-compatible Mobility adapter with legacy `estimate_minutes` compatibility;
- Photon geocoder adapter contract;
- Open-Meteo context adapter and weather-risk parser;
- AI explanation boundary with deterministic reason codes and LiteLLM adapter;
- Opportunity Window calculation;
- Feasibility Envelope summary;
- Replan Diff as a first-class deterministic object;
- OR-Tools optional solver boundary and reference plan-variant selector;
- WebAuthn step-up authentication contract;
- frontend MapLibre/Turf/XState scaffolding plan;
- Playwright Golden Scenario test contract;
- exact phased adoption matrix for MapLibre, Turf, routingpy, Valhalla, GraphHopper, OTP, LiteLLM/DeepSeek, Open-Meteo, Photon, OR-Tools, XState, shadcn/ui, py_webauthn, Playwright and optional PydanticAI;
- explicit reference-only treatment for PlacesRecommendation, Travel-Story, Timefold and Stripe samples.

Run `CODEX_AFTER_WP04_START_HERE.md` when WP04 is externally accepted.
