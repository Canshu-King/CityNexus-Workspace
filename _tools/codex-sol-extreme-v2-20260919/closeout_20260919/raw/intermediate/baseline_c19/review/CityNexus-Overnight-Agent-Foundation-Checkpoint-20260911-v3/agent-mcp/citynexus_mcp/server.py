from __future__ import annotations

from typing import Any

from .client import CityNexusAgentClient
from .schemas import MCPToolCall, MCPToolDescriptor, V1_TOOL_NAMES


TOOL_DESCRIPTIONS = {
    "inspect_journey": "Read the persisted Journey state.",
    "inspect_twin": "Read the JourneyTwin projection.",
    "list_replans": "List persisted Replan proposals.",
    "search_city_services": "Search server-owned city service facts.",
    "request_replan": "Request a proposal without activating a Plan.",
    "accept_replan": "Ask the server policy and deterministic gate to accept a proposal.",
}


class CityNexusMCPServer:
    """MCP-shaped adapter; an optional MCP SDK wrapper can delegate to this class."""

    def __init__(self, client: CityNexusAgentClient | None = None):
        self.client = client or CityNexusAgentClient()

    def list_tools(self) -> list[dict[str, str]]:
        return [
            MCPToolDescriptor(name=name, description=TOOL_DESCRIPTIONS[name]).as_dict()
            for name in V1_TOOL_NAMES
        ]

    def call(self, tool_name: str, call: MCPToolCall) -> dict[str, Any]:
        if tool_name not in V1_TOOL_NAMES:
            raise ValueError("tool is outside the CityNexus MCP V1 allowlist")
        return self.client.call(tool_name, call.payload())

