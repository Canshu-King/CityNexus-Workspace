# CITYNEXUS V11 — QWEN SIDECAR MASTER BACKLOG

This backlog is intentionally large. Use the abundant token budget on work that is expensive for Codex but does not need to block the authoritative implementation.

## TRACK A — V11 P0 CODE LOCATION MAP

Read the repository and produce:

`analysis/P0_CODE_LOCATION_MAP.md`

For each item below list:
- exact file;
- class/function;
- current behavior;
- why it is a gap;
- minimal implementation path;
- tests that should prove the fix;
- dependencies / side effects.

Items:
1. real DeepSeek V4.1 live CityNexus tool loop;
2. Generic Compose still using MockMobilityProvider;
3. plan selection final gate using different mobility truth;
4. OpenAPI generated TS types not actually driving client types;
5. leg-level provider provenance;
6. UNKNOWN money semantics;
7. ExecutionClock / Edge countdown / offline actual-now;
8. MapLibre resize;
9. Storybook state coverage;
10. sourceful web evidence.

Do not rewrite the system. Create a precise map for Codex.

## TRACK B — ADVERSARIAL TEST GENERATION

Create candidate tests under:

`candidate_tests/`

Do NOT modify main-repo tests.

Generate focused tests for:

### B1 DeepSeek Agent
- model chooses inspect before mutation;
- multi-turn function_call_output loop;
- repeated identical tool-call loop stops;
- malformed tool args;
- tool call points to another traveler's Journey;
- policy-required confirmation;
- model unavailable fallback;
- live tool result changes final model decision.

### B2 Compose / Provider Truth
- arbitrary 6-POI set reordered by solver;
- multi-day cross-midnight;
- Stay + arrival + departure + imported C4;
- same frozen mobility snapshot used during selection;
- mixed live/fallback leg provenance;
- stale route fact rejected / downgraded;
- no MockMobilityProvider in authoritative select gate.

### B3 Money
- UNKNOWN taxi price != free;
- ESTIMATED hotel price stays estimated;
- foreign currency stays foreign;
- free walking mode uses FREE_KNOWN;
- cancellation loss UNKNOWN does not auto-execute.

### B4 Execution
- delayed current Activity;
- skipped Activity;
- EN_ROUTE to protected C4;
- actual now after planned start;
- offline next-24h;
- Edge countdown;
- stale location accuracy;
- provider travel-duration change updates leave-by.

### B5 Journey Inbox
- ICS TZID;
- folded ICS lines;
- all-day ICS;
- ambiguous pasted text;
- screenshot extraction with UNKNOWN price;
- QR deterministic import;
- duplicated reservation import.

Write tests in the repository's existing style as far as possible.
Make them ready for Codex to copy.

## TRACK C — REAL TRAVEL EDGE-CASE CATALOG

Create:

`product/REAL_TRAVEL_EDGE_CASES.md`
`product/REAL_TRAVEL_EDGE_CASES.csv`

Build at least 120 non-duplicate real-world cases across:

- airport / railway arrival;
- luggage;
- early/late hotel check-in;
- hotel cancellation;
- hotel quote expiration;
- room occupancy;
- attraction timed entry;
- restaurant booking;
- weather;
- road congestion;
- metro/bus delay;
- transit cancellation;
- service alert;
- venue closure;
- opening-hours ambiguity;
- public holidays;
- last-train constraints;
- night travel;
- currency;
- payment/refund;
- offline;
- poor GPS;
- low battery;
- group split/join;
- accessibility;
- stroller/wheelchair;
- child/elderly constraints;
- meal/rest pacing;
- timezone;
- DST for international trips;
- provider outage;
- stale provider facts;
- map CRS mismatch;
- user manual override;
- AI hallucination;
- prompt injection from web content;
- duplicate provider events;
- imported bookings from other apps;
- PIC/Edge disconnect.

Columns:
ID
Scenario
Precondition
Expected CityNexus behavior
Hard/Soft constraint
Affected domain concepts
Test level
Priority

Use this catalog to identify missing product semantics, but do not expand the core architecture recklessly.

## TRACK D — OPENAPI / FRONTEND CONTRACT AUDIT

Create:

`frontend/OPENAPI_TYPE_ADOPTION_PLAN.md`
`frontend/HANDWRITTEN_TYPE_DUPLICATES.csv`

Find:
- all manually declared frontend interfaces/types that correspond to backend OpenAPI schemas;
- all direct fetch calls;
- all duplicated request/response shapes;
- all places TanStack Query can replace ad-hoc fetching;
- query keys and invalidation relationships.

Propose a staged migration:
1. V11 new surfaces only;
2. high-churn existing surfaces;
3. stable legacy surfaces later.

Do not demand a full rewrite.

## TRACK E — STORYBOOK / DESIGN SYSTEM MATRIX

Create:

`frontend/STORYBOOK_MATRIX.csv`
`frontend/DESIGN_SYSTEM_BACKLOG.md`

Inventory current reusable components.

For each component define states:
- default
- loading
- empty
- error
- offline
- stale
- risk
- protected
- disabled
- mobile where relevant.

Focus:
ActivityCard
JourneyLeg
CommitmentCard
RiskBanner
AgentAction
InboxArtifact
WalletTicket
HotelCard
ModeComparison
ApprovalSheet
OfflineBanner
ProviderFreshness
EdgeStatus
TravelerTwinPreference

Also identify inconsistent:
spacing
typography
color semantics
button hierarchy
icon usage
copy style
mobile touch targets.

## TRACK F — UI REFERENCE / GITHUB ADOPTION RESEARCH

Create:

`frontend/GITHUB_UI_ADOPTION_RESEARCH.md`

Inspect current versions/licenses/fit for:
- shadcn-ui/ui
- shadcn/originui
- 21st-dev/agent-elements
- 21st-dev/codex-plugin
- clauderic/dnd-kit
- emilkowalski/vaul
- ibelick/motion-primitives
- magicuidesign/magicui
- lucide-icons/lucide
- storybookjs/storybook
- react-hook-form/react-hook-form
- colinhacks/zod
- TanStack/query
- TanStack/router
- opentripplanner/otp-ui

For each:
- repository
- current license if verifiable
- exact CityNexus use
- adopt now / later / inspiration only
- migration risk
- concrete components/patterns to look for

If 21st MCP is available in WorkBuddy, use it only for research and component identification.
Do not paste ambiguous-license source code into candidate patches.

## TRACK G — OPENING HOURS / GTFS QUALITY

Create:

`providers/OPENING_HOURS_IMPLEMENTATION_NOTES.md`
`providers/GTFS_QUALITY_PIPELINE.md`

Study current CityNexus normalization.

Evaluate:
- KDE/kopeninghours
- MobilityData/gtfs-validator
- MobilityData/gtfs-realtime-bindings
- OpenTripPlanner

Produce:
- integration steps;
- platform/licensing concerns;
- fallback semantics;
- focused tests.

Important:
unknown/complex opening hours must remain uncertain rather than being flattened.
No realtime update must not mean "on time".

## TRACK H — SOURCEFUL WEB SEARCH

Create:

`web/SOURCEFUL_SEARCH_PROVIDER_DESIGN.md`
`web/WEB_TRUST_ADVERSARIAL_CASES.md`

Evaluate:
- DeepSeek built-in web search;
- SearXNG optional sourceful provider.

Design:
query
→ URL/title/domain/snippet
→ source classification
→ DeepSeek semantic interpretation
→ WebObservation

Generate at least 30 adversarial cases:
- SEO spam;
- outdated official page;
- fake official domain;
- prompt injection inside page;
- conflicting sources;
- social rumor;
- cached old closure notice;
- malformed date;
- event affecting another city;
- translated page ambiguity.

## TRACK I — PROVIDER REPLAY FIXTURE SPEC

Create:

`providers/SEALED_CAPTURE_SPEC.md`
`providers/PROVENANCE_TEST_MATRIX.csv`

Define exact file/schema for:
LIVE_CAPTURE
CAPTURED_REPLAY
SYNTHETIC_FIXTURE
FALLBACK
USER_IMPORTED
AI_INFERRED

Include:
provider
operation
request fingerprint
raw response
normalizer version
normalized facts
captured_at
expires_at
CRS
redaction metadata
checksum
per-leg provenance
aggregate provenance.

Design how mixed snapshots become MIXED.

## TRACK J — UX COPY / I18N

Create:

`frontend/COPY_ZH_CN.json`
`frontend/COPY_EN_US.json`
`frontend/COPY_GUIDE.md`

Write polished product copy for:
- Journey Hub;
- Live Journey;
- Offline;
- Recovering;
- Approval required;
- Booking imported;
- Booking field unresolved;
- Provider stale;
- Leave now;
- Commitment at risk;
- Autopilot acted;
- Agent unavailable;
- Edge device connected/disconnected;
- hotel quote expired;
- unknown price;
- transit realtime unavailable.

Avoid exposing internal terms like CP-SAT or PlanVersion in primary UI.

Keep technical terms for Evidence/Developer drawers only.

## TRACK K — DND TRIP STUDIO SPEC

Create:

`frontend/DND_TRIP_STUDIO_INTERACTION.md`

Define:
drag start
drag preview
drop
preview/replan request
feasibility response
impact summary
accept/reject
rollback
keyboard drag
mobile reorder

Important:
pointer drop must not directly mutate ACTIVE PlanVersion.

Design conflict handling:
- C4 protected;
- opening-hours violation;
- insufficient travel time;
- hotel/check-in conflict;
- stale route evidence.

## TRACK L — QWEN PATCH CANDIDATES

Only after the analyses above, create small candidate patches under:

`candidate_patches/`

Allowed candidate work:
- pure utility helpers;
- test helpers;
- frontend copy/i18n files;
- Storybook stories;
- Zod schemas;
- typed query-hook prototypes;
- fixture validators;
- documentation.

Avoid writing large authoritative backend rewrites.

Each candidate patch must have:
README
target path
why safe
tests expected
dependencies

## TRACK M — FINAL HANDOFF

Create:

`QWEN_HANDOFF_TO_CODEX.md`

Maximum ~2500 words.

Include:
1. top 10 findings;
2. exact code locations;
3. candidate test files;
4. candidate patch files;
5. libraries worth adopting now;
6. UI changes worth adopting now;
7. things Codex should NOT waste time on;
8. top 5 next implementation actions.

This handoff should save Codex time, not give it another novel to read.
