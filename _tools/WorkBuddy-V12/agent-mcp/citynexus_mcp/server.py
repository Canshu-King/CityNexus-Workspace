from __future__ import annotations

import os
import sys
from typing import Any

from .client import CityNexusAgentClient
from .schemas import V1_TOOL_NAMES, V2_TOOL_NAMES, MCPToolCall, MCPToolDescriptor

TOOL_DESCRIPTIONS = {
    "inspect_journey": "Read the persisted Journey state.",
    "inspect_twin": "Read the JourneyTwin projection.",
    "list_replans": "List persisted Replan proposals.",
    "search_city_services": "Search server-owned city service facts.",
    "request_replan": "Request a proposal without activating a Plan.",
    "accept_replan": "Ask the server policy and deterministic gate to accept a proposal.",
    "replace_activity": "Replace a mutable Activity through the server policy and feasibility gate.",
    "reschedule_activity": "Reschedule a mutable Activity through the server policy and feasibility gate.",
    "create_booking": "Create a provider booking when the server policy permits it.",
    "cancel_refundable_booking": "Cancel a refundable booking when the server policy permits it.",
    "request_commitment_change": "Request a protected Commitment change through the approval gate.",
}


class CityNexusMCPServer:
    """Safe CityNexus tool adapter used by the SDK-backed MCP runtime."""

    def __init__(self, client: CityNexusAgentClient | None = None):
        self.client = client or CityNexusAgentClient()

    def list_tools(self) -> list[dict[str, str]]:
        return [
            MCPToolDescriptor(name=name, description=TOOL_DESCRIPTIONS[name]).as_dict()
            for name in V1_TOOL_NAMES
        ]

    def list_tools_v2(self) -> list[dict[str, str]]:
        return [
            MCPToolDescriptor(name=name, description=TOOL_DESCRIPTIONS[name]).as_dict()
            for name in V2_TOOL_NAMES
        ]

    def call(self, tool_name: str, call: MCPToolCall) -> dict[str, Any]:
        if tool_name not in V2_TOOL_NAMES:
            raise ValueError("tool is outside the CityNexus MCP allowlist")
        return self.client.call(tool_name, call.payload())


def build_mcp_server(client: CityNexusAgentClient | None = None):
    """Build a real MCP server with only the CityNexus V1 tools registered."""

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised on minimal installs
        raise RuntimeError(
            "install citynexus-agent-mcp[mcp] to run the MCP server"
        ) from exc

    adapter = CityNexusMCPServer(client)
    mcp = FastMCP(
        name="citynexus",
        instructions=(
            "CityNexus exposes only server-owned Journey inspection and safe replan tools. "
            "The CityNexus HTTP gateway performs identity, policy, and deterministic feasibility checks."
        ),
    )

    def call(tool_name: str, request_id: str, **arguments: Any) -> dict[str, Any]:
        # This value is only a compatibility hint. The HTTP layer resolves the
        # trusted principal from its configured credential or local boundary.
        return adapter.call(
            tool_name,
            MCPToolCall(
                request_id=request_id, agent_id="mcp-client", arguments=arguments
            ),
        )

    @mcp.tool(name="inspect_journey", description=TOOL_DESCRIPTIONS["inspect_journey"])
    def inspect_journey(request_id: str, journey_id: str) -> dict[str, Any]:
        return call("inspect_journey", request_id, journey_id=journey_id)

    @mcp.tool(name="inspect_twin", description=TOOL_DESCRIPTIONS["inspect_twin"])
    def inspect_twin(request_id: str, journey_id: str) -> dict[str, Any]:
        return call("inspect_twin", request_id, journey_id=journey_id)

    @mcp.tool(name="list_replans", description=TOOL_DESCRIPTIONS["list_replans"])
    def list_replans(request_id: str, journey_id: str) -> dict[str, Any]:
        return call("list_replans", request_id, journey_id=journey_id)

    @mcp.tool(
        name="search_city_services",
        description=TOOL_DESCRIPTIONS["search_city_services"],
    )
    def search_city_services(
        request_id: str,
        journey_id: str | None = None,
        city_code: str | None = None,
        q: str | None = None,
        category: str | None = None,
        service_type: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "search_city_services",
            request_id,
            journey_id=journey_id,
            city_code=city_code,
            q=q,
            category=category,
            service_type=service_type,
        )

    @mcp.tool(name="request_replan", description=TOOL_DESCRIPTIONS["request_replan"])
    def request_replan(
        request_id: str,
        journey_id: str,
        trigger_event_id: str,
        candidate_count: int = 3,
    ) -> dict[str, Any]:
        return call(
            "request_replan",
            request_id,
            journey_id=journey_id,
            trigger_event_id=trigger_event_id,
            candidate_count=candidate_count,
        )

    @mcp.tool(name="accept_replan", description=TOOL_DESCRIPTIONS["accept_replan"])
    def accept_replan(
        request_id: str,
        proposal_id: str,
        journey_id: str | None = None,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "accept_replan",
            request_id,
            proposal_id=proposal_id,
            journey_id=journey_id,
            approval_id=approval_id,
        )

    return mcp


def build_mcp_v2_server(client: CityNexusAgentClient | None = None):
    """Build the expanded MCP surface without changing the pinned V1 server."""

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised on minimal installs
        raise RuntimeError(
            "install citynexus-agent-mcp[mcp] to run the MCP server"
        ) from exc

    adapter = CityNexusMCPServer(client)
    mcp = FastMCP(
        name="citynexus-v2",
        instructions=(
            "CityNexus V2 exposes typed Activity, Booking, and Commitment actions. "
            "The HTTP gateway remains authoritative for identity, approval, provider state, "
            "and deterministic feasibility."
        ),
    )

    def call(tool_name: str, request_id: str, **arguments: Any) -> dict[str, Any]:
        return adapter.call(
            tool_name,
            MCPToolCall(
                request_id=request_id, agent_id="mcp-client", arguments=arguments
            ),
        )

    @mcp.tool(name="inspect_journey", description=TOOL_DESCRIPTIONS["inspect_journey"])
    def inspect_journey(request_id: str, journey_id: str) -> dict[str, Any]:
        return call("inspect_journey", request_id, journey_id=journey_id)

    @mcp.tool(name="inspect_twin", description=TOOL_DESCRIPTIONS["inspect_twin"])
    def inspect_twin(request_id: str, journey_id: str) -> dict[str, Any]:
        return call("inspect_twin", request_id, journey_id=journey_id)

    @mcp.tool(name="list_replans", description=TOOL_DESCRIPTIONS["list_replans"])
    def list_replans(request_id: str, journey_id: str) -> dict[str, Any]:
        return call("list_replans", request_id, journey_id=journey_id)

    @mcp.tool(
        name="search_city_services",
        description=TOOL_DESCRIPTIONS["search_city_services"],
    )
    def search_city_services(
        request_id: str,
        journey_id: str | None = None,
        city_code: str | None = None,
        q: str | None = None,
        category: str | None = None,
        service_type: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "search_city_services",
            request_id,
            journey_id=journey_id,
            city_code=city_code,
            q=q,
            category=category,
            service_type=service_type,
        )

    @mcp.tool(name="request_replan", description=TOOL_DESCRIPTIONS["request_replan"])
    def request_replan(
        request_id: str,
        journey_id: str,
        trigger_event_id: str,
        candidate_count: int = 3,
    ) -> dict[str, Any]:
        return call(
            "request_replan",
            request_id,
            journey_id=journey_id,
            trigger_event_id=trigger_event_id,
            candidate_count=candidate_count,
        )

    @mcp.tool(name="accept_replan", description=TOOL_DESCRIPTIONS["accept_replan"])
    def accept_replan(
        request_id: str,
        proposal_id: str,
        journey_id: str | None = None,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "accept_replan",
            request_id,
            proposal_id=proposal_id,
            journey_id=journey_id,
            approval_id=approval_id,
        )

    @mcp.tool(
        name="replace_activity", description=TOOL_DESCRIPTIONS["replace_activity"]
    )
    def replace_activity(
        request_id: str,
        journey_id: str,
        activity_id: str,
        replacement_activity_id: str | None = None,
        replacement_place_id: str | None = None,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "replace_activity",
            request_id,
            journey_id=journey_id,
            activity_id=activity_id,
            replacement_activity_id=replacement_activity_id,
            replacement_place_id=replacement_place_id,
            approval_id=approval_id,
        )

    @mcp.tool(
        name="reschedule_activity", description=TOOL_DESCRIPTIONS["reschedule_activity"]
    )
    def reschedule_activity(
        request_id: str,
        journey_id: str,
        activity_id: str,
        start_at: str,
        end_at: str,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "reschedule_activity",
            request_id,
            journey_id=journey_id,
            activity_id=activity_id,
            start_at=start_at,
            end_at=end_at,
            approval_id=approval_id,
        )

    @mcp.tool(name="create_booking", description=TOOL_DESCRIPTIONS["create_booking"])
    def create_booking(
        request_id: str,
        journey_id: str,
        activity_id: str,
        provider_key: str = "mock-booking",
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "create_booking",
            request_id,
            journey_id=journey_id,
            activity_id=activity_id,
            provider_key=provider_key,
            approval_id=approval_id,
        )

    @mcp.tool(
        name="cancel_refundable_booking",
        description=TOOL_DESCRIPTIONS["cancel_refundable_booking"],
    )
    def cancel_refundable_booking(
        request_id: str,
        journey_id: str,
        booking_id: str,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "cancel_refundable_booking",
            request_id,
            journey_id=journey_id,
            booking_id=booking_id,
            approval_id=approval_id,
        )

    @mcp.tool(
        name="request_commitment_change",
        description=TOOL_DESCRIPTIONS["request_commitment_change"],
    )
    def request_commitment_change(
        request_id: str,
        journey_id: str,
        commitment_id: str,
        reason: str,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        return call(
            "request_commitment_change",
            request_id,
            journey_id=journey_id,
            commitment_id=commitment_id,
            reason=reason,
            approval_id=approval_id,
        )

    return mcp


def main() -> None:
    use_v2 = "--v2" in sys.argv or os.getenv("CITYNEXUS_MCP_V2", "").lower() == "true"
    (build_mcp_v2_server() if use_v2 else build_mcp_server()).run(transport="stdio")


if __name__ == "__main__":
    main()
