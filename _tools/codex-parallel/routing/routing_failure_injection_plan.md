# Xiamen routing failure-injection plan

This is an owner-run plan. It does not enable or deploy Valhalla.

| Case | Injection | Required observation | Hard failure condition |
| --- | --- | --- | --- |
| One failed leg | Make Valhalla fail exactly one OD pair while a second candidate remains fully live | Only the candidate using the failed pair is excluded; the fully-live candidate may survive | Whole proposal set fails, or failed candidate receives a mock ETA |
| All candidates unavailable | Fail at least one required pair in every candidate | API/UI reports `MOBILITY_DATA_UNAVAILABLE` and offers no hard Accept action | Fabricated ETA, generic `NO_ALTERNATIVE`, or an acceptable proposal |
| Timeout | Delay `/route` beyond configured timeout | Controlled provider error; no fallback fact promoted to hard truth | Request hangs indefinitely or mock becomes `LIVE_PROVIDER_CAPTURE` |
| Malformed route | Return missing/non-numeric/negative `trip.summary.time` | Adapter rejects response | Invalid duration reaches plan feasibility |
| Partial matrix | Return null/missing cell in `/sources_to_targets` | Affected pair is unavailable; unaffected live pairs retain identity | Null becomes zero/default minutes |
| Provenance laundering | Supply `SEALED_*`, `CAPTURED_REPLAY`, `RUNTIME_CAPTURE`, or unknown provenance without explicit quality | Hard gate refuses it | Any ambiguous label maps to live |
| Mock isolation | Configure live provider, make one live request fail while mock has a value | Mock may support soft UX only; never a hard-feasible candidate | Mock value enters hard feasibility |
| Stale capture | Replay an old captured response outside the accepted evidence window | UI and API identify stale evidence; no real-time claim | Stale response is labelled live/current |

Evidence per case: exact frozen commit, sanitized request/response, provider logs, API response, candidate IDs, fact qualities, visible UI state, and exit code. Never store credentials.
