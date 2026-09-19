# Collaborative Trip Studio Evidence

Trip Studio is a draft-then-accept surface backed by the existing dnd-kit primitives.

1. The UI keeps a local order and does not mutate the active plan during drag.
2. Preview sends the draft order to the server.
3. The server recomputes against the current active PlanVersion, frozen mobility evidence, hard constraints, money evidence, and protected anchors.
4. The ImpactPreview shows a deterministic PASS/blocked result.
5. Accept rechecks the live base/evidence and creates a new `MANUAL` PlanVersion, superseding the base and preserving evidence identity.

The browser run used a real pointer drag after scrolling the dnd-kit rows into view, received `Impact preview passed`, accepted the edit, and observed `PlanVersion 2 · MANUAL`, `same evidence`, and `No draft changes` after the query refresh. A separate backend test swaps a protected anchor and receives `PROTECTED_ACTIVITY_REORDER` without mutation.

The final UI also resets both parent draft state and reusable sortable child state when PlanVersion changes, preventing stale Activity IDs or UUID fallback labels after accept/reload.
