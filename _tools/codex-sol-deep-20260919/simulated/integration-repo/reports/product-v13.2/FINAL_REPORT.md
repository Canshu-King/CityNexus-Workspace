# CityNexus V13.2 Final Report

## Outcome

The V13.2 Intelligent Journey Memory slice is implemented in the authoritative worktree. The product path is now:

`artifact -> DeepSeek semantic interpretation -> role/confidence/semantic target -> deterministic identity/conflict gate -> smart intake/review -> Journey Memory -> protected Commitment/anchor -> authoritative Compose`

The V13.1.2 structural reservation identity baseline remains green. No V13.3 or V14 work was added.

## Delivered

- DeepSeek text and vision prompts now request semantic role, role confidence, payment/refundability, commitment suggestion, semantic target, Journey match, uncertainty, provenance, and a concise rationale.
- The server supplies bounded Journey context to the interpreter and resolves semantic targets against server-owned Journey activities and Places.
- `AUTO_APPLY`, `APPLY_WITH_NOTICE`, `NEEDS_REVIEW`, and `REQUIRES_CONFIRMATION` decisions are persisted with deterministic reasons and conflicts.
- Unknown roles do not silently become ARRIVAL. MID_TRIP imports require a non-structural semantic target.
- Added draft correction via `PATCH /api/v1/journeys/{journey_id}/inbox/{draft_id}`.
- Added policy-gated `POST .../smart-apply` and `GET /api/v1/journeys/{journey_id}/memory`.
- Confirming an artifact now initializes the Journey trip context when necessary, so artifact-first Journeys retain verified anchor coordinates before authoritative Compose.
- Added Journey Memory UI with role/confidence/target/rationale evidence, corrections, smart apply, and a protected timeline.
- QR/barcode output is passed into the same text extraction path through the existing scanner callback.
- OpenAPI runtime parity includes all new V13.2 routes.

## Gate status

| Gate | Result | Runtime label |
|---|---:|---|
| V13.2 semantic intake + Golden flow | 3 passed | `LOCAL_TEST_RUNTIME` / `SYNTHETIC_DEEPSEEK_FIXTURE` |
| V13.1.2 structural reservation identity | included in backend regression | `LOCAL_TEST_RUNTIME` |
| Full backend regression | 380 passed, 2 skipped | `LOCAL_TEST_RUNTIME` |
| Frontend production build | passed | `LOCAL_VITE_BUILD` |
| Browser product E2E | passed | `LOCAL_CHROMIUM` / `UI_PROVIDER_REPLAY` |
| Fresh-extract backend targeted gate | 41 passed | `FRESH_EXTRACT_LOCAL_TEST_RUNTIME` |
| Fresh-extract frontend build | passed | `FRESH_EXTRACT_LOCAL_VITE_BUILD` |

The browser evidence used a deterministic route stub for the provider response so the UI flow was reproducible without placing a live API key in the repository. It proves the semantic draft, Memory timeline, review surface, and smart-apply interaction; it is not claimed as live external DeepSeek evidence.

## Release

Target artifact: `CityNexus-V13.2-Intelligent-Journey-Memory-20260913.zip`

The release ZIP was extracted into a clean staging directory and executed independently. The fresh package passed the targeted backend gate and built the frontend from the included lockfile.

Secrets, databases, caches, virtual environments, frontend build output, test output, and nested historical archives are excluded from the release staging process.

Elapsed-time note: the task was not started with a wall-clock budget timer, so this report does not invent a total task duration. The reported labels identify the actual execution runtime for each gate.
