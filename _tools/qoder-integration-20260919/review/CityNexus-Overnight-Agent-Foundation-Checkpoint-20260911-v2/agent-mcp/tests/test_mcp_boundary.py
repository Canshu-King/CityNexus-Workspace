from __future__ import annotations

from citynexus_mcp.schemas import MCPToolCall, V1_TOOL_NAMES
from citynexus_mcp.server import CityNexusMCPServer


class FakeClient:
    def __init__(self):
        self.calls = []

    def call(self, tool_name, payload):
        self.calls.append((tool_name, payload))
        return {"tool": tool_name, "received": payload}


def test_mcp_discovery_is_exactly_the_safe_allowlist():
    server = CityNexusMCPServer(FakeClient())
    assert [item["name"] for item in server.list_tools()] == list(V1_TOOL_NAMES)
    assert not {"terminal", "file", "browser", "payment", "refund", "set_policy"} & set(
        V1_TOOL_NAMES
    )


def test_mcp_delegates_to_citynexus_agent_api_only():
    fake = FakeClient()
    server = CityNexusMCPServer(fake)
    result = server.call(
        "inspect_twin",
        MCPToolCall(
            request_id="mcp-request-1",
            agent_id="hermes",
            arguments={"journey_id": "journey-1"},
        ),
    )
    assert result["tool"] == "inspect_twin"
    assert fake.calls == [
        (
            "inspect_twin",
            {"request_id": "mcp-request-1", "agent_id": "hermes", "journey_id": "journey-1"},
        )
    ]


def test_mcp_rejects_unknown_arguments_and_tools():
    server = CityNexusMCPServer(FakeClient())
    try:
        server.call(
            "inspect_twin",
            MCPToolCall("mcp-request-2", "hermes", {"url": "http://evil.invalid"}),
        )
    except ValueError as exc:
        assert "unknown" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown arguments must fail closed")

    try:
        server.call("raw_sql", MCPToolCall("mcp-request-3", "hermes", {}))
    except ValueError as exc:
        assert "allowlist" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown tools must fail closed")

