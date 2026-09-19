# CityNexus V19.2 Real-Phone SHADOW Trial

1. Start backend from `backend` with `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.
2. Start the Vite app with `npm run dev -- --host 0.0.0.0`, or serve the production build through an HTTPS LAN tunnel.
3. On the phone, use HTTPS for PWA install and geolocation. Point the frontend API base at the LAN/tunnel backend address.
4. Install the PWA from the browser menu and launch standalone. Verify Today, Map, Copilot, Wallet, and Me navigation.
5. Grant location permission. If denied, use the visible permission/error state; never treat missing GPS as verified location.
6. Exercise Copilot in SHADOW mode with simulated booking/payment only. Compare the proposed plan with reality and record mismatches.
7. For a short SSE disconnect, reload/reopen Copilot and verify run state/history remains truthful without duplicate events.
8. Collect browser console, backend logs, run id, and runtime-status output for issues. Never include API keys.
9. Reset safely with `POST /api/v1/demo/reset` before another trial Journey; do not reset a real production Journey.

Required viewports for preflight: `390x844` and `430x932`. This trial does not authorize production payment, unattended mutation, or safety-critical accessibility decisions.
