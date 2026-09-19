> **SUPERSEDED BY QODER_V5_IMPLEMENTATION_REPORT.md** — v4 报告（`QODER_V4_BLOCKED`）。v5 已闭 4 个 T2 live `/replans` blocker + 同环境零回归证明 + v13/v6 诚实修复。当前权威见 v5 报告 + TEST_RESULTS.md。

# QODER_V4_IMPLEMENTATION_REPORT — Xiaomi Truth Hardening v4 (AUTHORITATIVE)

This is the current authoritative result doc for the v4 package. For v1–v3 history
see the SUPERSEDED-marked reports; where any older doc contradicts this one,
THIS one and `TEST_RESULTS.md` win.

Role: Qoder isolated implementation / proof line. Scope fences honored —
still entirely in the isolated copy `D:\moodle\_qoder_th_20260918`. Did NOT touch
`D:\moodle\CityNexus` main tree, did NOT `git init`/merge/cherry-pick, did NOT
deploy Valhalla, did NOT start Frontend vNext, did NOT add features.

## Commit chain (isolated self-git repo)
baseline `c6f9024` → v1 `2cfa1fe` → v2 `1b8fe42`/`f02ac26` → v3 `f971771`/`ce152df`/`c47bc1f`
→ v4 `c1f94d3`(safe subset #3/#7/Valhalla-LIVE) `656baa5`(#8 Today)
`d306e01`(#6 typecheck) `d8b48db`(#1) `7bf1845`(#2) `5392c71`(#4) `cd84897`(#5+regressions).

## v4 checklist (GPT's 9 mandatory items) — status and where

1. **T2 legacy provenance fail-closed** — DONE.
   `provider_snapshots._derive_fact_quality_from_provenance`: removed the
   `SYNTHETIC_FIXTURE → EXPLICIT_FROZEN_FIXTURE` laundering; a sealed fact whose
   only signal is `SYNTHETIC_FIXTURE` (no honest `fact_quality`) is now UNKNOWN →
   rejected. `authoritative_v12` persists the real `fact_quality` at BOTH the
   `MobilityFact` seal and the recovery `evidence` payload (source =
   `mock.fact_quality()`), so `from_evidence` never has to guess. Direct
   round-trip regression: `test_qoder_mobility_truth_contract.py`
   (`test_sealed_legacy_synthetic_fixture_without_quality_fails_closed`,
   `test_explicit_fact_quality_survives_round_trip`).

2. **`_resolve_fact_quality` fail-closed** — DONE.
   `snapshot_capture._resolve_fact_quality`: provider-name heuristic removed.
   A provider must attest `fact_quality` and the classifier must not raise;
   otherwise UNKNOWN. Negative regression: `test_resolve_fact_quality_is_fail_closed`
   (absent attribute / raising / unknown-string all rejected by `hard_minutes`).

3. **`from_minutes` unknown by default** — DONE (verified).
   `MobilitySnapshot.from_minutes(fact_quality=None)`; explicit callers opt in to
   `EXPLICIT_FROZEN_FIXTURE`. Covered by `test_hard_minutes_fails_closed_on_unrecorded_quality`.

4. **live routing never falls back to mock fixture as hard truth** — DONE.
   `runtime.capture_runtime_mobility_snapshot`: when `settings.live_valhalla_url`
   is configured AND the capture is a hard replan capture
   (`require_explicit_facts=True`), `fallback=None`. A live failure →
   `MobilitySnapshotCaptureError` → `MOBILITY_DATA_UNAVAILABLE` (per-leg, other
   candidates continue). Soft/offline captures keep the pair-level mock fallback.
   Focused regression: `test_qoder_live_hard_fallback.py` (both directions).
   Inert without a live URL, so no test-env behavior change.

5. **legacy test mobility helper narrowing** — DONE (per GPT: per-module minimal
   subset, not per-test; not one shared ~25 table).
   `_qoder_explicit_demo_mobility` now exposes a distinct table per module
   (discovered empirically with a temporary probe conftest, since removed). Each
   module autouses only its own subset. v12's module-wide autouse (which seeded
   an irrelevant `place-*` table for a `v12:{journey_id}:*`-keyed journey) was
   removed — its recovery scenario self-seeds its own legs. Sentinel:
   `test_qoder_module_mobility_subsets.py` proves, per module, that a declared leg
   is EXPLICIT while an undeclared pair stays SYNTHETIC_DEFAULT (B1 intact).
   No complete-graph, no universal 15/20; every subset ≤ 3 legs.

   Module → declared legs (fixture durations, see TEST_RESULTS §3):

   | module | legs seeded (explicit deterministic fixture facts) |
   |---|---|
   | golden_contract | food-hall→river-cruise(20), tech-art→city-park(8) |
   | guardian_model | city-park→riverside-museum(17), design-library→riverside-museum(15) |
   | post_goal_five_defects | food-hall→river-cruise(20), old-town→city-park(22) |
   | solver_runtime_gate | tech-art→city-park(8), food-hall→river-cruise(20) |
   | solver_v2_integration | river-cruise→city-park(16), tech-art→city-park(8) |
   | vertical_slice | food-hall→river-cruise(20), tech-art→city-park(8) |
   | wp06_followup_assist | food-hall→river-cruise(20), old-town→city-park(22) |
   | wp06_postgate | food-hall→river-cruise(20) |

6. **typecheck covers changed UI files (no shrinking)** — DONE.
   `tsconfig.check.json` includes `V8Experience.tsx`, `LiveRecovery.tsx`,
   `LocaleContext.tsx`, `budgetEvidence.ts`, `disruptionState.ts`. Our own
   `Set<unknown>` errors were fixed. Remaining errors are pre-existing app debt:
   baseline-vs-v4 raw logs prove **0 new errors** introduced by Qoder (the 3
   V8Experience errors are identical to baseline, on lines outside our hunks; the
   other changed files yield 0). See `raw_frontend_typecheck_v4.log` and
   `raw_frontend_typecheck_v4_BASELINE.log`.

7. **T4 PARTIAL counter** — DONE. `budgetEvidence.unverifiedCount = totalCount -
   verifiedCount`; PARTIAL copy reads "还有 {n} 项缺少已验证的供应商价格". No
   "还有 0 站…不给结论" behavior. Rendered test updated to the new copy (passes).

8. **Today rendered unrelated-accepted case** — DONE.
   `qoder-ack-rendered.spec.ts` covers `/v8/today` + an unrelated ACCEPTED
   proposal still leaving the change unresolved. 9 rendered specs pass.

9. **stale docs** — DONE. v2/v3 top reports and the per-contract result docs are
   marked `SUPERSEDED BY QODER_V4_IMPLEMENTATION_REPORT.md`; the MOBILITY result
   doc's contradicting body ("None/legacy trusted") was corrected to v4 truth.

## Judgment calls GPT approved this round (constraints honored)
- **A (v12 recovery):** kept as a positive `FULLY_GROUNDED_JOURNEY` test; it
  declares its 11 itinerary legs + 1 recovery-adjacency as EXPLICIT DETERMINISTIC
  FIXTURE facts (test values, NOT real/live mobility — comment relabelled per
  your constraint). Unseeded legs stay synthetic. The independent fail-closed
  proof is the existing T2 endpoint regression (`test_qoder_mobility_replan_endpoint.py`);
  v12 was NOT repurposed as a mobility-failure test.
- **B (provider-contract doubles):** `_Provider` / `_ConstantProvider` explicitly
  attest `fact_quality → LIVE_PROVIDER_CAPTURE` (mirroring `valhalla_http`),
  rather than being name-laundered or delegating to the mock. Negative provider-
  contract tests retained (`test_resolve_fact_quality_is_fail_closed`).
- **T4 scope:** Stay/Booking are NOT wired into Studio (accepted).

## Verification (2026-09-19, isolated copy)
- **Backend full suite:** `4 failed, 810 passed, 15 skipped`. The 4
  (`aiv3_02`, `v13_integrity`, `v18_3_convergence`, `v6_predictive_real_city`) are
  all pre-existing baseline failures; NEW-vs-baseline diff is empty → **zero new
  regressions**, and **7 baseline failures now pass** (guardian_v4 ×3, v5, v7, v8,
  v15). Raw: `raw_full_backend_v4.log`; sets in `fail_baseline.txt` / `fail_v4.txt`.
- **Environmental caveat:** a live `DEEPSEEK_API_KEY` was present in the test
  process env; with it set, `test_v16_integration` (a `skipif(settings.ai_api_key)`
  bare-string SyntaxError) and `test_v14_grounded_adaptive_recovery` (real DeepSeek
  call → 502) fail for reasons unrelated to this diff. Full-suite runs here unset
  it (`DEEPSEEK_API_KEY=` / `CITYNEXUS_AI_API_KEY=`) and note this explicitly.
- **Frontend:** typecheck (5 files, 0 new errors), `vite build` ok, 9 rendered
  Playwright specs pass. Raw logs: `raw_frontend_typecheck_v4(_BASELINE).log`,
  `raw_frontend_build_v4.log`, `raw_frontend_rendered_v4.log`.

## Not done (owner / next-phase gates, explicitly out of scope)
Freeze authoritative CityNexus git baseline; integrate/cherry-pick this patch onto
an integration branch; re-run truth gates on the main tree; configure a real routing
provider; Xiamen mobility smoke; Xiaomi 13 Ultra. These are post-approval, not Qoder v4 work.
