# V19.2.1 Real-Phone Shadow-Trial Gate

Status: `SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE`

The live V19.2.1 tree contains the reviewed capability/evidence and planning
consistency fixes required for a real-phone shadow trial. Focused regression is
green (24 tests), and the frontend production build is green.

This package does not claim a physical phone run, production payment, or
unattended mutation. Native Hermes is also not claimed: the local runtime probe
was unavailable because the backend was stopped, and the previously observed
status had `ready: false`/`native_mcp_proven: false`.

Next gate: execute PHONE_TRIAL_RUNBOOK.md on a controlled device, capture run
IDs and browser/backend evidence, then review before any production exposure.
