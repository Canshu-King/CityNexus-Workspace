# Event Provenance and Deterministic Demo Time

## Current risk

`EventCreate` currently accepts a client-provided `provider_key`. That is acceptable for a demo simulator, but it must not be confused with provider-verified evidence once Open-Meteo/OTP/real mobility integrations are active.

Without a provenance boundary, a client could submit:

```text
provider_key = "open-meteo"
```

and make synthetic input look like trusted provider data.

## Recommended model

At minimum distinguish:

```text
SIMULATED
PROVIDER_VERIFIED
USER_REPORTED
SYSTEM_DERIVED
```

The server, not an arbitrary API client, should derive provider identity for PROVIDER_VERIFIED events.

For the coursework Event Simulator, use explicit:

```text
provenance = SIMULATED
provider_key = demo-simulator
```

For Open-Meteo ingestion:

```text
provenance = PROVIDER_VERIFIED
provider_key = open-meteo
provider_call/evidence reference = server generated
```

Do not expand the schema until the provider ingestion route is ready, but freeze this rule before frontend contracts become difficult to change.

## Demo time

The fixture Journey is intentionally deterministic and can be in the future relative to wall clock. Therefore Event Simulator should always send explicit `occurred_at` and Twin should receive/infer the same demo `now`.

Do not let:

```text
real wall clock
```

silently mix with:

```text
fixture Journey date
```

because OpportunityWindow, slack, event ordering and UI timelines will become nonsensical while all individual timestamps remain syntactically valid.
