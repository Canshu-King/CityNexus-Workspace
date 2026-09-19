# Provider-backed Compose Evidence

`PROVIDER_BACKED_COMPOSE=PASS_REPLAY_OR_CONFIGURED_PROVIDER`.

Generic Compose and plan selection now capture one immutable MobilitySnapshot
before feasibility evaluation. The same frozen facts, including per-leg
provider/degraded metadata and snapshot id, feed the deterministic gate and are
recorded in plan explanation evidence. Mock mobility is no longer used in the
generic Compose/select critical path.

With no Valhalla URL configured, the runtime truth is explicit captured
synthetic/replay evidence; it is not called live. Existing 24 focused Compose
and Agent tests plus the full scoped backend suite cover this boundary.
