# Native Hermes evidence

## Official profile

The running gateway was started and checked with the official profile:

```text
hermes -p citynexus profile show citynexus
Profile: citynexus
Path: C:\Users\仓鼠王\AppData\Local\hermes\profiles\citynexus
Model: deepseek-v4-flash (deepseek)
Gateway: running
Alias: citynexus → hermes -p citynexus
```

`hermes -p citynexus config path` resolved the same profile's
`config.yaml`, and `hermes -p citynexus config get model.default` returned
`deepseek-v4-flash`. The profile's enabled MCP server is `citynexus`, using
`citynexus_mcp.server --v2` with exactly the 11 CityNexus tools.

`hermes -p citynexus mcp test citynexus` was run once. It discovered the 11
tools; that discovery check was not counted as the execution proof.

## Gateway status

The CityNexus runtime-status response during the live proof reported:

```json
{
  "runtime_identity": "HERMES_NATIVE_MCP",
  "native_binary_detected": true,
  "deepseek_configured": true,
  "hermes_native_gateway": {
    "configured": true,
    "reachable": true,
    "runs": true,
    "events": true,
    "approval": true,
    "stop": true,
    "ready": true,
    "profile": "citynexus"
  }
}
```

The API-server key was a random process-local value used only for the
localhost gateway. It was never written to a file or included in the release.
The existing Windows User-scope DeepSeek credential was resolved by presence
only and passed to child processes without printing its value. No Machine-scope
credential was present. If only `CITYNEXUS_AI_API_KEY` is available, the
launcher maps it to `DEEPSEEK_API_KEY` for Hermes.

## Actual multi-step execution

Run `run_29f0d35ad0694970a9d5a671f048e365` was submitted through the CityNexus
Copilot endpoint with a mission-scoped Hermes session. The response reported
`runtime_identity = HERMES_NATIVE_MCP`; the proxied Hermes event stream then
returned `run.completed` and these actual tool events (Hermes internal schema
names are shown only for traceability):

```text
tool_describe → tool_call → inspect_journey → inspect_twin
→ inspect_journey → inspect_journey
→ search_city_services (four calls)
→ request_replan (two calls)
→ list_replans → search_city_services → run.completed
```

`inspect_journey`, `inspect_twin`, `search_city_services`, `request_replan`,
and `list_replans` are real CityNexus MCP V2 tools, not timers or fabricated
timeline entries. The stream was consumed through the CityNexus proxy; only
normalized event metadata is persisted.

The desktop flow also visibly rendered real native events for run
`run_b465415020d8434f9925b449d8cc5c07`, including `inspect_journey` and
`inspect_twin`, before the user-facing Stop control cancelled the long-running
mission. This proves the UI is connected to events rather than a fixed rail.

## Golden scenario

The reproducible sealed-truth fixture is
`evals/v18_2/golden_hermes_tianjin.json`. It fixes the paid 17:30 Haihe cruise
as a C4 anchored commitment, asks for rain recovery, low walking, and indoor
alternatives, and expects the sequence:

```text
DeepSeek SemanticEnvelope
→ HERMES_NATIVE_MCP
→ inspect Journey / JourneyTwin / protected commitments / affected activities
→ search candidates
→ deterministic request_replan
→ Guardian proposal
→ explicit approval before mutation
```

No proof run accepted a proposal or changed the cruise anchor.

## External limitation

Two direct, bounded checks of the reused User-scope DeepSeek credential timed
out at the configured Responses endpoint. Hermes smoke runs that encountered
the same external condition were left truthful (`running` then explicitly
`cancelled` through Stop) and are not counted as completed proof. The completed
native run above is the qualifying execution evidence.
