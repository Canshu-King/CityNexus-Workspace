"""Optional developer smoke for a locally configured Valhalla service.

This script is intentionally not part of the default test path.
Run only when a real local Valhalla endpoint is explicitly configured.
"""
from __future__ import annotations

import os
import sys

import httpx


def main() -> int:
    base_url = os.getenv("CITYNEXUS_LIVE_VALHALLA_URL")
    if not base_url:
        print("SKIP: CITYNEXUS_LIVE_VALHALLA_URL is not set")
        return 0
    payload = {
        "locations": [
            {"lat": 39.10, "lon": 117.18},
            {"lat": 39.12, "lon": 117.21},
        ],
        "costing": "pedestrian",
        "units": "kilometers",
    }
    with httpx.Client(timeout=10.0) as client:
        response = client.post(base_url.rstrip("/") + "/route", json=payload)
        response.raise_for_status()
        trip = response.json().get("trip", {})
        summary = trip.get("summary", {})
        print({"time_seconds": summary.get("time"), "length_km": summary.get("length")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
