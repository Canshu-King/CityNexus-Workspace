from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True)
class TravelEstimateFact:
    origin_key: str
    destination_key: str
    minutes: int
    provider_key: str
    captured_at: str
    degraded: bool = False
    fallback_reason: str | None = None
    route_geometry: tuple[tuple[float, float], ...] = ()
    geometry_provider: str | None = None
    route_provenance: str | None = None
    cost_provenance: str | None = None
    time_basis: str | None = None
    distance_m: int | None = None

    def __post_init__(self) -> None:
        if self.minutes < 0:
            raise ValueError("travel minutes must be non-negative")


@dataclass(frozen=True)
class MobilitySnapshot:
    """Frozen travel facts consumed by the deterministic feasibility gate.

    External routing adapters run *before* the gate and their outputs are
    frozen into this value object.  The gate never performs a network call.
    """

    facts: Mapping[tuple[str, str], TravelEstimateFact]
    source_provider_key: str
    captured_at: str
    degraded: bool = False
    snapshot_id: str = ""
    operation_key: str | None = None
    provider_capabilities: Mapping[str, Any] = field(default_factory=dict)

    provider_key: str = "mobility-snapshot"
    is_frozen_snapshot: bool = True

    def __post_init__(self) -> None:
        frozen: dict[tuple[str, str], TravelEstimateFact] = {}
        for raw_pair, fact in self.facts.items():
            if len(raw_pair) != 2:
                raise ValueError("mobility snapshot keys must be origin/destination pairs")
            pair = (str(raw_pair[0]), str(raw_pair[1]))
            if pair != (fact.origin_key, fact.destination_key):
                raise ValueError("mobility snapshot key/fact identity mismatch")
            frozen[pair] = fact
        object.__setattr__(self, "facts", MappingProxyType(frozen))

    @classmethod
    def from_minutes(
        cls,
        *,
        source_provider_key: str,
        minutes: Mapping[tuple[str, str], int],
        captured_at: str | None = None,
        degraded: bool = False,
        snapshot_id: str | None = None,
        operation_key: str | None = None,
        route_geometries: Mapping[tuple[str, str], Any] | None = None,
        provider_capabilities: Mapping[str, Any] | None = None,
    ) -> MobilitySnapshot:
        stamp = captured_at or datetime.now(timezone.utc).isoformat()
        return cls(
            facts={
                pair: TravelEstimateFact(
                    origin_key=pair[0],
                    destination_key=pair[1],
                    minutes=int(value),
                    provider_key=source_provider_key,
                    captured_at=stamp,
                    degraded=degraded,
                    route_geometry=_normalize_geometry((route_geometries or {}).get(pair)),
                    geometry_provider=(
                        source_provider_key if (route_geometries or {}).get(pair) else None
                    ),
                )
                for pair, value in minutes.items()
            },
            source_provider_key=source_provider_key,
            captured_at=stamp,
            degraded=degraded,
            snapshot_id=snapshot_id or str(uuid4()),
            operation_key=operation_key,
            provider_capabilities=dict(provider_capabilities or {}),
        )

    def estimate_minutes(self, origin_key: str, destination_key: str) -> int:
        fact = self.facts.get((origin_key, destination_key))
        if fact is None:
            raise KeyError(f"missing frozen travel estimate: {origin_key}|{destination_key}")
        return fact.minutes

    def to_evidence(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "operation_key": self.operation_key,
            "captured_at": self.captured_at,
            "source_provider": self.source_provider_key,
            "degraded": self.degraded,
            "provider_capabilities": dict(self.provider_capabilities),
            "facts": [
                {
                    "origin_key": fact.origin_key,
                    "destination_key": fact.destination_key,
                    "minutes": fact.minutes,
                    "provider": fact.provider_key,
                    "captured_at": fact.captured_at,
                    "degraded": fact.degraded,
                    "fallback_reason": fact.fallback_reason,
                    "route_geometry": [list(point) for point in fact.route_geometry],
                    "geometry_provider": fact.geometry_provider,
                    "route_provenance": fact.route_provenance,
                    "cost_provenance": fact.cost_provenance,
                    "time_basis": fact.time_basis,
                    "distance_m": fact.distance_m,
                }
                for _, fact in sorted(self.facts.items())
            ],
        }

    @classmethod
    def from_evidence(cls, payload: Mapping[str, Any]) -> MobilitySnapshot:
        facts: dict[tuple[str, str], TravelEstimateFact] = {}
        # V12 persists the complete directed matrix plus the exact mode fact
        # selected for each concrete leg.  Apply selected_facts last so a
        # replay/replan follows the original plan's frozen mode decision,
        # while still retaining matrix alternatives for Trip Studio edits.
        evidence_items = [
            *[item for item in payload.get("facts", []) if isinstance(item, Mapping)],
            *[item for item in payload.get("selected_facts", []) if isinstance(item, Mapping)],
        ]
        for item in evidence_items:
            if not isinstance(item, Mapping):
                continue
            origin = str(item.get("origin_key") or "")
            destination = str(item.get("destination_key") or "")
            if not origin or not destination:
                continue
            facts[(origin, destination)] = TravelEstimateFact(
                origin_key=origin,
                destination_key=destination,
                minutes=int(item["minutes"]),
                provider_key=str(
                    item.get("provider") or payload.get("source_provider") or "unknown"
                ),
                captured_at=str(item.get("captured_at") or payload.get("captured_at") or ""),
                degraded=bool(item.get("degraded", False)),
                fallback_reason=(
                    str(item["fallback_reason"])
                    if item.get("fallback_reason") is not None
                    else None
                ),
                route_geometry=_normalize_geometry(item.get("route_geometry")),
                geometry_provider=(
                    str(item["geometry_provider"])
                    if item.get("geometry_provider") is not None
                    else None
                ),
                route_provenance=(
                    str(item["route_provenance"])
                    if item.get("route_provenance") is not None
                    else None
                ),
                cost_provenance=(
                    str(item["cost_provenance"])
                    if item.get("cost_provenance") is not None
                    else None
                ),
                time_basis=(
                    str(item["time_basis"]) if item.get("time_basis") is not None else None
                ),
                distance_m=(
                    int(item["distance_m"]) if item.get("distance_m") is not None else None
                ),
            )
        return cls(
            facts=facts,
            source_provider_key=str(payload.get("source_provider") or "unknown"),
            captured_at=str(payload.get("captured_at") or ""),
            degraded=bool(payload.get("degraded", False)),
            snapshot_id=str(payload.get("snapshot_id") or ""),
            operation_key=(
                str(payload["operation_key"]) if payload.get("operation_key") is not None else None
            ),
            provider_capabilities=(
                dict(payload.get("provider_capabilities"))
                if isinstance(payload.get("provider_capabilities"), Mapping)
                else {}
            ),
        )


def _normalize_geometry(value: Any) -> tuple[tuple[float, float], ...]:
    """Normalize provider/GeoJSON geometry into immutable ``[lon, lat]`` pairs."""

    if isinstance(value, Mapping):
        geometry = value.get("geometry") if value.get("type") == "Feature" else value
        if isinstance(geometry, Mapping):
            if geometry.get("type") == "LineString":
                value = geometry.get("coordinates")
            elif geometry.get("type") == "MultiLineString":
                lines = geometry.get("coordinates")
                value = lines[0] if isinstance(lines, list) and lines else None
    if value is None:
        return ()
    if hasattr(value, "coordinates"):
        value = value.coordinates
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[tuple[float, float]] = []
    for point in value:
        if isinstance(point, Mapping):
            try:
                lon = float(point.get("longitude", point.get("lon")))
                lat = float(point.get("latitude", point.get("lat")))
            except (TypeError, ValueError):
                continue
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            try:
                lon = float(point[0])
                lat = float(point[1])
            except (TypeError, ValueError):
                continue
        else:
            continue
        if -180 <= lon <= 180 and -90 <= lat <= 90:
            normalized.append((lon, lat))
    return tuple(normalized) if len(normalized) >= 2 else ()
