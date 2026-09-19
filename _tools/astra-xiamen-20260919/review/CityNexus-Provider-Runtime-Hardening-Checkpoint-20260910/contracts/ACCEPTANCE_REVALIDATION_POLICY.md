# Acceptance Revalidation Policy

The currently uploaded Provider Runtime checkpoint has an important authority
split:

```text
Generate Proposal -> frozen MobilitySnapshot
Accept Proposal   -> implicit MockMobilityProvider
```

This must not remain.

## Minimum safe policy for the current course milestone

Reuse the proposal's persisted frozen mobility snapshot for accept-time
deterministic revalidation.

Advantages:

- no hidden network call;
- no provider switch between generation and acceptance;
- fully reproducible course demo;
- simple audit story;
- preserves graceful offline behavior.

## Future production-grade option

If later requirements demand current mobility revalidation at the instant of
acceptance, add an explicit acceptance-provider boundary:

```text
Accept request
-> determine required OD pairs
-> capture a NEW frozen acceptance snapshot outside the gate
-> deterministic feasibility with that snapshot
-> persist acceptance snapshot / provenance
-> activate only if PASS
```

A freshness/TTL policy must decide when this is required.

Do **not** implement the bad hybrid:

```text
proposal uses real Valhalla
accept silently uses default Mock
```
