# CityNexus Real-World Trip Operations V9 — Final Report

## Outcome

The V9 product completion gate is green on the deterministic/captured path. CityNexus imports an existing reservation, protects the arrival Commitment, plans a generic multi-day stay-aware Journey with per-leg mobility truth, handles luggage before check-in, executes a disruption recovery through the real post-action feasibility gate, keeps a read-only offline snapshot, and publishes the same active Journey state to the web/mobile UI and Edge Companion.

The final archive is the single delivery artifact requested for this iteration:

`CityNexus-Real-World-Trip-Operations-V9-Final-20260912.zip`

## Verification summary

- Supplied six-gate reality checker: `6 passed / 0 failed`.
- Backend full regression: `334 passed, 2 skipped, 2 warnings`.
- Frontend Playwright, serialized: `11 passed`.
- Frontend production build: PASS; Vite emitted only the existing large-chunk advisory.
- Ruff check: PASS; Ruff format check: `166 files already formatted`.
- Python compileall: PASS.
- MCP boundary suite: `6 passed`.
- Promptfoo-compatible adversarial evaluation: `13/13` under a deterministic adapter.
- Fresh package/extract replay: archive created at approximately `18:50:38+08:00`; extracted backend V7/V8/V9/contract selection `14 passed, 2 warnings`; extracted frontend `npm ci` plus `npm run build` PASS.

## What changed

Core work is summarized in `REAL_TRAVEL_EVIDENCE.md`, `PROVIDER_STATUS.md`, `UI_REAL_WORLD.md` and `EDGE_COMPANION_EVIDENCE.md`. The main product changes are domain reconciliation, generic city graph generation, complete per-leg mobility evidence, provider CRS boundaries, Journey Inbox and external reservations, luggage/check-in constraints, schedule freshness and Guardian wake-up, offline/location/push seams, Evidence drawer UI, and device-scoped Edge Companion APIs.

## Authority and autonomy

The policy boundary uses reversibility, loss, schedule drift, provider state, protected Commitment level and the traveler’s Autonomy Envelope. Ordinary reversible actions within the envelope can execute autonomously. Deterministic validation checks the post-action Journey and business facts. C4 is protected from unauthorized destruction, while explicit authorized Commitment management remains policy-governed. Learned preference evidence influences ranking and explanations but does not expand budget, payment, Commitment or autonomy authority.

## Honest external-runtime limits

- Amap live, GTFS-RT/OTP and Duffel credentials were not configured; those are `NOT_CONFIGURED`.
- The bounded DeepSeek smoke returned `FAILED_BLOCKED` and used the deterministic fallback. It is not reported as model-backed PASS.
- Hermes MCP V2 is protocol-tested; a Hermes CLI/model-backed external run is `NOT_RUN_EXTERNAL`.
- OpenInference/Phoenix has a checked-in tracing seam but no external collector was configured.

These limits do not invalidate the captured/replay product gate; they are explicit in the gate matrix and provider status report.

## Packaging exclusions

The final archive excludes temporary keys, API secrets, `.venv`, `node_modules`, frontend `dist`, runtime databases, caches, raw browser artifacts, staging directories and nested assist/final archives. It includes the seven V9 reports, curated UI screenshots, source/contracts/tests and supporting deterministic evidence. The verified package contained `7,867` entries and `0` forbidden entries.
