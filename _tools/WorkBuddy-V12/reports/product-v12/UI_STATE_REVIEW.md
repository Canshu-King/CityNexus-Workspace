# UI and State-System Review

## V12 browser checkpoint

Clean Playwright session `v12final` against the live local Vite/FastAPI pair verified:

- `/v8/authoritative` renders the authoritative Journey panel;
- frozen evidence badge and server execution truth are visible;
- live action control changes the Activity state;
- pointer reorder changes the draft only;
- preview renders `Impact preview passed`;
- accept creates `PlanVersion 2 · MANUAL`;
- refresh shows `same evidence`, `No draft changes`, and readable Activity titles;
- the final clean session reported zero console errors.

Curated screenshot: `reports/product-v12/evidence/v12-authoritative-trip-studio-final.png`.

## Regression surface

`npm run test:e2e -- --reporter=line` passed all 15 existing tests, including:

- V4/V5/V6/V8/V9/V10 product flows;
- TravelerTwin, Agent Gateway, Guardian, reload, and route/feed evidence;
- mobile 390×844 navigation/composition;
- axe accessibility scan;
- mobile layout/server-error budget.

## Map resize probe

At desktop size the MapLibre canvas measured 393×334 inside a 394.75×336 panel. After resizing to 390×844 it measured 354×245 inside a 356×247 panel. The non-zero, near-container dimensions confirm the ResizeObserver/map.resize lifecycle remains active through viewport change.

## State catalog

V12 primitives and MSW-backed stories cover READY, LIVE, DISRUPTED, RECOVERING, APPROVAL_REQUIRED, OFFLINE, and COMPLETED through the execution, risk, impact, offline, Edge, and live-journey components.
