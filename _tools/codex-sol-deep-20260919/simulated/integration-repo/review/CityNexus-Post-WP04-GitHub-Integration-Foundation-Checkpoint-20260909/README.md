# CityNexus Post-WP04 Deployment + WP04 Hardening Checkpoint

Date: 2026-09-09  
Workspace: `D:\\moodle\\CityNexus`

## Contract and scope

The supplied `CityNexus-Post-WP04-GitHub-Integration-Foundation-20260909.zip` contract was read in its required order: `CODEX_AFTER_WP04_START_HERE.md`, `CODEX_WORK_SEQUENCE_AFTER_CURRENT_TASK.md`, `README.md`, and `00_ADOPTION_MATRIX.md`, followed by the referenced roadmap and validation notes. The subsequent deployment-hardening instruction was then applied in the same working tree. No SHA, file, or archive hash work was performed.

Accepted WP00-WP04 implementation was preserved. The foundation installer was dry-run first, reported no target conflicts, and was then applied. Existing mocks, fallback providers, lazy optional dependencies, and no-live-network defaults remain in place.

## Implemented

- Post-WP04 intelligence/provider/planning/trust foundation overlay.
- SQLite `foreign_keys=ON` on every new SQLite connection, including file-backed engines.
- Authoritative booking service derivation, requested-window availability filtering, exact activity/provider-slot matching, and service/slot evidence in provider calls.
- Duplicate active booking rejection before provider creation (`409 ACTIVE_BOOKING_EXISTS`).
- Semantic duplicate successful CAPTURE rejection across different idempotency keys (`409 TARGET_ALREADY_CAPTURED`); same-key replay and failed-capture retry remain supported.
- WP05 Journey execution: PLANNED→ACTIVE start, activity completion advancement, reproducible JourneyTwin projection, audit history, and mock event recording.
- Deterministic mock replanning proposal lifecycle (generate/list/get/accept/reject) with `ReplanDiff` evidence.
- Verified-facts deterministic fallback Copilot endpoint; AI is not authoritative for feasibility or commitment strength.
- Frontend-facing map/state/replan contracts and existing Playwright golden-scenario scaffolding are preserved; no unrelated dependency installation was performed.

## Gates

- Backend regression + foundation + hardening/WP05 tests: **104 passed, 2 dependency deprecation warnings**.
- Python compile check: **PASS** (`backend/app`).
- Ruff check: **PASS**.
- Ruff format check: **PASS** (73 files formatted).
- Canonical River Cruise booking/payment path: **PASS**.
- Duplicate booking/CAPTURE, multi-connection SQLite FK, JourneyTwin, event/history, and deterministic replan regressions: **PASS**.
- Real Valhalla/GraphHopper/Photon/Open-Meteo/DeepSeek/Stripe/WebAuthn/OR-Tools services: **not live-tested or required**.

## Review boundary

This package is the checkpoint for external GPT validation of the continued post-WP04 deployment and hardening stream. The default demo remains deterministic and provider-independent. No production credentials, live gateways, or mandatory external services were enabled.
