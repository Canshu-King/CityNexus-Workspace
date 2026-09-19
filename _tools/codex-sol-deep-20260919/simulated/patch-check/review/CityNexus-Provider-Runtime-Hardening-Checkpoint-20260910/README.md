# CityNexus Provider Runtime Hardening Review Checkpoint

This package contains the current Provider Runtime implementation after PRH-01..PRH-05 hardening, the existing runtime source needed for reproducible review, the adversarial regression tests, freeze-gate contracts, and validation notes.

Start with `CURRENT_STATUS.md`, `TEST_RESULTS.md`, and `contracts/PROVIDER_RUNTIME_FREEZE_GATE.md`.

The package intentionally excludes `.venv`, `node_modules`, `dist`, pytest caches, Python bytecode caches, and runtime database files.
