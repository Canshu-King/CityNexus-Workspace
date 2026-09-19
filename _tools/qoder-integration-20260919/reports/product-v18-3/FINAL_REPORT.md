# CityNexus V18.3 Hermes + Experience Convergence

Date: 2026-09-15

## Outcome

V18.3 is a convergence release on the authoritative V18.2 tree. Native Hermes
remains a real, server-proxied runtime; DeepSeek remains semantic compiler;
CityNexus MCP V2 and Gateway/Guardian remain the authority for facts,
proposals, approvals, and mutation.

The release closes the confirmed V18.2 defects:

- native_hermes_status() now returns a stable ready: false when unconfigured;
- .v8-runtime-card has intentional block/grid styling;
- root status, test, integration, recommendation, manifest, and changed-file
  metadata are one consistent V18.3 snapshot;
- SQLite databases and *.db-wal / *.db-shm are excluded from staging and the
  stray sidecars were removed from the worktree.

## Selected experience convergence

MapLibre is dynamically loaded only by map surfaces. The non-map entrypoint no
longer statically imports the recovery map, and Vite emits a separate map
chunk. The existing vite-plugin-pwa / v10-sw.js architecture is unchanged.

The V18.2 event contract was strengthened with event IDs/sequences, stable
deduplication/order, bounded SSE retries, stale-stream messaging, and no
fixture substitution after live disconnect. Proposal-created remains distinct
from approval-required. Mobile keeps a compact current-mission view with
expandable real history.

Traveler Capability remains a next domain-wired slice; no decorative
localStorage-only authority was shipped.

## Native proof

The V18.3 convergence run run_5711e65d7914446aadd4ce4b4093cc44 executed with
HERMES_NATIVE_MCP and actual inspect_journey, inspect_twin,
search_city_services, and list_replans MCP tools. The earlier qualifying run
run_29f0d35ad0694970a9d5a671f048e365 remains retained as corroborating
evidence; both runs were real native executions. V18.3 does not relabel
unavailable or disconnected runs as Hermes success.

## Validation and artifact

Focused V18.3/V18.2 gates, the broad backend regression, frontend build, and
desktop/mobile browser gates are recorded in TEST_RESULTS.md. The final
artifact is CityNexus-V18.3-Hermes-Experience-Convergence-20260915.zip.

No credential value or external Hermes profile is stored or packaged.
