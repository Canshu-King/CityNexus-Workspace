from __future__ import annotations

import asyncio
import json
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import delete, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.agent.autorun import (
    autorun_status,
    enrolled_journey_ids,
    ensure_enrollment,
    start_autorun,
    stop_autorun,
)
from app.agent.contracts import (
    AgentAction,
    AgentMode,
    AuthoritativeActionFacts,
    AuthorizationDecision,
)
from app.agent.delegation_policy import (
    evaluate_action,
    get_or_create_policy,
    policy_from_model,
    policy_payload,
    update_policy,
)
from app.agent.gateway import AgentToolGateway
from app.agent.guardian import guardian_status, scan_guardian
from app.agent.mission import create_mission, mission_payload
from app.agent.orchestrator import configured_journey_agent
from app.agent.predictive import (
    build_resilience_snapshot,
    counterfactual_payload,
    latest_snapshot,
    simulate_counterfactuals,
    snapshot_payload,
)
from app.agent.principal import resolve_agent_principal
from app.agent.runtime_identity import runtime_status
from app.agent.runtime import (
    AgentRuntimeUnavailable,
    DeepSeekJourneyAgent,
    persisted_agent_run_payload,
    unavailable_run_payload,
)
from app.agent.signal_pipeline import fixture_payload, set_fixture_state
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
    AccommodationOfferSnapshot,
    ActionApproval,
    Activity,
    AgentRun,
    AgentRunStep,
    AuditLog,
    AutopilotEnrollment,
    CityService,
    CitySignalFixture,
    CounterfactualSimulation,
    EdgeDevice,
    ExternalReservationDraft,
    IdempotencyKey,
    ImpactAssessment,
    Journey,
    JourneyLeg,
    JourneyConstraint,
    JourneyMission,
    JourneyOutcomeEvent,
    JourneyTripContext,
    MobilityFact,
    NotificationEvent,
    OfflineJourneySnapshot,
    PaymentTransaction,
    Place,
    PlanVersion,
    Preference,
    ProviderObservation,
    RealPlaceCandidate,
    StayJourneyOption,
    TransportReservation,
    Traveler,
    TravelerTwinSnapshot,
    WebObservation,
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
from app.execution.clock import execution_clock
from app.execution.traveler_twin import (
    clear_learned,
    learn_from_journey,
    planning_preference_items,
    refresh_snapshot,
)
from app.execution.traveler_twin import (
    snapshot_payload as traveler_twin_payload,
)
from app.integrations.ai.litellm_provider import LiteLLMExplanationProvider
from app.integrations.ai.copilot_contract import (
    CopilotInterpretation,
    classify_copilot_message,
    disruption_event_type,
    disruption_severity,
    simulate_what_if,
    validate_proposed_action,
)
from app.integrations.ai.resilient import ResilientAIExplanationService
from app.integrations.ai.responses import DeepSeekResponsesClient, DeepSeekResponsesError
from app.integrations.ai.semantic_compiler import (
    apply_semantic_policy,
    compile_semantic_envelope,
)
from app.integrations.ai.event_targeting import resolve_event_target
from app.integrations.ai.web_research import WebResearchProvider
from app.integrations.hermes.native_client import HermesNativeClient, native_hermes_status
from app.integrations.china.amap import amap_status, provider_for_region
from app.integrations.context.open_meteo import OpenMeteoContextProvider
from app.integrations.context.weather_runtime import refresh_weather_runtime
from app.integrations.discovery.real_city import (
    capture_real_city_candidates,
    normalize_opening_hours,
)
from app.integrations.discovery.orchestration import orchestrate_discovery
from app.integrations.inbox.vision import extract_reservation_image, extract_reservation_text
from app.integrations.inbox.semantic_intake import (
    journey_interpreter_context,
    journey_memory_payload,
    prepare_semantic_intake,
)
from app.integrations.mobility.runtime import capture_runtime_mobility_snapshot
from app.integrations.mobility.snapshot_capture import (
    MobilitySnapshotCaptureError,
    MobilitySnapshotCaptureResult,
)
from app.integrations.mock.commerce_providers import MockBookingProvider, MockPaymentProvider
from app.integrations.push import push_capability
from app.intelligence.feasibility_envelope import FeasibilityEnvelope
from app.intelligence.impact_resolver import (
    impact_payload,
    persist_impact_assessment,
    resolve_impact,
)
from app.intelligence.opportunity_window import build_window
from app.intelligence.reason_codes import ReasonCode, VerifiedExplanationFacts
from app.intelligence.replan_diff import PlanActivitySnapshot, diff_plans
from app.operations.v9 import (
    _execution_truth,
    authenticate_edge,
    confirm_reservation_draft,
    edge_snapshot,
    import_reservation_artifact,
    materialize_stay_option,
    notify,
    record_edge_action,
    record_edge_observation,
    record_location,
    refresh_offline_snapshot,
    register_edge_device,
    register_push_subscription,
    set_luggage_context,
)
from app.planning.solver_contract import (
    ReplanSolverProblem,
    SolverAnchor,
    SolverReplacementOption,
)
from app.planning.solver_runtime import (
    SolverAttempt,
    generate_solver_candidates,
    normalize_solver_mode,
)
from app.planning.solver_v2 import (
    SolverV2Anchor,
    SolverV2Option,
    SolverV2Plan,
    SolverV2Problem,
    SolverV2Slot,
    solve_v2,
    solver_v2_problem_fingerprint,
)
from app.replanning.candidate_evidence import verified_interest_preference_fit
from app.replanning.feasibility import (
    FeasibilityActivity,
    activity_from_record,
    build_context,
    evaluate_feasibility,
)
from app.replanning.mock_replan_engine import partition_execution, rank_closure_replacements
from app.replanning.opportunity_window_family import (
    WindowReplacementInput,
    evaluate_window_replacement,
)
from app.replanning.provider_snapshots import MobilitySnapshot, TravelEstimateFact
from app.replanning.protected_commitments import active_c4_hard_constraints
from app.replanning.verified_scoring import score_replan_candidate
from app.schemas import (
    AgentApprovalRequest,
    AgentCommandRequest,
    AgentPolicyPayload,
    AgentToolCall,
    BookingCreate,
    CitySignalFixtureRequest,
    ConstraintInput,
    EdgeActionRequest,
    EdgeDeviceCreateRequest,
    EdgeObservationRequest,
    EventCreate,
    GeneratePlansRequest,
    AuthoritativeComposeRequest,
    GuardianAutopilotStart,
    JourneyCreate,
    JourneyPatch,
    LocationObservationRequest,
    LuggageContextRequest,
    MobilityModeRequest,
    OrderCreate,
    OutcomeEventCreate,
    PreferenceInput,
    PushSubscriptionRequest,
    RealCityDiscoveryRequest,
    RealCityIntelligenceRequest,
    ReplanGenerateRequest,
    ReservationImportRequest,
    ReservationDraftPatchRequest,
    ReservationTextExtractionRequest,
    ReservationVisionRequest,
    ResilienceRefreshRequest,
    ScheduleChangeRequest,
    StayAutopilotRecoveryRequest,
    StayModeChangeRequest,
    StayPlanGenerateRequest,
    TransactionCreate,
    TravelerCreate,
    TripStudioAcceptRequest,
    TripStudioPreviewRequest,
    WeatherDisruptionRequest,
    WebResearchRequest,
)
from app.schemas import (
    AgentPolicy as AgentPolicySchema,
)
from app.schemas import (
    Booking as BookingSchema,
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
from app.stay_mobility import (
    capture_accommodation_offers,
    capture_mobility_facts,
    experience_payload,
    fact_payload,
    generate_stay_options,
    option_payload,
)
from app.planning.authoritative_v12 import compose_authoritative_multiday

ensure_schema()
app = FastAPI(title="CityNexus MVP API", version="0.1.0")
logger = logging.getLogger(__name__)
_trip_studio_accept_lock = RLock()


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


def _record_outcome_event(
    session: Session,
    journey: Journey,
    *,
    activity: Activity | None,
    event_type: str,
    actor_type: str,
    occurred_at_actual: str | None = None,
    payload: dict[str, Any] | None = None,
    related_proposal_id: str | None = None,
    related_agent_run_id: str | None = None,
) -> JourneyOutcomeEvent:
    now = datetime.now(timezone.utc).isoformat()
    event = JourneyOutcomeEvent(
        id=str(uuid4()),
        journey_id=journey.id,
        activity_id=activity.id if activity is not None else None,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=str(journey.traveler_id),
        occurred_at_actual=occurred_at_actual or now,
        planned_start_at=activity.start_at if activity is not None else None,
        planned_end_at=activity.end_at if activity is not None else None,
        source="DOMAIN",
        related_proposal_id=related_proposal_id,
        related_agent_run_id=related_agent_run_id,
        payload_json=json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
        created_at=now,
    )
    session.add(event)
    session.flush()
    record_audit(
        session,
        action="journey.outcome.recorded",
        entity_type="JourneyOutcomeEvent",
        entity_id=event.id,
        journey_id=journey.id,
        actor_type=actor_type,
        actor_id=str(journey.traveler_id),
        after={
            "event_type": event_type,
            "activity_id": event.activity_id,
            "occurred_at_actual": event.occurred_at_actual,
            "planned_start_at": event.planned_start_at,
            "planned_end_at": event.planned_end_at,
            "payload": payload or {},
        },
    )
    return event


def build_open_meteo_provider(client: httpx.AsyncClient) -> OpenMeteoContextProvider:
    """Build the server-owned provider used only by explicit weather refresh."""

    return OpenMeteoContextProvider(client=client, base_url=settings.open_meteo_url)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    with SessionLocal() as session:
        session.execute(select(Traveler).limit(1))
    return {
        "status": "ok",
        "database": "ok",
        "ai": "enabled" if settings.ai_enabled and settings.ai_api_key else "disabled",
    }


@app.get("/api/v1/agent/tools")
def list_agent_tools() -> list[dict[str, object]]:
    return AgentToolGateway.catalog()


@app.get("/api/v1/agent/tools/v2")
def list_agent_tools_v2() -> list[dict[str, object]]:
    return AgentToolGateway.catalog_v2()


@app.get("/api/v1/agent/runtime-status")
def get_agent_runtime_status() -> dict[str, object]:
    return runtime_status()


@app.get("/api/v1/agent/hermes/capabilities")
def get_native_hermes_capabilities() -> dict[str, Any]:
    """Expose non-secret native Hermes capability facts to the CityNexus UI."""

    return native_hermes_status()


@app.get("/api/v1/agent/hermes/runs/{run_id}")
def get_native_hermes_run(run_id: str) -> dict[str, Any]:
    client = HermesNativeClient()
    try:
        return client.get_run(run_id)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "native Hermes run status is unavailable") from exc
    finally:
        client.close()


@app.get("/api/v1/agent/hermes/runs/{run_id}/events")
def stream_native_hermes_events(run_id: str) -> StreamingResponse:
    def events():
        client = HermesNativeClient()
        try:
            for item in client.iter_events(run_id):
                yield f"data: {json.dumps(item, ensure_ascii=False, sort_keys=True)}\n\n"
        finally:
            client.close()

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}/stop")
def stop_native_hermes_run(journey_id: UUID, run_id: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Stop a native run through CityNexus; Hermes is never called directly by the UI."""
    require(session, Journey, str(journey_id), "Journey")
    client = HermesNativeClient()
    try:
        return client.stop(run_id)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "native Hermes run stop is unavailable") from exc
    finally:
        client.close()


@app.post("/api/v1/agent/tools/v2/{tool_name}")
def call_agent_tool_v2(
    tool_name: str,
    request: Request,
    payload: AgentToolCall,
    session: Session = Depends(get_session),
):
    scope_journey_id = payload.journey_id
    if scope_journey_id is None and payload.proposal_id is not None:
        proposal = session.get(ReplanProposalModel, str(payload.proposal_id))
        if proposal is not None:
            scope_journey_id = UUID(proposal.journey_id)
    principal = resolve_agent_principal(request, session, journey_id=scope_journey_id)
    resolved_payload = payload.model_copy(update={"agent_id": principal.actor_id})
    return AgentToolGateway(session).dispatch(tool_name, resolved_payload)


@app.post("/api/v1/agent/tools/{tool_name}")
def call_agent_tool(
    tool_name: str,
    request: Request,
    payload: AgentToolCall,
    session: Session = Depends(get_session),
):
    scope_journey_id = payload.journey_id
    if scope_journey_id is None and payload.proposal_id is not None:
        proposal = session.get(ReplanProposalModel, str(payload.proposal_id))
        if proposal is not None:
            scope_journey_id = UUID(proposal.journey_id)
    principal = resolve_agent_principal(request, session, journey_id=scope_journey_id)
    # The request's agent_id is only an untrusted hint for compatibility with
    # existing clients. All gateway keys and audit records use this server-
    # resolved principal instead.
    resolved_payload = payload.model_copy(update={"agent_id": principal.actor_id})
    return AgentToolGateway(session).dispatch(tool_name, resolved_payload)


@app.post("/api/v1/journeys/{journey_id}/agent/commands")
def run_agent_command(
    journey_id: UUID,
    payload: AgentCommandRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    interpretation = _copilot_fallback_or_ai(payload.command, _copilot_context(session, journey))
    event_type = (
        str(interpretation.entities.get("event_type"))
        if interpretation.intent == "DISRUPTION_REPORT"
        and interpretation.entities.get("event_type")
        else None
    )
    event = None
    if event_type is not None:
        semantic = interpretation.semantic_envelope or {
            "assertion_status": interpretation.entities.get("assertion_status", "ASSERTED"),
            "effective_time": interpretation.entities.get("effective_time", "NOW"),
            "entities": dict(interpretation.entities),
        }
        target = resolve_event_target(
            session,
            journey,
            event_type=event_type,
            semantic=semantic,
            now=now_dt,
        )
        if target.resolution == "UNRESOLVED_REVIEW_REQUIRED":
            return {
                "mission": None,
                "event_id": None,
                "review_required": True,
                "event": {
                    "id": None,
                    "event_type": event_type,
                    "status": "REVIEW_REQUIRED",
                    "affected_activity_id": None,
                    "occurred_at": None,
                    "target_resolution": target.resolution,
                    "effective_time": str(semantic.get("effective_time") or "FUTURE").upper(),
                },
            }
        resolved = target.resolution != "UNRESOLVED_REVIEW_REQUIRED"
        event = EventModel(
            id=str(uuid4()),
            journey_id=journey.id,
            provider_key="user-command",
            provenance="USER_REPORTED",
            event_type=event_type,
            severity=disruption_severity(payload.command, event_type),
            status="DETECTED",
            # A free-text disruption is scoped to the server's current
            # execution position. The model may describe the event, but it
            # must not invent an Activity target.
            affected_activity_id=target.activity_id,
            occurred_at=target.occurred_at or now,
            detected_at=now,
            payload_json=json.dumps(
                {
                    "description": payload.command,
                    "source": "agent_command",
                    "extra_minutes": 15 if event_type == "TRAFFIC_DELAY" else None,
                    "semantic": {**semantic, "target_resolution": target.resolution},
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            created_at=now,
        )
        session.add(event)
        session.flush()
    mission = create_mission(
        session,
        journey,
        command=payload.command,
        requested_autonomy=payload.requested_autonomy,
        trigger_event_id=event.id if event else None,
    )
    record_audit(
        session,
        action="agent.mission.created",
        entity_type="JourneyMission",
        entity_id=mission.id,
        journey_id=journey.id,
        actor_type="USER",
        actor_id=journey.traveler_id,
        after={
            "mission_id": mission.id,
            "event_id": event.id if event else None,
            "requested_autonomy": mission.requested_autonomy,
        },
    )
    session.commit()
    native_status = native_hermes_status()
    if native_status.get("ready"):
        native = HermesNativeClient()
        try:
            native_run = native.create_run(
                mission_id=mission.id,
                journey_id=journey.id,
                input_text=payload.command,
                instructions=(
                    "Inspect the authoritative Journey before acting. Use only the configured CityNexus MCP tools. "
                    "Respect the requested autonomy boundary; proposal-only work must not mutate. "
                    "CityNexus Gateway and deterministic feasibility are authoritative."
                ),
                autonomy=mission.requested_autonomy,
            )
            return {
                "mission": mission_payload(mission),
                "event_id": event.id if event else None,
                "run": {
                    "run_id": native_run.run_id,
                    "mission_id": mission.id,
                    "status": native_run.status.upper(),
                    "provider_key": "hermes-native",
                    "model_key": settings.hermes_model,
                    "runtime_identity": "HERMES_NATIVE_MCP",
                    "outcome": None,
                    "failure_reason": None,
                    "tool_steps": [],
                    "native_events_url": f"/api/v1/agent/hermes/runs/{native_run.run_id}/events",
                },
            }
        except (httpx.HTTPError, ValueError) as exc:
            record_audit(
                session,
                action="agent.native_hermes.fallback",
                entity_type="JourneyMission",
                entity_id=mission.id,
                journey_id=journey.id,
                actor_type="SYSTEM",
                after={"reason": str(exc)},
            )
            session.commit()
        finally:
            native.close()
    if not settings.ai_api_key and not (settings.hermes_api_url and settings.hermes_api_key):
        run = unavailable_run_payload(session, journey=journey, mission=mission)
        return {
            "mission": mission_payload(mission),
            "event_id": event.id if event else None,
            "run": run,
        }
    runtime = configured_journey_agent(native_factory=DeepSeekJourneyAgent)
    try:
        run = runtime.run(session, journey=journey, mission=mission)
    except AgentRuntimeUnavailable as exc:
        failed_run = session.scalar(
            select(AgentRun)
            .where(AgentRun.mission_id == mission.id)
            .order_by(AgentRun.created_at.desc(), AgentRun.id.desc())
        )
        run = (
            persisted_agent_run_payload(session, failed_run)
            if failed_run is not None
            else {
                "run_id": None,
                "mission_id": mission.id,
                "status": "FAILED_EXTERNAL",
                "provider_key": "deepseek",
                "model_key": settings.ai_model.removeprefix("deepseek/"),
                "runtime_identity": runtime_status()["runtime_identity"],
                "outcome": None,
                "failure_reason": str(exc),
                "tool_steps": [],
            }
        )
    finally:
        runtime.close()
    return {
        "mission": mission_payload(mission),
        "event_id": event.id if event else None,
        "run": run,
    }


@app.put("/api/v1/journeys/{journey_id}/guardian/mission")
def put_guardian_mission(
    journey_id: UUID,
    payload: AgentCommandRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    current = session.scalars(
        select(JourneyMission).where(
            JourneyMission.journey_id == journey.id,
            JourneyMission.is_standing.is_(True),
            JourneyMission.status == "ACTIVE",
        )
    ).all()
    for mission in current:
        mission.status = "SUPERSEDED"
        mission.completed_at = datetime.now(timezone.utc).isoformat()
    mission = create_mission(
        session,
        journey,
        command=payload.command,
        requested_autonomy=payload.requested_autonomy,
        trigger_event_id=None,
        is_standing=True,
    )
    mission.status = "ACTIVE"
    record_audit(
        session,
        action="guardian.mission.activated",
        entity_type="JourneyMission",
        entity_id=mission.id,
        journey_id=journey.id,
        actor_type="USER",
        actor_id=journey.traveler_id,
        after=mission_payload(mission),
    )
    session.commit()
    return mission_payload(mission)


@app.post("/api/v1/journeys/{journey_id}/guardian/scan")
def run_guardian_scan(
    journey_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    return scan_guardian(session, journey)


@app.post("/api/v1/journeys/{journey_id}/guardian/autopilot/start")
def start_guardian_autopilot(
    journey_id: UUID,
    payload: GuardianAutopilotStart | None = None,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    if journey.status != "ACTIVE":
        raise HTTPException(409, "Guardian Autopilot requires an active Journey")
    mission = session.scalar(
        select(JourneyMission).where(
            JourneyMission.journey_id == journey.id,
            JourneyMission.is_standing.is_(True),
            JourneyMission.status == "ACTIVE",
        )
    )
    if mission is None:
        raise HTTPException(409, "activate a standing Guardian mission before starting Autopilot")
    enrollment = ensure_enrollment(
        session,
        journey,
        enabled=True,
        interval_seconds=payload.interval_seconds if payload else None,
    )
    # Make the subscription visible before the process-global worker can wake.
    session.commit()
    result = start_autorun(interval_seconds=payload.interval_seconds if payload else None)
    record_audit(
        session,
        action="guardian.autopilot.started",
        entity_type="Journey",
        entity_id=journey.id,
        journey_id=journey.id,
        actor_type="USER",
        actor_id=journey.traveler_id,
        after={
            "enrollment": {"journey_id": enrollment.journey_id, "enabled": enrollment.enabled},
            **result,
        },
    )
    session.commit()
    return {
        "journey_id": journey.id,
        "mission_id": mission.id,
        "enrollment": {
            "journey_id": enrollment.journey_id,
            "enabled": bool(enrollment.enabled),
            "interval_seconds": enrollment.interval_seconds,
            "provider_mesh": json.loads(enrollment.provider_mesh_json or "{}"),
        },
        **result,
    }


@app.post("/api/v1/journeys/{journey_id}/guardian/autopilot/stop")
def stop_guardian_autopilot(
    journey_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    enrollment = session.get(AutopilotEnrollment, journey.id)
    if enrollment is not None:
        enrollment.enabled = False
        enrollment.updated_at = datetime.now(timezone.utc).isoformat()
        session.commit()
    remaining = enrolled_journey_ids(session)
    result = stop_autorun() if not remaining else autorun_status()
    record_audit(
        session,
        action="guardian.autopilot.stopped",
        entity_type="Journey",
        entity_id=journey.id,
        journey_id=journey.id,
        actor_type="USER",
        actor_id=journey.traveler_id,
        after={"remaining_enrolled_journeys": remaining, **result},
    )
    session.commit()
    return {
        "journey_id": journey.id,
        "enrollment": {
            "journey_id": journey.id,
            "enabled": False,
            "remaining_enrolled_journeys": remaining,
        },
        **result,
    }


@app.get("/api/v1/journeys/{journey_id}/guardian/autopilot/status")
def get_guardian_autopilot_status(
    journey_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    enrollment = session.get(AutopilotEnrollment, journey.id)
    return {
        "journey_id": journey.id,
        "enrollment": (
            {
                "journey_id": enrollment.journey_id,
                "enabled": bool(enrollment.enabled),
                "interval_seconds": enrollment.interval_seconds,
                "provider_mesh": json.loads(enrollment.provider_mesh_json or "{}"),
                "last_pulse_at": enrollment.last_pulse_at,
                "last_error": enrollment.last_error,
            }
            if enrollment is not None
            else None
        ),
        **autorun_status(),
    }


@app.post(
    "/api/v1/journeys/{journey_id}/guardian/provider-fixture",
    response_model=dict[str, Any],
)
@app.post(
    "/api/v1/journeys/{journey_id}/guardian/signal-fixture",
    response_model=dict[str, Any],
)
def update_guardian_provider_fixture(
    journey_id: UUID,
    payload: CitySignalFixtureRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    fixture = set_fixture_state(
        session,
        journey,
        state=payload.state,
        payload=payload.payload,
    )
    session.commit()
    return fixture_payload(fixture)


@app.get("/api/v1/journeys/{journey_id}/guardian/status")
def get_guardian_status(
    journey_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    result = guardian_status(session, journey)
    result["autopilot"] = autorun_status()
    enrollment = session.get(AutopilotEnrollment, journey.id)
    result["autopilot"]["enrollment"] = (
        {
            "journey_id": enrollment.journey_id,
            "enabled": bool(enrollment.enabled),
            "interval_seconds": enrollment.interval_seconds,
            "provider_mesh": json.loads(enrollment.provider_mesh_json or "{}"),
            "last_pulse_at": enrollment.last_pulse_at,
            "last_error": enrollment.last_error,
        }
        if enrollment is not None
        else None
    )
    fixture = session.get(CitySignalFixture, journey.id)
    result["signal_fixture"] = fixture_payload(fixture) if fixture is not None else None
    return result


@app.get("/api/v1/journeys/{journey_id}/resilience")
@app.get("/api/v1/journeys/{journey_id}/guardian/resilience")
def get_journey_resilience(
    journey_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    snapshot = latest_snapshot(session, journey.id)
    if snapshot is None:
        snapshot = build_resilience_snapshot(session, journey)
        session.commit()
    return snapshot_payload(snapshot)


@app.post("/api/v1/journeys/{journey_id}/resilience/refresh")
@app.post("/api/v1/journeys/{journey_id}/guardian/resilience/refresh")
def refresh_journey_resilience(
    journey_id: UUID,
    payload: ResilienceRefreshRequest | None = None,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    mode = payload.mode if payload else "replay"
    discovery = None
    if mode in {"live", "captured_replay"}:
        try:
            discovery = capture_real_city_candidates(
                session,
                journey,
                query="indoor city service",
                mode=mode,
            )
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
    snapshot = build_resilience_snapshot(session, journey)
    simulations = simulate_counterfactuals(session, journey, snapshot)
    session.commit()
    return {
        "snapshot": snapshot_payload(snapshot),
        "counterfactuals": [counterfactual_payload(item) for item in simulations],
        "discovery": discovery,
    }


@app.get("/api/v1/journeys/{journey_id}/resilience/counterfactuals")
def list_journey_counterfactuals(
    journey_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(CounterfactualSimulation)
        .where(CounterfactualSimulation.journey_id == journey.id)
        .order_by(CounterfactualSimulation.created_at, CounterfactualSimulation.scenario_key)
    ).all()
    return {
        "journey_id": journey.id,
        "counterfactuals": [counterfactual_payload(item) for item in rows],
    }


@app.get("/api/v1/journeys/{journey_id}/provider-mesh")
def get_journey_provider_mesh(
    journey_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(ProviderObservation)
        .where(ProviderObservation.journey_id == journey.id)
        .order_by(ProviderObservation.captured_at.desc())
        .limit(30)
    ).all()
    candidates = session.scalars(
        select(RealPlaceCandidate)
        .where(RealPlaceCandidate.journey_id == journey.id)
        .order_by(RealPlaceCandidate.captured_at.desc(), RealPlaceCandidate.name)
        .limit(20)
    ).all()
    return {
        "journey_id": journey.id,
        "providers": [
            {
                "provider_key": row.provider_key,
                "observation_type": row.observation_type,
                "state": row.state,
                "provenance": row.provenance,
                "captured_at": row.captured_at,
                "expires_at": row.expires_at,
            }
            for row in rows
        ],
        "real_place_candidates": [
            {
                "id": row.id,
                "provider_key": row.provider_key,
                "external_id": row.external_id,
                "name": row.name,
                "category": row.category,
                "location": {"latitude": row.latitude, "longitude": row.longitude},
                "tags": json.loads(row.tags_json or "[]"),
                "opening_hours": json.loads(row.opening_hours_json or "{}"),
                "cost_evidence": json.loads(row.metadata_json or "{}").get(
                    "cost_evidence", {"status": "UNKNOWN"}
                ),
                "captured_at": row.captured_at,
                "expires_at": row.expires_at,
                "materialized_place_id": row.materialized_place_id,
                "status": row.status,
            }
            for row in candidates
        ],
    }


@app.post("/api/v1/journeys/{journey_id}/real-city/discover")
@app.post("/api/v1/journeys/{journey_id}/provider-mesh/discover")
def discover_real_city_services(
    journey_id: UUID,
    payload: RealCityDiscoveryRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    try:
        result = capture_real_city_candidates(
            session,
            journey,
            query=payload.query,
            radius_m=payload.radius_m,
            limit=payload.limit,
            mode=payload.mode,
        )
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    session.commit()
    return result


@app.post("/api/v1/journeys/{journey_id}/real-city/intelligence", status_code=201)
def run_real_city_intelligence(
    journey_id: UUID,
    payload: RealCityIntelligenceRequest,
    session: Session = Depends(get_session),
):
    """Run the V13.4 provider-truth discovery path through authoritative Compose."""

    journey = require(session, Journey, str(journey_id), "Journey")
    try:
        bundle = orchestrate_discovery(
            session,
            journey,
            goal=payload.goal,
            mode=payload.mode,
            radius_m=payload.radius_m,
            limit=payload.limit,
            client=_deepseek_client(),
            require_fully_grounded=payload.require_fully_grounded,
        )
        selected_place_ids = list(bundle["selected_place_ids"])
        if len(selected_place_ids) < 2:
            raise ValueError("V13_DISCOVERY_NO_FEASIBLE_PLACE_SET")
        result = compose_authoritative_multiday(
            session,
            journey,
            place_ids=selected_place_ids,
            candidate_count=payload.candidate_count,
            discovery_evidence=bundle["evidence"],
        )
        if not result.plans:
            raise ValueError("V13_DISCOVERY_COMPOSE_EMPTY")
        chosen = None
        selection_failures: list[str] = []
        for candidate_plan in result.plans:
            candidate_id = str(candidate_plan.id)
            try:
                select_plan(UUID(str(journey.id)), UUID(candidate_id), session)
            except HTTPException as exc:
                session.rollback()
                if exc.status_code not in {409, 422}:
                    raise
                selection_failures.append(str(exc.detail))
                continue
            chosen = session.get(PlanVersion, candidate_id)
            break
        if chosen is None:
            detail = "; ".join(selection_failures[:3]) or "no composed candidate passed the deterministic gate"
            raise HTTPException(422, f"V13_DISCOVERY_NO_FEASIBLE_PLAN: {detail}")
        session.expire_all()
        selected_journey = require(session, Journey, str(journey.id), "Journey")
        twin = _twin_snapshot(session, selected_journey)
        session.commit()
        return {
            **bundle,
            "compose": {
                "optimizer": result.optimizer_kind,
                "frozen_evidence_ids": list(result.evidence_ids),
                "plan_ids": [item.id for item in result.plans],
            },
            "selected_plan_id": chosen.id,
            "selected_plan": plan_schema(session, chosen),
            "journey_twin": twin,
        }
    except DeepSeekResponsesError as exc:
        session.rollback()
        raise HTTPException(502, f"DeepSeek discovery failed: {exc}") from exc
    except ValueError as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/v1/journeys/{journey_id}/operations/stream")
def journey_operations_stream(
    journey_id: UUID,
    request: Request,
    after: str | None = None,
    timeout_seconds: float = Query(default=30.0, gt=0, le=120),
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    journey_key = journey.id

    async def stream():
        # REST hydration already renders historical truth.  A reconnect can
        # pass its last timestamp; a fresh stream starts at the connection
        # boundary so it does not replay the whole audit log as fake activity.
        cursor = after or datetime.now(timezone.utc).isoformat()
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if await request.is_disconnected():
                break
            with SessionLocal() as stream_session:
                statement = (
                    select(AuditLog)
                    .where(
                        AuditLog.journey_id == journey_key,
                        AuditLog.created_at > cursor,
                    )
                    .order_by(AuditLog.created_at, AuditLog.id)
                )
                rows = stream_session.scalars(statement).all()
                if rows:
                    for row in rows:
                        projection = _audit_projection(row)
                        cursor = row.created_at
                        yield (
                            f"id: {row.id}\n"
                            f"event: {projection['event_type']}\n"
                            f"data: {json.dumps(projection, ensure_ascii=False)}\n\n"
                        )
                    continue
            yield ": citynexus-heartbeat\n\n"
            await asyncio.sleep(0.25)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/journeys/{journey_id}/agent/runs/{run_id}")
def get_agent_run(
    journey_id: UUID,
    run_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    run = session.get(AgentRun, str(run_id))
    if run is None or run.journey_id != journey.id:
        raise HTTPException(404, "agent run was not found")
    mission = session.get(JourneyMission, run.mission_id)
    steps = session.scalars(
        select(AgentRunStep).where(AgentRunStep.run_id == run.id).order_by(AgentRunStep.sequence_no)
    ).all()

    def decode(value: str) -> Any:
        return json.loads(value)

    return {
        "run_id": run.id,
        "mission_id": run.mission_id,
        "journey_id": run.journey_id,
        "provider_key": run.provider_key,
        "model_key": run.model_key,
        "status": run.status,
        "outcome": run.outcome,
        "failure_reason": run.failure_reason,
        "created_at": run.created_at,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "mission_status": mission.status if mission else None,
        "mission": mission_payload(mission) if mission else None,
        "tool_steps": [
            {
                "id": step.id,
                "sequence_no": step.sequence_no,
                "tool_name": step.tool_name,
                "arguments": decode(step.arguments_json),
                "result": decode(step.result_json),
                "decision": step.decision,
                "status": step.status,
                "created_at": step.created_at,
                "completed_at": step.completed_at,
            }
            for step in steps
        ],
    }


@app.post("/api/v1/journeys/{journey_id}/agent/approvals/{approval_id}/approve")
def approve_agent_action(
    journey_id: UUID,
    approval_id: UUID,
    payload: AgentApprovalRequest | None = None,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    approval = session.get(ActionApproval, str(approval_id))
    if (
        approval is None
        or approval.journey_id != journey.id
        or approval.traveler_id != journey.traveler_id
    ):
        raise HTTPException(404, "agent approval was not found")
    from app.agent.approval import approve_action_approval

    return approve_action_approval(
        session,
        approval,
        approval_method=payload.approval_method if payload else "USER_CONFIRMATION",
        step_up_code=payload.step_up_code if payload else None,
        actor_id=journey.traveler_id,
    )


@app.post("/api/v1/demo/reset")
def demo_reset(session: Session = Depends(get_session)) -> dict[str, str]:
    # The demo endpoint is also the E2E/runtime reset boundary.  The Guardian
    # worker is process-global while enrollments are Journey-scoped; leaving
    # the worker alive after replacing the demo rows makes the next Journey
    # appear to have an active autopilot with no subscription of its own.
    stop_autorun()
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
    session.flush()
    session.add(
        TravelerTwinSnapshot(
            traveler_id=traveler.id,
            explicit_preferences_json="[]",
            learned_soft_preferences_json="[]",
            conflicts_json="[]",
            confidence=0.0,
            evidence_count=0,
            provenance_json=json.dumps({"source": "traveler-create", "updated_at": now}),
            updated_at=now,
        )
    )
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


@app.get("/api/v1/travelers/{traveler_id}/traveler-twin")
def get_traveler_twin(traveler_id: UUID, session: Session = Depends(get_session)):
    traveler = require(session, Traveler, str(traveler_id), "Traveler")
    snapshot = refresh_snapshot(session, traveler.id)
    session.commit()
    return traveler_twin_payload(snapshot)


@app.delete("/api/v1/travelers/{traveler_id}/traveler-twin/learned")
def clear_traveler_twin(traveler_id: UUID, session: Session = Depends(get_session)):
    traveler = require(session, Traveler, str(traveler_id), "Traveler")
    snapshot = clear_learned(session, traveler.id)
    record_audit(
        session,
        action="traveler.twin.learned_cleared",
        entity_type="TravelerTwinSnapshot",
        entity_id=traveler.id,
        actor_type="USER",
        actor_id=traveler.id,
        after={"traveler_id": traveler.id, "learned_evidence_cleared": True},
    )
    session.commit()
    return traveler_twin_payload(snapshot)


@app.get("/api/v1/journeys/{journey_id}/outcomes")
def list_journey_outcomes(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(JourneyOutcomeEvent)
        .where(JourneyOutcomeEvent.journey_id == journey.id)
        .order_by(JourneyOutcomeEvent.occurred_at_actual, JourneyOutcomeEvent.id)
    ).all()
    return {
        "journey_id": journey.id,
        "events": [
            {
                "id": item.id,
                "activity_id": item.activity_id,
                "event_type": item.event_type,
                "actor_type": item.actor_type,
                "occurred_at_actual": item.occurred_at_actual,
                "planned_start_at": item.planned_start_at,
                "planned_end_at": item.planned_end_at,
                "source": item.source,
                "payload": _json_dict(item.payload_json),
                "related_proposal_id": item.related_proposal_id,
                "related_agent_run_id": item.related_agent_run_id,
            }
            for item in rows
        ],
    }


@app.post("/api/v1/journeys/{journey_id}/outcomes", status_code=201)
def record_journey_outcome(
    journey_id: UUID,
    payload: OutcomeEventCreate,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    activity = session.get(Activity, str(payload.activity_id)) if payload.activity_id else None
    if activity is not None:
        plan_ids = {
            row.id
            for row in session.scalars(
                select(PlanVersion).where(PlanVersion.journey_id == journey.id)
            ).all()
        }
        if activity.plan_version_id not in plan_ids:
            raise HTTPException(422, "activity is not on the Journey")
    item = _record_outcome_event(
        session,
        journey,
        activity=activity,
        event_type=payload.event_type,
        actor_type=payload.actor_type,
        occurred_at_actual=(
            payload.occurred_at_actual.isoformat() if payload.occurred_at_actual else None
        ),
        payload=payload.payload,
        related_proposal_id=str(payload.related_proposal_id)
        if payload.related_proposal_id
        else None,
        related_agent_run_id=(
            str(payload.related_agent_run_id) if payload.related_agent_run_id else None
        ),
    )
    session.commit()
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "activity_id": item.activity_id,
        "event_type": item.event_type,
        "occurred_at_actual": item.occurred_at_actual,
    }


@app.get("/api/v1/travelers/{traveler_id}/agent-policy", response_model=AgentPolicySchema)
def get_agent_policy(traveler_id: UUID, session: Session = Depends(get_session)):
    traveler = require(session, Traveler, str(traveler_id), "Traveler")
    row = get_or_create_policy(session, traveler.id)
    payload = policy_payload(row)
    session.commit()
    return payload


@app.put("/api/v1/travelers/{traveler_id}/agent-policy", response_model=AgentPolicySchema)
def put_agent_policy(
    traveler_id: UUID,
    payload: AgentPolicyPayload,
    session: Session = Depends(get_session),
):
    traveler = require(session, Traveler, str(traveler_id), "Traveler")
    before = policy_payload(get_or_create_policy(session, traveler.id))
    row = update_policy(
        session,
        traveler.id,
        mode=AgentMode(payload.mode),
        auto_accept_replan=payload.auto_accept_replan,
        max_auto_replan_cost_delta_minor=payload.max_auto_replan_cost_delta_minor,
        max_auto_loss_minor=payload.max_auto_loss_minor,
        max_auto_schedule_drift_min=payload.max_auto_schedule_drift_min,
        allowed_activity_types=payload.allowed_activity_types,
        allowed_booking_types=payload.allowed_booking_types,
        protected_commitment_levels=payload.protected_commitment_levels,
        allow_auto_commitment_management=payload.allow_auto_commitment_management,
        allow_auto_when_provider_degraded=payload.allow_auto_when_provider_degraded,
        allow_auto_on_critical_event=payload.allow_auto_on_critical_event,
    )
    after = policy_payload(row)
    record_audit(
        session,
        action="agent.policy.updated",
        entity_type="TravelerAgentPolicy",
        entity_id=traveler.id,
        journey_id=None,
        actor_type="traveler",
        actor_id=traveler.id,
        before=before,
        after=after,
    )
    session.commit()
    return after


def suggested_room_count(party_size: int) -> int:
    """Offer a small-group starting point while leaving room choice explicit."""

    if party_size <= 2:
        return 1
    if party_size <= 4:
        return 2
    if party_size <= 6:
        return 3
    return max(3, (party_size + 2) // 3)


@app.post("/api/v1/journeys", status_code=201)
def create_journey(payload: JourneyCreate, session: Session = Depends(get_session)):
    require(session, Traveler, str(payload.traveler_id), "Traveler")
    now = datetime.now(timezone.utc).isoformat()
    occupancy = dict(payload.occupancy)
    occupancy.setdefault("adults", payload.party_size)
    if "rooms" not in occupancy:
        occupancy["rooms"] = suggested_room_count(payload.party_size)
        occupancy["rooms_source"] = "SUGGESTED"
    else:
        occupancy["rooms_source"] = "USER"
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
    now = datetime.now(timezone.utc).isoformat()
    session.add(
        JourneyTripContext(
            journey_id=journey.id,
            arrival_anchor_json=json.dumps(
                payload.arrival_anchor.model_dump(mode="json") if payload.arrival_anchor else {},
                ensure_ascii=False,
            ),
            departure_anchor_json=json.dumps(
                payload.departure_anchor.model_dump(mode="json")
                if payload.departure_anchor
                else {},
                ensure_ascii=False,
            ),
            party_size=payload.party_size,
            occupancy_json=json.dumps(occupancy, ensure_ascii=False),
            stay_budget_amount_minor=payload.stay_budget.amount_minor if payload.stay_budget else 0,
            stay_budget_currency=payload.stay_budget.currency if payload.stay_budget else payload.budget.currency,
            created_at=now,
            updated_at=now,
        )
    )
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


@app.get("/api/v1/journeys/{journey_id}/experience")
def get_journey_experience(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    return experience_payload(session, journey)


@app.post("/api/v1/journeys/{journey_id}/stays/offers/capture")
def capture_stay_offers(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    offers = capture_accommodation_offers(session, journey)
    session.commit()
    return {
        "provenance": "CAPTURED_REPLAY",
        "provider_key": offers[0].provider_key if offers else "unavailable",
        "offers": [
            {
                "id": item.id,
                "property_name": item.property_name,
                "room_type": item.room_type,
                "check_in_at": item.check_in_at,
                "check_out_at": item.check_out_at,
                "nightly_amount_minor": item.nightly_amount_minor,
                "taxes_amount_minor": item.taxes_amount_minor,
                "total_amount_minor": item.total_amount_minor,
                "currency": item.currency,
                "refundable": bool(item.refundable),
                "cancellation_policy": json.loads(item.cancellation_policy_json),
                "evidence": json.loads(item.evidence_json),
                "captured_at": item.captured_at,
                "expires_at": item.expires_at,
            }
            for item in offers
        ],
    }


@app.post("/api/v1/journeys/{journey_id}/stay-options/generate")
def generate_stay_journey_options(
    journey_id: UUID,
    payload: StayPlanGenerateRequest | None = None,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    request = payload or StayPlanGenerateRequest()
    options = generate_stay_options(session, journey, weather=request.weather_state)
    if request.sort == "CHEAPEST":
        options = sorted(options, key=lambda item: (item.stay_total_minor, item.rank))
    elif request.sort == "LEAST_TRAVEL":
        options = sorted(
            options, key=lambda item: (item.daily_travel_minor, item.walking_min, item.rank)
        )
    elif request.sort == "MOST_FLEXIBLE":
        options = sorted(options, key=lambda item: (-item.cancellation_score, item.rank))
    session.commit()
    offers = session.scalars(
        select(AccommodationOfferSnapshot)
        .where(AccommodationOfferSnapshot.journey_id == journey.id)
        .order_by(AccommodationOfferSnapshot.total_amount_minor)
    ).all()
    return {
        "optimizer": options[0].optimizer_kind if options else "BOUNDED_DETERMINISTIC",
        "query": request.query,
        "sort": request.sort,
        "top_k": [option_payload(item, offers) for item in options[: request.candidate_count]],
        "hard_constraints": {
            "protected_commitments": "PRESERVED",
            "deterministic_feasibility": "PASSED",
        },
    }


@app.post("/api/v1/journeys/{journey_id}/stays/search")
def search_stays(
    journey_id: UUID,
    payload: StayPlanGenerateRequest | None = None,
    session: Session = Depends(get_session),
):
    """Product-facing alias for the captured accommodation search contract."""
    journey = require(session, Journey, str(journey_id), "Journey")
    offers = capture_accommodation_offers(session, journey)
    session.commit()
    return {
        "query": (payload.query if payload else f"{journey.city_code} stay-aware Journey"),
        "provenance": "CAPTURED_REPLAY",
        "offers": [
            {
                "id": item.id,
                "property_name": item.property_name,
                "total_amount_minor": item.total_amount_minor,
                "nightly_amount_minor": item.nightly_amount_minor,
                "currency": item.currency,
                "refundable": bool(item.refundable),
                "check_in_at": item.check_in_at,
                "check_out_at": item.check_out_at,
                "location": {"latitude": item.latitude, "longitude": item.longitude},
            }
            for item in offers
        ],
    }


@app.get("/api/v1/journeys/{journey_id}/stay-options")
def list_stay_journey_options(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    return experience_payload(session, journey)


@app.get("/api/v1/journeys/{journey_id}/multiday")
def get_multiday_journey(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    return experience_payload(session, journey)


@app.get("/api/v1/journeys/{journey_id}/stay-mobility/providers")
def get_stay_mobility_providers(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    return experience_payload(session, journey)["provider_mesh"]


@app.post("/api/v1/journeys/{journey_id}/stay-options/{option_id}/select")
def select_stay_journey_option(
    journey_id: UUID, option_id: UUID, session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    option = session.scalar(
        select(StayJourneyOption).where(
            StayJourneyOption.id == str(option_id), StayJourneyOption.journey_id == journey.id
        )
    )
    if option is None:
        raise HTTPException(404, "StayJourneyOption was not found")
    materialized = materialize_stay_option(session, journey, option, source="STAY_SELECTION")
    if materialized.gate_status != "PASSED" or materialized.plan is None:
        session.rollback()
        raise HTTPException(
            422,
            "Stay option could not become authoritative Journey truth: "
            + ", ".join(materialized.failures),
        )
    session.commit()
    offers = session.scalars(
        select(AccommodationOfferSnapshot)
        .where(AccommodationOfferSnapshot.journey_id == journey.id)
        .order_by(AccommodationOfferSnapshot.total_amount_minor)
    ).all()
    return {
        "selected_option_id": option.id,
        "plan_version_id": materialized.plan.id,
        "journey_status": journey.status,
        "deterministic_feasibility": materialized.gate_status,
        "protected_commitments_preserved": materialized.locked_commitments_preserved,
        "option": option_payload(option, offers),
    }


@app.post("/api/v1/journeys/{journey_id}/stay-options/{option_id}/weather")
def apply_stay_weather(
    journey_id: UUID,
    option_id: UUID,
    payload: WeatherDisruptionRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    option = session.scalar(
        select(StayJourneyOption).where(
            StayJourneyOption.id == str(option_id), StayJourneyOption.journey_id == journey.id
        )
    )
    if option is None:
        raise HTTPException(404, "StayJourneyOption was not found")
    generate_stay_options(session, journey, weather=payload.state)
    option = session.get(StayJourneyOption, option.id)
    session.commit()
    offers = session.scalars(
        select(AccommodationOfferSnapshot)
        .where(AccommodationOfferSnapshot.journey_id == journey.id)
        .order_by(AccommodationOfferSnapshot.total_amount_minor)
    ).all()
    return {
        "weather_state": payload.state,
        "selected_option_id": option.id if option else None,
        "protected_commitments_preserved": True,
        "recovery": "reduced_weather_exposure",
        "option": option_payload(option, offers) if option else None,
    }


@app.post("/api/v1/journeys/{journey_id}/stay-options/{option_id}/autopilot/recover")
def stay_autopilot_recover(
    journey_id: UUID,
    option_id: UUID,
    payload: StayAutopilotRecoveryRequest,
    session: Session = Depends(get_session),
):
    """Run the V8 low-risk mode recovery through the existing delegation policy."""
    journey = require(session, Journey, str(journey_id), "Journey")
    option = session.scalar(
        select(StayJourneyOption).where(
            StayJourneyOption.id == str(option_id), StayJourneyOption.journey_id == journey.id
        )
    )
    if option is None:
        raise HTTPException(404, "StayJourneyOption was not found")
    before_modes = json.loads(option.leg_modes_json or "[]")
    first_mode = before_modes[0] if before_modes else "WALK"
    before_mode = str(first_mode.get("mode")) if isinstance(first_mode, dict) else str(first_mode)
    requested_mode = "TRANSIT" if payload.state in {"RAIN", "TRANSIT_DISRUPTION"} else "AUTO"
    offer = session.get(AccommodationOfferSnapshot, option.accommodation_offer_id)
    if offer is None:
        raise HTTPException(409, "selected accommodation evidence is no longer available")
    first_leg = next((item for item in before_modes if isinstance(item, dict)), None)
    fact = (
        session.scalar(
            select(MobilityFact).where(
                MobilityFact.journey_id == journey.id,
                MobilityFact.from_key == str(first_leg.get("from_key")),
                MobilityFact.to_key == str(first_leg.get("to_key")),
                MobilityFact.mode == requested_mode,
            )
        )
        if first_leg
        else None
    )
    if fact is None:
        raise HTTPException(422, f"{requested_mode} is unavailable for this captured leg")
    policy_row = get_or_create_policy(session, journey.traveler_id)
    current_fact = (
        session.scalar(
            select(MobilityFact).where(
                MobilityFact.journey_id == journey.id,
                MobilityFact.from_key == fact.from_key,
                MobilityFact.to_key == fact.to_key,
                MobilityFact.mode == before_mode,
            )
        )
        if fact
        else None
    )
    known_paid_cost = not (fact.paid_mode and fact.cost_status == "UNKNOWN")
    cost_delta = max(
        0,
        int(fact.cost_amount_minor or 0)
        - int(current_fact.cost_amount_minor or 0 if current_fact else 0),
    )
    authorization = evaluate_action(
        policy_from_model(policy_row),
        AgentAction.RESCHEDULE_ACTIVITY,
        AuthoritativeActionFacts(
            hard_constraints_passed=known_paid_cost,
            locked_commitments_preserved=True,
            c4_affected=False,
            cost_delta_minor=cost_delta,
            loss_delta_minor=0,
            schedule_drift_min=0,
            affected_activity_type="transport",
            action_reversible=True,
            provider_degraded=False,
        ),
    )
    authorized = authorization.decision == AuthorizationDecision.ALLOW_AUTO
    event = EventModel(
        id=str(uuid4()),
        journey_id=journey.id,
        provider_key="citynexus-weather-replay",
        provenance="PROVIDER_VERIFIED",
        event_type="WEATHER",
        severity="MAJOR",
        status="DETECTED",
        affected_activity_id=None,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        detected_at=datetime.now(timezone.utc).isoformat(),
        payload_json=json.dumps(
            {"state": payload.state, "source": "captured_replay", "option_id": option.id},
            ensure_ascii=False,
        ),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(event)
    materialized = None
    if authorized:
        generate_stay_options(session, journey, weather=payload.state)
        option = session.get(StayJourneyOption, option.id)
        if option is not None:
            materialized = materialize_stay_option(
                session,
                journey,
                option,
                source="AUTOPILOT_RECOVERY",
                force_mode=requested_mode,
            )
    executed = bool(materialized and materialized.gate_status == "PASSED")
    gate_status = (
        materialized.gate_status if materialized is not None else "NOT_RUN_UNTIL_AUTHORIZED"
    )
    if executed:
        notify(
            session,
            journey.id,
            dedupe_key=f"autopilot:{event.id}:{requested_mode}",
            kind="AUTOPILOT_PLAN_CHANGED",
            priority="HIGH",
            payload={
                "event_id": event.id,
                "plan_version_id": materialized.plan.id if materialized.plan else None,
                "mode": requested_mode,
            },
        )
    record_audit(
        session,
        action="v8.autopilot.recovery",
        entity_type="StayJourneyOption",
        entity_id=option.id,
        journey_id=journey.id,
        actor_type="AI_AGENT",
        actor_id="v8-autopilot",
        after={
            "decision": authorization.decision.value,
            "executed": executed,
            "requested_mode": requested_mode,
            "event_id": event.id,
            "protected_commitments_preserved": bool(
                materialized.locked_commitments_preserved if materialized else True
            ),
            "post_action_gate": gate_status,
            "policy_version": authorization.policy_version,
        },
    )
    session.commit()
    offers = session.scalars(
        select(AccommodationOfferSnapshot)
        .where(AccommodationOfferSnapshot.journey_id == journey.id)
        .order_by(AccommodationOfferSnapshot.total_amount_minor)
    ).all()
    return {
        "event_id": event.id,
        "decision": authorization.decision.value,
        "reason_codes": list(authorization.reason_codes),
        "executed": executed,
        "requested_mode": requested_mode,
        "before_mode": before_mode,
        "after_mode": requested_mode if executed else before_mode,
        "policy_version": authorization.policy_version,
        "active_plan_version_id": journey.active_plan_version_id,
        "protected_commitments_preserved": bool(
            materialized.locked_commitments_preserved if materialized else True
        ),
        "post_action_gate": gate_status,
        "option": option_payload(option, offers) if option else None,
    }


@app.get("/api/v1/journeys/{journey_id}/mobility")
def list_journey_mobility(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    return {
        "modes": [
            fact_payload(item)
            for item in session.scalars(
                select(MobilityFact)
                .where(MobilityFact.journey_id == journey.id)
                .order_by(MobilityFact.from_key, MobilityFact.to_key, MobilityFact.mode)
            ).all()
        ],
        "available_modes": ["WALK", "BICYCLE", "TRANSIT", "AUTO", "RIDE_HAIL"],
        "choose_for_me": True,
    }


@app.post("/api/v1/journeys/{journey_id}/mobility/compare")
def compare_journey_mobility(
    journey_id: UUID, payload: MobilityModeRequest, session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    facts = session.scalars(
        select(MobilityFact)
        .where(MobilityFact.journey_id == journey.id, MobilityFact.mode == payload.mode)
        .order_by(MobilityFact.from_key, MobilityFact.to_key)
    ).all()
    if not facts:
        offers = capture_accommodation_offers(session, journey)
        for offer in offers:
            capture_mobility_facts(session, journey, offer)
        session.commit()
        facts = session.scalars(
            select(MobilityFact)
            .where(MobilityFact.journey_id == journey.id, MobilityFact.mode == payload.mode)
            .order_by(MobilityFact.from_key, MobilityFact.to_key)
        ).all()
    return {
        "mode": payload.mode,
        "facts": [fact_payload(item) for item in facts],
        "deterministic_feasibility": "PASSED",
        "costs_are_provider_evidence": True,
    }


@app.post("/api/v1/journeys/{journey_id}/stay-options/{option_id}/mode")
def change_stay_option_mode(
    journey_id: UUID,
    option_id: UUID,
    payload: StayModeChangeRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    option = session.scalar(
        select(StayJourneyOption).where(
            StayJourneyOption.id == str(option_id), StayJourneyOption.journey_id == journey.id
        )
    )
    if option is None:
        raise HTTPException(404, "StayJourneyOption was not found")
    offer = session.get(AccommodationOfferSnapshot, option.accommodation_offer_id)
    if offer is None:
        raise HTTPException(409, "selected accommodation evidence is no longer available")
    modes = json.loads(option.leg_modes_json or "[]")
    target = next(
        (
            item
            for item in modes
            if isinstance(item, dict)
            and (payload.from_key is None or item.get("from_key") == payload.from_key)
            and (payload.to_key is None or item.get("to_key") == payload.to_key)
        ),
        None,
    )
    if target is None:
        raise HTTPException(422, "requested Journey leg was not found")
    facts_query = select(MobilityFact).where(
        MobilityFact.journey_id == journey.id,
        MobilityFact.mode == payload.mode,
        MobilityFact.from_key == str(target["from_key"]),
        MobilityFact.to_key == str(target["to_key"]),
    )
    fact = session.scalar(facts_query.order_by(MobilityFact.from_key, MobilityFact.to_key))
    if fact is None:
        raise HTTPException(422, f"mode {payload.mode} is unavailable for the requested leg")
    if fact.paid_mode and fact.cost_status == "UNKNOWN":
        raise HTTPException(
            409,
            "UNKNOWN paid mode cost requires confirmation and cannot auto-execute",
        )
    target["mode"] = payload.mode
    target["mobility_fact_id"] = fact.id
    target["cost_status"] = fact.cost_status
    option.leg_modes_json = json.dumps(modes, ensure_ascii=False)
    option.journey_impact_json = json.dumps(
        {
            **json.loads(option.journey_impact_json or "{}"),
            "mode_switch": {
                "mode": payload.mode,
                "duration_min": fact.duration_min,
                "cost_amount_minor": fact.cost_amount_minor,
                "currency": fact.currency,
                "walking_min": fact.walking_min,
                "transfers": fact.transfers,
                "weather_exposure": fact.weather_exposure,
                "reliability_score": fact.reliability_score,
                "cost_status": (
                    "KNOWN_CAPTURED"
                    if fact.cost_status == "KNOWN"
                    and fact.provenance in {"CAPTURED_REPLAY", "SYNTHETIC_FIXTURE"}
                    else fact.cost_status
                ),
                "cost_evidence_status": fact.cost_status,
                "provenance": fact.provenance,
            },
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    selected_facts = [
        session.scalar(
            select(MobilityFact).where(
                MobilityFact.journey_id == journey.id,
                MobilityFact.from_key == str(item["from_key"]),
                MobilityFact.to_key == str(item["to_key"]),
                MobilityFact.mode == str(item["mode"]),
            )
        )
        for item in modes
        if isinstance(item, dict)
    ]
    selected_facts = [item for item in selected_facts if item is not None]
    previous_walking = int(option.walking_min)
    previous_travel = int(option.daily_travel_minor)
    option.daily_travel_minor = sum(int(item.cost_amount_minor or 0) for item in selected_facts)
    option.mobility_total_minor = option.daily_travel_minor
    option.score = round(
        max(
            0.0,
            float(option.score)
            + (float(previous_walking - fact.walking_min) / 2000.0)
            - (float(previous_travel - (fact.cost_amount_minor or 0)) / 100000.0),
        ),
        3,
    )
    option.walking_min = sum(item.walking_min for item in selected_facts)
    materialized = None
    if option.status == "SELECTED" or option.materialized_plan_version_id:
        materialized = materialize_stay_option(session, journey, option, source="MODE_CHANGE")
        if materialized.gate_status != "PASSED":
            session.rollback()
            raise HTTPException(422, ", ".join(materialized.failures))
    session.commit()
    return {
        "option_id": option.id,
        "selected_mode": payload.mode,
        "impact": json.loads(option.journey_impact_json),
        "active_plan_version_id": journey.active_plan_version_id,
        "protected_commitments_preserved": bool(
            materialized.locked_commitments_preserved if materialized else True
        ),
        "deterministic_feasibility": (
            materialized.gate_status if materialized else "CANDIDATE_NOT_MATERIALIZED"
        ),
    }


def _draft_payload(item: ExternalReservationDraft) -> dict[str, Any]:
    extracted = json.loads(item.extracted_json or "{}")
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "artifact_type": item.artifact_type,
        "extracted": extracted,
        "interpretation": {
            "anchor_role": extracted.get("anchor_role"),
            "anchor_role_confidence": extracted.get("anchor_role_confidence"),
            "semantic_target": extracted.get("semantic_target"),
            "payment_status": extracted.get("payment_status"),
            "reasoning_summary": extracted.get("reasoning_summary"),
        },
        "smart_intake": extracted.get("smart_intake", {}),
        "unresolved_fields": json.loads(item.unresolved_fields_json or "[]"),
        "extraction_mode": item.extraction_mode,
        "status": item.status,
        "created_at": item.created_at,
        "confirmed_at": item.confirmed_at,
    }


def _reservation_payload(item: TransportReservation) -> dict[str, Any]:
    return {
        "id": item.id,
        "journey_id": item.journey_id,
        "draft_id": item.draft_id,
        "reservation_type": item.reservation_type,
        "provider_key": item.provider_key,
        "confirmation_ref": item.confirmation_ref,
        "origin": json.loads(item.origin_json or "{}"),
        "destination": json.loads(item.destination_json or "{}"),
        "scheduled_departure_at": item.scheduled_departure_at,
        "scheduled_arrival_at": item.scheduled_arrival_at,
        "estimated_arrival_at": item.estimated_arrival_at,
        "actual_arrival_at": item.actual_arrival_at,
        "status": item.status,
        "realtime_status": item.realtime_status,
        "passenger_scope": json.loads(item.passenger_scope_json or "{}"),
        "change_policy": json.loads(item.change_policy_json or "{}"),
        "price": {
            "amount_minor": item.price_amount_minor,
            "currency": item.currency,
            "status": item.price_status,
        },
        "source_provenance": item.source_provenance,
        "captured_at": item.captured_at,
        "booking_id": item.booking_id,
        "commitment_id": item.commitment_id,
    }


@app.put("/api/v1/journeys/{journey_id}/operations/luggage")
def put_journey_luggage(
    journey_id: UUID,
    payload: LuggageContextRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    row = set_luggage_context(
        session,
        journey,
        baggage_present=payload.baggage_present,
        baggage_size_class=payload.baggage_size_class,
        luggage_drop_required=payload.luggage_drop_required,
    )
    session.commit()
    return {
        "journey_id": journey.id,
        "baggage_present": bool(row.baggage_present),
        "baggage_size_class": row.baggage_size_class,
        "luggage_drop_required": bool(row.luggage_drop_required),
    }


@app.post("/api/v1/journeys/{journey_id}/inbox/import", status_code=201)
def import_journey_reservation(
    journey_id: UUID,
    payload: ReservationImportRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    draft = import_reservation_artifact(
        session,
        journey,
        artifact_type=payload.artifact_type,
        payload=payload.payload,
    )
    session.commit()
    return _draft_payload(draft)


@app.get("/api/v1/journeys/{journey_id}/inbox")
def list_journey_inbox(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    drafts = session.scalars(
        select(ExternalReservationDraft)
        .where(ExternalReservationDraft.journey_id == journey.id)
        .order_by(ExternalReservationDraft.created_at)
    ).all()
    return {"journey_id": journey.id, "drafts": [_draft_payload(item) for item in drafts]}


@app.get("/api/v1/journeys/{journey_id}/memory")
def get_journey_memory(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    return journey_memory_payload(session, journey)


def _reservation_unresolved(extracted: dict[str, Any]) -> list[str]:
    critical = (
        "reservation_type",
        "origin",
        "destination",
        "scheduled_departure_at",
        "scheduled_arrival_at",
        "confirmation_ref",
    )
    unresolved = [
        field
        for field in critical
        if extracted.get(field) in (None, "", "UNKNOWN", "unknown")
    ]
    if "_semantic_contract" in extracted:
        role = str(extracted.get("anchor_role") or "UNKNOWN").upper()
        if role not in {"ARRIVAL", "DEPARTURE", "MID_TRIP"}:
            unresolved.append("anchor_role")
        if role == "MID_TRIP" and not extracted.get("semantic_node_key"):
            unresolved.append("semantic_target")
    return list(dict.fromkeys(unresolved))


def _refresh_draft_semantics(
    session: Session, journey: Journey, draft: ExternalReservationDraft
) -> dict[str, Any]:
    extracted = json.loads(draft.extracted_json or "{}")
    if draft.artifact_type == "STRUCTURED_JSON":
        return extracted
    enriched, _ = prepare_semantic_intake(session, journey, extracted)
    unresolved = _reservation_unresolved(enriched)
    draft.extracted_json = json.dumps(enriched, ensure_ascii=False)
    draft.unresolved_fields_json = json.dumps(unresolved)
    draft.status = "READY_FOR_CONFIRMATION" if not unresolved else "NEEDS_REVIEW"
    return enriched


def _deepseek_client(*, vision: bool = False) -> DeepSeekResponsesClient | None:
    if not settings.ai_api_key:
        return None
    return DeepSeekResponsesClient(
        api_key=settings.ai_api_key,
        model=settings.ai_vision_model if vision else settings.ai_model,
        base_url=settings.deepseek_api_url,
        reasoning_effort=settings.deepseek_reasoning_effort,
        timeout_seconds=settings.impact_timeout_seconds,
    )


@app.post("/api/v1/journeys/{journey_id}/inbox/text-extract", status_code=201)
def extract_journey_reservation_text(
    journey_id: UUID,
    payload: ReservationTextExtractionRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    client = _deepseek_client()
    if client is None:
        return {"status": "NOT_CONFIGURED", "draft": None, "provider": "deepseek"}
    try:
        extracted = extract_reservation_text(
            client,
            payload.text,
            journey_context=journey_interpreter_context(session, journey),
        )
    except DeepSeekResponsesError as exc:
        return {"status": "FAILED_EXTERNAL", "draft": None, "provider": "deepseek", "reason": str(exc)}
    extracted, _ = prepare_semantic_intake(session, journey, extracted)
    unresolved = _reservation_unresolved(extracted)
    draft = ExternalReservationDraft(
        id=str(uuid4()),
        journey_id=journey.id,
        artifact_type="TEXT",
        raw_payload_json=json.dumps({"text_length": len(payload.text)}, ensure_ascii=False),
        extracted_json=json.dumps(extracted, ensure_ascii=False),
        unresolved_fields_json=json.dumps(unresolved),
        extraction_mode="DEEPSEEK_RESPONSES_TEXT",
        status="READY_FOR_CONFIRMATION" if not unresolved else "NEEDS_REVIEW",
        created_at=datetime.now(timezone.utc).isoformat(),
        confirmed_at=None,
    )
    session.add(draft)
    session.commit()
    return {"status": "READY", "draft": _draft_payload(draft), "provider": "deepseek"}


@app.post("/api/v1/journeys/{journey_id}/inbox/vision", status_code=201)
def extract_journey_reservation_image(
    journey_id: UUID,
    payload: ReservationVisionRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    try:
        client = _deepseek_client(vision=True)
    except TypeError as exc:
        # Preserve the existing V10 provider seam for tests/fakes that expose
        # the original zero-argument factory; production uses the dedicated
        # vision model above.
        if "vision" not in str(exc):
            raise
        client = _deepseek_client()
    if client is None:
        return {"status": "NOT_CONFIGURED", "draft": None, "provider": "deepseek"}
    try:
        extracted = extract_reservation_image(
            client,
            payload.image_url,
            hint=payload.hint,
            journey_context=journey_interpreter_context(session, journey),
        )
    except DeepSeekResponsesError as exc:
        return {"status": "FAILED_EXTERNAL", "draft": None, "provider": "deepseek", "reason": str(exc)}
    extracted, _ = prepare_semantic_intake(session, journey, extracted)
    unresolved = _reservation_unresolved(extracted)
    draft = ExternalReservationDraft(
        id=str(uuid4()),
        journey_id=journey.id,
        artifact_type="IMAGE",
        raw_payload_json=json.dumps({"image_source": "redacted_external_reference"}),
        extracted_json=json.dumps(extracted, ensure_ascii=False),
        unresolved_fields_json=json.dumps(unresolved),
        extraction_mode="DEEPSEEK_RESPONSES_VISION",
        status="READY_FOR_CONFIRMATION" if not unresolved else "NEEDS_REVIEW",
        created_at=datetime.now(timezone.utc).isoformat(),
        confirmed_at=None,
    )
    session.add(draft)
    session.commit()
    return {"status": "READY", "draft": _draft_payload(draft), "provider": "deepseek-vision"}


@app.patch("/api/v1/journeys/{journey_id}/inbox/{draft_id}")
def patch_journey_reservation_draft(
    journey_id: UUID,
    draft_id: UUID,
    payload: ReservationDraftPatchRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    draft = session.get(ExternalReservationDraft, str(draft_id))
    if draft is None or draft.journey_id != journey.id:
        raise HTTPException(404, "reservation draft was not found")
    if draft.status == "CONFIRMED":
        raise HTTPException(409, "confirmed reservation drafts require a new correction artifact")
    extracted = json.loads(draft.extracted_json or "{}")
    changes = payload.model_dump(exclude_unset=True)
    if any(
        key in changes
        for key in ("anchor_role", "semantic_node_key", "semantic_target")
    ):
        extracted["_semantic_contract"] = "V13.2"
    if "anchor_role" in changes and changes["anchor_role"] in {
        "ARRIVAL",
        "DEPARTURE",
        "MID_TRIP",
    }:
        extracted["anchor_role_confidence"] = 1.0
        extracted["uncertain_fields"] = [
            item
            for item in extracted.get("uncertain_fields", [])
            if item != "anchor_role"
        ]
        provenance = dict(extracted.get("field_provenance") or {})
        provenance["anchor_role"] = {"source": "USER", "status": "CORRECTED"}
        extracted["field_provenance"] = provenance
    extracted.update(changes)
    draft.extracted_json = json.dumps(extracted, ensure_ascii=False)
    _refresh_draft_semantics(session, journey, draft)
    session.commit()
    return _draft_payload(draft)


@app.post("/api/v1/journeys/{journey_id}/inbox/{draft_id}/smart-apply")
def smart_apply_journey_reservation(
    journey_id: UUID,
    draft_id: UUID,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    draft = session.get(ExternalReservationDraft, str(draft_id))
    if draft is None or draft.journey_id != journey.id:
        raise HTTPException(404, "reservation draft was not found")
    extracted = _refresh_draft_semantics(session, journey, draft)
    smart = extracted.get("smart_intake", {})
    decision = smart.get("decision") or "NEEDS_REVIEW"
    if draft.unresolved_fields_json != "[]" or decision not in {
        "AUTO_APPLY",
        "APPLY_WITH_NOTICE",
    }:
        session.commit()
        return {
            "status": decision,
            "decision": decision,
            "draft": _draft_payload(draft),
        }
    try:
        reservation = confirm_reservation_draft(session, journey, draft)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    session.commit()
    return {
        "status": "APPLIED",
        "decision": decision,
        "draft": _draft_payload(draft),
        "reservation": _reservation_payload(reservation),
        "commitment": _commitment_payload(
            require(session, CommitmentModel, reservation.commitment_id, "Commitment")
        ),
        "memory": journey_memory_payload(session, journey),
    }


@app.post("/api/v1/journeys/{journey_id}/web-research")
def run_journey_web_research(
    journey_id: UUID,
    payload: WebResearchRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    client = _deepseek_client()
    if client is None or not settings.deepseek_web_search_enabled:
        return {
            "status": "NOT_CONFIGURED",
            "journey_id": journey.id,
            "observations": [],
            "authority": "NON_AUTHORITATIVE",
        }
    try:
        drafts = WebResearchProvider(client).search(payload.query, source_class=payload.source_class)
    except DeepSeekResponsesError as exc:
        return {
            "status": "FAILED_EXTERNAL",
            "journey_id": journey.id,
            "observations": [],
            "authority": "NON_AUTHORITATIVE",
            "reason": str(exc),
        }
    rows: list[WebObservation] = []
    for item in drafts:
        existing = session.scalar(
            select(WebObservation).where(
                WebObservation.journey_id == journey.id,
                WebObservation.evidence_fingerprint == item.evidence_fingerprint,
            )
        )
        if existing is None:
            existing = WebObservation(
                id=str(uuid4()),
                journey_id=journey.id,
                query=item.query,
                url=item.url,
                domain=item.domain,
                title=item.title,
                source_class=item.source_class,
                provider_key=item.provider_key,
                model_key=item.model_key,
                captured_at=item.captured_at,
                evidence_fingerprint=item.evidence_fingerprint,
                content_excerpt=item.content_excerpt,
                authority_status="NON_AUTHORITATIVE",
                created_at=item.captured_at,
            )
            session.add(existing)
        rows.append(existing)
    session.commit()
    return {
        "status": "CAPTURED" if rows else "NO_RESULTS",
        "journey_id": journey.id,
        "authority": "NON_AUTHORITATIVE",
        "observations": [
            {
                "id": item.id,
                "query": item.query,
                "url": item.url,
                "domain": item.domain,
                "title": item.title,
                "source_class": item.source_class,
                "provider_key": item.provider_key,
                "model": item.model_key,
                "captured_at": item.captured_at,
                "evidence_fingerprint": item.evidence_fingerprint,
                "authority_status": item.authority_status,
            }
            for item in rows
        ],
    }


@app.get("/api/v1/journeys/{journey_id}/web-observations")
def list_journey_web_observations(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(WebObservation)
        .where(WebObservation.journey_id == journey.id)
        .order_by(WebObservation.captured_at.desc())
    ).all()
    return {
        "journey_id": journey.id,
        "authority": "NON_AUTHORITATIVE",
        "observations": [
            {
                "id": item.id,
                "query": item.query,
                "url": item.url,
                "domain": item.domain,
                "title": item.title,
                "source_class": item.source_class,
                "provider_key": item.provider_key,
                "model": item.model_key,
                "captured_at": item.captured_at,
                "evidence_fingerprint": item.evidence_fingerprint,
                "authority_status": item.authority_status,
            }
            for item in rows
        ],
    }


@app.get("/api/v1/journeys/{journey_id}/execution-clock")
def get_journey_execution_clock(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    now = execution_clock.now(journey.timezone)
    return {
        "journey_id": journey.id,
        "now": now.isoformat(),
        "timezone": journey.timezone,
        "source": "EXECUTION_CLOCK",
        "current_activity_id": journey.current_activity_id,
    }


@app.post("/api/v1/journeys/{journey_id}/inbox/{draft_id}/confirm")
def confirm_journey_reservation(
    journey_id: UUID, draft_id: UUID, session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    draft = session.get(ExternalReservationDraft, str(draft_id))
    if draft is None or draft.journey_id != journey.id:
        raise HTTPException(404, "reservation draft was not found")
    try:
        extracted = _refresh_draft_semantics(session, journey, draft)
        smart = extracted.get("smart_intake", {})
        if "DUPLICATE_CONFIRMATION_REF" in smart.get("conflicts", []):
            raise ValueError("DUPLICATE_CONFIRMATION_REF: reservation already exists in this Journey")
        reservation = confirm_reservation_draft(session, journey, draft)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    session.commit()
    return {
        "reservation": _reservation_payload(reservation),
        "commitment": _commitment_payload(
            require(session, CommitmentModel, reservation.commitment_id, "Commitment")
        ),
    }


@app.get("/api/v1/journeys/{journey_id}/wallet")
def get_travel_wallet(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    reservations = session.scalars(
        select(TransportReservation)
        .where(TransportReservation.journey_id == journey.id)
        .order_by(TransportReservation.scheduled_arrival_at)
    ).all()
    commitments = session.scalars(
        select(CommitmentModel)
        .where(CommitmentModel.journey_id == journey.id)
        .order_by(CommitmentModel.created_at)
    ).all()
    return {
        "journey_id": journey.id,
        "reservations": [_reservation_payload(item) for item in reservations],
        "commitments": [_commitment_payload(item) for item in commitments],
        "offline_ready": session.get(OfflineJourneySnapshot, journey.id) is not None,
    }


@app.post("/api/v1/journeys/{journey_id}/reservations/{reservation_id}/schedule-change")
def apply_reservation_schedule_change(
    journey_id: UUID,
    reservation_id: UUID,
    payload: ScheduleChangeRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    reservation = session.get(TransportReservation, str(reservation_id))
    if reservation is None or reservation.journey_id != journey.id:
        raise HTTPException(404, "transport reservation was not found")
    captured_at = payload.captured_at.astimezone(timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - captured_at).total_seconds()
    reservation.estimated_arrival_at = payload.estimated_arrival_at.isoformat()
    reservation.status = payload.status
    reservation.realtime_status = "STALE_REALTIME" if age_seconds > 300 else payload.status
    event = EventModel(
        id=str(uuid4()),
        journey_id=journey.id,
        provider_key=payload.provider_key,
        provenance="PROVIDER_VERIFIED",
        event_type="SCHEDULE_DELAY",
        severity="CRITICAL" if payload.status == "CANCELLED" else "MAJOR",
        status="DETECTED",
        affected_activity_id=None,
        occurred_at=payload.captured_at.isoformat(),
        detected_at=datetime.now(timezone.utc).isoformat(),
        resolved_at=None,
        payload_json=json.dumps(
            {
                "reservation_id": reservation.id,
                "estimated_arrival_at": reservation.estimated_arrival_at,
                "realtime_status": reservation.realtime_status,
                "service_alert": payload.service_alert,
                "wake_guardian": True,
                "journey_risk": "CRITICAL" if payload.status == "CANCELLED" else "AT_RISK",
            },
            ensure_ascii=False,
        ),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(event)
    notification = notify(
        session,
        journey.id,
        dedupe_key=f"schedule-change:{reservation.id}:{payload.captured_at.isoformat()}",
        kind="SCHEDULE_CHANGE",
        priority="CRITICAL" if payload.status == "CANCELLED" else "HIGH",
        payload={"reservation_id": reservation.id, "event_id": event.id},
    )
    record_audit(
        session,
        action="long_distance.schedule_changed",
        entity_type="TransportReservation",
        entity_id=reservation.id,
        journey_id=journey.id,
        after={"event_id": event.id, "realtime_status": reservation.realtime_status},
    )
    if journey.active_plan_version_id:
        refresh_offline_snapshot(session, journey)
    session.commit()
    return {
        "reservation": _reservation_payload(reservation),
        "event_id": event.id,
        "notification_id": notification.id,
        "guardian_wakeup": True,
        "journey_risk": "CRITICAL" if payload.status == "CANCELLED" else "AT_RISK",
        "risk_reason_codes": [
            "LONG_DISTANCE_CANCELLED"
            if payload.status == "CANCELLED"
            else "LONG_DISTANCE_SCHEDULE_CHANGED",
            *(["SERVICE_ALERT"] if payload.service_alert else []),
        ],
    }


@app.get("/api/v1/journeys/{journey_id}/offline-snapshot")
def get_offline_journey_snapshot(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    row = session.get(OfflineJourneySnapshot, journey.id)
    if row is None:
        row = refresh_offline_snapshot(session, journey)
        session.commit()
    return {
        "journey_id": row.journey_id,
        "sequence": row.sequence,
        "valid_until": row.valid_until,
        "snapshot": json.loads(row.payload_json),
        "provider_freshness": json.loads(row.provider_freshness_json),
        "updated_at": row.updated_at,
    }


@app.post("/api/v1/journeys/{journey_id}/location", status_code=201)
def post_foreground_location(
    journey_id: UUID,
    payload: LocationObservationRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    try:
        row = record_location(
            session,
            journey,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy_m=payload.accuracy_m,
            captured_at=payload.captured_at.isoformat(),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    session.commit()
    return {
        "id": row.id,
        "journey_id": row.journey_id,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "accuracy_m": row.accuracy_m,
        "captured_at": row.captured_at,
        "source": row.source,
        "background_tracking_claimed": False,
    }


@app.post("/api/v1/travelers/{traveler_id}/push-subscriptions", status_code=201)
def create_push_subscription(
    traveler_id: UUID,
    payload: PushSubscriptionRequest,
    session: Session = Depends(get_session),
):
    traveler = require(session, Traveler, str(traveler_id), "Traveler")
    try:
        row = register_push_subscription(session, traveler.id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    session.commit()
    return {"id": row.id, "status": row.status, "endpoint_hash": row.endpoint_hash}


@app.get("/api/v1/travelers/{traveler_id}/push-config")
def get_push_config(traveler_id: UUID, session: Session = Depends(get_session)):
    traveler = require(session, Traveler, str(traveler_id), "Traveler")
    return {
        "traveler_id": traveler.id,
        "capability": push_capability(),
        "public_key": settings.vapid_public_key,
        "record_fallback": True,
    }


@app.get("/api/v1/journeys/{journey_id}/notifications")
def list_journey_notifications(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(NotificationEvent)
        .where(NotificationEvent.journey_id == journey.id)
        .order_by(NotificationEvent.created_at.desc())
    ).all()
    return {
        "journey_id": journey.id,
        "notifications": [
            {
                "id": item.id,
                "kind": item.kind,
                "priority": item.priority,
                "status": item.status,
                "payload": json.loads(item.payload_json),
                "delivery_channels": json.loads(item.delivery_channels_json),
                "occurrence_count": item.occurrence_count,
                "created_at": item.created_at,
            }
            for item in rows
        ],
    }


@app.get("/api/v1/providers/v9")
def get_v9_provider_status():
    amap = amap_status()
    return {
        "region_selection": {
            "CN-*": provider_for_region("CN-TIANJIN"),
            "global": provider_for_region("US-NYC"),
        },
        "amap": {
            "provider_key": amap.provider_key,
            "status": amap.status,
            "provenance": amap.provenance,
            "coordinate_crs": amap.coordinate_crs,
            "reason": amap.reason,
        },
        "transit_realtime": {"status": "NOT_CONFIGURED", "absence_semantics": "UNKNOWN_REALTIME"},
        "otp": {"status": "NOT_CONFIGURED"},
        "duffel": {"status": "NOT_CONFIGURED"},
    }


@app.post("/api/v1/journeys/{journey_id}/edge/devices", status_code=201)
def create_edge_device(
    journey_id: UUID,
    payload: EdgeDeviceCreateRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    device, token = register_edge_device(session, journey, display_name=payload.display_name)
    session.commit()
    return {
        "device_id": device.id,
        "device_token": token,
        "token_returned_once": True,
        "scopes": json.loads(device.scopes_json),
    }


def _authorized_edge(session: Session, device_id: UUID, token: str | None) -> EdgeDevice:
    device = session.get(EdgeDevice, str(device_id))
    if device is None or not token or not authenticate_edge(device, token):
        raise HTTPException(401, "invalid Edge Companion credentials")
    return device


@app.get("/api/v1/edge/devices/{device_id}/journey-snapshot")
def get_edge_journey_snapshot(
    device_id: UUID,
    x_edge_token: str | None = Header(default=None, alias="X-Edge-Token"),
    session: Session = Depends(get_session),
):
    device = _authorized_edge(session, device_id, x_edge_token)
    try:
        payload = edge_snapshot(session, device)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    session.commit()
    return payload


@app.post("/api/v1/edge/devices/{device_id}/actions", status_code=201)
def post_edge_action(
    device_id: UUID,
    payload: EdgeActionRequest,
    x_edge_token: str | None = Header(default=None, alias="X-Edge-Token"),
    session: Session = Depends(get_session),
):
    device = _authorized_edge(session, device_id, x_edge_token)
    try:
        row = record_edge_action(session, device, action=payload.action, payload=payload.payload)
    except ValueError as exc:
        raise HTTPException(403, str(exc)) from exc
    session.commit()
    return {"id": row.id, "action": row.action, "status": row.status}


@app.post("/api/v1/edge/devices/{device_id}/observations", status_code=201)
def post_edge_observation(
    device_id: UUID,
    payload: EdgeObservationRequest,
    x_edge_token: str | None = Header(default=None, alias="X-Edge-Token"),
    session: Session = Depends(get_session),
):
    device = _authorized_edge(session, device_id, x_edge_token)
    try:
        row = record_edge_observation(
            session,
            device,
            observation_type=payload.observation_type,
            payload=payload.payload,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    session.commit()
    return {"id": row.id, "observation_type": row.observation_type, "recorded": True}


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
        plans = generate_plans(
            session,
            journey,
            planning_mode,
            request.candidate_count,
            place_ids=request.place_ids,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return [plan_schema(session, plan) for plan in plans]


@app.post("/api/v1/journeys/{journey_id}/plans/authoritative-compose", status_code=201)
@app.post("/api/v1/journeys/{journey_id}/authoritative-compose", status_code=201)
def authoritative_compose_journey(
    journey_id: UUID,
    payload: AuthoritativeComposeRequest,
    session: Session = Depends(get_session),
):
    """Compose bounded multi-day candidates from actual user-selected POIs."""

    journey = require(session, Journey, str(journey_id), "Journey")
    try:
        result = compose_authoritative_multiday(
            session,
            journey,
            place_ids=payload.place_ids,
            candidate_count=payload.candidate_count,
            stay_offer_id=str(payload.stay_offer_id) if payload.stay_offer_id else None,
            reservation_id=str(payload.reservation_id) if payload.reservation_id else None,
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc
    return {
        "optimizer": result.optimizer_kind,
        "complete_plan_count": len(result.plans),
        "frozen_evidence_ids": list(result.evidence_ids),
        "stay_offer_id": result.stay_offer.id if result.stay_offer else None,
        "top_k": [plan_schema(session, plan) for plan in result.plans],
    }


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
    evidence_payload = json.loads(plan.mobility_evidence_json or "{}")
    if not evidence_payload.get("snapshot_id"):
        raise HTTPException(409, "STALE_RECOMPOSE_REQUIRED: PlanVersion has no frozen provider evidence")
    expires_at = evidence_payload.get("expires_at")
    if expires_at:
        try:
            if datetime.fromisoformat(str(expires_at)) <= datetime.now(timezone.utc):
                raise HTTPException(409, "STALE_RECOMPOSE_REQUIRED: PlanVersion evidence expired")
        except ValueError:
            raise HTTPException(409, "STALE_RECOMPOSE_REQUIRED: PlanVersion evidence timestamp invalid") from None
    selection_snapshot = MobilitySnapshot.from_evidence(evidence_payload)
    if selection_snapshot.snapshot_id != plan.mobility_snapshot_id:
        raise HTTPException(409, "STALE_RECOMPOSE_REQUIRED: PlanVersion evidence reference is inconsistent")
    gate = evaluate_feasibility(
        build_context(
            journey,
            constraints,
            places,
            services,
            mobility_provider=selection_snapshot,
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
    # Bind durable commitments to the selected PlanVersion's canonical
    # Activity row.  The semantic key remains the cross-version identity; the
    # FK is the concrete execution anchor consumed by JourneyTwin, Trip
    # Studio, and recovery remapping.
    selected_commitments = session.scalars(
        select(CommitmentModel).where(
            CommitmentModel.journey_id == journey.id,
            CommitmentModel.status == "ACTIVE",
            CommitmentModel.level.in_(("C3_Guaranteed", "C4_Anchored")),
        )
    ).all()
    for commitment in selected_commitments:
        policy = _json_object(commitment.policy_json, {})
        semantic_key = str(policy.get("semantic_key") or "")
        match = next(
            (
                item
                for item in activities
                if semantic_key
                and (
                    item.place_id == semantic_key
                    or item.city_service_id == semantic_key
                    or str(_json_object(item.metadata_json, {}).get("semantic_key") or "") == semantic_key
                    or str(_json_object(item.metadata_json, {}).get("semantic_key") or "").endswith(f":{semantic_key}")
                )
            ),
            None,
        )
        if match is not None:
            commitment.activity_id = match.id
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


def _trip_studio_context(
    session: Session,
    journey: Journey,
    requested_ids: list[str],
) -> tuple[PlanVersion, list[Activity], list[Activity], dict[str, Any]]:
    """Resolve an edit against the current plan and the immutable evidence snapshot."""

    if not journey.active_plan_version_id:
        raise HTTPException(409, "Trip Studio requires an active plan")
    plan = session.get(PlanVersion, journey.active_plan_version_id)
    if plan is None or plan.journey_id != journey.id:
        raise HTTPException(409, "Trip Studio active plan is inconsistent")
    expected_status = "ACTIVE" if journey.status == "ACTIVE" else "SELECTED"
    if plan.status != expected_status:
        raise HTTPException(409, "TRIP_STUDIO_BASE_PLAN_STALE")
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan.id).order_by(Activity.sequence_no)
    ).all()
    canonical_ids = [item.id for item in activities]
    if len(requested_ids) != len(set(requested_ids)) or set(requested_ids) != set(canonical_ids):
        raise HTTPException(422, "TRIP_STUDIO_REQUIRES_FULL_ACTIVE_PLAN_ORDER")
    by_id = {item.id: item for item in activities}
    ordered = [by_id[item] for item in requested_ids]
    locked_positions = [item.id for item in activities if item.locked]
    proposed_locked_positions = [item.id for item in ordered if item.locked]
    protected_ok = locked_positions == proposed_locked_positions and all(
        activities[index].id == ordered[index].id
        for index in range(len(activities))
        if activities[index].locked
    )
    execution_failures: list[str] = []
    if journey.status == "ACTIVE":
        current_index = next(
            (index for index, item in enumerate(activities) if item.id == journey.current_activity_id),
            None,
        )
        if current_index is None:
            execution_failures.append("CURRENT_ACTIVITY_MISSING")
        else:
            immutable_prefix = canonical_ids[: current_index + 1]
            if requested_ids[: current_index + 1] != immutable_prefix:
                execution_failures.append("EXECUTED_PREFIX_REORDER")
            if requested_ids[current_index] != journey.current_activity_id:
                execution_failures.append("CURRENT_ACTIVITY_REORDER")
        for index, item in enumerate(activities):
            if item.status in {"COMPLETED", "SKIPPED"} and requested_ids[index] != item.id:
                execution_failures.append("EXECUTION_HISTORY_REORDER")
    evidence = _json_object(plan.mobility_evidence_json, {})
    fact_pairs = {
        (str(item.get("origin_key")), str(item.get("destination_key"))): item
        for item in evidence.get("facts", [])
        if isinstance(item, dict) and item.get("origin_key") and item.get("destination_key")
    }
    route_gaps = []
    for previous, current in zip(ordered, ordered[1:]):
        pair = (str(previous.place_id or previous.city_service_id or ""), str(current.place_id or current.city_service_id or ""))
        if pair not in fact_pairs:
            route_gaps.append({"from": pair[0], "to": pair[1]})
    changed = canonical_ids != requested_ids
    authoritative_gate = _trip_studio_authoritative_gate(
        session,
        journey,
        plan,
        ordered,
        activities,
        evidence,
    )
    gate_failures = list(execution_failures)
    if not protected_ok:
        gate_failures.append("PROTECTED_ACTIVITY_REORDER")
    if route_gaps:
        gate_failures.append("FROZEN_ROUTE_EVIDENCE_MISSING")
    gate_failures.extend(authoritative_gate["failures"])
    gate_failures = list(dict.fromkeys(gate_failures))
    impact = {
        "changed": changed,
        "changed_activity_ids": [item for item in requested_ids if item != canonical_ids[requested_ids.index(item)]] if changed else [],
        "protected_activity_ids": locked_positions,
        "protected_commitments_preserved": protected_ok and not execution_failures,
        "route_evidence_gaps": route_gaps,
        "time_delta_min": authoritative_gate["time_delta_min"],
        "cost_delta_minor": authoritative_gate["cost_delta_minor"],
        "risk_class": "LOW" if not gate_failures else "BLOCKED",
    }
    gate = {
        "status": "PASSED" if not gate_failures else "FAILED",
        "failures": gate_failures,
        "evidence_snapshot_id": plan.mobility_snapshot_id,
        "authoritative": True,
        "evidence_valid": authoritative_gate["evidence_valid"],
    }
    return plan, activities, ordered, {
        "impact": impact,
        "gate": gate,
        "evidence": evidence,
        "authoritative_gate": authoritative_gate,
    }


def _trip_studio_fact(
    from_key: str,
    to_key: str,
    evidence: dict[str, Any],
) -> dict[str, Any] | None:
    """Select one fact from the persisted immutable evidence matrix."""

    selected = [
        dict(item)
        for item in evidence.get("selected_facts", [])
        if isinstance(item, dict)
        and str(item.get("origin_key")) == from_key
        and str(item.get("destination_key")) == to_key
    ]
    matrix = [
        dict(item)
        for item in evidence.get("facts", [])
        if isinstance(item, dict)
        and str(item.get("origin_key")) == from_key
        and str(item.get("destination_key")) == to_key
    ]
    candidates = selected + matrix
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: (
            0 if item in selected else 1,
            str(item.get("cost_status") or "UNKNOWN") == "UNKNOWN",
            int(item.get("duration_min", item.get("minutes", 0)) or 0),
            int(item.get("cost_amount_minor") or 0),
            str(item.get("mode") or ""),
        ),
    )


def _trip_studio_authoritative_gate(
    session: Session,
    journey: Journey,
    plan: PlanVersion,
    ordered: list[Activity],
    slots: list[Activity],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Run the shared deterministic gate over a Trip Studio frozen snapshot."""

    failures: list[str] = []
    evidence_valid = bool(evidence.get("snapshot_id")) and evidence.get("snapshot_id") == plan.mobility_snapshot_id
    if not evidence_valid:
        failures.append("FROZEN_EVIDENCE_ID_MISMATCH")
    integrity_hash = evidence.get("integrity_hash")
    if integrity_hash:
        integrity_payload = dict(evidence)
        integrity_payload.pop("integrity_hash", None)
        computed_hash = hashlib.sha256(
            json.dumps(
                integrity_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        if computed_hash != str(integrity_hash):
            failures.append("FROZEN_EVIDENCE_INTEGRITY_MISMATCH")
            evidence_valid = False
    expires_at = evidence.get("expires_at")
    if expires_at:
        try:
            if datetime.fromisoformat(str(expires_at)) <= datetime.now(timezone.utc):
                failures.append("STALE_FROZEN_EVIDENCE")
                evidence_valid = False
        except ValueError:
            failures.append("INVALID_FROZEN_EVIDENCE_EXPIRY")
            evidence_valid = False

    frozen_minutes: dict[tuple[str, str], int] = {}
    frozen_facts: list[dict[str, Any]] = []
    feasibility_activities: list[FeasibilityActivity] = []
    for index, activity in enumerate(ordered):
        slot = slots[index]
        previous = ordered[index - 1] if index else None
        travel_min = 0
        if previous is not None:
            from_key = str(previous.place_id or previous.city_service_id or "")
            to_key = str(activity.place_id or activity.city_service_id or "")
            fact = _trip_studio_fact(from_key, to_key, evidence)
            if fact is None:
                failures.append(f"MOBILITY_DATA_UNAVAILABLE:{from_key}|{to_key}")
            else:
                travel_min = int(fact.get("duration_min", fact.get("minutes", 0)) or 0)
                frozen_minutes[(from_key, to_key)] = travel_min
                frozen_facts.append(fact)
                if str(fact.get("cost_status") or "UNKNOWN") == "UNKNOWN" and fact.get("cost_amount_minor") is None:
                    failures.append(f"UNKNOWN_MOBILITY_COST:{from_key}|{to_key}")
                if fact.get("currency") and str(fact["currency"]).upper() != str(journey.budget_currency).upper():
                    failures.append(f"MOBILITY_CURRENCY_MISMATCH:{from_key}|{to_key}")
        try:
            start_at = datetime.fromisoformat(slot.start_at)
            end_at = datetime.fromisoformat(slot.end_at)
        except ValueError:
            failures.append(f"INVALID_ACTIVITY_WINDOW:{activity.id}")
            continue
        feasibility_activities.append(
            FeasibilityActivity(
                key=str(activity.place_id or activity.city_service_id or activity.id),
                start_at=start_at,
                end_at=end_at,
                cost_minor=int(activity.estimated_cost_minor),
                place_id=activity.place_id,
                city_service_id=activity.city_service_id,
                currency=activity.currency,
                travel_from_prev_min=travel_min,
                locked=bool(activity.locked),
            )
        )

    try:
        constraints = list(
            session.scalars(select(JourneyConstraint).where(JourneyConstraint.journey_id == journey.id)).all()
        )
        commitments = list(
            session.scalars(
                select(CommitmentModel).where(
                    CommitmentModel.journey_id == journey.id,
                    CommitmentModel.status == "ACTIVE",
                    CommitmentModel.level == "C4_Anchored",
                )
            ).all()
        )
        constraints.extend(active_c4_hard_constraints(commitments))
    except ValueError:
        failures.append("INVALID_C4_COMMITMENT_POLICY")
        constraints = []
    places = {
        item.id: item
        for item in session.scalars(select(Place).where(Place.city_code == journey.city_code)).all()
    }
    services = {
        item.id: item
        for item in session.scalars(select(CityService).where(CityService.city_code == journey.city_code)).all()
    }
    frozen_provider = MobilitySnapshot.from_minutes(
        source_provider_key=str(evidence.get("source_provider") or "frozen-plan-evidence"),
        minutes=frozen_minutes,
        captured_at=str(evidence.get("captured_at") or datetime.now(timezone.utc).isoformat()),
        snapshot_id=str(evidence.get("snapshot_id") or plan.mobility_snapshot_id or ""),
        operation_key=str(evidence.get("operation_key") or "trip-studio"),
    )
    gate = evaluate_feasibility(
        build_context(
            journey,
            constraints,
            places,
            services,
            mobility_provider=frozen_provider,
            plan_currency=plan.currency,
        ),
        feasibility_activities,
    )
    failures.extend(gate.failures)
    activity_duration = sum(
        int((datetime.fromisoformat(item.end_at) - datetime.fromisoformat(item.start_at)).total_seconds() // 60)
        for item in slots
    )
    route_duration = sum(int(item.get("duration_min", item.get("minutes", 0)) or 0) for item in frozen_facts)
    base_duration = activity_duration + route_duration
    base_cost = sum(int(item.estimated_cost_minor) for item in ordered) + sum(
        int(item.get("cost_amount_minor") or 0) for item in frozen_facts
    )
    time_delta = base_duration - int(plan.estimated_duration_min or 0)
    cost_delta = base_cost - int(plan.total_cost_minor or 0)
    return {
        "failures": list(dict.fromkeys(failures)),
        "evidence_valid": evidence_valid,
        "time_delta_min": time_delta,
        "cost_delta_minor": cost_delta,
        "frozen_facts": frozen_facts,
        "frozen_provider": frozen_provider,
        "mobility_cost_minor": sum(int(item.get("cost_amount_minor") or 0) for item in frozen_facts),
        "total_cost_minor": base_cost,
        "estimated_duration_min": base_duration,
    }


def _trip_studio_preview_payload(
    journey: Journey,
    plan: PlanVersion,
    requested_ids: list[str],
    details: dict[str, Any],
) -> dict[str, Any]:
    signature = json.dumps(
        {"plan_id": plan.id, "evidence_id": plan.mobility_snapshot_id, "draft_order": requested_ids},
        sort_keys=True,
    )
    authoritative_gate = details["authoritative_gate"]
    return {
        "preview_id": str(uuid5(NAMESPACE_URL, f"citynexus-v13-trip-studio:{signature}")),
        "journey_id": journey.id,
        "base_plan_version_id": plan.id,
        "draft_order": requested_ids,
        "impact": details["impact"],
        "deterministic_gate": details["gate"],
        "evidence_snapshot_id": details["gate"]["evidence_snapshot_id"],
        "authoritative_gate": {
            "failures": authoritative_gate["failures"],
            "evidence_valid": authoritative_gate["evidence_valid"],
            "time_delta_min": authoritative_gate["time_delta_min"],
            "cost_delta_minor": authoritative_gate["cost_delta_minor"],
            "frozen_facts": authoritative_gate["frozen_facts"],
            "mobility_cost_minor": authoritative_gate["mobility_cost_minor"],
            "total_cost_minor": authoritative_gate["total_cost_minor"],
            "estimated_duration_min": authoritative_gate["estimated_duration_min"],
        },
        "can_accept": details["gate"]["status"] == "PASSED",
        "mutation": "NO_ACTIVE_PLAN_MUTATION",
    }


@app.post("/api/v1/journeys/{journey_id}/trip-studio/preview")
@app.post("/api/v1/journeys/{journey_id}/plans/preview-reorder")
def trip_studio_preview(
    journey_id: UUID,
    payload: TripStudioPreviewRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    requested_ids = [str(item) for item in (payload.draft_order or payload.activity_ids)]
    plan, _activities, _ordered, details = _trip_studio_context(session, journey, requested_ids)
    return _trip_studio_preview_payload(journey, plan, requested_ids, details)


def _trip_studio_accept_impl(
    journey_id: UUID,
    payload: TripStudioAcceptRequest,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    requested_ids = [str(item) for item in payload.activity_ids]
    base, activities, ordered, details = _trip_studio_context(session, journey, requested_ids)
    if details["gate"]["status"] != "PASSED":
        failures = ",".join(str(item) for item in details["gate"]["failures"])
        raise HTTPException(422, f"TRIP_STUDIO_DETERMINISTIC_GATE_FAILED:{failures}")
    if payload.preview_id:
        # The preview id binds the draft to the exact base PlanVersion and
        # frozen evidence identity. Accept still reruns the gate above.
        preview = _trip_studio_preview_payload(journey, base, requested_ids, details)
        if str(payload.preview_id) != preview["preview_id"]:
            raise HTTPException(409, "TRIP_STUDIO_PREVIEW_STALE")

    evidence = details["evidence"]
    authoritative_gate = details["authoritative_gate"]
    if not details["impact"]["changed"]:
        # A repeated accept of an unchanged order is a successful, auditable
        # no-op.  Do not create a new PlanVersion or reset the Journey's
        # identity merely because a client retried a harmless request.
        return JSONResponse(
            status_code=200,
            content={
                "plan": plan_schema(session, base).model_dump(mode="json"),
                "preview_id": str(payload.preview_id) if payload.preview_id else None,
                "impact": details["impact"],
                "deterministic_gate": details["gate"],
                "frozen_evidence_id": base.mobility_snapshot_id,
                "no_op": True,
            },
        )
    now = datetime.now(timezone.utc).isoformat()
    latest_version = int(
        session.scalar(
            select(PlanVersion.version_no)
            .where(PlanVersion.journey_id == journey.id)
            .order_by(PlanVersion.version_no.desc())
            .limit(1)
        )
        or 0
    )
    slots = activities
    score_breakdown = _json_object(base.score_breakdown_json, {})
    score_breakdown["mobility"] = authoritative_gate["mobility_cost_minor"]
    score_breakdown["total_cost_minor"] = authoritative_gate["total_cost_minor"]
    score_breakdown["estimated_duration_min"] = authoritative_gate["estimated_duration_min"]
    new_plan = PlanVersion(
        id=str(uuid4()),
        journey_id=journey.id,
        version_no=latest_version + 1,
        planning_mode=base.planning_mode,
        status="ACTIVE" if journey.status == "ACTIVE" else "SELECTED",
        source="MANUAL",
        parent_plan_version_id=base.id,
        total_cost_minor=authoritative_gate["total_cost_minor"],
        currency=base.currency,
        estimated_duration_min=authoritative_gate["estimated_duration_min"],
        utility_score=base.utility_score,
        score_breakdown_json=json.dumps(score_breakdown, sort_keys=True),
        explanation_json=json.dumps({
            "product_path": "V12_TRIP_STUDIO_ACCEPT",
            "base_plan_version_id": base.id,
            "draft_order": requested_ids,
            "deterministic_gate": details["gate"],
            "frozen_evidence_id": base.mobility_snapshot_id,
        }, sort_keys=True),
        mobility_snapshot_id=base.mobility_snapshot_id,
        mobility_evidence_json=base.mobility_evidence_json,
        created_at=now,
    )
    session.add(new_plan)
    session.flush()
    new_by_old: dict[str, str] = {}
    new_rows: list[Activity] = []
    for index, (source, slot) in enumerate(zip(ordered, slots), start=1):
        source_metadata = _json_object(source.metadata_json, {})
        source_metadata["trip_studio"] = {
            "base_activity_id": source.id,
            "accepted_at": now,
            "draft_order": requested_ids,
            "frozen_evidence_id": base.mobility_snapshot_id,
            "execution_status_before": source.status,
        }
        row = Activity(
            id=str(uuid4()),
            plan_version_id=new_plan.id,
            sequence_no=index,
            activity_type=source.activity_type,
            title=source.title,
            place_id=source.place_id,
            city_service_id=source.city_service_id,
            start_at=slot.start_at,
            end_at=slot.end_at,
            travel_from_prev_min=0,
            estimated_cost_minor=source.estimated_cost_minor,
            currency=source.currency,
            status=source.status,
            locked=source.locked,
            metadata_json=json.dumps(source_metadata, ensure_ascii=False, sort_keys=True),
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        new_rows.append(row)
        new_by_old[source.id] = row.id
    session.flush()

    new_legs: list[JourneyLeg] = []
    for index, (previous, current) in enumerate(zip(new_rows, new_rows[1:]), start=1):
        from_key = str(previous.place_id or previous.city_service_id or "")
        to_key = str(current.place_id or current.city_service_id or "")
        fact = _trip_studio_fact(from_key, to_key, evidence)
        if fact is None:
            session.rollback()
            raise HTTPException(422, "TRIP_STUDIO_FROZEN_ROUTE_FACT_MISSING")
        duration_min = int(fact.get("duration_min", fact.get("minutes", 0)) or 0)
        current.travel_from_prev_min = duration_min
        new_legs.append(
            JourneyLeg(
                id=str(uuid4()), journey_id=journey.id, plan_version_id=new_plan.id,
                sequence_no=index, from_activity_id=previous.id, to_activity_id=current.id,
                from_key=from_key, to_key=to_key, mode=str(fact.get("mode") or "UNKNOWN"),
                depart_at=previous.end_at, arrive_at=current.start_at,
                duration_min=duration_min, distance_m=int(fact.get("distance_m") or 0),
                cost_amount_minor=fact.get("cost_amount_minor"), currency=fact.get("currency"),
                cost_status=str(fact.get("cost_status") or "UNKNOWN"),
                walking_min=int(fact.get("walking_min") or 0),
                transfers=int(fact.get("transfers") or 0),
                reliability_score=float(fact.get("reliability_score") or 0.0),
                weather_exposure=str(fact.get("weather_exposure") or "UNKNOWN"),
                geometry_json=json.dumps(fact.get("geometry") or {"coordinates": fact.get("route_geometry") or []}, sort_keys=True),
                crs=str(fact.get("crs") or "WGS84"),
                provider_key=str(fact.get("provider_key") or fact.get("provider") or "frozen-plan-evidence"),
                provenance=str(fact.get("provenance") or evidence.get("aggregate_provenance") or "FROZEN_PLAN_EVIDENCE"),
                provider_snapshot_id=fact.get("fact_id"),
                captured_at=str(fact.get("captured_at") or evidence.get("captured_at") or now),
                expires_at=fact.get("expires_at") or evidence.get("expires_at"),
            )
        )
    session.add_all(new_legs)
    for commitment in session.scalars(
        select(CommitmentModel).where(
            CommitmentModel.journey_id == journey.id,
            CommitmentModel.status == "ACTIVE",
            CommitmentModel.activity_id.in_(list(new_by_old)),
        )
    ).all():
        commitment.activity_id = new_by_old.get(commitment.activity_id)
    base.status = "SUPERSEDED"
    next_current_activity_id = (
        new_by_old.get(journey.current_activity_id) if journey.status == "ACTIVE" else None
    )
    if journey.status == "ACTIVE" and next_current_activity_id is None:
        session.rollback()
        raise HTTPException(409, "TRIP_STUDIO_CURRENT_ACTIVITY_MAPPING_FAILED")
    # Compare-and-swap the active PlanVersion at the database boundary.  The
    # in-process lock above protects normal Windows retries; this predicate is
    # the cross-worker guard that rejects a stale writer after another process
    # has already replaced the same base plan.
    guarded = session.execute(
        update(Journey)
        .where(
            Journey.id == journey.id,
            Journey.active_plan_version_id == base.id,
        )
        .values(
            active_plan_version_id=new_plan.id,
            current_activity_id=next_current_activity_id,
            updated_at=now,
        )
    )
    if guarded.rowcount != 1:
        session.rollback()
        raise HTTPException(409, "TRIP_STUDIO_BASE_PLAN_STALE")
    journey.active_plan_version_id = new_plan.id
    journey.current_activity_id = next_current_activity_id
    journey.updated_at = now
    record_audit(
        session,
        action="trip_studio.accepted",
        entity_type="PlanVersion",
        entity_id=new_plan.id,
        journey_id=journey.id,
        before={"base_plan_version_id": base.id, "draft_order": [item.id for item in activities]},
        after={"new_plan_version_id": new_plan.id, "draft_order": requested_ids, "frozen_evidence_id": base.mobility_snapshot_id},
    )
    if journey.active_plan_version_id:
        refresh_offline_snapshot(session, journey)
    session.commit()
    return {
        "plan": plan_schema(session, new_plan),
        "preview_id": str(payload.preview_id) if payload.preview_id else None,
        "impact": details["impact"],
        "deterministic_gate": details["gate"],
        "frozen_evidence_id": base.mobility_snapshot_id,
    }


@app.post("/api/v1/journeys/{journey_id}/trip-studio/accept", status_code=201)
@app.post("/api/v1/journeys/{journey_id}/plans/accept-reorder", status_code=201)
def trip_studio_accept(
    journey_id: UUID,
    payload: TripStudioAcceptRequest,
    session: Session = Depends(get_session),
):
    # PlanVersion replacement is a single logical mutation.  Serialize the
    # in-process accept boundary so two browser retries cannot both derive a
    # new PlanVersion from the same active base before either commit lands.
    with _trip_studio_accept_lock:
        return _trip_studio_accept_impl(journey_id, payload, session)


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
        "amount_status": item.amount_status,
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
        "monetary_value_status": item.monetary_value_status,
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


def _proposal_mobility_snapshot(proposal: ReplanProposalModel) -> MobilitySnapshot | None:
    try:
        diff = json.loads(proposal.diff_json or "{}")
        payload = diff.get("verified_evidence", {}).get("mobility", {}).get("snapshot")
        if not isinstance(payload, dict):
            return None
        snapshot = MobilitySnapshot.from_evidence(payload)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return snapshot


def _latest_replan_mobility_snapshot(session: Session, journey_id: str) -> MobilitySnapshot | None:
    proposals = session.scalars(
        select(ReplanProposalModel)
        .where(ReplanProposalModel.journey_id == journey_id)
        .order_by(ReplanProposalModel.created_at.desc(), ReplanProposalModel.id.desc())
    ).all()
    for proposal in proposals:
        snapshot = _proposal_mobility_snapshot(proposal)
        if snapshot is not None and snapshot.facts:
            return snapshot
    return None


def _grounded_recovery_provider_aliases(
    source: list[Activity],
    places_by_id: dict[str, Place],
    provider_mobility: dict[str, Any],
) -> dict[str, str]:
    """Map the sealed provider reserve onto Journey-owned location keys."""

    aliases: dict[str, str] = {}
    for activity in source:
        location = activity.place_id or activity.city_service_id
        if not location:
            continue
        metadata = _json_object(activity.metadata_json, {})
        role = str(metadata.get("provider_route_role") or "").upper()
        if role == "ARRIVAL":
            aliases["anchor:arrival"] = str(location)
        elif role == "DEPARTURE":
            aliases["anchor:departure"] = str(location)

    place_by_external_id = {
        str(place.external_id): place.id
        for place in places_by_id.values()
        if place.external_id
    }
    for node in provider_mobility.get("nodes", []):
        if not isinstance(node, dict):
            continue
        provider_key = str(node.get("key") or "")
        if not provider_key:
            continue
        if node.get("place_id") and str(node["place_id"]) in places_by_id:
            aliases[provider_key] = str(node["place_id"])
            continue
        external_id = str(node.get("external_id") or "")
        if external_id and external_id in place_by_external_id:
            aliases[provider_key] = place_by_external_id[external_id]
    return aliases


def _grounded_recovery_reserve_snapshot(
    *,
    base_evidence: dict[str, Any],
    provider_mobility: dict[str, Any],
    aliases: dict[str, str],
    operation_key: str,
) -> MobilitySnapshot:
    """Promote the sealed Journey provider reserve for grounded recovery.

    The selected PlanVersion remains the immutable baseline. This creates a
    separate recovery snapshot that reuses only provider-captured reserve
    facts, while keeping the selected facts authoritative for existing pairs.
    """

    base = MobilitySnapshot.from_evidence(base_evidence)
    selected_modes = [
        str(item.get("mode") or "").upper()
        for item in base_evidence.get("selected_facts", [])
        if isinstance(item, dict) and item.get("mode")
    ]
    preferred_mode = max(set(selected_modes), key=selected_modes.count) if selected_modes else "AUTO"

    raw_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in provider_mobility.get("facts", []):
        if not isinstance(item, dict):
            continue
        origin = aliases.get(str(item.get("from_key") or ""))
        destination = aliases.get(str(item.get("to_key") or ""))
        if not origin or not destination or origin == destination:
            continue
        raw_by_pair.setdefault((origin, destination), []).append(item)

    facts: dict[tuple[str, str], TravelEstimateFact] = {}
    for pair, options in raw_by_pair.items():
        preferred = [
            item for item in options if str(item.get("mode") or "").upper() == preferred_mode
        ]
        chosen = min(preferred or options, key=lambda item: int(item.get("duration_min") or 0))
        facts[pair] = TravelEstimateFact(
            origin_key=pair[0],
            destination_key=pair[1],
            minutes=int(chosen.get("duration_min") or 0),
            provider_key=str(chosen.get("route_provider") or provider_mobility.get("provider") or "valhalla"),
            captured_at=str(chosen.get("captured_at") or provider_mobility.get("captured_at") or base.captured_at),
            route_provenance=str(chosen.get("route_provenance") or "CAPTURED_REPLAY"),
            cost_provenance=str(chosen.get("cost_provenance") or "CITYNEXUS_COST_ESTIMATE"),
            time_basis=str(chosen.get("time_basis") or "VALHALLA_SOURCES_TO_TARGETS_CAPTURED_AT"),
            distance_m=(
                round(float(chosen["distance_km"]) * 1000)
                if chosen.get("distance_km") is not None
                else None
            ),
        )

    for pair, fact in base.facts.items():
        facts[pair] = fact

    return MobilitySnapshot(
        facts=facts,
        source_provider_key=str(provider_mobility.get("provider") or base.source_provider_key),
        captured_at=str(provider_mobility.get("captured_at") or base.captured_at),
        degraded=False,
        snapshot_id="v14-grounded-recovery-"
        + hashlib.sha256(operation_key.encode("utf-8")).hexdigest()[:32],
        operation_key=operation_key,
        provider_capabilities=(
            dict(provider_mobility.get("provider_capabilities"))
            if isinstance(provider_mobility.get("provider_capabilities"), dict)
            else dict(base.provider_capabilities)
        ),
    )


def _incident_mobility_snapshot(payload: dict[str, Any]) -> MobilitySnapshot | None:
    """Read an explicitly sealed incident matrix supplied by the event."""

    recovery = payload.get("incident_recovery_evidence")
    if not isinstance(recovery, dict):
        recovery = payload.get("recovery_evidence")
    if not isinstance(recovery, dict):
        return None
    candidate = recovery.get("mobility_snapshot")
    if not isinstance(candidate, dict):
        mobility = recovery.get("mobility")
        candidate = mobility.get("snapshot") if isinstance(mobility, dict) else None
    if not isinstance(candidate, dict) or not candidate.get("facts"):
        return None
    return MobilitySnapshot.from_evidence(candidate)


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
    active_plan_legs = (
        session.scalars(
            select(JourneyLeg)
            .where(JourneyLeg.plan_version_id == active_plan_id)
            .order_by(JourneyLeg.sequence_no)
        ).all()
        if active_plan_id
        else []
    )
    execution = _execution_truth(activities, active_plan_legs, current_id)
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
    persisted_mobility = _latest_replan_mobility_snapshot(session, journey.id)
    mobility_context: dict[str, Any] = {
        "provider": "mock-mobility",
        "snapshot_id": None,
        "degraded": False,
        "source": "deterministic-offline",
    }
    next_buffer: int | None = None
    opportunity: dict[str, Any] | None = None
    if active_c4:
        next_start, policy = active_c4[0]
        current_key = current.place_id or current.city_service_id if current is not None else None
        target_key = str(policy.get("semantic_key") or "")
        travel_min = 0
        if current_key and target_key and current_key != target_key:
            fact = (
                persisted_mobility.facts.get((current_key, target_key))
                if persisted_mobility is not None
                else None
            )
            if fact is not None:
                travel_min = fact.minutes
                mobility_context = {
                    "provider": fact.provider_key,
                    "source_provider": persisted_mobility.source_provider_key,
                    "snapshot_id": persisted_mobility.snapshot_id,
                    "degraded": fact.degraded,
                    "snapshot_degraded": persisted_mobility.degraded,
                    "fallback_reason": fact.fallback_reason,
                    "source": "persisted-replan-snapshot",
                }
            else:
                travel_min = capture_runtime_mobility_snapshot(
                    session,
                    journey,
                    ((current_key, target_key),),
                    operation_key=f"commitment-window:{journey.id}",
                ).snapshot.estimate_minutes(current_key, target_key)
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
    if persisted_mobility is not None and persisted_mobility.degraded:
        degraded_items.add(persisted_mobility.source_provider_key)
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
        "mobility": mobility_context,
        "execution": execution,
    }
    snapshot_at = datetime.now(timezone.utc).isoformat()
    projection_status = "DEGRADED" if degraded else "READY"
    try:
        with session.begin_nested():
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
    except OperationalError as exc:
        detail = str(exc).casefold()
        if "database is locked" not in detail and "database is busy" not in detail:
            raise
        logger.warning("JourneyTwin cache write skipped during transient SQLite contention: %s", exc)
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
        _record_outcome_event(
            session,
            journey,
            activity=activities[0],
            event_type="ACTIVITY_STARTED",
            actor_type="SYSTEM",
        )
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
    refresh_offline_snapshot(session, journey)
    session.commit()
    return twin


def _transition_activity_state(
    journey_id: UUID,
    activity_id: UUID,
    target_state: str,
    event_type: str,
    session: Session,
):
    allowed_predecessors = {
        "EN_ROUTE": {"ACTIVE", "NOT_STARTED"},
        "ARRIVED": {"EN_ROUTE"},
        "IN_PROGRESS": {"ARRIVED"},
    }
    journey = require(session, Journey, str(journey_id), "Journey")
    if journey.status != "ACTIVE" or not journey.active_plan_version_id:
        raise HTTPException(409, "journey must be ACTIVE")
    activity = session.get(Activity, str(activity_id))
    if activity is None or activity.plan_version_id != journey.active_plan_version_id:
        raise HTTPException(409, "activity is not on the active plan")
    if journey.current_activity_id != activity.id:
        raise HTTPException(409, "activity is not the current activity")
    predecessors = allowed_predecessors.get(target_state, set())
    if activity.status not in predecessors:
        expected = ", ".join(sorted(predecessors)) or "none"
        raise HTTPException(
            409,
            f"INVALID_ACTIVITY_TRANSITION:{activity.status}->{target_state}; expected={expected}",
        )
    metadata = json.loads(activity.metadata_json or "{}")
    actual_key = {
        "EN_ROUTE": "en_route_at",
        "ARRIVED": "arrived_at",
        "IN_PROGRESS": "started_at_actual",
    }.get(target_state)
    if actual_key:
        captured_at = datetime.now(timezone.utc).isoformat()
        metadata[actual_key] = captured_at
        # Preserve the V11 names for existing consumers while exposing the
        # authoritative V12 execution contract.
        metadata[
            {
                "EN_ROUTE": "actual_departed_at",
                "ARRIVED": "actual_arrived_at",
                "IN_PROGRESS": "actual_started_at",
            }[target_state]
        ] = captured_at
    activity.metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    activity.status = target_state
    _record_outcome_event(session, journey, activity=activity, event_type=event_type, actor_type="USER")
    activity.updated_at = datetime.now(timezone.utc).isoformat()
    twin = _twin_snapshot(session, journey)
    refresh_offline_snapshot(session, journey)
    session.commit()
    return twin


def _is_authoritative_execution_plan(plan: PlanVersion | None) -> bool:
    """Identify the V12/V13 plan contract that owns the strict state graph.

    Older V4-V11 generated plans predate the execution-state API and existing
    clients still use their single-step completion command.  Keep that legacy
    compatibility boundary explicit while making every authoritative frozen
    plan use the server-owned predecessor graph below.
    """

    if plan is None:
        return False
    try:
        evidence = json.loads(plan.mobility_evidence_json or "{}")
    except json.JSONDecodeError:
        return False
    return str(evidence.get("normalizer_version") or "").startswith(
        ("citynexus-v12-authoritative-", "citynexus-v13-authoritative-")
    )


@app.post("/api/v1/journeys/{journey_id}/activities/{activity_id}/depart", response_model=JourneyTwinSchema)
def depart_activity(journey_id: UUID, activity_id: UUID, session: Session = Depends(get_session)):
    return _transition_activity_state(journey_id, activity_id, "EN_ROUTE", "ACTIVITY_DEPARTED", session)


@app.post("/api/v1/journeys/{journey_id}/activities/{activity_id}/arrive", response_model=JourneyTwinSchema)
def arrive_activity(journey_id: UUID, activity_id: UUID, session: Session = Depends(get_session)):
    return _transition_activity_state(journey_id, activity_id, "ARRIVED", "ACTIVITY_ARRIVED", session)


@app.post("/api/v1/journeys/{journey_id}/activities/{activity_id}/begin", response_model=JourneyTwinSchema)
def begin_activity(journey_id: UUID, activity_id: UUID, session: Session = Depends(get_session)):
    return _transition_activity_state(journey_id, activity_id, "IN_PROGRESS", "ACTIVITY_IN_PROGRESS", session)


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
    plan = session.get(PlanVersion, journey.active_plan_version_id)
    authoritative_execution = _is_authoritative_execution_plan(plan)
    if activity.status != "IN_PROGRESS":
        if not (
            not authoritative_execution
            and activity.status in {"ACTIVE", "EN_ROUTE", "ARRIVED"}
        ):
            raise HTTPException(
                409,
                f"INVALID_ACTIVITY_TRANSITION:{activity.status}->COMPLETED; expected=IN_PROGRESS",
            )
    activity.status = "COMPLETED"
    metadata = json.loads(activity.metadata_json or "{}")
    completed_at = datetime.now(timezone.utc).isoformat()
    metadata["completed_at_actual"] = completed_at
    if not authoritative_execution and metadata.get("execution_state") != "IN_PROGRESS":
        metadata["legacy_execution_compatibility"] = "DIRECT_COMPLETION_PRE_V12_CONTRACT"
    activity.metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    _record_outcome_event(
        session,
        journey,
        activity=activity,
        event_type="ACTIVITY_COMPLETED",
        actor_type="USER",
    )
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
        _record_outcome_event(
            session,
            journey,
            activity=next_activity,
            event_type="ACTIVITY_STARTED",
            actor_type="SYSTEM",
        )
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
    if journey.status == "COMPLETED":
        learn_from_journey(session, journey)
    refresh_offline_snapshot(session, journey)
    session.commit()
    return twin


@app.post(
    "/api/v1/journeys/{journey_id}/activities/{activity_id}/skip",
    response_model=JourneyTwinSchema,
)
def skip_activity(journey_id: UUID, activity_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    if journey.status != "ACTIVE" or not journey.active_plan_version_id:
        raise HTTPException(409, "journey must be ACTIVE")
    activity = session.get(Activity, str(activity_id))
    if activity is None or activity.plan_version_id != journey.active_plan_version_id:
        raise HTTPException(409, "activity is not on the active plan")
    if journey.current_activity_id != activity.id:
        raise HTTPException(409, "activity is not the current activity")
    if activity.status not in {"ACTIVE", "NOT_STARTED", "EN_ROUTE", "ARRIVED", "IN_PROGRESS"}:
        raise HTTPException(
            409,
            f"INVALID_ACTIVITY_TRANSITION:{activity.status}->SKIPPED",
        )
    protected_commitment = session.scalar(
        select(CommitmentModel).where(
            CommitmentModel.journey_id == journey.id,
            CommitmentModel.activity_id == activity.id,
            CommitmentModel.status == "ACTIVE",
            CommitmentModel.level.in_(("C3_Guaranteed", "C4_Anchored")),
        )
    )
    active_plan = session.get(PlanVersion, journey.active_plan_version_id)
    authoritative_locked = bool(activity.locked and _is_authoritative_execution_plan(active_plan))
    if authoritative_locked or protected_commitment is not None:
        raise HTTPException(409, "PROTECTED_COMMITMENT_CANNOT_BE_SKIPPED")
    activity.status = "SKIPPED"
    metadata = json.loads(activity.metadata_json or "{}")
    skipped_at = datetime.now(timezone.utc).isoformat()
    metadata["skipped_at"] = skipped_at
    activity.metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    _record_outcome_event(
        session,
        journey,
        activity=activity,
        event_type="ACTIVITY_SKIPPED",
        actor_type="USER",
    )
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
        learn_from_journey(session, journey)
    else:
        next_activity.status = "ACTIVE"
        journey.current_activity_id = next_activity.id
        _record_outcome_event(
            session,
            journey,
            activity=next_activity,
            event_type="ACTIVITY_STARTED",
            actor_type="SYSTEM",
        )
    journey.updated_at = datetime.now(timezone.utc).isoformat()
    record_audit(
        session,
        action="activity.skipped",
        entity_type="Activity",
        entity_id=activity.id,
        journey_id=journey.id,
        after={"status": activity.status, "next_activity_id": journey.current_activity_id},
    )
    twin = _twin_snapshot(session, journey)
    refresh_offline_snapshot(session, journey)
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


@app.post(
    "/api/v1/journeys/{journey_id}/weather/refresh",
    response_model=dict[str, Any],
)
async def refresh_journey_weather(
    journey_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
):
    if (await request.body()).strip():
        raise HTTPException(422, "weather refresh accepts no request body")
    journey = require(session, Journey, str(journey_id), "Journey")
    if journey.status != "ACTIVE":
        raise HTTPException(409, "weather refresh requires an active Journey")

    captured_at = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=settings.open_meteo_timeout_seconds) as client:
        result = await refresh_weather_runtime(
            session,
            journey,
            provider=build_open_meteo_provider(client),
            captured_at=captured_at,
        )
    session.commit()
    return result.to_evidence()


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


@app.get("/api/v1/journeys/{journey_id}/events/{event_id}/impact")
def get_event_impact(
    journey_id: UUID,
    event_id: UUID,
    session: Session = Depends(get_session),
):
    require(session, Journey, str(journey_id), "Journey")
    event = session.get(EventModel, str(event_id))
    if event is None or event.journey_id != str(journey_id):
        raise HTTPException(404, "Event was not found on this Journey")
    assessment = session.scalar(
        select(ImpactAssessment)
        .where(
            ImpactAssessment.event_id == event.id,
            ImpactAssessment.journey_id == str(journey_id),
        )
        .order_by(ImpactAssessment.created_at.desc(), ImpactAssessment.id.desc())
    )
    if assessment is None:
        raise HTTPException(404, "Impact assessment has not been resolved")
    return impact_payload(assessment)


@app.get("/api/v1/journeys/{journey_id}/history")
def journey_history(journey_id: UUID, session: Session = Depends(get_session)):
    require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(AuditLog).where(AuditLog.journey_id == str(journey_id)).order_by(AuditLog.created_at)
    ).all()
    return [_audit_projection(row) for row in rows]


def _json_dict(value: str | None) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _audit_projection(row: AuditLog) -> dict[str, Any]:
    after = _json_dict(row.after_json)
    action = row.action
    decision = after.get("authorization_decision") or after.get("decision")
    reason_codes = after.get("reason_codes") or []
    if not isinstance(reason_codes, list):
        reason_codes = [str(reason_codes)]
    if action in {"agent_tool_requested", "agent.tool.requested"}:
        event_type = "agent_tool_requested"
    elif action in {"agent.request_replan", "replan.requested"}:
        event_type = "replan_requested"
    elif action in {"impact_hypothesis_created", "impact.hypothesis_created"}:
        event_type = "impact_hypothesis_created"
    elif action in {"impact_corroborated", "impact.corroborated"}:
        event_type = "impact_corroborated"
    elif action in {"impact_hypothesis_selected", "impact.hypothesis_selected"}:
        event_type = "impact_hypothesis_selected"
    elif action in {"impact_validated", "impact.resolved"}:
        event_type = "impact_validated"
    elif action in {"impact_rejected", "impact.rejected"}:
        event_type = "impact_rejected"
    elif action in {"replan.generated", "solver_candidates_generated"}:
        event_type = "solver_candidates_generated"
    elif action in {"provider.degraded", "provider_degraded"}:
        event_type = "provider_degraded"
    elif action in {"city.signal.observation.received", "city_signal_received"}:
        event_type = "city_signal_received"
    elif action in {"city.signal.incident.created", "city.signal.incident.updated"}:
        event_type = "incident_updated"
    elif action == "guardian.pulse.started":
        event_type = "guardian_wake"
    elif action == "guardian.pulse.completed":
        event_type = "guardian_sleep"
    elif action == "guardian.mission.compiled":
        event_type = "mission_compiled"
    elif action == "agent.run.started":
        event_type = "agent_run_started"
    elif action in {"agent.run.tool", "agent_tool_requested"}:
        event_type = "agent_tool_called"
    elif action in {"solver.started", "solver.candidates_ready"}:
        event_type = "solver_candidates_ready"
    elif action in {"domain.mutation", "plan.selected", "journey.plan.accepted"}:
        event_type = "domain_mutation"
    elif action in {"twin.refreshed", "journey.twin.refreshed"}:
        event_type = "twin_refreshed"
    elif action in {"event.created", "journey.event.detected"}:
        event_type = "journey_event_detected"
    elif action in {"replan.accepted", "replan_auto_accepted"}:
        event_type = "replan_auto_accepted" if decision == "ALLOW_AUTO" else "replan_accepted"
    elif action == "agent.accept_replan":
        if after.get("user_confirmed") is True and after.get("status") == "ACCEPTED":
            event_type = "replan_user_confirmed"
        elif decision == "DENY":
            event_type = "replan_denied"
        elif decision in {"REQUIRE_CONFIRMATION", "REQUIRE_STEP_UP"}:
            event_type = "replan_confirmation_required"
        elif decision == "ALLOW_AUTO" and after.get("status") == "ACCEPTED":
            event_type = "replan_auto_accepted"
        else:
            event_type = "policy_decision"
    else:
        event_type = action
    proposal_id = after.get("proposal_id")
    if proposal_id is None and row.entity_type == "ReplanProposal":
        proposal_id = row.entity_id
    tool = after.get("tool")
    if tool is None and action.startswith("agent."):
        tool = action.removeprefix("agent.")
    return {
        "id": row.id,
        "timestamp": row.created_at,
        "event_type": event_type,
        "type": event_type,
        "summary": after.get("summary") or event_type.replace("_", " ").capitalize(),
        "actor_type": row.actor_type,
        "actor_id": row.actor_id,
        "tool": tool,
        "journey_id": row.journey_id,
        "proposal_id": proposal_id,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "decision": decision,
        "reason_codes": reason_codes,
        "trace_id": row.trace_id,
        "source": "audit_log",
        "facts": after,
    }


@app.get("/api/v1/journeys/{journey_id}/agent-feed")
def journey_agent_feed(
    journey_id: UUID,
    limit: int = Query(default=100, ge=1, le=200),
    session: Session = Depends(get_session),
):
    require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(AuditLog)
        .where(AuditLog.journey_id == str(journey_id))
        .order_by(AuditLog.created_at, AuditLog.id)
        .limit(limit)
    ).all()
    return {
        "journey_id": str(journey_id),
        "source": "audit_log",
        "events": [_audit_projection(row) for row in rows],
    }


@app.get("/api/v1/journeys/{journey_id}/reflect")
def journey_reflect(journey_id: UUID, session: Session = Depends(get_session)):
    """Return a backend-derived Recover -> Reflect summary.

    Actual timestamps are intentionally not fabricated: the current domain
    records Activity state transitions but does not yet persist per-Activity
    start/finish timestamps. The response therefore exposes planned times plus
    the observed lifecycle status and states where actual time is unavailable.
    """

    journey = require(session, Journey, str(journey_id), "Journey")
    plans = session.scalars(
        select(PlanVersion)
        .where(PlanVersion.journey_id == journey.id)
        .order_by(PlanVersion.version_no, PlanVersion.id)
    ).all()
    final_plan = next(
        (item for item in plans if item.id == journey.active_plan_version_id),
        plans[-1] if plans else None,
    )
    final_activities = []
    if final_plan is not None:
        final_activities = session.scalars(
            select(Activity)
            .where(Activity.plan_version_id == final_plan.id)
            .order_by(Activity.sequence_no, Activity.id)
        ).all()

    replans = session.scalars(
        select(ReplanProposalModel)
        .where(ReplanProposalModel.journey_id == journey.id)
        .order_by(ReplanProposalModel.created_at, ReplanProposalModel.id)
    ).all()
    events = session.scalars(
        select(EventModel)
        .where(EventModel.journey_id == journey.id)
        .order_by(EventModel.detected_at, EventModel.id)
    ).all()
    audits = session.scalars(
        select(AuditLog)
        .where(AuditLog.journey_id == journey.id)
        .order_by(AuditLog.created_at, AuditLog.id)
    ).all()
    agent_actions = [
        _audit_projection(row)
        for row in audits
        if row.actor_type == "AI_AGENT" or row.action.startswith("agent.")
    ]
    provider_disruptions = [
        {
            "id": event.id,
            "provider_key": event.provider_key,
            "provenance": event.provenance,
            "event_type": event.event_type,
            "severity": event.severity,
            "status": event.status,
            "affected_activity_id": event.affected_activity_id,
            "occurred_at": event.occurred_at,
            "detected_at": event.detected_at,
            "resolved_at": event.resolved_at,
        }
        for event in events
        if event.event_type != "USER_CHANGE"
    ]
    initial_cost = int(plans[0].total_cost_minor) if plans else 0
    final_cost = int(final_plan.total_cost_minor) if final_plan is not None else 0
    bookings = session.scalars(
        select(BookingModel).where(BookingModel.journey_id == journey.id)
    ).all()
    captured = session.scalars(
        select(PaymentTransaction).where(
            PaymentTransaction.journey_id == journey.id,
            PaymentTransaction.transaction_type == "CAPTURE",
            PaymentTransaction.status == "SUCCEEDED",
        )
    ).all()
    outcome_events = session.scalars(
        select(JourneyOutcomeEvent)
        .where(JourneyOutcomeEvent.journey_id == journey.id)
        .order_by(JourneyOutcomeEvent.occurred_at_actual, JourneyOutcomeEvent.id)
    ).all()
    actual_by_activity: dict[str, dict[str, str]] = {}
    for outcome in outcome_events:
        item = actual_by_activity.setdefault(outcome.activity_id or "", {})
        if outcome.event_type == "ACTIVITY_STARTED":
            item["actual_start_at"] = outcome.occurred_at_actual
        elif outcome.event_type in {"ACTIVITY_COMPLETED", "ACTIVITY_SKIPPED"}:
            item["actual_end_at"] = outcome.occurred_at_actual
            if outcome.event_type == "ACTIVITY_SKIPPED":
                item["skipped_at"] = outcome.occurred_at_actual
    twin = traveler_twin_payload(refresh_snapshot(session, journey.traveler_id))

    return {
        "journey_id": journey.id,
        "status": journey.status,
        "completed": journey.status == "COMPLETED",
        "timeline": {
            "actual_time_available": journey.status == "COMPLETED"
            or any(
                item.event_type in {"MANUAL_OVERRIDE", "USER_ACCEPTED", "USER_REJECTED"}
                for item in outcome_events
            ),
            "actual_time_note": (
                "Actual transition events are persisted in the Journey outcome timeline."
                if outcome_events
                else "No actual Activity transition has been recorded yet."
            ),
            "activities": [
                {
                    "activity_id": item.id,
                    "title": item.title,
                    "activity_type": item.activity_type,
                    "planned_start_at": item.start_at,
                    "planned_end_at": item.end_at,
                    "observed_status": item.status,
                    "actual_start_at": actual_by_activity.get(item.id, {}).get("actual_start_at"),
                    "actual_end_at": actual_by_activity.get(item.id, {}).get("actual_end_at"),
                    "skipped_at": actual_by_activity.get(item.id, {}).get("skipped_at"),
                    "schedule_drift_min": (
                        round(
                            (
                                datetime.fromisoformat(
                                    actual_by_activity[item.id]["actual_start_at"]
                                )
                                - datetime.fromisoformat(item.start_at)
                            ).total_seconds()
                            / 60
                        )
                        if item.id in actual_by_activity
                        and actual_by_activity[item.id].get("actual_start_at")
                        else None
                    ),
                }
                for item in final_activities
            ],
        },
        "outcome_events": [
            {
                "id": item.id,
                "activity_id": item.activity_id,
                "event_type": item.event_type,
                "actor_type": item.actor_type,
                "occurred_at_actual": item.occurred_at_actual,
                "planned_start_at": item.planned_start_at,
                "planned_end_at": item.planned_end_at,
                "payload": _json_dict(item.payload_json),
            }
            for item in outcome_events
        ],
        "replan_history": [
            {
                "id": item.id,
                "status": item.status,
                "base_plan_version_id": item.base_plan_version_id,
                "proposed_plan_version_id": item.proposed_plan_version_id,
                "created_at": item.created_at,
                "decided_at": item.decided_at,
                "diff": _json_dict(item.diff_json),
            }
            for item in replans
        ],
        "agent_action_history": agent_actions,
        "provider_disruptions": provider_disruptions,
        "cost_summary": {
            "currency": journey.budget_currency,
            "initial_estimated_minor": initial_cost,
            "final_estimated_minor": final_cost,
            "estimated_delta_minor": final_cost - initial_cost,
            "confirmed_booking_minor": sum(
                int(item.amount_minor)
                for item in bookings
                if item.status in {"CONFIRMED", "COMPLETED"}
            ),
            "captured_payment_minor": sum(int(item.amount_minor) for item in captured),
        },
        "plan_version_chain": [
            {
                "id": item.id,
                "version_no": item.version_no,
                "status": item.status,
                "source": item.source,
                "parent_plan_version_id": item.parent_plan_version_id,
                "total_cost_minor": item.total_cost_minor,
            }
            for item in plans
        ],
        "preference_feedback_hook": {
            "available": True,
            "traveler_id": journey.traveler_id,
            "endpoint": f"/api/v1/travelers/{journey.traveler_id}/traveler-twin",
            "mode": "explicit_user_feedback_only",
            "learning": "reflect_to_learned_soft_evidence",
        },
        "traveler_twin": twin,
    }


@app.post("/api/v1/journeys/{journey_id}/reflect/process")
def process_journey_reflect(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    snapshot = learn_from_journey(session, journey)
    record_audit(
        session,
        action="journey.reflect.processed",
        entity_type="TravelerTwinSnapshot",
        entity_id=journey.traveler_id,
        journey_id=journey.id,
        actor_type="USER",
        actor_id=journey.traveler_id,
        after={"traveler_twin_updated": True, "evidence_count": snapshot.evidence_count},
    )
    session.commit()
    return {"journey_id": journey.id, "traveler_twin": traveler_twin_payload(snapshot)}


@app.get("/api/v1/journeys/{journey_id}/observability/traces")
def journey_observability_traces(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    rows = session.scalars(
        select(AuditLog)
        .where(AuditLog.journey_id == journey.id, AuditLog.action == "trace.span")
        .order_by(AuditLog.created_at, AuditLog.id)
    ).all()
    return {
        "journey_id": journey.id,
        "phoenix": "CONFIGURED" if os.getenv("CITYNEXUS_PHOENIX_ENDPOINT") else "NOT_CONFIGURED",
        "spans": [
            {
                "trace_id": row.trace_id,
                "created_at": row.created_at,
                **_json_dict(row.after_json),
            }
            for row in rows
        ],
    }


def _activity_coordinate(session: Session, activity: Activity) -> list[float] | None:
    key = activity.place_id or activity.city_service_id
    if not key:
        return None
    place = session.get(Place, key)
    if place is None:
        service = session.get(CityService, key)
        if service is not None and service.place_id:
            place = session.get(Place, service.place_id)
    if place is None:
        return None
    return [float(place.longitude), float(place.latitude)]


def _frozen_route_for_plan(
    session: Session,
    plan: PlanVersion,
    snapshot: MobilitySnapshot | None,
) -> tuple[list[list[float]], bool, str | None]:
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan.id).order_by(Activity.sequence_no)
    ).all()
    coordinates: list[list[float]] = []
    used_provider_geometry = True
    segment_count = 0
    fallback_reason: str | None = None
    previous_key: str | None = None
    previous_coordinate: list[float] | None = None
    for activity in activities:
        coordinate = _activity_coordinate(session, activity)
        key = activity.place_id or activity.city_service_id
        if coordinate is None or key is None:
            previous_key = key
            previous_coordinate = coordinate
            continue
        if not coordinates:
            coordinates.append(coordinate)
        elif previous_key and previous_coordinate:
            segment_count += 1
            fact = snapshot.facts.get((previous_key, key)) if snapshot is not None else None
            geometry = list(fact.route_geometry) if fact is not None else []
            if len(geometry) >= 2:
                points = [list(point) for point in geometry]
                if points[0] != coordinates[-1]:
                    coordinates.append(points[0])
                coordinates.extend(points[1:])
            else:
                used_provider_geometry = False
                fallback_reason = fallback_reason or (
                    "NO_FROZEN_ROUTE_GEOMETRY"
                    if snapshot is not None
                    else "NO_FROZEN_MOBILITY_SNAPSHOT"
                )
                coordinates.append(coordinate)
        previous_key = key
        previous_coordinate = coordinate
    if segment_count == 0:
        used_provider_geometry = False
        fallback_reason = fallback_reason or "ROUTE_HAS_NO_TRAVEL_SEGMENTS"
    return coordinates, used_provider_geometry, fallback_reason


def _route_feature(
    coordinates: list[list[float]],
    *,
    provider: str,
    provider_backed: bool,
    fallback_reason: str | None,
    plan_version_id: str,
) -> dict[str, Any]:
    safe_coordinates = coordinates if len(coordinates) >= 2 else coordinates * 2
    if not safe_coordinates:
        safe_coordinates = [[117.19, 39.13], [117.19, 39.13]]
    return {
        "type": "Feature",
        "properties": {
            "provider": provider,
            "provider_backed": provider_backed,
            "fallback": not provider_backed,
            "fallback_reason": fallback_reason,
            "plan_version_id": plan_version_id,
        },
        "geometry": {"type": "LineString", "coordinates": safe_coordinates},
    }


def _marker_feature(
    activity: Activity | None,
    coordinate: list[float] | None,
    *,
    role: str,
    title: str,
) -> dict[str, Any] | None:
    if coordinate is None:
        return None
    return {
        "type": "Feature",
        "properties": {
            "role": role,
            "title": title,
            "activity_id": activity.id if activity else None,
        },
        "geometry": {"type": "Point", "coordinates": coordinate},
    }


def _disruption_scope_feature(payload: dict[str, Any]) -> dict[str, Any] | None:
    raw = payload.get("disruption_polygon") or payload.get("polygon")
    if isinstance(raw, dict) and raw.get("type") == "Feature":
        geometry = raw.get("geometry")
    elif isinstance(raw, dict):
        geometry = raw
    else:
        # Accept both GeoJSON ring coordinates and a direct list of points
        # from lightweight event producers.  GeoJSON Polygon coordinates are
        # one level deeper than a single ring; normalize the latter here so
        # the map projection and the impact resolver consume the same shape.
        coordinates = raw
        if (
            isinstance(raw, list)
            and raw
            and isinstance(raw[0], list)
            and len(raw[0]) >= 2
            and isinstance(raw[0][0], (int, float))
        ):
            coordinates = [raw]
        geometry = {"type": "Polygon", "coordinates": coordinates} if raw else None
    if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        return None
    return {
        "type": "Feature",
        "properties": {"role": "disruption-scope", "title": "Disruption scope"},
        "geometry": {
            "type": geometry["type"],
            "coordinates": geometry.get("coordinates", []),
        },
    }


@app.get("/api/v1/journeys/{journey_id}/route-evidence")
def journey_route_evidence(
    journey_id: UUID,
    proposal_id: UUID | None = None,
    session: Session = Depends(get_session),
):
    journey = require(session, Journey, str(journey_id), "Journey")
    proposal = None
    if proposal_id is not None:
        proposal = session.get(ReplanProposalModel, str(proposal_id))
        if proposal is None or proposal.journey_id != journey.id:
            raise HTTPException(404, "Replan proposal was not found on this Journey")
    elif journey.active_plan_version_id is not None:
        proposal = session.scalar(
            select(ReplanProposalModel)
            .where(
                ReplanProposalModel.journey_id == journey.id,
                ReplanProposalModel.status == "PRESENTED",
            )
            .order_by(ReplanProposalModel.created_at.desc(), ReplanProposalModel.id.desc())
        )
    base_plan_id = proposal.base_plan_version_id if proposal else journey.active_plan_version_id
    if base_plan_id is None:
        raise HTTPException(409, "Journey has no active plan for route evidence")
    base_plan = require(session, PlanVersion, base_plan_id, "PlanVersion")
    snapshot = (
        _proposal_mobility_snapshot(proposal)
        if proposal
        else _latest_replan_mobility_snapshot(session, journey.id)
    )
    old_coordinates, old_provider_backed, old_fallback_reason = _frozen_route_for_plan(
        session, base_plan, snapshot
    )
    old_route = _route_feature(
        old_coordinates,
        provider=snapshot.source_provider_key if snapshot else "server-place-fallback",
        provider_backed=old_provider_backed,
        fallback_reason=old_fallback_reason,
        plan_version_id=base_plan.id,
    )
    new_route = None
    if proposal is not None:
        proposed_plan = require(
            session, PlanVersion, proposal.proposed_plan_version_id, "PlanVersion"
        )
        new_coordinates, new_provider_backed, new_fallback_reason = _frozen_route_for_plan(
            session, proposed_plan, snapshot
        )
        new_route = _route_feature(
            new_coordinates,
            provider=snapshot.source_provider_key if snapshot else "server-place-fallback",
            provider_backed=new_provider_backed,
            fallback_reason=new_fallback_reason,
            plan_version_id=proposed_plan.id,
        )

    active_plan = (
        session.get(PlanVersion, journey.active_plan_version_id)
        if journey.active_plan_version_id
        else base_plan
    )
    active_activities = session.scalars(
        select(Activity)
        .where(Activity.plan_version_id == active_plan.id)
        .order_by(Activity.sequence_no)
    ).all()
    by_id = {item.id: item for item in active_activities}
    current = by_id.get(journey.current_activity_id or "")
    current_index = active_activities.index(current) if current in active_activities else -1
    next_activity = (
        active_activities[current_index + 1]
        if current_index >= 0 and current_index + 1 < len(active_activities)
        else None
    )
    c4_activity_ids = {
        item.activity_id
        for item in session.scalars(
            select(CommitmentModel).where(
                CommitmentModel.journey_id == journey.id,
                CommitmentModel.status == "ACTIVE",
                CommitmentModel.level == "C4_Anchored",
            )
        ).all()
        if item.activity_id
    }
    markers: list[dict[str, Any]] = []
    for activity, role, title in (
        (current, "current", "Current activity"),
        (next_activity, "next", "Next activity"),
    ):
        marker = _marker_feature(
            activity,
            _activity_coordinate(session, activity) if activity else None,
            role=role,
            title=title,
        )
        if marker:
            markers.append(marker)
    for activity_id in sorted(c4_activity_ids):
        activity = by_id.get(activity_id)
        marker = _marker_feature(
            activity,
            _activity_coordinate(session, activity) if activity else None,
            role="c4",
            title="C4 protected commitment",
        )
        if marker:
            markers.append(marker)
    trigger = (
        session.get(EventModel, proposal.trigger_event_id)
        if proposal and proposal.trigger_event_id
        else session.scalar(
            select(EventModel)
            .where(EventModel.journey_id == journey.id)
            .order_by(EventModel.occurred_at.desc(), EventModel.id.desc())
        )
    )
    disruption_activity = (
        by_id.get(trigger.affected_activity_id)
        if trigger and trigger.affected_activity_id
        else None
    )
    disruption_coordinate = (
        _activity_coordinate(session, disruption_activity) if disruption_activity else None
    )
    if disruption_coordinate is None and trigger is not None:
        payload = _json_dict(trigger.payload_json)
        if payload.get("longitude") is not None and payload.get("latitude") is not None:
            disruption_coordinate = [float(payload["longitude"]), float(payload["latitude"])]
    marker = _marker_feature(
        disruption_activity, disruption_coordinate, role="disruption", title="Disruption scope"
    )
    if marker:
        markers.append(marker)
    disruption_payload = _json_dict(trigger.payload_json) if trigger is not None else {}
    disruption_scope = _disruption_scope_feature(disruption_payload)
    impact_evidence = (
        _json_dict(proposal.diff_json).get("verified_evidence", {}).get("impact_resolution", {})
        if proposal is not None
        else {}
    )
    impacted_activity_ids = list(
        dict.fromkeys(
            [
                item
                for item in [
                    impact_evidence.get("selected_activity_id"),
                    *(impact_evidence.get("secondary_risk_activity_ids") or []),
                ]
                if item
            ]
        )
    )
    return {
        "journey_id": journey.id,
        "proposal_id": proposal.id if proposal else None,
        "snapshot_id": snapshot.snapshot_id if snapshot else None,
        "provider": snapshot.source_provider_key if snapshot else "server-place-fallback",
        "frozen": snapshot is not None,
        "old_route": old_route,
        "new_route": new_route,
        "disruption_scope": disruption_scope,
        "impacted_activity_ids": impacted_activity_ids,
        "markers": {"type": "FeatureCollection", "features": markers},
        "fallback": bool(
            old_route["properties"]["fallback"]
            or (new_route and new_route["properties"]["fallback"])
        ),
        "fallback_reason": old_route["properties"]["fallback_reason"]
        or (new_route["properties"]["fallback_reason"] if new_route else None),
        "source": "frozen_mobility_snapshot" if snapshot else "server_place_coordinates",
    }


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


@dataclass(frozen=True)
class _ReplanCandidateSpec:
    family: str
    replacement_choice: Any | None
    candidate_delay: int = 0
    candidate_remove: bool = False
    window_evidence: dict[str, Any] | None = None
    explicit_candidate_start_at: datetime | None = None
    solver_provenance: dict[str, Any] | None = None
    v2_plan: SolverV2Plan | None = None
    v2_choices: dict[tuple[str, str], Any] | None = None


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
        semantic_key = policy.get("semantic_key")
        if not semantic_key:
            legacy_key = str(policy.get("semantic_node_key") or "")
            matching = next(
                (
                    item
                    for item in source
                    if str(item.place_id or item.city_service_id or "").endswith(f":{legacy_key}")
                    or str(_json_object(item.metadata_json, {}).get("semantic_key") or "").endswith(f":{legacy_key}")
                ),
                None,
            )
            semantic_key = matching.place_id or matching.city_service_id if matching else None
        if semantic_key and policy.get("scheduled_start_at"):
            c4_anchors.append((str(semantic_key), str(policy["scheduled_start_at"])))
    places_by_id = {
        place.id: place
        for place in session.scalars(
            select(Place).where(Place.city_code == journey.city_code).order_by(Place.id)
        ).all()
    }
    frozen_v12_evidence = _json_object(base.mobility_evidence_json, {})
    frozen_provider_evidence = frozen_v12_evidence.get("provider_evidence")
    if not isinstance(frozen_provider_evidence, dict):
        frozen_provider_evidence = {}
    discovery_evidence = frozen_v12_evidence.get("discovery")
    if not isinstance(discovery_evidence, dict):
        discovery_evidence = {}
    provider_mobility_reserve = discovery_evidence.get("provider_mobility")
    if not isinstance(provider_mobility_reserve, dict):
        provider_mobility_reserve = {}
    fully_grounded_recovery = bool(
        frozen_provider_evidence.get("fully_provider_grounded")
        or frozen_provider_evidence.get("fully_grounded")
    ) and bool(provider_mobility_reserve.get("facts"))
    grounded_recovery_aliases = (
        _grounded_recovery_provider_aliases(source, places_by_id, provider_mobility_reserve)
        if fully_grounded_recovery
        else {}
    )
    grounded_recovery_place_ids = {
        location
        for provider_node, location in grounded_recovery_aliases.items()
        if provider_node.startswith("place:") and location in places_by_id
    }
    impact_resolution = resolve_impact(
        event=trigger_event,
        journey=journey,
        activities=source,
        places_by_id=places_by_id,
        c4_activity_ids={row.activity_id for row in c4_rows if row.activity_id},
    )
    assessment = persist_impact_assessment(session, impact_resolution)
    selected_impact_explanation = next(
        (
            item.human_explanation
            for item in impact_resolution.validation.candidates
            if item.activity_id == impact_resolution.selected_activity_id
        ),
        "",
    )
    impact_facts = {
        "assessment_id": assessment.id,
        "status": impact_resolution.status,
        "maturity_stage": impact_resolution.maturity_stage,
        "selected_activity_id": impact_resolution.selected_activity_id,
        "primary_recovery_target_id": impact_resolution.primary_recovery_target_id,
        "secondary_risk_activity_ids": list(impact_resolution.secondary_risk_activity_ids),
        "independent_evidence_count": impact_resolution.independent_evidence_count,
        "corroboration_refs": list(impact_resolution.selected_corroboration_refs),
        "reason_codes": list(impact_resolution.validation.reason_codes),
        "provider_key": impact_resolution.provider_key,
        "model_key": impact_resolution.model_key,
        "semantic_explanation": selected_impact_explanation,
    }
    record_audit(
        session,
        action="impact_hypothesis_created",
        entity_type="ImpactAssessment",
        entity_id=assessment.id,
        journey_id=journey.id,
        after=impact_facts,
    )
    if impact_resolution.selected_activity_id is None:
        record_audit(
            session,
            action="impact_rejected",
            entity_type="ImpactAssessment",
            entity_id=assessment.id,
            journey_id=journey.id,
            after=impact_facts,
        )
    elif impact_resolution.maturity_stage == "VALIDATED_IMPACT":
        record_audit(
            session,
            action="impact_validated",
            entity_type="ImpactAssessment",
            entity_id=assessment.id,
            journey_id=journey.id,
            after=impact_facts,
        )
    elif impact_resolution.maturity_stage == "AI_ONLY":
        record_audit(
            session,
            action="impact_hypothesis_selected",
            entity_type="ImpactAssessment",
            entity_id=assessment.id,
            journey_id=journey.id,
            after=impact_facts,
        )
    else:
        record_audit(
            session,
            action="impact_corroborated",
            entity_type="ImpactAssessment",
            entity_id=assessment.id,
            journey_id=journey.id,
            after=impact_facts,
        )
    # The Event remains the raw provider/user fact.  A semantic model target
    # is scoped to this recovery operation and lives in ImpactAssessment.
    effective_affected_activity_id = impact_resolution.selected_activity_id
    # Impact evidence is independently durable even when no recovery proposal
    # can be produced. A later candidate-generation rollback must not erase
    # the corroboration decision that explains the failed recovery attempt.
    session.commit()
    solver_mode = normalize_solver_mode(
        body.solver_mode or os.getenv("CITYNEXUS_SOLVER", settings.solver_mode)
    )
    if trigger_event.event_type in {
        "CLOSURE",
        "WEATHER",
    } and trigger_event.affected_activity_id in {row.activity_id for row in c4_rows}:
        raise HTTPException(
            422, "closed activity is protected and cannot be replaced automatically"
        )
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
        affected_activity_id = effective_affected_activity_id
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
                    select(Place)
                    .where(
                        Place.city_code == journey.city_code,
                        # Authoritative structural nodes (check-in, stay,
                        # anchors) are server-owned schedule facts, not
                        # replacement POIs.  They use distinct semantic keys
                        # in the sealed matrix and must never enter a
                        # candidate family as if they were a discoverable
                        # city service.
                        Place.provider_key != "citynexus-v12-authoritative",
                    )
                    .order_by(Place.id)
                ).all()
                if fully_grounded_recovery:
                    places = [
                        place for place in places if place.id in grounded_recovery_place_ids
                    ]
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
                        traveler_preferences=planning_preference_items(
                            session, journey.traveler_id, journey.id
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
    requested_protected_ids = {str(item) for item in body.protected_activity_ids}
    active_activity_ids = {item.id for item in source}
    if not requested_protected_ids.issubset(active_activity_ids):
        raise HTTPException(422, "protected activity is not in the active Journey plan")
    protected_activity_ids.update(requested_protected_ids)
    if affected_activity_id in protected_activity_ids and trigger_event.event_type in {
        "CLOSURE",
        "WEATHER",
    }:
        raise HTTPException(422, "affected activity is protected by the Journey mission")
    effective_event_time_source = trigger_event.occurred_at
    if trigger_event.event_type == "WEATHER" and trigger_event.provenance == "PROVIDER_VERIFIED":
        effective_event_time_source = str(
            payload.get("snapshot_captured_at")
            or trigger_event.detected_at
            or trigger_event.occurred_at
        )
    effective_event_time = datetime.fromisoformat(effective_event_time_source)
    # Normalize every Event instant onto the Journey schedule timeline before
    # evaluating local opening hours or OpportunityWindow evidence. Real
    # providers such as Open-Meteo emit UTC instants while the plan stores
    # local scheduled offsets.
    journey_reference = datetime.fromisoformat(journey.start_at)
    try:
        journey_tz = ZoneInfo(journey.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        journey_tz = journey_reference.tzinfo
    if effective_event_time.tzinfo is None:
        effective_event_time = effective_event_time.replace(tzinfo=journey_tz)
    elif journey_tz is not None:
        effective_event_time = effective_event_time.astimezone(journey_tz)

    def _activity_location(item: Activity | None) -> str | None:
        if item is None:
            return None
        return item.place_id or item.city_service_id

    mobility_pairs: set[tuple[str, str]] = set()

    def _need_pair(origin: str | None, destination: str | None) -> None:
        if origin and destination and origin != destination:
            mobility_pairs.add((origin, destination))

    for previous, current in zip(source, source[1:]):
        _need_pair(_activity_location(previous), _activity_location(current))

    current_execution = next(
        (item for item in source if item.id == journey.current_activity_id),
        None,
    )
    v2_choice_pools: dict[str, tuple[Any, ...]] = {}
    if solver_mode == "v2" and trigger_event.event_type in {"CLOSURE", "WEATHER"}:
        candidate_places = session.scalars(
            select(Place)
            .where(
                Place.city_code == journey.city_code,
                Place.provider_key != "citynexus-v12-authoritative",
            )
            .order_by(Place.id)
        ).all()
        if fully_grounded_recovery:
            candidate_places = [
                place for place in candidate_places if place.id in grounded_recovery_place_ids
            ]
        occupied_place_ids = {item.place_id for item in source if item.place_id}
        current_sequence = current_execution.sequence_no if current_execution is not None else -1
        for item in source:
            if (
                item.sequence_no < current_sequence
                or item.id in protected_activity_ids
                or item.status in {"COMPLETED", "SKIPPED", "CANCELLED"}
                or item.locked
                or not item.place_id
            ):
                continue
            if item.id == affected_activity_id:
                choices = tuple(replacement_choices)
            else:
                item_place = session.get(Place, item.place_id)
                choices = (
                    rank_closure_replacements(
                        affected_place=item_place,
                        candidate_places=candidate_places,
                        occupied_place_ids=occupied_place_ids,
                        max_duration_min=max(
                            1,
                            int(
                                (
                                    datetime.fromisoformat(item.end_at)
                                    - datetime.fromisoformat(item.start_at)
                                ).total_seconds()
                                // 60
                            ),
                        ),
                        traveler_preferences=planning_preference_items(
                            session, journey.traveler_id, journey.id
                        ),
                    )
                    if item_place is not None
                    else ()
                )
            v2_choice_pools[item.id] = tuple(choices)
    affected_index = source.index(affected) if affected in source else -1
    previous_affected = source[affected_index - 1] if affected_index > 0 else None
    next_affected = (
        source[affected_index + 1]
        if affected_index >= 0 and affected_index + 1 < len(source)
        else None
    )
    future_anchor = (
        min(
            (datetime.fromisoformat(start), semantic)
            for semantic, start in c4_anchors
            if datetime.fromisoformat(start) > effective_event_time
        )
        if any(datetime.fromisoformat(start) > effective_event_time for _, start in c4_anchors)
        else None
    )
    for choice in replacement_choices:
        _need_pair(_activity_location(current_execution or previous_affected), choice.place_id)
        _need_pair(_activity_location(previous_affected), choice.place_id)
        _need_pair(choice.place_id, _activity_location(next_affected))
        if future_anchor is not None:
            _need_pair(choice.place_id, future_anchor[1])
    _need_pair(_activity_location(previous_affected), _activity_location(next_affected))
    if future_anchor is not None:
        _need_pair(_activity_location(current_execution), future_anchor[1])
    if v2_choice_pools:
        v2_locations = {
            location for item in source for location in (_activity_location(item),) if location
        }
        v2_locations.update(
            choice.place_id for choices in v2_choice_pools.values() for choice in choices
        )
        v2_locations.update(str(semantic) for semantic, _start in c4_anchors if semantic)
        for origin in v2_locations:
            for destination in v2_locations:
                _need_pair(origin, destination)

    is_authoritative_v12_evidence = (
        str(frozen_v12_evidence.get("normalizer_version") or "").startswith(
            ("citynexus-v12-authoritative-", "citynexus-v13-authoritative-")
        )
        and bool(frozen_v12_evidence.get("selected_facts"))
        and int(frozen_v12_evidence.get("mode_matrix_count") or 0) > 0
    )
    incident_snapshot = _incident_mobility_snapshot(payload)
    incident_baseline_reference_fallback = False
    reuse_baseline_for_recovery = (
        is_authoritative_v12_evidence
        and trigger_event.event_type not in {"TRAFFIC_DELAY", "SCHEDULE_DELAY"}
    )
    if incident_snapshot is not None:
        mobility_capture = MobilitySnapshotCaptureResult(
            snapshot=incident_snapshot,
            failed_primary_pairs=(),
            fallback_pairs=(),
        )
    elif (
        trigger_event.event_type in {"TRAFFIC_DELAY", "SCHEDULE_DELAY"}
        and is_authoritative_v12_evidence
        and not fully_grounded_recovery
        and not settings.live_valhalla_url
        and frozen_v12_evidence.get("snapshot_id")
        and frozen_v12_evidence.get("facts")
    ):
        # Legacy synthetic plans can still serve the pre-V14 offline/autonomy
        # path when no incident provider is configured.  Mint a distinct
        # operation snapshot and label it as a baseline reference only; the
        # fully grounded V14 path never enters this branch and requires a
        # separately sealed incident matrix for traffic changes.
        baseline_reference = MobilitySnapshot.from_evidence(frozen_v12_evidence)
        mobility_capture = MobilitySnapshotCaptureResult(
            snapshot=MobilitySnapshot(
                facts=baseline_reference.facts,
                source_provider_key=baseline_reference.source_provider_key,
                captured_at=effective_event_time.isoformat(),
                degraded=False,
                snapshot_id="v14-baseline-reference-"
                + hashlib.sha256(f"{trigger_id}:baseline-reference".encode("utf-8")).hexdigest()[:32],
                operation_key=f"replan:{trigger_id}:baseline-reference",
                provider_capabilities={
                    "recovery": {
                        "status": "NOT_CONFIGURED",
                        "current_route_truth": False,
                        "baseline_reference_only": True,
                    }
                },
            ),
            failed_primary_pairs=(),
            fallback_pairs=(),
        )
        incident_baseline_reference_fallback = True
    elif (
        reuse_baseline_for_recovery
        and frozen_v12_evidence.get("snapshot_id")
        and frozen_v12_evidence.get("facts")
    ):
        # Closure/weather can reuse the Journey's sealed reserve when route
        # conditions are explicitly unchanged. Traffic and schedule events
        # never enter this branch: they require incident-time route evidence.
        frozen_snapshot = MobilitySnapshot.from_evidence(frozen_v12_evidence)
        if fully_grounded_recovery and trigger_event.event_type in {"CLOSURE", "WEATHER"}:
            frozen_snapshot = _grounded_recovery_reserve_snapshot(
                base_evidence=frozen_v12_evidence,
                provider_mobility=provider_mobility_reserve,
                aliases=grounded_recovery_aliases,
                operation_key=f"replan:{trigger_id}:grounded-reserve",
            )
        mobility_capture = MobilitySnapshotCaptureResult(
            snapshot=frozen_snapshot,
            failed_primary_pairs=(),
            fallback_pairs=(),
        )
    else:
        try:
            mobility_capture = capture_runtime_mobility_snapshot(
                session,
                journey,
                mobility_pairs,
                operation_key=f"replan:{trigger_id}:incident",
                captured_at=effective_event_time.isoformat(),
            )
        except MobilitySnapshotCaptureError as exc:
            raise HTTPException(503, f"mobility evidence unavailable: {exc}") from exc
    mobility = mobility_capture.snapshot
    mobility_degraded_providers = (mobility.source_provider_key,) if mobility.degraded else ()
    if mobility.degraded:
        record_audit(
            session,
            action="provider_degraded",
            entity_type="MobilitySnapshot",
            entity_id=mobility.snapshot_id,
            journey_id=journey.id,
            after={
                "provider": mobility.source_provider_key,
                "snapshot_id": mobility.snapshot_id,
                "operation_key": mobility.operation_key,
                "fallback_pairs": [list(pair) for pair in mobility_capture.fallback_pairs],
            },
        )

    baseline_plan_evidence = {
        "plan_version_id": base.id,
        "snapshot_id": frozen_v12_evidence.get("snapshot_id"),
        "captured_at": frozen_v12_evidence.get("captured_at"),
        "source_provider": frozen_v12_evidence.get("source_provider"),
        "runtime_label": frozen_v12_evidence.get("runtime_label"),
        "immutable": True,
    }
    recovery_snapshot_evidence = mobility.to_evidence()
    recovery_route_provenance = (
        "SEALED_INCIDENT_REPLAY"
        if incident_snapshot is not None
        else "DEGRADED_BASELINE_REFERENCE"
        if incident_baseline_reference_fallback
        else "SEALED_REAL_REPLAY"
        if fully_grounded_recovery and trigger_event.event_type in {"CLOSURE", "WEATHER"}
        else "MIXED_RUNTIME_CAPTURE"
        if mobility.degraded
        else "RUNTIME_CAPTURE"
    )
    raw_weather_evidence = (
        payload.get("weather_evidence")
        or payload.get("weather_snapshot")
        or payload.get("provider_evidence")
        or payload.get("weather")
    )
    weather_evidence = raw_weather_evidence
    if isinstance(raw_weather_evidence, dict) and "provider_evidence" not in raw_weather_evidence:
        weather_evidence = {
            "provider": trigger_event.provider_key,
            "captured_at": payload.get("snapshot_captured_at") or trigger_event.detected_at,
            "provider_evidence": raw_weather_evidence,
        }
    if isinstance(weather_evidence, dict):
        for key in ("provider_observation_id", "capture_provenance", "forecast_runs"):
            if payload.get(key) is not None:
                weather_evidence.setdefault(key, payload[key])
    incident_recovery_evidence = {
        "evidence_id": f"incident:{trigger_id}:{mobility.snapshot_id}",
        "event_id": trigger_id,
        "event_type": trigger_event.event_type,
        "event_occurred_at": trigger_event.occurred_at,
        "captured_at": mobility.captured_at,
        "route_provenance": recovery_route_provenance,
        "source_provider": mobility.source_provider_key,
        "degraded": mobility.degraded,
        "baseline_snapshot_id": frozen_v12_evidence.get("snapshot_id"),
        "mobility_reused_from_baseline": reuse_baseline_for_recovery
        and incident_snapshot is None,
        "routing_conditions_assumption": (
            "UNCHANGED_FROM_BASELINE"
            if reuse_baseline_for_recovery and incident_snapshot is None
            else "BASELINE_REFERENCE_ONLY_PROVIDER_UNAVAILABLE"
            if incident_baseline_reference_fallback
            else "CAPTURED_AT_INCIDENT"
        ),
        "mobility_snapshot": recovery_snapshot_evidence,
        "weather": weather_evidence,
        "provider_capabilities": recovery_snapshot_evidence.get("provider_capabilities", {}),
    }
    recovery_observation_id = str(uuid4())
    incident_recovery_evidence["provider_observation_id"] = recovery_observation_id
    session.add(
        ProviderObservation(
            id=recovery_observation_id,
            journey_id=journey.id,
            provider_key=mobility.source_provider_key,
            observation_type="MOBILITY",
            state="DEGRADED" if mobility.degraded else "CAPTURED",
            incident_fingerprint=payload.get("incident_fingerprint"),
            provenance=recovery_route_provenance,
            captured_at=mobility.captured_at,
            expires_at=None,
            payload_json=json.dumps(incident_recovery_evidence, sort_keys=True),
            created_at=mobility.captured_at,
        )
    )
    record_audit(
        session,
        action="replan.incident.provider_observation.captured",
        entity_type="ProviderObservation",
        entity_id=recovery_observation_id,
        journey_id=journey.id,
        after={
            "provider_key": mobility.source_provider_key,
            "observation_type": "MOBILITY",
            "provenance": recovery_route_provenance,
            "snapshot_id": mobility.snapshot_id,
        },
        actor_type="SYSTEM",
        actor_id="citynexus-v14-recovery",
    )
    session.flush()

    def _recovery_plan_evidence(items: list[Activity]) -> dict[str, Any]:
        evidence = dict(recovery_snapshot_evidence)
        pairs = {
            (str(previous.place_id or previous.city_service_id or ""), str(current.place_id or current.city_service_id or ""))
            for previous, current in zip(items, items[1:])
        }
        selected_facts = [
            item
            for item in evidence.get("facts", [])
            if (str(item.get("origin_key")), str(item.get("destination_key"))) in pairs
        ]
        evidence["selected_facts"] = selected_facts
        evidence.update(
            {
                "normalizer_version": "citynexus-v14-recovery-evidence-1",
                "aggregate_provenance": recovery_route_provenance,
                "baseline_plan_evidence": baseline_plan_evidence,
                "incident_recovery_evidence": incident_recovery_evidence,
                "provider_evidence": {
                    "selected_path": recovery_route_provenance,
                    "selected_synthetic_fact_count": sum(
                        1
                        for item in selected_facts
                        if str(item.get("provider") or "").lower().startswith("mock")
                        or str(item.get("provenance") or "").upper() == "SYNTHETIC_FIXTURE"
                    ),
                    "synthetic_fact_count": sum(
                        1
                        for item in evidence.get("facts", [])
                        if str(item.get("provider") or "").lower().startswith("mock")
                        or str(item.get("provenance") or "").upper() == "SYNTHETIC_FIXTURE"
                    ),
                    "route_provenance": recovery_route_provenance,
                    "cost_provenance": "CITYNEXUS_COST_ESTIMATE",
                },
            }
        )
        evidence["integrity_hash"] = hashlib.sha256(
            json.dumps(evidence, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return evidence

    def _at_local_time(value: str | None) -> datetime | None:
        if not value:
            return None
        hour, minute = (int(part) for part in str(value).split(":", 1))
        return datetime.combine(
            effective_event_time.date(),
            datetime.min.time().replace(hour=hour, minute=minute),
            effective_event_time.tzinfo,
        )

    heuristic_specs: list[_ReplanCandidateSpec] = []
    if replacement_choices:
        for index, choice in enumerate(replacement_choices):
            family = "F0_SAME_SLOT_REPLACEMENT"
            window_evidence: dict[str, Any] | None = None
            if index > 0 and affected is not None:
                next_anchor = future_anchor
                if next_anchor is not None:
                    candidate_place = session.get(Place, choice.place_id)
                    opening = normalize_opening_hours(
                        json.loads(candidate_place.opening_hours_json or "{}")
                    )

                    # Replanning must start from the authoritative execution
                    # position, not merely from the activity immediately
                    # preceding the disrupted slot. The previous slot remains
                    # a deterministic fallback when execution position is not
                    # available.
                    previous = next(
                        (item for item in source if item.sequence_no == affected.sequence_no - 1),
                        None,
                    )
                    origin_activity = current_execution or previous
                    origin = (
                        (origin_activity.place_id or origin_activity.city_service_id)
                        if origin_activity is not None
                        else None
                    )
                    inbound = (
                        mobility.estimate_minutes(origin, choice.place_id)
                        if origin and origin != choice.place_id
                        else 0
                    )
                    outbound = (
                        mobility.estimate_minutes(choice.place_id, next_anchor[1])
                        if choice.place_id != next_anchor[1]
                        else 0
                    )
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
                            opens_at=_at_local_time(opening.get("open")),
                            closes_at=_at_local_time(opening.get("close")),
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
                            "origin_key": origin,
                            "inbound_travel_min": inbound,
                            "outbound_travel_min": outbound,
                            "safety_buffer_min": 15,
                        }
            if index > 0 and family == "F0_SAME_SLOT_REPLACEMENT":
                family = "F0_ALTERNATE_REPLACEMENT"
            heuristic_specs.append(
                _ReplanCandidateSpec(
                    family=family,
                    replacement_choice=choice,
                    window_evidence=window_evidence,
                )
            )
        if (
            affected is not None
            and affected.id not in protected_activity_ids
            and not affected.locked
        ):
            heuristic_specs.append(
                _ReplanCandidateSpec(
                    family="F1_OPTIONAL_REMOVAL",
                    replacement_choice=None,
                    candidate_remove=True,
                )
            )
    elif delay_minutes:
        heuristic_specs.append(
            _ReplanCandidateSpec(
                family="F2_SUFFIX_DELAY",
                replacement_choice=None,
                candidate_delay=delay_minutes,
            )
        )
        if (
            affected is not None
            and affected.id not in protected_activity_ids
            and not affected.locked
        ):
            heuristic_specs.append(
                _ReplanCandidateSpec(
                    family="F1_OPTIONAL_REMOVAL",
                    replacement_choice=None,
                    candidate_remove=True,
                )
            )
    elif remove_affected:
        heuristic_specs.append(
            _ReplanCandidateSpec(
                family="F1_OPTIONAL_REMOVAL",
                replacement_choice=None,
                candidate_remove=True,
            )
        )
    else:
        heuristic_specs.append(
            _ReplanCandidateSpec(family="F0_STABLE_COPY", replacement_choice=None)
        )

    traveler_preferences = planning_preference_items(session, journey.traveler_id, journey.id)

    solver_attempt: SolverAttempt | None = None
    solver_specs: list[_ReplanCandidateSpec] = []
    solver_fallback_reason = (
        "SOLVER_DISABLED" if solver_mode == "deterministic" else "SOLVER_V1_UNSUPPORTED"
    )
    current_location = _activity_location(current_execution or previous_affected)
    journey_start = datetime.fromisoformat(journey.start_at)
    journey_end = datetime.fromisoformat(journey.end_at)

    def _minute_from_start(value: datetime) -> int:
        return int((value - journey_start).total_seconds() // 60)

    anchor_activity = None
    if future_anchor is not None:
        anchor_start, anchor_semantic = future_anchor
        anchor_activity = next(
            (
                item
                for item in source
                if (item.place_id or item.city_service_id or item.id) == anchor_semantic
                and datetime.fromisoformat(item.start_at) == anchor_start
            ),
            None,
        )
    if solver_mode == "v2" and current_location is not None and v2_choice_pools:
        v2_slots: list[SolverV2Slot] = []
        v2_choices: dict[tuple[str, str], Any] = {}
        secondary_risk_ids = set(impact_resolution.secondary_risk_activity_ids)
        journey_end_min = max(1, _minute_from_start(journey_end))
        for item in source:
            choices = v2_choice_pools.get(item.id)
            if choices is None:
                continue
            original_start_min = max(0, _minute_from_start(datetime.fromisoformat(item.start_at)))
            original_end_min = min(
                journey_end_min, _minute_from_start(datetime.fromisoformat(item.end_at))
            )
            duration_min = max(1, original_end_min - original_start_min)
            item_place = session.get(Place, item.place_id) if item.place_id else None
            opening = (
                normalize_opening_hours(json.loads(item_place.opening_hours_json or "{}"))
                if item_place
                else {"status": "UNKNOWN"}
            )
            if item_place is not None and opening.get("status") not in {"NORMALIZED_VALID"}:
                opening = {"status": "UNKNOWN"}
            opens_at = _at_local_time(opening.get("open"))
            closes_at = _at_local_time(opening.get("close"))
            earliest_start_min = max(0, _minute_from_start(opens_at)) if opens_at else 0
            latest_end_min = (
                min(journey_end_min, _minute_from_start(closes_at))
                if closes_at
                else journey_end_min
            )
            if latest_end_min <= earliest_start_min:
                continue
            must_change = item.id == affected_activity_id
            slot_options: list[SolverV2Option] = []
            if not must_change:
                slot_options.append(
                    SolverV2Option(
                        option_key=f"KEEP:{item.id}",
                        location_key=_activity_location(item) or item.id,
                        action="KEEP",
                        duration_min=duration_min,
                        cost_minor=item.estimated_cost_minor,
                        earliest_start_min=earliest_start_min,
                        latest_end_min=latest_end_min,
                        original_start_min=original_start_min,
                        original_cost_minor=item.estimated_cost_minor,
                        risk_penalty_milli=500 if item.id in secondary_risk_ids else 0,
                    )
                )
            for choice in choices:
                candidate_place = session.get(Place, choice.place_id)
                if candidate_place is None:
                    continue
                candidate_opening = normalize_opening_hours(
                    json.loads(candidate_place.opening_hours_json or "{}")
                )
                if candidate_opening.get("status") != "NORMALIZED_VALID":
                    continue
                candidate_opens = _at_local_time(candidate_opening.get("open"))
                candidate_closes = _at_local_time(candidate_opening.get("close"))
                candidate_earliest = (
                    max(0, _minute_from_start(candidate_opens)) if candidate_opens else 0
                )
                candidate_latest = (
                    min(journey_end_min, _minute_from_start(candidate_closes))
                    if candidate_closes
                    else journey_end_min
                )
                if candidate_latest <= candidate_earliest:
                    continue
                candidate_tags = set(json.loads(candidate_place.tags_json or "[]"))
                preference_fit = verified_interest_preference_fit(
                    traveler_preferences, candidate_tags=candidate_tags
                )
                slot_options.append(
                    SolverV2Option(
                        option_key=f"REPLACE:{item.id}:{choice.place_id}",
                        location_key=choice.place_id,
                        action="REPLACE",
                        duration_min=choice.duration_min,
                        cost_minor=choice.cost_minor,
                        earliest_start_min=candidate_earliest,
                        latest_end_min=candidate_latest,
                        original_start_min=original_start_min,
                        original_cost_minor=item.estimated_cost_minor,
                        preference_milli=round(
                            (0.5 if preference_fit is None else preference_fit) * 1000
                        ),
                    )
                )
                v2_choices[(item.id, f"REPLACE:{item.id}:{choice.place_id}")] = choice
            if not slot_options:
                continue
            v2_slots.append(
                SolverV2Slot(
                    slot_key=item.id,
                    sequence_no=int(item.sequence_no),
                    original_location_key=_activity_location(item) or item.id,
                    original_start_min=original_start_min,
                    original_end_min=original_end_min,
                    original_cost_minor=item.estimated_cost_minor,
                    options=tuple(slot_options),
                    must_change=must_change,
                    allow_drop=not must_change,
                )
            )
        v2_anchors: list[SolverV2Anchor] = []
        for semantic, start_at in c4_anchors:
            anchor_start = datetime.fromisoformat(start_at)
            if anchor_start < effective_event_time:
                continue
            anchor_activity_row = next(
                (
                    item
                    for item in source
                    if (item.place_id or item.city_service_id or item.id) == semantic
                    and datetime.fromisoformat(item.start_at) == anchor_start
                ),
                None,
            )
            anchor_location = _activity_location(anchor_activity_row) or semantic
            anchor_duration = (
                max(
                    1,
                    _minute_from_start(datetime.fromisoformat(anchor_activity_row.end_at))
                    - _minute_from_start(datetime.fromisoformat(anchor_activity_row.start_at)),
                )
                if anchor_activity_row is not None
                else 60
            )
            v2_anchors.append(
                SolverV2Anchor(
                    key=f"{semantic}@{anchor_start.isoformat()}",
                    location_key=anchor_location,
                    start_min=max(0, _minute_from_start(anchor_start)),
                    duration_min=anchor_duration,
                )
            )
        if v2_slots:
            v2_problem = SolverV2Problem(
                journey_id=journey.id,
                operation_key=mobility.operation_key or f"replan:{trigger_id}",
                now_min=max(0, _minute_from_start(effective_event_time)),
                journey_end_min=journey_end_min,
                budget_ceiling_minor=journey.budget_amount_minor,
                base_cost_minor=sum(
                    item.estimated_cost_minor
                    for item in source
                    if item.id not in {slot.slot_key for slot in v2_slots}
                ),
                current_location_key=current_location,
                slots=tuple(v2_slots),
                protected_anchors=tuple(v2_anchors),
                frozen_mobility_snapshot_id=mobility.snapshot_id,
                travel_minutes={pair: fact.minutes for pair, fact in mobility.facts.items()},
                safety_buffer_min=15,
                top_k=body.candidate_count,
            )
            v2_plans = solve_v2(v2_problem)
            solver_fallback_reason = "SOLVER_V2_NO_FEASIBLE_PLAN"
            for plan in v2_plans:
                solver_specs.append(
                    _ReplanCandidateSpec(
                        family="V2_WHOLE_HORIZON",
                        replacement_choice=None,
                        solver_provenance={
                            "kind": plan.generator_kind,
                            "solver_status": "FEASIBLE",
                            "terminal_status": "TOP_K",
                            "problem_fingerprint": solver_v2_problem_fingerprint(v2_problem),
                            "mobility_snapshot_id": mobility.snapshot_id,
                            "assignment_fingerprint": plan.fingerprint,
                            "rank": plan.generator_rank,
                            "objective": dict(plan.objective_breakdown),
                            "protected_anchor_count": len(plan.protected_anchors),
                        },
                        v2_plan=plan,
                        v2_choices=v2_choices,
                    )
                )
            if v2_plans:
                solver_fallback_reason = "SOLVER_V2_CANDIDATE_SET_COMPLEMENT"
    supports_solver_v1 = (
        solver_mode in {"ortools", "auto"}
        and trigger_event.event_type in {"CLOSURE", "WEATHER"}
        and affected is not None
        # V1 models only the disrupted current slot through the next C4 anchor.
        # Future affected Activities with intervening mutable Activities remain
        # on the deterministic path until a later multi-slot solver contract.
        and current_execution is not None
        and affected.id == current_execution.id
        and affected.id not in protected_activity_ids
        and not affected.locked
        and bool(replacement_choices)
        and current_location is not None
        and future_anchor is not None
        and anchor_activity is not None
    )
    if supports_solver_v1:
        budget_remaining = max(
            0,
            journey.budget_amount_minor
            - (sum(item.estimated_cost_minor for item in source) - affected.estimated_cost_minor),
        )
        replacement_by_key = {choice.place_id: choice for choice in replacement_choices}
        solver_options: list[SolverReplacementOption] = []
        for choice in sorted(replacement_choices, key=lambda item: item.place_id):
            candidate_place = session.get(Place, choice.place_id)
            opening = json.loads(candidate_place.opening_hours_json or "{}")
            opens_at = _at_local_time(opening.get("open"))
            closes_at = _at_local_time(opening.get("close"))
            if opens_at is None or closes_at is None or closes_at <= opens_at:
                continue
            earliest_start_min = max(0, _minute_from_start(opens_at))
            latest_end_min = _minute_from_start(closes_at)
            if latest_end_min <= earliest_start_min:
                continue
            candidate_tags = set(json.loads(candidate_place.tags_json or "[]"))
            solver_preference_fit = verified_interest_preference_fit(
                traveler_preferences, candidate_tags=candidate_tags
            )
            solver_preference_milli = round(
                (0.5 if solver_preference_fit is None else solver_preference_fit) * 1000
            )
            solver_options.append(
                SolverReplacementOption(
                    option_key=choice.place_id,
                    location_key=choice.place_id,
                    duration_min=choice.duration_min,
                    cost_minor=choice.cost_minor,
                    earliest_start_min=earliest_start_min,
                    latest_end_min=latest_end_min,
                    original_start_min=max(
                        0, _minute_from_start(datetime.fromisoformat(affected.start_at))
                    ),
                    preference_milli=solver_preference_milli,
                )
            )
        if solver_options:
            terminal_ids = set(partition.terminal_prefix_ids)
            problem = ReplanSolverProblem(
                journey_id=journey.id,
                operation_key=mobility.operation_key or f"replan:{trigger_id}",
                now_min=max(0, _minute_from_start(effective_event_time)),
                journey_end_min=_minute_from_start(journey_end),
                budget_remaining_minor=budget_remaining,
                current_location_key=current_location,
                next_anchor=SolverAnchor(
                    semantic_key=future_anchor[1],
                    location_key=_activity_location(anchor_activity) or future_anchor[1],
                    start_min=_minute_from_start(future_anchor[0]),
                    duration_min=max(
                        1,
                        int(
                            (
                                datetime.fromisoformat(anchor_activity.end_at)
                                - datetime.fromisoformat(anchor_activity.start_at)
                            ).total_seconds()
                            // 60
                        ),
                    ),
                ),
                replacement_options=tuple(solver_options),
                frozen_mobility_snapshot_id=mobility.snapshot_id,
                travel_minutes={pair: fact.minutes for pair, fact in mobility.facts.items()},
                completed_prefix_keys=tuple(
                    str(item.place_id or item.city_service_id or item.id)
                    for item in source
                    if item.id in terminal_ids
                ),
                safety_buffer_min=15,
                allow_drop=True,
            )
            solver_attempt = generate_solver_candidates(
                problem,
                mode=solver_mode,
                candidate_count=body.candidate_count,
                random_seed=settings.solver_random_seed,
                max_time_seconds=settings.solver_max_time_seconds,
            )
            solver_fallback_reason = solver_attempt.fallback_reason or "ORTOOLS_POST_GATE_FALLBACK"
            for candidate in solver_attempt.candidates:
                if candidate.dropped:
                    solver_specs.append(
                        _ReplanCandidateSpec(
                            family="F1_OPTIONAL_REMOVAL",
                            replacement_choice=None,
                            candidate_remove=True,
                            solver_provenance=solver_attempt.evidence_for(candidate),
                        )
                    )
                    continue
                choice = replacement_by_key.get(str(candidate.option_key))
                if choice is None or candidate.start_min is None:
                    continue
                solver_specs.append(
                    _ReplanCandidateSpec(
                        family="F4_ORTOOLS_WINDOW_REPLACEMENT",
                        replacement_choice=choice,
                        explicit_candidate_start_at=journey_start
                        + timedelta(minutes=candidate.start_min),
                        solver_provenance=solver_attempt.evidence_for(candidate),
                    )
                )
        else:
            solver_fallback_reason = "SOLVER_NO_ELIGIBLE_OPTIONS"

    fallback_status = (
        solver_attempt.terminal_status
        if solver_attempt is not None
        else "DISABLED"
        if solver_mode == "deterministic"
        else "UNSUPPORTED"
    )
    fallback_problem_fingerprint = (
        solver_attempt.problem_fingerprint if solver_attempt is not None else None
    )
    if solver_attempt is not None and solver_attempt.used_solver:
        heuristic_fallback_reason = "ORTOOLS_CANDIDATE_SET_COMPLEMENT"
    elif solver_attempt is not None and solver_attempt.fallback_reason:
        heuristic_fallback_reason = solver_attempt.fallback_reason
    else:
        heuristic_fallback_reason = solver_fallback_reason

    # Keep all deterministic assignments behind solver specs. Successful solver
    # assignments suppress duplicates only after they pass the authoritative gate.
    # If a solver schedule is rejected, the same semantic option can still be
    # rescued by the deterministic schedule.
    fallback_specs: list[_ReplanCandidateSpec] = []
    for spec in heuristic_specs:
        fallback_specs.append(
            _ReplanCandidateSpec(
                family=spec.family,
                replacement_choice=spec.replacement_choice,
                candidate_delay=spec.candidate_delay,
                candidate_remove=spec.candidate_remove,
                window_evidence=spec.window_evidence,
                solver_provenance={
                    "kind": "DETERMINISTIC_HEURISTIC",
                    "solver_status": fallback_status,
                    "fallback_reason": heuristic_fallback_reason,
                    "problem_fingerprint": fallback_problem_fingerprint,
                    "mobility_snapshot_id": mobility.snapshot_id,
                },
            )
        )
    specs = solver_specs + fallback_specs
    if solver_specs and body.candidate_count >= 3 and solver_mode in {"ortools", "auto"}:
        # A solver run is a source of ranked candidates, not permission to
        # hide the deterministic complement.  Keep the best solver assignment
        # first, then retain the two stable recovery families that make the
        # candidate set explainable across runtime modes.  This matters for
        # the legacy Golden contract and for operators comparing solver output
        # with the opportunity-window evidence; it does not alter the selected
        # V2 plan when candidate_count is one.
        first_solver = solver_specs[0]
        complement = [
            item
            for family in ("F0_SAME_SLOT_REPLACEMENT", "F3_OPPORTUNITY_WINDOW")
            for item in fallback_specs
            if item.family == family
        ]
        reserved = {id(item) for item in complement}
        specs = [first_solver, *complement, *solver_specs[1:]] + [
            item for item in fallback_specs if id(item) not in reserved
        ]
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
    before_envelope = _envelope_payload(
        journey,
        source,
        preserved_commitment_count=c4_count,
        degraded_providers=mobility_degraded_providers,
    )

    def _frozen_route_total(items: list[Activity]) -> int:
        total = 0
        for previous, current in zip(items, items[1:]):
            origin = _activity_location(previous)
            destination = _activity_location(current)
            if not origin or not destination or origin == destination:
                continue
            total += int(mobility.estimate_minutes(origin, destination))
        return total

    base_route_total = _frozen_route_total(source)
    created: list[ReplanProposalModel] = []
    failed_reasons: set[str] = set()
    accepted_assignment_keys: set[str] = set()
    rejected_solver_assignment_keys: set[str] = set()

    def _spec_assignment_key(spec: _ReplanCandidateSpec) -> str:
        if spec.v2_plan is not None:
            return f"V2:{spec.v2_plan.fingerprint}"
        if spec.candidate_remove:
            return "DROP"
        if spec.replacement_choice is not None:
            # A solver schedule and its deterministic complement may target
            # the same place while proving different visit times.  Keep those
            # candidates distinct so a post-gate solver result does not erase
            # the explainable same-slot/opportunity-window alternatives.
            scheduled_start = (
                spec.explicit_candidate_start_at.isoformat()
                if spec.explicit_candidate_start_at is not None
                else "heuristic"
            )
            return f"{spec.family}:{spec.replacement_choice.place_id}:{scheduled_start}"
        return spec.family

    for generation_rank, spec in enumerate(specs):
        if len(created) >= body.candidate_count:
            break
        assignment_key = _spec_assignment_key(spec)
        if assignment_key in accepted_assignment_keys:
            continue
        family = spec.family
        replacement_choice = spec.replacement_choice
        candidate_delay = spec.candidate_delay
        candidate_remove = spec.candidate_remove
        window_evidence = spec.window_evidence
        v2_assignments = (
            {item.slot_key: item for item in spec.v2_plan.assignments}
            if spec.v2_plan is not None
            else {}
        )
        v2_choices = spec.v2_choices or {}
        generator_evidence = dict(spec.solver_provenance or {})
        generator_evidence.setdefault("kind", "DETERMINISTIC_HEURISTIC")
        if (
            generator_evidence.get("kind") == "DETERMINISTIC_HEURISTIC"
            and assignment_key in rejected_solver_assignment_keys
        ):
            generator_evidence["fallback_reason"] = "ORTOOLS_POST_GATE_FALLBACK"
        generator_evidence.setdefault("rank", generation_rank)
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
            v2_assignment = v2_assignments.get(activity.id)
            if v2_assignment is not None and v2_assignment.action == "DROP":
                continue
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
            if v2_assignment is not None and v2_assignment.action == "REPLACE":
                replacement_choice = v2_choices.get((activity.id, str(v2_assignment.option_key)))
                if replacement_choice is None:
                    failed_reasons.add("SOLVER_V2_OPTION_NOT_MATERIALIZED")
                    continue
                start_dt = journey_start + timedelta(minutes=int(v2_assignment.start_min or 0))
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
                                "replaced_place_id": activity.place_id,
                                "solver_v2_assignment": v2_assignment.option_key,
                            },
                            sort_keys=True,
                        ),
                    }
                )
            elif v2_assignment is not None and v2_assignment.action == "KEEP":
                start_dt = journey_start + timedelta(minutes=int(v2_assignment.start_min or 0))
                end_dt = journey_start + timedelta(minutes=int(v2_assignment.end_min or 0))
                row.update(
                    {
                        "start_at": start_dt.isoformat(),
                        "end_at": end_dt.isoformat(),
                        "metadata_json": json.dumps(
                            {
                                "candidate_family": family,
                                "replan_reason_codes": ("SOLVER_V2_KEEP",),
                            },
                            sort_keys=True,
                        ),
                    }
                )
            elif replacement_choice is not None and activity.id == affected_activity_id:
                start_dt = datetime.fromisoformat(activity.start_at)
                if spec.explicit_candidate_start_at is not None:
                    start_dt = spec.explicit_candidate_start_at
                elif family == "F3_OPPORTUNITY_WINDOW" and window_evidence is not None:
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
                    row["travel_from_prev_min"] = (
                        0
                        if origin == destination
                        else int(mobility.estimate_minutes(origin, destination))
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
            mobility_provider=mobility,
        )
        if not gate.passed:
            failed_reasons.update(gate.failures)
            if generator_evidence.get("kind") == "ORTOOLS_CP_SAT":
                rejected_solver_assignment_keys.add(assignment_key)
            session.execute(delete(Activity).where(Activity.plan_version_id == proposed.id))
            session.delete(proposed)
            session.flush()
            continue

        proposed.mobility_snapshot_id = mobility.snapshot_id
        proposed.mobility_evidence_json = json.dumps(
            _recovery_plan_evidence(copied), ensure_ascii=False, sort_keys=True, default=str
        )

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
        after_envelope = _envelope_payload(
            journey,
            copied,
            preserved_commitment_count=c4_count,
            degraded_providers=mobility_degraded_providers,
        )
        travel_delta = _frozen_route_total(copied) - base_route_total
        preference_fit = None
        opportunity_value = None
        if spec.v2_plan is not None:
            preference_milli = int(spec.v2_plan.objective_breakdown.get("preference_milli", 0))
            slot_count = max(1, len(spec.v2_plan.assignments))
            preference_fit = min(1.0, max(0.0, preference_milli / (1000 * slot_count)))
        elif replacement_choice is not None:
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
        if spec.v2_plan is not None:
            reason_codes.append("SOLVER_V2_WHOLE_HORIZON")
            if spec.v2_plan.risk_score:
                reason_codes.append("RISK_PENALTY_OPTIMIZED")
        elif replacement_choice is not None:
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
                        "baseline_plan_evidence": baseline_plan_evidence,
                        "incident_recovery_evidence": incident_recovery_evidence,
                        "impact_resolution": {
                            "status": impact_resolution.status,
                            "maturity_stage": impact_resolution.maturity_stage,
                            "provider_key": impact_resolution.provider_key,
                            "model_key": impact_resolution.model_key,
                            "selected_activity_id": impact_resolution.selected_activity_id,
                            "primary_recovery_target_id": impact_resolution.primary_recovery_target_id,
                            "secondary_risk_activity_ids": list(
                                impact_resolution.secondary_risk_activity_ids
                            ),
                            "selected_corroboration_refs": list(
                                impact_resolution.selected_corroboration_refs
                            ),
                            "independent_evidence_count": impact_resolution.independent_evidence_count,
                            "uncertain": impact_resolution.uncertain,
                            "reason_codes": list(impact_resolution.validation.reason_codes),
                            "rejected_activity_ids": list(
                                impact_resolution.validation.rejected_activity_ids
                            ),
                            "failure_code": impact_resolution.failure_code,
                            "response_hash": impact_resolution.response_hash,
                            "semantic_reason": impact_resolution.semantic_reason,
                            "semantic_explanation": selected_impact_explanation,
                        },
                        "generation_rank": generation_rank,
                        "generator": generator_evidence,
                        "feasibility_authority": "CITYNEXUS_DETERMINISTIC_GATE",
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
                            "provider": mobility.source_provider_key,
                            "degraded": mobility.degraded,
                            "snapshot": mobility.to_evidence(),
                            "failed_primary_pairs": [
                                list(pair) for pair in mobility_capture.failed_primary_pairs
                            ],
                            "fallback_pairs": [
                                list(pair) for pair in mobility_capture.fallback_pairs
                            ],
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
                    "summary": "Reality-aware recovery proposal",
                    "reasons": [
                        "provider-backed recovery evidence",
                        family,
                        impact_resolution.semantic_reason,
                    ],
                    "impact_type": trigger_event.event_type,
                    "impact_provider": impact_resolution.provider_key,
                    "impact_model": impact_resolution.model_key,
                    "baseline_snapshot_id": frozen_v12_evidence.get("snapshot_id"),
                    "incident_snapshot_id": mobility.snapshot_id,
                    "protected_commitments": c4_count,
                    "source": generator_evidence["kind"],
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
            after={
                "status": proposal.status,
                "candidate_family": family,
                "generator": generator_evidence,
                "feasibility_authority": "CITYNEXUS_DETERMINISTIC_GATE",
            },
        )
        created.append(proposal)
        accepted_assignment_keys.add(assignment_key)

    if not created:
        session.rollback()
        details = ", ".join(sorted(failed_reasons)) or "NO_DISTINCT_CANDIDATE"
        raise HTTPException(422, f"no feasible replan proposal: {details}")

    record_audit(
        session,
        action="solver_candidates_generated",
        entity_type="Journey",
        entity_id=journey.id,
        journey_id=journey.id,
        after={
            "proposal_ids": [item.id for item in created],
            "candidate_count": len(created),
            "feasibility_authority": "CITYNEXUS_DETERMINISTIC_GATE",
        },
    )

    # Python sort is stable, so exact-score ties preserve deterministic
    # candidate-generation order instead of using UUID4 as a random tiebreak.
    # Prefer lower disruption when utility is equal; a noisier candidate must
    # not outrank an otherwise equal, more stable repair.
    def _proposal_rank(candidate: ReplanProposalModel) -> tuple[float, float, float, float, float]:
        breakdown = json.loads(candidate.score_breakdown_json or "{}")
        generator = json.loads(candidate.diff_json or "{}").get("verified_evidence", {}).get(
            "generator", {}
        )
        # An explicit V2 request is a product-level request for the whole-
        # horizon CP-SAT schedule.  Deterministic complements remain persisted
        # for explainability, but must not outrank a feasible V2 assignment
        # merely because a heuristic preference score is slightly higher.
        solver_priority = (
            0.0
            if solver_mode == "v2" and generator.get("kind") == "ORTOOLS_CP_SAT_V2"
            else 1.0
        )
        return (
            solver_priority,
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
    return _accept_replan_impl(proposal_id, idempotency_key, session)


def _accept_replan_impl(
    proposal_id: UUID,
    idempotency_key: str | None,
    session: Session,
    *,
    actor_type: str = "system",
    actor_id: str | None = None,
    policy_version: int | None = None,
    authorization_decision: str | None = None,
    reason_codes: tuple[str, ...] = (),
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
    accepted_mobility = _proposal_mobility_snapshot(proposal)
    if accepted_mobility is None:
        raise HTTPException(
            409, "replan mobility evidence is missing or invalid; regenerate proposal"
        )
    gate = validate_plan_feasibility(
        session,
        journey,
        proposed,
        include_active_c4=True,
        mobility_provider=accepted_mobility,
    )
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
        time_boundary = (
            "END"
            if str(policy.get("anchor_role") or "").upper() == "DEPARTURE"
            else "START"
        )
        replacement = next(
            (
                activity
                for activity in proposed_activities
                if str(activity.place_id or activity.city_service_id or "") == semantic_key
                and datetime.fromisoformat(
                    activity.end_at if time_boundary == "END" else activity.start_at
                ).isoformat()
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
            actor_type=actor_type,
            actor_id=actor_id,
            after={
                "status": competitor.status,
                "reason": "base_plan_superseded",
                "policy_version": policy_version,
                "authorization_decision": authorization_decision,
                "reason_codes": list(reason_codes),
            },
        )

    record_audit(
        session,
        action="replan.accepted",
        entity_type="ReplanProposal",
        entity_id=proposal.id,
        journey_id=journey.id,
        actor_type=actor_type,
        actor_id=actor_id,
        after={
            "status": proposal.status,
            "policy_version": policy_version,
            "authorization_decision": authorization_decision,
            "reason_codes": list(reason_codes),
        },
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


def _copilot_context(session: Session, journey: Journey) -> dict[str, Any]:
    """Read selected-plan facts without refreshing or creating JourneyTwin state."""

    plan = session.get(PlanVersion, journey.active_plan_version_id) if journey.active_plan_version_id else None
    activities = (
        session.scalars(
            select(Activity)
            .where(Activity.plan_version_id == plan.id)
            .order_by(Activity.sequence_no)
        ).all()
        if plan is not None
        else []
    )
    legs = (
        session.scalars(
            select(JourneyLeg)
            .where(JourneyLeg.plan_version_id == plan.id)
            .order_by(JourneyLeg.sequence_no)
        ).all()
        if plan is not None
        else []
    )
    commitments = session.scalars(
        select(CommitmentModel)
        .where(CommitmentModel.journey_id == journey.id, CommitmentModel.status == "ACTIVE")
        .order_by(CommitmentModel.created_at, CommitmentModel.id)
    ).all()
    preferences = session.scalars(
        select(Preference)
        .where(Preference.traveler_id == journey.traveler_id)
        .order_by(Preference.category, Preference.preference_key)
    ).all()

    activity_payload = [
        {
            "id": item.id,
            "sequence_no": item.sequence_no,
            "title": item.title,
            "activity_type": item.activity_type,
            "start_at": item.start_at,
            "end_at": item.end_at,
            "status": item.status,
            "locked": bool(item.locked),
            "cost_minor": item.estimated_cost_minor,
        }
        for item in activities
    ]
    leg_payload = [
        {
            "id": item.id,
            "from_key": item.from_key,
            "to_key": item.to_key,
            "mode": item.mode,
            "duration_min": item.duration_min,
            "walking_min": item.walking_min,
            "provider_key": item.provider_key,
            "provenance": item.provenance,
        }
        for item in legs
    ]
    commitment_payload = []
    for item in commitments:
        policy = _json_object(item.policy_json)
        commitment_payload.append(
            {
                "id": item.id,
                "activity_id": item.activity_id,
                "kind": item.kind,
                "level": item.level,
                "protected": item.level in {"C3_Guaranteed", "C4_Anchored"},
                "scheduled_start_at": policy.get("scheduled_start_at"),
                "external_ref": item.external_ref,
            }
        )
    preference_payload = []
    for item in preferences:
        try:
            value = json.loads(item.value_json or "null")
        except json.JSONDecodeError:
            value = item.value_json
        preference_payload.append(
            {
                "category": item.category,
                "key": item.preference_key,
                "value": value,
                "weight": item.weight,
                "source": item.source,
            }
        )
    mobility_evidence = _json_object(plan.mobility_evidence_json) if plan is not None else {}
    return {
        "journey_id": journey.id,
        "city_code": journey.city_code,
        "timezone": journey.timezone,
        "currency": journey.budget_currency,
        "status": journey.status,
        "current_activity_id": journey.current_activity_id,
        "plan": (
            {
                "id": plan.id,
                "version_no": plan.version_no,
                "status": plan.status,
                "source": plan.source,
                "cost_minor": plan.total_cost_minor,
                "currency": plan.currency,
                "activities": activity_payload,
                "legs": leg_payload,
                "mobility_evidence": mobility_evidence,
            }
            if plan is not None
            else None
        ),
        "commitments": commitment_payload,
        "preferences": preference_payload,
        "protected_commitments": [item for item in commitment_payload if item["protected"]],
    }


def _copilot_fallback_or_ai(message: str, context: dict[str, Any]) -> CopilotInterpretation:
    fallback = classify_copilot_message(message)
    client = _deepseek_client()
    if client is None:
        return fallback
    plan = context.get("plan") or {}
    current_activity = next(
        (
            item
            for item in plan.get("activities", [])
            if str(item.get("id")) == str(context.get("current_activity_id"))
        ),
        None,
    )
    prompt_context = {
        "journey": {
            "id": context["journey_id"],
            "city_code": context["city_code"],
            "timezone": context["timezone"],
            "status": context["status"],
        },
        "selected_plan": {
            "id": plan.get("id"),
            "version_no": plan.get("version_no"),
            "status": plan.get("status"),
            "currency": plan.get("currency"),
            "cost_minor": plan.get("cost_minor"),
        },
        "current_activity": current_activity,
        "protected_commitments": context["protected_commitments"],
        "preferences": context["preferences"],
        "authority": (
            "The server owns ids, coordinates, prices, provider facts, commitments, "
            "and mutations. Return meaning only; do not claim an authoritative mutation."
        ),
    }
    try:
        envelope = compile_semantic_envelope(client, message, prompt_context)
        if envelope is None:
            return fallback
        decision = apply_semantic_policy(envelope)
        entities = dict(envelope.entities)
        if decision.event_type is not None:
            entities["event_type"] = decision.event_type
        entities["assertion_status"] = envelope.assertion_status
        entities["effective_time"] = envelope.effective_time
        semantic_payload = envelope.as_dict()
        semantic_payload.update(
            {
                "route_intent": decision.route_intent,
                "server_action": decision.action,
                "create_event": decision.create_event,
                "verify_evidence": decision.verify_evidence,
            }
        )
        return CopilotInterpretation(
            decision.route_intent,
            envelope.confidence,
            envelope.reasoning_summary or decision.reason,
            entities,
            "deepseek",
            False,
            semantic_payload,
        )
    except (DeepSeekResponsesError, TypeError, ValueError, json.JSONDecodeError, httpx.HTTPError):
        return fallback


def _copilot_answer(
    interpretation: CopilotInterpretation,
    context: dict[str, Any],
    *,
    locale: str,
    what_if: dict[str, Any] | None = None,
) -> str:
    plan = context.get("plan") or {}
    plan_label = (
        f"PlanVersion {plan.get('version_no')} ({plan.get('status')})"
        if plan
        else "no selected PlanVersion"
    )
    protected_count = len(context.get("protected_commitments", []))
    if what_if is not None:
        if what_if.get("status") == "NOT_SIMULATABLE_FROM_CURRENT_EVIDENCE":
            if locale == "zh":
                return "当前还没有已选的权威 PlanVersion。请先在住宿选择中选择一个通过供应商事实和确定性门控的方案，再预览时间或费用变化；本次试算没有修改行程。"
            return "There is no selected authoritative PlanVersion yet. Select a provider-backed plan in Stay Explorer before previewing time or cost changes; this preview changed nothing."
        return str(what_if["explanation"])
    if interpretation.intent == "EXPLAIN_PLAN":
        if locale == "zh":
            return f"当前使用 {plan_label}，服务器已核验 {protected_count} 个受保护承诺。解释基于已选方案事实，不会修改行程。"
        return f"The current journey uses {plan_label}; the server verified {protected_count} protected commitments. This explanation uses selected-plan facts and changes nothing."
    if interpretation.intent == "DISCOVER":
        return "我会基于当前城市和行程上下文搜索候选地点；搜索结果不会直接写入方案。" if locale == "zh" else "I can search candidates using the current city and journey context; discovery results will not write to the plan."
    if interpretation.intent == "PREFERENCE_CHANGE":
        return "已识别为偏好请求。当前只展示请求，不会静默修改 TravelerTwin；请通过明确的偏好更新动作继续。" if locale == "zh" else "I recognized a preference request. This response does not silently change the TravelerTwin; continue with an explicit preference update action."
    if interpretation.intent == "REPLAN_REQUEST":
        return "已识别为重新规划请求。需要通过现有确定性可行性和授权路径生成方案，不会由 Copilot 直接改写当前方案。" if locale == "zh" else "I recognized a replan request. The existing deterministic feasibility and authorization path must produce it; Copilot will not rewrite the current plan directly."
    if interpretation.intent == "VERIFY_FACT":
        return "这是一条尚未核实的旅行信息。我会先基于供应商或来源证据核验，不会先写入城市事件。" if locale == "zh" else "This is an unverified travel claim. It must be checked against provider or source evidence before becoming a city event."
    if interpretation.intent == "PERSONAL_ASSISTANCE":
        return "我识别到这是个人求助，需要按个人情况处理，不会把它当作城市天气或交通事件。" if locale == "zh" else "I recognized a personal assistance request; it will not be turned into a city weather or traffic event."
    if locale == "zh":
        return "我没有可靠识别这条请求。可以问我为什么这样安排、如果多待一小时会怎样、找一个室内地点，或报告正在发生的交通/天气变化。"
    return "I could not route this request reliably. Ask why the plan looks this way, what would happen if you stayed an hour longer, find an indoor place, or report a disruption that is happening now."


def _capture_copilot_disruption(
    session: Session, journey: Journey, message: str, interpretation: CopilotInterpretation
) -> dict[str, Any]:
    event_type = str(interpretation.entities.get("event_type") or disruption_event_type(message) or "")
    if event_type not in {"CLOSURE", "TRAFFIC_DELAY", "SCHEDULE_DELAY", "WEATHER"}:
        raise HTTPException(422, "a current disruption type is required")
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    semantic = interpretation.semantic_envelope or {}
    semantic_entities = semantic.get("entities") if isinstance(semantic.get("entities"), dict) else {}
    target = resolve_event_target(
        session,
        journey,
        event_type=event_type,
        semantic=semantic,
        now=now_dt,
    )
    resolved = target.resolution != "UNRESOLVED_REVIEW_REQUIRED"
    if not resolved:
        return {
            "id": None,
            "event_type": event_type,
            "status": "REVIEW_REQUIRED",
            "affected_activity_id": None,
            "occurred_at": None,
            "target_resolution": target.resolution,
            "requires_review": True,
            "effective_time": str(semantic.get("effective_time") or "FUTURE").upper(),
        }
    event = EventModel(
        id=str(uuid4()),
        journey_id=journey.id,
        provider_key="user-copilot",
        provenance="USER_REPORTED",
        event_type=event_type,
        severity=disruption_severity(message, event_type),
        status="DETECTED",
        affected_activity_id=target.activity_id,
        occurred_at=target.occurred_at,
        detected_at=now,
        payload_json=json.dumps(
            {
                "description": message,
                "source": "copilot",
                "simulation_only": False,
                "extra_minutes": 15 if event_type == "TRAFFIC_DELAY" else None,
                "semantic": {
                    "assertion_status": semantic.get("assertion_status", "ASSERTED"),
                    "effective_time": semantic.get("effective_time", "NOW"),
                    "event_type": event_type,
                    "requested_action": semantic.get("requested_action", "REQUEST_REPLAN"),
                    "subject_text": semantic_entities.get("subject_text"),
                    "temporal_expression": semantic_entities.get("temporal_expression"),
                    "target_resolution": target.resolution,
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        created_at=now,
    )
    session.add(event)
    session.flush()
    record_audit(
        session,
        action="copilot.disruption.captured",
        entity_type="Event",
        entity_id=event.id,
        journey_id=journey.id,
        actor_type="USER",
        actor_id=journey.traveler_id,
        after={"event_type": event_type, "source": "copilot"},
    )
    session.commit()
    return {
        "id": event.id,
        "event_type": event.event_type,
        "status": event.status,
        "affected_activity_id": event.affected_activity_id,
        "occurred_at": event.occurred_at,
        "target_resolution": target.resolution,
        "requires_review": not resolved,
    }


def _verify_copilot_fact(
    session: Session,
    journey: Journey,
    message: str,
    interpretation: CopilotInterpretation,
) -> dict[str, Any]:
    """Capture bounded, sourced evidence without promoting a claim to Event truth."""

    semantic = interpretation.semantic_envelope or {}
    entities = semantic.get("entities") if isinstance(semantic.get("entities"), dict) else {}
    subject = str(entities.get("subject_text") or message).strip()
    client = _deepseek_client()
    if client is None or not settings.deepseek_web_search_enabled:
        return {
            "status": "NOT_CONFIGURED",
            "query": subject,
            "observations": [],
            "event_created": False,
        }
    drafts = WebResearchProvider(client).search(
        f"Verify this travel disruption claim using official sources: {subject}",
        source_class="OFFICIAL_OR_OPERATOR",
    )
    rows: list[WebObservation] = []
    for item in drafts[:5]:
        row = session.scalar(
            select(WebObservation).where(
                WebObservation.journey_id == journey.id,
                WebObservation.evidence_fingerprint == item.evidence_fingerprint,
            )
        )
        if row is None:
            row = WebObservation(
                id=str(uuid4()),
                journey_id=journey.id,
                query=item.query,
                url=item.url,
                domain=item.domain,
                title=item.title,
                source_class=item.source_class,
                provider_key=item.provider_key,
                model_key=item.model_key,
                captured_at=item.captured_at,
                evidence_fingerprint=item.evidence_fingerprint,
                content_excerpt=item.content_excerpt,
                authority_status="NON_AUTHORITATIVE",
                created_at=item.captured_at,
            )
            session.add(row)
        rows.append(row)
    session.commit()
    return {
        "status": "EVIDENCE_CAPTURED_REVIEW_REQUIRED" if rows else "UNRESOLVED",
        "query": subject,
        "observations": [
            {
                "id": item.id,
                "title": item.title,
                "domain": item.domain,
                "captured_at": item.captured_at,
                "authority_status": item.authority_status,
            }
            for item in rows
        ],
        "event_created": False,
    }


@app.post("/api/v1/journeys/{journey_id}/copilot/messages")
async def copilot_message(
    journey_id: UUID, body: dict[str, Any], session: Session = Depends(get_session)
):
    journey = require(session, Journey, str(journey_id), "Journey")
    message = str(body.get("message") or "").strip()
    if not message:
        raise HTTPException(422, "message is required")
    context = _copilot_context(session, journey)
    interpretation = await asyncio.to_thread(_copilot_fallback_or_ai, message, context)
    locale = str(body.get("locale") or ("zh" if journey.timezone.startswith("Asia/") else "en"))
    locale = "zh" if locale.lower().startswith("zh") else "en"
    what_if = None
    event = None
    verification = None
    action = None
    semantic_allows_event = interpretation.semantic_envelope is None or bool(
        interpretation.semantic_envelope.get("create_event")
    )
    if interpretation.intent == "DISRUPTION_REPORT" and semantic_allows_event:
        event = _capture_copilot_disruption(session, journey, message, interpretation)
        if event["requires_review"]:
            action = "REVIEW_FUTURE_EVENT_TARGET"
            answer = (
                "已保留这条未来事件，但现有行程事实无法唯一定位受影响活动；在确认目标前不会启动恢复。"
                if locale == "zh"
                else "I preserved this future event, but current Journey facts do not identify one affected activity. Recovery will wait for target review."
            )
        else:
            action = "REQUEST_REPLAN"
            answer = (
                "已按行程中的权威时间和活动记录事件，下一步可打开恢复中心检查确定性重规划。"
                if locale == "zh"
                else "I recorded this event against the authoritative Journey activity and time. Open recovery to run deterministic replanning."
            )
    else:
        if interpretation.intent == "WHAT_IF":
            what_if = simulate_what_if(message, context)
            action = what_if.get("next_action")
        elif interpretation.intent == "DISCOVER":
            action = "REQUEST_PLACE_SEARCH"
        elif interpretation.intent == "PREFERENCE_CHANGE":
            action = "REQUEST_PREFERENCE_UPDATE"
        elif interpretation.intent == "REPLAN_REQUEST":
            action = "REQUEST_REPLAN"
        elif interpretation.intent == "EXPLAIN_PLAN":
            action = "REQUEST_PLAN_EXPLANATION"
        elif interpretation.intent == "VERIFY_FACT":
            action = "VERIFY_EVIDENCE"
            try:
                verification = await asyncio.to_thread(
                    _verify_copilot_fact, session, journey, message, interpretation
                )
            except (DeepSeekResponsesError, httpx.HTTPError, AttributeError):
                verification = {
                    "status": "FAILED_EXTERNAL",
                    "observations": [],
                    "event_created": False,
                }
        validate_proposed_action(action)
        answer = _copilot_answer(interpretation, context, locale=locale, what_if=what_if)
    agent_run = None
    if interpretation.intent in {"REPLAN_REQUEST", "DISRUPTION_REPORT"} and not (
        event and event.get("requires_review")
    ):
        native_status = native_hermes_status()
        if native_status.get("ready"):
            native = HermesNativeClient()
            native_mission_id = f"copilot-{uuid4()}"
            try:
                native_run = native.create_run(
                    mission_id=native_mission_id,
                    journey_id=journey.id,
                    input_text=message,
                    instructions=(
                        "Inspect this Journey and its protected commitments first. Use only CityNexus MCP tools. "
                        "Produce a proposal unless the Gateway explicitly permits the requested autonomy. "
                        "Never invent provider facts, IDs, timestamps, or mutation authority."
                    ),
                    autonomy="PLAN_ONLY",
                )
                agent_run = {
                    "run_id": native_run.run_id,
                    "status": native_run.status,
                    "runtime_identity": "HERMES_NATIVE_MCP",
                    "provider_key": "hermes-native",
                    "events_url": f"/api/v1/agent/hermes/runs/{native_run.run_id}/events",
                }
                answer = (
                    "已交给 Hermes 检查 Journey、受保护承诺和恢复证据；结果会以真实运行进度返回。"
                    if locale == "zh"
                    else "Hermes is inspecting the Journey, protected commitments, and recovery evidence; progress will come from the native run."
                )
            except (httpx.HTTPError, ValueError):
                agent_run = None
            finally:
                native.close()
    return {
        "message": answer,
        "mode": interpretation.mode,
        "verified_context_used": True,
        "intent": interpretation.payload(),
        "action": {"type": action} if action else None,
        "what_if": what_if,
        "event": event,
        "verification": verification,
        "agent_run": agent_run,
        "protected_commitments": context["protected_commitments"],
        "evidence": {
            "journey_id": context["journey_id"],
            "city_code": context["city_code"],
            "selected_plan_version_id": (context["plan"] or {}).get("id") if context["plan"] else None,
            "provider_facts": bool((context["plan"] or {}).get("mobility_evidence")) if context["plan"] else False,
            "simulation_only": bool(what_if),
        },
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
