# T4 UI + TypeScript gate

## Decision on cross-source wiring

Do NOT wire stay/booking costs into Studio in v3.

The safe scope downgrade is accepted:
if the UI explicitly says only activity costs are complete and explicitly says
the total trip budget is not verified, that is truth-safe.

`tripBudgetEvidence()` may remain unit-tested future infrastructure.

## Fix the heading

Current:
`已通过全部安全检查`

Subtext:
`整趟行程预算（含住宿与交通）未在此处验证`

Those statements conflict.

Use a heading that matches the proven scope, for example:

`行程约束检查已通过`

or another traveler-friendly equivalent.

Do not say:
- all safety checks passed;
- trip budget verified;
unless the corresponding evidence actually exists.

## Fix the duplicate type alias

The submitted new `budgetEvidence.ts` declares:

`BudgetEvidenceCoverage`

twice.

A real TypeScript compiler reports duplicate identifier errors.

Keep a single definition including `verifiedCount`.

## Add a real typecheck gate

Add an npm script if missing, e.g.:

`"typecheck": "tsc --noEmit"`

Then run:
- `npm run typecheck`
- `npm run build`

Both must pass.

Vite build alone is not a TypeScript correctness proof.

## Render tests

Keep rendered activity-cost tests, but name them honestly.

Do not describe mocked hotel/transport rows embedded inside `activities` as a
real cross-source UI test.

The rendered assertion should prove:
- activity NONE/PARTIAL/FULL copy;
- no whole-trip budget verdict.

Cross-source stay/booking remains unit-only and explicitly future-facing.
