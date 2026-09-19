"""Authoritative deterministic feasibility gate for MVP plan candidates.

The gate is deliberately independent of FastAPI route handlers.  It accepts
snapshots of a Journey, its active constraints, the current mock catalog and
the current mock mobility provider so the exact same check can be reused by
initial planning, plan selection and the later WP06 replanning flow.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Any, Iterable, Mapping, Sequence

from app.integrations.mock.providers import MockMobilityProvider
from app.replanning.reference_replanner import Activity as ReferenceActivity
from app.replanning.reference_replanner import Candidate as ReferenceCandidate
from app.replanning.reference_replanner import Commitment, validate_candidate


@dataclass(frozen=True)
class FeasibilityActivity:
    """The activity facts needed by the deterministic gate."""

    key: str
    start_at: datetime
    end_at: datetime
    cost_minor: int
    place_id: str | None = None
    city_service_id: str | None = None
    currency: str | None = None
    travel_from_prev_min: int = 0
    locked: bool = False


@dataclass(frozen=True)
class FeasibilityContext:
    """A read-only planning context captured immediately before a gate run."""

    journey_id: str
    city_code: str
    journey_start: datetime
    journey_end: datetime
    budget_amount_minor: int
    budget_currency: str
    constraints: tuple[Any, ...]
    places: Mapping[str, Any]
    services: Mapping[str, Any]
    mobility_provider: Any
    plan_currency: str | None = None


@dataclass(frozen=True)
class FeasibilityResult:
    passed: bool
    failures: tuple[str, ...]
    effective_start_at: datetime
    effective_end_at: datetime
    budget_max_minor: int


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _parse_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def _parse_dt(value: Any, *, reference: datetime | None = None) -> datetime:
    if isinstance(value, datetime):
        result = value
    else:
        text = str(value)
        if reference is not None and ":" in text and "T" not in text and "-" not in text:
            hour, minute = (int(part) for part in text.split(":", 1))
            result = datetime.combine(reference.date(), time(hour, minute), reference.tzinfo)
        else:
            result = datetime.fromisoformat(text)
    if result.tzinfo is None:
        result = result.replace(tzinfo=reference.tzinfo if reference else timezone.utc)
    return result


def _minutes_from_start(value: datetime, start: datetime) -> int:
    return int((value - start).total_seconds() / 60)


def _constraint_parts(constraint: Any) -> tuple[str, str, str, dict[str, Any], bool]:
    params = _parse_json(_field(constraint, "params_json", _field(constraint, "params", {})), {})
    if not isinstance(params, dict):
        params = {}
    return (
        str(_field(constraint, "kind", "")),
        str(_field(constraint, "category", "")),
        str(_field(constraint, "rule_code", "")).upper(),
        params,
        bool(_field(constraint, "active", True)),
    )


def build_context(
    journey: Any,
    constraints: Iterable[Any],
    places: Mapping[str, Any] | Iterable[Any],
    services: Mapping[str, Any] | Iterable[Any],
    *,
    mobility_provider: Any | None = None,
    plan_currency: str | None = None,
) -> FeasibilityContext:
    """Build a planning snapshot from ORM records or plain dictionaries."""

    place_map = (
        dict(places)
        if isinstance(places, Mapping)
        else {str(_field(item, "id")): item for item in places}
    )
    service_map = (
        dict(services)
        if isinstance(services, Mapping)
        else {str(_field(item, "id")): item for item in services}
    )
    return FeasibilityContext(
        journey_id=str(_field(journey, "id")),
        city_code=str(_field(journey, "city_code")),
        journey_start=_parse_dt(_field(journey, "start_at")),
        journey_end=_parse_dt(_field(journey, "end_at")),
        budget_amount_minor=int(_field(journey, "budget_amount_minor", 0)),
        budget_currency=str(_field(journey, "budget_currency", "")),
        plan_currency=plan_currency.upper() if plan_currency else None,
        constraints=tuple(constraints),
        places=place_map,
        services=service_map,
        mobility_provider=mobility_provider or MockMobilityProvider(),
    )


def activity_from_record(item: Any) -> FeasibilityActivity:
    """Adapt an ORM Activity (or compatible mapping) into gate facts."""

    # A persisted Activity UUID is an implementation detail of one
    # PlanVersion.  Feasibility (and especially locked commitments) must use
    # the stable semantic location identity so generation and revalidation
    # evaluate the same candidate.  Services are handled the same way; only
    # activities without a location fall back to their own id/key.
    place_id = _field(item, "place_id")
    city_service_id = _field(item, "city_service_id")
    semantic_key = place_id or city_service_id or _field(item, "activity_key")
    if semantic_key is None:
        semantic_key = _field(item, "id")
    return FeasibilityActivity(
        key=str(semantic_key),
        start_at=_parse_dt(_field(item, "start_at")),
        end_at=_parse_dt(_field(item, "end_at")),
        cost_minor=int(_field(item, "estimated_cost_minor", _field(item, "cost_minor", 0))),
        place_id=place_id,
        city_service_id=city_service_id,
        currency=(str(_field(item, "currency")) if _field(item, "currency") is not None else None),
        travel_from_prev_min=int(_field(item, "travel_from_prev_min", 0)),
        locked=bool(_field(item, "locked", False)),
    )


def _daily_minutes(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value)
    if "T" in text:
        text = text.split("T", 1)[1]
    text = text.split("+", 1)[0].split("-", 1)[0]
    pieces = text.split(":")
    if len(pieces) < 2:
        return None
    try:
        hour, minute = int(pieces[0]), int(pieces[1])
    except ValueError:
        return None
    if hour == 24 and minute == 0:
        return 24 * 60
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    return hour * 60 + minute


def _within_open_interval(
    start_at: datetime, end_at: datetime, interval: Mapping[str, Any]
) -> bool:
    open_min = _daily_minutes(interval.get("open", interval.get("first_service")))
    close_min = _daily_minutes(interval.get("close", interval.get("last_service")))
    if open_min is None or close_min is None:
        return True
    start_min = start_at.hour * 60 + start_at.minute + start_at.second / 60
    end_min = end_at.hour * 60 + end_at.minute + end_at.second / 60
    if close_min >= open_min:
        return start_min >= open_min and end_min <= close_min
    # Overnight intervals are supported without introducing a second date
    # interpretation into the fixture contract.
    return start_min >= open_min or end_min <= close_min


def _location_key(activity: FeasibilityActivity) -> str | None:
    return activity.place_id or activity.city_service_id or None


def _active_hard_constraints(
    context: FeasibilityContext,
) -> list[tuple[str, str, str, dict[str, Any]]]:
    return [
        (kind, category, code, params)
        for constraint in context.constraints
        for kind, category, code, params, active in [_constraint_parts(constraint)]
        if active and kind.upper() == "HARD"
    ]


def _locked_commitments(
    hard_constraints: Sequence[tuple[str, str, str, dict[str, Any]]],
    *,
    journey_start: datetime,
) -> list[Commitment]:
    """Normalize every lock to semantic identity + minutes from journey start.

    The contract accepts an ISO datetime (``start_at``) or a time-only value
    (``time``).  Both are converted exactly once to the reference replanner's
    relative-minute basis.  ``start_min`` is retained as an explicit relative
    form for framework-independent callers; ambiguous minute-of-day integers
    are intentionally not inferred.
    """

    commitments: list[Commitment] = []
    for _, _, code, params in hard_constraints:
        if code != "LOCKED_COMMITMENT":
            continue
        activity_key = (
            params.get("place_id")
            or params.get("service_id")
            or params.get("semantic_ref")
            or params.get("activity_key")
        )
        start_value = params.get("start_at") or params.get("time")
        if activity_key is None or (start_value is None and params.get("start_min") is None):
            raise ValueError("LOCKED_COMMITMENT requires an activity and start time")
        if params.get("start_min") is not None:
            try:
                start = int(params["start_min"])
            except (TypeError, ValueError):
                raise ValueError("LOCKED_COMMITMENT relative start time is invalid") from None
        else:
            try:
                start = _minutes_from_start(
                    _parse_dt(start_value, reference=journey_start), journey_start
                )
            except (TypeError, ValueError, OverflowError):
                raise ValueError("LOCKED_COMMITMENT start time is invalid") from None
        commitments.append(Commitment(str(activity_key), "LOCKED", start))
    return commitments


def evaluate_feasibility(
    context: FeasibilityContext,
    activities: Sequence[FeasibilityActivity],
) -> FeasibilityResult:
    """Run every authoritative deterministic MVP feasibility invariant.

    The function has no persistence side effects.  Callers must evaluate it
    before scoring or adding a PlanVersion and must use the same function again
    immediately before selecting an existing candidate.
    """

    failures: list[str] = []
    provider = context.mobility_provider
    provider_key = getattr(provider, "provider_key", None)
    provider_is_frozen = bool(getattr(provider, "is_frozen_snapshot", False))
    if provider_key != "mock-mobility" and not provider_is_frozen:
        failures.append("NON_DETERMINISTIC_MOBILITY_PROVIDER")

    hard_constraints = _active_hard_constraints(context)
    effective_start = context.journey_start
    effective_end = context.journey_end
    budget_max = context.budget_amount_minor
    blocked_places: set[str] = set()
    blocked_services: set[str] = set()
    required_places: set[str] = set()

    for _, category, code, params in hard_constraints:
        if code == "BUDGET_MAX":
            raw_amount = params.get("amount_minor")
            try:
                amount = int(raw_amount)
            except (TypeError, ValueError):
                failures.append("INVALID_BUDGET_MAX")
                continue
            if amount < 0:
                failures.append("INVALID_BUDGET_MAX")
            else:
                budget_max = min(budget_max, amount)
            currency = params.get("currency")
            if currency and str(currency).upper() != context.budget_currency.upper():
                failures.append("BUDGET_CURRENCY_MISMATCH")
        elif code == "JOURNEY_END_BY":
            raw_end = params.get("time") or params.get("end_at")
            try:
                end_by = _parse_dt(raw_end, reference=context.journey_start)
            except (TypeError, ValueError):
                failures.append("INVALID_JOURNEY_END_BY")
            else:
                effective_end = min(effective_end, end_by)
        elif code == "JOURNEY_START_AT":
            raw_start = params.get("time") or params.get("start_at")
            try:
                start_at = _parse_dt(raw_start, reference=context.journey_start)
            except (TypeError, ValueError):
                failures.append("INVALID_JOURNEY_START_AT")
            else:
                effective_start = max(effective_start, start_at)
        elif code in {"PLACE_UNAVAILABLE", "PLACE_CLOSED"}:
            value = params.get("place_id") or params.get("place_ids")
            if isinstance(value, list):
                blocked_places.update(str(item) for item in value)
            elif value is not None:
                blocked_places.add(str(value))
        elif code in {"SERVICE_UNAVAILABLE", "SERVICE_CLOSED"}:
            value = params.get("service_id") or params.get("service_ids")
            if isinstance(value, list):
                blocked_services.update(str(item) for item in value)
            elif value is not None:
                blocked_services.add(str(value))
        elif code == "REQUIRE_PLACE":
            value = params.get("place_id") or params.get("place_ids")
            if isinstance(value, list):
                required_places.update(str(item) for item in value)
            elif value is not None:
                required_places.add(str(value))
        elif code not in {"LOCKED_COMMITMENT"}:
            # A hard rule that the gate cannot interpret must never be bypassed
            # by scoring or persistence.
            failures.append(f"UNSUPPORTED_HARD_CONSTRAINT:{code or category}")

    if effective_end < effective_start:
        failures.append("JOURNEY_WINDOW_INVALID")

    ordered = sorted(activities, key=lambda item: (item.start_at, item.end_at, item.key))
    if not ordered:
        failures.append("NO_ACTIVITIES")
    if any(item.cost_minor < 0 for item in ordered):
        failures.append("INVALID_ACTIVITY_COST")
    # A PLANNED Journey must not carry a selected plan whose activities are
    # denominated in another currency.  This check intentionally lives in the
    # shared deterministic gate so generation, selection, and mutation
    # revalidation apply the same invariant even without a HARD BUDGET_MAX rule.
    expected_currency = context.budget_currency.upper()
    if context.plan_currency is not None and context.plan_currency != expected_currency:
        failures.append("PLAN_CURRENCY_MISMATCH")
    for item in ordered:
        if item.currency is not None and item.currency.upper() != expected_currency:
            failures.append(f"ACTIVITY_CURRENCY_MISMATCH:{item.key}")
    if any(item.end_at <= item.start_at for item in ordered):
        failures.append("INVALID_ACTIVITY_WINDOW")
    if any(previous.end_at > current.start_at for previous, current in zip(ordered, ordered[1:])):
        failures.append("ACTIVITY_OVERLAP")
    reference_activities = tuple(
        ReferenceActivity(
            # Prefer the semantic location identity even when a caller built
            # FeasibilityActivity with a transient display key.
            key=_location_key(item) or item.key,
            start_min=_minutes_from_start(item.start_at, context.journey_start),
            end_min=_minutes_from_start(item.end_at, context.journey_start),
            cost_minor=item.cost_minor,
            available=True,
        )
        for item in ordered
    )
    try:
        locked_commitments = _locked_commitments(
            hard_constraints, journey_start=context.journey_start
        )
    except ValueError:
        failures.append("INVALID_LOCKED_COMMITMENT")
        locked_commitments = []
    reference_result = validate_candidate(
        ReferenceCandidate(f"{context.journey_id}:feasibility", reference_activities, {}),
        journey_start_min=_minutes_from_start(effective_start, context.journey_start),
        journey_end_min=_minutes_from_start(effective_end, context.journey_start),
        budget_max_minor=budget_max,
        locked_commitments=locked_commitments,
    )
    failures.extend(reference_result.failures)

    if any(
        item.start_at < effective_start or item.end_at > effective_end for item in ordered
    ) and any(code == "JOURNEY_END_BY" for _, _, code, _ in hard_constraints):
        failures.append("JOURNEY_END_BY_EXCEEDED")
    if required_places and not required_places.issubset(
        {item.place_id for item in ordered if item.place_id is not None}
    ):
        failures.append("REQUIRED_PLACE_MISSING")

    for item in ordered:
        if not item.place_id and not item.city_service_id:
            failures.append(f"LOCATION_MISSING:{item.key}")
        if item.place_id:
            place = context.places.get(str(item.place_id))
            if place is None:
                failures.append(f"PLACE_UNAVAILABLE:{item.place_id}")
                continue
            if str(_field(place, "city_code", context.city_code)) != context.city_code:
                failures.append(f"PLACE_CITY_MISMATCH:{item.place_id}")
            if item.place_id in blocked_places:
                failures.append(f"PLACE_UNAVAILABLE:{item.place_id}")
            place_status = _field(
                place, "status", _field(place, "availability_status", "available")
            )
            place_metadata = _parse_json(_field(place, "metadata_json", {}), {})
            if str(place_status).lower() not in {"available", "open", "ready"} or (
                isinstance(place_metadata, dict) and place_metadata.get("available") is False
            ):
                failures.append(f"PLACE_UNAVAILABLE:{item.place_id}")
            opening = _parse_json(
                _field(place, "opening_hours_json", _field(place, "opening_hours", {})), {}
            )
            if not isinstance(opening, dict) or not opening:
                failures.append(f"PLACE_AVAILABILITY_UNKNOWN:{item.place_id}")
            elif not _within_open_interval(item.start_at, item.end_at, opening):
                failures.append(f"PLACE_CLOSED:{item.place_id}")
        if item.city_service_id:
            service = context.services.get(str(item.city_service_id))
            if service is None:
                failures.append(f"SERVICE_UNAVAILABLE:{item.city_service_id}")
                continue
            if str(_field(service, "city_code", context.city_code)) != context.city_code:
                failures.append(f"SERVICE_CITY_MISMATCH:{item.city_service_id}")
            if item.city_service_id in blocked_services:
                failures.append(f"SERVICE_UNAVAILABLE:{item.city_service_id}")
            availability = _parse_json(
                _field(service, "availability_json", _field(service, "availability", {})), {}
            )
            if not isinstance(availability, dict) or not availability:
                failures.append(f"SERVICE_AVAILABILITY_UNKNOWN:{item.city_service_id}")
            else:
                status = str(availability.get("status", "available")).lower()
                if status not in {"available", "open", "ready"}:
                    failures.append(f"SERVICE_UNAVAILABLE:{item.city_service_id}")
                elif not _within_open_interval(item.start_at, item.end_at, availability):
                    failures.append(f"SERVICE_CLOSED:{item.city_service_id}")

    if provider_key == "mock-mobility" or provider_is_frozen:
        for previous, current in zip(ordered, ordered[1:]):
            origin = _location_key(previous)
            destination = _location_key(current)
            if not origin or not destination:
                failures.append("MOBILITY_CONTEXT_MISSING")
                continue
            try:
                travel_minutes = int(provider.estimate_minutes(origin, destination))
            except (KeyError, TypeError, ValueError):
                failures.append(f"MOBILITY_DATA_UNAVAILABLE:{origin}|{destination}")
                continue
            if travel_minutes < 0:
                failures.append(f"MOBILITY_DATA_INVALID:{origin}|{destination}")
            elif previous.end_at + timedelta(minutes=travel_minutes) > current.start_at:
                failures.append(f"INSUFFICIENT_TRAVEL_GAP:{origin}|{destination}")

    return FeasibilityResult(
        passed=not failures,
        failures=tuple(sorted(set(failures))),
        effective_start_at=effective_start,
        effective_end_at=effective_end,
        budget_max_minor=budget_max,
    )


def check_records(
    journey: Any,
    constraints: Iterable[Any],
    places: Mapping[str, Any] | Iterable[Any],
    services: Mapping[str, Any] | Iterable[Any],
    activities: Sequence[Any],
    *,
    mobility_provider: Any | None = None,
) -> FeasibilityResult:
    """Convenience adapter for route handlers and future WP06 callers."""

    context = build_context(
        journey,
        constraints,
        places,
        services,
        mobility_provider=mobility_provider,
    )
    return evaluate_feasibility(context, [activity_from_record(item) for item in activities])
