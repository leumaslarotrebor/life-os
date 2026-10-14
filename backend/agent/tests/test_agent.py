"""LIFE OS — Agent tests.

Tests cover:
1. Normal request (create goal) — tool succeeds, response is correct
2. Normal request (create monitor) — tool succeeds, confirmation flagged
3. Query context — get_current_context tool returns data
4. Query events — get_recent_events returns events
5. Tool error — unknown tool name produces error result
6. Invalid result — tool returns success=False
7. Empty context — agent handles empty DB gracefully
8. General chat — unknown intent produces a chat response
9. Audit trail — every response has reasoning steps
10. Tool registry completeness
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

# ── Path bootstrap ────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[3]
_MCP_TOOLS_DIR = _REPO_ROOT / "mcp-server" / "tools"

for _p in [str(_REPO_ROOT), str(_MCP_TOOLS_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Test DB bootstrap ──────────────────────────────────────────────────────────
# Use a named SQLite temp file (same pattern as mcp-server/tests/conftest.py)
_TEST_DB_PATH = f"/tmp/lifeos_agent_test_{uuid.uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"

import backend.database.connection as _conn  # noqa: E402
import backend.models  # noqa: E402, F401

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

_test_engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
_conn.engine = _test_engine
_conn.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_conn.Base.metadata.create_all(bind=_test_engine)

import atexit as _atexit  # noqa: E402


def _cleanup():
    try:
        os.unlink(_TEST_DB_PATH)
    except OSError:
        pass


_atexit.register(_cleanup)

# ── Imports under test ─────────────────────────────────────────────────────────
from backend.agent.model_provider import MockModelProvider  # noqa: E402
from backend.agent.orchestrator import AgentOrchestrator  # noqa: E402
from backend.agent.tool_executor import execute_tool, TOOL_REGISTRY  # noqa: E402
from backend.agent.result_validator import validate_result  # noqa: E402
from backend.agent.types import IntentType, StepType, ToolCall, ToolResult  # noqa: E402

from backend.models.goal import Goal  # noqa: E402
from backend.models.monitor import Monitor  # noqa: E402
from backend.models.event import Event  # noqa: E402
from backend.models.action import Action  # noqa: E402
from backend.models.memory import Memory  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    """Clear all tables before each test so tests are isolated."""
    from sqlalchemy import delete

    db = _conn.SessionLocal()
    try:
        db.execute(delete(Memory))
        db.execute(delete(Event))
        db.execute(delete(Action))
        db.execute(delete(Monitor))
        db.execute(delete(Goal))
        db.commit()
    finally:
        db.close()
    yield
    # Clean up after the test too
    db = _conn.SessionLocal()
    try:
        db.execute(delete(Memory))
        db.execute(delete(Event))
        db.execute(delete(Action))
        db.execute(delete(Monitor))
        db.execute(delete(Goal))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def agent():
    """Agent orchestrator with the deterministic mock provider."""
    return AgentOrchestrator(MockModelProvider())


# ── 1. Normal request: create goal ───────────────────────────────────────────


def test_create_goal_normal(agent):
    """Agent creates a goal and reports success."""
    response = agent.process("I have an interview next Friday")

    assert response.success is True
    assert response.intent_type == IntentType.create_goal
    assert len(response.tool_calls) >= 1

    create_calls = [c for c in response.tool_calls if c.name == "create_goal"]
    assert len(create_calls) == 1

    goal_results = [r for r in response.tool_results if r.tool_name == "create_goal"]
    assert len(goal_results) == 1
    assert goal_results[0].success is True
    assert goal_results[0].data is not None
    assert "goal" in goal_results[0].data
    assert goal_results[0].data["goal"]["status"] == "active"


# ── 2. Normal request: create monitor ────────────────────────────────────────


def test_create_monitor_normal(agent):
    """Agent creates a monitor and flags it for confirmation."""
    response = agent.process("Monitor my package delivery while I'm away")

    assert response.success is True
    assert response.intent_type == IntentType.create_monitor
    assert response.requires_confirmation is True

    monitor_results = [r for r in response.tool_results if r.tool_name == "create_monitor"]
    assert len(monitor_results) == 1
    assert monitor_results[0].success is True
    assert monitor_results[0].data["monitor"]["status"] == "active"


# ── 3. Query context ─────────────────────────────────────────────────────────


def test_query_context(agent):
    """Agent retrieves current context for a 'what's going on' question."""
    response = agent.process("What's going on?")

    assert response.success is True
    assert response.intent_type == IntentType.query_context

    context_results = [r for r in response.tool_results if r.tool_name == "get_current_context"]
    assert len(context_results) >= 1
    assert context_results[0].success is True
    assert "active_goals" in context_results[0].data


# ── 4. Query events ──────────────────────────────────────────────────────────


def test_query_events(agent):
    """Agent retrieves recent events."""
    response = agent.process("What events have happened recently?")

    assert response.success is True
    assert response.intent_type == IntentType.query_events

    event_results = [r for r in response.tool_results if r.tool_name == "get_recent_events"]
    assert len(event_results) == 1
    assert event_results[0].success is True
    assert "events" in event_results[0].data
    assert "count" in event_results[0].data


# ── 5. Tool error: unknown tool ───────────────────────────────────────────────


def test_unknown_tool_error():
    """Executing an unknown tool returns a failure ToolResult, not an exception."""
    call = ToolCall(name="nonexistent_tool", arguments={})
    result = execute_tool(call)

    assert result.success is False
    assert result.error is not None
    assert "Unknown tool" in result.error


# ── 6. Invalid result: validation downgrades bad data ────────────────────────


def test_invalid_result_validation():
    """Validator downgrades a success result with missing keys to a failure."""
    fake_result = ToolResult(
        tool_name="create_goal",
        success=True,
        data={},  # missing "goal" key
    )
    validated = validate_result(fake_result)

    assert validated.success is False
    assert "Missing" in validated.error


# ── 7. Empty context ────────────────────────────────────────────────────────


def test_empty_context(agent):
    """Agent works correctly with an empty database (no goals, monitors, events)."""
    response = agent.process("What's going on?")

    assert response.success is True
    context_results = [r for r in response.tool_results if r.tool_name == "get_current_context"]
    assert context_results[0].data["active_goals"] == []
    assert context_results[0].data["active_monitors"] == []
    assert context_results[0].data["recent_events"] == []


# ── 8. General chat / unknown intent ─────────────────────────────────────────


def test_general_chat_unknown_intent(agent):
    """Unknown intent falls through to general chat with no tool calls."""
    response = agent.process("Tell me a joke")

    assert response.success is True
    assert response.intent_type == IntentType.general_chat
    non_context_calls = [c for c in response.tool_calls if c.name != "get_current_context"]
    assert len(non_context_calls) == 0
    assert "Tell me a joke" in response.message


# ── 9. Audit trail ───────────────────────────────────────────────────────────


def test_audit_trail(agent):
    """Every response has reasoning steps recorded for the audit trail."""
    response = agent.process("I have an interview Friday")

    assert len(response.steps) >= 3  # context + intent + at least one tool call

    step_types = [s.step_type for s in response.steps]
    assert StepType.context in step_types
    assert StepType.intent in step_types

    if response.tool_calls:
        assert StepType.tool_call in step_types
        assert StepType.tool_result in step_types


# ── 10. Tool registry completeness ──────────────────────────────────────────


def test_tool_registry_has_all_9_v1_tools():
    """The tool executor knows about all 9 V1 tools."""
    expected = {
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
    assert set(TOOL_REGISTRY.keys()) == expected
