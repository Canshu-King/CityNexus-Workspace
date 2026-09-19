# Provider and Model Status

All status labels below are explicit. Captured/replay is not called live, and unavailable credentials are not treated as successful live integrations.

| Capability | Status | Evidence / limitation |
|---|---|---|
| City operations / accommodation | `CAPTURED_REPLAY` | `data/v9/city_operations.json`, offer provenance and expiry/cancellation evidence. |
| Mobility graph | `CAPTURED_REPLAY` | Normalized five-mode facts with provider metadata and frozen geometry; used by CP-SAT/per-leg selection. |
| Amap adapter | `CONTRACT_PASS` | Regional provider selection, POI/route adapter boundary, CRS conversion and normalization tests. |
| Amap live Tianjin | `NOT_CONFIGURED` | `AMAP_WEB_KEY` was absent; bounded live call was not attempted. |
| GTFS-RT / OTP | `NOT_CONFIGURED` | `GTFS_RT_URL` and `OTP_BASE_URL` were absent. Realtime absence is `UNKNOWN_REALTIME`, not “on time.” |
| Long-distance reservation | `CAPTURED_REPLAY` | Provider-neutral rail/flight/coach/ferry reservation and schedule-change model. |
| Duffel sandbox | `NOT_CONFIGURED` | `DUFFEL_ACCESS_TOKEN` was absent; no airline live claim. |
| DeepSeek live semantic impact | `FAILED_BLOCKED` | Bounded smoke loaded the temporary key into the child process only. Result: deterministic fallback, no model-backed autonomy claim. |
| Native deterministic fallback | `PASS` | Server-side impact fallback, deterministic feasibility and autonomy-envelope policy are fully exercised. |
| Hermes MCP V2 surface | `PASS` | Eleven typed inspect/plan/action tools and principal boundary are protocol-tested; `agent-mcp` suite passed `6`. |
| Hermes CLI/model-backed E2E | `NOT_RUN_EXTERNAL` | Hermes binary/provider was not available; no external Hermes claim is made. |
| OpenInference/Phoenix seam | `IMPLEMENTED_NOT_CONFIGURED` | Trace spans and provider provenance are persisted; no external collector endpoint was configured. |
| Promptfoo-compatible evaluation | `13/13 PASS` | `LOCAL_DETERMINISTIC_ADAPTER`, `model_backed=false`; adversarial decisions are replayable, not a live model evaluation. |

The temporary `TEMP_DEEPSEEK.env` was read only from the staging directory into a process environment for the bounded smoke. It is excluded from reports, source and the final archive.
