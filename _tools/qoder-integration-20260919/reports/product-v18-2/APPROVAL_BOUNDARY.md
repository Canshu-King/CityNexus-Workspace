# Approval and mutation boundary

CityNexus is the authorization authority. Hermes and DeepSeek never supply
authoritative IDs, coordinates, prices, provider status, timestamps,
commitments, feasibility, or mutation decisions.

## Native mission envelope

Native Copilot missions are created as `PLAN_ONLY` and carry an explicit
`citynexus.mission-plan.v1` sequence. The allowed native surface is:

```text
inspect_journey
inspect_twin
list_replans
search_city_services
request_replan
```

The plan ends at proposal inspection and an approval boundary. Hermes receives
the Journey ID, mission ID, and (when applicable) the server-created trigger
event ID in its instructions; it must call one MCP tool at a time and cannot
invent identifiers.

## Gateway / Guardian rules

- `request_replan` may generate a deterministic proposal in PLAN_ONLY.
- `accept_replan` requires a CityNexus-issued approval and remains blocked when
  protected commitments are affected.
- Booking creation/cancellation, payment, commitment changes, departure or
  arrival anchor changes, and C3/C4 changes are never silently executed.
- Requests identified as Hermes/MCP native or PLAN_ONLY are bounded by the
  Gateway to `REQUIRE_CONFIRMATION` for typed mutations, regardless of any
  caller-supplied confirmation boolean.
- Hermes's own API-server approval behavior is not used as the safety boundary.

## User decisions

The UI exposes three CityNexus decisions when a proposal requires action:

- **Approve** records the CityNexus approval and leaves execution authority in
  the Gateway/Guardian.
- **Reject** stops the native run through the CityNexus backend proxy.
- **Modify / Review** opens the authoritative recovery surface for a revised
  request.

The 17:30 paid Haihe cruise remains shown as a protected commitment. No proof
run accepted, booked, paid, or mutated it.
