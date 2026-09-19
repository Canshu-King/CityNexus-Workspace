# Safe future code-splitting candidates

No source changes are included. Order candidates by benefit/risk and implement one at a time.

| Priority | Boundary | Why it is safe/useful | Risk and focused gates |
| --- | --- | --- | --- |
| P1 | Booking/inbox QR scanner (`BookingArtifactScanner`, `@zxing/browser`) | Device-only feature; no reason to load on Today/Live first paint | Camera permission, import/manual fallback, offline error boundary |
| P1 | Trip Studio (`V12TripStudioPanel`, `SortableActivityList`, `@dnd-kit/*`) | Editing route is separate from execution views | Drag/drop state, keyboard accessibility, plan version persistence |
| P1 | Discovery/Plan-with-AI/Hotels/Stay Explorer | Setup/planning surfaces are not current-journey execution | Journey creation, selected plan, return navigation |
| P2 | Inbox workbench and secondary history/control-tower surfaces | Large, infrequent feature groups | Deep-link and stale-session loading states |
| P2 | Split locale dictionaries from provider logic | ~65 KB source contains both languages | Instant language switch, offline locale availability, no key drift |
| P2 | V8 route component registry with `lazy()` per non-core route | `V8Experience` eagerly imports almost every feature | Keep Today and Live core synchronous initially; add per-route error/loading boundary |
| P3 | CSS by feature after JS boundaries stabilize | Global CSS is 161 KB raw | Avoid FOUC and token-order changes; visual regression matrix |
| Policy | Exclude MapLibre from Workbox precache and runtime-cache on demand | Fresh install avoids ~1.05 MB raw map chunk | Product decision: offline map capability may regress; test offline shell and map empty state |
| Last | Stable vendor `manualChunks` for React/query/state | Can improve cache reuse after feature splits | Avoid overfragmentation/circular chunks; inspect Rollup graph |

Recommended experiment: lazy-load QR scanner and Trip Studio first, then measure. Keep Today/Live behavior untouched during the first experiment. MapLibre is already isolated; do not spend the first optimization pass re-solving it.
