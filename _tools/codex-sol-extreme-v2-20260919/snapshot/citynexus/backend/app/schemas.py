from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PlanningMode = Literal["balanced", "budget", "explore", "strict_schedule"]


class Money(BaseModel):
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, value: str) -> str:
        return value.upper()


class TravelerCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    email: str | None = None
    locale: str = "en-GB"
    timezone: str


class Traveler(TravelerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class PreferenceInput(BaseModel):
    category: str = Field(min_length=1)
    key: str = Field(min_length=1)
    value: Any
    weight: float = Field(ge=0, le=1)


class Preference(PreferenceInput):
    id: UUID
    traveler_id: UUID


class CapabilityInput(BaseModel):
    """Validated explicit capability input (JSON uses ``class``)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    code: str = Field(min_length=2, max_length=64)
    capability_class: str = Field(default="SOFT_PREFERENCE", alias="class")
    severity: Literal["HARD", "STRONG", "SOFT"] = "SOFT"
    params: dict[str, Any] = Field(default_factory=dict)
    scope: Literal["TRAVELER", "JOURNEY"] = "TRAVELER"
    source: str = Field(default="USER_CONFIRMED", min_length=1, max_length=64)
    provenance: str = Field(default="USER_STATED", min_length=1, max_length=120)
    explicit: bool = True
    confirmed: bool = False
    active: bool = True


class AgentPolicyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["ADVISORY", "ASSISTED", "AUTONOMOUS"] = "ADVISORY"
    auto_accept_replan: bool = False
    max_auto_replan_cost_delta_minor: int = Field(default=0, ge=0)
    max_auto_loss_minor: int = Field(default=0, ge=0)
    max_auto_schedule_drift_min: int = Field(default=0, ge=0)
    allowed_activity_types: list[str] = Field(default_factory=list, max_length=20)
    allowed_booking_types: list[str] = Field(default_factory=list, max_length=20)
    protected_commitment_levels: list[str] = Field(
        default_factory=lambda: ["C3_Guaranteed", "C4_Anchored"], max_length=5
    )
    allow_auto_commitment_management: bool = False
    allow_auto_when_provider_degraded: bool = False
    allow_auto_on_critical_event: bool = False


class AgentPolicy(AgentPolicyPayload):
    traveler_id: UUID
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class AgentToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=8, max_length=128)
    agent_id: str = Field(default="hermes", min_length=1, max_length=128)
    journey_id: UUID | None = None
    mission_id: UUID | None = None
    proposal_id: UUID | None = None
    trigger_event_id: UUID | None = None
    candidate_count: int = Field(default=3, ge=1, le=5)
    solver_mode: Literal["deterministic", "ortools", "auto", "v2"] | None = None
    city_code: str | None = Field(default=None, min_length=1, max_length=32)
    q: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    service_type: str | None = Field(default=None, max_length=80)
    approval_id: UUID | None = None
    activity_id: UUID | None = None
    replacement_activity_id: UUID | None = None
    replacement_place_id: str | None = Field(default=None, min_length=1, max_length=128)
    booking_id: UUID | None = None
    commitment_id: UUID | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    provider_key: str = Field(default="mock-booking", min_length=1, max_length=64)
    reason: str | None = Field(default=None, min_length=1, max_length=500)
    # Compatibility-only input. The gateway never treats this caller-owned
    # boolean as authorization; approvals are server-issued and user-bound.
    user_confirmed: bool = False


class AgentApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_method: Literal["USER_CONFIRMATION", "STEP_UP", "WEBAUTHN"] = "USER_CONFIRMATION"
    # A process-scoped demo proof for REQUIRE_STEP_UP. The production seam is
    # replaceable by a verified WebAuthn assertion without trusting the method
    # label itself.
    step_up_code: str | None = Field(default=None, min_length=4, max_length=128)


class AgentCommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str = Field(min_length=8, max_length=2000)
    requested_autonomy: Literal["PLAN_ONLY", "EXECUTE_WITHIN_BOUNDS"] = "EXECUTE_WITHIN_BOUNDS"


class GuardianAutopilotStart(BaseModel):
    interval_seconds: float | None = Field(default=None, gt=0, le=3600)


class CitySignalFixtureRequest(BaseModel):
    state: Literal["NORMAL", "DISRUPTED", "OUTAGE", "RISK_FORECAST"]
    payload: dict[str, Any] = Field(default_factory=dict)


class ResilienceRefreshRequest(BaseModel):
    mode: Literal["replay", "captured_replay", "live"] = "replay"


class RealCityDiscoveryRequest(BaseModel):
    query: str = Field(default="indoor cafe", min_length=1, max_length=120)
    radius_m: int = Field(default=2500, ge=100, le=5000)
    limit: int = Field(default=8, ge=1, le=20)
    mode: Literal["replay", "captured_replay", "live"] = "captured_replay"


class RealCityIntelligenceRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=1000)
    radius_m: int = Field(default=3000, ge=100, le=5000)
    limit: int = Field(default=8, ge=1, le=10)
    mode: Literal["replay", "captured_replay", "live"] = "captured_replay"
    candidate_count: int = Field(default=2, ge=1, le=4)
    require_fully_grounded: bool = False


class JourneyAnchor(BaseModel):
    at: datetime
    location: str = Field(min_length=1, max_length=240)
    place_id: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class JourneyCreate(BaseModel):
    traveler_id: UUID
    title: str = Field(min_length=1, max_length=160)
    city_code: str = Field(min_length=1)
    timezone: str
    start_at: datetime
    end_at: datetime
    budget: Money
    planning_mode: PlanningMode = "balanced"
    arrival_anchor: JourneyAnchor | None = None
    departure_anchor: JourneyAnchor | None = None
    party_size: int = Field(default=1, ge=1, le=20)
    occupancy: dict[str, Any] = Field(default_factory=dict)
    stay_budget: Money | None = None

    @model_validator(mode="after")
    def valid_window(self) -> JourneyCreate:
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class JourneyPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    start_at: datetime | None = None
    end_at: datetime | None = None
    budget: Money | None = None


class Journey(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    traveler_id: UUID
    title: str
    city_code: str
    timezone: str
    start_at: datetime
    end_at: datetime
    budget: Money
    planning_mode: PlanningMode = "balanced"
    status: Literal["DRAFT", "PLANNED", "ACTIVE", "COMPLETED", "CANCELLED"]
    active_plan_version_id: UUID | None = None
    current_activity_id: UUID | None = None


class MobilityModeRequest(BaseModel):
    mode: Literal["WALK", "BICYCLE", "TRANSIT", "AUTO", "RIDE_HAIL"]


class WeatherDisruptionRequest(BaseModel):
    state: Literal["NORMAL", "RAIN", "SEVERE_RAIN", "TRANSIT_DISRUPTION"]


class StayPlanGenerateRequest(BaseModel):
    query: str = Field(default="stay-aware journey", min_length=1, max_length=500)
    weather_state: Literal["NORMAL", "RAIN", "SEVERE_RAIN", "TRANSIT_DISRUPTION"] = "NORMAL"
    candidate_count: int = Field(default=4, ge=3, le=8)
    sort: Literal["BEST_FOR_JOURNEY", "CHEAPEST", "LEAST_TRAVEL", "MOST_FLEXIBLE"] = (
        "BEST_FOR_JOURNEY"
    )


class StayModeChangeRequest(BaseModel):
    mode: Literal["WALK", "BICYCLE", "TRANSIT", "AUTO", "RIDE_HAIL"]
    from_key: str | None = None
    to_key: str | None = None


class StayAutopilotRecoveryRequest(BaseModel):
    state: Literal["RAIN", "SEVERE_RAIN", "TRANSIT_DISRUPTION"] = "RAIN"


class LuggageContextRequest(BaseModel):
    baggage_present: bool = True
    baggage_size_class: Literal["NONE", "CABIN", "MEDIUM", "HEAVY"] = "MEDIUM"
    luggage_drop_required: bool = True


class ReservationImportRequest(BaseModel):
    artifact_type: Literal["STRUCTURED_JSON", "ICS", "TEXT"]
    payload: dict[str, Any]


class ReservationTextExtractionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class ReservationVisionRequest(BaseModel):
    image_url: str = Field(min_length=8, max_length=12_000_000)
    hint: str = Field(default="booking confirmation", max_length=200)


class ReservationDraftPatchRequest(BaseModel):
    reservation_type: str | None = Field(default=None, min_length=1, max_length=40)
    confirmation_ref: str | None = Field(default=None, max_length=120)
    origin: dict[str, Any] | None = None
    destination: dict[str, Any] | None = None
    scheduled_departure_at: str | None = None
    scheduled_arrival_at: str | None = None
    price_amount_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    anchor_role: Literal["ARRIVAL", "DEPARTURE", "MID_TRIP", "UNKNOWN"] | None = None
    semantic_node_key: str | None = Field(default=None, max_length=200)
    semantic_target: dict[str, Any] | None = None


class WebResearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    source_class: Literal["OFFICIAL_NOTICE", "OPERATOR_NOTICE", "OPEN_WEB"] = "OPEN_WEB"


class ScheduleChangeRequest(BaseModel):
    estimated_arrival_at: datetime
    status: Literal["DELAYED", "CANCELLED", "RESCHEDULED"] = "DELAYED"
    provider_key: str = Field(default="captured-transit-status", min_length=1, max_length=80)
    captured_at: datetime
    service_alert: str | None = Field(default=None, max_length=500)


class LocationObservationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float = Field(gt=0, le=10000)
    captured_at: datetime


class PushSubscriptionRequest(BaseModel):
    endpoint: str = Field(min_length=8, max_length=2048)
    keys: dict[str, str] = Field(default_factory=dict)


class EdgeDeviceCreateRequest(BaseModel):
    display_name: str = Field(default="Trip companion", min_length=1, max_length=80)


class EdgeActionRequest(BaseModel):
    action: Literal["ACKNOWLEDGE", "NEXT", "REJECT_PROPOSAL", "SOS"]
    payload: dict[str, Any] = Field(default_factory=dict)


class EdgeObservationRequest(BaseModel):
    observation_type: Literal["RAIN", "SOS", "TEMP", "ACK"]
    payload: dict[str, Any] = Field(default_factory=dict)
    option_id: UUID | None = None


class ConstraintInput(BaseModel):
    kind: Literal["HARD", "SOFT"]
    category: str
    rule_code: str
    params: dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0)


class Constraint(ConstraintInput):
    id: UUID
    journey_id: UUID
    active: bool


class GeoPoint(BaseModel):
    latitude: float
    longitude: float


class Place(BaseModel):
    id: str
    name: str
    category: str
    city_code: str
    location: GeoPoint
    tags: list[str] = Field(default_factory=list)


class CityService(BaseModel):
    id: str
    name: str
    service_type: str
    city_code: str
    place_id: str | None = None


class Activity(BaseModel):
    id: UUID
    sequence_no: int = Field(ge=1)
    title: str
    activity_type: str = "visit"
    place_id: str | None = None
    city_service_id: str | None = None
    start_at: datetime
    end_at: datetime
    travel_from_prev_min: int = Field(default=0, ge=0)
    estimated_cost: Money
    # Whether the amount is a real, provider-backed fact.  ``KNOWN_FREE`` is a
    # genuine 0 (a free attraction), ``UNKNOWN`` means no price evidence exists,
    # and ``KNOWN_PAID`` carries a real amount.  Collapsing UNKNOWN into 0 made
    # free attractions read "暂无价格" and paid ones look free.
    cost_status: str = "UNKNOWN"
    status: Literal["PLANNED", "READY", "NOT_STARTED", "EN_ROUTE", "ARRIVED", "IN_PROGRESS", "ACTIVE", "COMPLETED", "SKIPPED", "CANCELLED"]
    locked: bool = False
    # The map and travel surfaces resolve a stop's pin from its metadata
    # (latitude/longitude/crs/role).  Without projecting it a real plan shows no
    # coordinates at all.
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoreBreakdown(BaseModel):
    commitment_preservation: float = Field(ge=0, le=1)
    stability: float = Field(ge=0, le=1)
    time_reliability: float = Field(ge=0, le=1)
    preference_fit: float = Field(ge=0, le=1)
    mobility_fit: float = Field(ge=0, le=1)
    budget_fit: float = Field(ge=0, le=1)
    robustness: float = Field(ge=0, le=1)
    opportunity_value: float = Field(ge=0, le=1)
    total: float = Field(ge=0, le=1)


class PlanVersion(BaseModel):
    id: UUID
    journey_id: UUID
    version_no: int = Field(ge=1)
    planning_mode: PlanningMode
    status: Literal["CANDIDATE", "SELECTED", "ACTIVE", "SUPERSEDED", "REJECTED"]
    source: Literal["INITIAL", "REPLAN", "MANUAL"]
    parent_plan_version_id: UUID | None = None
    total_cost: Money
    utility_score: float | None = Field(default=None, ge=0, le=1)
    score_breakdown: ScoreBreakdown | None = None
    activities: list[Activity]
    mobility_snapshot_id: str | None = None
    mobility_evidence: dict[str, Any] = Field(default_factory=dict)
    explanation: dict[str, Any] = Field(default_factory=dict)
    # Stale/recompose-required projection.  A plan whose frozen evidence has
    # expired must not look like an ordinary current recommendation; selection
    # revalidation remains the final guard.
    stale: bool = False
    selectable: bool = True
    stale_reason: str | None = None


class GeneratePlansRequest(BaseModel):
    planning_mode: PlanningMode | None = None
    candidate_count: int = Field(default=3, ge=1, le=5)
    place_ids: list[str] | None = Field(default=None, min_length=2, max_length=12)


class AuthoritativeComposeRequest(BaseModel):
    """User-selected bounded input for the V12 multi-day planner."""

    place_ids: list[str] = Field(min_length=2, max_length=12)
    candidate_count: int = Field(default=3, ge=1, le=5)
    stay_offer_id: UUID | None = None
    reservation_id: UUID | None = None


class TripStudioPreviewRequest(BaseModel):
    activity_ids: list[UUID] = Field(min_length=2, max_length=40)
    draft_order: list[UUID] | None = None


class TripStudioAcceptRequest(BaseModel):
    activity_ids: list[UUID] = Field(min_length=2, max_length=40)
    preview_id: UUID | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    trace_id: str | None = None
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class EventCreate(BaseModel):
    provider_key: str | None = None
    provenance: Literal["SIMULATED", "PROVIDER_VERIFIED", "USER_REPORTED", "SYSTEM_DERIVED"] = (
        "SIMULATED"
    )
    event_type: Literal[
        "TRAFFIC_DELAY",
        "CLOSURE",
        "WEATHER",
        "SCHEDULE_DELAY",
        "SERVICE_UNAVAILABLE",
        "USER_CHANGE",
        "OTHER",
    ]
    severity: Literal["INFO", "MINOR", "MAJOR", "CRITICAL"] = "INFO"
    affected_activity_id: UUID | None = None
    occurred_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class Event(EventCreate):
    id: UUID
    journey_id: UUID
    status: Literal["DETECTED", "ACKNOWLEDGED", "RESOLVED", "IGNORED"]
    detected_at: datetime


class OutcomeEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: Literal[
        "ACTIVITY_STARTED",
        "ACTIVITY_COMPLETED",
        "ACTIVITY_SKIPPED",
        "MANUAL_OVERRIDE",
        "AGENT_PROPOSED",
        "USER_ACCEPTED",
        "USER_REJECTED",
    ]
    occurred_at_actual: datetime | None = None
    activity_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    actor_type: str = Field(default="USER", min_length=1, max_length=40)
    related_proposal_id: UUID | None = None
    related_agent_run_id: UUID | None = None


class TravelerTwinClearRequest(BaseModel):
    confirm: bool = True


class JourneyTwin(BaseModel):
    journey_id: UUID
    active_plan_version_id: UUID | None = None
    current_activity_id: UUID | None = None
    latest_event_id: UUID | None = None
    projection_status: Literal["READY", "STALE", "DEGRADED"]
    snapshot_at: datetime
    upcoming_commitments: list[Commitment] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class ReplanProposal(BaseModel):
    id: UUID
    journey_id: UUID
    trigger_event_id: UUID | None = None
    base_plan_version_id: UUID
    proposed_plan_version_id: UUID
    status: Literal["GENERATED", "PRESENTED", "ACCEPTED", "REJECTED", "EXPIRED", "INVALIDATED"]
    hard_constraints_passed: bool
    locked_commitments_preserved: bool
    utility_score: float = Field(ge=0, le=1)
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    diff: dict[str, Any] = Field(default_factory=dict)
    explanation: dict[str, Any] = Field(default_factory=dict)


class ReplanGenerateRequest(BaseModel):
    trigger_event_id: UUID
    candidate_count: int = Field(default=3, ge=1, le=5)
    solver_mode: Literal["deterministic", "ortools", "auto", "v2"] | None = None
    protected_activity_ids: list[UUID] = Field(default_factory=list, max_length=50)


# === WP04 COMMERCE API SCHEMAS (generated) ===
class BookingSlot(BaseModel):
    start_at: datetime
    end_at: datetime
    provider_key: str
    provider_slot_ref: str


class BookingCreate(BaseModel):
    activity_id: UUID
    provider_key: str = "mock-booking"
    # Deterministic failure controls are test-fixture switches only.  They can
    # request a provider failure, never forge provider success.
    failure_token: Literal["FORCE_BOOKING_FAIL"] | None = None
    force_failure: bool = False


class Booking(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    journey_id: UUID
    activity_id: UUID | None
    commitment_id: UUID | None
    provider_key: str
    external_ref: str | None
    status: Literal["DRAFT", "PENDING", "CONFIRMED", "COMPLETED", "CANCELLED", "FAILED"]
    amount: Money
    amount_status: Literal["FREE_KNOWN", "KNOWN", "ESTIMATED", "UNKNOWN"] = "KNOWN"
    cancellation_policy: dict


class OrderItemInput(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    quantity: int = Field(ge=1, le=99)


class OrderCreate(BaseModel):
    activity_id: UUID
    items: list[OrderItemInput] = Field(min_length=1, max_length=50)
    provider_key: str = "mock-booking"


class OrderItem(BaseModel):
    """Server-priced order line returned after catalog authority is applied."""

    sku: str
    quantity: int = Field(ge=1, le=99)
    unit_amount_minor: int = Field(ge=0)
    line_total_minor: int = Field(ge=0)


class Order(BaseModel):
    id: UUID
    journey_id: UUID
    activity_id: UUID | None
    commitment_id: UUID | None
    provider_key: str
    external_ref: str | None
    status: Literal["DRAFT", "PENDING", "CONFIRMED", "FULFILLED", "CANCELLED", "FAILED"]
    amount: Money
    items: list[OrderItem]


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    booking_id: UUID | None = None
    order_id: UUID | None = None
    transaction_type: Literal["AUTHORIZE", "CAPTURE", "REFUND", "VOID"]
    amount: Money
    provider_key: str = "mock-payment"
    # Deterministic failure controls are test-fixture switches only; sensitive
    # card credentials are rejected by the extra='forbid' boundary above.
    failure_token: Literal["FORCE_PAYMENT_FAIL"] | None = None
    force_failure: bool = False

    @model_validator(mode="after")
    def exactly_one_target(self) -> TransactionCreate:
        if (self.booking_id is None) == (self.order_id is None):
            raise ValueError("exactly one of booking_id or order_id is required")
        return self


class Transaction(BaseModel):
    id: UUID
    journey_id: UUID
    booking_id: UUID | None
    order_id: UUID | None
    provider_key: str
    transaction_type: Literal["AUTHORIZE", "CAPTURE", "REFUND", "VOID"]
    status: Literal["INITIATED", "AUTHORIZED", "SUCCEEDED", "FAILED", "REFUNDED", "VOIDED"]
    amount: Money
    external_ref: str | None


class Commitment(BaseModel):
    id: UUID
    journey_id: UUID
    activity_id: UUID | None
    kind: Literal["BOOKING", "ORDER", "PAYMENT", "APPOINTMENT", "OTHER"]
    # The exact five allowed source-domain codes MUST be injected from the frozen YAML.
    level: str
    status: Literal["PROPOSED", "ACTIVE", "FULFILLED", "CANCELLED", "BREACHED"]
    monetary_value: Money
    monetary_value_status: Literal["FREE_KNOWN", "KNOWN", "ESTIMATED", "UNKNOWN"] = "KNOWN"
    external_ref: str | None
    policy: dict

    @field_validator("level")
    @classmethod
    def exact_commitment_strength(cls, value: str) -> str:
        # Keep the API boundary aligned with the exact five values reconciled from
        # the frozen domain YAML; an invented sixth label must fail validation.
        from app.commerce.strengths_generated import SOURCE_COMMITMENT_STRENGTHS

        if value not in SOURCE_COMMITMENT_STRENGTHS:
            raise ValueError("level must be one of the frozen commitment strength codes")
        return value
