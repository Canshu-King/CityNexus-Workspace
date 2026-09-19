from __future__ import annotations

import os
import sys
from pathlib import Path

import anyio
from citynexus_mcp.schemas import V1_TOOL_NAMES, V2_TOOL_NAMES, MCPToolCall
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
            {
                "request_id": "mcp-request-1",
                "agent_id": "hermes",
                "journey_id": "journey-1",
            },
        )
    ]


def test_mcp_v2_exposes_typed_actions_without_changing_v1_discovery():
    fake = FakeClient()
    server = CityNexusMCPServer(fake)
    names = [item["name"] for item in server.list_tools_v2()]
    assert names == list(V2_TOOL_NAMES)
    result = server.call(
        "reschedule_activity",
        MCPToolCall(
            request_id="mcp-v2-request-1",
            agent_id="hermes",
            arguments={
                "journey_id": "journey-1",
                "activity_id": "activity-1",
                "start_at": "2026-10-10T10:00:00+08:00",
                "end_at": "2026-10-10T11:00:00+08:00",
            },
        ),
    )
    assert result["tool"] == "reschedule_activity"


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


def test_real_mcp_stdio_protocol_discovers_only_citynexus_tools():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def exercise() -> None:
        package_root = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        existing_path = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = str(package_root) + (
            os.pathsep + existing_path if existing_path else ""
        )
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "citynexus_mcp.server"],
            cwd=package_root,
            env=environment,
        )
        async with (
            stdio_client(parameters) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()
            result = await session.list_tools()
            names = [item.name for item in result.tools]
            assert names == list(V1_TOOL_NAMES)
            assert all(
                item.inputSchema.get("type") == "object" for item in result.tools
            )

    anyio.run(exercise)


def test_real_mcp_v2_stdio_protocol_discovers_coherent_inspect_plan_act_surface():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def exercise() -> None:
        package_root = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        existing_path = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = str(package_root) + (
            os.pathsep + existing_path if existing_path else ""
        )
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "citynexus_mcp.server", "--v2"],
            cwd=package_root,
            env=environment,
        )
        async with (
            stdio_client(parameters) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()
            result = await session.list_tools()
            names = [item.name for item in result.tools]
            assert names == list(V2_TOOL_NAMES)

    anyio.run(exercise)
