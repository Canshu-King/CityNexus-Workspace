# Blockers and optional boundaries

No blocker prevented the deterministic overnight gate.

1. **Live Valhalla unavailable (non-blocking).**
   `CITYNEXUS_LIVE_VALHALLA_URL` is not configured, so the live smoke was
   skipped. The HTTP adapter, malformed/timeout behavior, MobilitySnapshot
   capture, and mock fallback are tested offline.
2. **DeepSeek/LiteLLM credentials unavailable (non-blocking).**
   No API key was present. The LiteLLM boundary, verified-facts contract,
   and deterministic fallback are tested without a live model.
3. **OR-Tools not installed (non-blocking).**
   The optional candidate-generator boundary and common verified ranking path
   are covered; OR-Tools is intentionally not a mandatory dependency.
4. **Frontend remains a deterministic contract shell (known limitation).**
   The Journey Mode and Playwright flow are runnable offline, but real backend
   API wiring, live map tiles, and provider route geometry remain a follow-up
   integration step.

No secrets, API keys, live payment gateways, or production providers were
introduced. No destructive Git operation was used.

