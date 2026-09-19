# V18 Hermes Native Evidence

The official Hermes Agent 0.21.2 executable is installed at the Windows user
profile location under `AppData/Local/hermes/hermes-agent`. The dedicated
CityNexus profile is outside the repository at:

`D:\moodle\_v18_hermes_citynexus_profile\config.yaml`

The profile uses the CityNexus MCP V2 server over stdio, disables resources and
prompts, and includes exactly these tools:

`inspect_journey`, `inspect_twin`, `list_replans`, `search_city_services`,
`request_replan`, `accept_replan`, `replace_activity`, `reschedule_activity`,
`create_booking`, `cancel_refundable_booking`, and
`request_commitment_change`.

The native server boundary supports capability discovery, official Runs API
submission, run status, approval, stop, and SSE event streaming. The browser
only sees a server-proxied events URL; the Hermes bearer key remains in the
backend process.

The current status probe returned:

```json
{"configured":false,"reachable":false,"runs":false,"events":false,"approval":false,"profile":"citynexus"}
```

This is the correct result for the current environment: no
`CITYNEXUS_HERMES_NATIVE_API_URL`, no loopback `CITYNEXUS_HERMES_API_SERVER_KEY`,
and no process DeepSeek provider credential are configured. The package makes
no claim that a native Hermes model mission ran. The existing
`HERMES_COMPAT_ENDPOINT` path remains separately labeled.
