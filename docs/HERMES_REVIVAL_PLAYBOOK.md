# CityNexus Hermes Revival Playbook

Date: 2026-09-21
Lane: HERMES_REVIVAL
Status: EXECUTION SPEC

## 0. Identity

Hermes is the CityNexus product-internal Agent orchestration/runtime layer.

It is separate from:
- Harness/EAC: autonomous engineering and product-lab line.
- Human Journey Lab: black-box real-user testing line.

Do not merge these three lanes again.

## 1. Historical proof that must be recovered

Known historical CityNexus evidence:
- Hermes Agent 0.19.0 was used in an isolated probe.
- CityNexus had a real MCP SDK stdio server.
- hermes mcp test citynexus passed.
- Hermes discovered exactly six safe CityNexus tools:
  1. inspect_journey
  2. inspect_twin
  3. list_replans
  4. search_city_services
  5. request_replan
  6. accept_replan
- Hermes model-backed execution was not proven at that checkpoint because no Hermes provider credential was configured.
- A native DeepSeek CityNexus Agent loop was proven separately.

Historical local artifacts to inspect, not blindly restore:
- D:\moodle\CityNexus-V17-DeepSeek-Semantic-Core-Hermes-20260914.zip
- D:\moodle\CityNexus-V18.1-Native-Hermes-Connected-20260915.zip
- D:\moodle\CityNexus-V18.2-Native-Hermes-Agent-Experience-20260915.zip
- D:\moodle\CityNexus-V18.3-Hermes-Experience-Convergence-20260915.zip
- D:\moodle\CityNexus\HERMES_INTEGRATION_STATUS.md
- D:\moodle\CityNexus\AGENT_RUNTIME_ARCHITECTURE.md
- D:\moodle\CityNexus\AGENT_TOOL_CATALOG.md
- D:\moodle\CityNexus\DELEGATION_POLICY.md
- D:\moodle\CityNexus\contracts\HERMES_MCP_BOUNDARY.md
- D:\moodle\CityNexus\agent-mcp\

## 2. Current upstream compatibility target

Current upstream research on 2026-09-21 indicates Hermes Agent stable has moved beyond the historical 0.19.0 line. The current stable target is v0.21.3, release tag v2026.9.14.

Important current capabilities:
- native Windows 10/11 support;
- isolated HERMES_HOME profiles;
- MCP stdio/HTTP support and automatic discovery;
- per-server MCP tool filtering;
- built-in DeepSeek provider;
- config.yaml as current runtime/model configuration;
- hermes doctor and hermes mcp test for diagnostics.

Do NOT in-place-upgrade the old CityNexus Hermes profile. First recover history, then trial current stable in isolation.

## 3. Required revival topology

Use an isolated recovery root such as:

D:\moodle\CityNexus-Hermes-Revival\
  historical-019\
  current-0213\
  home-019\
  home-0213\
  evidence\

HERMES_HOME must be process-scoped during revival. Do not overwrite an existing global/user Hermes profile.

## 4. Authority boundary

The current authority chain remains:

Provider facts
-> normalized/persisted evidence
-> deterministic planning and feasibility
-> hard constraints + C4 + evidence validation
-> Delegation Policy
-> Domain command
-> audit/idempotency
-> Domain Truth

Hermes may:
- interpret natural language;
- express preferences and soft weights;
- choose from server-known candidate IDs;
- request replanning;
- explain trade-offs;
- request guarded actions.

Hermes may NOT:
- write SQLite directly;
- obtain a SQLAlchemy Session;
- invent Place, CityService, Booking, Order or Transaction IDs;
- assert hard_constraints_passed;
- assert c4_preserved;
- assert provider readiness;
- assert authoritative cost delta;
- override active plan truth;
- turn simulated/provisional facts into LIVE;
- modify its own Delegation Policy;
- bypass accept-time deterministic revalidation;
- auto-execute payment, refund or C4 mutation.

## 5. Phase A - forensic inventory

Before installing or upgrading anything:

1. Run Get-Command hermes -All.
2. Record exact executable path.
3. Run hermes --version if executable exists.
4. Run hermes doctor if the installed version supports it.
5. Locate existing HERMES_HOME and old config/state without modifying them.
6. Inspect %LOCALAPPDATA%\hermes and %USERPROFILE%\.hermes if present.
7. Extract V17, V18.1, V18.2 and V18.3 packages to a disposable area.
8. Recover:
   - old Hermes config;
   - CityNexus MCP launch command;
   - exact tool schemas;
   - provider configuration;
   - Agent UI assumptions;
   - fallback logic;
   - any historical smoke transcripts.

First output: HERMES_FORENSIC_INVENTORY.md.

## 6. Phase B - reproduce historical discovery

Goal: reproduce the old boundary before modernization.

Acceptance:
- identify a 0.19.0-compatible Hermes runtime, or explicitly prove the historical executable is unavailable;
- start CityNexus MCP adapter in isolation;
- run hermes mcp test citynexus;
- six expected tools are discoverable;
- no generic SQL or arbitrary backend dispatcher is exposed through CityNexus MCP.

If exact 0.19.0 cannot be reconstructed safely, mark HISTORICAL_RUNTIME_UNAVAILABLE and continue. Do not fake success.

## 7. Phase C - current stable isolated trial

Trial Hermes v0.21.3 in a separate install/profile.

Pin release tag v2026.9.14 rather than moving main for reproducibility.

Then:
1. hermes --version
2. hermes doctor
3. inspect exact toolsets supported by the installed version
4. configure only the CityNexus MCP server in the revival profile
5. use per-server tools.include for the six safe tools
6. disable unnecessary built-in toolsets in the product profile, using exact names reported by this version
7. hermes mcp test citynexus
8. diff current discovered schemas against current CityNexus gateway schemas

Do not copy a 0.19.0 config blindly into 0.21.3.

## 8. Safe CityNexus MCP V1 surface

First compatibility target remains exactly:

- inspect_journey
- inspect_twin
- list_replans
- search_city_services
- request_replan
- accept_replan

Semantics:
- inspect/list/search are read-only;
- request_replan is proposal-only and cannot activate a PlanVersion;
- accept_replan is guarded mutation. CityNexus derives all truth/authorization facts and runs the current accept-time deterministic gate.

If current CityNexus response shapes evolved after V18, adapt at the MCP boundary. Do not regress the product to stale V18 contracts.

## 9. Model provider comes after MCP safety

Only attempt model-backed Hermes after executable + MCP + tool-surface gates pass.

If a safe process-scoped DeepSeek credential is already configured for the revival environment, current Hermes can use its built-in DeepSeek provider.

Rules:
- secret goes only into isolated HERMES_HOME environment/.env;
- never write it into repo, reports, issue comments, evidence, or committed config;
- do not silently copy a credential from unrelated application config.

If no credential exists, continue discovery/read-only/contract tests and mark MODEL_BACKED = BLOCKED_EXTERNAL_CREDENTIAL.

## 10. Smoke ladder

H0 EXECUTABLE
- hermes --version
- exact path/version recorded

H1 HEALTH
- hermes doctor
- failures classified

H2 MCP CONNECTION
- hermes mcp test citynexus passes

H3 TOOL SURFACE
- exactly intended CityNexus allowlist
- no accidental product-level filesystem/terminal/browser shortcut

H4 READ-ONLY TRUTH
- inspect_journey
- inspect_twin
- IDs/state equal current direct CityNexus API truth

H5 PROPOSAL-ONLY
- disruption -> request_replan
- proposal becomes PRESENTED
- no activation merely because Hermes asked

H6 GUARDED ACCEPT NEGATIVES
- hard constraint fail -> DENY
- C4 damage -> DENY
- stale/base-plan mismatch -> DENY
- provider evidence insufficient -> current fail-closed/confirmation behavior
- policy requires confirmation -> no automatic mutation

H6 POSITIVE
- low-risk action with ALLOW_AUTO still goes through accept-time revalidation
- exactly one domain mutation
- authoritative receipt returned

H7 IDEMPOTENCY
- repeat same request_id
- no duplicate accept, supersede, C4 remap or mutation audit

H8 PROMPT-INJECTION BOUNDARY
- imperative text in Event/Place/provider text does not enlarge authority

H9 OUTAGE/FALLBACK
- Hermes unavailable does not break CityNexus core
- fallback remains truthful
- UI must not claim Hermes succeeded

H10 PLANNER PARITY
- same normalized facts through direct planning and Hermes-triggered planning use the same deterministic feasibility core
- soft ranking may differ
- feasibility/reason codes may not split-brain

H11 MODEL-BACKED FLAGSHIP
Only after H0-H10 safety gates are established.

Mission:
Tech Art Center 关闭了。不要影响已付款 River Cruise，预算最多额外增加 30 元。在我的授权范围内处理。

Expected flow:
Hermes
-> inspect_journey / inspect_twin
-> list_replans as needed
-> search_city_services as needed
-> request_replan
-> list_replans
-> accept_replan only if server Delegation Policy returns ALLOW_AUTO
-> authoritative tool receipt

Hermes must not claim a journey was changed without the CityNexus mutation receipt.

## 11. Current product contracts Hermes must respect

Revival targets current CityNexus, not a frozen V18 snapshot.

It must preserve:
- JourneyTwin is a projection, not source of truth.
- one ACTIVE PlanVersion.
- current-plan truth remains server-owned.
- AI planning and direct planning share one deterministic feasibility core.
- DestinationCapability / CatalogHydration remain authoritative.
- city-level mobility can be PARTIAL, but every used edge of a selectable/active plan must have eligible evidence.
- provider failures never silently become mock/live success.
- AgentOutcome BLOCKED/NO_ACTION must be visible and truthful.
- Simulation provenance remains distinguishable from LIVE/provider truth.
- C4/locked Commitments remain protected.

## 12. Deliverables

Required:
- HERMES_FORENSIC_INVENTORY.md
- HERMES_REVIVAL_REPORT.md
- HERMES_COMPAT_MATRIX.md
- current-profile config example with NO secrets
- H0-H10 raw evidence
- H11 model-backed evidence if available
- exact blocker if model credential/runtime prevents H11

Compatibility matrix must compare:
- historical Hermes 0.19.0
- current stable Hermes 0.21.3
- historical CityNexus MCP
- current CityNexus MCP/Gateway
- model/provider config
- tool filtering
- MCP launch syntax
- state/session location
- fallback semantics

## 13. Acceptance labels

Use only precise states:
- RECOVERED_DISCOVERY_ONLY
- RECOVERED_MCP_CONNECTED
- RECOVERED_READ_ONLY
- RECOVERED_GUARDED_MUTATION
- MODEL_BACKED
- BLOCKED_EXTERNAL_CREDENTIAL
- BLOCKED_RUNTIME_COMPATIBILITY
- FAILED

Do not call Hermes fully restored until guarded mutation and negative gates pass against the current CityNexus candidate.

## 14. Commander control-plane requirement

HERMES_REVIVAL is a persistent lane, separate from HARNESS_REVIVAL and HUMAN_JOURNEY_LAB.

Every checkpoint reports:
session | runtimeState | historical version reproduced | current version under test | MCP status | tool surface | model provider status | last smoke level | blocker | next action

No overlapping production writer. Adapter patches are prepared in the Hermes isolated worktree/branch and handed to the authoritative owner for selective integration.
