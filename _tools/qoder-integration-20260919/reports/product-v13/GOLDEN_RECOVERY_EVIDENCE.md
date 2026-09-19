# Authoritative Golden Recovery Evidence

Runtime label: `V13_LOCAL_REPLAY_AND_SYNTHETIC_AUTONOMOUS_GOLDEN`

The flagship local path is:

`provider fixture/replay -> normalized signal -> Event -> affected Activity -> Guardian -> Gateway policy -> deterministic feasibility -> bounded autonomous mutation -> JourneyTwin/offline projections`

The live API test is
`test_v13_authoritative_predictive_recovery_executes_through_gateway_and_offline_truth`.
It proves:

- an enrolled Journey is composed and selected through the authoritative API;
- the user-owned Autonomy Envelope and Guardian mission are persisted;
- a provider fixture yields a replay-labelled risk signal and an Event;
- Guardian produces a `PREDICTIVE` `PREEMPTIVE_RECOVERY` decision;
- policy evidence is `ALLOW_AUTO` inside cost, loss, drift, provider and
  commitment bounds;
- the deterministic planner returns a bounded candidate and the domain creates
  a new active PlanVersion;
- the original protected Commitment remains active;
- JourneyTwin and the offline snapshot expose the same active PlanVersion and
  execution projection.

The local test reports solver kind `DETERMINISTIC_HEURISTIC`. CP-SAT/OR-Tools
parity is validated separately by the solver regression suite; the V13 Golden
does not falsely claim that an external model or a live solver service made the
decision.

## Product/runtime boundary

The current process had no DeepSeek API key, Hermes URL/key, or Phoenix
collector configured. Native DeepSeek/Hermes and external Phoenix traces are
therefore `NOT CONFIGURED` for this run. The gateway and MCP surfaces remain
available and are tested independently; model absence does not bypass the
server-owned authorization gate.

Browser evidence includes the authoritative online and offline screenshots in
this report directory. The full Playwright matrix completed cleanly after the
operations stream was moved to an async generator, removing the long-lived
synchronous thread-pool pressure observed during repeated navigation.
