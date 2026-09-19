# Provider failure and graceful intelligence ladder

The system must degrade by capability, not crash as a whole.

## Capability ladder

```text
L0  deterministic mock/cache only
L1  real mobility available
L2  real context/weather available
L3  OR-Tools optimizer available
L4  AI explanation/personalisation available
```

Higher levels enrich lower levels; they never invalidate the lower-level ability to complete the canonical flow.

## Provider policy

Every adapter exposes:
- `provider_key`
- capability name
- ready/degraded/disabled/unavailable status
- optional last error/latency metadata

A provider error becomes one of:
- fallback to deterministic provider;
- a visible degraded badge;
- explicit `PROVIDER_UNAVAILABLE` when no safe fallback exists.

Never silently substitute an AI-generated ETA, opening time, booking result or payment result when a provider fails.
