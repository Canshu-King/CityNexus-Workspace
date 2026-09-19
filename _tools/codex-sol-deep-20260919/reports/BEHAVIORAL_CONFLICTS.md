# Behavioral conflicts

1. **Truth state versus visual convenience (resolved by candidate):** fixed array positions made a simple Live layout but contradicted the backend execution cursor.
2. **ACK status versus handled decision (currently resolved, fragile):** Event ACKNOWLEDGED is still open unless its exact trigger is linked to an ACCEPTED proposal. Any merge replacing `isDisruptionOpen` with a status-only filter regresses truth.
3. **Provider label versus hard eligibility (server correctly wins):** only normalized fact-quality allowlist can authorize hard routing. UI/provider names are evidence labels, not authorization.
4. **Activity cost completeness versus trip budget completeness (currently resolved):** visual copy must retain the explicit stay/transport disclaimer.
5. **Visual bounding-box success versus actual decision prominence (open owner decision):** Qoder's L2 screenshot shows the Accept CTA below the mobile fold because of the map and Copilot dock, despite geometric non-overlap gates passing. This is visual/IA, not truth corruption.

