# CityNexus V18 Native Hermes Journey Experience

Captured: 2026-09-15 00:00 Asia/Shanghai

Target artifact: `CityNexus-V18-Native-Hermes-Journey-Experience-20260914.zip`

V18 is implemented against the current CityNexus worktree. The V17
SemanticEnvelope remains the semantic boundary: DeepSeek can interpret human
language, while CityNexus owns facts, identifiers, timestamps, money,
commitments, feasibility, authorization, and mutations.

The main correctness repair closes the future-event gap. An asserted future
disruption is resolved only from an authoritative Journey end, Booking,
Commitment, or Activity fact. A unique target produces an Event at that
authoritative future time. An unresolved target produces a review candidate
with `occurred_at: null` and no database Event, so it cannot silently become a
current disruption or bind to the current Activity.

`VERIFY_FACT` now executes a bounded source-evidence path when the configured
DeepSeek web-search provider is available. Captured observations remain
non-authoritative and require review; the verification path never creates a
city Event by itself.

The official Hermes Agent 0.21.2 is installed in the Windows user profile.
A dedicated `citynexus` profile outside the repository points Hermes at the
CityNexus MCP V2 server and allowlists eleven tools. CityNexus exposes a
server-side native Runs capability check, run submission, run status, and SSE
progress proxy. The frontend's progress rail consumes the returned SSE URL
when a native run exists. The current environment has no configured
DeepSeek credential and no loopback `API_SERVER_KEY`, so native Hermes model
execution is honestly marked **NOT CONFIGURED**; no native inspect, PLAN_ONLY,
or policy-gated model session is claimed.

The frontend now has grouped desktop navigation, a persistent Copilot dock,
server-derived runtime labels, real-run progress state, reduced-motion route
transitions, MapLibre transition timing, and mobile Today / Map / Copilot /
Wallet / Me navigation. A fresh desktop browser flow completed Journey setup
and Copilot `EXPLAIN_PLAN`; a fresh mobile flow completed read-only
`WHAT_IF`. Both flows showed `DIRECT` because that was the actual server
runtime.

Validation completed:

- V18 semantic, verification, Hermes client, V17, contract, and MCP focused
  checks: **22 passed** in the final combined focused run;
- V16 integration, V15 Copilot, and V14 recovery/trial checks: **20 passed**;
- broad backend regression: **421 passed, 2 skipped, 2 warnings**;
- frontend production build: **Vite 7.3.6, 1,904 modules transformed**;
- desktop and mobile Playwright flows: **PASS**.
- fresh-extract runtime gate: **22 passed, 2 warnings**, with 474 ZIP entries
  and no forbidden release entries or secret-shaped names.

The two warnings are existing FastAPI/Starlette/httpx deprecations. The
release archive is assembled from an allowlisted staging tree and excludes
credentials, databases, caches, virtual environments, frontend build output,
old incoming trees, browser state, logs, and nested archives.
