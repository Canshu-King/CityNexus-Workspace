from __future__ import annotations

import json
from pathlib import Path

MOCK_ROOT = Path(__file__).resolve().parents[4] / "data" / "mock"


class MockCityDataProvider:
    provider_key = "mock-city"

    def places(self) -> list[dict]:
        return json.loads((MOCK_ROOT / "places.json").read_text(encoding="utf-8"))

    def city_services(self) -> list[dict]:
        return json.loads((MOCK_ROOT / "city_services.json").read_text(encoding="utf-8"))


class MockMobilityProvider:
    provider_key = "mock-mobility"

    def __init__(self) -> None:
        self._fixture = json.loads((MOCK_ROOT / "mobility_matrix.json").read_text(encoding="utf-8"))

    def estimate_minutes(self, origin_place_id: str, destination_place_id: str) -> int:
        key = f"{origin_place_id}|{destination_place_id}"
        return int(self._fixture["minutes"].get(key, self._fixture["default_minutes"]))
