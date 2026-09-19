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


class AgentPolicyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["ADVISORY", "ASSISTED", "AUTONOMOUS"] = "ADVISORY"
    auto_accept_replan: bool = False
    max_auto_replan_cost_delta_minor: int = Field(default=0, ge=0)
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
    proposal_id: UUID | None = None
    trigger_event_id: UUID | None = None
    candidate_count: int = Field(default=3, ge=1, le=5)
    city_code: str | None = Field(default=None, min_length=1, max_length=32)
    q: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    service_type: str | None = Field(default=None, max_length=80)


class JourneyCreate(BaseModel):
    traveler_id: UUID
    title: str = Field(min_length=1, max_length=160)
    city_code: str = Field(min_length=1)
    timezone: str
    start_at: datetime
    end_at: datetime
    budget: Money
    planning_mode: PlanningMode = "balanced"

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
    status: Literal["PLANNED", "READY", "ACTIVE", "COMPLETED", "SKIPPED", "CANCELLED"]
    locked: bool = False


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


class GeneratePlansRequest(BaseModel):
    planning_mode: PlanningMode | None = None
    candidate_count: int = Field(default=3, ge=1, le=5)


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
