# V8 UI before / after

## Evidence

Before:

- [V7 desktop baseline](ui/before/desktop-v7.png)
- [V7 mobile baseline](ui/before/mobile-v7.png)

After:

- [Journey Hub desktop](ui/after/journey-hub-desktop.png)
- [Trip Studio desktop](ui/after/trip-studio-desktop.png)
- [Stay Explorer desktop](ui/after/stay-explorer-desktop.png)
- [Intelligence desktop](ui/after/intelligence-desktop.png)
- [Live Journey mobile](ui/after/live-journey-mobile.png)
- [Mobility sheet mobile](ui/after/mobility-sheet-mobile.png)
- [Agent composer mobile](ui/after/agent-composer-mobile.png)

## Product change

The old surface exposed a long engineering/control dashboard. V8 now has a map-first Journey shell with a calm hierarchy: the current Journey, date anchors, protected margin, plan health, and the next action are visible before advanced evidence. Desktop navigation separates Journey Hub, Trip Studio, Stay, Bookings, Intelligence, Traveler Twin, and AI desk. The mobile composition is intentionally different: Journey, Map, AI, Bookings, and Me are persistent bottom destinations.

The new UI uses a shared token set and semantic states for captured evidence, protected commitments, risk, and policy. Loading, error, focus-visible, reduced-motion, and unavailable-provider states are represented. The Mobility sheet discloses time, cost, walking, transfers, exposure, and reliability without inventing an unknown fare.

The V8 frontend remains Vite + React. It is split into `app/`, `components/v8/`, `features/stay/`, `features/mobility/`, and `features/agent/`; the V7 legacy entry remains at `/` for regression compatibility.

