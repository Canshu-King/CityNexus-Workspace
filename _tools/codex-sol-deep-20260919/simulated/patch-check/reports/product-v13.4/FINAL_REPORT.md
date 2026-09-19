# CityNexus V13.4 — Provider Truth / Real Evidence

Date: 2026-09-13  
Target: `CityNexus-V13.4-Provider-Truth-Real-Evidence-20260913.zip`

## Outcome

V13.4 is implemented and converged on the current authoritative worktree. The vertical slice now carries Journey Memory and semantic intent into a Journey-aware provider capture, materializes real/sealed-real Places, completes missing venue facts only from captured official observations, applies a deterministic provider-fact gate, composes an authoritative PlanVersion, and exposes the result through the discovery UI and existing JourneyTwin/plan surfaces.

The final backend regression is green: **388 passed, 2 skipped, 2 warnings**. The focused V13.4/V13.3/V7 convergence set is **7 passed**. A Playwright UI flow reached `SELECTED` with `SEALED REAL REPLAY`, displayed official versus unknown candidate evidence, and saved a screenshot at `output/playwright/v13.4-provider-truth-discovery.png`.

## Important truth boundary

The Golden path is deliberately not reported as a fully live provider matrix. The selected PlanVersion contains a captured Valhalla fact for the selected real Place, while uncovered structural/commitment legs remain `SYNTHETIC_FIXTURE`. The PlanVersion runtime label is therefore `SEALED_REAL_REPLAY_WITH_EXPLICIT_SYNTHETIC_FALLBACK`, and `fully_provider_grounded=false`. This prevents a mixed matrix from being presented as wholly real.

The sealed weather snapshot is time-local when its captured window overlaps the requested Journey window. When it does not, the result is explicitly `WEATHER_WINDOW_UNCERTAIN` / `SEALED_REPLAY_OUT_OF_REQUEST_WINDOW`; no weather certainty is invented.

## Delivered

- Journey-scoped `RealPlaceCandidate` identity and SQLite migration.
- Append-only `ProviderCall` audit event IDs.
- Journey-derived discovery anchor selection and captured provider status.
- Multi-query DiscoveryIntent execution with bounded query limits.
- Captured official-web evidence completion for Tianjin Museum opening hours and cost.
- Explicit preservation of unknown/conflicting hours and cost.
- Captured Valhalla mobility facts with per-fact provenance and explicit synthetic fallback.
- Time-window-aware sealed Open-Meteo evidence.
- Safe DeepSeek HTTP/provider diagnostics with no key or prompt persistence.
- V13.4 default sealed-real-replay UI mode and provenance/uncertainty presentation.

## Security and release hygiene

The DeepSeek key supplied in chat was not written to source, reports, the database, or the release archive. API diagnostics retain only status, provider code, model, and response ID. The release package excludes secrets, databases, caches, virtual environments, frontend build output, Playwright state, and nested archives.

## Remaining explicit limitation

The current sealed mobility bundle is a mixed provider snapshot: selected real-Place legs can be `CAPTURED_REPLAY`, but all legs are not yet backed by a single Journey-time live Valhalla matrix. That limitation is visible in the evidence and is not silently promoted to a stronger claim.
