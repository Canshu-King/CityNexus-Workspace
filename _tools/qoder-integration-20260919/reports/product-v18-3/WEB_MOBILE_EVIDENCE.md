# Web and mobile evidence

## Desktop

The Copilot truth strip remains Semantic: DeepSeek, Execution: DIRECT or
HERMES_NATIVE_MCP, and Truth: CityNexus. Hermes is shown only after a real
native lifecycle/tool event. The ordered timeline preserves tool events,
friendly labels, safe raw disclosure, run/mission observability, proposal
state, protected-commitment badges, approval controls, and CityNexus Stop.

The desktop captures are output/playwright/desktop-native-hermes.png and
output/playwright/v183-desktop-hermes.png; the final 1440x900 shell capture is
output/playwright/v183-desktop-1440.png. The 1280x720 and 1440x900 checks had
no horizontal overflow.

## Mobile

The existing Today / Map / Copilot / Wallet / Me navigation remains. At
390x844 and 430x932 the Copilot route uses a compact activity sheet showing the
current mission, current status, runtime identity, proposal/commitment state,
and Stop/approval actions. Full real history is expandable; it is not a
desktop console squeezed into the viewport.

Captures:

- output/playwright/mobile-390-native-hermes.png
- output/playwright/mobile-430-native-hermes.png
- output/playwright/v183-mobile-390.png
- output/playwright/v183-mobile-430.png

The timeline uses state-driven CSS motion only. Reduced-motion removes route,
step, and view-transition animations. Live disconnects show stale/unavailable
state while retaining received events; no unrelated fixture is replayed. The
320x720 sanity check also reported no horizontal overflow.
