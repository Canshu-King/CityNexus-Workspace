from __future__ import annotations

import os
from typing import Any

import httpx

from .schemas import V2_TOOL_NAMES


class CityNexusAgentClient:
    """Small HTTP client that can call only the server-owned Agent allowlist."""

    def __init__(
        self, base_url: str | None = None, *, client: httpx.Client | None = None
    ):
        self.base_url = base_url or os.getenv(
            "CITYNEXUS_API_BASE_URL", "http://127.0.0.1:8000"
        )
        self.base_url = self.base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=15.0)

    def call(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in V2_TOOL_NAMES:
            raise ValueError("tool is outside the CityNexus MCP allowlist")
        headers = {}
        token = os.getenv("CITYNEXUS_AGENT_TOKEN")
        if token:
            headers["X-CityNexus-Agent-Token"] = token
        response = self._client.post(
            f"{self.base_url}/api/v1/agent/tools/{tool_name}",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()
