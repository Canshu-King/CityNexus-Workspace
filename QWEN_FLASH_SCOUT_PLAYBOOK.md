# Qwen3.8Flash Scout Playbook — CityNexus

Purpose: use free/cheap Flash capacity for high-throughput evidence work while preserving Commander authority and CityNexus truth contracts.

## Role split

Commander:
- owns orchestration, arbitration, integration decisions
- validates scout claims before routing work
- does not let scouts rewrite truth semantics

Implementation owner:
- sole writer for current backend / truth-sensitive production files

Flash scouts:
- read-only by default
- bounded tasks
- evidence, not authority

UI writer:
- isolated worktree only
- presentation changes only unless Commander explicitly changes ownership

Verifier:
- independent, read-only against production

## Scout contract

Every Flash scout prompt must include:
1. current HEAD
2. exact read-only path
3. task boundary
4. invariants
5. output schema
6. hard stop
7. forbidden actions

Every scout returns:
- DONE or PARTIAL
- evidence paths
- exact commands run
- collected/deselected counts for pytest
- no unsupported PASS claims

## Wave 1

### F1 Execution-truth auditor

Goal:
Find all remaining execution-truth inference based on wall clock, array index, or silent fallback.

Search seeds:
- Date.now(
- new Date(
- activities[0]
- activities[1]
- legs[0]
- activities.find(
- findIndex(
- current_activity_id
- next_activity_id
- next_leg_id
- STALE_CURSOR

Classify:
- DISPLAY_ONLY
- AUTHORITATIVE
- SUSPECT_WALL_CLOCK
- SUSPECT_POSITIONAL
- SUSPECT_STALE_FALLBACK
- DUPLICATE_CONSUMER_SEMANTICS

Priority files:
- frontend/src/app/V8Experience.tsx
- current Today/Live/Edge/V10 consumers
- backend/app/operations/v9.py

Output:
FLASH_EXECUTION_TRUTH_AUDIT.md

Do not use the stale published GitHub branch as proof of a current local defect.

### F2 Mutation cartographer

Goal:
Preflight all 16 actionable Mission-002 mutants before campaign execution.

For each mutant:
- target file
- anchor match count after CRLF->LF normalization
- exact selector
- pytest --collect-only node IDs
- collected count
- intended discriminating assertion
- possible vacuity / wrong-path risk

Known required sentinel:
backend/app/services.py active-C4 constraint assembly must be mapped to RX-4 coverage.

Output:
FLASH_MUTATION_MAP.md
FLASH_MUTATION_MAP.json

Preflight target:
- 16 actionable rows
- 16 valid anchors
- 16 collected_count > 0
- 0 silent skips

### F3 Mobile UI auditor

Audit viewports:
- 360x800
- 390x844
- 412x915

Surfaces:
- Journey setup
- Today
- Live
- Trips -> Bookings / wallet-facing path
- mobile shell/nav

Inspect:
- styles.css
- design-tokens.css
- JourneyTrialSetup.tsx
- JourneyInboxWorkbench.tsx
- current mobile nav

Check:
- safe-area
- keyboard overlap
- bottom-nav clearance
- dark-mode hard-coded-white leaks
- touch targets
- overflow
- blank states
- primary CTA hierarchy
- duplicated animations / specificity conflicts

Output:
FLASH_UI_AUDIT.md

Rank:
BLOCKER / HIGH / MEDIUM / LOW

End with top 6 low-write-set presentation fixes.

## Wave 2

### F4 Vacuous-test hunter

Prioritize:
- 422 tests that do not check failure reason
- C4 fixtures with locked=True but no real commitment
- tests that fail before mutated branch
- helper mocks that bypass real endpoint
- ACK != resolved
- replan ownership
- stale cursor
- hard mobility truth

Return:
KEEP / REWRITE / RETIRE / ADD_SENTINEL

### F5 API/UI truth map

Map:
backend field -> endpoint -> frontend type -> consumer -> fallback -> tests

Priority:
- current_activity_id
- cursor_status
- now_activity_id
- next_activity_id
- next_leg_id
- next_mode
- next_eta_min
- commitment level/status
- fact_quality/provenance
- replan proposal status

### F6 Requirements evidence inventory

Only after current truth/UI lanes are healthy.

Map existing 138 requirements to:
- implementation
- API
- tests
- demo evidence
- missing/partial

Do not rewrite the requirement baseline.

## Evidence discipline

A Flash claim is not accepted because it sounds plausible.

Commander must independently validate at least the top two findings from each scout and label:
- CONFIRMED
- REJECTED
- NEEDS_REPRO

Only CONFIRMED findings may enter a writer queue.

## Mutation discipline

KILLED:
- selected tests collected > 0
- tests execute
- genuine invariant assertion fails because of mutation

SURVIVED:
- selected tests collected > 0
- tests execute
- all pass

HARNESS_INVALID:
- zero collected
- wrong node
- import/syntax/collection error
- infrastructure failure
- timeout without invariant assertion

Never use non-zero exit code alone as a kill verdict.

## UI discipline

Prefer presentation-only changes:
- design tokens
- semantic surfaces
- safe-area
- spacing
- hierarchy
- touch targets
- loading/empty/error states

Do not:
- fabricate provider data
- hide degraded/unknown states
- change execution truth to make screens look nicer
- copy fixed-index Live logic from stale published snapshots
- rebuild an existing flow just because it is easier than auditing it

## Stop rule

Flash scouts do not invent new work after their bounded task is complete.
Commander may immediately recycle the session into the next bounded scout task.
