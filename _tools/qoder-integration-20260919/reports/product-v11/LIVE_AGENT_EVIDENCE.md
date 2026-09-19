# Live Agent Evidence

Runtime label: `REAL_DEEPSEEK_TOOL_AGENT=PASS`.

Using the staged V11 key only in a child process, the official DeepSeek
Responses probe returned HTTP 200 with `function_call` output. The full
CityNexus scenario then ran against the local FastAPI domain: a natural-language
mission caused the live model to select `inspect_journey`, `inspect_twin`,
`request_replan`, and `accept_replan`. The Gateway returned `ALLOW_AUTO` inside
an explicitly configured AUTONOMOUS envelope and the accepted proposal changed
the active PlanVersion. AgentRun, AgentRunStep, audit, trace, and domain state
were persisted and reloadable.

The runtime now stops repeated `(tool, arguments)` requests with a persisted
`STOP_REPETITION` result and never retries a policy escalation. A separate live
run demonstrated that a confirmation-required result is surfaced without
mutation when the server cannot validate the target.

No MockTransport was used for the passing live scenario.
