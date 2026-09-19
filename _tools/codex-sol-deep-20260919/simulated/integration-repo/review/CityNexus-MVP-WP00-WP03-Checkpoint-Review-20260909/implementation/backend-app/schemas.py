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
    planning_mode: PlanningMode = "balanced"
    candidate_count: int = Field(default=3, ge=1, le=5)


class ErrorDetail(BaseModel):
    code: str
    message: str
    trace_id: str | None = None
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
