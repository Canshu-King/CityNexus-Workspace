# CityNexus Codex Sol Deep Mission results

This package completes Deep Tracks E–H against frozen integration commit `1de4e0c569349d7eee4bc22995cc49c487e3279e`. The authoritative repository and Qoder worktrees were read-only; all experiments and the candidate patch were isolated here.

## Start here

1. Read `SOL_DEEP_MISSION_REPORT.md`.
2. Review verified findings in `artifacts/findings.json`.
3. Inspect the machine-readable contract in `artifacts/contract_graph.json`.
4. Run `python tests/repro_live_current_activity.py`.
5. Owner-review `candidate_patches/CX-SOL-001-live-current-activity.patch` and its Playwright regression.

## Executable tools

- `tests/stateful_recovery_audit.py`: deterministic randomized state-machine audit; defaults to 400,000 transitions.
- `tests/repro_live_current_activity.py`: minimized CX-SOL-001 counterexample.
- `tests/repro_ack_linkage.py`: ACK/linkage contract proof.
- `tests/semantic_overlap.py`: regenerates symbol overlap from the disposable Git history.

## Boundaries

- No infrastructure was deployed and Valhalla was not enabled.
- No secrets are included.
- External map-tile outage was modeled/static-inspected rather than induced.
- The `simulated/` and `input_lab/` working directories are intentionally excluded from the result ZIP; all durable evidence is copied into reports, artifacts, tests and candidate patches.

Verdict: `CODEX_SOL_DEEP_MISSION_COMPLETE`

