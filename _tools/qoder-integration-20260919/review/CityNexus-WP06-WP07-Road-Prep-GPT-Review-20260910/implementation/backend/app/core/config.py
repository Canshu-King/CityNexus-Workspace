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


settings = Settings()
