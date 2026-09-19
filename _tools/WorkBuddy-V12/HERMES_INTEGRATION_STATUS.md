# Hermes Integration Status

Protocol status: **IMPLEMENTED / PASS**

- The checked-in stdio server supports both the pinned V1 session and an
  explicit `--v2` session. The V2 session discovers all eleven coherent
  inspect/plan/action tools in one protocol test.
- The example Hermes profile selects `--v2` and includes all eleven tools. It
  does not grant terminal, file, browser, payment-capture, refund, or raw C4
  modification capabilities; high-risk typed calls remain Gateway-gated.
- The CityNexus server ignores body-supplied agent identity and resolves the
  principal server-side.

Model status: **MODEL_BACKED / PASS (DeepSeek adapter)**. A real DeepSeek
OpenAI-compatible tool-calling loop selected its own inspection, search,
replan, and acceptance sequence; the tool trace and run were persisted and
reloaded. A Hermes binary/provider was not installed in the current process,
so this evidence must not be labeled as a Hermes CLI E2E run. The MCP V2
protocol surface and the backend DeepSeek adapter are separately verified.

V7 runtime attempt (2026-09-12): **HERMES_CLI_NOT_COMPLETED / EXTERNAL
CONNECTIVITY BLOCKER**. The official Windows installer was run in the isolated
staging directory `D:\\moodle\\_hermes_v7_runtime`; its local prerequisite
stages completed, but the installer could not clone the Hermes repository after
the GitHub connection failed. No Hermes binary or provider-backed Hermes E2E
claim is made. The native CityNexus DeepSeek runtime remains the verified
fallback, and the checked-in MCP V2/Gateway/CP-SAT/Policy path remains covered
by the server-side tests.
