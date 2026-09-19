from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx


@dataclass(frozen=True)
class WeatherObservation:
    at: datetime
    precipitation_probability: int | None
    weather_code: int | None


@dataclass(frozen=True)
class WeatherRisk:
    code: str
    severity: str
    at: datetime
    evidence: dict[str, Any]


class OpenMeteoContextProvider:
    provider_key = "open-meteo"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        base_url: str = "https://api.open-meteo.com",
        rain_probability_threshold: int = 70,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._rain_threshold = rain_probability_threshold

    async def forecast(self, *, latitude: float, longitude: float) -> list[WeatherObservation]:
        response = await self._client.get(
            f"{self._base_url}/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "precipitation_probability,weather_code",
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        payload = response.json()
        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        probabilities = hourly.get("precipitation_probability", [])
        codes = hourly.get("weather_code", [])
        observations: list[WeatherObservation] = []
        for index, raw_time in enumerate(times):
            probability = probabilities[index] if index < len(probabilities) else None
            code = codes[index] if index < len(codes) else None
            observations.append(
                WeatherObservation(
                    at=datetime.fromisoformat(raw_time),
                    precipitation_probability=None if probability is None else int(probability),
                    weather_code=None if code is None else int(code),
                )
            )
        return observations

    def risks(self, observations: list[WeatherObservation]) -> list[WeatherRisk]:
        risks: list[WeatherRisk] = []
        for item in observations:
            if (
                item.precipitation_probability is not None
                and item.precipitation_probability >= self._rain_threshold
            ):
                risks.append(
                    WeatherRisk(
                        code="HEAVY_RAIN_RISK",
                        severity="HIGH",
                        at=item.at,
                        evidence={
                            "precipitation_probability": item.precipitation_probability,
                            "weather_code": item.weather_code,
                        },
                    )
                )
        return risks
