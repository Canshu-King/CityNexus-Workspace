# Package Manifest

## Review documents

- `SOL_V2_CLOSEOUT_REPORT.md`
- `CONVERGENCE_MATRIX.md`
- `findings.json`
- `RACE_CONDITION_RESULTS.md`
- `PROJECTION_DIVERGENCE_REPORT.md`
- `MOBILITY_TAINT_PROOF.md`
- `mutation_results.md`
- `mutation_manifest.json`

## Candidate and executable evidence

- `candidate_patch/0001-candidate-close-C4-ambiguity-and-cursor-convergence-.patch`
- `focused_tests/test_sol_v2_closeout.py`
- `focused_tests/test_extreme_real_api.py`
- `focused_tests/extreme-live-projection.spec.ts`
- `replay_cases/concurrency_harness.py`
- `replay_cases/projection_oracle.py`
- `replay_cases/real_api_state_machine.py`
- `replay_cases/mutation_runner.py`

## Final raw evidence

- full backend regression and focused truth-contract logs
- state-machine, race, projection, browser, build, and typecheck logs
- machine-readable race, projection, and mutation results
- baseline typecheck comparison proving zero candidate diagnostic delta

`raw/intermediate/` contains only the superseded dependency-missing backend run and is explicitly non-final. Databases, caches, `__pycache__`, and `.pyc` files are excluded from the package.
