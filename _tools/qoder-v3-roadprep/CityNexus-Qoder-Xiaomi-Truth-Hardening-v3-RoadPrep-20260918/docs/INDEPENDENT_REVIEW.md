# Independent review of Qoder v2

## Overall verdict

v2 is materially better than v1, especially:
- T2 now reaches the actual `/replans` path;
- T1 separates SAME from AMBIGUOUS exclusion;
- ACK-only copy is reachable;
- budget language was partially downgraded.

However, v2 is not safe to integrate as submitted.

## A. Direct answer to question (1): the legacy test helper

Principle:
**Yes, it is legitimate to repair old tests that accidentally depended on the
fake default 20 by giving those scenarios explicit test mobility facts.**

But the submitted implementation is too broad.

Current helper:
- builds a complete directed graph over all demo places;
- gives every previously missing edge the same 15-minute value;
- is installed as an autouse fixture at module scope in multiple existing test
  modules.

This can hide missing-mobility behavior in unrelated tests and changes scenario
timing from the historical fallback 20 to an invented 15.

It does not invalidate the dedicated new B1 endpoint test, but it weakens the old
suite as regression evidence.

Required v3:
- seed only the exact pairs each scenario requires;
- avoid module-wide complete-graph autouse injection;
- do not invent a different universal 15-minute world;
- if preserving a legacy test's timing assumption, declare the exact duration in
  that test/scenario fixture;
- any pair not explicitly seeded must remain unavailable/synthetic.

## B. Direct answer to question (2): T4 cross-source aggregation

The independent review ACCEPTS the safe scope downgrade:

Studio does **not** need to wire stay + booking aggregation before Xiaomi trial
if the traveler UI no longer claims that the whole trip budget is verified.

So v3 does NOT require a broad Studio cross-source integration.

But v2 still has two problems:

1. the heading says `已通过全部安全检查 / All safety checks passed` while the
   subtext says the total trip budget is not verified. That is still an
   overclaim;
2. `budgetEvidence.ts` contains two declarations of
   `BudgetEvidenceCoverage`, so a real TypeScript typecheck fails even though
   `vite build` can transpile the file.

The cross-source `tripBudgetEvidence()` helper may stay unit-tested and unused as
future infrastructure, but the live UI must make only the narrower claim it can
prove.

## C. New T2 issue: hard truth is denylist, not allowlist

v2 defines:

`HARD_FEASIBLE_QUALITIES = {EXPLICIT_FROZEN_FIXTURE, LIVE_PROVIDER_CAPTURE}`

but `hard_minutes()` never uses that allowlist.

It rejects only `SYNTHETIC_DEFAULT` and explicitly trusts `fact_quality=None`.

That is not fail-closed.

A pre-v2 sealed snapshot can contain an old synthetic default 20 with no quality
tag at all. The current code would trust it as hard truth.

Required:
hard feasibility accepts only explicitly trusted qualities.
Unknown / legacy-unclassified provenance must be unavailable unless migrated or
re-captured with trustworthy provenance.

## D. T2 candidate-specific endpoint proof is weaker than the report says

The second endpoint test allows:

`200 | 201 | 422`

and asserts only that it is not 500.

Therefore it does NOT prove the report's claim that:
"one trustworthy candidate survives when another candidate lacks mobility."

v3 must create a deterministic scenario and assert:
- 201;
- exact surviving candidate identity;
- unavailable candidate excluded for mobility-evidence reason.

## E. T1 cross-provider drift is still a gap

v2 cross-provider ambiguity requires equal quantized coordinates.

Real providers often locate the same venue several meters apart.

If:
- normalized name matches;
- category is compatible;
- coordinates are near but not equal;
then the current function may return DIFFERENT and allow the closed venue back
under another provider.

For replacement exclusion this should become AMBIGUOUS within a conservative
distance threshold, preferably using address/provider context where available.

## F. T3 rendered evidence still proves Live, not Today

`qoder-ack-rendered.spec.ts` opens `/v8/live`.

That is useful and genuinely rendered.

But the previous integration gate asked to prove Today and Live agree.
Shared helper usage makes the Today fix plausible, but it is not independently
rendered/proven in this package.

v3 should render `/v8/today` as well.

## G. Consumer error fallback still leaks raw strings

`humanReplanReason()` maps known codes, but its default is:

`return code`

So an unknown backend detail can still appear directly to the traveler.

Required:
generic safe copy by default; raw diagnostics only under Advanced.

## H. TypeScript compile claim is too strong

The package reports:

`npm run build` -> pass

The current frontend package's build script is Vite-only, and Vite does not
perform a full TypeScript typecheck.

Independent reconstruction of the submitted new `budgetEvidence.ts` and:

`tsc --noEmit`

produces:

- duplicate identifier `BudgetEvidenceCoverage`;
- returned object contains `verifiedCount` not present in the first alias.

v3 must add/run an actual typecheck gate.

## I. Raw baseline evidence is still missing

v2 includes `raw_full_backend_v2.log`.
It still does not include the full raw baseline log used to prove the set
subtraction.

The zero-new-regression claim is plausible from the reported counts and fail
list, but not independently reproducible from this ZIP alone.
