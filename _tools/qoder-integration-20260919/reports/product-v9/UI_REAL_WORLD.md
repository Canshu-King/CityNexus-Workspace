# V9 Real-World UI Evidence

## Traveler-first Live Journey

The primary Live Journey surface now prioritizes:

- `NOW` — the current Activity or arrival state;
- `NEXT` and `LEAVE BY` — the next operation and slack;
- `NAVIGATE` — a provider-specific deep link (Amap WGS84 URI for China journeys, Google fallback elsewhere);
- `RISK` — disruption/Guardian state.

Technical route, freshness, walking, transfers and cost details are behind an `EVIDENCE` drawer. The map uses backend/provider GeoJSON with dynamic Activity, hotel, protected Commitment, current-leg, disruption and permitted user-location markers. No CSS route or static attraction pin is used as travel evidence.

## Accessibility and mobile

The V9 browser scenario checks mobile Now/Next/LeaveBy/Navigate composition, 44px-class touch targets, contrast threshold, responsive navigation and real browser offline reload. The shell provides English/Chinese copy through `frontend/src/i18n/tripOperations.ts`; the language control switches the product navigation seam without changing domain facts.

## PWA and offline behavior

`manifest.webmanifest` declares standalone display; `sw.js` caches the app shell and deliberately does not cache API responses. IndexedDB stores the next 24 hours of authoritative snapshot data. Offline mode is read-only, shows freshness, and disables financial actions. No background GPS tracking is claimed.

## Curated visual evidence

- [Live Journey mobile](ui/live-journey-mobile.png)
- [Offline Journey mobile](ui/offline-journey-mobile.png)

Both images were captured by the V9 Playwright scenario and are included in the final archive. Raw Playwright artifacts are excluded.
