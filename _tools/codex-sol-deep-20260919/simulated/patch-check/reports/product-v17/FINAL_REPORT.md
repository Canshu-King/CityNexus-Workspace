# CityNexus V17 Final Report

Date: 2026-09-14

## Outcome

V17 semantic-core implementation is complete in the current CityNexus
worktree. Natural-language Copilot requests now use a strict DeepSeek
`SemanticEnvelope` when the provider is available; the deterministic fallback
is conservative and is no longer allowed to override a valid envelope.
CityNexus remains authoritative for IDs, provider facts, money, commitments,
feasibility, authorization, and mutations.

The official Hermes Agent runtime is installed and the native `citynexus` MCP
server is configured in the Windows user profile. Hermes 0.21.2 connects to
the MCP 2-compatible CityNexus server and discovers all eleven V2 tools. No
DeepSeek/Hermes provider credential is configured in this process, so the
model-driven native Hermes mission proof is explicitly **NOT CONFIGURED** and
is not represented as a pass.

## Implemented

- strict schema-validated `SemanticEnvelope` compiler with assertion status,
  effective time, event type, requested action, confidence, entities, and
  constraints;
- policy mapping for hypothetical, unverified, negated, historical, personal,
  asserted-now, and asserted-future requests;
- valid model envelope wins over deterministic fallback disagreement;
- Copilot and legacy `/agent/commands` event creation share the same semantic
  decision boundary;
- semantic evidence is persisted on user-reported Event payloads;
- explicit non-secret runtime identity endpoint:
  `/api/v1/agent/runtime-status`;
- explicit identities distinguishing `HERMES_NATIVE_MCP`,
  `NATIVE_DEEPSEEK_TOOL_LOOP`, `HERMES_COMPAT_ENDPOINT`, and
  `NOT_CONFIGURED`;
- MCP 2 low-level compatibility path preserving the existing V1/V2 surface,
  allowlist, and Gateway policy boundary;
- Copilot semantic evidence and runtime provenance are visible in the UI;
- OpenAPI contract includes the runtime-status endpoint.

## Honest limitation

The native Hermes model loop could not be run without a configured provider
credential. The server-side MCP boundary, deterministic Gateway policy,
PLAN_ONLY proposal semantics, and policy-gated action tests remain the proof
for those layers. The package does not claim a native Hermes inspect/replan/
action agent session.

## Release

Target: `CityNexus-V17-DeepSeek-Semantic-Core-Hermes-20260914.zip`

The archive is assembled from an allowlisted staging set. It excludes source
control metadata, virtual environments, databases, caches, logs, secrets,
frontend build output, prior archives, and Hermes user-profile data.
