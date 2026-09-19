# Deep Track G — Semantic merge / reconciliation simulator

Goal:
Go beyond Git textual conflicts and predict behavioral conflicts before owner
integration.

Inputs:
- authoritative/main tree
- Qoder v6 truth handoff/patch
- Apple frontend Pass1-5 handoff/patch
- current integration tree as read-only evidence

Create disposable candidate worktrees/copies under the Codex output directory.

Build:
- `reports/SEMANTIC_MERGE_MAP.md`
- `reports/FILE_OVERLAP_MATRIX.md`
- `reports/BEHAVIORAL_CONFLICTS.md`
- `reports/RECOMMENDED_RECONCILIATION_ORDER.md`
- `artifacts/reconcile_manifest.json`

For every overlapping file/symbol:
- describe baseline behavior;
- describe truth-line behavior;
- describe frontend-line behavior;
- distinguish additive vs conflicting changes;
- state which semantics must win and why;
- identify exact tests/gates that prove the merge preserved behavior.

Especially inspect:
- V8Experience.tsx
- LiveRecovery.tsx
- main.tsx
- v8Types.ts
- v10Execution.ts
- provider snapshots / runtime mobility capture
- replan endpoint code
- i18n mappings
- rendered truth tests

Where safe, create a disposable simulated reconciliation and run focused gates.
Do not merge to the user's real repositories.
