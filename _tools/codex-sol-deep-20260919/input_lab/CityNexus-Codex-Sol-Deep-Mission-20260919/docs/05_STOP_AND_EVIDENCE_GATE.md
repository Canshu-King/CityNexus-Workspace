# Stop / evidence gate

Do not spend most of the run on:
- repeating already-green broad suites without a hypothesis;
- rewriting documentation that already exists;
- prettier formatting;
- hash checking;
- package inventory busywork.

Spend time on:
- source-level reasoning;
- semantic diffing;
- state-space exploration;
- shrinking concrete counterexamples;
- reproducible failure cases;
- executable harnesses.

Final package:
`CityNexus-Codex-Sol-Deep-Mission-Results-20260919.zip`

Required:
- README.md
- SOL_DEEP_MISSION_REPORT.md
- reports/
- artifacts/
- tests/
- candidate_patches/ (only if real defects found)
- raw/

Rank findings:
- P0 truth/corruption
- P1 product behavior
- P2 integration risk
- P3 performance/maintainability

For each finding include:
- proof
- affected path/symbol
- minimal repro
- whether it is already covered by Qoder/current integration
- recommended owner action

Final verdict exactly:
`CODEX_SOL_DEEP_MISSION_COMPLETE`
or
`CODEX_SOL_DEEP_MISSION_PARTIAL`
