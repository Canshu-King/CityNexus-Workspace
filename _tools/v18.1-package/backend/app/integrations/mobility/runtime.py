from __future__ import annotations

from dataclasses import replace
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import CityService, Journey, Place
from app.integrations.mobility.snapshot_capture import (
    MobilitySnapshotCaptureResult,
    capture_mobility_snapshot,
)
from app.integrations.mobility.valhalla_http import (
    ValhallaHTTPMobilityProvider,
    ValhallaProviderError,
)
from app.integrations.mock.providers import MockMobilityProvider


def _place_lookup(session: Session, key: str) -> dict[str, float]:
    place = session.get(Place, key)
    if place is None:
        service = session.get(CityService, key)
        if service is not None and service.place_id:
            place = session.get(Place, service.place_id)
    if place is None:
        raise KeyError(f"no routable coordinates for {key}")
    return {"latitude": float(place.latitude), "longitude": float(place.longitude)}


def capture_runtime_mobility_snapshot(
    session: Session,
    journey: Journey,
    pairs: Iterable[tuple[str, str]],
    *,
    operation_key: str,
    captured_at: str | None = None,
) -> MobilitySnapshotCaptureResult:
    """Capture one immutable mobility reality for a product operation.

    The default/offline profile uses the deterministic mock provider. When an
    opt-in Valhalla URL is configured, Valhalla becomes the primary provider
    and the deterministic mock remains an explicit pair-level fallback. The
    returned snapshot is the only object allowed into the feasibility gate.
    """

    normalized_pairs = tuple(sorted({(str(a), str(b)) for a, b in pairs if a and b and a != b}))
    mock = MockMobilityProvider(place_lookup=lambda key: _place_lookup(session, key))
    if not settings.live_valhalla_url:
        return capture_mobility_snapshot(
            normalized_pairs,
            primary=mock,
            captured_at=captured_at,
            operation_key=operation_key,
        )

    with httpx.Client(timeout=10.0) as client:
        primary: Any = ValhallaHTTPMobilityProvider(
            client=client,
            base_url=settings.live_valhalla_url,
            place_lookup=lambda key: _place_lookup(session, key),
        )
        try:
            capabilities = primary.status_capabilities()
        except ValhallaProviderError as exc:
            capabilities = {
                "status": "UNAVAILABLE",
                "has_live_traffic": False,
                "error_type": type(exc).__name__,
            }
        captured = capture_mobility_snapshot(
            normalized_pairs,
            primary=primary,
            fallback=mock,
            captured_at=captured_at,
            operation_key=operation_key,
        )
        return replace(
            captured,
            snapshot=replace(
                captured.snapshot,
                provider_capabilities={"valhalla": capabilities},
            ),
        )


def capture_journey_mobility_matrix(
    nodes: Iterable[dict[str, Any]],
    *,
    operation_key: str,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Capture one Journey-owned Valhalla matrix per supported costing.

    The node keys are the structural Journey identities, not a city-wide
    centroid or a reusable place-only snapshot.  The caller freezes this
    result into PlanVersion evidence; it is intentionally not a fallback to
    the deterministic fixture provider.
    """

    captured = captured_at or datetime.now(timezone.utc).isoformat()
    normalized_nodes = [
        {
            "key": str(item["key"]),
            "role": str(item.get("role") or "ACTIVITY"),
            "place_id": item.get("place_id"),
            "external_id": item.get("external_id"),
            "latitude": float(item["latitude"]),
            "longitude": float(item["longitude"]),
        }
        for item in nodes
    ]
    result: dict[str, Any] = {
        "status": "NOT_CONFIGURED",
        "provider": "valhalla",
        "operation_key": operation_key,
        "captured_at": captured,
        "nodes": normalized_nodes,
        "facts": [],
        "supported_modes": [],
        "route_provenance": "NONE",
        "cost_provenance": "NONE",
        "time_basis": "NOT_CAPTURED",
    }
    if not settings.live_valhalla_url or not normalized_nodes:
        return result

    keys = [item["key"] for item in normalized_nodes]
    lookup = {item["key"]: item for item in normalized_nodes}
    facts: list[dict[str, Any]] = []
    try:
        with httpx.Client(timeout=10.0) as client:
            capability_by_deployment: dict[str, Any]
            for mode, costing in (("WALK", "pedestrian"), ("AUTO", "auto")):
                provider = ValhallaHTTPMobilityProvider(
                    client=client,
                    base_url=settings.live_valhalla_url,
                    place_lookup=lambda key: lookup[key],
                    costing=costing,
                )
                if mode == "WALK":
                    try:
                        capability_by_deployment = provider.status_capabilities()
                    except ValhallaProviderError as exc:
                        capability_by_deployment = {
                            "status": "UNAVAILABLE",
                            "has_live_traffic": False,
                            "error_type": type(exc).__name__,
                        }
                matrix = provider.matrix(keys)
                for source_index, row in enumerate(matrix):
                    for target_index, cell in enumerate(row):
                        if source_index == target_index or cell is None:
                            continue
                        facts.append(
                            {
                                "from_key": keys[source_index],
                                "to_key": keys[target_index],
                                "mode": mode,
                                "duration_min": cell.duration_min,
                                "distance_km": None
                                if cell.distance_m is None
                                else cell.distance_m / 1000.0,
                                "captured_at": captured,
                                "route_provider": "valhalla",
                                "route_provenance": "LIVE_CAPTURE",
                                "cost_provenance": "CITYNEXUS_COST_ESTIMATE",
                                "time_basis": "VALHALLA_SOURCES_TO_TARGETS",
                                "matrix_cell": cell.raw,
                            }
                        )
    except ValhallaProviderError as exc:
        result["status"] = "FAILED"
        result["error_type"] = type(exc).__name__
        return result

    result.update(
        {
            "status": "CAPTURED" if facts else "NO_RESULTS",
            "facts": facts,
            "supported_modes": sorted({str(item["mode"]) for item in facts}),
            "route_provenance": "LIVE_CAPTURE" if facts else "NONE",
            "cost_provenance": "CITYNEXUS_COST_ESTIMATE" if facts else "NONE",
            "time_basis": "VALHALLA_SOURCES_TO_TARGETS" if facts else "NOT_CAPTURED",
            "provider_capabilities": {"valhalla": capability_by_deployment},
        }
    )
    return result
