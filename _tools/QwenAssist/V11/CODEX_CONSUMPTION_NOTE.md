# How Codex should consume Qwen output

Codex should NOT blindly apply all Qwen patches.

Recommended order:

1. Read only `QWEN_HANDOFF_TO_CODEX.md`.
2. Pull specific candidate test/helper files referenced there.
3. Verify code-location findings against the current worktree.
4. Use Qwen edge-case matrices to strengthen gates.
5. Use UI copy/design artifacts selectively.
6. Keep architectural decisions in the main CityNexus plan.

This sidecar exists to save Codex tokens/time, not to create a second source of truth.
