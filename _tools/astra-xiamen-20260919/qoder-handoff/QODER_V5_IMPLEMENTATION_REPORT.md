> **SUPERSEDED BY QODER_V6_IMPLEMENTATION_REPORT.md** — v5 报告（`QODER_V5_BLOCKED`：live `/replans` 修复已被接受，仅剩 legacy provenance 推断洗白）。v6 已把它改成 exact + fail-closed。当前权威见 v6 报告 + TEST_RESULTS.md 顶部 v6 节。

# QODER_V5_IMPLEMENTATION_REPORT — Xiaomi Truth Hardening v5 (AUTHORITATIVE)

Current authoritative result for the v5 package. v4's report and earlier docs are
SUPERSEDED. Qoder remains the isolated implementation/proof line: still entirely in
`D:\moodle\_qoder_th_20260918`; did NOT touch `D:\moodle\CityNexus` main tree, no
git init/merge/cherry-pick, no Valhalla deploy, no Frontend vNext, no new features,
and did NOT reopen T1/T3/T4 (their tests still pass).

## What v4 verdict said and what v5 changed
v4 = `QODER_V4_BLOCKED`, narrowed to 4 precise T2 blockers (all on the ACTUAL
live-provider `/replans` path). Commit chain continues v4…`5392c71` → `cd84897` →
v5 `13c1639`(blockers 1-3) `450e0f9`(v13 shared seed) `e233c9e`(v6 repair).

### Blocker 1 (hard) — live `/replans` bulk-capture bypass  — CLOSED
`generate_replan`'s initial BULK mobility capture runs soft, so with a live routing
provider configured a failed live leg fell back to the mock; when that leg happened
to be an explicit demo-matrix pair it was tagged `EXPLICIT_FROZEN_FIXTURE` and
`hard_minutes()` accepted it, so the strict per-pair recapture never fired.
Fix (centralised, closes both bulk and on-demand): in
`runtime.capture_runtime_mobility_snapshot`, under a configured live provider every
mock-FALLBACK-sourced fact is downgraded to unknown quality, so a live-failed leg
can never enter hard feasibility via the mock's matrix value. That candidate stays
unavailable on the failed leg while a fully-live candidate still proceeds
(candidate-scoped). Offline demos have no fallback facts and are unaffected — they
keep using their legitimate explicit mock facts (your "engineering/demo smoke" case).

Proven by real `POST /api/v1/journeys/{id}/replans` tests in
`test_qoder_live_replans_endpoint.py` (live configured via a fake Valhalla that
fails chosen legs the mock still has explicit):
- L1 live-failed city-park leg (mock-explicit) is NOT rescued -> city-park excluded,
  fully-live design-library still yields 201.
- L2 one fully-live candidate -> 201 (proposal = that candidate), the live-failed
  candidate excluded.
- L3 all legs live-failed -> 422 `MOBILITY_DATA_UNAVAILABLE` (NOT `REPLAN_NO_ALTERNATIVE`).
- L4 the accepted proposal's hard evidence carries NO mock-sourced hard-eligible fact.
- Control (live healthy) -> 201.
NON-VACUOUS proof: with the blocker-1 downgrade removed, 4/5 of these fail (control
still passes) — recorded in the package notes.

### Blocker 2 — hard-feasibility single entry — CLOSED
`_replan_estimate` now reads `hard_minutes()` (allowlisted) after the strict
re-capture instead of raw `estimate_minutes()`; a duck-typed double that predates
quality tagging still falls back to the raw accessor. Unknown quality ->
`MobilityDataUnavailable`. Regression: existing truth + live-endpoint tests stay green.

### Blocker 3 — provenance -> LIVE promotion must be proven or closed — DONE (keep-with-proof)
The dangerous `SYNTHETIC_FIXTURE` laundering stays removed (V4 #1; still `None`). The
remaining promotions are the four labels the product's real capture/replay/seal paths
write. Proof table (label -> producer -> why it cannot be the blanket mock-20 -> regression):

| legacy label promoted to LIVE | who writes it | why not blanket mock-20 | regression |
|---|---|---|---|
| `*LIVE*` / `LIVE_CAPTURE` | `ValhallaHTTPMobilityProvider` (valhalla_http) real matrix capture | a measured routing response, never the offline default | `test_provider_runtime_gate` (prt02 real-provider provenance), `test_qoder_live_replans_endpoint` |
| `CAPTURED_REPLAY` | `snapshot_capture`/`authoritative_v12` provider_provenance for a captured replay matrix of real_city `captured_replay` places | a frozen provider matrix captured before the gate, not the fixture constant | `test_v12_authoritative_trip_execution`, `test_v13_integrity` (grounded compose/execute) |
| `SEALED*` (`SEALED_INCIDENT_REPLAY`, `SEALED_REAL_REPLAY`) | incident-recovery seal reusing a provider-captured incident matrix | a per-incident captured matrix frozen into evidence | `test_v14_grounded_adaptive_recovery` |
| `RUNTIME_CAPTURE` | runtime on-demand capture of the real provider | a live capture at replan time | `test_qoder_mobility_replan_endpoint`, `test_qoder_live_hard_fallback` |

Every fact that flows through the current product capture now also persists an
explicit `fact_quality` (V4 #1), so the promotion branch is a legacy backstop for
exactly these four provenances. Going forward, `from_evidence` reads the explicit
quality first. If a row cannot be attributed to one of these producers it is `None`
and refused.

### Blocker 4 — strict SAME-environment zero-regression proof — DONE
Both baseline `c6f9024` and patched HEAD were run in the IDENTICAL sanitized env with
`DEEPSEEK_API_KEY=` and `CITYNEXUS_AI_API_KEY=` cleared.
- Baseline (clean): `2 failed, 756 passed` + a `test_v9_real_trip_operations`
  collection `FileNotFoundError` that is a git-worktree copy artifact (missing
  generated file), not a code failure. Real failures: `test_aiv3_02`, `test_v18_3`.
- Patched (clean): `2 failed, 817 passed, 15 skipped` — the SAME two real failures
  (`test_aiv3_02`, `test_v18_3`), no collection error (main tree has the artifact).
- NEW-vs-baseline (same env) = **∅**. 817-756 = +61 passing tests are Qoder's new
  regressions/fixtures plus the two repairs below.

### Two truth-gate casualties surfaced by the same-env proof — repaired honestly
Clearing the key (correctly) exposed that `test_v13_authoritative_predictive_recovery`
and `test_v6_predictive_real_city_twin` had been failing only on DeepSeek at the noisy
with-key baseline, but actually pass at clean baseline and were broken by the T2 allowlist
(latent since v3). They are the same class as v12: legacy journeys whose mobility was
laundered. Repaired the GPT-approved way — the scenarios now declare their exact route
legs as explicit deterministic fixture facts (not real mobility):
- v13 shares v12's journey -> same `seed_authoritative_recovery_mobility` (12 legs).
- v6's offline real-city REPLAY journey -> declares the 9 concrete replay+demo legs it
  traverses (stable replay ids), both directions.
B1 stays intact: any leg outside those tables is still SYNTHETIC_DEFAULT/unavailable.

## Scope note
T1 / T3 / T4 untouched (their regression tests remain green; 9 rendered Playwright specs
still pass; typecheck still covers the 5 UI/lib files with 0 new errors). No new product
behavior beyond the four blockers. This was not treated as a v6 archaeology round.

## Remaining owner/next-phase gates (out of Qoder scope)
Freeze main-repo authoritative git baseline -> integration branch -> reconcile patch ->
rerun truth gates on main -> deploy/configure a trustworthy routing provider -> Xiamen
mobility smoke -> Xiaomi 13 Ultra.
