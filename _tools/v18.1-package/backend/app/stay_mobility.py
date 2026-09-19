"""Generic stay-aware, mode-per-leg planning backed by normalized provider evidence."""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.money import major_to_minor
from app.core.temporal import derive_journey_temporal_shape
from app.db.models import (
    AccommodationOfferSnapshot,
    Activity,
    Commitment,
    Event,
    Journey,
    JourneyLeg,
    JourneyOperationsContext,
    JourneyTripContext,
    LocationObservation,
    MobilityFact,
    PlanVersion,
    StayJourneyOption,
)
from app.execution.traveler_twin import planning_preference_items
from app.planning.stay_mode_solver import solve_mode_choices

MODES = ("WALK", "BICYCLE", "TRANSIT", "AUTO", "RIDE_HAIL")
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "v9" / "city_operations.json"
CAPTURED_FIXTURE_CURRENCY = "CNY"
SYNTHETIC_ESTIMATE_MAJOR_BY_CURRENCY = {
    "CNY": {"BICYCLE": 6, "TRANSIT": 4, "AUTO": 12},
}


@dataclass(frozen=True)
class AccommodationOfferDraft:
    external_offer_id: str
    property_name: str
    latitude: float
    longitude: float
    nightly_amount_minor: int
    room_type: str
    refundable: bool
    evidence_confidence: float
    coordinate_crs: str
    luggage_drop: dict[str, Any]


@dataclass(frozen=True)
class GraphNode:
    key: str
    title: str
    role: str
    start_at: str
    end_at: str
    latitude: float
    longitude: float
    place_key: str | None = None
    locked: bool = False
    estimated_cost_minor: int = 0
    cost_status: str = "FREE_KNOWN"


class AccommodationProvider(Protocol):
    provider_key: str
    provenance: str

    def discover(
        self, *, city_code: str, party_size: int, nights: int
    ) -> tuple[AccommodationOfferDraft, ...]: ...


class CapturedAccommodationProvider:
    provider_key = "citynexus-city-fixture"
    provenance = "CAPTURED_REPLAY"

    def discover(
        self, *, city_code: str, party_size: int, nights: int
    ) -> tuple[AccommodationOfferDraft, ...]:
        city = city_fixture(city_code)
        return tuple(
            AccommodationOfferDraft(
                external_offer_id=str(item["external_offer_id"]),
                property_name=str(item["property_name"]),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                nightly_amount_minor=int(item["nightly_amount_minor"]),
                room_type=str(item["room_type"]),
                refundable=bool(item["refundable"]),
                evidence_confidence=0.96,
                coordinate_crs=str(city.get("center", {}).get("crs", "WGS84")),
                luggage_drop=dict(item.get("luggage_drop", {})),
            )
            for item in city.get("stays", [])
        )


class LiveAccommodationProvider:
    provider_key = "live-accommodation"
    provenance = "UNAVAILABLE"

    def discover(
        self, *, city_code: str, party_size: int, nights: int
    ) -> tuple[AccommodationOfferDraft, ...]:
        return ()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(raw: str | None, fallback: Any) -> Any:
    try:
        return json.loads(raw or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def city_fixture(city_code: str) -> dict[str, Any]:
    fixtures = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    value = fixtures.get(str(city_code).upper())
    return dict(value) if isinstance(value, dict) else {}


def _context(session: Session, journey: Journey) -> JourneyTripContext:
    row = session.get(JourneyTripContext, journey.id)
    if row is None:
        now = _now()
        row = JourneyTripContext(
            journey_id=journey.id,
            arrival_anchor_json=_json({"at": journey.start_at, "location": "Arrival"}),
            departure_anchor_json=_json({"at": journey.end_at, "location": "Departure"}),
            party_size=1,
            occupancy_json=_json({"adults": 1}),
            stay_budget_amount_minor=0,
            stay_budget_currency=journey.budget_currency,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
    return row


def _operations_context(session: Session, journey: Journey) -> JourneyOperationsContext:
    row = session.get(JourneyOperationsContext, journey.id)
    if row is None:
        now = _now()
        row = JourneyOperationsContext(
            journey_id=journey.id,
            baggage_present=False,
            baggage_size_class="NONE",
            luggage_drop_required=False,
            constraints_json="{}",
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
    return row


def _anchor(context: JourneyTripContext, journey: Journey, kind: str) -> dict[str, Any]:
    raw = context.arrival_anchor_json if kind == "arrival" else context.departure_anchor_json
    fallback_at = journey.start_at if kind == "arrival" else journey.end_at
    value = _load(raw, {})
    return {
        "at": str(value.get("at") or fallback_at),
        "location": str(value.get("location") or kind.title()),
        "latitude": value.get("latitude"),
        "longitude": value.get("longitude"),
        "reservation_id": value.get("reservation_id"),
    }


def _nights(context: JourneyTripContext, journey: Journey) -> int:
    start = datetime.fromisoformat(_anchor(context, journey, "arrival")["at"])
    end = datetime.fromisoformat(_anchor(context, journey, "departure")["at"])
    return derive_journey_temporal_shape(start, end).night_count


def _at_on_day(anchor_at: datetime, day_offset: int, hhmm: str) -> datetime:
    hour, minute = (int(part) for part in hhmm.split(":"))
    local_date = anchor_at.date() + timedelta(days=day_offset)
    return datetime.combine(local_date, time(hour, minute), tzinfo=anchor_at.tzinfo)


def capture_accommodation_offers(
    session: Session, journey: Journey
) -> list[AccommodationOfferSnapshot]:
    context = _context(session, journey)
    arrival = datetime.fromisoformat(_anchor(context, journey, "arrival")["at"])
    departure = datetime.fromisoformat(_anchor(context, journey, "departure")["at"])
    nights = _nights(context, journey)
    if nights == 0:
        return []
    captured = _now()
    expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    provider: AccommodationProvider = CapturedAccommodationProvider()
    result: list[AccommodationOfferSnapshot] = []
    for draft in provider.discover(
        city_code=journey.city_code, party_size=context.party_size, nights=nights
    ):
        existing = session.scalar(
            select(AccommodationOfferSnapshot).where(
                AccommodationOfferSnapshot.journey_id == journey.id,
                AccommodationOfferSnapshot.provider_key == provider.provider_key,
                AccommodationOfferSnapshot.external_offer_id == draft.external_offer_id,
            )
        )
        total = draft.nightly_amount_minor * nights
        check_in = _at_on_day(arrival, 0, "14:00")
        check_out = _at_on_day(arrival, nights, "12:00")
        if check_out > departure:
            check_out = departure - timedelta(hours=2)
        if existing is None:
            existing = AccommodationOfferSnapshot(
                id=str(uuid4()),
                journey_id=journey.id,
                provider_key=provider.provider_key,
                external_offer_id=draft.external_offer_id,
                property_name=draft.property_name,
                latitude=draft.latitude,
                longitude=draft.longitude,
                coordinate_crs=draft.coordinate_crs,
                room_type=draft.room_type,
                occupancy_json=_json(
                    {"party_size": context.party_size, **_load(context.occupancy_json, {})}
                ),
                check_in_at=check_in.isoformat(),
                check_out_at=check_out.isoformat(),
                nightly_amount_minor=draft.nightly_amount_minor,
                taxes_amount_minor=0,
                total_amount_minor=total,
                # The current accommodation fixture is intentionally CNY-only;
                # a future non-CNY fixture must supply its own captured currency.
                currency=CAPTURED_FIXTURE_CURRENCY,
                cancellation_policy_json=_json(
                    {
                        "refundable": draft.refundable,
                        "deadline": arrival.isoformat(),
                        "summary": "Free cancellation before arrival"
                        if draft.refundable
                        else "Non-refundable captured rate",
                    }
                ),
                luggage_drop_json=_json(draft.luggage_drop),
                refundable=draft.refundable,
                evidence_json=_json(
                    {
                        "source": provider.provenance,
                        "provider": provider.provider_key,
                        "confidence": draft.evidence_confidence,
                        "price_basis": "per_night × nights",
                        "currency_explicit": True,
                        "city_fixture": journey.city_code,
                    }
                ),
                captured_at=captured,
                expires_at=expires,
                status="CAPTURED",
            )
            session.add(existing)
        result.append(existing)
    session.flush()
    return result


def build_candidate_nodes(
    session: Session, journey: Journey, offer: AccommodationOfferSnapshot
) -> list[GraphNode]:
    context = _context(session, journey)
    operations = _operations_context(session, journey)
    city = city_fixture(journey.city_code)
    center = city.get("center", {})
    arrival = _anchor(context, journey, "arrival")
    departure = _anchor(context, journey, "departure")
    arrival_at = datetime.fromisoformat(arrival["at"])
    departure_at = datetime.fromisoformat(departure["at"])
    center_lat = float(center.get("latitude", offer.latitude))
    center_lon = float(center.get("longitude", offer.longitude))
    arrival_lat = float(arrival.get("latitude") or center_lat - 0.018)
    arrival_lon = float(arrival.get("longitude") or center_lon - 0.028)
    departure_lat = float(departure.get("latitude") or center_lat + 0.072)
    departure_lon = float(departure.get("longitude") or center_lon + 0.095)
    events: list[GraphNode] = [
        GraphNode(
            key="arrival-anchor",
            title=arrival["location"],
            role="ARRIVAL",
            start_at=arrival_at.isoformat(),
            end_at=(arrival_at + timedelta(minutes=20)).isoformat(),
            latitude=arrival_lat,
            longitude=arrival_lon,
            locked=True,
        )
    ]
    check_in_at = datetime.fromisoformat(offer.check_in_at)
    drop = _load(offer.luggage_drop_json, {})
    if operations.baggage_present and arrival_at < check_in_at:
        if not bool(drop.get("available")):
            return []
        drop_at = arrival_at + timedelta(minutes=60)
        events.append(
            GraphNode(
                key=f"stay:{offer.external_offer_id}:luggage-drop",
                title=f"Luggage drop · {offer.property_name}",
                role="LUGGAGE_DROP",
                start_at=drop_at.isoformat(),
                end_at=(drop_at + timedelta(minutes=20)).isoformat(),
                latitude=offer.latitude,
                longitude=offer.longitude,
                locked=True,
            )
        )
    events.append(
        GraphNode(
            key=f"stay:{offer.external_offer_id}:check-in",
            title=f"Check in · {offer.property_name}",
            role="CHECK_IN",
            start_at=max(check_in_at, arrival_at + timedelta(minutes=45)).isoformat(),
            end_at=(
                max(check_in_at, arrival_at + timedelta(minutes=45)) + timedelta(minutes=20)
            ).isoformat(),
            latitude=offer.latitude,
            longitude=offer.longitude,
            locked=True,
        )
    )
    for item in city.get("activities", []):
        start_at = _at_on_day(arrival_at, int(item["day_offset"]), str(item["start"]))
        end_at = _at_on_day(arrival_at, int(item["day_offset"]), str(item["end"]))
        if start_at <= arrival_at + timedelta(minutes=20) or end_at >= departure_at:
            continue
        events.append(
            GraphNode(
                key=f"place:{item['key']}",
                title=str(item["title"]),
                role="ACTIVITY",
                start_at=start_at.isoformat(),
                end_at=end_at.isoformat(),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                place_key=str(item["key"]),
                estimated_cost_minor=int(item.get("cost_amount_minor", 0)),
                cost_status=str(item.get("cost_status", "UNKNOWN")),
            )
        )
    for day_offset in range(_nights(context, journey)):
        overnight_at = _at_on_day(arrival_at, day_offset, "22:30")
        if arrival_at < overnight_at < departure_at:
            events.append(
                GraphNode(
                    key=f"stay:{offer.external_offer_id}:night:{day_offset + 1}",
                    title=f"Overnight · {offer.property_name}",
                    role="STAY",
                    start_at=overnight_at.isoformat(),
                    end_at=(overnight_at + timedelta(hours=8)).isoformat(),
                    latitude=offer.latitude,
                    longitude=offer.longitude,
                    locked=True,
                )
            )
    check_out_at = datetime.fromisoformat(offer.check_out_at)
    events.append(
        GraphNode(
            key=f"stay:{offer.external_offer_id}:check-out",
            title=f"Check out · {offer.property_name}",
            role="CHECK_OUT",
            start_at=check_out_at.isoformat(),
            end_at=(check_out_at + timedelta(minutes=20)).isoformat(),
            latitude=offer.latitude,
            longitude=offer.longitude,
            locked=True,
        )
    )
    events.append(
        GraphNode(
            key="departure-anchor",
            title=departure["location"],
            role="DEPARTURE",
            start_at=(departure_at - timedelta(minutes=10)).isoformat(),
            end_at=departure_at.isoformat(),
            latitude=departure_lat,
            longitude=departure_lon,
            locked=True,
        )
    )
    ordered = sorted(events, key=lambda node: datetime.fromisoformat(node.start_at))
    result: list[GraphNode] = []
    cursor = arrival_at - timedelta(minutes=1)
    for node in ordered:
        start = datetime.fromisoformat(node.start_at)
        end = datetime.fromisoformat(node.end_at)
        if start < cursor and node.role not in {"STAY"}:
            continue
        result.append(node)
        cursor = max(cursor, end)
    return result


def _distance_m(a: GraphNode, b: GraphNode) -> int:
    lat_scale = 111_320.0
    lon_scale = 111_320.0 * math.cos(math.radians((a.latitude + b.latitude) / 2))
    return max(
        80,
        int(
            math.hypot(
                (a.latitude - b.latitude) * lat_scale, (a.longitude - b.longitude) * lon_scale
            )
        ),
    )


def _mode_fact(
    journey_id: str,
    option_id: str | None,
    from_node: GraphNode,
    to_node: GraphNode,
    mode: str,
    currency: str = "CNY",
) -> MobilityFact:
    distance = _distance_m(from_node, to_node)
    profiles = {
        "WALK": (
            max(5, math.ceil(distance / 75)),
            0,
            "FREE_KNOWN",
            None,
            0,
            "HIGH",
            0.82,
            False,
        ),
        "BICYCLE": (
            max(4, math.ceil(distance / 210)),
            None,
            "UNKNOWN",
            5,
            0,
            "MEDIUM",
            0.78,
            True,
        ),
        "TRANSIT": (
            max(8, math.ceil(distance / 330) + 6),
            None,
            "UNKNOWN",
            5,
            1,
            "LOW",
            0.91,
            True,
        ),
        "AUTO": (
            max(5, math.ceil(distance / 430) + 3),
            None,
            "UNKNOWN",
            2,
            0,
            "LOW",
            0.88,
            True,
        ),
        "RIDE_HAIL": (
            max(5, math.ceil(distance / 420) + 4),
            None,
            "UNKNOWN",
            2,
            0,
            "LOW",
            0.84,
            True,
        ),
    }
    duration, cost_major, cost_status, walking, transfers, exposure, reliability, paid = (
        profiles[mode]
    )
    normalized_currency = str(currency or "CNY").upper()
    estimate = SYNTHETIC_ESTIMATE_MAJOR_BY_CURRENCY.get(normalized_currency, {}).get(mode)
    if mode not in {"WALK", "RIDE_HAIL"} and estimate is not None:
        cost_major = estimate
        cost_status = "ESTIMATED"
    cost = major_to_minor(cost_major, normalized_currency) if cost_major is not None else None
    if mode == "WALK":
        walking = duration
    captured = _now()
    geometry = {
        "type": "Feature",
        "properties": {"provider": "citynexus-synthetic-fixture", "mode": mode, "crs": "WGS84"},
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [from_node.longitude, from_node.latitude],
                [to_node.longitude, to_node.latitude],
            ],
        },
    }
    return MobilityFact(
        id=str(uuid4()),
        journey_id=journey_id,
        option_id=option_id,
        from_key=from_node.key,
        to_key=to_node.key,
        mode=mode,
        duration_min=int(duration),
        distance_m=distance,
        cost_amount_minor=cost,
        currency=normalized_currency if cost is not None else None,
        cost_status=cost_status,
        walking_min=int(walking or 0),
        transfers=int(transfers),
        weather_exposure=exposure,
        reliability_score=float(reliability),
        provider_key="citynexus-synthetic-fixture",
        provenance="SYNTHETIC_FIXTURE",
        geometry_json=_json(geometry),
        crs="WGS84",
        paid_mode=paid,
        evidence_json=_json(
            {
                "fact_type": "normalized_route_leg",
                "provider_status": "SYNTHETIC_FIXTURE",
                "cost_status": cost_status,
                "cost_provenance": "CITYNEXUS_ESTIMATE" if cost_status == "ESTIMATED" else ("FREE_KNOWN" if mode == "WALK" else "UNKNOWN"),
                "coordinate_boundary": "captured provider coordinates normalized to WGS84",
            }
        ),
        captured_at=captured,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
    )


def capture_mobility_facts(
    session: Session, journey: Journey, offer: AccommodationOfferSnapshot
) -> list[MobilityFact]:
    nodes = build_candidate_nodes(session, journey, offer)
    facts: list[MobilityFact] = []
    for from_node, to_node in zip(nodes, nodes[1:]):
        for mode in MODES:
            existing = session.scalar(
                select(MobilityFact).where(
                    MobilityFact.journey_id == journey.id,
                    MobilityFact.from_key == from_node.key,
                    MobilityFact.to_key == to_node.key,
                    MobilityFact.mode == mode,
                )
            )
            if existing is None:
                existing = _mode_fact(
                    journey.id,
                    None,
                    from_node,
                    to_node,
                    mode,
                    journey.budget_currency,
                )
                session.add(existing)
            facts.append(existing)
    session.flush()
    return facts


def _day_payload(nodes: list[GraphNode], selected: dict[str, MobilityFact]) -> list[dict[str, Any]]:
    grouped: dict[str, list[GraphNode]] = {}
    for node in nodes:
        grouped.setdefault(datetime.fromisoformat(node.start_at).date().isoformat(), []).append(
            node
        )
    days: list[dict[str, Any]] = []
    for index, (local_date, items) in enumerate(sorted(grouped.items()), start=1):
        outgoing = [
            selected[f"{item.key}->{next_item.key}"].mode
            for item, next_item in zip(items, items[1:])
            if f"{item.key}->{next_item.key}" in selected
        ]
        anchor = next(
            (item.role for item in items if item.role in {"ARRIVAL", "DEPARTURE"}), "STAY"
        )
        days.append(
            {
                "day": index,
                "date": local_date,
                "label": datetime.fromisoformat(items[0].start_at).strftime("%A · %d %b"),
                "anchor": anchor,
                "activities": [item.title for item in items],
                "mode": outgoing[0] if outgoing else "WALK",
            }
        )
    return days


def generate_stay_options(
    session: Session, journey: Journey, *, weather: str = "NORMAL"
) -> list[StayJourneyOption]:
    offers = capture_accommodation_offers(session, journey)
    preference_items = planning_preference_items(session, journey.traveler_id, journey.id)
    learned_dimensions = {
        str(getattr(item, "preference_key", ""))
        for item in preference_items
        if getattr(item, "source", "") in {"LEARNED_SOFT", "EXPLICIT_MISSION"}
    }
    staged: list[tuple[StayJourneyOption, list[MobilityFact]]] = []
    for provisional_rank, offer in enumerate(offers, start=1):
        nodes = build_candidate_nodes(session, journey, offer)
        if len(nodes) < 2:
            continue
        facts = capture_mobility_facts(session, journey, offer)
        try:
            solver_result = solve_mode_choices(
                facts,
                budget_minor=max(
                    0, int(journey.budget_amount_minor) - int(offer.total_amount_minor)
                ),
                weather_state=weather,
                learned_dimensions=learned_dimensions,
            )
        except ValueError:
            continue
        selected_facts = list(solver_result.selected)
        selected_map = {f"{item.from_key}->{item.to_key}": item for item in selected_facts}
        mobility_total = sum(int(item.cost_amount_minor or 0) for item in selected_facts)
        walking = sum(item.walking_min for item in selected_facts)
        latest_pre_departure = datetime.fromisoformat(nodes[-2].end_at)
        departure_at = datetime.fromisoformat(nodes[-1].start_at)
        final_leg = selected_map.get(f"{nodes[-2].key}->{nodes[-1].key}")
        margin = max(
            0,
            int((departure_at - latest_pre_departure).total_seconds() // 60)
            - int(final_leg.duration_min if final_leg else 0),
        )
        check_in = next((node for node in nodes if node.role == "CHECK_IN"), nodes[0])
        arrival_fit = (
            1.0
            if datetime.fromisoformat(check_in.start_at) >= datetime.fromisoformat(nodes[0].end_at)
            else 0.0
        )
        departure_fit = min(1.0, margin / 60) if margin else 0.0
        preference_bonus = 0.08 if "low_walking" in learned_dimensions and walking <= 45 else 0.0
        total_cost = int(offer.total_amount_minor) + mobility_total
        score = round(
            max(
                0.0,
                1.0
                - total_cost / max(1, int(journey.budget_amount_minor)) * 0.30
                - walking / 1500
                + min(margin, 90) / 900
                + (0.08 if offer.refundable else 0.0)
                + preference_bonus,
            ),
            4,
        )
        raw_leg_map = [
            {
                "from_key": item.from_key,
                "to_key": item.to_key,
                "mode": item.mode,
                "mobility_fact_id": item.id,
                "cost_status": item.cost_status,
            }
            for item in selected_facts
        ]
        impact = {
            "schedule_evidence": {
                "protected_margin_min": margin,
                "arrival_fit": arrival_fit,
                "departure_fit": departure_fit,
                "source": "actual candidate timeline and selected route durations",
            },
            "weather": {
                "state": weather,
                "protected_commitments_preserved": margin >= 0,
            },
            "modes_available": list(MODES),
            "twin": {
                "dimensions": sorted(learned_dimensions),
                "authority": "ranking_only",
            },
            "mode_solver": {
                "kind": solver_result.optimizer_kind,
                "status": solver_result.solver_status,
                "objective_value": solver_result.objective_value,
                "unknown_paid_cost_selected": solver_result.unknown_paid_cost_selected,
            },
            "leg_mode_map": raw_leg_map,
        }
        existing = session.scalar(
            select(StayJourneyOption).where(
                StayJourneyOption.journey_id == journey.id,
                StayJourneyOption.accommodation_offer_id == offer.id,
            )
        )
        if existing is None:
            existing = StayJourneyOption(
                id=str(uuid4()),
                journey_id=journey.id,
                accommodation_offer_id=offer.id,
                rank=100 + provisional_rank,
                score=score,
                status="CANDIDATE",
                stay_total_minor=offer.total_amount_minor,
                daily_travel_minor=mobility_total,
                mobility_total_minor=mobility_total,
                walking_min=walking,
                protected_margin_min=margin,
                arrival_fit=arrival_fit,
                departure_fit=departure_fit,
                cancellation_score=1.0 if offer.refundable else 0.25,
                days_json=_json(_day_payload(nodes, selected_map)),
                leg_modes_json=_json(raw_leg_map),
                journey_impact_json=_json(impact),
                hard_constraints_passed=margin >= 0,
                optimizer_kind=solver_result.optimizer_kind,
                weather_state=weather,
                materialized_plan_version_id=None,
                created_at=_now(),
            )
            session.add(existing)
        else:
            existing.rank = 100 + provisional_rank
            existing.score = score
            existing.weather_state = weather
            existing.days_json = _json(_day_payload(nodes, selected_map))
            existing.leg_modes_json = _json(raw_leg_map)
            existing.journey_impact_json = _json(impact)
            existing.mobility_total_minor = mobility_total
            existing.daily_travel_minor = mobility_total
            existing.walking_min = walking
            existing.protected_margin_min = margin
            existing.arrival_fit = arrival_fit
            existing.departure_fit = departure_fit
            existing.hard_constraints_passed = margin >= 0
            existing.optimizer_kind = solver_result.optimizer_kind
        session.flush()
        for fact in selected_facts:
            fact.option_id = existing.id
        staged.append((existing, selected_facts))
    session.flush()
    ranked = sorted((item for item, _facts in staged), key=lambda item: (-item.score, item.id))
    for rank, item in enumerate(ranked, start=1):
        item.rank = rank
    session.flush()
    return ranked


def _active_plan_payload(session: Session, journey: Journey) -> dict[str, Any] | None:
    if not journey.active_plan_version_id:
        return None
    plan = session.get(PlanVersion, journey.active_plan_version_id)
    if plan is None:
        return None
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan.id).order_by(Activity.sequence_no)
    ).all()
    legs = session.scalars(
        select(JourneyLeg)
        .where(JourneyLeg.plan_version_id == plan.id)
        .order_by(JourneyLeg.sequence_no)
    ).all()
    protected_activity_ids = set(
        session.scalars(
            select(Commitment.activity_id).where(
                Commitment.journey_id == journey.id,
                Commitment.status == "ACTIVE",
                Commitment.activity_id.is_not(None),
            )
        ).all()
    )
    location = session.scalar(
        select(LocationObservation)
        .where(LocationObservation.journey_id == journey.id)
        .order_by(LocationObservation.captured_at.desc(), LocationObservation.id.desc())
    )
    disruptions = session.scalars(
        select(Event)
        .where(Event.journey_id == journey.id, Event.status.in_(("DETECTED", "ACKNOWLEDGED")))
        .order_by(Event.detected_at.desc(), Event.id.desc())
        .limit(10)
    ).all()
    return {
        "id": plan.id,
        "version_no": plan.version_no,
        "status": plan.status,
        "source": plan.source,
        "mobility_snapshot_id": plan.mobility_snapshot_id,
        "mobility_evidence": {
            "snapshot_id": plan.mobility_snapshot_id,
            "expires_at": _load(plan.mobility_evidence_json, {}).get("expires_at"),
            "aggregate_provenance": _load(plan.mobility_evidence_json, {}).get("aggregate_provenance"),
            "replayable": bool(plan.mobility_evidence_json),
        },
        "current_activity_id": journey.current_activity_id,
        "activities": [
            {
                "id": item.id,
                "sequence_no": item.sequence_no,
                "type": item.activity_type,
                "title": item.title,
                "start_at": item.start_at,
                "end_at": item.end_at,
                "locked": bool(item.locked),
                "protected": item.id in protected_activity_ids,
                "metadata": _load(item.metadata_json, {}),
            }
            for item in activities
        ],
        "legs": [journey_leg_payload(item) for item in legs],
        "user_location": {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy_m": location.accuracy_m,
            "captured_at": location.captured_at,
            "source": location.source,
        }
        if location
        else None,
        "disruptions": [
            {
                "id": item.id,
                "type": item.event_type,
                "severity": item.severity,
                "affected_activity_id": item.affected_activity_id,
                "occurred_at": item.occurred_at,
                "payload": _load(item.payload_json, {}),
            }
            for item in disruptions
        ],
    }


def experience_payload(session: Session, journey: Journey) -> dict[str, Any]:
    context = _context(session, journey)
    operations = _operations_context(session, journey)
    preference_items = planning_preference_items(session, journey.traveler_id, journey.id)
    offers = session.scalars(
        select(AccommodationOfferSnapshot)
        .where(AccommodationOfferSnapshot.journey_id == journey.id)
        .order_by(AccommodationOfferSnapshot.total_amount_minor)
    ).all()
    options = session.scalars(
        select(StayJourneyOption)
        .where(StayJourneyOption.journey_id == journey.id)
        .order_by(StayJourneyOption.rank)
    ).all()
    facts = session.scalars(
        select(MobilityFact)
        .where(MobilityFact.journey_id == journey.id)
        .order_by(MobilityFact.from_key, MobilityFact.to_key, MobilityFact.mode)
    ).all()
    selected = next((item for item in options if item.status == "SELECTED"), None)
    return {
        "journey": {
            "id": journey.id,
            "traveler_id": journey.traveler_id,
            "title": journey.title,
            "city_code": journey.city_code,
            "timezone": journey.timezone,
            "start_at": journey.start_at,
            "end_at": journey.end_at,
            "status": journey.status,
            "active_plan_version_id": journey.active_plan_version_id,
            "budget": {
                "amount_minor": journey.budget_amount_minor,
                "currency": journey.budget_currency,
            },
        },
        "trip": {
            "arrival_anchor": _anchor(context, journey, "arrival"),
            "departure_anchor": _anchor(context, journey, "departure"),
            "party_size": context.party_size,
            "occupancy": _load(context.occupancy_json, {}),
            "stay_budget": {
                "amount_minor": context.stay_budget_amount_minor,
                "currency": context.stay_budget_currency,
            },
            "baggage": {
                "present": bool(operations.baggage_present),
                "size_class": operations.baggage_size_class,
                "luggage_drop_required": bool(operations.luggage_drop_required),
            },
        },
        "offers": [offer_payload(item) for item in offers],
        "options": [option_payload(item, offers) for item in options],
        "selected_option_id": selected.id if selected else None,
        "mobility_facts": [fact_payload(item) for item in facts],
        "active_plan": _active_plan_payload(session, journey),
        "traveler_twin": {
            "explicit_dimensions": sorted(
                {
                    str(getattr(item, "preference_key", ""))
                    for item in preference_items
                    if getattr(item, "source", "") != "LEARNED_SOFT"
                }
            ),
            "learned_soft_dimensions": sorted(
                {
                    str(getattr(item, "preference_key", ""))
                    for item in preference_items
                    if getattr(item, "source", "") == "LEARNED_SOFT"
                }
            ),
            "authority": "soft_planning_input_only",
        },
        "provider_mesh": {
            "accommodation": {
                "captured": {
                    "provider_key": CapturedAccommodationProvider.provider_key,
                    "status": "READY" if offers else "UNAVAILABLE_FOR_CITY",
                    "provenance": "CAPTURED_REPLAY",
                },
                "live": {
                    "provider_key": LiveAccommodationProvider.provider_key,
                    "status": "NOT_CONFIGURED",
                },
            },
            "mobility": {
                "amap": {
                    "status": "READY" if os.getenv("AMAP_WEB_KEY") else "NOT_CONFIGURED",
                    "captured_fallback": "READY"
                    if city_fixture(journey.city_code)
                    else "UNAVAILABLE_FOR_CITY",
                    "coordinate_crs": "GCJ02 at provider boundary; canonical domain WGS84",
                },
                "valhalla": {"status": "NOT_CONFIGURED"},
                "transit_realtime": {"status": "UNKNOWN_REALTIME"},
                "ride_hail": {"status": "UNKNOWN_COST"},
            },
        },
    }


def offer_payload(item: AccommodationOfferSnapshot) -> dict[str, Any]:
    expired = bool(
        item.expires_at and datetime.fromisoformat(item.expires_at) <= datetime.now(timezone.utc)
    )
    return {
        "id": item.id,
        "external_offer_id": item.external_offer_id,
        "provider_key": item.provider_key,
        "property_name": item.property_name,
        "location": {
            "latitude": item.latitude,
            "longitude": item.longitude,
            "crs": item.coordinate_crs,
        },
        "room_type": item.room_type,
        "occupancy": _load(item.occupancy_json, {}),
        "check_in_at": item.check_in_at,
        "check_out_at": item.check_out_at,
        "nightly_amount_minor": item.nightly_amount_minor,
        "taxes_amount_minor": item.taxes_amount_minor,
        "total_amount_minor": item.total_amount_minor,
        "currency": item.currency,
        "cancellation_policy": _load(item.cancellation_policy_json, {}),
        "luggage_drop": _load(item.luggage_drop_json, {}),
        "refundable": bool(item.refundable),
        "evidence": _load(item.evidence_json, {}),
        "captured_at": item.captured_at,
        "expires_at": item.expires_at,
        "status": "EXPIRED" if expired else item.status,
        "bookable": not expired and item.status not in {"EXPIRED", "WITHDRAWN"},
    }


def option_payload(
    item: StayJourneyOption, offers: list[AccommodationOfferSnapshot]
) -> dict[str, Any]:
    offer = next(offer for offer in offers if offer.id == item.accommodation_offer_id)
    raw_leg_modes = _load(item.leg_modes_json, [])
    legacy_modes = [
        str(value.get("mode"))
        for value in raw_leg_modes
        if isinstance(value, dict) and value.get("mode")
    ]
    if not legacy_modes:
        legacy_modes = [str(value) for value in raw_leg_modes]
    return {
        "id": item.id,
        "rank": item.rank,
        "status": item.status,
        "score": item.score,
        "stay": offer_payload(offer),
        "stay_total_minor": item.stay_total_minor,
        "daily_travel_minor": item.daily_travel_minor,
        "mobility_total_minor": item.mobility_total_minor,
        "walking_min": item.walking_min,
        "protected_margin_min": item.protected_margin_min,
        "arrival_fit": item.arrival_fit,
        "departure_fit": item.departure_fit,
        "cancellation_score": item.cancellation_score,
        "days": _load(item.days_json, []),
        "leg_modes": legacy_modes,
        "leg_mode_map": raw_leg_modes,
        "journey_impact": _load(item.journey_impact_json, {}),
        "hard_constraints_passed": bool(item.hard_constraints_passed),
        "optimizer_kind": item.optimizer_kind,
        "weather_state": item.weather_state,
        "materialized_plan_version_id": item.materialized_plan_version_id,
    }


def fact_payload(item: MobilityFact) -> dict[str, Any]:
    return {
        "id": item.id,
        "from_key": item.from_key,
        "to_key": item.to_key,
        "mode": item.mode,
        "duration_min": item.duration_min,
        "distance_m": item.distance_m,
        "cost_amount_minor": item.cost_amount_minor,
        "currency": item.currency,
        "cost_status": item.cost_status,
        "paid_mode": bool(item.paid_mode),
        "walking_min": item.walking_min,
        "transfers": item.transfers,
        "weather_exposure": item.weather_exposure,
        "reliability_score": item.reliability_score,
        "provider_key": item.provider_key,
        "provenance": item.provenance,
        "geometry": _load(item.geometry_json, {}),
        "crs": item.crs,
        "evidence": _load(item.evidence_json, {}),
        "captured_at": item.captured_at,
        "expires_at": item.expires_at,
    }


def journey_leg_payload(item: JourneyLeg) -> dict[str, Any]:
    return {
        "id": item.id,
        "sequence_no": item.sequence_no,
        "from_activity_id": item.from_activity_id,
        "to_activity_id": item.to_activity_id,
        "from_key": item.from_key,
        "to_key": item.to_key,
        "mode": item.mode,
        "depart_at": item.depart_at,
        "arrive_at": item.arrive_at,
        "duration_min": item.duration_min,
        "distance_m": item.distance_m,
        "cost_amount_minor": item.cost_amount_minor,
        "currency": item.currency,
        "cost_status": item.cost_status,
        "walking_min": item.walking_min,
        "transfers": item.transfers,
        "reliability_score": item.reliability_score,
        "weather_exposure": item.weather_exposure,
        "geometry": _load(item.geometry_json, {}),
        "crs": item.crs,
        "provider_key": item.provider_key,
        "provenance": item.provenance,
        "captured_at": item.captured_at,
        "expires_at": item.expires_at,
    }
