# CityNexus V18 Native Hermes Journey Experience

Status: **IMPLEMENTED / backend and frontend convergence gates green / native model run not configured**

V18 keeps the V17 DeepSeek SemanticEnvelope boundary and adds authoritative
future-event targeting, bounded VERIFY_FACT evidence capture, an official
Hermes Runs/SSE server boundary, and the traveler-first desktop/mobile
Copilot experience.

CityNexus remains authoritative for provider facts, IDs, timestamps, money,
commitments, feasibility, policy, and mutations. The UI shows the runtime
identity returned by the server. The current process reports `DIRECT` for
Copilot and `NOT_CONFIGURED` for native Hermes because no provider credential
or loopback Hermes API server key is configured.

See `reports/product-v18/FINAL_REPORT.md` and `reports/product-v18/GATE_MATRIX.md`.
# Current runtime status — 2026-09-15

Native Hermes is live and proven through the CityNexus Copilot path. The
official `citynexus` profile uses DeepSeek `deepseek-v4-flash`; the loopback
Runs API is reachable and a real MCP tool event was observed. Runtime identity
is live-state based and falls back honestly if the gateway is down.
