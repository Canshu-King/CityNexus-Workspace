from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from itertools import permutations
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.execution.traveler_twin import capability_constraint_items
from app.core.audit import record_audit
from app.db.models import (
    Activity,
    CityService,
    Commitment,
    Journey,
    JourneyConstraint,
    Place,
    PlanVersion,
    Preference,
    Traveler,
    TravelerTwinSnapshot,
)
from app.integrations.mock.providers import MockCityDataProvider
from app.integrations.mobility.runtime import capture_runtime_mobility_snapshot
from app.replanning.feasibility import (
    FeasibilityActivity,
    FeasibilityResult,
    activity_from_record,
    build_context,
    evaluate_feasibility,
)
from app.replanning.provider_snapshots import MobilitySnapshot
from app.planning.anchor_schedule import (
    ANCHOR_DURATION_MIN,
    CandidateActivity,
    MID_TRIP_ROLE,
    effective_journey_window,
    resolve_plan_anchors,
    schedule_template_with_anchors,
    validate_anchor_timeline,
)
from app.replanning.protected_commitments import active_c4_hard_constraints
from app.replanning.reference_replanner import WEIGHTS
from app.schemas import Activity as ActivitySchema
from app.schemas import CityService as CityServiceSchema
from app.schemas import Constraint as ConstraintSchema
from app.schemas import Journey as JourneySchema
from app.schemas import Money, ScoreBreakdown
from app.schemas import Place as PlaceSchema
from app.schemas import PlanVersion as PlanSchema
from app.schemas import Preference as PreferenceSchema
from app.schemas import Traveler as TravelerSchema

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MOCK_ROOT = PROJECT_ROOT / "data" / "mock"
DEMO_NAMESPACE = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _journey_constraints_with_capabilities(
    session: Session, journey: Journey, *, active_only: bool = False, include_c4: bool = True
) -> list[Any]:
    query = select(JourneyConstraint).where(JourneyConstraint.journey_id == journey.id)
    if active_only:
        query = query.where(JourneyConstraint.active.is_(True))
    constraints: list[Any] = list(session.scalars(query).all())
    constraints.extend(capability_constraint_items(session, journey.traveler_id, journey.id))
    if include_c4:
        commitments = session.scalars(
            select(Commitment).where(
                Commitment.journey_id == journey.id,
                Commitment.status == "ACTIVE",
                Commitment.level == "C4_Anchored",
            )
        ).all()
        constraints.extend(active_c4_hard_constraints(commitments))
    return constraints


def load(name: str) -> Any:
    return json.loads((MOCK_ROOT / name).read_text(encoding="utf-8"))


def deterministic_id(label: str) -> str:
    return str(uuid5(DEMO_NAMESPACE, label))


def reset_all(session: Session) -> None:
    # Delete children first because the package schema intentionally enables FKs.
    for table in (
        "edge_actions",
        "edge_observations",
        "edge_devices",
        "push_subscriptions",
        "location_observations",
        "offline_journey_snapshots",
        "notification_events",
        "journey_legs",
        "transport_reservations",
        "external_reservation_drafts",
        "journey_operations_contexts",
        "counterfactual_simulations",
        "guardian_runs",
        "agent_run_steps",
        "agent_runs",
        "journey_missions",
        "guardian_pulses",
        "provider_observations",
        "journey_outcome_events",
        "traveler_preference_evidence",
        "traveler_capabilities",
        "traveler_twin_snapshots",
        "city_signal_fixtures",
        "autopilot_enrollments",
        "real_place_candidates",
        "mobility_facts",
        "stay_journey_options",
        "accommodation_offer_snapshots",
        "journey_trip_contexts",
        "journey_resilience_snapshots",
        "audit_logs",
        "provider_calls",
        "idempotency_keys",
        "action_approvals",
        "replan_proposals",
        "recommendations",
        "impact_assessments",
        "transactions",
        "orders",
        "bookings",
        "commitments",
        "events",
        "journey_twins",
        "activities",
        "plan_versions",
        "constraints",
        "city_services",
        "places",
        "journeys",
        "preferences",
        "traveler_agent_policies",
        "travelers",
    ):
        session.connection().execute(text(f'DELETE FROM "{table}"'))
    session.expire_all()
    session.commit()


def seed_demo(session: Session) -> dict[str, str]:
    reset_all(session)
    # The fixture is deliberately frozen so two reset/seed runs produce the
    # same logical rows and byte-identical exported records.
    now = "2026-10-01T00:00:00+00:00"
    traveler_data = load("traveler_demo.json")
    traveler = Traveler(
        id=traveler_data["id"],
        display_name=traveler_data["display_name"],
        email=traveler_data["email"],
        locale=traveler_data["locale"],
        timezone=traveler_data["timezone"],
        created_at=now,
        updated_at=now,
    )
    session.add(traveler)
    session.flush()
    session.add(
        TravelerTwinSnapshot(
            traveler_id=traveler.id,
            explicit_preferences_json="[]",
            learned_soft_preferences_json="[]",
            conflicts_json="[]",
            confidence=0.0,
            evidence_count=0,
            provenance_json=dump({"source": "seed", "updated_at": now}),
            updated_at=now,
        )
    )
    for index, item in enumerate(traveler_data["preferences"], start=1):
        session.add(
            Preference(
                id=deterministic_id(f"preference:{index}"),
                traveler_id=traveler.id,
                category=item["category"],
                preference_key=item["key"],
                value_json=dump(item["value"]),
                weight=item["weight"],
                source="user",
                created_at=now,
                updated_at=now,
            )
        )
    city_provider = MockCityDataProvider()
    for item in city_provider.places():
        session.add(
            Place(
                id=item["id"],
                provider_key=item["provider_key"],
                external_id=item["external_id"],
                city_code=item["city_code"],
                name=item["name"],
                category=item["category"],
                latitude=item["location"]["latitude"],
                longitude=item["location"]["longitude"],
                opening_hours_json=dump({"open": item["open"], "close": item["close"]}),
                tags_json=dump(item["tags"]),
                metadata_json=dump(
                    {"duration_min": item["duration_min"], "cost_minor": item["cost_minor"]}
                ),
                updated_at=now,
            )
        )
    session.flush()
    for item in city_provider.city_services():
        session.add(
            CityService(
                id=item["id"],
                provider_key=item["provider_key"],
                external_id=item["external_id"],
                place_id=item["place_id"],
                city_code=item["city_code"],
                service_type=item["service_type"],
                name=item["name"],
                availability_json=dump(item["availability"]),
                metadata_json=dump({}),
                updated_at=now,
            )
        )
    # WP04's supplied commerce overlay extends the frozen mock city catalog
    # with the bookable River Cruise and tradable Food Hall services.  Keep the
    # overlay additive so the WP00-WP03 city fixtures remain unchanged.
    for item in load("wp04_city_services_overlay.json"):
        session.add(
            CityService(
                id=item["id"],
                provider_key=item["provider_key"],
                external_id=item["external_id"],
                place_id=item.get("place_id"),
                city_code=item["city_code"],
                service_type=item["service_type"],
                name=item["name"],
                availability_json=dump(item.get("availability", {})),
                metadata_json=dump({"source": "wp04_commerce_catalog.json"}),
                updated_at=now,
            )
        )
    journey_data = load("demo_journey.json")["journey"]
    journey = Journey(
        id=journey_data["id"],
        traveler_id=journey_data["traveler_id"],
        title=journey_data["title"],
        city_code=journey_data["city_code"],
        timezone=journey_data["timezone"],
        start_at=journey_data["start_at"],
        end_at=journey_data["end_at"],
        budget_currency=journey_data["budget"]["currency"],
        budget_amount_minor=journey_data["budget"]["amount_minor"],
        planning_mode=journey_data.get("planning_mode", "balanced"),
        status="DRAFT",
        active_plan_version_id=None,
        current_activity_id=None,
        created_at=now,
        updated_at=now,
    )
    session.add(journey)
    session.flush()
    for index, item in enumerate(load("demo_journey.json")["constraints"], start=1):
        session.add(
            JourneyConstraint(
                id=deterministic_id(f"constraint:{index}"),
                journey_id=journey.id,
                kind=item["kind"],
                category=item["category"],
                rule_code=item["rule_code"],
                params_json=dump(item["params"]),
                weight=item["weight"],
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
    session.commit()
    return {
        "traveler_id": traveler.id,
        "journey_id": journey.id,
        "city_code": journey.city_code,
    }


def traveler_schema(item: Traveler) -> TravelerSchema:
    return TravelerSchema(
        id=item.id,
        display_name=item.display_name,
        email=item.email,
        locale=item.locale,
        timezone=item.timezone,
        created_at=parse_dt(item.created_at),
        updated_at=parse_dt(item.updated_at),
    )


def preference_schema(item: Preference) -> PreferenceSchema:
    return PreferenceSchema(
        id=item.id,
        traveler_id=item.traveler_id,
        category=item.category,
        key=item.preference_key,
        value=json.loads(item.value_json),
        weight=item.weight,
    )


def journey_schema(item: Journey) -> JourneySchema:
    return JourneySchema(
        id=item.id,
        traveler_id=item.traveler_id,
        title=item.title,
        city_code=item.city_code,
        timezone=item.timezone,
        start_at=parse_dt(item.start_at),
        end_at=parse_dt(item.end_at),
        budget=Money(amount_minor=item.budget_amount_minor, currency=item.budget_currency),
        planning_mode=item.planning_mode,
        status=item.status,
        active_plan_version_id=item.active_plan_version_id,
        current_activity_id=item.current_activity_id,
    )


def constraint_schema(item: JourneyConstraint) -> ConstraintSchema:
    return ConstraintSchema(
        id=item.id,
        journey_id=item.journey_id,
        kind=item.kind,
        category=item.category,
        rule_code=item.rule_code,
        params=json.loads(item.params_json),
        weight=item.weight,
        active=bool(item.active),
    )


def place_schema(item: Place) -> PlaceSchema:
    return PlaceSchema(
        id=item.id,
        name=item.name,
        category=item.category,
        city_code=item.city_code,
        location={"latitude": item.latitude, "longitude": item.longitude},
        tags=json.loads(item.tags_json),
    )


def service_schema(item: CityService) -> CityServiceSchema:
    return CityServiceSchema(
        id=item.id,
        name=item.name,
        service_type=item.service_type,
        city_code=item.city_code,
        place_id=item.place_id,
    )


def _activity_cost_status(
    item: Activity, metadata: dict[str, Any], place: Place | None
) -> str:
    """Whether this activity's price is a real fact.

    Order of evidence:
    1. an explicit status on the activity metadata wins;
    2. the Place's own price evidence (``price_known``) decides, because a
       discovered place knows whether its price was actually captured;
    3. otherwise a positive amount is treated as a known price.
    """

    explicit = str(
        metadata.get("cost_status") or metadata.get("price_status") or ""
    ).upper()
    if explicit in {"KNOWN", "KNOWN_FREE", "KNOWN_PAID", "UNKNOWN"}:
        if explicit == "KNOWN":
            return "KNOWN_PAID" if item.estimated_cost_minor > 0 else "KNOWN_FREE"
        return explicit
    price_known = metadata.get("price_known")
    if price_known is None and place is not None:
        try:
            place_metadata = json.loads(place.metadata_json or "{}")
        except (TypeError, ValueError):
            place_metadata = {}
        price_known = place_metadata.get("price_known")
    if price_known is True:
        return "KNOWN_PAID" if item.estimated_cost_minor > 0 else "KNOWN_FREE"
    if price_known is False:
        return "UNKNOWN"
    return "KNOWN_PAID" if item.estimated_cost_minor > 0 else "UNKNOWN"


def activity_schema(item: Activity, place: Place | None = None) -> ActivitySchema:
    """Project one activity, resolving coordinates from its Place row.

    Activity Detail must show real Place coordinates (Snapshot M contract).
    The activity metadata only carries them on some paths, so the Place row is
    the authoritative source and is merged in here.
    """

    metadata = json.loads(item.metadata_json or "{}") if item.metadata_json else {}
    if place is not None:
        metadata.setdefault("latitude", place.latitude)
        metadata.setdefault("longitude", place.longitude)
        metadata.setdefault("crs", "WGS84")
        if place.category:
            metadata.setdefault("category", place.category)
        if place.opening_hours_json and "opening_hours" not in metadata:
            try:
                metadata["opening_hours"] = json.loads(place.opening_hours_json)
            except (TypeError, ValueError):
                pass
    return ActivitySchema(
        id=item.id,
        sequence_no=item.sequence_no,
        title=item.title,
        activity_type=item.activity_type,
        place_id=item.place_id,
        city_service_id=item.city_service_id,
        start_at=parse_dt(item.start_at),
        end_at=parse_dt(item.end_at),
        travel_from_prev_min=item.travel_from_prev_min,
        estimated_cost=Money(amount_minor=item.estimated_cost_minor, currency=item.currency),
        cost_status=_activity_cost_status(item, metadata, place),
        status=item.status,
        locked=bool(item.locked),
        metadata=metadata,
    )


def _plan_staleness(item: PlanVersion) -> tuple[bool, str | None]:
    """Whether a plan's frozen provider evidence makes it unusable as-is.

    This is a *projection* only; ``select`` revalidation remains the authority.
    """

    try:
        evidence = json.loads(item.mobility_evidence_json or "{}")
    except json.JSONDecodeError:
        return True, "STALE_RECOMPOSE_REQUIRED: mobility evidence is not readable"
    if not isinstance(evidence, dict) or not evidence.get("snapshot_id"):
        return True, "STALE_RECOMPOSE_REQUIRED: no frozen provider evidence"
    expires_at = evidence.get("expires_at")
    if expires_at:
        try:
            if datetime.fromisoformat(str(expires_at)) <= datetime.now(timezone.utc):
                return True, "STALE_RECOMPOSE_REQUIRED: frozen provider evidence expired"
        except ValueError:
            return True, "STALE_RECOMPOSE_REQUIRED: evidence timestamp invalid"
    return False, None


def plan_schema(session: Session, item: PlanVersion) -> PlanSchema:
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == item.id).order_by(Activity.sequence_no)
    ).all()
    # Activity Detail needs real Place coordinates and opening hours, so the
    # Place rows are resolved once here rather than per activity.
    place_ids = {str(a.place_id) for a in activities if a.place_id}
    places_by_id: dict[str, Place] = {}
    if place_ids:
        places_by_id = {
            place.id: place
            for place in session.scalars(select(Place).where(Place.id.in_(place_ids))).all()
        }
    breakdown = _plan_score_breakdown(item)
    # Stale/recompose-required projection: an expired or evidence-less plan is
    # flagged so the API and UI never present it as a current recommendation.
    stale, stale_reason = _plan_staleness(item)
    return PlanSchema(
        id=item.id,
        journey_id=item.journey_id,
        version_no=item.version_no,
        planning_mode=item.planning_mode,
        status=item.status,
        source=item.source,
        parent_plan_version_id=item.parent_plan_version_id,
        total_cost=Money(amount_minor=item.total_cost_minor, currency=item.currency),
        utility_score=item.utility_score,
        score_breakdown=breakdown,
        activities=[
            activity_schema(a, places_by_id.get(str(a.place_id)))
            for a in activities
        ],
        mobility_snapshot_id=item.mobility_snapshot_id,
        mobility_evidence=json.loads(item.mobility_evidence_json or "{}"),
        explanation=json.loads(item.explanation_json or "{}"),
        stale=stale,
        selectable=not stale,
        stale_reason=stale_reason,
    )


def _plan_score_breakdown(item: PlanVersion) -> ScoreBreakdown | None:
    """Project legacy persisted score rows into the current public contract.

    V8/V9 materialization stored provider totals (for example ``stay`` and
    ``mobility``) rather than the normalized score dimensions introduced by
    the current PlanVersion schema.  Those rows remain valid historical
    plans, so listing a Journey must not fail merely because a newer client
    reads them.  New writers continue to persist the full breakdown.
    """

    if not item.score_breakdown_json:
        return None
    raw = json.loads(item.score_breakdown_json)
    required = {
        "commitment_preservation",
        "stability",
        "time_reliability",
        "preference_fit",
        "mobility_fit",
        "budget_fit",
        "robustness",
        "opportunity_value",
        "total",
    }
    if required.issubset(raw):
        return ScoreBreakdown(**raw)

    # Legacy provider-backed plans did not expose normalized dimensions.  Use
    # their utility score as the stable aggregate and retain the provider
    # facts as extension fields in the raw database JSON.
    aggregate = max(0.0, min(1.0, float(item.utility_score or raw.get("score", 0.8))))
    normalized = {
        "commitment_preservation": 1.0,
        "stability": aggregate,
        "time_reliability": aggregate,
        "preference_fit": aggregate,
        "mobility_fit": aggregate,
        "budget_fit": aggregate,
        "robustness": aggregate,
        "opportunity_value": aggregate,
        "total": aggregate,
    }
    return ScoreBreakdown(**normalized)


def _score(metrics: dict[str, float]) -> float:
    return round(sum(WEIGHTS[name] * max(0.0, min(1.0, metrics[name])) for name in WEIGHTS), 6)


def _templates() -> list[list[tuple[str, str, str, str]]]:
    return [
        [
            ("place-old-town", "Old Town Gate", "09:00", "10:15"),
            ("place-riverside-museum", "Riverside Museum", "10:30", "11:45"),
            ("place-food-hall", "Central Food Hall", "12:00", "13:00"),
            ("place-tech-art", "Tech Art Center", "13:20", "14:40"),
            ("place-river-cruise", "Nexus River Cruise Pier", "15:30", "16:30"),
            ("place-skyline-dinner", "Skyline Dinner House", "17:00", "18:30"),
        ],
        [
            ("place-old-town", "Old Town Gate", "09:00", "10:15"),
            ("place-riverside-museum", "Riverside Museum", "10:30", "11:45"),
            ("place-food-hall", "Central Food Hall", "12:00", "13:00"),
            ("place-city-park", "Nexus City Park", "13:20", "14:20"),
            ("place-river-cruise", "Nexus River Cruise Pier", "15:30", "16:30"),
            ("place-skyline-dinner", "Skyline Dinner House", "17:00", "18:30"),
        ],
        [
            ("place-old-town", "Old Town Gate", "09:00", "10:15"),
            ("place-riverside-museum", "Riverside Museum", "10:30", "11:45"),
            ("place-food-hall", "Central Food Hall", "12:00", "13:00"),
            ("place-design-library", "Design Library", "13:20", "14:20"),
            ("place-river-cruise", "Nexus River Cruise Pier", "15:30", "16:30"),
            ("place-skyline-dinner", "Skyline Dinner House", "17:00", "18:30"),
        ],
    ]


def _safe_estimate_minutes(provider, origin: str | None, destination: str | None) -> int:
    """Frozen-provider lookup that never raises for an unknown pair.

    A missing pair is a real planning fact (``MOBILITY_DATA_UNAVAILABLE`` in the
    gate), not a reason to abort the whole generation loop.
    """

    if not origin or not destination:
        return 0
    try:
        return int(provider.estimate_minutes(origin, destination))
    except (KeyError, TypeError, ValueError):
        return 0


def _anchor_block_reason(session: Session, journey: Journey) -> str:
    """Name the C4 anchor that blocked generation, when there is one.

    ``select`` already returns an accurate ``LOCKED_COMMITMENT_LOST:<key>``;
    ``generate`` must not collapse that into an anonymous sentence.
    """

    try:
        anchors, unresolved = resolve_plan_anchors(session, journey)
    except Exception:  # noqa: BLE001 - reason text must never break generation
        return ""
    if unresolved:
        return ": C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved)))
    if not anchors:
        return ""
    # Prefer the precise structural reason (overlap, arrival-after-departure,
    # outside journey) over a generic "blocked" list.
    try:
        effective_start, effective_end = effective_journey_window(journey, anchors)
        conflict = validate_anchor_timeline(
            anchors,
            parse_dt(effective_start),
            parse_dt(effective_end),
        )
    except Exception:  # noqa: BLE001
        conflict = None
    if conflict:
        return f": {conflict}"
    keys = ", ".join(sorted({anchor.semantic_key for anchor in anchors}))
    return f": C4_ANCHOR_BLOCKED:{keys}"


# How much of a day a traveller actually spends moving between and visiting
# stops.  Used to spread a multi-day trip across its days instead of packing
# everything into the arrival morning.
DAY_ACTIVITY_BUDGET_MIN = 330


def _generic_day_windows(
    journey_start: datetime, journey_end: datetime
) -> list[tuple[datetime, datetime]]:
    """Usable sightseeing windows, one per calendar day of the trip.

    Day 1 starts at arrival; the last day ends at departure.  Middle days are
    full days bounded by a normal sightseeing span so stops are not scheduled
    at 03:00.
    """

    windows: list[tuple[datetime, datetime]] = []
    day = journey_start.date()
    last_day = journey_end.date()
    while day <= last_day:
        day_start = datetime.combine(day, datetime.min.time(), journey_start.tzinfo)
        day_end = day_start + timedelta(hours=23)
        if day == journey_start.date():
            day_start = max(day_start, journey_start)
        if day == last_day:
            day_end = min(day_end, journey_end)
        if day_end > day_start:
            windows.append((day_start, day_end))
        day += timedelta(days=1)
    return windows or [(journey_start, journey_end)]


def _generic_compose_plans(
    session: Session,
    journey: Journey,
    planning_mode: str,
    place_ids: Sequence[str],
) -> list[PlanVersion]:
    """Compose a bounded plan from explicit POIs rather than city templates.

    The legacy fixture templates remain available for deterministic demo
    seeding.  This path is the product-facing seam: its candidate set comes
    from selected/discovered Place records, then the same deterministic gate
    validates opening hours, budget, windows, commitments, and route gaps
    before anything is persisted.
    """

    selected_ids = list(dict.fromkeys(str(item) for item in place_ids))
    places = {
        item.id: item
        for item in session.scalars(
            select(Place).where(Place.city_code == journey.city_code, Place.id.in_(selected_ids))
        ).all()
    }
    missing = [item for item in selected_ids if item not in places]
    if missing:
        raise ValueError(f"GENERIC_COMPOSE_PLACE_NOT_FOUND:{','.join(missing)}")
    if len(places) < 2:
        raise ValueError("GENERIC_COMPOSE_REQUIRES_TWO_PLACES")

    constraints = _journey_constraints_with_capabilities(session, journey, active_only=True)
    # A confirmed C4 anchor is a requirement to build around on this path too.
    anchors, unresolved_anchors = resolve_plan_anchors(session, journey)
    for anchor in anchors:
        places.setdefault(anchor.place_id, anchor.place)
    services = {
        service.id: service
        for service in session.scalars(
            select(CityService).where(CityService.city_code == journey.city_code)
        ).all()
    }
    lookup = {
        item.id: {"location": {"latitude": item.latitude, "longitude": item.longitude}}
        for item in places.values()
    }
    schedulable_ids = tuple(dict.fromkeys([*selected_ids, *(a.place_id for a in anchors)]))
    mobility_pairs = tuple(
        (origin, destination)
        for origin in schedulable_ids
        for destination in schedulable_ids
        if origin != destination
    )
    mobility_provider = capture_runtime_mobility_snapshot(
        session,
        journey,
        mobility_pairs,
        operation_key=f"generic-compose:{journey.id}",
    ).snapshot
    bounded_orders = tuple(permutations(selected_ids))
    ordered_ids = min(
        bounded_orders,
        key=lambda order: sum(
            mobility_provider.estimate_minutes(order[index - 1], order[index])
            for index in range(1, len(order))
        ),
    )
    journey_start = parse_dt(journey.start_at)
    journey_end = parse_dt(journey.end_at)
    # A multi-day trip must actually use its days.  Laying every stop out from
    # the arrival instant crammed an 8-stop Xiamen trip into one morning, which
    # then made every hotel's pinned check-in genuinely unreachable.
    day_windows = _generic_day_windows(journey_start, journey_end)
    day_index = 0
    cursor = day_windows[0][0]
    day_used_min = 0
    previous: str | None = None
    facts: list[FeasibilityActivity] = []
    rows: list[tuple[Place, datetime, datetime, int, int]] = []
    total_cost = 0

    for place_id in ordered_ids:
        place = places[place_id]
        metadata = json.loads(place.metadata_json or "{}")
        raw_cost = metadata.get("cost_minor")
        if raw_cost is None:
            raise ValueError(f"GENERIC_COMPOSE_UNKNOWN_COST:{place_id}")
        cost_minor = int(raw_cost)
        duration_min = max(15, int(metadata.get("duration_min", 60)))
        travel_min = (
            mobility_provider.estimate_minutes(previous, place_id) if previous else 0
        )
        start_at = cursor + timedelta(minutes=travel_min)
        opening = json.loads(place.opening_hours_json or "{}")
        if isinstance(opening, dict) and opening.get("open"):
            hour, minute = (int(part) for part in str(opening["open"]).split(":", 1))
            open_at = datetime.combine(
                start_at.date(), datetime.min.time().replace(hour=hour, minute=minute), start_at.tzinfo
            )
            start_at = max(start_at, open_at)
        end_at = start_at + timedelta(minutes=duration_min)
        # Roll over to the next day when this one is full (a real sightseeing
        # day, not a 23-hour window) or when the stop would overflow it.  A
        # multi-day trip must not cram every stop into its first morning.
        while day_index < len(day_windows) - 1 and (
            end_at > day_windows[day_index][1]
            or day_used_min + duration_min + travel_min > DAY_ACTIVITY_BUDGET_MIN
        ):
            day_index += 1
            next_start, _next_end = day_windows[day_index]
            start_at = next_start
            end_at = start_at + timedelta(minutes=duration_min)
            cursor = next_start
            day_used_min = 0
            travel_min = 0
        if end_at > journey_end:
            raise ValueError(f"GENERIC_COMPOSE_JOURNEY_WINDOW_EXCEEDED:{place_id}")
        facts.append(
            FeasibilityActivity(
                key=place_id,
                place_id=place_id,
                start_at=start_at,
                end_at=end_at,
                cost_minor=cost_minor,
                currency=journey.budget_currency,
                travel_from_prev_min=travel_min,
                locked=False,
            )
        )
        rows.append((place, start_at, end_at, travel_min, cost_minor))
        total_cost += cost_minor
        cursor = end_at
        day_used_min += duration_min + travel_min
        previous = place_id

    # Pin every resolved anchor into the candidate schedule before the gate.
    anchored = _inject_anchors_into_generic(
        journey=journey,
        selected_ids=ordered_ids,
        places=places,
        anchors=anchors,
        facts=facts,
        rows=rows,
    )
    if anchored is None:
        if unresolved_anchors:
            raise ValueError(
                "C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved_anchors)))
            )
        raise ValueError("GENERIC_COMPOSE_INFEASIBLE:C4_ANCHOR_UNSATISFIABLE")
    facts, rows = anchored
    total_cost = sum(int(row[4]) for row in rows)
    gate = evaluate_feasibility(
        build_context(
            journey,
            constraints,
            places,
            services,
            mobility_provider=mobility_provider,
        ),
        facts,
    )
    if not gate.passed:
        raise ValueError(f"GENERIC_COMPOSE_INFEASIBLE:{'|'.join(gate.failures)}")

    existing_max = (
        session.scalar(
            select(PlanVersion.version_no)
            .where(PlanVersion.journey_id == journey.id)
            .order_by(PlanVersion.version_no.desc())
            .limit(1)
        )
        or 0
    )
    version_no = existing_max + 1
    plan_id = deterministic_id(
        f"plan:{journey.id}:{version_no}:generic:{','.join(ordered_ids)}"
    )
    budget_fit = max(0.0, min(1.0, 1 - total_cost / max(1, journey.budget_amount_minor)))
    metrics = {
        "commitment_preservation": 1.0,
        "stability": 0.9,
        "time_reliability": 0.9,
        "preference_fit": 0.8,
        "mobility_fit": 0.85,
        "budget_fit": budget_fit,
        "robustness": 0.85,
        "opportunity_value": 0.8,
    }
    breakdown = {**metrics, "total": _score(metrics)}
    now = iso_now()
    plan = PlanVersion(
        id=plan_id,
        journey_id=journey.id,
        version_no=version_no,
        planning_mode=planning_mode,
        status="CANDIDATE",
        source="INITIAL",
        parent_plan_version_id=None,
        total_cost_minor=total_cost,
        currency=journey.budget_currency,
        estimated_duration_min=sum(
            int((end_at - start_at).total_seconds() // 60) + travel_min
            for _place, start_at, end_at, travel_min, _cost in rows
        ),
        utility_score=breakdown["total"],
        score_breakdown_json=dump(breakdown),
        explanation_json=dump(
            {
                "reason": "Generic Compose Engine from explicit POIs",
                "input_place_ids": selected_ids,
                "compose_order": list(ordered_ids),
                "deterministic_gate": "PASSED",
                "mobility_provider": mobility_provider.source_provider_key,
                "mobility_snapshot_id": mobility_provider.snapshot_id,
                "mobility_provenance": [
                    {
                        "from": fact.origin_key,
                        "to": fact.destination_key,
                        "provider": fact.provider_key,
                        "degraded": fact.degraded,
                    }
                    for fact in mobility_provider.facts.values()
                ],
            }
        ),
        mobility_snapshot_id=mobility_provider.snapshot_id,
        mobility_evidence_json=dump(mobility_provider.to_evidence()),
        created_at=now,
    )
    session.add(plan)
    session.flush()
    for sequence, (place, start_at, end_at, travel_min, cost_minor) in enumerate(rows, start=1):
        session.add(
            Activity(
                id=deterministic_id(f"activity:{plan_id}:{sequence}"),
                plan_version_id=plan.id,
                sequence_no=sequence,
                activity_type="visit",
                title=place.name,
                place_id=place.id,
                city_service_id=None,
                start_at=start_at.isoformat(),
                end_at=end_at.isoformat(),
                travel_from_prev_min=travel_min,
                estimated_cost_minor=cost_minor,
                currency=journey.budget_currency,
                status="PLANNED",
                locked=False,
                metadata_json=dump(
                    {
                        "compose_source": "EXPLICIT_POI_SET",
                        "semantic_key": (
                            f"v12:{journey.id}:{place.category.upper()}-anchor"
                            if place.category.upper() in {"ARRIVAL", "DEPARTURE"}
                            else place.id
                        ),
                        "category": place.category,
                        "opening_hours": json.loads(place.opening_hours_json or "{}"),
                        # The map resolves pins from activity metadata; without
                        # them a real Xiamen plan renders no Xiamen coordinates.
                        "latitude": place.latitude,
                        "longitude": place.longitude,
                        "crs": "WGS84",
                    }
                ),
                created_at=now,
                updated_at=now,
            )
        )
    record_audit(
        session,
        action="plans.generated.generic_compose",
        entity_type="PlanVersion",
        entity_id=plan.id,
        journey_id=journey.id,
        after={"place_ids": selected_ids, "gate": "PASSED"},
    )
    session.commit()
    return [plan]




def _generic_compose_variants(
    session: Session,
    journey: Journey,
    planning_mode: str,
    place_ids: Sequence[str],
    candidate_count: int,
) -> list[PlanVersion]:
    """Compose genuinely different candidates from the same discovered POIs.

    Real provider discovery returns POIs without a "tour style", so inventing
    marketing names like 轻松版/经典版/深度版 would be fabrication.  What *is*
    real is how much fits in the trip: we therefore build candidates of
    decreasing scope (full set, then progressively fewer stops).  They differ in
    stop count, total cost and walking burden, which is exactly what the
    comparison card is supposed to show.
    """

    ordered = list(dict.fromkeys(str(item) for item in place_ids))
    if len(ordered) < 2:
        raise ValueError("GENERIC_COMPOSE_REQUIRES_TWO_PLACES")

    # Distinct scopes, longest first, never below two stops.
    scopes: list[list[str]] = []
    for drop in range(min(3, len(ordered) - 1)):
        scope = ordered[: len(ordered) - drop]
        if len(scope) >= 2 and scope not in scopes:
            scopes.append(scope)
    scopes = scopes[: max(1, candidate_count)]

    created: list[PlanVersion] = []
    failures: list[str] = []
    for scope in scopes:
        try:
            created.extend(
                _generic_compose_plans(session, journey, planning_mode, scope)
            )
        except ValueError as exc:
            failures.append(str(exc))
    if not created:
        raise ValueError(
            "GENERIC_COMPOSE_INFEASIBLE:" + "|".join(failures[:3] or ["NO_VARIANT"])
        )
    return created

def _inject_anchors_into_generic(
    *,
    journey: Journey,
    selected_ids: Sequence[str],
    places: Mapping[str, Any],
    anchors: Sequence[Any],
    facts: list[FeasibilityActivity],
    rows: list[Any],
) -> tuple[list[FeasibilityActivity], list[Any]] | None:
    """Insert resolved C4 anchors into an explicit-POI schedule.

    The optional POIs keep their relative order; anchors are pinned to their
    required time.  Returns ``None`` when an anchor cannot be satisfied.
    """

    if not anchors:
        return facts, rows
    # Rebuild the schedule from the (place, start, end, travel, cost) rows and
    # re-interleave the anchors, preserving the original POI ordering.
    scheduled: list[tuple[str, Any, Any, Any, int, str | None]] = []
    by_place = {place_id: row for row, place_id in zip(facts, selected_ids)}
    for place_id in selected_ids:
        fact = by_place.get(place_id)
        if fact is None:
            continue
        place = places.get(place_id)
        if place is None:
            return None
        scheduled.append(
            (place_id, fact.start_at, fact.end_at, fact.cost_minor, place.id, None)
        )
    anchor_rows = []
    for anchor in anchors:
        duration = (
            ANCHOR_DURATION_MIN
            if anchor.role != MID_TRIP_ROLE
            else max(ANCHOR_DURATION_MIN, 60)
        )
        if anchor.time_boundary == "END":
            start_at = anchor.scheduled_at - timedelta(minutes=duration)
            end_at = anchor.scheduled_at
        else:
            start_at = anchor.scheduled_at
            end_at = anchor.scheduled_at + timedelta(minutes=duration)
        anchor_rows.append(
            (
                anchor.place_id,
                start_at,
                end_at,
                0,
                anchor.place_id,
                anchor.semantic_key,
                anchor.role,
            )
        )
    combined = [
        (
            item[0],
            item[1],
            item[2],
            item[3],
            item[4],
            item[5],
            None,
        )
        for item in scheduled
    ] + anchor_rows
    combined.sort(key=lambda item: (item[1], 0 if item[6] else 1, item[0]))
    new_facts: list[FeasibilityActivity] = []
    new_rows: list[Any] = []
    for place_id, start_at, end_at, cost_minor, db_place_id, semantic, role in combined:
        place = places.get(db_place_id) or places.get(place_id)
        if place is None:
            return None
        new_facts.append(
            FeasibilityActivity(
                key=place_id,
                place_id=db_place_id,
                start_at=start_at,
                end_at=end_at,
                cost_minor=int(cost_minor),
                currency=journey.budget_currency,
                travel_from_prev_min=0,
                locked=bool(role),
                metadata=(
                    {"semantic_key": semantic, "anchor_role": role, "commitment_anchor": True}
                    if role
                    else {"semantic_key": semantic or db_place_id}
                ),
            )
        )
        new_rows.append((place, start_at, end_at, 0, int(cost_minor)))
    return new_facts, new_rows


def validate_plan_feasibility(
    session: Session,
    journey: Journey,
    plan: PlanVersion,
    *,
    journey_overrides: Mapping[str, Any] | None = None,
    additional_constraints: Sequence[Any] = (),
    include_active_c4: bool = True,
    mobility_provider: Any | None = None,
) -> FeasibilityResult:
    """Evaluate any persisted plan against the current authoritative Journey facts."""

    if plan.journey_id != journey.id:
        raise ValueError("PlanVersion does not belong to Journey")
    overrides = dict(journey_overrides or {})
    # The effective journey window is widened inside ``evaluate_feasibility``
    # from the active C4 constraints themselves, so generation and every
    # revalidation (select / booking / start) automatically agree.
    proposed_journey = {
        "id": journey.id,
        "city_code": overrides.get("city_code", journey.city_code),
        "start_at": overrides.get("start_at", journey.start_at),
        "end_at": overrides.get("end_at", journey.end_at),
        "budget_amount_minor": overrides.get("budget_amount_minor", journey.budget_amount_minor),
        "budget_currency": overrides.get("budget_currency", journey.budget_currency),
    }
    constraints: list[Any] = _journey_constraints_with_capabilities(
        session, journey, include_c4=include_active_c4
    )
    constraints.extend(additional_constraints)
    places = {
        item.id: item
        for item in session.scalars(
            select(Place).where(Place.city_code == proposed_journey["city_code"])
        ).all()
    }
    services = {
        item.id: item
        for item in session.scalars(
            select(CityService).where(CityService.city_code == proposed_journey["city_code"])
        ).all()
    }
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan.id).order_by(Activity.sequence_no)
    ).all()
    return evaluate_feasibility(
        build_context(
            proposed_journey,
            constraints,
            places,
            services,
            mobility_provider=mobility_provider or _snapshot_for_plan(session, journey, plan),
            plan_currency=plan.currency,
        ),
        [activity_from_record(item) for item in activities],
    )


def _snapshot_for_plan(session: Session, journey: Journey, plan: PlanVersion):
    """Load the PlanVersion's frozen mobility evidence; never recapture here."""
    raw = json.loads(plan.mobility_evidence_json or "{}")
    snapshot_id = raw.get("snapshot_id")
    if not snapshot_id or snapshot_id != plan.mobility_snapshot_id:
        raise ValueError("STALE_RECOMPOSE_REQUIRED: PlanVersion frozen mobility evidence is missing or inconsistent")
    expires_at = raw.get("expires_at")
    if expires_at and parse_dt(str(expires_at)) <= datetime.now(timezone.utc):
        raise ValueError("STALE_RECOMPOSE_REQUIRED: PlanVersion frozen mobility evidence expired")
    return MobilitySnapshot.from_evidence(raw)


def validate_selected_plan_feasibility(
    session: Session,
    journey: Journey,
    *,
    journey_overrides: Mapping[str, Any] | None = None,
    additional_constraints: Sequence[Any] = (),
    mobility_provider: Any | None = None,
) -> FeasibilityResult | None:
    """Re-evaluate the current selected/active plan against a proposed mutation snapshot."""

    if journey.status not in {"PLANNED", "ACTIVE"} or not journey.active_plan_version_id:
        return None

    selected = session.get(PlanVersion, journey.active_plan_version_id)
    expected_plan_status = "SELECTED" if journey.status == "PLANNED" else "ACTIVE"
    if (
        selected is None
        or selected.journey_id != journey.id
        or selected.status != expected_plan_status
    ):
        raise ValueError("Journey active plan state is invalid")
    return validate_plan_feasibility(
        session,
        journey,
        selected,
        journey_overrides=journey_overrides,
        additional_constraints=additional_constraints,
        include_active_c4=True,
        mobility_provider=mobility_provider,
    )


def generate_plans(
    session: Session,
    journey: Journey,
    planning_mode: str,
    candidate_count: int,
    *,
    place_ids: Sequence[str] | None = None,
) -> list[PlanVersion]:
    if place_ids:
        return _generic_compose_variants(
            session, journey, planning_mode, place_ids, candidate_count
        )
    existing_max = (
        session.scalar(
            select(PlanVersion.version_no)
            .where(PlanVersion.journey_id == journey.id)
            .order_by(PlanVersion.version_no.desc())
            .limit(1)
        )
        or 0
    )
    places = {
        p.id: p
        for p in session.scalars(select(Place).where(Place.city_code == journey.city_code)).all()
    }
    services = {
        service.id: service
        for service in session.scalars(
            select(CityService).where(CityService.city_code == journey.city_code)
        ).all()
    }
    constraints = _journey_constraints_with_capabilities(session, journey)
    raw_templates = _templates()
    created: list[PlanVersion] = []
    now = iso_now()
    journey_start = parse_dt(journey.start_at)
    journey_end = parse_dt(journey.end_at)
    # A confirmed C4 anchor is a requirement to *build around*, not only a veto.
    # Resolve every active anchor to a concrete, routable Place identity and pin
    # it into the candidate schedule before the gate runs.
    anchors, unresolved_anchors = resolve_plan_anchors(session, journey)
    for anchor in anchors:
        places.setdefault(anchor.place_id, anchor.place)
    # A confirmed reservation is an authoritative real-world fact: the draft
    # journey window expands to contain it rather than making it unplannable.
    effective_start_text, effective_end_text = effective_journey_window(
        journey, anchors
    )
    journey_start = parse_dt(effective_start_text)
    journey_end = parse_dt(effective_end_text)
    metrics_list = [
        {
            "commitment_preservation": 0.98,
            "stability": 0.95,
            "time_reliability": 0.94,
            "preference_fit": 0.92,
            "mobility_fit": 0.88,
            "budget_fit": 0.90,
            "robustness": 0.90,
            "opportunity_value": 0.82,
        },
        {
            "commitment_preservation": 0.98,
            "stability": 0.93,
            "time_reliability": 0.96,
            "preference_fit": 0.90,
            "mobility_fit": 0.93,
            "budget_fit": 0.96,
            "robustness": 0.92,
            "opportunity_value": 0.78,
        },
        {
            "commitment_preservation": 0.98,
            "stability": 0.92,
            "time_reliability": 0.95,
            "preference_fit": 0.91,
            "mobility_fit": 0.91,
            "budget_fit": 0.95,
            "robustness": 0.91,
            "opportunity_value": 0.80,
        },
    ]
    # Capture one frozen mobility matrix over every node a candidate can visit
    # (template POIs plus resolved anchors) *before* scheduling, so the
    # scheduler inserts real travel gaps and the gate consumes the exact same
    # frozen evidence.
    schedulable_ids = tuple(
        dict.fromkeys(
            [
                *(
                    place_id
                    for template in raw_templates
                    for place_id, *_ in template
                    if place_id in places
                ),
                *(anchor.place_id for anchor in anchors),
            ]
        )
    )
    mobility_provider = capture_runtime_mobility_snapshot(
        session,
        journey,
        tuple(
            (origin, destination)
            for origin in schedulable_ids
            for destination in schedulable_ids
            if origin != destination
        ),
        operation_key=f"template-compose:{journey.id}",
    ).snapshot
    travel_minutes = {
        (origin, destination): fact.minutes
        for (origin, destination), fact in mobility_provider.facts.items()
    }
    schedules: list[list[CandidateActivity]] = []
    for template in raw_templates:
        schedule = schedule_template_with_anchors(
            journey=journey,
            template=template,
            places=places,
            anchors=anchors,
            journey_start=journey_start,
            journey_end=journey_end,
            travel_minutes=travel_minutes,
        )
        if schedule is not None:
            schedules.append(schedule)
    for offset, schedule in enumerate(schedules):
        if len(created) >= candidate_count:
            break
        total_cost = sum(int(item.cost_minor) for item in schedule)
        if total_cost > journey.budget_amount_minor:
            continue
        metrics = metrics_list[offset % len(metrics_list)]
        activity_facts: list[FeasibilityActivity] = []
        previous_place: str | None = None
        for item in schedule:
            travel = (
                _safe_estimate_minutes(mobility_provider, previous_place, item.place_id)
                if previous_place
                else 0
            )
            activity_facts.append(
                FeasibilityActivity(
                    key=item.place_id,
                    place_id=item.place_id,
                    start_at=item.start_at,
                    end_at=item.end_at,
                    cost_minor=item.cost_minor,
                    currency=journey.budget_currency,
                    travel_from_prev_min=travel,
                    locked=item.locked,
                    metadata=dict(item.metadata),
                )
            )
            previous_place = item.place_id
        # This is the sole authoritative gate.  It runs before score
        # calculation and before a PlanVersion or Activity is persisted.
        gate = evaluate_feasibility(
            build_context(
                journey,
                constraints,
                places,
                services,
                mobility_provider=mobility_provider,
            ),
            activity_facts,
        )
        if not gate.passed:
            continue
        # Version numbers remain contiguous among accepted candidates even
        # when an earlier raw template is rejected by a hard constraint.
        version_no = existing_max + len(created) + 1
        plan_id = deterministic_id(f"plan:{journey.id}:{version_no}")
        total = _score(metrics)
        breakdown = {**metrics, "total": total}
        plan = PlanVersion(
            id=plan_id,
            journey_id=journey.id,
            version_no=version_no,
            planning_mode=planning_mode,
            status="CANDIDATE",
            source="INITIAL",
            parent_plan_version_id=None,
            total_cost_minor=total_cost,
            currency=journey.budget_currency,
            estimated_duration_min=570,
            utility_score=total,
            score_breakdown_json=dump(breakdown),
            explanation_json=dump({"reason": "Deterministic provider-backed candidate", "mobility_snapshot_id": mobility_provider.snapshot_id}),
            mobility_snapshot_id=mobility_provider.snapshot_id,
            mobility_evidence_json=dump(mobility_provider.to_evidence()),
            created_at=now,
        )
        session.add(plan)
        session.flush()
        for sequence, item in enumerate(schedule, start=1):
            aid = deterministic_id(f"activity:{plan_id}:{sequence}")
            travel = activity_facts[sequence - 1].travel_from_prev_min
            session.add(
                Activity(
                    id=aid,
                    plan_version_id=plan_id,
                    sequence_no=sequence,
                    activity_type=(
                        "arrival"
                        if item.anchor_role == "ARRIVAL"
                        else "departure"
                        if item.anchor_role == "DEPARTURE"
                        else "visit"
                    ),
                    title=item.title,
                    place_id=item.place_id,
                    city_service_id=None,
                    start_at=item.start_at.isoformat(),
                    end_at=item.end_at.isoformat(),
                    travel_from_prev_min=travel,
                    estimated_cost_minor=item.cost_minor,
                    currency=journey.budget_currency,
                    status="PLANNED",
                    locked=item.locked,
                    metadata_json=dump(dict(item.metadata)),
                    created_at=now,
                    updated_at=now,
                )
            )
        created.append(plan)
    if not created:
        if unresolved_anchors:
            raise ValueError(
                "C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved_anchors)))
            )
        detail = _anchor_block_reason(session, journey)
        raise ValueError(
            "No feasible plan candidates satisfy the journey constraints" + detail
        )
    record_audit(
        session,
        action="plans.generated",
        entity_type="PlanVersion",
        entity_id=journey.id,
        journey_id=journey.id,
        after={"count": len(created), "plan_ids": [plan.id for plan in created]},
    )
    session.commit()
    return created
