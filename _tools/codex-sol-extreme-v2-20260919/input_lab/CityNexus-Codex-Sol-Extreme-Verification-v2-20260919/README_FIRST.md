# CityNexus — Codex Sol Extreme Verification v2

This mission is intentionally harder than the previous Sol Deep Mission.

Why:
The previous run found CX-SOL-001, but its 400k-transition state-machine audit
was mostly an abstract-model consistency test. This v2 mission must attack the
REAL CityNexus code through real APIs, real persistence, real projection code,
targeted mutation testing, concurrency, and differential oracles.

READ-ONLY INPUT TREES:
- D:\moodle\_qoder_integration_20260919
- D:\moodle\_qoder_th_20260918
- D:\moodle\CityNexus

ALL WRITES:
- D:\moodle\_codex_sol_extreme_v2_20260919

Important:
- Never modify/reset/clean/merge/cherry-pick the input trees.
- Create a disposable committed snapshot/clone under the output directory.
- If the active Qoder integration tree is dirty or moving, do NOT treat its
  uncommitted state as an authoritative merge source.
- Do not duplicate the current Qoder legacy-E2E repair task.
