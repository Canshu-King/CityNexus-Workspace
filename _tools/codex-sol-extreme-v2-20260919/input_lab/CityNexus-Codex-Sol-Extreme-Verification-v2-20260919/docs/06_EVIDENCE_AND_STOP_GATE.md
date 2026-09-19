# Evidence / stop gate

This run is successful only if it produces one of:
A. verified new defects with minimized repros and regression tests, or
B. strong negative evidence that dangerous mutations are killed and real-code
   stateful/concurrency/projection tests pass.

Do not waste the run on:
- broad full-suite reruns without a hypothesis
- rewriting existing documentation
- cosmetic refactors
- checksum busywork
- repeating abstract models without real-code execution

Required final package:
CityNexus-Codex-Sol-Extreme-Verification-v2-Results-20260919.zip

Required contents:
- EXTREME_VERIFICATION_REPORT.md
- findings.json
- mutation_manifest.json
- mutation_results.md
- RACE_CONDITION_RESULTS.md
- PROJECTION_DIVERGENCE_REPORT.md
- MOBILITY_TAINT_PROOF.md
- tests/
- replay_cases/
- candidate_patches/ (verified defects only)
- raw/

Finding severity:
P0 truth/data corruption
P1 user-visible wrong behavior / unsafe acceptance
P2 contract/integration fragility
P3 performance/maintainability

Final verdict exactly:
CODEX_SOL_EXTREME_VERIFICATION_COMPLETE
or
CODEX_SOL_EXTREME_VERIFICATION_PARTIAL

If PARTIAL, finish every unblocked track before stopping.
