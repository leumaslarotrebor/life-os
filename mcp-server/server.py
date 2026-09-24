"""
LIFE OS — MCP Server (Streamable HTTP).

Starts a self-hosted MCP server using the official MCP Python SDK.
Transport: Streamable HTTP (required by ARCHITECTURE.md §7).

PATH BOOTSTRAP STRATEGY:
  This server adds two paths to sys.path before importing anything:
    1. The repo root  -> makes `backend` importable
    2. The mcp-server directory  -> makes `tools` importable
  This avoids duplicating the SQLAlchemy models and is the simplest
  approach for a monorepo where two services share a package.

Start command (from repo root, venv active):
    python mcp-server/server.py

  Or via uvicorn:
    uvicorn "mcp-server.server:create_app" --factory --host 127.0.0.1 --port 8001

MCP endpoint: http://127.0.0.1:8001/mcp
"""

# NOTE: do NOT add `from __future__ import annotations` here.
# The mcp library's Tool.from_function inspects annotations at runtime;
# making them strings (PEP 563 lazy evaluation) causes an issubclass() error
# on Python 3.14 inside the mcp SDK.

import os
import sys
from pathlib import Path
from typing import Any

# ── Path bootstrap ────────────────────────────────────────────────────────────
_MCP_SERVER_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _MCP_SERVER_DIR.parent

for _p in [str(_REPO_ROOT), str(_MCP_SERVER_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Imports ───────────────────────────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP  # noqa: E402

from tools.v1_tools import (  # noqa: E402
    create_goal,
    create_monitor,
    create_notification,
    get_current_context,
    get_recent_events,
    list_goals,
    list_monitors,
    record_action,
    record_event,
)

mcp = FastMCP(
    name="life-os-mcp",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_SERVER_PORT", "8001")),
    stateless_http=True,
)

# ── Register all 9 V1 tools ───────────────────────────────────────────────────
# Return type is Any (not dict) so the mcp SDK's annotation inspection
# does not fail on Python 3.14 with a generic alias.


@mcp.tool(name="get_current_context")
def get_current_context_tool() -> Any:
    """
    Return a compact snapshot of the current LIFE OS context:
    active goals, active monitors, and the 10 most recent events.
    Call this at the start of every reasoning cycle.
    """
    return get_current_context()


@mcp.tool(name="list_goals")
def list_goals_tool(status: str = "active") -> Any:
    """
    Return goals filtered by status.
    status: active | paused | completed | cancelled  (default: active)
    """
    return list_goals(status=status)


@mcp.tool(name="create_goal")
def create_goal_tool(
    title: str,
    description: str = "",
    priority: str = "",
    deadline: str = "",
) -> Any:
    """
    Create a new active goal.
    title: Required.
    description: Optional longer context.
    priority: Optional -- low | medium | high.
    deadline: Optional ISO-8601 datetime, e.g. '2026-10-01T09:00:00Z'.
    """
    return create_goal(
        title=title,
        description=description or None,
        priority=priority or None,
        deadline=deadline or None,
    )


@mcp.tool(name="create_monitor")
def create_monitor_tool(
    name: str,
    description: str = "",
    condition: str = "",
    related_goal: int = 0,
) -> Any:
    """
    Create an active monitor.
    name: Required.
    description: Optional context.
    condition: Optional trigger condition, e.g. 'package_delivered AND user_away'.
    related_goal: Optional ID of a related goal (0 = none).
    """
    return create_monitor(
        name=name,
        description=description or None,
        condition=condition or None,
        related_goal=related_goal if related_goal > 0 else None,
    )


@mcp.tool(name="list_monitors")
def list_monitors_tool() -> Any:
    """Return all active monitors."""
    return list_monitors()


@mcp.tool(name="record_event")
def record_event_tool(
    source: str,
    event_type: str,
    importance: str = "",
    payload_json: str = "",
) -> Any:
    """
    Store an incoming event. Does NOT perform AI reasoning.
    source: Required. Origin, e.g. 'home_simulator'.
    event_type: Required. Category, e.g. 'package_delivered'.
    importance: Optional hint -- low | medium | high.
    payload_json: Optional JSON string with structured event data.
    """
    import json as _json

    payload = None
    if payload_json:
        try:
            payload = _json.loads(payload_json)
        except _json.JSONDecodeError as exc:
            raise ValueError("payload_json must be valid JSON") from exc

    return record_event(
        source=source,
        event_type=event_type,
        payload=payload,
        importance=importance or None,
    )


@mcp.tool(name="get_recent_events")
def get_recent_events_tool(limit: int = 10) -> Any:
    """
    Return recent events, newest first.
    limit: Maximum events to return (default 10, max 50).
    """
    return get_recent_events(limit=limit)


@mcp.tool(name="create_notification")
def create_notification_tool(message: str, context: str = "") -> Any:
    """
    Create a user-facing notification.
    message: Required. The notification text for the user.
    context: Optional. Why the notification was created.
    Stored in the actions table with action_type='notification'.
    """
    return create_notification(message=message, context=context or None)


@mcp.tool(name="record_action")
def record_action_tool(
    action_type: str,
    description: str = "",
    status: str = "completed",
) -> Any:
    """
    Record an agent action in the LIFE OS audit log.
    action_type: Required. Label, e.g. 'create_monitor'.
    description: Optional explanation.
    status: completed | pending | failed  (default: completed).
    """
    return record_action(
        action_type=action_type,
        description=description or None,
        status=status,
    )


# ── Starlette app factory (for uvicorn / tests) ───────────────────────────────


def create_app():
    """Return the Starlette ASGI app for the MCP Streamable HTTP server."""
    return mcp.streamable_http_app()


# ── CLI entry point ───────────────────────────────────────────────────────────


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
