# Planner Integration

`services.generate_plans`, generic compose, selection, and revalidation now project active hard capabilities into the existing Journey constraint shape. Recovery uses the same shared gate through `validate_plan_feasibility`.

Mission compilation adds `CAPABILITY_AWARE` only when bounded capability meaning is present. The native mission plan then inserts `inspect_capabilities` after the JourneyTwin read. The existing Hermes/Gateway/Guardian authority boundary remains unchanged.

Walking constraints use explicit activity metadata or frozen mobility facts. Missing distance/time evidence is a failure requiring live evidence, not an optimistic pass. Rest and nap windows require deterministic schedule gaps.
