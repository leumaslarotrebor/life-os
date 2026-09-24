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

### Backend (Milestone 1)

```bash
# From the repo root:

# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start the backend
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Verify health
curl http://127.0.0.1:8000/health
# → {"status":"ok","service":"life-os-backend"}

# 5. Run tests
python -m pytest backend/tests/ -v
```

### Database (Milestone 2)

Requires a running PostgreSQL instance. Set the connection string in `.env`:

```bash
cp .env.example .env
# Edit .env: set DATABASE_URL=postgresql://user:password@localhost:5432/lifeos
```

Run migrations (from repo root, with venv active):

```bash
cd backend
DATABASE_URL=<your-url> alembic upgrade head
```

For local development without PostgreSQL, the backend falls back to a local
SQLite file (`lifeos_dev.db`). Tests always use an in-memory SQLite database
and require no credentials.

### MCP Server, Frontend (future milestones)

Setup instructions will appear here as each milestone is implemented.

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
