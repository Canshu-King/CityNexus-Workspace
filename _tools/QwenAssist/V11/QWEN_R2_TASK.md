# CITYNEXUS V11 — QWEN SIDECAR ROUND 2 TASK

## A. REPAIR ROUND-1 ARTIFACTS

Read the prior V11 sidecar outputs.

Repair these known issues first:

1. `candidate_tests/test_compose_provider_truth.py`
   - currently contains invalid Python syntax involving `...`;
   - replace pseudo-code with syntactically valid, repository-grounded tests.

2. `candidate_tests/test_deepseek_agent_adversarial.py`
   - remove all TODO/pass placeholder tests;
   - use actual repository classes/functions/import paths;
   - skip a test only for a clearly documented external dependency.

3. `product/REAL_TRAVEL_EDGE_CASES.csv`
   - rewrite as valid machine-readable CSV;
   - exactly 8 columns on every row:
     ID,Category,Scenario,Precondition,Expected Behavior,Hard/Soft,Affected Concepts,Priority
   - use normal CSV commas/quoting, not Chinese full-width punctuation as delimiters;
   - preserve at least 150 useful unique cases;
   - correct PIC/Edge semantics:
     PIC16F877A is a physical edge companion, not a "personal intelligent center" and not a local AI/solver fallback;
   - correct QR semantics:
     decoding a QR/barcode does NOT prove authenticity.

4. Correct GitHub licensing claims using actual current repository metadata.
   In particular VERIFY, do not guess:
   - 21st-dev/agent-elements
   - 21st-dev/codex-plugin

5. Remove "TBD / needs reading" from P0 code-location maps where the main repository is available.
   Actually read the files.

## B. FINISH THE MISSING ROUND-1 TRACKS

Complete ALL of these:

### B1 Money adversarial tests
Create runnable candidate tests for:
- FREE_KNOWN / KNOWN / ESTIMATED / UNKNOWN;
- imported unknown reservation price;
- unknown cancellation loss;
- unknown ride-hail/taxi price;
- foreign currency;
- budget headroom;
- autonomous action boundary.

### B2 Execution tests
Create runnable candidate tests for:
- actual now after planned start;
- EN_ROUTE;
- ARRIVED / IN_PROGRESS / COMPLETED / SKIPPED;
- NOW/NEXT;
- leave-by;
- C4 countdown;
- offline next-24h;
- stale/high-error location;
- provider duration update;
- Edge risk/autopilot state.

### B3 Journey Inbox tests
Create runnable tests for:
- TZID ICS;
- folded ICS lines;
- all-day ICS;
- duplicated ICS import;
- ambiguous text extraction;
- screenshot-extracted UNKNOWN field;
- QR/barcode deterministic import;
- confirmation boundary.

### B4 Opening hours / GTFS quality
Produce:
- `providers/OPENING_HOURS_IMPLEMENTATION_NOTES.md`
- `providers/GTFS_QUALITY_PIPELINE.md`
- runnable candidate tests.

Evaluate current:
- KDE/kopeninghours
- MobilityData/gtfs-validator
- MobilityData/gtfs-realtime-bindings
- OpenTripPlanner

Do not flatten day/date/holiday semantics.

### B5 Sourceful Web Search
Produce:
- `web/SOURCEFUL_SEARCH_PROVIDER_DESIGN.md`
- `web/WEB_TRUST_ADVERSARIAL_CASES.md`

Evaluate SearXNG as optional URL/title/domain provider.

Create at least 30 adversarial cases.

### B6 Sealed provider capture
Produce:
- `providers/SEALED_CAPTURE_SPEC.md`
- `providers/PROVENANCE_TEST_MATRIX.csv`
- candidate schema/validator helper if safe.

Must model:
LIVE_CAPTURE
CAPTURED_REPLAY
SYNTHETIC_FIXTURE
FALLBACK
USER_IMPORTED
AI_INFERRED
MIXED aggregate provenance.

### B7 DnD Trip Studio
Produce:
- `frontend/DND_TRIP_STUDIO_INTERACTION.md`
- candidate state-machine / Zod schema or test helper if useful.

Flow:
drag -> draft -> preview/replan -> impact -> accept/reject.

Never direct-mutate ACTIVE PlanVersion on pointer drop.

### B8 Candidate patches
Create small sidecar candidate patches/helpers for low-risk work:
- query keys;
- Zod schemas;
- i18n copy;
- Storybook stories;
- fixture validators;
- test utilities.

Each candidate patch folder must include README with:
target path
why safe
dependencies
tests
how Codex should apply it.

Do not write a giant authoritative backend rewrite.

## C. VERIFY CURRENT GITHUB ADOPTION RESEARCH

For each library in the current adoption research:
- verify repository exists;
- verify license from current metadata/explicit license file;
- do not infer "already adopted" unless package.json/source proves it;
- distinguish:
  INSTALLED
  USED_IN_SOURCE
  REFERENCED_ONLY
  NOT_ADOPTED

Output:
`frontend/GITHUB_UI_ADOPTION_RESEARCH_R2.md`
`frontend/GITHUB_ADOPTION_STATUS.csv`

## D. MAKE THE OPENAPI AUDIT CONCRETE

Actually scan frontend source.

Produce:
`frontend/HANDWRITTEN_TYPE_DUPLICATES.csv`

Columns:
File
TypeName
BackendSchemaEquivalent
GeneratedTypeAvailable
MigrationPriority
Notes

Also scan direct fetch/API calls:
`frontend/DIRECT_API_CALLS.csv`

Do not say "scan later".

## E. MAKE STORYBOOK MATRIX CONCRETE

Actually scan components/stories.

Produce:
`frontend/STORYBOOK_MATRIX_R2.csv`

Columns:
Component
SourceFile
StoryFile
Default
Loading
Empty
Error
Offline
Stale
Risk
Protected
Disabled
Mobile
Priority

No invented components marked as existing.

## F. VALIDATE BEFORE HANDOFF

Run the supplied validator:
`python VERIFY_QWEN_R2_OUTPUT.py D:\moodle\CityNexus-QwenAssist\V11-R2`

Fix every failure that is under your control.

For candidate Python tests:
- syntax compile must pass;
- no TODO;
- no placeholder `pass`;
- no Ellipsis pseudo-code;
- imports must be based on actual repo paths.

Where tests cannot run because of an external dependency:
- make syntax valid;
- use a justified `pytest.mark.skipif`;
- document the missing dependency.

## G. FINAL HANDOFF

Only after validation, write:
`QWEN_HANDOFF_TO_CODEX_R2.md`

Maximum 2000 words.

Sections:
1. Verified P0 findings
2. Ready-to-copy tests
3. Ready-to-copy helpers
4. Corrected GitHub/license findings
5. Real travel edge-case highlights
6. Missing external dependencies
7. Top 5 Codex actions
8. Do-not-waste-time list

Do not claim to have saved "N hours".
Do not estimate productivity savings unless measured.
