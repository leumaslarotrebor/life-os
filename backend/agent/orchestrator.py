"""LIFE OS — Agent Orchestrator.

The core orchestration layer that ties together:
1. Model provider (intent understanding + tool selection)
2. Tool executor (dispatching to MCP tools)
3. Result validator (checking tool outputs)

The orchestrator follows the flow defined in ARCHITECTURE.md §5:

    USER REQUEST
         ↓
    UNDERSTAND INTENT       ← model_provider.process()
         ↓
    RETRIEVE CONTEXT        ← get_current_context tool
         ↓
    SELECT TOOL(S)          ← from model decision
         ↓
    EXECUTE TOOL(S)         ← tool_executor.execute_tool()
         ↓
    VALIDATE RESULT(S)      ← result_validator.validate_result()
         ↓
    RESPOND / AUDIT         ← AgentResponse with steps

Key design decisions:
- The orchestrator always retrieves context first (ARCHITECTURE.md §8).
- Every step is recorded as an AgentStep for the audit trail.
- If a tool fails, the agent reports the failure honestly — never fabricates
  success (AGENT_RULES.md §7).
- The agent records an audit action for each tool call it makes.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.agent.model_provider import ModelDecision, ModelProvider
from backend.agent.result_validator import validate_result
from backend.agent.tool_executor import execute_tool
from backend.agent.types import (
    AgentResponse,
    AgentStep,
    IntentType,
    StepType,
    ToolCall,
    ToolResult,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the agent loop: intent → context → tools → validate → respond.

    Usage:
        agent = AgentOrchestrator(model_provider)
        response = agent.process("I have an interview Friday")
    """

    def __init__(self, model_provider: ModelProvider) -> None:
        self.provider = model_provider

    def process(self, message: str) -> AgentResponse:
        """
        Process a user message end-to-end.

        Args:
            message: The user's raw message text.

        Returns:
            An AgentResponse with the final message, tool calls/results,
            and the reasoning steps (audit trail).
        """
        steps: list[AgentStep] = []

        # ── 1. Retrieve current context ─────────────────────────────────────
        context_step, context = self._retrieve_context(steps)

        # ── 2. Understand intent (model provider) ──────────────────────────
        decision = self.provider.process(message, context)
        steps.append(
            AgentStep(
                step_type=StepType.intent,
                description=f"Intent classified as: {decision.intent_type.value}",
                data={"confidence": "N/A (mock)", "reasoning": decision.reasoning},
            )
        )

        # ── 3. Execute tool calls ──────────────────────────────────────────
        tool_results: list[ToolResult] = []
        tool_calls: list[ToolCall] = []

        for call in decision.tool_calls:
            tool_calls.append(call)
            steps.append(
                AgentStep(
                    step_type=StepType.tool_call,
                    description=f"Calling tool: {call.name}",
                    data={"arguments": call.arguments},
                )
            )

            result = execute_tool(call)
            result = validate_result(result)

            tool_results.append(result)
            steps.append(
                AgentStep(
                    step_type=StepType.tool_result,
                    description=f"Tool {call.name}: {'success' if result.success else 'failed'}",
                    data={"error": result.error} if not result.success else None,
                )
            )

        # ── 4. Build final response ────────────────────────────────────────
        all_succeeded = all(r.success for r in tool_results)
        any_failed = any(not r.success for r in tool_results)

        if not decision.tool_calls:
            # No tools to call — general chat or unknown intent
            response = AgentResponse(
                message=decision.response_message,
                intent_type=decision.intent_type,
                tool_calls=tool_calls,
                tool_results=tool_results,
                steps=steps,
                requires_confirmation=decision.requires_confirmation,
                success=True,
            )
        elif all_succeeded:
            response = AgentResponse(
                message=decision.response_message,
                intent_type=decision.intent_type,
                tool_calls=tool_calls,
                tool_results=tool_results,
                steps=steps,
                requires_confirmation=decision.requires_confirmation,
                success=True,
            )
        else:
            # At least one tool failed — report honestly
            failure_msgs = [
                f"{r.tool_name}: {r.error}" for r in tool_results if not r.success
            ]
            error_summary = "; ".join(failure_msgs)
            response = AgentResponse(
                message=(
                    f"I attempted to handle your request, but something went wrong: "
                    f"{error_summary}"
                ),
                intent_type=decision.intent_type,
                tool_calls=tool_calls,
                tool_results=tool_results,
                steps=steps,
                requires_confirmation=False,
                success=False,
                error=error_summary,
            )

        steps.append(
            AgentStep(
                step_type=StepType.response,
                description=f"Response delivered: success={response.success}",
            )
        )
        response.steps = steps

        logger.info(
            "Agent processed message: intent=%s tools=%d success=%s",
            response.intent_type.value,
            len(response.tool_calls),
            response.success,
        )

        return response

    def _retrieve_context(self, steps: list[AgentStep]) -> tuple[AgentStep, dict[str, Any]]:
        """Retrieve current context via the get_current_context tool."""
        context_call = ToolCall(name="get_current_context", arguments={})
        raw_result = execute_tool(context_call)
        validated = validate_result(raw_result)

        steps.append(
            AgentStep(
                step_type=StepType.context,
                description=f"Context retrieved: {'success' if validated.success else 'failed'}",
                data=validated.data if validated.success else {"error": validated.error},
            )
        )

        if validated.success and validated.data:
            return steps[-1], validated.data

        # Context retrieval failed — continue with empty context
        logger.warning("Context retrieval failed: %s", validated.error)
        return steps[-1], {}
