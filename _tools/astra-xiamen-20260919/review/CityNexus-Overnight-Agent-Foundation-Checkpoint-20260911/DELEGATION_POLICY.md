# Delegation Policy

The policy is persisted in `traveler_agent_policies` and configured through:

- `GET /api/v1/travelers/{traveler_id}/agent-policy`
- `PUT /api/v1/travelers/{traveler_id}/agent-policy`

The default is conservative `ADVISORY` with no automatic acceptance, zero
cost allowance, and no degraded-provider or CRITICAL-event exception. Agent
requests cannot update this policy or provide trusted gate facts.

