# LIFE OS

> Most assistants wait for you to ask. LIFE OS monitors what matters after you make a decision.

LIFE OS is an agentic personal operating system built for the [Amazon Developer Hackathon 2026](https://devpost.com/).

Primary track: **Alexa+** | Secondary target: **AWS Builder**

---

## What it does

When you tell LIFE OS something important — "I'm leaving home for three days" — it doesn't just acknowledge the statement.

It understands the **consequences**: active goals, upcoming deadlines, monitored deliveries, commitments. It creates a plan, sets up monitoring, and tells you what it's doing and why.

When something changes while you're away — a package arrives, a deadline shifts — LIFE OS evaluates whether it matters to your current context and notifies you if it does.

The core loop:

```
USER INTENT
  → UNDERSTAND
  → REMEMBER
  → PLAN
  → MONITOR
  → DETECT CHANGE
  → REASON
  → ACT
  → REMEMBER RESULT
```

---

## Technical Stack

| Layer | Technology |
|---|---|
| Frontend | React / Next.js + TypeScript |
| Backend | Python + FastAPI |
| AI | AWS Bedrock (Claude) |
| Agent tools | MCP server (Streamable HTTP) |
| Database | PostgreSQL / Supabase |
| Simulator | Python event simulator |

---

## Project Status

See [SPEC.md](SPEC.md) for the full product specification.
See [ARCHITECTURE.md](ARCHITECTURE.md) for the technical architecture.
See [AGENT_RULES.md](AGENT_RULES.md) for AI agent development rules.

**Current phase:** Pre-implementation — architecture reviewed, decisions resolved.

---

## Getting Started

```bash
# 1. Copy environment variables
cp .env.example .env
# Edit .env with your database URL, AWS region, and Bedrock model ID

# 2. Backend (once implementation begins)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 3. MCP Server
cd mcp-server
# (setup instructions will appear here)

# 4. Frontend
cd frontend
npm install
npm run dev
```

---

## Simulated Components

This prototype uses a **simulated event system** in place of real hardware integrations.

All simulated data is clearly labelled as simulated in the UI and documentation.
No simulated data is presented as real-world device data.

---

## Hackathon Integrity

- Original project, built during the hackathon.
- AI tools used for development assistance under team supervision.
- Simulated integrations clearly identified.
