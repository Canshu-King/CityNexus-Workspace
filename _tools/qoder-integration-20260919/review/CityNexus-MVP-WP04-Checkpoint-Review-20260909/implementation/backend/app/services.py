from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.db.models import (
    Activity,
    CityService,
    Journey,
    JourneyConstraint,
    Place,
    PlanVersion,
    Preference,
    Traveler,
)
from app.integrations.mock.providers import MockCityDataProvider, MockMobilityProvider
from app.replanning.feasibility import (
    FeasibilityActivity,
    FeasibilityResult,
    activity_from_record,
    build_context,
    evaluate_feasibility,
)
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


def load(name: str) -> Any:
    return json.loads((MOCK_ROOT / name).read_text(encoding="utf-8"))


def deterministic_id(label: str) -> str:
    return str(uuid5(DEMO_NAMESPACE, label))


def reset_all(session: Session) -> None:
    # Delete children first because the package schema intentionally enables FKs.
    for table in (
        "audit_logs",
        "provider_calls",
        "idempotency_keys",
        "replan_proposals",
        "recommendations",
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
        "travelers",
    ):
        session.execute(
            delete(
                __import__("sqlalchemy").Table(
                    table, __import__("sqlalchemy").MetaData(), autoload_with=session.bind
                )
            )
        )
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
    return {"traveler_id": traveler.id, "journey_id": journey.id}


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


def activity_schema(item: Activity) -> ActivitySchema:
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
        status=item.status,
        locked=bool(item.locked),
    )


def plan_schema(session: Session, item: PlanVersion) -> PlanSchema:
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == item.id).order_by(Activity.sequence_no)
    ).all()
    breakdown = (
        ScoreBreakdown(**json.loads(item.score_breakdown_json))
        if item.score_breakdown_json
        else None
    )
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
        activities=[activity_schema(a) for a in activities],
    )


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


def validate_selected_plan_feasibility(
    session: Session,
    journey: Journey,
    *,
    journey_overrides: Mapping[str, Any] | None = None,
    additional_constraints: Sequence[Any] = (),
) -> FeasibilityResult | None:
    """Re-evaluate a selected plan against a proposed mutation snapshot.

    This is the single mutation guard used by Journey PATCH and HARD
    constraint creation.  It deliberately builds a read-only snapshot rather
    than mutating ORM state, so a rejected request cannot leak partial changes
    through the current transaction.
    """

    if journey.status != "PLANNED" or not journey.active_plan_version_id:
        return None

    selected = session.get(PlanVersion, journey.active_plan_version_id)
    if selected is None or selected.journey_id != journey.id or selected.status != "SELECTED":
        raise ValueError("Journey selected plan state is invalid")

    overrides = dict(journey_overrides or {})
    proposed_journey = {
        "id": journey.id,
        "city_code": overrides.get("city_code", journey.city_code),
        "start_at": overrides.get("start_at", journey.start_at),
        "end_at": overrides.get("end_at", journey.end_at),
        "budget_amount_minor": overrides.get("budget_amount_minor", journey.budget_amount_minor),
        "budget_currency": overrides.get("budget_currency", journey.budget_currency),
    }
    constraints = list(
        session.scalars(
            select(JourneyConstraint).where(JourneyConstraint.journey_id == journey.id)
        ).all()
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
        select(Activity)
        .where(Activity.plan_version_id == selected.id)
        .order_by(Activity.sequence_no)
    ).all()
    return evaluate_feasibility(
        build_context(
            proposed_journey,
            constraints,
            places,
            services,
            mobility_provider=MockMobilityProvider(),
            plan_currency=selected.currency,
        ),
        [activity_from_record(item) for item in activities],
    )


def generate_plans(
    session: Session, journey: Journey, planning_mode: str, candidate_count: int
) -> list[PlanVersion]:
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
    constraints = session.scalars(
        select(JourneyConstraint).where(JourneyConstraint.journey_id == journey.id)
    ).all()
    raw_templates = _templates()
    created: list[PlanVersion] = []
    now = iso_now()
    journey_start = parse_dt(journey.start_at)
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
    mobility_provider = MockMobilityProvider()
    for offset, template in enumerate(raw_templates):
        if len(created) >= candidate_count:
            break
        if any(place_id not in places for place_id, *_ in template):
            continue
        total_cost = sum(
            int(json.loads(places[p].metadata_json)["cost_minor"]) for p, *_ in template
        )
        if total_cost > journey.budget_amount_minor:
            continue
        metrics = metrics_list[offset % len(metrics_list)]
        activity_facts: list[FeasibilityActivity] = []
        previous_place: str | None = None
        for place_id, _, start, end in template:
            travel = (
                mobility_provider.estimate_minutes(previous_place, place_id)
                if previous_place
                else 0
            )
            activity_facts.append(
                FeasibilityActivity(
                    key=place_id,
                    place_id=place_id,
                    start_at=parse_dt(
                        f"{journey_start.date().isoformat()}T{start}:00{journey_start.strftime('%z')}"
                    ),
                    end_at=parse_dt(
                        f"{journey_start.date().isoformat()}T{end}:00{journey_start.strftime('%z')}"
                    ),
                    cost_minor=int(json.loads(places[place_id].metadata_json)["cost_minor"]),
                    currency=journey.budget_currency,
                    travel_from_prev_min=travel,
                    locked=(place_id == "place-river-cruise"),
                )
            )
            previous_place = place_id
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
            explanation_json=dump({"reason": "Deterministic mock city candidate"}),
            created_at=now,
        )
        session.add(plan)
        session.flush()
        for sequence, (place_id, title, start, end) in enumerate(template, start=1):
            aid = deterministic_id(f"activity:{plan_id}:{sequence}")
            travel = activity_facts[sequence - 1].travel_from_prev_min
            start_text = (
                f"{journey_start.date().isoformat()}T{start}:00{journey_start.strftime('%z')}"
            )
            end_text = f"{journey_start.date().isoformat()}T{end}:00{journey_start.strftime('%z')}"
            session.add(
                Activity(
                    id=aid,
                    plan_version_id=plan_id,
                    sequence_no=sequence,
                    activity_type="visit",
                    title=title,
                    place_id=place_id,
                    city_service_id=None,
                    start_at=start_text,
                    end_at=end_text,
                    travel_from_prev_min=travel,
                    estimated_cost_minor=int(
                        json.loads(places[place_id].metadata_json)["cost_minor"]
                    ),
                    currency=journey.budget_currency,
                    status="PLANNED",
                    locked=(place_id == "place-river-cruise"),
                    metadata_json=dump({}),
                    created_at=now,
                    updated_at=now,
                )
            )
        created.append(plan)
    if not created:
        raise ValueError("No feasible plan candidates satisfy the journey constraints")
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
