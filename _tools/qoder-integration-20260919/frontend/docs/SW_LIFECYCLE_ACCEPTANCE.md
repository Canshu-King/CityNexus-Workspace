# Service Worker Lifecycle Acceptance — Mission 003 A4

Status: candidate patch for Commander review. This branch is not an authoritative product release.

## Product contract

1. Development does not register the production service worker. If a same-origin worker is left behind from an earlier preview, development unregisters it on load so it cannot hijack Vite/HMR modules.
2. Production registers only `/v10-sw.js`, with `updateViaCache: "none"`.
3. A controller transition on an already-controlled page triggers one safety reload, keyed by the old->new controller URL pair, so an old HTML shell cannot keep running against a new asset graph.
4. The checked-in `/sw.js` is a recovery/legacy worker. It is destination-aware:
   - `script`, `style`, `worker`, and `serviceworker` requests are network-only;
   - document navigation may use an HTML fallback;
   - images/fonts may use same-request cache fallback;
   - API and cross-origin requests are never intercepted.
5. Recovery caches are versioned. Activation removes older CityNexus recovery caches and the known poisoned legacy cache names.
6. The generated Workbox worker uses versioned runtime caches, accepts only HTTP 200 responses, and never caches opaque/status-0 responses.
7. Vite content-hashed scripts/styles use `StaleWhileRevalidate`; documents use `NetworkFirst`. Worker scripts are not runtime-cached by the Workbox rule.
8. SPA fallback is navigation-only. API paths, `/assets/`, and a narrow allowlist of known static-resource extensions are denied from `navigateFallback`; dotted SPA route segments are not rejected merely because they contain a period.

## Why the document timeout is 8 seconds

The previous 3-second document timeout was observed to return a stale shell on real mobile/tunnel use. Mission 003 also measured a valid user operation at roughly 3.6 seconds, showing that a 3-second budget is below normal end-to-end mobile latency in this environment. The candidate is therefore 8 seconds: more than twice that observed successful latency while still bounding a dead navigation.

This value is not accepted merely because it appears in config. CI must measure it on the production build:

- delay only the document response by 4 seconds: navigation must wait for and use the fresh network document, proving the old 3-second fallback no longer fires;
- delay the document response beyond 8 seconds (recommended 9–10 seconds) after a current-version document has been cached: the worker may serve that same-version cached document;
- in both cases, `#root` must become non-empty and executable resources must never receive `text/html`.

Prefer delaying the local preview server/proxy response rather than `page.route()` for this measurement. Requests made by a Service Worker are not reliably represented by ordinary page routing, so a server-side delay or Chromium network emulation is the honest test.

## Production Playwright command

Build and run the dedicated service-worker suite:

```powershell
cd frontend
npx playwright test -c playwright.sw.config.ts
```

For an authoritative run, use the same isolated backend/run-id/database environment required by the existing CityNexus authoritative E2E policy.

The dedicated config sets:

```ts
use: {
  baseURL: "http://127.0.0.1:<owned-port>",
  serviceWorkers: "allow",
}
```

Do not run this gate with `serviceWorkers: "block"`; that mode is useful for request interception but cannot prove lifecycle behavior.

## Old worker -> new deployment regression

The executable test `e2e/qoder-sw-lifecycle.spec.ts` uses a fresh `browser.newContext({ serviceWorkers: "allow" })`.

The important sequence is:

1. Open a same-origin non-app document.
2. Test setup only: unregister previous workers and clear caches to establish a deterministic starting point.
3. Register `/sw.js` at scope `/` and verify it controls the page.
4. Seed the historical cache names with stale shell/module-shaped data.
5. From this point onward, **do not call `unregister()` or `caches.delete()`**.
6. Navigate to `/v8/live`. Production `main.tsx` registers `/v10-sw.js`.
7. Wait for the controller URL to become `/v10-sw.js`.
8. Assert `#root` is non-empty, reload, and assert it is still non-empty.
9. Assert known legacy cache names are gone.
10. Separately place the recovery worker offline and request uncached script/style/worker resources. All must fail as executable requests and no observed response may be `text/html`.

For a stronger two-build CI simulation, keep the origin and port stable while the static server switches its root from an archived bad `dist-old` artifact to the candidate `dist-new` artifact. Reuse the same browser context across the switch. Do not use manual cache clearing after the switch. The candidate passes only if the browser updates its worker and the application recovers by itself.

Useful Playwright APIs:

```ts
const context = await browser.newContext({ serviceWorkers: "allow" });
const page = await context.newPage();

const workersBefore = context.serviceWorkers().map((worker) => worker.url());
const nextWorkerPromise = context.waitForEvent("serviceworker");

// deploy/switch the static root here

await page.reload({ waitUntil: "domcontentloaded" });
const nextWorker = await nextWorkerPromise;
console.log(nextWorker.url(), workersBefore);

await page.waitForFunction(
  () => navigator.serviceWorker.controller?.scriptURL.includes("/v10-sw.js"),
);
```

If network delay must be emulated at Chromium level, use a CDP session after the initial page load; server-side document delay remains preferable because it targets only navigation and avoids slowing every API/asset request.

## Frozen-contract declaration

This candidate changes only frontend service-worker registration/caching and its acceptance harness. It does **not** change or weaken:

- mobility provenance or `fact_quality` propagation;
- `HARD_FEASIBLE_QUALITIES`;
- database single-ACTIVE-plan invariants;
- stale-cursor fail-closed semantics;
- idempotency semantics;
- physical identity / SAME / AMBIGUOUS semantics;
- C4 commitment protection;
- authoritative E2E acceptance policy.

The new Playwright config is additive and production-only. It does not replace the existing authoritative product suite.
