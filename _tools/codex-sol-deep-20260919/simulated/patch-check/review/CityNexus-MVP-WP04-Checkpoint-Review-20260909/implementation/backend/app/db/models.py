from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
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
    traveler_id: Mapped[str] = mapped_column(ForeignKey("travelers.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String)
    preference_key: Mapped[str] = mapped_column(String)
    value_json: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column()
    source: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("traveler_id", "category", "preference_key"),)


class Journey(Base):
    __tablename__ = "journeys"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    traveler_id: Mapped[str] = mapped_column(ForeignKey("travelers.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String)
    city_code: Mapped[str] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String)
    start_at: Mapped[str] = mapped_column(String)
    end_at: Mapped[str] = mapped_column(String)
    budget_currency: Mapped[str] = mapped_column(String)
    budget_amount_minor: Mapped[int] = mapped_column(Integer)
    planning_mode: Mapped[str] = mapped_column(
        String, default="balanced", server_default="balanced"
    )
    status: Mapped[str] = mapped_column(String)
    active_plan_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("plan_versions.id", ondelete="SET NULL"), nullable=True
    )
    current_activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class JourneyConstraint(Base):
    __tablename__ = "constraints"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
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

    __table_args__ = (UniqueConstraint("provider_key", "external_id"),)


class CityService(Base):
    __tablename__ = "city_services"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_key: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    place_id: Mapped[str | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL"), nullable=True
    )
    city_code: Mapped[str] = mapped_column(String)
    service_type: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    availability_json: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("provider_key", "external_id"),)


class PlanVersion(Base):
    __tablename__ = "plan_versions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    version_no: Mapped[int] = mapped_column(Integer)
    planning_mode: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    parent_plan_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("plan_versions.id", ondelete="SET NULL"), nullable=True
    )
    total_cost_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    estimated_duration_min: Mapped[int] = mapped_column(Integer)
    utility_score: Mapped[float | None] = mapped_column(nullable=True)
    score_breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("journey_id", "version_no"),)


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    plan_version_id: Mapped[str] = mapped_column(ForeignKey("plan_versions.id", ondelete="CASCADE"))
    sequence_no: Mapped[int] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    place_id: Mapped[str | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL"), nullable=True
    )
    city_service_id: Mapped[str | None] = mapped_column(
        ForeignKey("city_services.id", ondelete="SET NULL"), nullable=True
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

    __table_args__ = (UniqueConstraint("plan_version_id", "sequence_no"),)


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


# === WP04 COMMERCE ORM SCAFFOLD (generated) ===
class Commitment(Base):
    __tablename__ = "commitments"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String)
    level: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    monetary_value_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    policy_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    commitment_id: Mapped[str | None] = mapped_column(
        ForeignKey("commitments.id", ondelete="SET NULL"), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    cancellation_policy_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    commitment_id: Mapped[str | None] = mapped_column(
        ForeignKey("commitments.id", ondelete="SET NULL"), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    items_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class PaymentTransaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    booking_id: Mapped[str | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    idempotency_key: Mapped[str] = mapped_column(String)
    transaction_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("provider_key", "idempotency_key"),)


class ProviderCall(Base):
    __tablename__ = "provider_calls"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_key: Mapped[str] = mapped_column(String)
    operation: Mapped[str] = mapped_column(String)
    request_json: Mapped[str] = mapped_column(Text)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    operation: Mapped[str] = mapped_column(String)
    request_hash: Mapped[str] = mapped_column(Text)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str] = mapped_column(String)
