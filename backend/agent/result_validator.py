"""LIFE OS — Result Validator.

Validates tool results before the agent uses them to formulate a response.
This is a critical safety layer: per AGENT_RULES.md §7, the agent must
never fabricate results or claim an action succeeded when it failed.

The validator checks:
- Success/failure status
- Structural validity (expected keys present)
- Non-empty results where data is expected
"""

from __future__ import annotations

import logging

from backend.agent.types import ToolResult

logger = logging.getLogger(__name__)

# Expected top-level keys in each tool's successful return value
EXPECTED_KEYS: dict[str, set[str]] = {
    "get_current_context": {"active_goals", "active_monitors", "recent_events"},
    "list_goals": {"goals", "count"},
    "create_goal": {"goal"},
    "create_monitor": {"monitor"},
    "list_monitors": {"monitors", "count"},
    "record_event": {"event"},
    "get_recent_events": {"events", "count"},
    "create_notification": {"notification"},
    "record_action": {"action"},
}


def validate_result(result: ToolResult) -> ToolResult:
    """
    Validate a tool result.

    If the tool failed, the result is returned as-is (error already set).
    If the tool succeeded but the data is structurally invalid, the result
    is downgraded to a failure with a descriptive error.

    Args:
        result: The raw ToolResult from the executor.

    Returns:
        A validated ToolResult — possibly downgraded if validation failed.
    """
    if not result.success:
        # Already a failure — pass through
        return result

    if result.data is None:
        logger.warning("Tool %s returned success but data is None", result.tool_name)
        return ToolResult(
            tool_name=result.tool_name,
            success=False,
            error=f"Tool '{result.tool_name}' returned no data despite success=True",
        )

    # Check expected keys
    expected = EXPECTED_KEYS.get(result.tool_name)
    if expected is None:
        # Unknown tool shape — accept as-is (shouldn't happen with V1 tools)
        logger.debug("No expected key set for tool %s, skipping structural check", result.tool_name)
        return result

    actual_keys = set(result.data.keys()) if isinstance(result.data, dict) else set()
    missing = expected - actual_keys

    if missing:
        logger.warning(
            "Tool %s returned unexpected structure. Missing keys: %s",
            result.tool_name,
            missing,
        )
        return ToolResult(
            tool_name=result.tool_name,
            success=False,
            data=result.data,
            error=f"Tool '{result.tool_name}' returned incomplete data. Missing: {sorted(missing)}",
        )

    return result
