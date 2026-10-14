"""LIFE OS — Tool Executor.

Executes MCP tool calls by dispatching to the existing V1 tool functions
in mcp-server/tools/v1_tools.py.  This module does NOT duplicate the tool
implementations — it imports and calls them directly.

The executor validates results before returning them to the agent.  It
never fabricates results: if a tool raises an error, the ToolResult will
have success=False with the error message.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from backend.agent.types import ToolCall, ToolResult

logger = logging.getLogger(__name__)

# ── Path bootstrap: make mcp-server/tools importable ─────────────────────────
# The MCP tools live in mcp-server/tools/v1_tools.py.  We need that directory
# on sys.path so we can import the tool functions directly without duplicating
# the SQLAlchemy model logic.
_REPO_ROOT = Path(__file__).resolve().parents[2]  # backend/agent/ -> backend/ -> repo root
_MCP_TOOLS_DIR = _REPO_ROOT / "mcp-server" / "tools"

if str(_MCP_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_TOOLS_DIR))

# Import the actual V1 tool functions (no duplication)
from v1_tools import (  # noqa: E402
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

# Registry: tool name -> callable
TOOL_REGISTRY: dict[str, Any] = {
    "get_current_context": get_current_context,
    "list_goals": list_goals,
    "create_goal": create_goal,
    "create_monitor": create_monitor,
    "list_monitors": list_monitors,
    "record_event": record_event,
    "get_recent_events": get_recent_events,
    "create_notification": create_notification,
    "record_action": record_action,
}


def execute_tool(call: ToolCall) -> ToolResult:
    """
    Execute a single tool call.

    Args:
        call: A ToolCall with a name and arguments.

    Returns:
        A ToolResult with success=True and data, or success=False and error.
        Never raises — all exceptions are caught and returned as errors.
    """
    name = call.name

    if name not in TOOL_REGISTRY:
        return ToolResult(
            tool_name=name,
            success=False,
            error=f"Unknown tool: '{name}'. Available: {sorted(TOOL_REGISTRY)}",
        )

    func = TOOL_REGISTRY[name]

    try:
        result = func(**call.arguments)
        return ToolResult(
            tool_name=name,
            success=True,
            data=result,
        )
    except ValueError as exc:
        # Input validation error
        logger.warning("Tool %s rejected input: %s", name, exc)
        return ToolResult(
            tool_name=name,
            success=False,
            error=f"Validation error: {exc}",
        )
    except RuntimeError as exc:
        # Database error wrapped by the tool functions
        logger.error("Tool %s database error: %s", name, exc)
        return ToolResult(
            tool_name=name,
            success=False,
            error=f"Tool execution failed: {exc}",
        )
    except Exception as exc:
        # Unexpected error — catch-all so the agent never crashes
        logger.exception("Tool %s unexpected error", name)
        return ToolResult(
            tool_name=name,
            success=False,
            error=f"Unexpected error in tool '{name}': {exc}",
        )
