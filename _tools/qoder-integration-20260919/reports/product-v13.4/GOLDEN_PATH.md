# V13.4 Golden Path

1. A Journey with a selected PlanVersion and protected Haihe cruise commitment is loaded.
2. The user submits: “I prefer quiet indoor culture, low walking, and rain-friendly places near my protected Journey moments.”
3. The UI posts `mode=captured_replay` and displays `SEALED REAL REPLAY`.
4. The server resolves `UPCOMING_COMMITMENT` as the semantic anchor, executes bounded provider-backed discovery, and materializes real Tianjin candidates.
5. The official Tianjin Museum candidate is `Eligible` with normalized opening hours, `¥0`, and visible source evidence from `www.tjbwg.cn`. Candidates with unknown facts are visibly `Rejected` rather than silently treated as all-day/free.
6. Deterministic Compose selects a new PlanVersion while preserving the paid cruise commitment. The same PlanVersion is available to JourneyTwin, map, and authoritative execution surfaces.
7. The selected plan records `SEALED_REAL_REPLAY_WITH_EXPLICIT_SYNTHETIC_FALLBACK` because the captured Valhalla fact covers the selected provider Place while uncovered structural legs remain synthetic.

The browser proof was run through `/v8/discover` with Playwright CLI. The screenshot is outside the release archive at `output/playwright/v13.4-provider-truth-discovery.png` so browser state and generated artifacts are not shipped.
