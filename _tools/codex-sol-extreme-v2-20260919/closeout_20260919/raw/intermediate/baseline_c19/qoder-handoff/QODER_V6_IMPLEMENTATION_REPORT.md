# QODER_V6_IMPLEMENTATION_REPORT — Xiaomi Truth Hardening v6 (AUTHORITATIVE)

Current authoritative result for the v6 package. v5's report and earlier docs are
SUPERSEDED. Isolated implementation line only; `D:\moodle\CityNexus` untouched; no
git init/merge/cherry-pick; no Valhalla deploy; no Frontend vNext; T1/T3/T4 not
reopened (their tests remain green); the legacy test helper was not touched this round.

## Context
v5 verdict = `QODER_V5_BLOCKED` with the live `/replans` fix ACCEPTED and exactly
ONE narrow code blocker left: legacy provenance inference in
`_derive_fact_quality_from_provenance` still laundered via BROAD rules
(`"LIVE" in prov`, `prov.startswith("SEALED")`, promote `CAPTURED_REPLAY`/
`RUNTIME_CAPTURE`) — wider than the proof table claimed. Historical seal labels
`SEALED_REAL_REPLAY_WITH_EXPLICIT_SYNTHETIC_FALLBACK` and
`SEALED_REPLAY_OR_SYNTHETIC_FIXTURE_EXPLICIT` start with "SEALED" -> were promoted to
LIVE despite naming SYNTHETIC in the label. v6 closes exactly this.

## v6 change (commit 3ae7cd8)
`_derive_fact_quality_from_provenance` is now EXACT + fail-closed:
1. an explicit persisted `fact_quality` always wins;
2. ONLY the exact label `LIVE_CAPTURE` (emitted solely by the real valhalla capture)
   maps to `LIVE_PROVIDER_CAPTURE`;
3. `CAPTURED_REPLAY`, any `SEALED*`, `RUNTIME_CAPTURE`, substring/prefix, and every
   unrecognised legacy label -> `None` (UNKNOWN) -> `hard_minutes` refuses.
No substring/prefix matching remains. A row must now carry an explicit, honest
quality (or be re-captured) — "looks sealed/live" no longer earns a hard-truth passport.

Stale comments corrected: `TravelEstimateFact.fact_quality` and
`hard_minutes`'s docstring no longer claim "None/legacy trusted" — they now state
the true allowlist and that unknown/None fails closed.

## Honest producer-side quality persistence (so genuine captures stay trusted
without re-introducing inference)
The exact rule is only safe if real captures carry an explicit quality. Three
producers that previously relied on the removed label-guessing now attest honestly:
- `runtime.capture_journey_mobility_matrix`: each valhalla `matrix()` result fact is
  stamped `fact_quality=LIVE_PROVIDER_CAPTURE` (it is a live capture at source).
- `main._grounded_recovery_reserve_snapshot`: passes the captured source fact's
  `fact_quality` through instead of dropping it.
- the captured Tianjin replay fixture `data/replay/tianjin_v135_journey_snapshot.json`
  (a SEALED_LIVE_CAPTURE valhalla artifact): its 128 mobility facts now record
  `fact_quality=LIVE_PROVIDER_CAPTURE` — the sealed artifact declares its own captured
  provenance explicitly rather than being inferred by the gate.
This is why the previously-green grounded tests (v12/v13/v14/v6) stay green WITHOUT
any provenance guessing: they carry explicit quality.

## Regressions (targeted legacy-payload, per LEGACY_PROVENANCE_EXACT_GATE)
`test_qoder_mobility_truth_contract.py`:
- `test_v6_ambiguous_legacy_provenance_fails_closed[...]` parametrized over
  `SEALED_REAL_REPLAY_WITH_EXPLICIT_SYNTHETIC_FALLBACK`,
  `SEALED_REPLAY_OR_SYNTHETIC_FIXTURE_EXPLICIT`, `CAPTURED_REPLAY`,
  `RUNTIME_CAPTURE`, `SEALED_INCIDENT_REPLAY` -> all resolve to None.
- `test_v6_only_exact_live_capture_promotes` -> LIVE_CAPTURE -> LIVE.
- `test_v6_explicit_quality_overrides_provenance_label` -> explicit wins.
- `test_v6_sealed_synthetic_fallback_payload_hard_rejects` -> a from_evidence payload
  with route_provenance=SEALED_*_SYNTHETIC_FALLBACK and no fact_quality -> hard raises.

## Verification
- Dedicated focused raw log (each L1/L2/L3/L4 shown PASS individually) in
  `raw_v6_focused_live_endpoint_and_provenance.log` (29 passed: 5 live-endpoint +
  full truth-contract incl the new v6 cases).
- Same sanitized environment (`DEEPSEEK_API_KEY=` and `CITYNEXUS_AI_API_KEY=`):
  patched full backend = `2 failed / 825 passed / 15 skipped`; the two failures
  (`test_aiv3_02`, `test_v18_3`) are exactly the clean baseline's real failures
  (`raw_full_backend_v5_baseline_SANITIZED.log` shows the same two) ->
  **NEW-vs-baseline = ∅**. The baseline's v9 collection error is a git-worktree
  copy artifact, not a code failure, and is absent on the main tree.
- Frontend untouched this round (v6 is backend-only per GPT): typecheck gate (5 files,
  0 new errors), build, and 9 rendered specs remain as in v5.

## Scope honored
Did not touch the live replan algorithm (only provenance + honest quality persistence),
T1/T3/T4, the test helper, or the frontend. v5's accepted live fix is preserved intact.

## Next phase (after approval — owner gates, out of Qoder scope)
Freeze main-repo authoritative git baseline -> integration branch -> manually
reconcile the cumulative Qoder patch -> rerun T1-T4 / live-replan / typecheck / build
on main -> configure a trustworthy routing provider -> Xiamen real mobility smoke ->
Xiaomi 13 Ultra fresh trial. Per GPT, a clean v6 ends the isolated archaeology line;
there should be no v7.
