from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from app.integrations.context.open_meteo import WeatherRisk


@dataclass(frozen=True)
class WeatherRiskFact:
    code: str
    severity: str
    at: str
    provider_key: str
    evidence: dict[str, Any]


@dataclass(frozen=True)
class WeatherSnapshot:
    provider_key: str
    captured_at: str
    facts: tuple[WeatherRiskFact, ...]
    degraded: bool = False


def freeze_weather_risks(
    risks: Iterable[WeatherRisk],
    *,
    provider_key: str = "open-meteo",
    captured_at: str | None = None,
    degraded: bool = False,
) -> WeatherSnapshot:
    """Freeze external weather output before it becomes CityNexus event evidence."""

    stamp = captured_at or datetime.now(timezone.utc).isoformat()
    facts = tuple(
        WeatherRiskFact(
            code=str(item.code),
            severity=str(item.severity),
            at=item.at.isoformat(),
            provider_key=provider_key,
            evidence=dict(item.evidence),
        )
        for item in sorted(risks, key=lambda row: (row.at, row.code, row.severity))
    )
    return WeatherSnapshot(
        provider_key=provider_key,
        captured_at=stamp,
        facts=facts,
        degraded=degraded,
    )


def provider_verified_event_payload(fact: WeatherRiskFact) -> dict[str, Any]:
    """Return server-owned evidence for an Event ingestion service.

    This is deliberately not a public EventCreate payload. Public clients must
    not be able to forge PROVIDER_VERIFIED provenance.
    """

    return {
        "provider_key": fact.provider_key,
        "provenance": "PROVIDER_VERIFIED",
        "event_type": "WEATHER",
        "severity": fact.severity,
        "occurred_at": fact.at,
        "payload": {
            "reason_code": fact.code,
            "provider_evidence": dict(fact.evidence),
        },
    }
