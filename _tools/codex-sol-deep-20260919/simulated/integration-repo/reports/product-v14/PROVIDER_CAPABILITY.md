# Provider Capability and Provenance

## Valhalla

The runtime now probes the configured Valhalla `/status` endpoint before treating a route as live traffic. The normalized capability record includes deployment status, live-traffic support, version/tileset information, and the raw status payload. The runtime does not infer live traffic from a route response alone.

This release environment did not have a configured live Valhalla URL. The strict Golden therefore uses separately sealed replay evidence labelled `SEALED_REAL_REPLAY`, with a distinct incident mobility snapshot. It does not claim live traffic.

Each travel fact separates:

- route provenance: where geometry and duration came from;
- cost provenance: how the cost estimate was derived;
- time basis: when/how the route time was captured;
- distance and provider capability metadata.

## Weather

Weather capture persists provider observations with provider name, capture provenance, forecast run, target time, query scope, and immutable snapshot evidence. The Golden uses a reproducible sealed Open-Meteo deterioration rather than an unlabelled synthetic weather event.

## Degraded operation

General operation still supports deterministic mock/fixture fallback. When used, it is labelled in the evidence and cannot satisfy the V14 fully grounded acceptance gate. The legacy compatibility path is specifically marked `DEGRADED_BASELINE_REFERENCE` and is not reachable for the strict fully grounded traffic Golden.

