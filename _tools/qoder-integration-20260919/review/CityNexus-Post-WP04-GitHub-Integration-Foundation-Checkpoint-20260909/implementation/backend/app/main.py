from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.commerce.idempotency import IdempotencyConflict
from app.commerce.order_pricing import OrderLineRequest, OrderPricingError
from app.commerce.service_impl import (
    CommerceConflict,
    load_catalog,
    service_id_for_activity,
)
from app.commerce.service_impl import (
    cancel_booking as commerce_cancel_booking,
)
from app.commerce.service_impl import (
    create_booking as commerce_create_booking,
)
from app.commerce.service_impl import (
    create_order as commerce_create_order,
)
from app.commerce.service_impl import (
    create_transaction as commerce_create_transaction,
)
from app.commerce.service_impl import (
    get_booking_slots as commerce_get_booking_slots,
)
from app.commerce.strengths_generated import SOURCE_COMMITMENT_STRENGTHS
from app.commerce.validators import CommerceValidationError
from app.core.audit import record_audit
from app.db.models import (
    Activity,
    AuditLog,
    CityService,
    Journey,
    JourneyConstraint,
    PaymentTransaction,
    Place,
    PlanVersion,
    Preference,
    Traveler,
)
from app.db.models import (
    Booking as BookingModel,
)
from app.db.models import (
    Commitment as CommitmentModel,
)
from app.db.models import (
    Event as EventModel,
)
from app.db.models import (
    JourneyTwin as JourneyTwinModel,
)
from app.db.models import (
    Order as OrderModel,
)
from app.db.models import (
    ReplanProposal as ReplanProposalModel,
)
from app.db.session import SessionLocal, ensure_schema, get_session
from app.integrations.ai.fallback import DeterministicFallbackAIProvider
from app.integrations.mock.commerce_providers import MockBookingProvider, MockPaymentProvider
from app.integrations.mock.providers import MockMobilityProvider
from app.intelligence.reason_codes import ReasonCode, VerifiedExplanationFacts
from app.intelligence.replan_diff import PlanActivitySnapshot, diff_plans
from app.replanning.feasibility import activity_from_record, build_context, evaluate_feasibility
from app.schemas import (
    Booking as BookingSchema,
)
from app.schemas import (
    BookingCreate,
    ConstraintInput,
    EventCreate,
    GeneratePlansRequest,
    JourneyCreate,
    JourneyPatch,
    OrderCreate,
    PreferenceInput,
    TransactionCreate,
    TravelerCreate,
)
from app.schemas import (
    BookingSlot as BookingSlotSchema,
)
from app.schemas import (
    Commitment as CommitmentSchema,
)
from app.schemas import (
    Event as EventSchema,
)
from app.schemas import (
    JourneyTwin as JourneyTwinSchema,
)
from app.schemas import (
    Order as OrderSchema,
)
from app.schemas import (
    ReplanProposal as ReplanProposalSchema,
)
from app.schemas import (
    Transaction as TransactionSchema,
)
from app.services import (
    constraint_schema,
    generate_plans,
    journey_schema,
    place_schema,
    plan_schema,
    preference_schema,
    seed_demo,
    service_schema,
    traveler_schema,
    validate_selected_plan_feasibility,
)

ensure_schema()
app = FastAPI(title="CityNexus MVP API", version="0.1.0")


def create_app() -> FastAPI:
    """Return the configured application for ASGI servers and tests."""
    return app


def trace_id() -> str:
    return str(uuid4())


def error(code: str, message: str, *, status: int, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {"code": code, "message": message, "trace_id": trace_id(), "details": details}
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    safe_errors = [
        {"loc": list(item.get("loc", ())), "msg": item.get("msg"), "type": item.get("type")}
        for item in exc.errors()
    ]
    return error(
        "VALIDATION_ERROR", "Request validation failed", status=422, details={"errors": safe_errors}
    )


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    code = {404: "NOT_FOUND", 409: "CONFLICT", 422: "VALIDATION_ERROR"}.get(
        exc.status_code, "REQUEST_ERROR"
    )
    return error(code, detail, status=exc.status_code)


def require(session: Session, model: type, identifier: str, label: str):
    item = session.get(model, identifier)
    if item is None:
        raise HTTPException(404, f"{label} {identifier} was not found")
    return item


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    with SessionLocal() as session:
        session.execute(select(Traveler).limit(1))
    return {"status": "ok", "database": "ok", "ai": "disabled"}


@app.post("/api/v1/demo/reset")
def demo_reset(session: Session = Depends(get_session)) -> dict[str, str]:
    summary = seed_demo(session)
    return {"status": "reset", **summary}


@app.post("/api/v1/travelers", status_code=201)
def create_traveler(payload: TravelerCreate, session: Session = Depends(get_session)):
    identifier = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    traveler = Traveler(
        id=identifier,
        display_name=payload.display_name,
        email=payload.email,
        locale=payload.locale,
        timezone=payload.timezone,
        created_at=now,
        updated_at=now,
    )
    session.add(traveler)
    session.commit()
    record_audit(session, action="traveler.created", entity_type="Traveler", entity_id=traveler.id)
    session.commit()
    return traveler_schema(traveler)


@app.get("/api/v1/travelers/{traveler_id}")
def get_traveler(traveler_id: UUID, session: Session = Depends(get_session)):
    return traveler_schema(require(session, Traveler, str(traveler_id), "Traveler"))


@app.get("/api/v1/travelers/{traveler_id}/preferences")
def list_preferences(traveler_id: UUID, session: Session = Depends(get_session)):
    require(session, Traveler, str(traveler_id), "Traveler")
    items = session.scalars(
        select(Preference)
        .where(Preference.traveler_id == str(traveler_id))
        .order_by(Preference.category, Preference.preference_key)
    ).all()
    return [preference_schema(item) for item in items]


@app.put("/api/v1/travelers/{traveler_id}/preferences")
def replace_preferences(
    traveler_id: UUID, payload: list[PreferenceInput], session: Session = Depends(get_session)
):
    traveler = require(session, Traveler, str(traveler_id), "Traveler")
    keys = [(item.category, item.key) for item in payload]
    seen: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    for key in keys:
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    if duplicates:
        raise HTTPException(422, f"Duplicate preferences are not allowed: {sorted(duplicates)}")
    existing = session.scalars(
        select(Preference)
        .where(Preference.traveler_id == traveler.id)
        .order_by(Preference.category, Preference.preference_key)
    ).all()
    before = [preference_schema(item).model_dump(mode="json") for item in existing]
    session.query(Preference).filter(Preference.traveler_id == traveler.id).delete(
        synchronize_session=False
    )
    now = datetime.now(timezone.utc).isoformat()
    for item in payload:
        session.add(
            Preference(
                id=str(uuid4()),
                traveler_id=traveler.id,
                category=item.category,
                preference_key=item.key,
                value_json=json.dumps(item.value, ensure_ascii=False),
                weight=item.weight,
                source="user",
                created_at=now,
                updated_at=now,
            )
        )
    updated = session.scalars(
        select(Preference)
        .where(Preference.traveler_id == traveler.id)
        .order_by(Preference.category, Preference.preference_key)
    ).all()
    after = [preference_schema(item).model_dump(mode="json") for item in updated]
    record_audit(
        session,
        action="preferences.replaced",
        entity_type="Preference",
        entity_id=traveler.id,
        after={"traveler_id": traveler.id, "preferences": after},
        before={"traveler_id": traveler.id, "preferences": before},
    )
    session.commit()
    return [preference_schema(item) for item in updated]


@app.post("/api/v1/journeys", status_code=201)
def create_journey(payload: JourneyCreate, session: Session = Depends(get_session)):
    require(session, Traveler, str(payload.traveler_id), "Traveler")
    now = datetime.now(timezone.utc).isoformat()
    journey = Journey(
        id=str(uuid4()),
        traveler_id=str(payload.traveler_id),
        title=payload.title,
        city_code=payload.city_code,
        timezone=payload.timezone,
        start_at=payload.start_at.isoformat(),
        end_at=payload.end_at.isoformat(),
        budget_currency=payload.budget.currency,
        budget_amount_minor=payload.budget.amount_minor,
        planning_mode=payload.planning_mode,
        status="DRAFT",
        active_plan_version_id=None,
        current_activity_id=None,
        created_at=now,
        updated_at=now,
    )
    session.add(journey)
    session.commit()
    record_audit(
        session,
        action="journey.created",
        entity_type="Journey",
        entity_id=journey.id,
        journey_id=journey.id,
    )
    session.commit()
    return journey_schema(journey)


@app.get("/api/v1/journeys/{journey_id}")
def get_journey(journey_id: UUID, session: Session = Depends(get_session)):
    return journey_schema(require(session, Journey, str(journey_id), "Journey"))


@app.patch("/api/v1/journeys/{journey_id}")
def update_journey(
    journey_id: UUID, payload: JourneyPatch, session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    before = journey_schema(journey).model_dump(mode="json")
    start = payload.start_at or datetime.fromisoformat(journey.start_at)
    end = payload.end_at or datetime.fromisoformat(journey.end_at)
    if end <= start:
        raise HTTPException(422, "end_at must be after start_at")
    overrides = {}
    if payload.start_at is not None:
        overrides["start_at"] = payload.start_at.isoformat()
    if payload.end_at is not None:
        overrides["end_at"] = payload.end_at.isoformat()
    if payload.budget is not None:
        overrides["budget_amount_minor"] = payload.budget.amount_minor
        overrides["budget_currency"] = payload.budget.currency
    try:
        gate = validate_selected_plan_feasibility(session, journey, journey_overrides=overrides)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if gate is not None and not gate.passed:
        failures = ", ".join(gate.failures)
        raise HTTPException(
            422, f"Journey update would make the selected plan infeasible: {failures}"
        )
    if payload.title is not None:
        journey.title = payload.title
    if payload.start_at is not None:
        journey.start_at = payload.start_at.isoformat()
    if payload.end_at is not None:
        journey.end_at = payload.end_at.isoformat()
    if payload.budget is not None:
        journey.budget_amount_minor, journey.budget_currency = (
            payload.budget.amount_minor,
            payload.budget.currency,
        )
    journey.updated_at = datetime.now(timezone.utc).isoformat()
    after = journey_schema(journey).model_dump(mode="json")
    record_audit(
        session,
        action="journey.updated",
        entity_type="Journey",
        entity_id=journey.id,
        journey_id=journey.id,
        before=before,
        after=after,
    )
    session.commit()
    return journey_schema(journey)


@app.get("/api/v1/journeys/{journey_id}/constraints")
def list_constraints(journey_id: UUID, session: Session = Depends(get_session)):
    require(session, Journey, str(journey_id), "Journey")
    items = session.scalars(
        select(JourneyConstraint)
        .where(JourneyConstraint.journey_id == str(journey_id))
        .order_by(JourneyConstraint.created_at)
    ).all()
    return [constraint_schema(item) for item in items]


@app.post("/api/v1/journeys/{journey_id}/constraints", status_code=201)
def add_constraint(
    journey_id: UUID, payload: ConstraintInput, session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    now = datetime.now(timezone.utc).isoformat()
    item = JourneyConstraint(
        id=str(uuid4()),
        journey_id=str(journey_id),
        kind=payload.kind,
        category=payload.category,
        rule_code=payload.rule_code,
        params_json=json.dumps(payload.params, ensure_ascii=False),
        weight=payload.weight,
        active=True,
        created_at=now,
        updated_at=now,
    )
    if payload.kind == "HARD":
        try:
            gate = validate_selected_plan_feasibility(
                session,
                journey,
                additional_constraints=[item],
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if gate is not None and not gate.passed:
            failures = ", ".join(gate.failures)
            raise HTTPException(
                422, f"Constraint would make the selected plan infeasible: {failures}"
            )
    session.add(item)
    session.commit()
    record_audit(
        session,
        action="constraint.created",
        entity_type="Constraint",
        entity_id=item.id,
        journey_id=item.journey_id,
    )
    session.commit()
    return constraint_schema(item)


@app.delete("/api/v1/journeys/{journey_id}/constraints/{constraint_id}", status_code=204)
def delete_constraint(
    journey_id: UUID, constraint_id: UUID, session: Session = Depends(get_session)
):
    item = session.scalar(
        select(JourneyConstraint).where(
            JourneyConstraint.id == str(constraint_id),
            JourneyConstraint.journey_id == str(journey_id),
        )
    )
    if item is None:
        raise HTTPException(404, f"Constraint {constraint_id} was not found")
    before = constraint_schema(item).model_dump(mode="json")
    session.delete(item)
    record_audit(
        session,
        action="constraint.deleted",
        entity_type="Constraint",
        entity_id=item.id,
        journey_id=item.journey_id,
        before=before,
    )
    session.commit()


@app.get("/api/v1/places")
def search_places(
    city_code: str = Query(...),
    category: str | None = None,
    q: str | None = None,
    session: Session = Depends(get_session),
):
    items = session.scalars(
        select(Place).where(Place.city_code == city_code).order_by(Place.id)
    ).all()
    if category:
        items = [item for item in items if item.category.lower() == category.lower()]
    if q:
        needle = q.lower()
        items = [
            item
            for item in items
            if needle in item.name.lower() or needle in item.tags_json.lower()
        ]
    return [place_schema(item) for item in items]


@app.get("/api/v1/city-services")
def search_services(
    city_code: str = Query(...),
    service_type: str | None = None,
    session: Session = Depends(get_session),
):
    items = session.scalars(
        select(CityService).where(CityService.city_code == city_code).order_by(CityService.id)
    ).all()
    if service_type:
        items = [item for item in items if item.service_type.lower() == service_type.lower()]
    return [service_schema(item) for item in items]


@app.post("/api/v1/journeys/{journey_id}/plans/generate", status_code=201)
def generate_journey_plans(
    journey_id: UUID,
    payload: GeneratePlansRequest | None = None,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    request = payload or GeneratePlansRequest()
    planning_mode = request.planning_mode or journey.planning_mode
    try:
        plans = generate_plans(session, journey, planning_mode, request.candidate_count)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return [plan_schema(session, plan) for plan in plans]


@app.get("/api/v1/journeys/{journey_id}/plans")
def list_plans(journey_id: UUID, session: Session = Depends(get_session)):
    require(session, Journey, str(journey_id), "Journey")
    items = session.scalars(
        select(PlanVersion)
        .where(PlanVersion.journey_id == str(journey_id))
        .order_by(PlanVersion.version_no)
    ).all()
    return [plan_schema(session, item) for item in items]


@app.get("/api/v1/plans/{plan_version_id}")
def get_plan(plan_version_id: UUID, session: Session = Depends(get_session)):
    return plan_schema(session, require(session, PlanVersion, str(plan_version_id), "PlanVersion"))


@app.post("/api/v1/journeys/{journey_id}/plans/{plan_version_id}/select")
def select_plan(journey_id: UUID, plan_version_id: UUID, session: Session = Depends(get_session)):
    journey = session.scalar(
        select(Journey)
        .where(Journey.id == str(journey_id))
        .execution_options(populate_existing=True)
    )
    if journey is None:
        raise HTTPException(404, f"Journey {journey_id} was not found")
    plan = session.scalar(
        select(PlanVersion).where(
            PlanVersion.id == str(plan_version_id), PlanVersion.journey_id == journey.id
        )
    )
    if plan is None:
        raise HTTPException(404, f"PlanVersion {plan_version_id} was not found")
    # Selecting the already-current selected plan is a safe idempotent read.
    # Do this before the normal transition/audit path so retries do not emit a
    # second plan.selected audit event.
    if plan.status == "SELECTED" and journey.active_plan_version_id == plan.id:
        return journey_schema(journey)
    if plan.status not in {"CANDIDATE", "SELECTED"}:
        raise HTTPException(422, "Only a candidate plan can be selected")
    constraints = session.scalars(
        select(JourneyConstraint).where(
            JourneyConstraint.journey_id == journey.id,
            JourneyConstraint.active.is_(True),
        )
    ).all()
    places = {
        place.id: place
        for place in session.scalars(
            select(Place).where(Place.city_code == journey.city_code)
        ).all()
    }
    services = {
        service.id: service
        for service in session.scalars(
            select(CityService).where(CityService.city_code == journey.city_code)
        ).all()
    }
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan.id).order_by(Activity.sequence_no)
    ).all()
    gate = evaluate_feasibility(
        build_context(
            journey,
            constraints,
            places,
            services,
            mobility_provider=MockMobilityProvider(),
            plan_currency=plan.currency,
        ),
        [activity_from_record(item) for item in activities],
    )
    if not gate.passed:
        failures = ", ".join(gate.failures)
        raise HTTPException(422, f"PlanVersion {plan.id} is infeasible: {failures}")

    current = session.scalar(
        select(PlanVersion).where(
            PlanVersion.journey_id == journey.id,
            PlanVersion.status == "SELECTED",
            PlanVersion.id != plan.id,
        )
    )
    before = {
        "journey": journey_schema(journey).model_dump(mode="json"),
        "plan_status": plan.status,
        "previous_selected_plan_id": current.id if current else None,
    }
    if current:
        current.status = "REJECTED"
    plan.status = "SELECTED"
    journey.status = "PLANNED"
    journey.active_plan_version_id = plan.id
    journey.updated_at = datetime.now(timezone.utc).isoformat()
    after = {
        "journey": journey_schema(journey).model_dump(mode="json"),
        "plan_status": plan.status,
        "previous_selected_plan_id": current.id if current else None,
    }
    record_audit(
        session,
        action="plan.selected",
        entity_type="PlanVersion",
        entity_id=plan.id,
        journey_id=journey.id,
        before=before,
        after=after,
    )
    session.commit()
    return journey_schema(journey)


# === WP04 commerce adapter routes ===


def _json_object(value: str | None, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not value:
        return default or {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return default or {}
    return parsed if isinstance(parsed, dict) else (default or {})


def _booking_payload(item: BookingModel) -> dict[str, Any]:
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "activity_id": item.activity_id,
        "commitment_id": item.commitment_id,
        "provider_key": item.provider_key,
        "external_ref": item.external_ref,
        "status": item.status,
        "amount": {"amount_minor": item.amount_minor, "currency": item.currency},
        "cancellation_policy": _json_object(item.cancellation_policy_json),
    }


def _order_payload(item: OrderModel) -> dict[str, Any]:
    raw_items = json.loads(item.items_json or "[]")
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "activity_id": item.activity_id,
        "commitment_id": item.commitment_id,
        "provider_key": item.provider_key,
        "external_ref": item.external_ref,
        "status": item.status,
        "amount": {"amount_minor": item.amount_minor, "currency": item.currency},
        "items": raw_items,
    }


def _transaction_payload(item: PaymentTransaction) -> dict[str, Any]:
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "booking_id": item.booking_id,
        "order_id": item.order_id,
        "provider_key": item.provider_key,
        "transaction_type": item.transaction_type,
        "status": item.status,
        "amount": {"amount_minor": item.amount_minor, "currency": item.currency},
        "external_ref": item.external_ref,
    }


def _commitment_payload(item: CommitmentModel) -> dict[str, Any]:
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "activity_id": item.activity_id,
        "kind": item.kind,
        "level": item.level,
        "status": item.status,
        "monetary_value": {
            "amount_minor": item.monetary_value_minor,
            "currency": item.currency,
        },
        "external_ref": item.external_ref,
        "policy": _json_object(item.policy_json),
    }


def _mock_booking_provider(provider_key: str) -> tuple[MockBookingProvider, bool]:
    if provider_key not in {"mock-booking", "mock-booking-fail"}:
        raise CommerceValidationError("only the supplied mock-booking provider is enabled in WP04")
    return MockBookingProvider(), provider_key.endswith("-fail")


def _mock_payment_provider(provider_key: str) -> tuple[MockPaymentProvider, bool]:
    if provider_key not in {"mock-payment", "mock-payment-fail"}:
        raise CommerceValidationError("only the supplied mock-payment provider is enabled in WP04")
    return MockPaymentProvider(), provider_key.endswith("-fail")


def _assert_selected_plan_feasible(session: Session, journey: Journey, _plan: PlanVersion):
    gate = validate_selected_plan_feasibility(session, journey)
    if gate is not None and not gate.passed:
        failures = ", ".join(gate.failures)
        raise CommerceValidationError(f"selected plan is no longer feasible: {failures}")
    return gate


def _twin_snapshot(session: Session, journey: Journey) -> dict[str, Any]:
    """Build a reproducible read projection from Journey/Plan/Commitment facts."""
    active_plan_id = journey.active_plan_version_id
    current_id = journey.current_activity_id
    latest_event = session.scalar(
        select(EventModel)
        .where(EventModel.journey_id == journey.id)
        .order_by(EventModel.detected_at.desc(), EventModel.id.desc())
    )
    commitments = session.scalars(
        select(CommitmentModel)
        .where(CommitmentModel.journey_id == journey.id, CommitmentModel.status == "ACTIVE")
        .order_by(CommitmentModel.created_at, CommitmentModel.id)
    ).all()
    snapshot_at = datetime.now(timezone.utc).isoformat()
    twin = session.get(JourneyTwinModel, journey.id)
    if twin is None:
        twin = JourneyTwinModel(journey_id=journey.id)
        session.add(twin)
    twin.active_plan_version_id = active_plan_id
    twin.current_activity_id = current_id
    twin.latest_event_id = latest_event.id if latest_event else None
    twin.projection_status = "READY"
    twin.snapshot_at = snapshot_at
    twin.updated_at = snapshot_at
    twin.context_json = json.dumps({"journey_status": journey.status}, sort_keys=True)
    twin.upcoming_commitments_json = json.dumps(
        [_commitment_payload(item) for item in commitments], sort_keys=True
    )
    session.flush()
    return {
        "journey_id": journey.id,
        "active_plan_version_id": active_plan_id,
        "current_activity_id": current_id,
        "latest_event_id": latest_event.id if latest_event else None,
        "projection_status": "READY",
        "snapshot_at": snapshot_at,
        "upcoming_commitments": [_commitment_payload(item) for item in commitments],
        "context": {"journey_status": journey.status},
    }


@app.post("/api/v1/journeys/{journey_id}/start", response_model=JourneyTwinSchema)
def start_journey(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    if journey.status == "ACTIVE":
        return _twin_snapshot(session, journey)
    if journey.status != "PLANNED" or not journey.active_plan_version_id:
        raise HTTPException(409, "journey must be PLANNED with a selected plan")
    plan = session.get(PlanVersion, journey.active_plan_version_id)
    if plan is None or plan.status != "SELECTED":
        raise HTTPException(409, "selected plan is missing or inconsistent")
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan.id).order_by(Activity.sequence_no)
    ).all()
    journey.status = "ACTIVE"
    plan.status = "ACTIVE"
    if activities:
        journey.current_activity_id = activities[0].id
        activities[0].status = "ACTIVE"
    journey.updated_at = datetime.now(timezone.utc).isoformat()
    record_audit(
        session,
        action="journey.started",
        entity_type="Journey",
        entity_id=journey.id,
        journey_id=journey.id,
        after={"status": journey.status, "current_activity_id": journey.current_activity_id},
    )
    session.commit()
    return _twin_snapshot(session, journey)


@app.post(
    "/api/v1/journeys/{journey_id}/activities/{activity_id}/complete",
    response_model=JourneyTwinSchema,
)
def complete_activity(journey_id: UUID, activity_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    if journey.status != "ACTIVE" or not journey.active_plan_version_id:
        raise HTTPException(409, "journey must be ACTIVE")
    activity = session.get(Activity, str(activity_id))
    if activity is None or activity.plan_version_id != journey.active_plan_version_id:
        raise HTTPException(409, "activity is not on the active plan")
    if journey.current_activity_id != activity.id:
        raise HTTPException(409, "activity is not the current activity")
    activity.status = "COMPLETED"
    next_activity = session.scalar(
        select(Activity)
        .where(
            Activity.plan_version_id == journey.active_plan_version_id,
            Activity.sequence_no > activity.sequence_no,
            Activity.status.not_in(("COMPLETED", "SKIPPED", "CANCELLED")),
        )
        .order_by(Activity.sequence_no)
    )
    if next_activity is None:
        journey.current_activity_id = None
        journey.status = "COMPLETED"
        plan = session.get(PlanVersion, journey.active_plan_version_id)
        if plan is not None:
            plan.status = "ACTIVE"
    else:
        next_activity.status = "ACTIVE"
        journey.current_activity_id = next_activity.id
    journey.updated_at = datetime.now(timezone.utc).isoformat()
    record_audit(
        session,
        action="activity.completed",
        entity_type="Activity",
        entity_id=activity.id,
        journey_id=journey.id,
        after={"status": activity.status, "next_activity_id": journey.current_activity_id},
    )
    session.commit()
    return _twin_snapshot(session, journey)


@app.get("/api/v1/journeys/{journey_id}/twin", response_model=JourneyTwinSchema)
def get_journey_twin(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    result = _twin_snapshot(session, journey)
    session.commit()
    return result


@app.post("/api/v1/journeys/{journey_id}/events", response_model=EventSchema, status_code=201)
def create_journey_event(
    journey_id: UUID, payload: EventCreate, session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    if payload.affected_activity_id is not None:
        activity = session.get(Activity, str(payload.affected_activity_id))
        if activity is None or activity.plan_version_id != journey.active_plan_version_id:
            raise HTTPException(422, "affected activity is not on the active plan")
    now = datetime.now(timezone.utc).isoformat()
    item = EventModel(
        id=str(uuid4()),
        journey_id=journey.id,
        provider_key=payload.provider_key,
        event_type=payload.event_type,
        severity=payload.severity,
        status="DETECTED",
        affected_activity_id=str(payload.affected_activity_id)
        if payload.affected_activity_id
        else None,
        occurred_at=(payload.occurred_at or datetime.now(timezone.utc)).isoformat(),
        detected_at=now,
        payload_json=json.dumps(payload.payload, sort_keys=True),
        created_at=now,
    )
    session.add(item)
    record_audit(
        session,
        action="journey.event.detected",
        entity_type="Event",
        entity_id=item.id,
        journey_id=journey.id,
        after={"event_type": item.event_type, "severity": item.severity},
    )
    session.commit()
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "provider_key": item.provider_key,
        "event_type": item.event_type,
        "severity": item.severity,
        "status": item.status,
        "affected_activity_id": item.affected_activity_id,
        "occurred_at": item.occurred_at,
        "detected_at": item.detected_at,
        "payload": json.loads(item.payload_json),
    }


@app.get("/api/v1/journeys/{journey_id}/events", response_model=list[EventSchema])
def list_journey_events(journey_id: UUID, session: Session = Depends(get_session)):
    require(session, Journey, str(journey_id), "Journey")
    items = session.scalars(
        select(EventModel)
        .where(EventModel.journey_id == str(journey_id))
        .order_by(EventModel.detected_at, EventModel.id)
    ).all()
    return [
        {
            "id": item.id,
            "journey_id": item.journey_id,
            "provider_key": item.provider_key,
            "event_type": item.event_type,
            "severity": item.severity,
            "status": item.status,
            "affected_activity_id": item.affected_activity_id,
            "occurred_at": item.occurred_at,
            "detected_at": item.detected_at,
            "payload": json.loads(item.payload_json),
        }
        for item in items
    ]


@app.get("/api/v1/journeys/{journey_id}/history")
def journey_history(journey_id: UUID, session: Session = Depends(get_session)):
    require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(AuditLog).where(AuditLog.journey_id == str(journey_id)).order_by(AuditLog.created_at)
    ).all()
    return [
        {
            "timestamp": row.created_at,
            "type": row.action,
            "summary": row.action,
            "entity_id": row.entity_id,
        }
        for row in rows
    ]


def _replan_payload(item: ReplanProposalModel) -> dict[str, Any]:
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "trigger_event_id": item.trigger_event_id,
        "base_plan_version_id": item.base_plan_version_id,
        "proposed_plan_version_id": item.proposed_plan_version_id,
        "status": item.status,
        "hard_constraints_passed": bool(item.hard_constraints_passed),
        "locked_commitments_preserved": bool(item.locked_commitments_preserved),
        "utility_score": item.utility_score,
        "score_breakdown": json.loads(item.score_breakdown_json or "{}"),
        "diff": json.loads(item.diff_json or "{}"),
        "explanation": json.loads(item.explanation_json or "{}"),
    }


@app.post(
    "/api/v1/journeys/{journey_id}/replans", response_model=ReplanProposalSchema, status_code=201
)
def generate_replan(
    journey_id: UUID, body: dict[str, Any], session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    if not journey.active_plan_version_id:
        raise HTTPException(422, "journey has no active plan")
    base = session.get(PlanVersion, journey.active_plan_version_id)
    trigger_id = body.get("trigger_event_id")
    if base is None:
        raise HTTPException(422, "active plan is missing")
    if trigger_id and (session.get(EventModel, str(trigger_id)) is None):
        raise HTTPException(422, "trigger event is not on this journey")
    source = session.scalars(
        select(Activity).where(Activity.plan_version_id == base.id).order_by(Activity.sequence_no)
    ).all()
    proposed_id = str(uuid4())
    latest_version = (
        session.scalar(
            select(PlanVersion.version_no)
            .where(PlanVersion.journey_id == journey.id)
            .order_by(PlanVersion.version_no.desc())
            .limit(1)
        )
        or 0
    )
    proposed = PlanVersion(
        id=proposed_id,
        journey_id=journey.id,
        version_no=latest_version + 1,
        planning_mode=base.planning_mode,
        status="CANDIDATE",
        source="REPLAN",
        parent_plan_version_id=base.id,
        total_cost_minor=base.total_cost_minor,
        currency=base.currency,
        estimated_duration_min=base.estimated_duration_min,
        utility_score=base.utility_score,
        score_breakdown_json=base.score_breakdown_json,
        explanation_json=json.dumps({"reason": "Deterministic mock replan"}),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(proposed)
    session.flush()
    for activity in source:
        session.add(
            Activity(
                id=str(uuid4()),
                plan_version_id=proposed.id,
                sequence_no=activity.sequence_no,
                activity_type=activity.activity_type,
                title=activity.title,
                place_id=activity.place_id,
                city_service_id=activity.city_service_id,
                start_at=activity.start_at,
                end_at=activity.end_at,
                travel_from_prev_min=activity.travel_from_prev_min,
                estimated_cost_minor=activity.estimated_cost_minor,
                currency=activity.currency,
                status=activity.status,
                locked=activity.locked,
                metadata_json=activity.metadata_json,
                created_at=activity.created_at,
                updated_at=activity.updated_at,
            )
        )
    session.flush()
    copied = session.scalars(
        select(Activity)
        .where(Activity.plan_version_id == proposed.id)
        .order_by(Activity.sequence_no)
    ).all()
    old = [
        PlanActivitySnapshot(
            a.place_id or a.id,
            datetime.fromisoformat(a.start_at),
            datetime.fromisoformat(a.end_at),
            a.estimated_cost_minor,
            a.locked,
        )
        for a in source
    ]
    new = [
        PlanActivitySnapshot(
            a.place_id or a.id,
            datetime.fromisoformat(a.start_at),
            datetime.fromisoformat(a.end_at),
            a.estimated_cost_minor,
            a.locked,
        )
        for a in copied
    ]
    d = diff_plans(old, new)
    now = datetime.now(timezone.utc).isoformat()
    item = ReplanProposalModel(
        id=str(uuid4()),
        journey_id=journey.id,
        trigger_event_id=str(trigger_id) if trigger_id else None,
        base_plan_version_id=base.id,
        proposed_plan_version_id=proposed.id,
        status="GENERATED",
        hard_constraints_passed=True,
        locked_commitments_preserved=True,
        utility_score=float(base.utility_score or 0),
        score_breakdown_json=base.score_breakdown_json or "{}",
        diff_json=json.dumps(
            {
                "kept": d.kept,
                "moved": [m.__dict__ for m in d.moved],
                "removed": d.removed,
                "added": d.added,
                "cost_delta_minor": d.cost_delta_minor,
            },
            default=str,
        ),
        explanation_json=json.dumps(
            {
                "summary": "Deterministic mock replan proposal",
                "reasons": ["provider-independent deterministic candidate"],
                "source": "DETERMINISTIC",
            }
        ),
        created_at=now,
    )
    session.add(item)
    record_audit(
        session,
        action="replan.generated",
        entity_type="ReplanProposal",
        entity_id=item.id,
        journey_id=journey.id,
        after={"status": item.status},
    )
    session.commit()
    return _replan_payload(item)


@app.get("/api/v1/journeys/{journey_id}/replans", response_model=list[ReplanProposalSchema])
def list_replans(journey_id: UUID, session: Session = Depends(get_session)):
    require(session, Journey, str(journey_id), "Journey")
    return [
        _replan_payload(p)
        for p in session.scalars(
            select(ReplanProposalModel)
            .where(ReplanProposalModel.journey_id == str(journey_id))
            .order_by(ReplanProposalModel.created_at)
        ).all()
    ]


@app.get("/api/v1/replans/{proposal_id}", response_model=ReplanProposalSchema)
def get_replan(proposal_id: UUID, session: Session = Depends(get_session)):
    return _replan_payload(
        require(session, ReplanProposalModel, str(proposal_id), "Replan proposal")
    )


@app.post("/api/v1/replans/{proposal_id}/accept")
def accept_replan(proposal_id: UUID, session: Session = Depends(get_session)):
    proposal = require(session, ReplanProposalModel, str(proposal_id), "Replan proposal")
    if proposal.status != "GENERATED":
        raise HTTPException(409, "replan proposal is no longer actionable")
    journey = require(session, Journey, proposal.journey_id, "Journey")
    if journey.active_plan_version_id != proposal.base_plan_version_id:
        raise HTTPException(409, "replan base plan is stale")
    base = session.get(PlanVersion, proposal.base_plan_version_id)
    proposed = session.get(PlanVersion, proposal.proposed_plan_version_id)
    if base is None or proposed is None:
        raise HTTPException(409, "replan plan is missing")
    base.status = "SUPERSEDED"
    proposed.status = "ACTIVE"
    journey.active_plan_version_id = proposed.id
    proposal.status = "ACCEPTED"
    proposal.decided_at = datetime.now(timezone.utc).isoformat()
    record_audit(
        session,
        action="replan.accepted",
        entity_type="ReplanProposal",
        entity_id=proposal.id,
        journey_id=journey.id,
        after={"status": proposal.status},
    )
    twin = _twin_snapshot(session, journey)
    session.commit()
    return {
        "journey": journey_schema(journey).model_dump(mode="json"),
        "proposal": _replan_payload(proposal),
        "twin": twin,
    }


@app.post("/api/v1/replans/{proposal_id}/reject", response_model=ReplanProposalSchema)
def reject_replan(proposal_id: UUID, session: Session = Depends(get_session)):
    proposal = require(session, ReplanProposalModel, str(proposal_id), "Replan proposal")
    if proposal.status == "GENERATED":
        proposal.status = "REJECTED"
        proposal.decided_at = datetime.now(timezone.utc).isoformat()
        session.commit()
    return _replan_payload(proposal)


@app.post("/api/v1/journeys/{journey_id}/copilot/messages")
async def copilot_message(
    journey_id: UUID, body: dict[str, Any], session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    message = str(body.get("message") or "").strip()
    if not message:
        raise HTTPException(422, "message is required")
    twin = _twin_snapshot(session, journey)
    facts = VerifiedExplanationFacts(
        reason_codes=(ReasonCode.COMMITMENT_PRESERVED,) if twin["upcoming_commitments"] else (),
        evidence={
            "journey_status": journey.status,
            "current_activity_id": twin["current_activity_id"],
        },
        locale="zh" if journey.timezone.startswith("Asia/") else "en",
    )
    result = await DeterministicFallbackAIProvider().explain(facts, task=message)
    session.commit()
    return {
        "message": result.text,
        "mode": "FALLBACK",
        "verified_context_used": True,
        "recommendations": [],
    }


@app.get("/api/v1/city-services/{service_id}/booking-slots", response_model=list[BookingSlotSchema])
def booking_slots(
    service_id: str,
    start_at: datetime,
    end_at: datetime,
    session: Session = Depends(get_session),
):
    if end_at <= start_at:
        raise HTTPException(422, "end_at must be after start_at")
    if service_id not in load_catalog().get("booking_services", {}):
        raise HTTPException(404, f"CityService {service_id} was not found")
    try:
        provider, _ = _mock_booking_provider("mock-booking")
        slots = commerce_get_booking_slots(
            session,
            service_id=service_id,
            start_at=start_at.isoformat(),
            end_at=end_at.isoformat(),
            provider=provider,
        )
        session.commit()
        return [
            {
                "start_at": slot.start_at,
                "end_at": slot.end_at,
                "provider_key": slot.provider_key,
                "provider_slot_ref": slot.provider_slot_ref,
            }
            for slot in slots
        ]
    except CommerceConflict as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    except (CommerceValidationError, ValueError) as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/journeys/{journey_id}/bookings", response_model=BookingSchema, status_code=201)
def create_journey_booking(
    journey_id: UUID,
    payload: BookingCreate,
    x_mock_failure: str | None = Header(default=None, alias="X-Mock-Failure"),
    session: Session = Depends(get_session),
):
    try:
        provider, provider_failure = _mock_booking_provider(payload.provider_key)
        item = commerce_create_booking(
            session,
            journey_id=str(journey_id),
            activity_id=str(payload.activity_id),
            provider=provider,
            source_strength_codes=SOURCE_COMMITMENT_STRENGTHS,
            booking_source_type_code="booking",
            assert_selected_plan_feasible=_assert_selected_plan_feasible,
            force_failure=provider_failure
            or payload.force_failure
            or payload.failure_token is not None
            or x_mock_failure == "FORCE_BOOKING_FAIL",
        )
        session.commit()
        return _booking_payload(item)
    except CommerceConflict as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    except (CommerceValidationError, ValueError) as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/v1/bookings/{booking_id}", response_model=BookingSchema)
def get_booking(booking_id: UUID, session: Session = Depends(get_session)):
    item = session.get(BookingModel, str(booking_id))
    if item is None:
        raise HTTPException(404, f"Booking {booking_id} was not found")
    return _booking_payload(item)


@app.post("/api/v1/bookings/{booking_id}/cancel", response_model=BookingSchema)
def cancel_journey_booking(
    booking_id: UUID,
    x_mock_failure: str | None = Header(default=None, alias="X-Mock-Failure"),
    session: Session = Depends(get_session),
):
    item = session.get(BookingModel, str(booking_id))
    if item is None:
        raise HTTPException(404, f"Booking {booking_id} was not found")
    try:
        provider, provider_failure = _mock_booking_provider(item.provider_key)
        updated = commerce_cancel_booking(
            session,
            booking_id=item.id,
            provider=provider,
            force_failure=provider_failure or x_mock_failure == "FORCE_BOOKING_CANCEL_FAIL",
        )
        session.commit()
        return _booking_payload(updated)
    except CommerceConflict as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    except (CommerceValidationError, ValueError) as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/journeys/{journey_id}/orders", response_model=OrderSchema, status_code=201)
def create_journey_order(
    journey_id: UUID,
    payload: OrderCreate,
    session: Session = Depends(get_session),
):
    try:
        _mock_booking_provider(payload.provider_key)
        activity = session.get(Activity, str(payload.activity_id))
        if activity is None:
            raise CommerceValidationError("Activity not found")
        catalog = load_catalog()
        service_id = service_id_for_activity(session, activity, catalog, order=True)
        item = commerce_create_order(
            session,
            journey_id=str(journey_id),
            activity_id=str(payload.activity_id),
            service_id=service_id,
            items=[
                OrderLineRequest(sku=line.sku, quantity=line.quantity) for line in payload.items
            ],
            catalog=catalog,
            source_strength_codes=SOURCE_COMMITMENT_STRENGTHS,
            order_source_type_code="booking",
            provider_key=payload.provider_key,
            assert_selected_plan_feasible=_assert_selected_plan_feasible,
        )
        session.commit()
        return _order_payload(item)
    except OrderPricingError as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc
    except (CommerceValidationError, CommerceConflict, ValueError) as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc


@app.post(
    "/api/v1/journeys/{journey_id}/transactions",
    response_model=TransactionSchema,
    status_code=201,
)
def create_journey_transaction(
    journey_id: UUID,
    payload: TransactionCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_mock_failure: str | None = Header(default=None, alias="X-Mock-Failure"),
    session: Session = Depends(get_session),
):
    if idempotency_key is None:
        raise HTTPException(422, "Idempotency-Key header is required")
    try:
        provider, provider_failure = _mock_payment_provider(payload.provider_key)
        item = commerce_create_transaction(
            session,
            journey_id=str(journey_id),
            booking_id=str(payload.booking_id) if payload.booking_id else None,
            order_id=str(payload.order_id) if payload.order_id else None,
            transaction_type=payload.transaction_type,
            requested_amount_minor=payload.amount.amount_minor,
            requested_currency=payload.amount.currency,
            provider=provider,
            idempotency_key=idempotency_key,
            source_strength_codes=SOURCE_COMMITMENT_STRENGTHS,
            force_failure=provider_failure
            or payload.force_failure
            or payload.failure_token is not None
            or x_mock_failure == "FORCE_PAYMENT_FAIL",
        )
        session.commit()
        return _transaction_payload(item)
    except (IdempotencyConflict, CommerceConflict) as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    except (CommerceValidationError, ValueError) as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/v1/transactions/{transaction_id}", response_model=TransactionSchema)
def get_transaction(transaction_id: UUID, session: Session = Depends(get_session)):
    item = session.get(PaymentTransaction, str(transaction_id))
    if item is None:
        raise HTTPException(404, f"Transaction {transaction_id} was not found")
    return _transaction_payload(item)


@app.get("/api/v1/commitments/{commitment_id}", response_model=CommitmentSchema)
def get_commitment(commitment_id: UUID, session: Session = Depends(get_session)):
    item = session.get(CommitmentModel, str(commitment_id))
    if item is None:
        raise HTTPException(404, f"Commitment {commitment_id} was not found")
    return _commitment_payload(item)
