# Scope and boundaries

Qoder is actively reconciling the integrated frontend and legacy E2E behavior.
Do not duplicate or interfere with that work.

Allowed:
- read current trees;
- create reports, scripts and test scaffolding under
  `D:\moodle\_codex_parallel_20260919`;
- self-test isolated scripts;
- package evidence.

Forbidden:
- writes to `_qoder_integration_20260919`, `_qoder_th_20260918`, or `CityNexus`;
- main-repo Git init/merge/cherry-pick/reset/clean;
- Valhalla deployment;
- frontend Today/Live edits;
- truth-contract edits;
- repairing the legacy E2E tests Qoder is currently handling.
