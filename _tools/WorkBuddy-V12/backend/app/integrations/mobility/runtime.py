from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import CityService, Journey, Place
from app.integrations.mobility.snapshot_capture import (
    MobilitySnapshotCaptureResult,
    capture_mobility_snapshot,
)
from app.integrations.mobility.valhalla_http import ValhallaHTTPMobilityProvider
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
        return capture_mobility_snapshot(
            normalized_pairs,
            primary=primary,
            fallback=mock,
            captured_at=captured_at,
            operation_key=operation_key,
        )
