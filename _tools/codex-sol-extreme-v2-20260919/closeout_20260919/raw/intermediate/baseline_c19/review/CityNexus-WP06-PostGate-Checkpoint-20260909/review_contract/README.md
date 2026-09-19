# CityNexus WP06 Post-Gate Deep Assist — 2026-09-09

This package contains an independent review of the deterministic WP06/JourneyTwin v2 checkpoint, a tested bounded hardening patch, and the next-stage provider/solver/AI groundwork for Codex.

## Start here

Codex should read:

1. `CODEX_NEXT_INSTRUCTION.md`
2. `00_INDEPENDENT_REVIEW.md`
3. `PATCH_APPLY_NOTES.md`
4. `03_VALHALLA_SNAPSHOT_NEXT.md`
5. `05_SCORE_AND_CANDIDATE_COUNT_NEXT.md`
6. `08_NEXT_GATE.md`

## Important

- Do not roll back the current local CityNexus working tree.
- Do not make live providers mandatory for default tests/demo.
- Do not perform SHA/file/archive hash work.
- The patch excludes OpenAPI because of cross-platform line-ending robustness; merge the supplied OpenAPI reference overlay semantically.
