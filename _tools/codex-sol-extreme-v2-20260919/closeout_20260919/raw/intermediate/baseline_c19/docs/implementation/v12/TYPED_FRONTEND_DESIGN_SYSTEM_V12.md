# V12 Typed Frontend Design System

The V12 surface is typed from `contracts/openapi.yaml` through `openapi-typescript`, TanStack Query hooks, and the execution components. The authoritative page exposes the PlanVersion evidence badge, NOW/NEXT execution rail, actual state transitions, and Trip Studio draft/impact/accept states. Shared primitives cover ActivityCard, JourneyLeg, CommitmentCard, ImpactPreview, RiskBanner, AgentAction, OfflineBanner, EdgeStatus, and LiveJourney.

Storybook/MSW fixtures cover `NOT_STARTED`, `EN_ROUTE`, `ARRIVED`, `IN_PROGRESS`, `ACTIVE`, `COMPLETED`, `SKIPPED`, and offline read-only presentation. The MapLibre lifecycle calls `resize()` from a `ResizeObserver` and consumes the active plan's frozen leg geometry.
