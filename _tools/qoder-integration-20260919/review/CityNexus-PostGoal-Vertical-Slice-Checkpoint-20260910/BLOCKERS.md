# Remaining Blockers and Non-Blocking Notes

- No blocker remains for the Post-Goal semantic repair or backend-connected
  vertical-slice Stop Gate.
- Live Valhalla smoke is skipped because CITYNEXUS_LIVE_VALHALLA_URL is not
  configured. The deterministic Mock/Frozen Snapshot path remains the default.
- OR-Tools, LiteLLM/DeepSeek, and routingpy remain optional and were not
  installed or promoted to mandatory dependencies in this run.
- The map is a deterministic presentation surface; no live MapLibre tiles or
  external map service are required.
- The two test warnings are upstream FastAPI/Starlette TestClient and AnyIO
  deprecations.
- No secrets, live payments, live external Providers, hash manifests, or
  generated dependency directories are part of the review package.
