# LIFE OS — AI AGENT RULES

## 1. Source of Truth

Before making changes, read:

- SPEC.md
- ARCHITECTURE.md, if it exists
- this file

Do not contradict the product specification without explicitly identifying the conflict.

---

## 2. No Uncontrolled Rewrites

Do not rewrite the entire project.

Modify only the files necessary for the assigned task.

Do not remove working functionality unless explicitly instructed.

---

## 3. Architecture

Do not introduce a new framework, database, AI provider, AWS service, or major dependency without documenting why it is needed.

Prefer the simplest architecture that satisfies the requirement.

---

## 4. AI Providers

Do not add multiple AI providers just because they are available.

The production architecture should have a clearly defined primary AI provider.

Development AIs are separate from production AI.

---

## 5. MCP

MCP tools must:

- have clear names
- validate input
- return structured output
- handle errors
- clearly distinguish reads from mutations
- never claim an action succeeded when it failed

---

## 6. Security

Never:

- hardcode API keys
- commit secrets
- expose credentials
- disable authentication merely to make a demo work
- trust arbitrary user input
- execute arbitrary shell commands from an AI response

Use environment variables for secrets.

---

## 7. AI Behavior

The agent must never fabricate:

- device state
- events
- API results
- actions
- external information

If information is unavailable, the system must say so.

---

## 8. User Control

Do not silently perform consequential actions.

Ask for confirmation where appropriate.

Do not interpret a statement as authorization unless the product specification explicitly defines that behavior.

---

## 9. Testing

Every meaningful feature should have tests.

Before declaring a task complete:

1. Run tests.
2. Check errors.
3. Check existing functionality.
4. Verify the implementation matches SPEC.md.

---

## 10. Documentation

When implementing a major feature, document:

- what changed
- why it changed
- files affected
- tests added
- known limitations

---

## 11. Git

Use small commits.

Commit messages should describe the actual change.

Example:

feat: add persistent goal storage

fix: validate monitor creation input

test: add event relevance tests

---

## 12. Don't Fake Integrations

A simulated service may be used for the hackathon prototype.

If something is simulated:

- clearly identify it in code
- clearly identify it in documentation
- never represent simulated data as real device data

---

## 13. Don't Optimize for Complexity

More code does not mean a better project.

Prefer:

simple > complicated

reliable > impressive-looking

understandable > clever

real integration > fake integration

---

## 14. AI Coding Agents

AI-generated code must be reviewed.

No AI agent is automatically trusted.

Every agent should:

- read the specification
- follow these rules
- explain significant changes
- run tests
- avoid unrelated modifications

---

## 15. Final Principle

LIFE OS should demonstrate:

Context → Reasoning → Tool Use → Action → Memory

Not:

Prompt → LLM → Text

The project must remain an agentic system rather than becoming a generic chatbot.
