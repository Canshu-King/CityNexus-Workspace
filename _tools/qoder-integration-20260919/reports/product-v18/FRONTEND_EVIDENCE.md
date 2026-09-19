# V18 Frontend Evidence

The final browser checks used a freshly created sealed Tianjin Journey after
the convergence test suite had completed.

Desktop at 1440×900:

- grouped TODAY / PLAN / TRAVEL / SYSTEM navigation rendered;
- navigation labels include Copilot and Recovery;
- persistent Copilot dock opened;
- `Why is this Journey arranged this way?` returned `EXPLAIN_PLAN`;
- response showed `Execution: DIRECT`, matching the actual server runtime;
- response stated that no selected PlanVersion existed and that nothing was
  mutated.

Mobile at 390×844:

- bottom navigation rendered Today / Map / Copilot / Wallet / Me;
- Copilot stayed available above the bottom navigation;
- `What if I leave one hour later?` returned `WHAT_IF`;
- response stated that the preview changed nothing because no selected
  authoritative PlanVersion existed.

Screenshots are included in the release evidence tree:

- `output/playwright/v18-final-desktop.png`
- `output/playwright/v18-final-mobile.png`

The Copilot rail is empty for direct semantic requests and only appears when a
real `agent_run` is returned. When a native run exists, its EventSource is
bound to the server-proxied Hermes SSE endpoint; no timer fabricates progress.
Route and map transitions honor reduced-motion preferences.
