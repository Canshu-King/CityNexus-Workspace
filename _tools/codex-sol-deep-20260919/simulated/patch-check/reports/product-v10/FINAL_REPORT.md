# CityNexus V10 final checkpoint report

## Outcome

The V10 product path is implemented and regression-green under deterministic local/replay execution. It preserves V9 and adds a DeepSeek Responses boundary, multimodal Journey Inbox, truthful provider capture/replay, generic selected-POI composition, actual-time execution truth, PWA/IndexedDB offline state, Web Push capability/fallback, Storybook, accessibility, and a polished mobile Live/Inbox surface.

The honest completion label is `V10_FLAGSHIP_E2E=PASS_REPLAY_DETERMINISTIC_CONDITIONAL_EXTERNALS`: the flagship is proven with deterministic/replay fixtures and mocked model seams, while live external model/provider capabilities remain separately labelled below.

## Validation

| Check | Result |
|---|---|
| V10 current gaps | 10/10 passed |
| Backend regression | 343 passed, 2 skipped, 2 warnings |
| Playwright V5/V6/V8/V9/V10 | 15 passed |
| MCP boundary | 6 passed |
| Frontend production build | passed; 1,948.56 KB JS / 544.33 KB gzip warning |
| Storybook build | passed; Storybook manager chunk warning recorded |
| axe accessibility | passed with zero violations |
| Product-quality budget | passed via Playwright equivalent; Lighthouse CLI not run |
| Ruff / compileall | passed |
| Local adversarial adapter | 13/13 passed; not model-backed |

## Security and packaging

`API_KEY_21ST` remains in the Windows USER environment only. The temporary DeepSeek key was loaded only into child-process memory during probes. Neither key, environment file, database, dependency directory, browser cache, raw screenshot artifact, or nested archive is included in the final product ZIP.

## External limitations

- Official DeepSeek probe: TEXT 200, WEB_SEARCH 200, VISION 200; FUNCTION 400 when forced tool choice was combined with thinking. CityNexus handles the tool turn by sending reasoning effort `none` and preserving continuation items.
- Web search is non-authoritative. The live response used for the checkpoint produced no source observation; CityNexus does not invent a URL for a model summary.
- Hermes is an implemented optional adapter but no Hermes endpoint/key is configured; native DeepSeek remains the fallback.
- Live Valhalla/Amap and OTP/GTFS-RT are not configured. Synthetic mobility is labelled `SYNTHETIC_FIXTURE`; captured replay is checksum-validated.
- VAPID is not configured, so the default notification capability is `RECORD_ONLY`; the optional pywebpush path is implemented.
- DeepSeek visual review cycle 2 failed the strict external JSON parse. Cycle 1 findings were applied; axe and Playwright remain authoritative measurable gates.

## Deliverable

`CityNexus-V10-DeepSeek41-LiveExecution-UI-Final-20260913.zip` is the curated product checkpoint produced after this report set is written and fresh-extract verified.

