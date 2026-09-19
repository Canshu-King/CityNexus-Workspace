# Hermes Integration Status

Status: **SKIPPED_EXTERNAL_DEPENDENCY** for live Hermes/model smoke.

The current host has no `hermes` executable and no installed `hermes` Python
package. The independent `agent-mcp/` adapter, exact six-tool discovery, safe
argument validation, and mock delegation tests are implemented and pass.

Configuration example: `agent-mcp/citynexus-hermes-config.example.yaml`.
The profile permits only the six CityNexus tools and disables terminal, file,
browser, payment, refund, and C4 modification capabilities.

