# Accessibility Truth Evidence

The deterministic gate normalizes provider/frozen metadata into `ACCESSIBILITY_VERIFIED`, `ACCESSIBILITY_UNVERIFIED`, `ACCESSIBILITY_CONFLICT`, or `NEEDS_LIVE_EVIDENCE`.

For `STEP_FREE_REQUIRED` and `AVOID_STAIRS`, a missing or incomplete evidence object fails with both `ACCESSIBILITY_UNVERIFIED:<location>` and `NEEDS_LIVE_EVIDENCE:<location>`. Explicit conflict fails with `ACCESSIBILITY_CONFLICT:<location>`. Only verified provider/frozen evidence passes.

Focused test evidence: `test_unknown_accessibility_is_not_accessible` and `test_feasibility_blocks_unknown_and_conflicting_step_free_evidence` pass.
