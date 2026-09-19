# V13.4 Gate Matrix

| Gate | Result | Evidence |
|---|---|---|
| Repeat identical discovery does not crash | PASS | First request completed; second request returned a domain response rather than a `ProviderCall` primary-key failure. IDs are now UUID audit-event IDs. |
| Captured replay has a usable provider candidate | PASS | Tianjin Museum candidate was materialized from the sealed snapshot and promoted from captured official observations. |
| Selected real-Place mobility fact is captured | PASS | Selected PlanVersion contains a `CAPTURED_REPLAY` Valhalla fact for the materialized real Place. |
| Mixed matrix is not called fully real | PASS | Runtime label is `SEALED_REAL_REPLAY_WITH_EXPLICIT_SYNTHETIC_FALLBACK`; `fully_provider_grounded=false`. |
| Paid Haihe cruise is preserved | PASS | Golden setup retains the selected/captured `place-river-cruise` C4 commitment. |
| Journey-derived anchor | PASS | Discovery chooses the server-owned Journey anchor and reports it in provider status; captured mode does not re-geocode the city. |
| Bounded Nominatim/Overpass behavior | PASS | Live adapters retain bounded radius/limit and captured mode reports both providers as not called. |
| Unknown opening hours remain unknown | PASS | Four uncompleted snapshot candidates remain rejected as `OPENING_HOURS_UNKNOWN`. |
| Unknown cost remains unknown | PASS | Uncompleted candidates remain rejected as `COST_UNKNOWN` or opening-hours unknown; no zero-cost inference is applied. |
| Official evidence promotion | PASS | `tjbwg-notice-20260913` and `tjbwg-ticketing-20260913` are captured observations with official source classes and URLs. |
| Unsourced model claims | PASS | Focused test proves model-only source IDs do not promote hours or price. |
| Safe DeepSeek diagnostics | PASS | Focused test covers `402 / insufficient_balance` without key or prompt leakage. |
| Candidate curation authority | PASS | Curation may rank only server-known candidate IDs. |
| Multi-query intent execution | PASS | Accepted bounded queries are executed and deduplicated before curation. |
| Mobility provenance | PASS | Every selected fact carries provider, captured time, provenance, and origin/destination identity. |
| Weather time locality | PASS with explicit uncertainty | Matching windows are sliced; out-of-window sealed replay is labelled uncertain. |
| UI provenance | PASS | Default is Sealed real replay; UI distinguishes sealed, live, synthetic, eligible, rejected, and source-backed candidates. |
| Journey-specific capture ownership | PASS | Candidate uniqueness is `(journey_id, provider_key, external_id)` while global `Place` identity remains shareable. |
| Broad backend regression | PASS | 388 passed, 2 skipped, 2 warnings. |
| Fresh-extract release gate | PASS | Fresh extraction ran 5 targeted backend tests (`5 passed`) and a clean `npm ci` + Vite production build. |
