"""LIFE OS — AI Agent module.

The agent orchestrates: intent understanding → context retrieval → tool
selection → tool execution → result validation → response generation.

It is a module inside backend/agent/ (per ARCHITECTURE.md §4) and is kept
separate from both the FastAPI app and the MCP server.  It reuses the
existing V1 tool functions directly (no duplication) and talks to a
ModelProvider interface so that a deterministic mock can be used for tests
before AWS Bedrock is integrated.
"""
