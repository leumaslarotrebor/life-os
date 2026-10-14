"""LIFE OS — Agent type definitions.

Typed dataclasses and enums that define clear interfaces for:
- UserIntent: what the user wants
- ToolCall: which tool to invoke and with what arguments
- ToolResult: the outcome of a tool call (success or error)
- AgentResponse: the final response to the user
- AgentStep: one step in the agent's reasoning chain (for audit)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    """High-level category of user intent."""
    create_goal = "create_goal"
    create_monitor = "create_monitor"
    query_context = "query_context"
    query_events = "query_events"
    record_event = "record_event"
    notify_user = "notify_user"
    record_audit = "record_audit"
    general_chat = "general_chat"
    unknown = "unknown"


class StepType(str, Enum):
    """One step in the agent's reasoning chain."""
    intent = "intent"
    context = "context"
    tool_call = "tool_call"
    tool_result = "tool_result"
    reasoning = "reasoning"
    response = "response"


@dataclass
class UserIntent:
    """Parsed user intent from the model provider."""
    raw_message: str
    intent_type: IntentType
    entities: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class ToolCall:
    """A tool the agent has decided to call."""
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """The outcome of executing a tool call."""
    tool_name: str
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class AgentStep:
    """One step in the agent's reasoning chain — for the audit log."""
    step_type: StepType
    description: str
    data: dict[str, Any] | None = None


@dataclass
class AgentResponse:
    """Final response returned by the agent to the caller."""
    message: str
    intent_type: IntentType
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    steps: list[AgentStep] = field(default_factory=list)
    requires_confirmation: bool = False
    success: bool = True
    error: str | None = None
