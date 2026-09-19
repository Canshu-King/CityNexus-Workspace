# V12 Collaborative Trip Studio

Trip Studio uses a draft-only interaction followed by a server recheck.

1. The typed UI reorders the full active Activity order with drag-and-drop.
2. Preview returns a stateless `preview_id`, impact summary, protected-commitment result, frozen-evidence gaps, and deterministic-gate status without mutating the active plan.
3. Accept re-resolves the live active PlanVersion, rechecks the same evidence and protected positions, then creates a new `MANUAL` PlanVersion with parent lineage and the captured route facts.

Locked/protected positions cannot be moved. A blocked preview is visible in the impact drawer and cannot be accepted. Map geometry and offline/Edge references follow the newly accepted active PlanVersion.
