from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Traveler(Base):
    __tablename__ = "travelers"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    locale: Mapped[str] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Preference(Base):
    __tablename__ = "preferences"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    traveler_id: Mapped[str] = mapped_column(ForeignKey("travelers.id"))
    category: Mapped[str] = mapped_column(String)
    preference_key: Mapped[str] = mapped_column(String)
    value_json: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column()
    source: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Journey(Base):
    __tablename__ = "journeys"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    traveler_id: Mapped[str] = mapped_column(ForeignKey("travelers.id"))
    title: Mapped[str] = mapped_column(String)
    city_code: Mapped[str] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String)
    start_at: Mapped[str] = mapped_column(String)
    end_at: Mapped[str] = mapped_column(String)
    budget_currency: Mapped[str] = mapped_column(String)
    budget_amount_minor: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)
    active_plan_version_id: Mapped[str | None] = mapped_column(String, nullable=True)
    current_activity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class JourneyConstraint(Base):
    __tablename__ = "constraints"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id"))
    kind: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    rule_code: Mapped[str] = mapped_column(String)
    params_json: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column()
    active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Place(Base):
    __tablename__ = "places"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_key: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    city_code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    opening_hours_json: Mapped[str] = mapped_column(Text)
    tags_json: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(String)


class CityService(Base):
    __tablename__ = "city_services"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_key: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id"), nullable=True)
    city_code: Mapped[str] = mapped_column(String)
    service_type: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    availability_json: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(String)


class PlanVersion(Base):
    __tablename__ = "plan_versions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id"))
    version_no: Mapped[int] = mapped_column(Integer)
    planning_mode: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    parent_plan_version_id: Mapped[str | None] = mapped_column(String, nullable=True)
    total_cost_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    estimated_duration_min: Mapped[int] = mapped_column(Integer)
    utility_score: Mapped[float | None] = mapped_column(nullable=True)
    score_breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    plan_version_id: Mapped[str] = mapped_column(ForeignKey("plan_versions.id"))
    sequence_no: Mapped[int] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    place_id: Mapped[str | None] = mapped_column(ForeignKey("places.id"), nullable=True)
    city_service_id: Mapped[str | None] = mapped_column(
        ForeignKey("city_services.id"), nullable=True
    )
    start_at: Mapped[str] = mapped_column(String)
    end_at: Mapped[str] = mapped_column(String)
    travel_from_prev_min: Mapped[int] = mapped_column(Integer)
    estimated_cost_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    locked: Mapped[bool] = mapped_column(Boolean)
    metadata_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    actor_type: Mapped[str] = mapped_column(String)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    journey_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str | None] = mapped_column(String, nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
