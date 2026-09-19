# Semantic Merge Decisions

## Bundle patch handling

The implementation patch was inspected but not blindly applied. The first
preflight after importing the two supplied reference tests reported that those
test files already existed in the working directory. The current source also
contained newer provider error validation, provenance handling, verified
scoring, deterministic tie ordering, and verified-evidence fields. The source
changes were therefore merged by behavior with apply_patch, preserving those
newer sections.

## Five required repairs

1. F3_OPPORTUNITY_WINDOW now derives its effective trigger time from
   Event.occurred_at, normalizes timezone-free simulator input to the Journey
   schedule offset, evaluates opening/buffer evidence from that instant, and
   persists the replacement start as window opening plus inbound travel.

2. Accepted replans now remap every active C4 Commitment.activity_id by the
   durable semantic identity plus scheduled relative start into the new active
   PlanVersion. A missing mapping fails closed with HTTP 409.

3. validate_plan_feasibility and validate_selected_plan_feasibility now accept
   an injected mobility provider/snapshot while retaining MockMobilityProvider
   as the default.

4. Open-Meteo requests UTC Unix timestamps, parses numeric Unix time into
   timezone-aware UTC datetimes, and keeps compatible ISO fixtures explicitly
   timezone-aware.

5. TRAFFIC_DELAY prefers payload.extra_minutes and SCHEDULE_DELAY prefers
   payload.delay_minutes, with the alternate key as compatibility fallback.

## Frontend boundary

The supplied API client, Golden Scenario helper, and XState workflow were
adapted to the current backend response shapes. Backend responses own all
JourneyTwin, PlanVersion, Commitment, Event, Replan, feasibility, score, and
provider evidence. XState owns only UI workflow state. localStorage stores only
the reconnect journey_id. The map remains a presentation surface and no live
map or provider is required.
