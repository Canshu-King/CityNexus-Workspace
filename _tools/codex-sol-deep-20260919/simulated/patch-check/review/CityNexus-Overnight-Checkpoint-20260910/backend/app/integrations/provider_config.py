from __future__ import annotations

import os
from dataclasses import dataclass


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ExternalProviderSettings:
    real_mobility_enabled: bool = _flag("CITYNEXUS_REAL_MOBILITY_ENABLED")
    router_name: str = os.getenv("CITYNEXUS_ROUTER", "valhalla")
    router_base_url: str | None = os.getenv("CITYNEXUS_ROUTER_BASE_URL")
    router_profile: str = os.getenv("CITYNEXUS_ROUTER_PROFILE", "pedestrian")

    open_meteo_enabled: bool = _flag("CITYNEXUS_OPEN_METEO_ENABLED")
    photon_enabled: bool = _flag("CITYNEXUS_PHOTON_ENABLED")
    photon_base_url: str = os.getenv("CITYNEXUS_PHOTON_BASE_URL", "https://photon.komoot.io")

    ai_enabled: bool = _flag("CITYNEXUS_AI_ENABLED")
    ai_provider: str = os.getenv("CITYNEXUS_AI_PROVIDER", "deterministic-fallback")
    ai_model: str | None = os.getenv("CITYNEXUS_AI_MODEL")
    deepseek_api_key: str | None = os.getenv("DEEPSEEK_API_KEY")

    webauthn_enabled: bool = _flag("CITYNEXUS_WEBAUTHN_ENABLED")
