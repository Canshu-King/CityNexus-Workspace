# Test Results

- V19.1 focused capability/evidence/API tests: **7 passed**.
- Contract plus V18.3 convergence focused gate: **15 passed**.
- Frontend `npm run build`: **passed**; Vite/PWA generated production assets.
- Desktop Playwright smoke: **passed**; Copilot page loaded and exposed mission controls.
- Mobile Playwright smoke at 390x844: **passed** after backend startup; mobile control-tower content rendered.
- Runtime status: backend/database healthy; DeepSeek configured; native Hermes gateway `ready=false`, `configured=false`, `native_mcp_proven=false`.
- Broad backend regression (single convergence run): **424 passed, 10 failed, 3 skipped, 1 setup error**. Failures are pre-existing environment/provider/Guardian expectation drift, DeepSeek responsiveness, and the known malformed skip condition; no claim of broad green status is made.
