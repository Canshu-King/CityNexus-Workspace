# CityNexus V10 frontend adoption ledger

## 21st.dev Codex / MCP

- User-profile persistence: `API_KEY_21ST` is present in the Windows **USER** environment; the value is never written to this repository or any product artifact.
- MCP verification: `https://21st.dev/api/mcp` initialized successfully with protocol `2025-03-26`, server `21st`, version `0.1.1`, and returned 34 tools.
- Active design use: searched the 21st MCP for `calm travel itinerary live journey next step mobile route evidence`, then inspected component `Card / Travel Route Card` (id `7639`).
- Adapted pattern: the Live Execution rail uses the reference's strong route metric / supporting evidence hierarchy, but no source code was copied. The 21st response did not expose a license grant for the component, so CityNexus uses an independent implementation.
- Marketplace status: the official repository is an older marketplace layout that the installed `codex-cli 0.128.0` rejected as an incompatible marketplace manifest. This is recorded as an external compatibility limitation; direct MCP use remains verified.

## Runtime dependencies

- `openapi-typescript`: generated `frontend/src/generated/api.ts` from `contracts/openapi.yaml`.
- `@tanstack/react-query`: owns server-state reads for V10 ExecutionClock and WebObservation surfaces.
- `vite-plugin-pwa` + Workbox: emits an installable V10 service worker and manifest.
- `dexie`: stores the read-only offline Journey snapshot in IndexedDB.
- `@zxing/browser`: reserved for deterministic QR/barcode decoding in the Inbox capture surface.
- `lucide-react`: used for the execution rail's status icons.

No dependency was allowed to expand Agent authority, budget, payment, or protected Commitment scope.
