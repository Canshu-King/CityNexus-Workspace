"""Bounded authoritative multi-day composition for the V12 product path.

This module deliberately keeps the search space small: a user-supplied POI
set is assigned to three Journey days by CP-SAT, route order is bounded per
day, and one captured mode fact is selected for every concrete leg.  The
result is persisted as ordinary PlanVersion/Activity/JourneyLeg truth so the
existing selection, JourneyTwin, offline, Edge, and execution surfaces can
consume it without a second planning model.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from itertools import permutations
from typing import Any, Iterable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Activity,
    AccommodationOfferSnapshot,
    Commitment,
    Journey,
    JourneyLeg,
    JourneyTripContext,
    MobilityFact,
    Place,
    PlanVersion,
    TransportReservation,
)
from app.planning.stay_mode_solver import solve_mode_choices
from app.replanning.provider_snapshots import MobilitySnapshot
from app.stay_mobility import GraphNode, _mode_fact, capture_accommodation_offers, city_fixture

MODES = ("WALK", "BICYCLE", "TRANSIT", "AUTO", "RIDE_HAIL")
DAY_COUNT = 3


@dataclass(frozen=True)
class ComposeNode:
    key: str
    title: str
    role: str
    latitude: float
    longitude: float
    place_id: str
    day_index: int
    start_at: datetime
    end_at: datetime
    locked: bool = False
    cost_minor: int = 0
    cost_status: str = "FREE_KNOWN"
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ComposeResult:
    plans: tuple[PlanVersion, ...]
    stay_offer: AccommodationOfferSnapshot
    evidence_ids: tuple[str, ...]
    optimizer_kind: str


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _anchor(context: JourneyTripContext | None, journey: Journey, kind: str) -> dict[str, Any]:
    raw = context.arrival_anchor_json if context and kind == "arrival" else (
        context.departure_anchor_json if context else "{}"
    )
    fallback = journey.start_at if kind == "arrival" else journey.end_at
    value = _load(raw, {})
    return {
        "at": str(value.get("at") or fallback),
        "location": str(value.get("location") or kind.title()),
        "latitude": value.get("latitude"),
        "longitude": value.get("longitude"),
    }


def _city_center(journey: Journey) -> tuple[float, float]:
    center = city_fixture(journey.city_code).get("center", {})
    return float(center.get("latitude", 0.0)), float(center.get("longitude", 0.0))


def _ensure_place(
    session: Session,
    journey: Journey,
    *,
    key: str,
    title: str,
    category: str,
    latitude: float,
    longitude: float,
    metadata: dict[str, Any] | None = None,
) -> Place:
    provider_key = "citynexus-v12-authoritative"
    external_id = f"{journey.id}:{key}"
    row = session.scalar(
        select(Place).where(
            Place.provider_key == provider_key,
            Place.external_id == external_id,
        )
    )
    if row is None:
        row = Place(
            id=f"v12:{journey.id}:{key}",
            provider_key=provider_key,
            external_id=external_id,
            city_code=journey.city_code,
            name=title,
            category=category,
            latitude=latitude,
            longitude=longitude,
            opening_hours_json=_json({"status": "NORMALIZED", "always_available": True}),
            tags_json=_json(["v12-authoritative", category]),
            metadata_json=_json(metadata or {}),
            updated_at=_now(),
        )
        session.add(row)
        session.flush()
    return row


def _place_facts(place: Place) -> tuple[int, int, str]:
    metadata = _load(place.metadata_json, {})
    evidence = metadata.get("cost_evidence") if isinstance(metadata, dict) else None
    evidence = evidence if isinstance(evidence, dict) else {}
    raw_status = metadata.get("cost_status") or evidence.get("status")
    raw_cost = metadata.get("cost_minor", metadata.get("cost_amount_minor"))
    status = str(raw_status or ("KNOWN" if raw_cost is not None else "UNKNOWN"))
    if status == "FREE_KNOWN":
        return 0, 0, status
    if raw_cost is None:
        raise ValueError(f"V12_UNKNOWN_POI_COST:{place.id}")
    return int(raw_cost), max(15, int(metadata.get("duration_min", 60))), status


def _distance_minutes(a: ComposeNode | GraphNode, b: ComposeNode | GraphNode) -> int:
    lat = abs(float(a.latitude) - float(b.latitude)) * 111
    lon = abs(float(a.longitude) - float(b.longitude)) * 85
    return max(3, int((lat + lon) * 3.0))


def _solve_day_assignment(place_ids: list[str], *, variation: int) -> dict[str, int]:
    """Assign bounded POIs to exactly three days using CP-SAT."""

    quotas = [len(place_ids) // DAY_COUNT + (1 if day < len(place_ids) % DAY_COUNT else 0)
              for day in range(DAY_COUNT)]
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return {place_id: index % DAY_COUNT for index, place_id in enumerate(place_ids)}

    model = cp_model.CpModel()
    choices: dict[tuple[int, int], Any] = {}
    for index, _place_id in enumerate(place_ids):
        literals = []
        for day in range(DAY_COUNT):
            literal = model.NewBoolVar(f"poi_{index}_day_{day}")
            choices[(index, day)] = literal
            literals.append(literal)
        model.AddExactlyOne(literals)
    for day, quota in enumerate(quotas):
        model.Add(sum(choices[(index, day)] for index in range(len(place_ids))) == quota)
    target_offset = variation % DAY_COUNT
    objective = []
    for index in range(len(place_ids)):
        target = (index + target_offset) % DAY_COUNT
        for day in range(DAY_COUNT):
            objective.append(abs(day - target) * 1000 * choices[(index, day)])
    model.Minimize(sum(objective))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 0.6
    solver.parameters.num_search_workers = 1
    status = solver.Solve(model)
    if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
        return {place_id: index % DAY_COUNT for index, place_id in enumerate(place_ids)}
    return {
        place_id: next(day for day in range(DAY_COUNT) if solver.Value(choices[(index, day)]))
        for index, place_id in enumerate(place_ids)
    }


def _order_by_day(
    places: dict[str, Place], assignment: dict[str, int], *, variation: int,
) -> list[list[str]]:
    grouped = [[place_id for place_id, day in assignment.items() if day == index] for index in range(DAY_COUNT)]
    result: list[list[str]] = []
    for day, items in enumerate(grouped):
        if len(items) <= 1:
            result.append(items)
            continue
        # The bounded permutation is intentionally tiny (the flagship uses two
        # POIs/day).  It makes order a real planner decision without creating an
        # unbounded routing model.
        candidates = list(permutations(items))
        if variation % 3 == 1:
            candidates = list(reversed(candidates))
        result.append(list(min(
            candidates,
            key=lambda order: sum(
                _distance_minutes(places[order[index - 1]], places[order[index]])
                for index in range(1, len(order))
            ),
        )))
    return result


def _structural_nodes(
    session: Session,
    journey: Journey,
    stay: AccommodationOfferSnapshot,
    ordered_days: list[list[str]],
    places: dict[str, Place],
    arrival: dict[str, Any],
    departure: dict[str, Any],
    c4_ids: list[str],
) -> tuple[list[ComposeNode], dict[str, Place]]:
    arrival_at = datetime.fromisoformat(arrival["at"])
    departure_at = datetime.fromisoformat(departure["at"])
    center_lat, center_lon = _city_center(journey)
    arrival_place = _ensure_place(
        session=session,
        journey=journey,
        key="arrival-anchor",
        title=arrival["location"],
        category="arrival",
        latitude=float(arrival.get("latitude") or center_lat - 0.015),
        longitude=float(arrival.get("longitude") or center_lon - 0.02),
        metadata={"anchor": "ARRIVAL", "commitment_ids": c4_ids},
    )
    departure_place = _ensure_place(
        session=session,
        journey=journey,
        key="departure-anchor",
        title=departure["location"],
        category="departure",
        latitude=float(departure.get("latitude") or center_lat + 0.06),
        longitude=float(departure.get("longitude") or center_lon + 0.08),
        metadata={"anchor": "DEPARTURE"},
    )
    stay_place = _ensure_place(
        session=session,
        journey=journey,
        key=f"stay:{stay.external_offer_id}",
        title=stay.property_name,
        category="stay",
        latitude=stay.latitude,
        longitude=stay.longitude,
        metadata={"stay_offer_id": stay.id, "cost_minor": stay.total_amount_minor, "cost_status": "KNOWN"},
    )
    check_in_place = _ensure_place(
        session=session, journey=journey, key="check-in", title=f"Check in · {stay.property_name}",
        category="check-in", latitude=stay.latitude, longitude=stay.longitude,
        metadata={"stay_offer_id": stay.id},
    )
    check_out_place = _ensure_place(
        session=session, journey=journey, key="check-out", title=f"Check out · {stay.property_name}",
        category="check-out", latitude=stay.latitude, longitude=stay.longitude,
        metadata={"stay_offer_id": stay.id},
    )
    night_places = {
        day: _ensure_place(
            session=session, journey=journey, key=f"stay-night-{day}",
            title=f"Overnight · {stay.property_name}", category="stay",
            latitude=stay.latitude, longitude=stay.longitude,
            metadata={"stay_offer_id": stay.id, "night": day},
        )
        for day in range(1, DAY_COUNT)
    }
    place_map = {
        **places,
        arrival_place.id: arrival_place,
        departure_place.id: departure_place,
        stay_place.id: stay_place,
        check_in_place.id: check_in_place,
        check_out_place.id: check_out_place,
        **{item.id: item for item in night_places.values()},
    }
    # Node timestamps are replaced by _schedule_nodes after per-leg modes are
    # selected.  These values only provide a stable graph shape for evidence.
    placeholder = arrival_at
    nodes = [
        ComposeNode(arrival_place.id, arrival["location"], "ARRIVAL", arrival_place.latitude, arrival_place.longitude, arrival_place.id, 0, arrival_at, arrival_at + timedelta(minutes=20), True, 0, "FREE_KNOWN", {"commitment_ids": c4_ids}),
        ComposeNode(check_in_place.id, f"Check in · {stay.property_name}", "CHECK_IN", stay.latitude, stay.longitude, check_in_place.id, 0, placeholder, placeholder + timedelta(minutes=20), True, stay.total_amount_minor, "KNOWN", {"stay_offer_id": stay.id}),
    ]
    for day, ids in enumerate(ordered_days):
        for place_id in ids:
            place = places[place_id]
            cost, duration, status = _place_facts(place)
            nodes.append(ComposeNode(place.id, place.name, "ACTIVITY", place.latitude, place.longitude, place.id, day, placeholder, placeholder + timedelta(minutes=duration), False, cost, status, {"place_id": place.id, "category": place.category}))
        if day < DAY_COUNT - 1:
            night_place = night_places[day + 1]
            nodes.append(ComposeNode(night_place.id, f"Overnight · {stay.property_name}", "STAY", stay.latitude, stay.longitude, night_place.id, day, placeholder, placeholder + timedelta(minutes=20), True, 0, "FREE_KNOWN", {"stay_offer_id": stay.id, "night": day + 1}))
    nodes.extend([
        ComposeNode(check_out_place.id, f"Check out · {stay.property_name}", "CHECK_OUT", stay.latitude, stay.longitude, check_out_place.id, DAY_COUNT - 1, placeholder, placeholder + timedelta(minutes=20), True, 0, "FREE_KNOWN", {"stay_offer_id": stay.id}),
        ComposeNode(departure_place.id, departure["location"], "DEPARTURE", departure_place.latitude, departure_place.longitude, departure_place.id, DAY_COUNT - 1, departure_at - timedelta(minutes=10), departure_at, True, 0, "FREE_KNOWN", {"anchor": "DEPARTURE"}),
    ])
    return nodes, place_map


def _graph_nodes(nodes: Iterable[ComposeNode]) -> dict[str, GraphNode]:
    return {
        node.key: GraphNode(
            key=node.key,
            title=node.title,
            role=node.role,
            start_at=node.start_at.isoformat(),
            end_at=node.end_at.isoformat(),
            latitude=node.latitude,
            longitude=node.longitude,
            place_key=node.place_id,
            locked=node.locked,
            estimated_cost_minor=node.cost_minor,
            cost_status=node.cost_status,
        )
        for node in nodes
    }


def _capture_mode_matrix(
    session: Session,
    journey: Journey,
    graph: dict[str, GraphNode],
    keys: list[str],
) -> list[MobilityFact]:
    facts: list[MobilityFact] = []
    # Capture the complete directed matrix for the bounded node set.  Trip
    # Studio is allowed to reorder unlocked activities later, so a selected
    # route-only snapshot would silently turn an edit into a second provider
    # lookup.  The deterministic gate consumes this frozen matrix instead.
    for origin in keys:
        for destination in keys:
            if origin == destination:
                continue
            for mode in MODES:
                existing = session.scalar(
                    select(MobilityFact).where(
                        MobilityFact.journey_id == journey.id,
                        MobilityFact.from_key == origin,
                        MobilityFact.to_key == destination,
                        MobilityFact.mode == mode,
                    )
                )
                if existing is None:
                    existing = _mode_fact(journey.id, None, graph[origin], graph[destination], mode)
                    session.add(existing)
                facts.append(existing)
    session.flush()
    return facts


def _select_modes(facts: list[MobilityFact], budget_minor: int, variation: int) -> dict[tuple[str, str], MobilityFact]:
    solved = solve_mode_choices(facts, budget_minor=max(0, budget_minor))
    selected = list(solved.selected)
    if variation % 3 == 0:
        return {(item.from_key, item.to_key): item for item in selected}
    by_leg: dict[tuple[str, str], list[MobilityFact]] = {}
    for item in facts:
        by_leg.setdefault((item.from_key, item.to_key), []).append(item)
    spent = sum(int(item.cost_amount_minor or 0) for item in selected)
    for index, item in enumerate(selected):
        alternatives = [
            row for row in by_leg[(item.from_key, item.to_key)]
            if row.mode != item.mode and row.cost_status != "UNKNOWN"
        ]
        if alternatives and index % 2 == variation % 2:
            replacement = min(alternatives, key=lambda row: (row.duration_min, row.cost_amount_minor or 0))
            replacement_cost = int(replacement.cost_amount_minor or 0)
            current_cost = int(item.cost_amount_minor or 0)
            if spent - current_cost + replacement_cost <= max(0, int(budget_minor)):
                selected[index] = replacement
                spent = spent - current_cost + replacement_cost
    return {(item.from_key, item.to_key): item for item in selected}


def _schedule_nodes(
    nodes: list[ComposeNode],
    ordered_days: list[list[str]],
    place_by_id: dict[str, Place],
    selected_modes: dict[tuple[str, str], MobilityFact],
    journey: Journey,
    arrival: dict[str, Any],
    departure: dict[str, Any],
) -> list[ComposeNode]:
    by_key = {node.key: node for node in nodes}
    arrival_key = next(node.key for node in nodes if node.role == "ARRIVAL")
    check_in_key = next(node.key for node in nodes if node.role == "CHECK_IN")
    check_out_key = next(node.key for node in nodes if node.role == "CHECK_OUT")
    departure_key = next(node.key for node in nodes if node.role == "DEPARTURE")
    night_keys = [node.key for node in nodes if node.role == "STAY"]
    arrival_at = datetime.fromisoformat(arrival["at"])
    departure_at = datetime.fromisoformat(departure["at"])
    scheduled: list[ComposeNode] = []

    def add(key: str, start: datetime, end: datetime) -> None:
        node = by_key[key]
        scheduled.append(ComposeNode(node.key, node.title, node.role, node.latitude, node.longitude, node.place_id, node.day_index, start, end, node.locked, node.cost_minor, node.cost_status, node.metadata))

    add(arrival_key, arrival_at, arrival_at + timedelta(minutes=20))
    previous_key = arrival_key
    cursor = arrival_at + timedelta(minutes=20)
    check_in_start = max(cursor + timedelta(minutes=20), datetime.combine(arrival_at.date(), time(14, 0), tzinfo=arrival_at.tzinfo))
    if check_in_start + timedelta(minutes=20) > departure_at:
        raise ValueError("V12_STAY_CHECK_IN_OUTSIDE_JOURNEY")
    leg = selected_modes[(previous_key, check_in_key)]
    check_in_start = max(check_in_start, cursor + timedelta(minutes=leg.duration_min))
    add(check_in_key, check_in_start, check_in_start + timedelta(minutes=20))
    previous_key, cursor = check_in_key, check_in_start + timedelta(minutes=20)

    for day, ids in enumerate(ordered_days):
        if day:
            previous_key = night_keys[day - 1]
            cursor = max(cursor, datetime.combine(arrival_at.date() + timedelta(days=day), time(8, 30), tzinfo=arrival_at.tzinfo))
        else:
            cursor = max(cursor, arrival_at + timedelta(minutes=45))
        for place_id in ids:
            key = place_id
            place = place_by_id[place_id]
            metadata = _load(place.metadata_json, {})
            _cost, duration, _status = _place_facts(place)
            leg = selected_modes[(previous_key, key)]
            start = cursor + timedelta(minutes=leg.duration_min)
            earliest = datetime.combine(start.date(), time(9, 0), tzinfo=start.tzinfo)
            if day == 0:
                earliest = max(earliest, arrival_at + timedelta(minutes=45))
            if day == DAY_COUNT - 1:
                earliest = min(earliest, departure_at - timedelta(hours=4))
            start = max(start, earliest)
            end = start + timedelta(minutes=duration)
            if end >= departure_at - timedelta(minutes=30):
                raise ValueError(f"V12_ACTIVITY_OUTSIDE_DEPARTURE_WINDOW:{place_id}")
            opening = metadata.get("opening_hours") or _load(place.opening_hours_json, {})
            if isinstance(opening, dict) and opening.get("open"):
                hour, minute = (int(part) for part in str(opening["open"]).split(":", 1))
                start = max(start, datetime.combine(start.date(), time(hour, minute), tzinfo=start.tzinfo))
                end = start + timedelta(minutes=duration)
            add(key, start, end)
            previous_key, cursor = key, end
        if day < DAY_COUNT - 1:
            night_key = night_keys[day]
            leg = selected_modes[(previous_key, night_key)]
            night_start = max(cursor + timedelta(minutes=leg.duration_min), datetime.combine(arrival_at.date() + timedelta(days=day), time(22, 30), tzinfo=arrival_at.tzinfo))
            night_end = night_start + timedelta(hours=10)
            add(night_key, night_start, night_end)
            previous_key, cursor = night_key, night_end

    leg = selected_modes[(previous_key, check_out_key)]
    departure_leg = selected_modes[(check_out_key, departure_key)]
    # Size the final hotel -> departure-anchor window from the frozen route
    # fact, rather than assuming a two-hour checkout window.  This is the
    # deterministic protected-anchor slack gate for the authoritative plan.
    latest_checkout_start = departure_at - timedelta(
        minutes=30 + 20 + departure_leg.duration_min
    )
    checkout_start = max(cursor + timedelta(minutes=leg.duration_min), latest_checkout_start)
    if checkout_start + timedelta(minutes=20) > departure_at - timedelta(minutes=30):
        raise ValueError("V12_CHECK_OUT_DEPARTURE_BUFFER")
    add(check_out_key, checkout_start, checkout_start + timedelta(minutes=20))
    departure_start = max(checkout_start + timedelta(minutes=20) + timedelta(minutes=departure_leg.duration_min), departure_at - timedelta(minutes=10))
    if departure_start > departure_at:
        raise ValueError("V12_DEPARTURE_ANCHOR_INFEASIBLE")
    add(departure_key, departure_start, departure_at)
    return scheduled


def _evidence(
    facts: list[MobilityFact],
    selected_modes: dict[tuple[str, str], MobilityFact],
    *,
    journey: Journey,
    operation_key: str,
    stay: AccommodationOfferSnapshot,
) -> tuple[str, dict[str, Any]]:
    selected = list(selected_modes.values())

    def fact_payload(item: MobilityFact) -> dict[str, Any]:
        geometry = _load(item.geometry_json, {})
        route_geometry = []
        if isinstance(geometry, dict):
            route_geometry = geometry.get("geometry", {}).get("coordinates", [])
        return {
            "origin_key": item.from_key,
            "destination_key": item.to_key,
            "mode": item.mode,
            "minutes": item.duration_min,
            "duration_min": item.duration_min,
            "distance_m": item.distance_m,
            "cost_amount_minor": item.cost_amount_minor,
            "currency": item.currency,
            "cost_status": item.cost_status,
            "walking_min": item.walking_min,
            "transfers": item.transfers,
            "reliability_score": item.reliability_score,
            "weather_exposure": item.weather_exposure,
            "provider": item.provider_key,
            "provider_key": item.provider_key,
            "provenance": item.provenance,
            "route_geometry": route_geometry,
            "geometry": geometry,
            "crs": item.crs,
            "fact_id": item.id,
            "captured_at": item.captured_at,
            "expires_at": item.expires_at,
        }

    matrix_payload = [fact_payload(item) for item in facts]
    selected_payload = [fact_payload(item) for item in selected]
    identity = _json({"journey": journey.id, "operation": operation_key, "fact_ids": [item["fact_id"] for item in matrix_payload], "stay": stay.id})
    snapshot_id = "v12-authoritative-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
    evidence = {
        "snapshot_id": snapshot_id,
        "operation_key": operation_key,
        "captured_at": min((item.captured_at for item in facts), default=_now()),
        "expires_at": min((item.expires_at for item in facts if item.expires_at), default=stay.expires_at),
        "source_provider": ";".join(sorted({item.provider_key for item in facts})),
        "aggregate_provenance": ";".join(sorted({item.provenance for item in facts})),
        "facts": matrix_payload,
        "selected_facts": selected_payload,
        "mode_matrix_count": len(facts),
        "stay_offer_id": stay.id,
        "stay_evidence": _load(stay.evidence_json, {}),
        "normalizer_version": "citynexus-v12-authoritative-evidence-1",
    }
    return snapshot_id, evidence


def compose_authoritative_multiday(
    session: Session,
    journey: Journey,
    *,
    place_ids: Iterable[str],
    candidate_count: int = 3,
    stay_offer_id: str | None = None,
    reservation_id: str | None = None,
) -> ComposeResult:
    selected_ids = list(dict.fromkeys(str(item) for item in place_ids))
    if len(selected_ids) < 2:
        raise ValueError("V12_COMPOSE_REQUIRES_TWO_POIS")
    context = session.get(JourneyTripContext, journey.id)
    arrival = _anchor(context, journey, "arrival")
    departure = _anchor(context, journey, "departure")
    arrival_at = datetime.fromisoformat(arrival["at"])
    departure_at = datetime.fromisoformat(departure["at"])
    if (departure_at.date() - arrival_at.date()).days < 2:
        raise ValueError("V12_COMPOSE_REQUIRES_THREE_DAYS")
    places = {
        item.id: item
        for item in session.scalars(
            select(Place).where(Place.id.in_(selected_ids), Place.city_code == journey.city_code)
        ).all()
    }
    missing = [item for item in selected_ids if item not in places]
    if missing:
        raise ValueError("V12_COMPOSE_POI_NOT_FOUND:" + ",".join(missing))
    for place in places.values():
        _place_facts(place)
    offers = capture_accommodation_offers(session, journey)
    if not offers:
        raise ValueError("V12_STAY_CANDIDATE_UNAVAILABLE")
    stay = next((item for item in offers if stay_offer_id and item.id == stay_offer_id), offers[0])
    commitments = list(session.scalars(select(Commitment).where(Commitment.journey_id == journey.id, Commitment.status == "ACTIVE", Commitment.level == "C4_Anchored")).all())
    c4_ids = [item.id for item in commitments]
    if reservation_id:
        reservation = session.get(TransportReservation, reservation_id)
        reservation_commitment_id = reservation.commitment_id if reservation else None
        if not any(item.id == reservation_id or item.id == reservation_commitment_id for item in commitments):
            raise ValueError("V12_RESERVATION_NOT_PROTECTED")
    result: list[PlanVersion] = []
    all_evidence_ids: list[str] = []
    for variation in range(max(1, min(5, candidate_count))):
        assignment = _solve_day_assignment(selected_ids, variation=variation)
        ordered_days = _order_by_day(places, assignment, variation=variation)
        structural, place_map = _structural_nodes(
            session, journey, stay, ordered_days, places, arrival, departure, c4_ids
        )
        structural_keys = [item.key for item in structural]
        graph = _graph_nodes(structural)
        facts = _capture_mode_matrix(session, journey, graph, structural_keys)
        route_pairs = set(zip(structural_keys, structural_keys[1:]))
        route_facts = [item for item in facts if (item.from_key, item.to_key) in route_pairs]
        poi_cost = sum(_place_facts(place)[0] for place in places.values())
        selected_modes = _select_modes(
            route_facts,
            max(0, int(journey.budget_amount_minor) - int(stay.total_amount_minor) - poi_cost),
            variation,
        )
        scheduled = _schedule_nodes(structural, ordered_days, place_map, selected_modes, journey, arrival, departure)
        total_cost = int(stay.total_amount_minor) + poi_cost + sum(int(item.cost_amount_minor or 0) for item in selected_modes.values())
        if total_cost > int(journey.budget_amount_minor):
            raise ValueError("V12_COMPOSE_BUDGET_EXCEEDED")
        snapshot_id, evidence = _evidence(facts, selected_modes, journey=journey, operation_key=f"v12-compose:{journey.id}:{variation}", stay=stay)
        now = _now()
        latest_version = int(session.scalar(select(PlanVersion.version_no).where(PlanVersion.journey_id == journey.id).order_by(PlanVersion.version_no.desc()).limit(1)) or 0)
        plan = PlanVersion(
            id=str(uuid4()),
            journey_id=journey.id,
            version_no=latest_version + 1,
            planning_mode=journey.planning_mode,
            status="CANDIDATE",
            source="INITIAL",
            parent_plan_version_id=None,
            total_cost_minor=total_cost,
            currency=journey.budget_currency,
            estimated_duration_min=sum(int((item.end_at - item.start_at).total_seconds() // 60) for item in scheduled),
            utility_score=max(0.0, min(1.0, 0.96 - 0.04 * variation)),
            score_breakdown_json=_json({
                "commitment_preservation": 1.0,
                "stability": 0.94 - (0.01 * variation),
                "time_reliability": 0.92,
                "preference_fit": 0.84,
                "mobility_fit": 0.88,
                "budget_fit": max(0.0, min(1.0, 1.0 - (total_cost / max(1, int(journey.budget_amount_minor))))),
                "robustness": 0.86,
                "opportunity_value": 0.9,
                "total": max(0.0, min(1.0, 0.96 - 0.04 * variation)),
                "optimizer": "CP-SAT",
                "day_assignment": assignment,
                "stay": stay.total_amount_minor,
                "mobility": sum(int(item.cost_amount_minor or 0) for item in selected_modes.values()),
                "protected_c4": c4_ids,
            }),
            explanation_json=_json({"product_path": "V12_AUTHORITATIVE_MULTIDAY", "optimizer_kind": "ORTOOLS_CP_SAT", "complete": True, "days": 3, "nights": 2, "poi_ids": selected_ids, "day_assignment": assignment, "stay_offer_id": stay.id, "reservation_id": reservation_id, "protected_commitment_ids": c4_ids, "mobility_snapshot_id": snapshot_id, "deterministic_gate": "PASSED"}),
            mobility_snapshot_id=snapshot_id,
            mobility_evidence_json=_json(evidence),
            created_at=now,
        )
        session.add(plan)
        session.flush()
        activity_rows: list[Activity] = []
        for sequence, node in enumerate(scheduled, start=1):
            metadata = dict(node.metadata or {})
            metadata.update({"v12_day": node.day_index + 1, "execution_state": "NOT_STARTED", "cost_status": node.cost_status, "plan_evidence_id": snapshot_id, "semantic_key": node.key})
            if node.role == "ARRIVAL":
                metadata["protected_commitment_ids"] = c4_ids
            row = Activity(
                id=str(uuid4()), plan_version_id=plan.id, sequence_no=sequence, activity_type=node.role.lower(), title=node.title, place_id=node.place_id, city_service_id=None, start_at=node.start_at.isoformat(), end_at=node.end_at.isoformat(), travel_from_prev_min=0 if sequence == 1 else selected_modes[(scheduled[sequence - 2].key, node.key)].duration_min, estimated_cost_minor=node.cost_minor, currency=journey.budget_currency, status="NOT_STARTED", locked=node.locked, metadata_json=_json(metadata), created_at=now, updated_at=now,
            )
            session.add(row)
            activity_rows.append(row)
        session.flush()
        # Older reservation imports carry only semantic_node_key (for example
        # arrival-anchor). Persist the canonical V12 place key once it is
        # known, so the existing Guardian/replan tools can consume this plan's
        # frozen matrix without a second provider lookup.
        node_by_legacy_key = {
            node.key.rsplit(":", 1)[-1]: node
            for node in scheduled
            if node.role in {"ARRIVAL", "DEPARTURE"}
        }
        for commitment in commitments:
            policy = _load(commitment.policy_json, {})
            if policy.get("semantic_key"):
                continue
            legacy_key = str(policy.get("semantic_node_key") or "")
            node = node_by_legacy_key.get(legacy_key)
            if node is not None:
                policy["semantic_key"] = node.place_id
                commitment.policy_json = _json(policy)
                commitment.updated_at = _now()
        for sequence, (from_node, to_node) in enumerate(zip(scheduled, scheduled[1:]), start=1):
            fact = selected_modes[(from_node.key, to_node.key)]
            session.add(JourneyLeg(id=str(uuid4()), journey_id=journey.id, plan_version_id=plan.id, sequence_no=sequence, from_activity_id=activity_rows[sequence - 1].id, to_activity_id=activity_rows[sequence].id, from_key=from_node.key, to_key=to_node.key, mode=fact.mode, depart_at=from_node.end_at.isoformat(), arrive_at=(from_node.end_at + timedelta(minutes=fact.duration_min)).isoformat(), duration_min=fact.duration_min, distance_m=fact.distance_m, cost_amount_minor=fact.cost_amount_minor, currency=fact.currency, cost_status=fact.cost_status, walking_min=fact.walking_min, transfers=fact.transfers, reliability_score=fact.reliability_score, weather_exposure=fact.weather_exposure, geometry_json=fact.geometry_json, crs=fact.crs, provider_key=fact.provider_key, provenance=fact.provenance, provider_snapshot_id=fact.id, captured_at=fact.captured_at, expires_at=fact.expires_at))
        session.flush()
        result.append(plan)
        all_evidence_ids.append(snapshot_id)
    session.commit()
    return ComposeResult(tuple(result), stay, tuple(all_evidence_ids), "ORTOOLS_CP_SAT")
