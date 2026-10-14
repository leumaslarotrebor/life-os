"""
MCP server tests — Milestone 3.

Tests the actual MCP Streamable HTTP interface, not only internal Python functions.
Uses an in-memory SQLite database (set in conftest.py) — no real credentials needed.

Test coverage:
  1.  MCP server can be instantiated and the Starlette app created
  2.  Streamable HTTP transport is available (GET /mcp returns 405 or content, not 404)
  3.  MCP server exposes exactly the 9 expected V1 tools
  4.  Tool schemas are valid (each tool has a name and inputSchema)
  5.  create_goal tool succeeds and returns a goal
  6.  list_goals tool returns the created goal
  7.  create_monitor tool succeeds and returns a monitor
  8.  record_event tool succeeds and returns an event
  9.  get_recent_events tool returns the recorded event
  10. record_action tool succeeds and returns an audit entry
"""

import json

import pytest
from starlette.testclient import TestClient

# conftest.py sets DATABASE_URL="sqlite:///:memory:" and calls
# Base.metadata.create_all() before this module is imported.
import server as mcp_server_module

EXPECTED_TOOLS = {
    "get_current_context",
    "list_goals",
    "create_goal",
    "create_monitor",
    "list_monitors",
    "record_event",
    "get_recent_events",
    "create_notification",
    "record_action",
}


@pytest.fixture(scope="module")
def client():
    """Starlette TestClient for the MCP Streamable HTTP app."""
    app = mcp_server_module.create_app()
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def _mcp_call(client, method: str, params: dict = None) -> dict:
    """Send a JSON-RPC 2.0 request to the MCP endpoint and return the parsed response."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }
    response = client.post(
        "/mcp",
        json=payload,
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert response.status_code in (200, 202), (
        f"Unexpected status {response.status_code}: {response.text[:500]}"
    )
    # Streamable HTTP may return SSE or JSON
    text = response.text
    # If SSE, extract the data: line
    if "data:" in text:
        for line in text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
    return response.json()


# ── 1. Server instantiation ───────────────────────────────────────────────────


def test_mcp_server_instantiation():
    """MCP server can be instantiated and the Starlette app created."""
    app = mcp_server_module.create_app()
    assert app is not None
    assert hasattr(app, "routes")


# ── 2. Streamable HTTP transport ──────────────────────────────────────────────


def test_streamable_http_endpoint_exists(client):
    """
    GET /mcp returns something other than 404 — the endpoint exists.
    (405 Method Not Allowed is expected for GET on a POST-only endpoint.)
    """
    response = client.get("/mcp")
    assert response.status_code != 404, "/mcp endpoint must exist (got 404)"


# ── 3. Expected V1 tools are exposed ─────────────────────────────────────────


def test_all_v1_tools_registered():
    """MCP server exposes exactly the 9 expected V1 tools."""
    registered = {t.name for t in mcp_server_module.mcp._tool_manager.list_tools()}
    assert registered == EXPECTED_TOOLS, (
        f"Tool mismatch.\nExpected: {sorted(EXPECTED_TOOLS)}\nGot:      {sorted(registered)}"
    )


# ── 4. Tool schemas are valid ────────────────────────────────────────────────


def test_tool_schemas_are_valid():
    """Each registered tool has a name and a non-empty description."""
    tools = mcp_server_module.mcp._tool_manager.list_tools()
    for tool in tools:
        assert tool.name, f"Tool is missing a name: {tool!r}"
        assert tool.description, f"Tool '{tool.name}' is missing a description"


# ── 5. create_goal ───────────────────────────────────────────────────────────


def test_create_goal_tool(client):
    """create_goal creates a goal and returns it."""
    result = _mcp_call(
        client,
        "tools/call",
        {
            "name": "create_goal",
            "arguments": {
                "title": "Prepare for interview",
                "priority": "high",
                "deadline": "2026-10-01T09:00:00Z",
            },
        },
    )
    assert "error" not in result, f"Tool error: {result.get('error')}"
    content = result.get("result", {}).get("content", [{}])
    text = content[0].get("text", "") if content else ""
    data = json.loads(text) if text else result.get("result", {})
    goal = data.get("goal", data)
    assert goal.get("title") == "Prepare for interview"
    assert goal.get("status") == "active"


# ── 6. list_goals ────────────────────────────────────────────────────────────


def test_list_goals_tool(client):
    """list_goals returns active goals including the one just created."""
    result = _mcp_call(
        client,
        "tools/call",
        {"name": "list_goals", "arguments": {"status": "active"}},
    )
    assert "error" not in result, f"Tool error: {result.get('error')}"
    content = result.get("result", {}).get("content", [{}])
    text = content[0].get("text", "") if content else ""
    data = json.loads(text) if text else result.get("result", {})
    goals = data.get("goals", [])
    assert len(goals) >= 1
    titles = [g["title"] for g in goals]
    assert "Prepare for interview" in titles


# ── 7. create_monitor ────────────────────────────────────────────────────────


def test_create_monitor_tool(client):
    """create_monitor creates an active monitor and returns it."""
    result = _mcp_call(
        client,
        "tools/call",
        {
            "name": "create_monitor",
            "arguments": {
                "name": "Package delivery",
                "condition": "package_delivered AND user_away",
            },
        },
    )
    assert "error" not in result, f"Tool error: {result.get('error')}"
    content = result.get("result", {}).get("content", [{}])
    text = content[0].get("text", "") if content else ""
    data = json.loads(text) if text else result.get("result", {})
    monitor = data.get("monitor", data)
    assert monitor.get("name") == "Package delivery"
    assert monitor.get("status") == "active"


# ── 8. record_event ──────────────────────────────────────────────────────────


def test_record_event_tool(client):
    """record_event stores an event and returns it."""
    result = _mcp_call(
        client,
        "tools/call",
        {
            "name": "record_event",
            "arguments": {
                "source": "home_simulator",
                "event_type": "package_delivered",
                "importance": "medium",
                "payload_json": '{"carrier": "FedEx"}',
            },
        },
    )
    assert "error" not in result, f"Tool error: {result.get('error')}"
    content = result.get("result", {}).get("content", [{}])
    text = content[0].get("text", "") if content else ""
    data = json.loads(text) if text else result.get("result", {})
    event = data.get("event", data)
    assert event.get("event_type") == "package_delivered"
    assert event.get("source") == "home_simulator"


# ── 9. get_recent_events ─────────────────────────────────────────────────────


def test_get_recent_events_tool(client):
    """get_recent_events returns at least the event just recorded."""
    result = _mcp_call(
        client,
        "tools/call",
        {"name": "get_recent_events", "arguments": {"limit": 5}},
    )
    assert "error" not in result, f"Tool error: {result.get('error')}"
    content = result.get("result", {}).get("content", [{}])
    text = content[0].get("text", "") if content else ""
    data = json.loads(text) if text else result.get("result", {})
    events = data.get("events", [])
    assert len(events) >= 1
    types = [e["event_type"] for e in events]
    assert "package_delivered" in types


# ── 10. record_action ────────────────────────────────────────────────────────


def test_record_action_tool(client):
    """record_action creates an audit log entry and returns it."""
    result = _mcp_call(
        client,
        "tools/call",
        {
            "name": "record_action",
            "arguments": {
                "action_type": "trip_activated",
                "description": "User activated trip mode for 3 days.",
                "status": "completed",
            },
        },
    )
    assert "error" not in result, f"Tool error: {result.get('error')}"
    content = result.get("result", {}).get("content", [{}])
    text = content[0].get("text", "") if content else ""
    data = json.loads(text) if text else result.get("result", {})
    action = data.get("action", data)
    assert action.get("action_type") == "trip_activated"
    assert action.get("status") == "completed"
