# Harness merge decisions

The V18.2 Codex tree is authoritative. The two Harness packages were used only
as evidence/reference inputs.

## Ported

- Low-conflict ready: false capability-shape fix.
- Low-conflict .v8-runtime-card layout rule.
- Runtime adapter principles already present in the V18.2 CityNexus API:
  server-selected Journey IDs, normalized events, bounded history, and
  reconnect-safe UI state.
- Motion/reduced-motion conventions already present in product CSS.
- MapLibre route isolation, implemented as dynamic map imports and a lazy
  recovery-map component.
- Stale stream messaging and offline approval blocking without replaying
  another run's fixture.

## Rejected or held

- No handwritten second service worker; vite-plugin-pwa remains the only PWA
  architecture.
- No reference default Journey ID.
- No unrelated completed recorded-run fallback after live SSE loss.
- No hardcoded HERMES_NATIVE_MCP in a generic timeline.
- proposal.created does not become approval.required without explicit approval
  metadata/state.
- Traveler Capability localStorage-only panel is held for the next
  domain-wired planner/recovery slice.
- No wholesale replacement of the router, app shell, or LocaleProvider.

## Evidence basis

The Harness review identified the above as the safe merge boundary. Its
independent chaos/approval gaps and 34/23/13 reference-app result are not
claimed as production evidence. Native proof and product tests remain the
CityNexus evidence described in HERMES_RUNTIME_EVIDENCE.md and TEST_RESULTS.md.
