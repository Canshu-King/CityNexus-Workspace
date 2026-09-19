# Independent Review

## Overall

The submitted Qoder patch is useful and mostly well-directed, but the final
claim `QODER_PATCH_READY_FOR_REVIEW` is stronger than the evidence supports.

The current independent status is:

`QODER_PATCH_NOT_READY_TO_MERGE`

## What is genuinely good

### T1
- null IDs no longer trivially match;
- coordinate-only matching was removed as a sufficient condition;
- provider identity is namespaced;
- wrapper/provider relationship is modeled explicitly;
- the regression set is substantially better than the predecessor.

### T2
- `strict=True` on MockMobilityProvider is the correct primitive;
- `MOBILITY_DATA_UNAVAILABLE` is correctly distinguished from
  `REPLAN_NO_ALTERNATIVE`;
- the traveler copy is directionally correct.

### T3
- shared disruption-state semantics are a good architectural move;
- ACKNOWLEDGED is no longer intentionally equated with RESOLVED.

### T4
- NONE / PARTIAL / FULL is better than `hasPricedEvidence`;
- KNOWN_FREE is correctly treated as known evidence.

## Where this review disagrees with the submitted report

### D1 — T2 is not closed on the real replan path

The patch makes `_replan_estimate()` strict only **after a pair is missing from
the already-built mobility snapshot**.

But the real `generate_replan()` path pre-builds `mobility_pairs` including
replacement-candidate adjacencies and calls `capture_runtime_mobility_snapshot`
without `require_explicit_facts=True`.

Therefore the non-strict mock provider can still freeze the blanket
`default_minutes=20` into the mobility snapshot before `_replan_estimate()` is
called. Once frozen, `_replan_estimate()` sees a fact and never takes the strict
path.

This is the most important defect in the Qoder patch.

The focused T2 test file does not call the `/replans` endpoint and therefore
does not detect this bypass.

### D2 — the T2 result document overstates its tests

`test_qoder_mobility_truth_contract.py` contains nine tests, but they are
provider/capture/unit checks. It does NOT contain an end-to-end test proving:

- all unavailable candidates -> endpoint reports mobility unavailable;
- one valid candidate survives while unavailable candidates are skipped;
- overlap/travel-gap rejection still works through the endpoint.

Those claims should not appear as proven by that test file.

### D3 — T1 report and implementation disagree on AMBIGUOUS

The report says `is_same_physical_venue()` is true only for SAME.

The implementation returns:

`compare_physical_venue(left, right) != DIFFERENT`

Therefore AMBIGUOUS also returns true.

That behavior is defensible for *replacement exclusion*, but the function name
now lies about its semantics and is dangerous for future call sites.

### D4 — T1 has a cross-provider false-negative gap

If two records have different provider-scoped IDs, the function returns
DIFFERENT immediately.

Two providers can still describe the same physical venue.

Example:

- Overpass node A
- another provider place B
- same venue name
- same/near coordinates
- compatible category

Different provider IDs are proof that they are different provider objects, not
proof that they are different physical venues.

For replacement safety this should normally become AMBIGUOUS when strong
corroborating evidence says "possibly the same venue", so the candidate fails
safe.

### D5 — T3 Playwright test is a module test, not a cross-surface E2E

The Playwright spec dynamically imports `disruptionState.ts` and exercises pure
functions. It does not prove that Today and Live actually render the same event
state.

The integration code also contains a dead condition:

`acknowledgedOnly.length > 0 && openDisruptions.length === 0`

But `acknowledgedOnly` is defined as ACKNOWLEDGED **and open**, so it is a subset
of `openDisruptions`. The condition cannot be true.

### D6 — T4 is activity coverage, not trip-budget coverage

`budgetEvidenceCoverage(plan.activities)` does not include all budget-relevant
components such as selected stay / hotel and confirmed transport bookings.

Therefore `FULL` currently means:
"all supplied activities have price evidence"

It does NOT necessarily mean:
"the trip budget is fully evidenced".

The contract explicitly required the unknown-hotel case, but the submitted
Playwright test does not test a hotel at all.

### D7 — T4 Playwright test is also a module test

It imports `budgetEvidence.ts` and tests the helper. It does not prove that the
actual Studio/Trips UI refuses a final budget verdict in partial real-product
states.

### D8 — unknown replan errors can still leak raw internals

`humanReplanReason()` returns the raw input for unmapped reasons.

Default traveler UI should return a generic human-safe message and keep raw
diagnostics under Advanced.

### D9 — full-suite attribution cannot be independently proven from this ZIP

The package contains the summary counts, but not the raw full pytest logs for
both baseline and patched runs.

The failure-set subtraction is plausible, but the package itself does not let an
independent reviewer verify the asserted cause of all 11 failures / 1
collection error.

### D10 — repository hygiene is now a merge risk

Qoder reports that the authoritative project's backend/frontend are not
properly tracked in Git and therefore Worktree was impossible.

A synthetic git baseline inside a copied directory is useful for generating a
diff, but it is not a safe substitute for an authoritative repository baseline.

Do not merge multi-agent patches into an untracked main tree.
