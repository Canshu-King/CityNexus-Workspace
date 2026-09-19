from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.commerce.idempotency import IdempotencyConflict, canonical_request_signature
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
from app.commerce.validators import CommerceValidationError, validate_idempotency_key
from app.core.audit import record_audit
from app.core.config import settings
from app.db.models import (
    Activity,
    AuditLog,
    CityService,
    IdempotencyKey,
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
from app.integrations.ai.litellm_provider import LiteLLMExplanationProvider
from app.integrations.ai.resilient import ResilientAIExplanationService
from app.integrations.mock.commerce_providers import MockBookingProvider, MockPaymentProvider
from app.integrations.mock.providers import MockMobilityProvider
from app.intelligence.feasibility_envelope import FeasibilityEnvelope
from app.intelligence.opportunity_window import build_window
from app.intelligence.reason_codes import ReasonCode, VerifiedExplanationFacts
from app.intelligence.replan_diff import PlanActivitySnapshot, diff_plans
from app.replanning.candidate_evidence import verified_interest_preference_fit
from app.replanning.feasibility import activity_from_record, build_context, evaluate_feasibility
from app.replanning.mock_replan_engine import partition_execution, rank_closure_replacements
from app.replanning.opportunity_window_family import (
    WindowReplacementInput,
    evaluate_window_replacement,
)
from app.replanning.verified_scoring import score_replan_candidate
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
    ReplanGenerateRequest,
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
    validate_plan_feasibility,
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


def _envelope_payload(
    journey: Journey,
    activities: list[Activity],
    *,
    preserved_commitment_count: int,
    next_commitment_buffer_min: int | None = None,
    degraded_providers: tuple[str, ...] = (),
) -> dict[str, Any]:
    last_end = max(
        (datetime.fromisoformat(item.end_at) for item in activities),
        default=datetime.fromisoformat(journey.start_at),
    )
    envelope = FeasibilityEnvelope(
        next_commitment_buffer_min=next_commitment_buffer_min,
        journey_end_slack_min=int(
            (datetime.fromisoformat(journey.end_at) - last_end).total_seconds() // 60
        ),
        budget_remaining_minor=journey.budget_amount_minor
        - sum(item.estimated_cost_minor for item in activities),
        preserved_commitment_count=preserved_commitment_count,
        degraded_providers=degraded_providers,
        risk_reason_codes=(ReasonCode.PROVIDER_DEGRADED.value,) if degraded_providers else (),
    )
    return {
        "next_commitment_buffer_min": envelope.next_commitment_buffer_min,
        "journey_end_slack_min": envelope.journey_end_slack_min,
        "budget_remaining_minor": envelope.budget_remaining_minor,
        "preserved_commitment_count": envelope.preserved_commitment_count,
        "degraded_providers": list(envelope.degraded_providers),
        "risk_reason_codes": list(envelope.risk_reason_codes),
        "robust": envelope.robust,
    }


def _twin_snapshot(
    session: Session,
    journey: Journey,
    *,
    projection_now: datetime | None = None,
) -> dict[str, Any]:
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
    activities = (
        session.scalars(
            select(Activity)
            .where(Activity.plan_version_id == active_plan_id)
            .order_by(Activity.sequence_no)
        ).all()
        if active_plan_id
        else []
    )
    current = next((item for item in activities if item.id == current_id), None)
    derived_now = projection_now or (
        datetime.fromisoformat(current.start_at)
        if current is not None
        else datetime.fromisoformat(journey.start_at)
    )
    active_plan_activity_by_id = {item.id: item for item in activities}
    projected_commitments: list[CommitmentModel] = []
    for commitment in commitments:
        linked_activity = (
            active_plan_activity_by_id.get(commitment.activity_id)
            if commitment.activity_id
            else None
        )
        if linked_activity is not None and linked_activity.status in {
            "COMPLETED",
            "SKIPPED",
            "CANCELLED",
        }:
            continue
        policy = json.loads(commitment.policy_json or "{}")
        scheduled = policy.get("scheduled_start_at")
        if scheduled:
            try:
                scheduled_at = datetime.fromisoformat(str(scheduled))
            except ValueError:
                scheduled_at = None
            if scheduled_at is not None and scheduled_at < derived_now:
                continue
        projected_commitments.append(commitment)

    active_c4: list[tuple[datetime, dict[str, Any]]] = []
    for commitment in projected_commitments:
        if commitment.level != "C4_Anchored":
            continue
        policy = json.loads(commitment.policy_json or "{}")
        scheduled = policy.get("scheduled_start_at")
        if scheduled:
            start = datetime.fromisoformat(str(scheduled))
            if start >= derived_now:
                active_c4.append((start, policy))
    active_c4.sort(key=lambda item: (item[0], str(item[1].get("semantic_key", ""))))
    next_buffer: int | None = None
    opportunity: dict[str, Any] | None = None
    if active_c4:
        next_start, policy = active_c4[0]
        current_key = current.place_id or current.city_service_id if current is not None else None
        target_key = str(policy.get("semantic_key") or "")
        travel_min = (
            MockMobilityProvider().estimate_minutes(current_key, target_key)
            if current_key and target_key and current_key != target_key
            else 0
        )
        window = build_window(
            now=derived_now,
            next_commitment_start=next_start,
            travel_to_commitment_min=travel_min,
            safety_buffer_min=15,
        )
        next_buffer = window.available_minutes
        opportunity = {
            "opens_at": window.opens_at.isoformat(),
            "must_depart_by": window.must_depart_by.isoformat(),
            "available_minutes": window.available_minutes,
            "next_commitment_start": window.next_commitment_start.isoformat(),
        }
    degraded_items: set[str] = set()
    unresolved_events = session.scalars(
        select(EventModel).where(
            EventModel.journey_id == journey.id,
            EventModel.status.in_(("DETECTED", "ACKNOWLEDGED")),
        )
    ).all()
    for event_row in unresolved_events:
        try:
            event_payload = json.loads(event_row.payload_json or "{}")
        except json.JSONDecodeError:
            event_payload = {}
        degraded_items.update(
            str(item) for item in event_payload.get("degraded_providers", []) if item
        )
    degraded = tuple(sorted(degraded_items))
    envelope = _envelope_payload(
        journey,
        activities,
        preserved_commitment_count=len(active_c4),
        next_commitment_buffer_min=next_buffer,
        degraded_providers=degraded,
    )
    context = {
        "journey_status": journey.status,
        "provider_level": 1,
        "degraded_providers": list(degraded),
        "feasibility_envelope": envelope,
        "opportunity_window": opportunity,
    }
    snapshot_at = datetime.now(timezone.utc).isoformat()
    projection_status = "DEGRADED" if degraded else "READY"
    twin = session.get(JourneyTwinModel, journey.id)
    if twin is None:
        twin = JourneyTwinModel(journey_id=journey.id)
        session.add(twin)
    twin.active_plan_version_id = active_plan_id
    twin.current_activity_id = current_id
    twin.latest_event_id = latest_event.id if latest_event else None
    twin.projection_status = projection_status
    twin.snapshot_at = snapshot_at
    twin.updated_at = snapshot_at
    twin.context_json = json.dumps(context, sort_keys=True)
    twin.upcoming_commitments_json = json.dumps(
        [_commitment_payload(item) for item in projected_commitments], sort_keys=True
    )
    session.flush()
    return {
        "journey_id": journey.id,
        "active_plan_version_id": active_plan_id,
        "current_activity_id": current_id,
        "latest_event_id": latest_event.id if latest_event else None,
        "projection_status": projection_status,
        "snapshot_at": snapshot_at,
        "upcoming_commitments": [_commitment_payload(item) for item in projected_commitments],
        "context": context,
    }


@app.post("/api/v1/journeys/{journey_id}/start", response_model=JourneyTwinSchema)
def start_journey(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    if journey.status == "ACTIVE":
        twin = _twin_snapshot(session, journey)
        session.commit()
        return twin
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
    twin = _twin_snapshot(session, journey)
    session.commit()
    return twin


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
    twin = _twin_snapshot(session, journey)
    session.commit()
    return twin


@app.get("/api/v1/journeys/{journey_id}/twin", response_model=JourneyTwinSchema)
def get_journey_twin(
    journey_id: UUID,
    now: datetime | None = Query(default=None),
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    result = _twin_snapshot(session, journey, projection_now=now)
    session.commit()
    return result


@app.post("/api/v1/journeys/{journey_id}/events", response_model=EventSchema, status_code=201)
def create_journey_event(
    journey_id: UUID, payload: EventCreate, session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    if payload.provenance in {"PROVIDER_VERIFIED", "SYSTEM_DERIVED"}:
        raise HTTPException(422, "trusted event provenance is assigned only by server ingestion")
    provider_key = "demo-simulator" if payload.provenance == "SIMULATED" else "user-report"
    if payload.provider_key not in {None, provider_key}:
        raise HTTPException(422, "provider_key is server-assigned for public event input")
    affected_activity = None
    if payload.affected_activity_id is not None:
        affected_activity = session.get(Activity, str(payload.affected_activity_id))
        if (
            affected_activity is None
            or affected_activity.plan_version_id != journey.active_plan_version_id
        ):
            raise HTTPException(422, "affected activity is not on the active plan")
    now = datetime.now(timezone.utc).isoformat()
    current_activity = (
        session.get(Activity, journey.current_activity_id) if journey.current_activity_id else None
    )
    deterministic_default = (
        affected_activity.start_at
        if affected_activity is not None
        else (current_activity.start_at if current_activity is not None else journey.start_at)
    )
    occurred_at = payload.occurred_at.isoformat() if payload.occurred_at else deterministic_default
    item = EventModel(
        id=str(uuid4()),
        journey_id=journey.id,
        provider_key=provider_key,
        provenance=payload.provenance,
        event_type=payload.event_type,
        severity=payload.severity,
        status="DETECTED",
        affected_activity_id=str(payload.affected_activity_id)
        if payload.affected_activity_id
        else None,
        occurred_at=occurred_at,
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
        after={
            "event_type": item.event_type,
            "severity": item.severity,
            "provenance": item.provenance,
        },
    )
    session.commit()
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "provider_key": item.provider_key,
        "provenance": item.provenance,
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
            "provenance": item.provenance,
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
    journey_id: UUID,
    body: ReplanGenerateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    if journey.status != "ACTIVE" or not journey.active_plan_version_id:
        raise HTTPException(409, "journey must be ACTIVE with an active plan")
    base = session.get(PlanVersion, journey.active_plan_version_id)
    trigger_id = str(body.trigger_event_id)
    trigger_event = None
    if base is None or base.status != "ACTIVE":
        raise HTTPException(409, "active plan is missing or inconsistent")
    trigger_event = session.get(EventModel, trigger_id)
    if trigger_event is None or trigger_event.journey_id != journey.id:
        raise HTTPException(422, "trigger event is not on this journey")
    if trigger_event.status not in {"DETECTED", "ACKNOWLEDGED"}:
        raise HTTPException(409, "trigger event is no longer actionable")
    handled = session.scalar(
        select(ReplanProposalModel.id).where(
            ReplanProposalModel.trigger_event_id == trigger_id,
            ReplanProposalModel.status == "ACCEPTED",
        )
    )
    if handled is not None:
        raise HTTPException(409, "trigger event has already been handled by an accepted replan")

    generation_idempotency_key: str | None = None
    generation_signature: str | None = None
    if idempotency_key is not None:
        try:
            header_key = validate_idempotency_key(idempotency_key)
        except CommerceValidationError as exc:
            raise HTTPException(422, str(exc)) from exc
        generation_signature = canonical_request_signature(
            {
                "journey_id": journey.id,
                "base_plan_version_id": base.id,
                "trigger_event_id": trigger_id,
                "candidate_count": body.candidate_count,
            }
        )
        generation_idempotency_key = f"replan.generate:{header_key}"
        existing_generation = session.get(IdempotencyKey, generation_idempotency_key)
        if existing_generation is not None:
            if existing_generation.request_hash != generation_signature:
                raise HTTPException(409, "same idempotency key used for a different request")
            stored = json.loads(existing_generation.response_json or "{}")
            if not stored:
                raise HTTPException(409, "replan generation idempotency record is incomplete")
            return stored

    source = session.scalars(
        select(Activity).where(Activity.plan_version_id == base.id).order_by(Activity.sequence_no)
    ).all()
    c4_rows = session.scalars(
        select(CommitmentModel).where(
            CommitmentModel.journey_id == journey.id,
            CommitmentModel.status == "ACTIVE",
            CommitmentModel.level == "C4_Anchored",
        )
    ).all()
    c4_anchors = []
    for row in c4_rows:
        policy = json.loads(row.policy_json or "{}")
        c4_anchors.append((str(policy.get("semantic_key")), str(policy.get("scheduled_start_at"))))
    partition = partition_execution(
        source,
        current_activity_id=journey.current_activity_id,
        c4_anchors=c4_anchors,
    )
    affected_place = None
    replacement_choices = []
    affected_activity_id = None
    affected_place_id = None
    delay_minutes = 0
    remove_affected = False
    payload = json.loads(trigger_event.payload_json or "{}")
    if trigger_event.event_type in {"CLOSURE", "WEATHER", "TRAFFIC_DELAY", "SCHEDULE_DELAY"}:
        affected_activity_id = trigger_event.affected_activity_id
        if affected_activity_id is None and payload.get("affected_place_id"):
            affected_place_id = str(payload["affected_place_id"])
            match = next((a for a in source if a.place_id == affected_place_id), None)
            affected_activity_id = match.id if match else None
        if affected_activity_id is None and trigger_event.event_type in {
            "TRAFFIC_DELAY",
            "SCHEDULE_DELAY",
        }:
            affected_activity_id = journey.current_activity_id
        affected = next((a for a in source if a.id == affected_activity_id), None)
        if affected is not None:
            affected_place_id = affected.place_id
            if affected.status in {"COMPLETED", "SKIPPED", "CANCELLED"}:
                raise HTTPException(409, "disruption targets an activity that is already terminal")
            if affected.locked and trigger_event.event_type in {"CLOSURE", "WEATHER"}:
                raise HTTPException(
                    422, "closed activity is protected and cannot be replaced automatically"
                )
            if trigger_event.event_type in {"CLOSURE", "WEATHER"}:
                affected_place = (
                    session.get(Place, affected.place_id) if affected.place_id else None
                )
                if affected_place is None:
                    raise HTTPException(422, "affected place is unavailable")
                places = session.scalars(
                    select(Place).where(Place.city_code == journey.city_code).order_by(Place.id)
                ).all()
                replacement_choices = list(
                    rank_closure_replacements(
                        affected_place=affected_place,
                        candidate_places=places,
                        occupied_place_ids={a.place_id for a in source if a.place_id},
                        max_duration_min=max(
                            1,
                            int(
                                (
                                    datetime.fromisoformat(affected.end_at)
                                    - datetime.fromisoformat(affected.start_at)
                                ).total_seconds()
                                // 60
                            ),
                        ),
                    )
                )
                if not replacement_choices:
                    remove_affected = True
            else:
                raw_delay = (
                    payload.get("extra_minutes", payload.get("delay_minutes", 15))
                    if trigger_event.event_type == "TRAFFIC_DELAY"
                    else payload.get("delay_minutes", payload.get("extra_minutes", 15))
                )
                delay_minutes = max(1, min(int(raw_delay), 120))
    latest_version = (
        session.scalar(
            select(PlanVersion.version_no)
            .where(PlanVersion.journey_id == journey.id)
            .order_by(PlanVersion.version_no.desc())
            .limit(1)
        )
        or 0
    )
    affected = next((item for item in source if item.id == affected_activity_id), None)
    protected_activity_ids = set(partition.c4_anchor_ids)
    mobility = MockMobilityProvider()
    effective_event_time = datetime.fromisoformat(trigger_event.occurred_at)
    if effective_event_time.tzinfo is None:
        # EventCreate permits timezone-free simulator/user input. Keep all
        # planning arithmetic on one timeline by inheriting the Journey's
        # schedule offset instead of mixing naive and aware datetimes.
        reference_time = datetime.fromisoformat(
            affected.start_at if affected is not None else journey.start_at
        )
        effective_event_time = effective_event_time.replace(tzinfo=reference_time.tzinfo)
    specs: list[tuple[str, Any | None, int, bool, dict[str, Any] | None]] = []
    if replacement_choices:
        for index, choice in enumerate(replacement_choices):
            family = "F0_SAME_SLOT_REPLACEMENT"
            window_evidence: dict[str, Any] | None = None
            if index > 0 and affected is not None:
                next_anchor = (
                    min(
                        (
                            datetime.fromisoformat(start),
                            semantic,
                        )
                        for semantic, start in c4_anchors
                        if datetime.fromisoformat(start) > effective_event_time
                    )
                    if any(
                        datetime.fromisoformat(start) > effective_event_time
                        for _, start in c4_anchors
                    )
                    else None
                )
                if next_anchor is not None:
                    candidate_place = session.get(Place, choice.place_id)
                    opening = json.loads(candidate_place.opening_hours_json or "{}")
                    date = effective_event_time.date()

                    def _at_time(
                        value: str | None,
                        *,
                        day=date,
                        tz=effective_event_time.tzinfo,
                    ) -> datetime | None:
                        if not value:
                            return None
                        hour, minute = (int(part) for part in str(value).split(":", 1))
                        return datetime.combine(
                            day,
                            datetime.min.time().replace(hour=hour, minute=minute),
                            tz,
                        )

                    previous = next(
                        (item for item in source if item.sequence_no == affected.sequence_no - 1),
                        None,
                    )
                    origin = (
                        (previous.place_id or previous.city_service_id)
                        if previous is not None
                        else None
                    )
                    inbound = mobility.estimate_minutes(origin, choice.place_id) if origin else 0
                    outbound = mobility.estimate_minutes(choice.place_id, next_anchor[1])
                    budget_remaining = journey.budget_amount_minor - (
                        sum(item.estimated_cost_minor for item in source)
                        - affected.estimated_cost_minor
                    )
                    evidence = evaluate_window_replacement(
                        now=effective_event_time,
                        next_commitment_start=next_anchor[0],
                        safety_buffer_min=15,
                        budget_remaining_minor=budget_remaining,
                        candidate=WindowReplacementInput(
                            key=choice.place_id,
                            visit_minutes=choice.duration_min,
                            inbound_travel_min=inbound,
                            outbound_travel_min=outbound,
                            cost_minor=choice.cost_minor,
                            opens_at=_at_time(opening.get("open")),
                            closes_at=_at_time(opening.get("close")),
                        ),
                    )
                    if evidence.fits:
                        family = "F3_OPPORTUNITY_WINDOW"
                        window_evidence = {
                            "window_opens_at": evidence.window_opens_at.isoformat(),
                            "next_commitment_start": evidence.next_commitment_start.isoformat(),
                            "finish_at": evidence.finish_at.isoformat()
                            if evidence.finish_at
                            else None,
                            "remaining_buffer_min": evidence.remaining_buffer_min,
                            "inbound_travel_min": inbound,
                            "outbound_travel_min": outbound,
                            "safety_buffer_min": 15,
                        }
            if index > 0 and family == "F0_SAME_SLOT_REPLACEMENT":
                family = "F0_ALTERNATE_REPLACEMENT"
            specs.append((family, choice, 0, False, window_evidence))
        if (
            affected is not None
            and affected.id not in protected_activity_ids
            and not affected.locked
        ):
            specs.append(("F1_OPTIONAL_REMOVAL", None, 0, True, None))
    elif delay_minutes:
        specs.append(("F2_SUFFIX_DELAY", None, delay_minutes, False, None))
        if (
            affected is not None
            and affected.id not in protected_activity_ids
            and not affected.locked
        ):
            specs.append(("F1_OPTIONAL_REMOVAL", None, 0, True, None))
    elif remove_affected:
        specs.append(("F1_OPTIONAL_REMOVAL", None, 0, True, None))
    else:
        specs.append(("F0_STABLE_COPY", None, 0, False, None))
    disruption_constraints: list[dict[str, Any]] = []
    if affected_place_id and trigger_event.event_type in {"CLOSURE", "WEATHER"}:
        disruption_constraints.append(
            {
                "kind": "HARD",
                "category": "availability",
                "rule_code": "PLACE_UNAVAILABLE",
                "params": {"place_id": affected_place_id},
                "active": True,
            }
        )
    c4_anchor_set = {
        (semantic, datetime.fromisoformat(start).isoformat()) for semantic, start in c4_anchors
    }

    def _diff_semantic_key(activity: Activity) -> str:
        return str(activity.place_id or activity.city_service_id or activity.id)

    def _is_protected(activity: Activity) -> bool:
        semantic = _diff_semantic_key(activity)
        start = datetime.fromisoformat(activity.start_at).isoformat()
        return bool(activity.locked) or (semantic, start) in c4_anchor_set

    old_snapshots = [
        PlanActivitySnapshot(
            _diff_semantic_key(activity),
            datetime.fromisoformat(activity.start_at),
            datetime.fromisoformat(activity.end_at),
            activity.estimated_cost_minor,
            _is_protected(activity),
        )
        for activity in source
    ]
    c4_count = len(c4_rows)
    before_envelope = _envelope_payload(journey, source, preserved_commitment_count=c4_count)
    created: list[ReplanProposalModel] = []
    failed_reasons: set[str] = set()
    traveler_preferences = session.scalars(
        select(Preference)
        .where(Preference.traveler_id == journey.traveler_id)
        .order_by(Preference.category, Preference.preference_key)
    ).all()

    for generation_rank, (
        family,
        replacement_choice,
        candidate_delay,
        candidate_remove,
        window_evidence,
    ) in enumerate(specs):
        if len(created) >= body.candidate_count:
            break
        proposed = PlanVersion(
            id=str(uuid4()),
            journey_id=journey.id,
            version_no=latest_version + len(created) + 1,
            planning_mode=base.planning_mode,
            status="CANDIDATE",
            source="REPLAN",
            parent_plan_version_id=base.id,
            total_cost_minor=0,
            currency=base.currency,
            estimated_duration_min=0,
            utility_score=None,
            score_breakdown_json=None,
            explanation_json=json.dumps({"reason": family}, sort_keys=True),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        session.add(proposed)
        session.flush()
        copied_rows: list[dict[str, Any]] = []
        for activity in source:
            if candidate_remove and activity.id == affected_activity_id:
                continue
            row = {
                "sequence_no": activity.sequence_no,
                "activity_type": activity.activity_type,
                "title": activity.title,
                "place_id": activity.place_id,
                "city_service_id": activity.city_service_id,
                "start_at": activity.start_at,
                "end_at": activity.end_at,
                "travel_from_prev_min": activity.travel_from_prev_min,
                "estimated_cost_minor": activity.estimated_cost_minor,
                "currency": activity.currency,
                "status": activity.status,
                "locked": activity.locked,
                "metadata_json": activity.metadata_json,
                "created_at": activity.created_at,
                "updated_at": activity.updated_at,
            }
            if replacement_choice is not None and activity.id == affected_activity_id:
                start_dt = datetime.fromisoformat(activity.start_at)
                if family == "F3_OPPORTUNITY_WINDOW" and window_evidence is not None:
                    # Persist the exact visit schedule proven by the
                    # OpportunityWindow evidence: window open + inbound travel.
                    start_dt = datetime.fromisoformat(
                        str(window_evidence["window_opens_at"])
                    ) + timedelta(minutes=int(window_evidence["inbound_travel_min"]))
                row.update(
                    {
                        "title": replacement_choice.title,
                        "place_id": replacement_choice.place_id,
                        "city_service_id": None,
                        "start_at": start_dt.isoformat(),
                        "end_at": (
                            start_dt + timedelta(minutes=replacement_choice.duration_min)
                        ).isoformat(),
                        "estimated_cost_minor": replacement_choice.cost_minor,
                        "locked": False,
                        "metadata_json": json.dumps(
                            {
                                "candidate_family": family,
                                "replan_reason_codes": replacement_choice.reason_codes,
                                "replaced_place_id": affected_place_id,
                            },
                            sort_keys=True,
                        ),
                    }
                )
            elif candidate_delay and affected is not None:
                if (
                    activity.sequence_no >= affected.sequence_no
                    and activity.id not in protected_activity_ids
                    and not activity.locked
                    and activity.status not in {"COMPLETED", "SKIPPED", "CANCELLED"}
                ):
                    row["start_at"] = (
                        datetime.fromisoformat(activity.start_at)
                        + timedelta(minutes=candidate_delay)
                    ).isoformat()
                    row["end_at"] = (
                        datetime.fromisoformat(activity.end_at) + timedelta(minutes=candidate_delay)
                    ).isoformat()
                    row["metadata_json"] = json.dumps(
                        {
                            "candidate_family": family,
                            "replan_reason_codes": (
                                "SCHEDULE_DELAY_ABSORBED",
                                "COMMITMENT_PRESERVED",
                            ),
                            "delay_minutes": candidate_delay,
                        },
                        sort_keys=True,
                    )
            copied_rows.append(row)

        for index, row in enumerate(copied_rows):
            if index > 0:
                previous = copied_rows[index - 1]
                origin = previous.get("place_id") or previous.get("city_service_id")
                destination = row.get("place_id") or row.get("city_service_id")
                if origin and destination:
                    row["travel_from_prev_min"] = int(
                        mobility.estimate_minutes(origin, destination)
                    )
            session.add(Activity(id=str(uuid4()), plan_version_id=proposed.id, **row))

        proposed.total_cost_minor = sum(int(row["estimated_cost_minor"]) for row in copied_rows)
        if copied_rows:
            first_start = min(datetime.fromisoformat(str(row["start_at"])) for row in copied_rows)
            last_end = max(datetime.fromisoformat(str(row["end_at"])) for row in copied_rows)
            proposed.estimated_duration_min = max(
                0, int((last_end - first_start).total_seconds() // 60)
            )
        session.flush()
        copied = session.scalars(
            select(Activity)
            .where(Activity.plan_version_id == proposed.id)
            .order_by(Activity.sequence_no)
        ).all()
        gate = validate_plan_feasibility(
            session,
            journey,
            proposed,
            additional_constraints=disruption_constraints,
            include_active_c4=True,
        )
        if not gate.passed:
            failed_reasons.update(gate.failures)
            session.execute(delete(Activity).where(Activity.plan_version_id == proposed.id))
            session.delete(proposed)
            session.flush()
            continue

        new_snapshots = [
            PlanActivitySnapshot(
                _diff_semantic_key(activity),
                datetime.fromisoformat(activity.start_at),
                datetime.fromisoformat(activity.end_at),
                activity.estimated_cost_minor,
                _is_protected(activity),
            )
            for activity in copied
        ]
        diff = diff_plans(old_snapshots, new_snapshots)
        after_envelope = _envelope_payload(journey, copied, preserved_commitment_count=c4_count)
        travel_delta = sum(activity.travel_from_prev_min for activity in copied) - sum(
            activity.travel_from_prev_min for activity in source
        )
        preference_fit = None
        opportunity_value = None
        if replacement_choice is not None:
            replacement_place = session.get(Place, replacement_choice.place_id)
            replacement_tags = set(json.loads(replacement_place.tags_json or "[]"))
            preference_fit = verified_interest_preference_fit(
                traveler_preferences, candidate_tags=replacement_tags
            )
        elif candidate_remove:
            # Removing the disrupted activity contributes no interest match for
            # that slot; this is verified absence, not an inferred LLM score.
            preference_fit = 0.0
        else:
            # Delay/stable-copy families preserve the same activities, so their
            # already-verified preference coverage is preserved rather than re-scored.
            preference_fit = 1.0
        # Opportunity value remains neutral until a candidate family is backed
        # by verified OpportunityWindow evidence. Do not infer it from duration.
        opportunity_value = (
            min(1.0, max(0.0, float(window_evidence["remaining_buffer_min"]) / 60.0))
            if window_evidence is not None
            else None
        )
        score = score_replan_candidate(
            base_activity_count=len(source),
            moved_count=len(diff.moved),
            removed_count=len(diff.removed),
            added_count=len(diff.added),
            travel_delta_min=travel_delta,
            budget_amount_minor=journey.budget_amount_minor,
            after_envelope=after_envelope,
            commitments_preserved=True,
            preference_fit=preference_fit,
            opportunity_value=opportunity_value,
        )
        proposed.utility_score = score.total
        proposed.score_breakdown_json = json.dumps(score.breakdown, sort_keys=True)
        reason_codes = ["COMMITMENT_PRESERVED", "MINIMAL_DISRUPTION"]
        if replacement_choice is not None:
            reason_codes.extend(replacement_choice.reason_codes)
        elif candidate_delay:
            reason_codes.append("SCHEDULE_DELAY_ABSORBED")
        elif candidate_remove:
            reason_codes.append("DISRUPTED_ACTIVITY_REMOVED")
        proposal = ReplanProposalModel(
            id=str(uuid4()),
            journey_id=journey.id,
            trigger_event_id=trigger_id,
            base_plan_version_id=base.id,
            proposed_plan_version_id=proposed.id,
            status="PRESENTED",
            hard_constraints_passed=True,
            locked_commitments_preserved=True,
            utility_score=score.total,
            score_breakdown_json=proposed.score_breakdown_json,
            diff_json=json.dumps(
                {
                    "candidate_family": family,
                    "kept": diff.kept,
                    "moved": [moved.__dict__ for moved in diff.moved],
                    "removed": diff.removed,
                    "added": diff.added,
                    "cost_delta_minor": diff.cost_delta_minor,
                    "travel_delta_min": travel_delta,
                    "end_time_delta_min": int(
                        (
                            (diff.new_end_at or datetime.fromisoformat(journey.start_at))
                            - (diff.old_end_at or datetime.fromisoformat(journey.start_at))
                        ).total_seconds()
                        // 60
                    ),
                    "preserved_protected": diff.preserved_protected,
                    "before_feasibility_envelope": before_envelope,
                    "after_feasibility_envelope": after_envelope,
                    "opportunity_window_evidence": window_evidence,
                    "verified_evidence": {
                        "family": family,
                        "generation_rank": generation_rank,
                        "feasible": True,
                        "hard_constraint_result": {"passed": True, "failures": []},
                        "commitment_preservation": {
                            "preserved": True,
                            "protected_count": c4_count,
                        },
                        "stability": {
                            "score": score.breakdown["stability"],
                            "moved_count": len(diff.moved),
                            "removed_count": len(diff.removed),
                            "added_count": len(diff.added),
                        },
                        "budget": {
                            "remaining_minor": after_envelope["budget_remaining_minor"],
                            "currency": journey.budget_currency,
                        },
                        "mobility": {
                            "travel_delta_min": travel_delta,
                            "provider": "mock-mobility",
                        },
                        "time": {
                            "journey_end_slack_min": after_envelope["journey_end_slack_min"],
                            "end_time_delta_min": int(
                                (
                                    (diff.new_end_at or datetime.fromisoformat(journey.start_at))
                                    - (diff.old_end_at or datetime.fromisoformat(journey.start_at))
                                ).total_seconds()
                                // 60
                            ),
                        },
                        "preference": {"fit": preference_fit},
                        "opportunity": {
                            "value": opportunity_value,
                            "evidence": window_evidence,
                        },
                        "reason_codes": sorted(set(reason_codes)),
                    },
                    "reason_codes": sorted(set(reason_codes)),
                    "execution_partition": {
                        "terminal_prefix_ids": partition.terminal_prefix_ids,
                        "current_activity_id": partition.current_activity_id,
                        "c4_anchor_ids": partition.c4_anchor_ids,
                        "mutable_suffix_ids": partition.mutable_suffix_ids,
                    },
                },
                default=str,
            ),
            explanation_json=json.dumps(
                {
                    "summary": "Deterministic mock replan proposal",
                    "reasons": ["provider-independent deterministic candidate", family],
                    "source": "DETERMINISTIC",
                }
            ),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        session.add(proposal)
        record_audit(
            session,
            action="replan.generated",
            entity_type="ReplanProposal",
            entity_id=proposal.id,
            journey_id=journey.id,
            after={"status": proposal.status, "candidate_family": family},
        )
        created.append(proposal)

    if not created:
        session.rollback()
        details = ", ".join(sorted(failed_reasons)) or "NO_DISTINCT_CANDIDATE"
        raise HTTPException(422, f"no feasible replan proposal: {details}")

    # Python sort is stable, so exact-score ties preserve deterministic
    # candidate-generation order instead of using UUID4 as a random tiebreak.
    # Prefer lower disruption when utility is equal; a noisier candidate must
    # not outrank an otherwise equal, more stable repair.
    def _proposal_rank(candidate: ReplanProposalModel) -> tuple[float, float, float, float]:
        breakdown = json.loads(candidate.score_breakdown_json or "{}")
        return (
            -candidate.utility_score,
            -float(breakdown.get("stability", 0.0)),
            -float(breakdown.get("commitment_preservation", 0.0)),
            -float(breakdown.get("time_reliability", 0.0)),
        )

    created.sort(key=_proposal_rank)
    response = _replan_payload(created[0])
    if generation_idempotency_key is not None and generation_signature is not None:
        now = datetime.now(timezone.utc)
        session.add(
            IdempotencyKey(
                key=generation_idempotency_key,
                operation="replan.generate",
                request_hash=generation_signature,
                response_status=201,
                response_json=json.dumps(response, sort_keys=True),
                created_at=now.isoformat(),
                expires_at=(now + timedelta(days=7)).isoformat(),
            )
        )
    session.commit()
    return response


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
def accept_replan(
    proposal_id: UUID,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_session),
):
    if idempotency_key is None:
        raise HTTPException(422, "Idempotency-Key header is required")
    try:
        header_key = validate_idempotency_key(idempotency_key)
    except CommerceValidationError as exc:
        raise HTTPException(422, str(exc)) from exc

    signature = canonical_request_signature({"proposal_id": str(proposal_id)})
    scoped_key = f"replan.accept:{header_key}"
    existing = session.get(IdempotencyKey, scoped_key)
    if existing is not None:
        if existing.request_hash != signature:
            raise HTTPException(409, "same idempotency key used for a different request")
        stored = json.loads(existing.response_json or "{}")
        if not stored:
            raise HTTPException(409, "replan idempotency record is incomplete")
        return stored

    proposal = require(session, ReplanProposalModel, str(proposal_id), "Replan proposal")
    if proposal.status != "PRESENTED":
        raise HTTPException(409, "replan proposal is no longer actionable")
    journey = require(session, Journey, proposal.journey_id, "Journey")
    if (
        journey.status != "ACTIVE"
        or journey.active_plan_version_id != proposal.base_plan_version_id
    ):
        raise HTTPException(409, "replan base plan is stale")
    trigger_event = (
        session.get(EventModel, proposal.trigger_event_id) if proposal.trigger_event_id else None
    )
    if trigger_event is None or trigger_event.status not in {"DETECTED", "ACKNOWLEDGED"}:
        raise HTTPException(409, "replan trigger event is no longer actionable")
    base = session.get(PlanVersion, proposal.base_plan_version_id)
    proposed = session.get(PlanVersion, proposal.proposed_plan_version_id)
    if (
        base is None
        or proposed is None
        or base.status != "ACTIVE"
        or proposed.status != "CANDIDATE"
    ):
        raise HTTPException(409, "replan plan is missing or inconsistent")
    gate = validate_plan_feasibility(session, journey, proposed, include_active_c4=True)
    if not gate.passed:
        raise HTTPException(409, f"replan is no longer feasible: {', '.join(gate.failures)}")
    old_current = (
        session.get(Activity, journey.current_activity_id) if journey.current_activity_id else None
    )
    replacement_current = None
    if old_current is not None:
        replacement_current = session.scalar(
            select(Activity).where(
                Activity.plan_version_id == proposed.id,
                Activity.sequence_no == old_current.sequence_no,
            )
        )
        if replacement_current is None:
            replacement_current = session.scalar(
                select(Activity)
                .where(
                    Activity.plan_version_id == proposed.id,
                    Activity.sequence_no > old_current.sequence_no,
                    Activity.status.not_in(("COMPLETED", "SKIPPED", "CANCELLED")),
                )
                .order_by(Activity.sequence_no)
            )
        if replacement_current is None:
            raise HTTPException(409, "replan does not preserve the current execution position")

    decided_at = datetime.now(timezone.utc).isoformat()
    base.status = "SUPERSEDED"
    proposed.status = "ACTIVE"
    journey.active_plan_version_id = proposed.id
    journey.current_activity_id = replacement_current.id if replacement_current else None
    proposal.status = "ACCEPTED"
    proposal.decided_at = decided_at
    if trigger_event.status == "DETECTED":
        trigger_event.status = "ACKNOWLEDGED"

    # Commitment.activity_id is PlanVersion-local. The durable authority is
    # the stable semantic/time anchor in policy_json, but JourneyTwin exposes
    # activity_id for the active plan. Remap every active C4 reference after
    # accepting a replan so the projection cannot point into the superseded
    # plan.
    proposed_activities = session.scalars(
        select(Activity)
        .where(Activity.plan_version_id == proposed.id)
        .order_by(Activity.sequence_no)
    ).all()
    active_c4_commitments = session.scalars(
        select(CommitmentModel).where(
            CommitmentModel.journey_id == journey.id,
            CommitmentModel.status == "ACTIVE",
            CommitmentModel.level == "C4_Anchored",
        )
    ).all()
    for commitment in active_c4_commitments:
        policy = json.loads(commitment.policy_json or "{}")
        semantic_key = str(policy.get("semantic_key") or "")
        scheduled_start = str(policy.get("scheduled_start_at") or "")
        replacement = next(
            (
                activity
                for activity in proposed_activities
                if str(activity.place_id or activity.city_service_id or "") == semantic_key
                and datetime.fromisoformat(activity.start_at).isoformat()
                == datetime.fromisoformat(scheduled_start).isoformat()
            ),
            None,
        )
        if replacement is None:
            # A preserved commitment must remain addressable on the accepted
            # active plan; fail safe rather than persisting a stale pointer.
            raise HTTPException(409, "accepted replan cannot remap an active C4 commitment")
        commitment.activity_id = replacement.id
        commitment.updated_at = decided_at

    competitors = session.scalars(
        select(ReplanProposalModel).where(
            ReplanProposalModel.journey_id == journey.id,
            ReplanProposalModel.base_plan_version_id == base.id,
            ReplanProposalModel.id != proposal.id,
            ReplanProposalModel.status == "PRESENTED",
        )
    ).all()
    for competitor in competitors:
        competitor.status = "INVALIDATED"
        competitor.decided_at = decided_at
        competitor_plan = session.get(PlanVersion, competitor.proposed_plan_version_id)
        if competitor_plan is not None and competitor_plan.status == "CANDIDATE":
            competitor_plan.status = "REJECTED"
        record_audit(
            session,
            action="replan.invalidated",
            entity_type="ReplanProposal",
            entity_id=competitor.id,
            journey_id=journey.id,
            after={"status": competitor.status, "reason": "base_plan_superseded"},
        )

    record_audit(
        session,
        action="replan.accepted",
        entity_type="ReplanProposal",
        entity_id=proposal.id,
        journey_id=journey.id,
        after={"status": proposal.status},
    )
    twin = _twin_snapshot(session, journey)
    response = {
        "journey": journey_schema(journey).model_dump(mode="json"),
        "proposal": _replan_payload(proposal),
        "twin": twin,
    }
    session.add(
        IdempotencyKey(
            key=scoped_key,
            operation="replan.accept",
            request_hash=signature,
            response_status=200,
            response_json=json.dumps(response, sort_keys=True),
            created_at=decided_at,
            expires_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        )
    )
    session.commit()
    return response


@app.post("/api/v1/replans/{proposal_id}/reject", response_model=ReplanProposalSchema)
def reject_replan(proposal_id: UUID, session: Session = Depends(get_session)):
    proposal = require(session, ReplanProposalModel, str(proposal_id), "Replan proposal")
    if proposal.status == "REJECTED":
        return _replan_payload(proposal)
    if proposal.status != "PRESENTED":
        raise HTTPException(409, "replan proposal is no longer rejectable")
    proposal.status = "REJECTED"
    proposal.decided_at = datetime.now(timezone.utc).isoformat()
    proposed = session.get(PlanVersion, proposal.proposed_plan_version_id)
    if proposed is not None and proposed.status == "CANDIDATE":
        proposed.status = "REJECTED"
    record_audit(
        session,
        action="replan.rejected",
        entity_type="ReplanProposal",
        entity_id=proposal.id,
        journey_id=proposal.journey_id,
        after={"status": proposal.status},
    )
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
    primary = (
        LiteLLMExplanationProvider(model=settings.ai_model, api_key=settings.ai_api_key)
        if settings.ai_enabled
        else None
    )
    result = await ResilientAIExplanationService(primary=primary).explain(facts, task=message)
    session.commit()
    return {
        "message": result.text,
        "mode": "FALLBACK" if result.degraded else "AI",
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
