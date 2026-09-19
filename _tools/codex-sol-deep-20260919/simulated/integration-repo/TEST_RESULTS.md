# CityNexus V19.2.1 Test Results

Date: 2026-09-15

- Focused V19 capability, contract, V12, V13.1.2, and V9 regression: **24 passed**.
- Frontend production build (`npm run build`): **passed**. Vite/PWA output generated; existing large MapLibre chunks remain measurable build warnings.
- Local runtime-status probe: backend was not running during convergence (`connection refused`); no Hermes execution claim is made.
- Physical real-phone SHADOW trial: **not performed in this environment**.
- Full repository regression: **not a valid product gate**. One run collected historical `_fresh_*`, `review/`, and renderer snapshots and stopped at 8,413 import-collection errors (`ModuleNotFoundError: app`); current-tree focused tests remain green.
