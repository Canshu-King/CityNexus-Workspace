from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


V1_TOOL_NAMES = (
    "inspect_journey",
    "inspect_twin",
    "list_replans",
    "search_city_services",
    "request_replan",
    "accept_replan",
)

SAFE_ARGUMENT_NAMES = frozenset(
    {
        "request_id",
        "agent_id",
        "journey_id",
        "proposal_id",
        "trigger_event_id",
        "candidate_count",
        "city_code",
        "q",
        "category",
        "service_type",
    }
)


@dataclass(frozen=True)
class MCPToolDescriptor:
    name: str
    description: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "description": self.description}


@dataclass(frozen=True)
class MCPToolCall:
    request_id: str
    agent_id: str
    arguments: Mapping[str, Any]

    def payload(self) -> dict[str, Any]:
        payload = {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            **dict(self.arguments),
        }
        unknown = sorted(set(payload) - SAFE_ARGUMENT_NAMES)
        if unknown:
            raise ValueError(f"unknown CityNexus Agent arguments: {unknown}")
        return payload

