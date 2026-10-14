"""LIFE OS — Model Provider Interface.

Abstract interface for the AI model that powers the agent.  In production
this will be AWS Bedrock.  For Milestone 4, a deterministic mock provider
(MockModelProvider) is used so tests run without any external API calls.

The provider has one method: `process(message, context)` which returns
a ModelDecision telling the agent what tool(s) to call and/or what to
say to the user.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.agent.types import IntentType, ToolCall


@dataclass
class ModelDecision:
    """What the model decided to do."""
    intent_type: IntentType
    tool_calls: list[ToolCall] = field(default_factory=list)
    response_message: str = ""
    requires_confirmation: bool = False
    reasoning: str = ""


class ModelProvider(ABC):
    """Interface for the AI model that interprets user intent and selects tools."""

    @abstractmethod
    def process(self, message: str, context: dict[str, Any]) -> ModelDecision:
        """
        Interpret a user message given the current context.

        Args:
            message: The raw user message text.
            context: Current LIFE OS context (goals, monitors, recent events).

        Returns:
            A ModelDecision with intent type, optional tool calls, and
            a response message.
        """
        ...


class MockModelProvider(ModelProvider):
    """
    Deterministic mock for testing — no external API calls.

    Uses simple keyword matching to classify intent and decide tool calls.
    This is NOT real AI; it exists so the agent orchestration layer can be
    tested end-to-end before AWS Bedrock is integrated.
    """

    def process(self, message: str, context: dict[str, Any]) -> ModelDecision:
        msg_lower = message.lower().strip()

        # ── Intent: create_goal ───────────────────────────────────────────────
        if "interview" in msg_lower or "goal" in msg_lower and "create" in msg_lower:
            return ModelDecision(
                intent_type=IntentType.create_goal,
                tool_calls=[
                    ToolCall(
                        name="create_goal",
                        arguments={
                            "title": message.strip(),
                            "priority": "high",
                        },
                    )
                ],
                response_message=f"I've created a new goal: '{message.strip()}'.",
                reasoning="User mentioned an interview or asked to create a goal.",
            )

        # ── Intent: create_monitor ────────────────────────────────────────────
        if "monitor" in msg_lower or "watch" in msg_lower or "track" in msg_lower:
            return ModelDecision(
                intent_type=IntentType.create_monitor,
                tool_calls=[
                    ToolCall(
                        name="create_monitor",
                        arguments={
                            "name": message.strip(),
                            "condition": "package_delivered AND user_away",
                        },
                    )
                ],
                response_message=f"I've set up a monitor for: '{message.strip()}'.",
                requires_confirmation=True,
                reasoning="User asked to monitor or track something.",
            )

        # ── Intent: query_context ──────────────────────────────────────────────
        if "what" in msg_lower and ("going on" in msg_lower or "context" in msg_lower or "status" in msg_lower):
            return ModelDecision(
                intent_type=IntentType.query_context,
                tool_calls=[
                    ToolCall(name="get_current_context", arguments={}),
                ],
                response_message="Here's the current context.",
                reasoning="User asked about the current state.",
            )

        # ── Intent: query_events ───────────────────────────────────────────────
        if "event" in msg_lower or "what happened" in msg_lower:
            return ModelDecision(
                intent_type=IntentType.query_events,
                tool_calls=[
                    ToolCall(name="get_recent_events", arguments={"limit": 10}),
                ],
                response_message="Here are the recent events.",
                reasoning="User asked about recent events.",
            )

        # ── Intent: record_event ──────────────────────────────────────────────
        if "delivered" in msg_lower or "package" in msg_lower and "arrived" in msg_lower:
            return ModelDecision(
                intent_type=IntentType.record_event,
                tool_calls=[
                    ToolCall(
                        name="record_event",
                        arguments={
                            "source": "home_simulator",
                            "event_type": "package_delivered",
                            "importance": "medium",
                        },
                    )
                ],
                response_message="I've recorded a package delivery event.",
                reasoning="User mentioned a package delivery.",
            )

        # ── Default: general chat ─────────────────────────────────────────────
        return ModelDecision(
            intent_type=IntentType.general_chat,
            response_message=f"I heard you say: '{message}'. I'm not sure how to help with that yet.",
            reasoning="No specific intent matched. Defaulting to general chat.",
        )
