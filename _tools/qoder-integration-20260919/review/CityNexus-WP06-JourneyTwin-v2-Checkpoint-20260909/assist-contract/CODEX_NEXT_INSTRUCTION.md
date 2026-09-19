# CODEX — Continue from Post-WP04 Foundation Checkpoint

## User rules

- Do NOT perform SHA/file/archive hash work.
- Do not roll back the Post-WP04 GitHub Integration Foundation.
- Preserve current WP00-WP05/WP04-hardening work.
- Do not replace working code with older scaffold copies.

## First: reconcile this assist package against the real current workspace

The uploaded checkpoint is delta-style and some review-export paths were flattened. Your local `D:\moodle\CityNexus` is authoritative for file locations.

Read the real current versions of:

- `backend/app/main.py`
- `backend/app/services.py`
- `backend/app/replanning/feasibility.py`
- `backend/app/db/models.py`
- `backend/app/db/session.py`
- `backend/app/commerce/service_impl.py`
- current backend tests

Then read:

1. `00_INDEPENDENT_REVIEW.md`
2. `01_PREPARED_PATCH_CONTENTS.md`
3. `02_WP06_DETERMINISTIC_CORE.md`
4. `03_REAL_PROVIDER_SNAPSHOT_CONTRACT.md`
5. `04_JOURNEY_TWIN_V2.md`
6. `05_CONTRACT_DRIFT_TO_FIX.md`
7. `07_NEXT_GATE.md`

## Phase A — integrate the prepared integrity patch

Use `patches/WP05_WP06_PRECHECK_PATCH.patch` as a reviewed reference patch.

First:

```text
git apply --check <patch>
```

If the local files have advanced and the patch no longer applies cleanly, do **not** reset/revert the workspace. Merge the same semantics manually using `reference_overlay/` and the review notes.

The patch must achieve:

- durable JourneyTwin on start/complete;
- ACTIVE Journey mutation feasibility guard;
- ACTIVE-only replan semantics for the current MVP;
- same-Journey actionable Event guard;
- PRESENTED proposal before accept/reject;
- current-activity remap on accept;
- durable C4 semantic/time anchors included in hard feasibility;
- accept-time proposed-plan revalidation;
- deterministic Tech Art closure -> Design Library canonical recovery;
- frozen MobilitySnapshot boundary.

Run the entire suite. On the independently reconstructed checkpoint this moves 104 -> 115 passing tests. If your local tree has additional tests, all of them must also pass.

## Phase B — finish deterministic WP06, still offline/mock-first

Do not jump to DeepSeek or live Valhalla yet.

Complete:

1. protected terminal/current/C4 partition;
2. deterministic candidate families F0-F3;
3. CLOSURE canonical flow first;
4. then TRAFFIC_DELAY/SCHEDULE_DELAY family;
5. weather replacement policy after deterministic closure/delay are green;
6. persist actual ReplanDiff + before/after FeasibilityEnvelope;
7. acceptance is atomic and revalidated;
8. stale proposals fail safely.

Keep the canonical Golden Scenario executable without internet.

## Phase C — enrich JourneyTwin

Wire the already-installed:

- OpportunityWindow;
- FeasibilityEnvelope;
- provider degradation status;

into Twin `context` as derived data. Inject demo time explicitly in tests.

## Phase D — real-provider groundwork

Only after Phase B/C are green:

1. use existing routingpy adapter;
2. Valhalla first;
3. convert provider output into frozen MobilitySnapshot;
4. run the same deterministic feasibility gate;
5. keep MockMobility fallback;
6. add Open-Meteo as context provider;
7. GraphHopper optional second router;
8. OTP only with confirmed GTFS.

Do not weaken the gate by allowing arbitrary live network calls from inside it.

## Phase E — OR-Tools, AI, frontend

After deterministic WP06 external review:

- OR-Tools behind PlannerAdapter;
- then LiteLLM + DeepSeek for verified explanation only;
- then MapLibre + Turf + XState + shadcn/ui;
- then Playwright Golden Scenario.

## Stop point

Create the next checkpoint after deterministic WP06 + Twin v2 are fully green, before making a live provider mandatory.

The next review package must preserve exact repo-relative paths or provide an explicit overlay mapping. No hash manifest is required.
