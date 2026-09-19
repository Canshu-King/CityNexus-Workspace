from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import httpx


@dataclass(frozen=True)
class ValhallaRouteEstimate:
    duration_min: int
    distance_m: int | None
    shape: str | None
    raw: dict[str, Any]


class ValhallaHTTPMobilityProvider:
    """Thin injectable adapter for a Valhalla HTTP service.

    It is intentionally independent of the deterministic feasibility gate. Route
    or matrix results should be frozen through ``capture_mobility_snapshot``
    before the gate consumes them.
    """

    provider_key = "valhalla-http"

    def __init__(
        self,
        *,
        client: httpx.Client,
        base_url: str,
        place_lookup: Callable[[str], Mapping[str, Any]],
        costing: str = "pedestrian",
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._place_lookup = place_lookup
        self._costing = costing

    def _location(self, place_id: str) -> dict[str, float]:
        item = self._place_lookup(place_id)
        location = item.get("location", item)
        return {"lat": float(location["latitude"]), "lon": float(location["longitude"])}

    def estimate(self, origin_place_id: str, destination_place_id: str) -> ValhallaRouteEstimate:
        response = self._client.post(
            f"{self._base_url}/route",
            json={
                "locations": [
                    self._location(origin_place_id),
                    self._location(destination_place_id),
                ],
                "costing": self._costing,
                "units": "kilometers",
            },
        )
        response.raise_for_status()
        payload = response.json()
        trip = payload.get("trip") or {}
        summary = trip.get("summary") or {}
        seconds = float(summary["time"])
        if seconds < 0:
            raise ValueError("Valhalla returned negative route time")
        length_km = summary.get("length")
        legs = trip.get("legs") or []
        shape = legs[0].get("shape") if legs and isinstance(legs[0], dict) else None
        return ValhallaRouteEstimate(
            duration_min=max(0, math.ceil(seconds / 60.0)),
            distance_m=None if length_km is None else round(float(length_km) * 1000),
            shape=shape,
            raw=payload,
        )

    def estimate_minutes(self, origin_place_id: str, destination_place_id: str) -> int:
        return self.estimate(origin_place_id, destination_place_id).duration_min

    def matrix_minutes(self, place_ids: list[str]) -> list[list[int | None]]:
        locations = [self._location(place_id) for place_id in place_ids]
        response = self._client.post(
            f"{self._base_url}/sources_to_targets",
            json={
                "sources": locations,
                "targets": locations,
                "costing": self._costing,
                "verbose": False,
            },
        )
        response.raise_for_status()
        payload = response.json()
        raw = payload.get("durations")
        if raw is None and isinstance(payload.get("sources_to_targets"), dict):
            raw = payload["sources_to_targets"].get("durations")
        if not isinstance(raw, list):
            raise TypeError("Valhalla matrix response does not contain durations")
        matrix: list[list[int | None]] = []
        for row in raw:
            if not isinstance(row, list):
                raise TypeError("Valhalla matrix durations must be row-major")
            matrix.append(
                [None if value is None else max(0, math.ceil(float(value) / 60.0)) for value in row]
            )
        return matrix
