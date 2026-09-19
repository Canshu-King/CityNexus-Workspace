# Delegation Policy

The policy is persisted in `traveler_agent_policies` and configured through:

- `GET /api/v1/travelers/{traveler_id}/agent-policy`
- `PUT /api/v1/travelers/{traveler_id}/agent-policy`

The default is conservative `ADVISORY` with no automatic acceptance, zero
budget-increase/loss/schedule-drift allowance, and no degraded-provider or
CRITICAL-event exception. Agent requests cannot update this policy or provide
trusted gate facts.

The user-owned Autonomy Envelope also stores:

- maximum automatic budget increase, acceptable loss, and schedule drift;
- optional allowed Activity types;
- protected Commitment levels (default `C3_Guaranteed` and `C4_Anchored`);
- whether Commitment management has been explicitly pre-authorized.

`AI_ONLY` is an impact maturity, not an automatic denial. A server-known,
non-terminal, non-protected Activity selected by the model can enter proposal
generation. `accept_replan` may return `ALLOW_AUTO` for that hypothesis only
when the post-action deterministic feasibility facts and the entire envelope
pass. Missing target authority, hard-constraint failure, protected Commitment
damage, budget/loss/drift/type/provider/critical-event violations return a
confirmation, step-up, or denial decision as appropriate.

The deterministic layer verifies post-action hard constraints and business
facts; it does not attempt to replace the model's natural-language semantic
judgement. C4 management is a separate higher-risk action: it remains
step-up-protected unless the user explicitly enables the higher policy and the
provider/refund/loss facts satisfy that policy.

The V2 typed mutation surface uses the same envelope for low-to-medium risk
journey changes and booking actions. The gateway can expose a typed command to
Hermes even when it cannot execute it: it returns a server-issued scoped
approval receipt with `REQUIRE_CONFIRMATION` or `REQUIRE_STEP_UP`. A receipt is
bound to the exact action, Journey, target, policy version, server facts, and
command arguments; it expires and is consumed once.
