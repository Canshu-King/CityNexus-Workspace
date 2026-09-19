# Web and mobile experience

## Desktop

Copilot now keeps the three-part truth strip visible:

```text
Semantic: DeepSeek    Execution: DIRECT or HERMES_NATIVE_MCP    Truth: CityNexus
```

Native missions render the ordered events received from the backend/Hermes
stream. Tool names are friendly-localized (for example, `inspect_journey`
becomes “Inspect current Journey”); safe raw metadata is behind a Runtime
details disclosure. The panel shows run ID, mission ID, tool count, current
tool, duration, proposal/commitment state, and a real Stop control. Timelines
are cached locally only to survive panel close/navigation; the server audit
timeline remains authoritative.

The desktop Playwright capture is
`output/playwright/desktop-native-hermes.png`. The run displayed real lifecycle
events and was stopped through the CityNexus proxy; completed-tool events no
longer terminate the SSE connection prematurely.

## Mobile

The existing bottom navigation remains:

```text
Today · Map · Copilot · Wallet · Me
```

The Copilot route uses a compact activity sheet with the current mission,
current status, proposal/commitment summary, and approval/Stop actions. The
full event list can expand, and it is not replaced with a fixed four-step rail.
The 390x844 and 430x932 captures are:

- `output/playwright/mobile-390-native-hermes.png`
- `output/playwright/mobile-430-native-hermes.png`

Both viewports were exercised in the final Playwright session. CSS transitions
remain state-driven and are disabled for `prefers-reduced-motion`; no animation
was used to imply model work.
