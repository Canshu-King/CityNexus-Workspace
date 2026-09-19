# CityNexus V10 · nine-hour progress

## Runtime accounting

- Goal start: `2026-09-12 19:52:53 +08:00`
- Nine-hour target end: `2026-09-13 04:52:53 +08:00`
- Checkpoint: `2026-09-12 22:46 +08:00`
- Codex active time reported at checkpoint: `8,103 seconds` (~2h 15m)
- Wall-clock elapsed at checkpoint: ~2h 53m
- Runtime label: `LOCAL_EXECUTION_SHORT_OF_9H`

This is a product checkpoint, not a claim that a nine-hour wall-clock run was completed. Work continued past the first green milestone into Inbox, Provider replay, Web Push fallback, UI evidence, and regression stabilization.

## Completed slices

1. Baselines and V10 gap verification.
2. DeepSeek Responses normalization for text, tools, web-search, vision, reasoning continuation, usage, and latency metadata.
3. WebObservation trust boundary with URL/domain/title/fingerprint and non-authoritative status.
4. Mature ICS parsing, strict text/image extraction drafts, QR/barcode scan path, unresolved critical-field handling, and confirmation boundary.
5. Synthetic mobility provenance correction plus sealed checksum-validated provider replay.
6. Generic selected-POI Compose Engine path through deterministic feasibility and PlanVersion materialization.
7. Freezeable ExecutionClock, actual-time Edge/offline projections, generated OpenAPI client, and TanStack Query V10 surface.
8. Vite PWA/IndexedDB offline path, Storybook primitives, axe gate, Playwright quality budget, and mobile Inbox/Live UI.
9. Optional VAPID Web Push delivery with an explicit record-only fallback.
10. Fresh-process regression stabilization: V5/V6 tests reset demo state, and PWA document caching is scoped to V8 routes so legacy Hub reloads remain reliable.

## Latest evidence

- Current-gap checker: `10 passed / 0 failed`.
- Backend: `343 passed, 2 skipped, 2 warnings` in 34.43s.
- Frontend: `15 passed` in 50.6s, including V5/V6/V8/V9 and V10 Inbox, accessibility, Live Execution, and quality budget.
- MCP boundary: `6 passed`.
- Storybook 9.1.20 static build: passed.
- Promptfoo-compatible local adapter: `13/13`; model-backed Promptfoo CLI was not claimed.
- Ruff and Python compile checks: passed.

## Remaining external capability labels

DeepSeek’s official probe returned HTTP 200 for text/web/vision but HTTP 400 for forced function choice while thinking was enabled. The custom client’s `reasoning: {effort: "none"}` tool turn passed in a mocked/direct compatibility probe. The live web response did not expose normalized source items, so no unsourced summary is persisted as a WebObservation. Hermes endpoint, VAPID keys, live Valhalla, OTP/GTFS-RT, and model-backed Promptfoo/Phoenix are not configured in this workspace.

