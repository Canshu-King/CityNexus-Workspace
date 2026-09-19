from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.db.models import (
    CityService,
    Journey,
    JourneyConstraint,
    Place,
    PlanVersion,
    Preference,
    Traveler,
)
from app.db.session import SessionLocal, ensure_schema, get_session
from app.schemas import (
    ConstraintInput,
    GeneratePlansRequest,
    JourneyCreate,
    JourneyPatch,
    PreferenceInput,
    TravelerCreate,
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
                value_json=__import__("json").dumps(item.value, ensure_ascii=False),
                weight=item.weight,
                source="user",
                created_at=now,
                updated_at=now,
            )
        )
    session.commit()
    return [
        preference_schema(item)
        for item in session.scalars(
            select(Preference)
            .where(Preference.traveler_id == traveler.id)
            .order_by(Preference.category, Preference.preference_key)
        ).all()
    ]


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
    start = payload.start_at or datetime.fromisoformat(journey.start_at)
    end = payload.end_at or datetime.fromisoformat(journey.end_at)
    if end <= start:
        raise HTTPException(422, "end_at must be after start_at")
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
    require(session, Journey, str(journey_id), "Journey")
    now = datetime.now(timezone.utc).isoformat()
    item = JourneyConstraint(
        id=str(uuid4()),
        journey_id=str(journey_id),
        kind=payload.kind,
        category=payload.category,
        rule_code=payload.rule_code,
        params_json=__import__("json").dumps(payload.params, ensure_ascii=False),
        weight=payload.weight,
        active=True,
        created_at=now,
        updated_at=now,
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
    session.delete(item)
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
    try:
        plans = generate_plans(session, journey, request.planning_mode, request.candidate_count)
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
    journey = require(session, Journey, str(journey_id), "Journey")
    plan = session.scalar(
        select(PlanVersion).where(
            PlanVersion.id == str(plan_version_id), PlanVersion.journey_id == journey.id
        )
    )
    if plan is None:
        raise HTTPException(404, f"PlanVersion {plan_version_id} was not found")
    if plan.status not in {"CANDIDATE", "SELECTED"}:
        raise HTTPException(422, "Only a candidate plan can be selected")
    current = session.scalar(
        select(PlanVersion).where(
            PlanVersion.journey_id == journey.id, PlanVersion.status == "ACTIVE"
        )
    )
    if current and current.id != plan.id:
        current.status = "SUPERSEDED"
    plan.status = "ACTIVE"
    journey.status = "PLANNED"
    journey.active_plan_version_id = plan.id
    journey.updated_at = datetime.now(timezone.utc).isoformat()
    session.commit()
    return journey_schema(journey)
