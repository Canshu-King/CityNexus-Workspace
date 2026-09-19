# Test Results

Focused V19/V17/V18.2 gate: **16 passed, 2 warnings**.

V18.3 convergence gate: **4 passed**.

OpenAPI parity after adding capability routes: **1 passed**.

Frontend production build: **passed** (`vite build`, PWA generateSW completed).

One broad backend regression: **421 passed, 3 skipped, 10 failed, 1 setup error**. The failures are baseline/runtime-sensitive Guardian autonomous expectations, DeepSeek fallback expectations while a credential is configured, V8 model-provider behavior, and a Python 3.10 `StrEnum`/skipif environment issue; they do not represent a fabricated V19 capability proof. The added capability tests and the existing semantic/agent/convergence gates pass.

Native Hermes capability-aware run: **not executed/proven**. `/api/v1/agent/runtime-status` reported `runtime_identity=NATIVE_DEEPSEEK_TOOL_LOOP`, `native_mcp_proven=false`, and `hermes_native_gateway.ready=false`.
