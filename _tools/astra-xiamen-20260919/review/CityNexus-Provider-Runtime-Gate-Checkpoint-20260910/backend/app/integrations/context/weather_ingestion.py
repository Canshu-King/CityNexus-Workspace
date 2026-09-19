from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.db.models import Event
from app.integrations.context.weather_snapshot import WeatherRiskFact


def ingest_provider_verified_weather_event(
    session: Session,
    *,
    journey_id: str,
    fact: WeatherRiskFact,
    affected_activity_id: str | None = None,
) -> Event:
    """Persist a server-owned Open-Meteo fact as a PROVIDER_VERIFIED Event.

    Public EventCreate input cannot reach this function. Callers must pass a
    frozen ``WeatherRiskFact`` produced by ``freeze_weather_risks``; payment,
    commitment and feasibility state are never inferred here.
    """

    if fact.provider_key != "open-meteo":
        raise ValueError("provider-verified weather events require the open-meteo provider")
    severity = {
        "LOW": "INFO",
        "MEDIUM": "MINOR",
        "HIGH": "MAJOR",
        "EXTREME": "CRITICAL",
    }.get(fact.severity.upper(), fact.severity.upper())
    if severity not in {"INFO", "MINOR", "MAJOR", "CRITICAL"}:
        raise ValueError("weather severity does not map to an Event severity")
    now = datetime.now(timezone.utc).isoformat()
    item = Event(
        id=str(uuid4()),
        journey_id=str(journey_id),
        provider_key="open-meteo",
        provenance="PROVIDER_VERIFIED",
        event_type="WEATHER",
        severity=severity,
        status="DETECTED",
        affected_activity_id=affected_activity_id,
        occurred_at=fact.at,
        detected_at=now,
        payload_json=json.dumps(
            {"reason_code": fact.code, "provider_evidence": dict(fact.evidence)},
            sort_keys=True,
        ),
        created_at=now,
    )
    session.add(item)
    record_audit(
        session,
        action="journey.event.provider_verified",
        entity_type="Event",
        entity_id=item.id,
        journey_id=str(journey_id),
        after={"provider_key": item.provider_key, "provenance": item.provenance},
    )
    session.flush()
    return item


def record_provider_degradation(
    session: Session,
    *,
    journey_id: str,
    provider_key: str = "open-meteo",
    detail: str | None = None,
    occurred_at: str | None = None,
) -> Event:
    """Record a server-owned provider outage without inventing a weather fact.

    This is an internal status boundary used when a provider call cannot
    produce a ``WeatherRiskFact``.  The event intentionally carries only
    provider status metadata; it never becomes a weather observation.
    """

    if provider_key != "open-meteo":
        raise ValueError("weather provider degradation must identify open-meteo")
    now = datetime.now(timezone.utc).isoformat()
    item = Event(
        id=str(uuid4()),
        journey_id=str(journey_id),
        provider_key=provider_key,
        provenance="SYSTEM_DERIVED",
        event_type="SERVICE_UNAVAILABLE",
        severity="MAJOR",
        status="DETECTED",
        occurred_at=occurred_at or now,
        detected_at=now,
        payload_json=json.dumps(
            {
                "degraded_providers": [provider_key],
                "provider_status": "DEGRADED",
                "detail": detail,
            },
            sort_keys=True,
        ),
        created_at=now,
    )
    session.add(item)
    record_audit(
        session,
        action="journey.provider.degraded",
        entity_type="Event",
        entity_id=item.id,
        journey_id=str(journey_id),
        after={"provider_key": provider_key, "status": "DEGRADED"},
    )
    session.flush()
    return item


def resolve_provider_degradation(
    session: Session,
    *,
    journey_id: str,
    provider_key: str = "open-meteo",
    resolved_at: str | None = None,
) -> tuple[Event, ...]:
    """Resolve outstanding server-owned degradation events after recovery."""

    if provider_key != "open-meteo":
        raise ValueError("weather provider recovery must identify open-meteo")
    stamp = resolved_at or datetime.now(timezone.utc).isoformat()
    resolved: list[Event] = []
    rows = session.scalars(
        select(Event).where(
            Event.journey_id == str(journey_id),
            Event.provider_key == provider_key,
            Event.provenance == "SYSTEM_DERIVED",
            Event.status.in_(("DETECTED", "ACKNOWLEDGED")),
        )
    ).all()
    for item in rows:
        try:
            payload = json.loads(item.payload_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        if provider_key not in payload.get("degraded_providers", []):
            continue
        item.status = "RESOLVED"
        item.resolved_at = stamp
        resolved.append(item)
        record_audit(
            session,
            action="journey.provider.recovered",
            entity_type="Event",
            entity_id=item.id,
            journey_id=str(journey_id),
            after={"provider_key": provider_key, "status": "RESOLVED"},
        )
    session.flush()
    return tuple(resolved)
