# Hermes runtime evidence

## Profile and boundary

The official profile is citynexus, resolved by hermes -p citynexus, with
Hermes Agent 0.21.2 and DeepSeek deepseek-v4-flash. The profile exposes the
11-tool CityNexus MCP V2 surface. Runs, SSE, stop, and approval remain behind
the CityNexus backend proxy; Hermes is not the safety authority.

The capability contract now has the same keys on configured and unconfigured
branches, including ready: false when the gateway is absent. Runtime identity
is supplied by server/run state, never inferred from a timeline component.

## Qualifying execution

Run run_5711e65d7914446aadd4ce4b4093cc44 was submitted from Copilot during
the V18.3 convergence browser flow and returned runtime_identity =
HERMES_NATIVE_MCP. The proxied SSE stream
contained real CityNexus tool events:

    tool_describe -> tool_call -> inspect_journey -> inspect_twin
    -> inspect_journey -> inspect_journey
    -> search_city_services x4 -> request_replan x2
    -> list_replans -> search_city_services -> run.completed

The desktop flow also rendered real inspect_journey and inspect_twin events for
run run_b465415020d8434f9925b449d8cc5c07 before CityNexus Stop cancelled it.
These are actual MCP calls, not timers or a recorded fixture.

The earlier run run_29f0d35ad0694970a9d5a671f048e365 independently completed
the same native chain and included request_replan. No protected commitment,
booking, payment, or PlanVersion mutation occurred.

## Reconnect and approval semantics

The frontend preserves received events, de-duplicates by event identity,
stabilizes sequence/timestamp order, retries SSE at most three times, and then
shows an explicit stream-unavailable state. It never substitutes another
run's completed fixture. proposal.created remains proposal-only unless an
explicit approval event/status is received. Approve/Reject/Modify actions
remain CityNexus-backed.

The provider produced two bounded Responses timeouts during the V18.2/V18.3
window. Those smoke runs were left truthful as unavailable/cancelled; the
completed native run above is the qualifying proof.
