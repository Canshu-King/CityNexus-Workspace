# CityNexus Agent Runtime V1

The Agent foundation is a constrained action layer over the existing CityNexus
domain services:

```text
Hermes or another Agent brain
    -> agent-mcp safe adapter
    -> /api/v1/agent/tools/{tool}
    -> AgentToolGateway
    -> persisted DelegationPolicy
    -> server-derived proposal/Event/Journey/C4 facts
    -> existing deterministic accept-time gate
    -> PlanVersion/Activity/Commitment domain truth
```

JourneyTwin remains a projection. The Agent cannot write SQLite, receive a
SQLAlchemy Session, supply provider evidence, supply feasibility facts, modify
its policy, or mutate payment/refund/C4 state.

`request_replan` is proposal-only. `accept_replan` can return
`REQUIRE_CONFIRMATION` or `DENY`; only an `ALLOW_AUTO` result calls the
existing authoritative accept operation. That operation revalidates the
proposal using the persisted MobilitySnapshot and active C4 commitments.

The server persists one `traveler_agent_policies` row per traveler. New
travelers receive `ADVISORY`, no automatic acceptance, zero cost allowance,
and no degraded-provider or CRITICAL-event exception.

