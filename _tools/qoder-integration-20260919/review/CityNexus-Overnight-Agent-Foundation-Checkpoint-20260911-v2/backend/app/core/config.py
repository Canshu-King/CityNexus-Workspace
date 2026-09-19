from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("CITYNEXUS_ENV", "development")
    database_url: str = os.getenv("CITYNEXUS_DATABASE_URL", "sqlite:///./citynexus.db")
    ai_enabled: bool = os.getenv("CITYNEXUS_AI_ENABLED", "false").lower() == "true"
    ai_model: str = os.getenv("CITYNEXUS_AI_MODEL", "deepseek/deepseek-chat")
    ai_api_key: str | None = os.getenv("CITYNEXUS_AI_API_KEY") or None
    live_valhalla_url: str | None = os.getenv("CITYNEXUS_LIVE_VALHALLA_URL") or None
    open_meteo_url: str = os.getenv("CITYNEXUS_OPEN_METEO_URL", "https://api.open-meteo.com")
    open_meteo_timeout_seconds: float = float(
        os.getenv("CITYNEXUS_OPEN_METEO_TIMEOUT_SECONDS", "10")
    )
    solver_mode: str = os.getenv("CITYNEXUS_SOLVER", "deterministic")
    solver_random_seed: int = int(os.getenv("CITYNEXUS_SOLVER_RANDOM_SEED", "1"))
    solver_max_time_seconds: float = float(os.getenv("CITYNEXUS_SOLVER_MAX_TIME_SECONDS", "1.0"))


settings = Settings()
