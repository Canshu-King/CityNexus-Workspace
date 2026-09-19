# CityNexus V19 Traveler Capability + Accessibility

## Result

The capability slice is implemented in the V18.3 worktree. Explicit traveler and journey capabilities now have a canonical vocabulary, severity, scope, confirmation state, provenance, TravelerTwin projection, Copilot semantic exposure, mission-plan awareness, deterministic feasibility hooks, and candidate-ranking hooks.

The release is **not** marked Native-Hermes connected. The convergence environment reports `NATIVE_DEEPSEEK_TOOL_LOOP`; the Hermes gateway is not configured or reachable, so no new native Hermes capability-aware run is claimed.

## Implemented

- Capability contract and conservative natural-language extraction in `backend/app/capabilities.py`.
- Durable `traveler_capabilities` records with explicit confirmation boundary.
- Traveler and Journey capability APIs, including `/confirm` endpoints.
- TravelerTwin explicit capability projection; learned behavior remains soft and cannot create hard accessibility needs.
- SemanticEnvelope optional capabilities with server canonicalization and local safety-net extraction.
- Mission `CAPABILITY_AWARE` objective and explicit `inspect_capabilities` step.
- Deterministic gate checks for step-free/stairs evidence, walking limits, rest windows, and related context.
- Experience payload and Twin UI now render real capability records instead of guessed strengths.
- OpenAPI parity updated for the new endpoints.

## Truth boundary

Unknown accessibility evidence is treated as unverified and produces `NEEDS_LIVE_EVIDENCE`; it is never treated as accessible. Provider/frozen evidence remains authoritative. Hermes/DeepSeek cannot create accessibility facts or mutate protected commitments.
