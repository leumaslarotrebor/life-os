# LIFE OS — Technical Architecture

Version: 1.1
Status: Initial Architecture (Decisions Resolved)

---

# 1. System Overview

LIFE OS is an agentic application built around:

User
→ Web Interface
→ AI Agent
→ Context / Memory
→ MCP Server
→ Tools and Services
→ Results
→ AI Reasoning
→ User / Action
→ Audit Log

The system must maintain persistent context and support event-driven workflows.

---

# 2. High-Level Architecture

```text
                         USER
                           |
                           v
                +---------------------+
                |   LIFE OS FRONTEND  |
                | React / Next.js     |
                +----------+----------+
                           |
                           v
                +---------------------+
                |    FASTAPI BACKEND  |
                +----------+----------+
                           |
             +-------------+-------------+
             |                           |
             v                           v
      +-------------+             +---------------+
      | AI AGENT    |             | PostgreSQL    |
      | (backend/   |             | / Supabase    |
      |  agent/)    |             +---------------+
      +------+------+
             |
             v
      +-------------+
      | MCP CLIENT  |
      +------+------+
             |
             | Streamable HTTP
             v
      +-------------+
      | MCP SERVER  |
      +------+------+
             |
       +-----+------+----------------+
       |            |                |
       v            v                v
   Goal Tools   Context Tools   Event Tools
       |            |                |
       +------------+----------------+
                    |
                    v
             Simulation / Services

                    ^
                    |
             +------+------+
             | AWS Bedrock |
             +-------------+
```

---

# 3. Frontend

Technology:

- React or Next.js
- TypeScript
- modern CSS/UI system

The frontend is responsible for:

- conversational interface
- dashboard
- goals
- monitors
- event timeline
- AI activity
- settings

The frontend must NOT contain business logic that belongs in the backend.

---

# 4. Backend

Technology:

- Python
- FastAPI

Responsibilities:

- API endpoints
- authentication/session handling
- request validation
- agent orchestration
- database access
- event processing
- MCP integration
- audit logging

The backend should be modular.

**DECISION RESOLVED:** The AI agent code lives inside the backend as a module.
There is NO separate top-level `agent/` directory.

Suggested structure:

```
backend/
├── main.py
├── api/
├── services/
├── models/
├── schemas/
├── agent/          ← AI agent lives here, inside the backend
├── events/
├── memory/
├── database/
└── tests/
```

---

# 5. AI Agent

The AI agent is responsible for reasoning over user requests and available context.

The agent should follow:

```
USER REQUEST
     |
     v
UNDERSTAND INTENT
     |
     v
RETRIEVE RELEVANT CONTEXT
     |
     v
DETERMINE REQUIRED INFORMATION
     |
     v
SELECT TOOL(S)
     |
     v
EXECUTE TOOL
     |
     v
VALIDATE RESULT
     |
     v
REASON
     |
     v
RESPOND OR REQUEST CONFIRMATION
     |
     v
AUDIT ACTION
```

**DECISION RESOLVED:** Event relevance evaluation is an internal AI agent
reasoning step, NOT an MCP tool. When an event arrives, the agent retrieves
context via MCP tools and reasons internally about whether the event matters.
There is no `evaluate_event` MCP tool.

The agent must not directly access arbitrary databases or services if a defined
tool should be used.

---

# 6. AWS Bedrock

AWS Bedrock is the target production AI service for the hackathon implementation.

Purpose:

- natural-language understanding
- reasoning
- planning
- tool selection
- event interpretation
- response generation

Bedrock must be used meaningfully.

Do not add Bedrock only for the sake of qualifying for the AWS Builder challenge.

---

# 7. MCP Architecture

The MCP server is a core part of the Alexa+ implementation.

Transport:

- Streamable HTTP

The MCP server exposes structured tools.

**DECISION RESOLVED:** The V1 implementation contains only the essential tools
required for the first working demo. Deferred tools are documented separately.

### V1 Essential Tools

#### Goal Tools
- `create_goal`
- `list_goals`

#### Context Tools
- `get_current_context`

#### Event Tools
- `record_event`
- `get_recent_events`

#### Monitoring Tools
- `create_monitor`
- `list_monitors`

#### Action Tools
- `create_notification`
- `record_action`

**Total V1 tools: 9**

### Deferred Tools (implement after V1 core loop works)

The following tools are explicitly deferred. Do not implement them until the
V1 core loop is stable.

#### Deferred Goal Tools
- `get_goal`
- `update_goal`
- `complete_goal`

#### Deferred Planning Tools
- `create_plan`
- `get_plan`
- `update_plan`
- `replan_goal`

#### Deferred Context / Memory Tools
- `get_relevant_context`
- `store_memory`
- `retrieve_memory`

#### Deferred Monitoring Tools
- `get_monitor`
- `update_monitor`
- `disable_monitor`

#### Deferred Home Simulation Tools
- `get_home_state`
- `get_door_state`
- `get_recent_home_activity`
- `activate_home_mode`

#### Removed Tools
- `evaluate_event` — **REMOVED.** Event relevance evaluation is an internal
  agent reasoning step, not an MCP tool.

---

# 8. MCP Tool Flow

Example:

```
User:
"I'm leaving for three days."

        |
        v

AI Agent
        |
        v

get_current_context()
        |
        v

create_monitor()
        |
        v

record_action()
        |
        v

AI response
```

The agent should use tools instead of inventing information.

---

# 9. Database

**DECISION RESOLVED:** PostgreSQL is the only persistent storage for V1.

- No vector database.
- No pgvector extension.
- All goals, monitors, events, actions, memories, and context are stored as
  rows in PostgreSQL.
- pgvector may be reconsidered after V1 is working if semantic search becomes
  genuinely necessary.

Target: PostgreSQL / Supabase

Initial entities:

- users
- goals
- events
- memories
- monitors
- actions
- notifications

---

# 10. Goal Model

A goal should contain approximately:

- id
- title
- description
- status
- priority
- deadline
- created_at
- updated_at

Possible statuses:

- active
- paused
- completed
- cancelled

---

# 11. Event Model

An event should contain:

- id
- timestamp
- source
- event_type
- payload
- importance
- processed
- created_at

Example:

```json
{
  "source": "home_simulator",
  "event_type": "package_delivered",
  "importance": "medium"
}
```

---

# 12. Monitor Model

A monitor represents an ongoing condition that LIFE OS should watch.

Example:

- id
- name
- description
- condition
- related_goal
- status
- created_at
- updated_at

Example:

```
Monitor:
Package delivery while user is away

Condition:
package_delivered AND user_away

Response:
notify_user
```

---

# 13. Memory Architecture

**DECISION RESOLVED:** For V1, all memory is stored in PostgreSQL as rows.

Memory is divided into:

### Short-term context

Recent conversation and current task.
Stored as rows in the `memories` table with a `type = 'short_term'` tag.

### Persistent user state

Goals, plans, monitors and preferences.
Stored in their dedicated tables.

### Event history

Important historical events.
Stored in the `events` table.

### Derived memory

Useful information inferred from previous events.
Stored as rows in the `memories` table with a `type = 'derived'` tag.

No vector database is introduced in V1.
Memory should be relevant and minimal. Do not store unnecessary information.

---

# 14. Event Processing Architecture

Events follow:

```
EVENT RECEIVED
      |
      v
VALIDATE EVENT
      |
      v
STORE EVENT
      |
      v
CHECK ACTIVE MONITORS
      |
      v
RETRIEVE RELEVANT CONTEXT  ← via MCP: get_current_context, get_recent_events
      |
      v
AI RELEVANCE EVALUATION    ← internal agent reasoning step, NOT an MCP tool
      |
      v
DECISION
   /       \
  /         \
IGNORE     ACTION
             |
             v
       RECORD ACTION        ← via MCP: record_action
             |
             v
       NOTIFY USER          ← via MCP: create_notification
```

---

# 15. User Control

The system must distinguish between:

- information
- recommendation
- proposed action
- confirmed action
- completed action

Example:

The AI should say:

"I can adjust your interview plan."

before silently changing an important plan.

For consequential actions, confirmation should be used where appropriate.

---

# 16. Audit System

Important agent actions must be recorded.

Example:

```
14:02  User activated Trip Mode
14:05  LIFE OS created delivery monitor
16:42  Package delivery event received
16:42  Event evaluated as relevant
16:43  Notification created
```

The audit log should make the system understandable.

---

# 17. Security

Never store secrets in source code.

Use environment variables.

```
.env
```

Secrets must never be committed to GitHub.

The application should validate:

- user input
- MCP arguments
- database input
- tool responses

The AI must not be allowed to execute arbitrary shell commands.

---

# 18. Error Handling

Every external operation should handle failure.

Example:

```
MCP unavailable
       |
       v
Agent detects failure
       |
       v
Does not fabricate result
       |
       v
Tells user the action could not be completed
```

The system must never claim "Done" when an action actually failed.

---

# 19. Simulation Layer

Because the prototype does not require physical hardware, home/device events may
initially be simulated.

Example simulator:

```
simulator/
├── events.py
└── scenarios.py
```

Possible simulated events:

- door_opened
- door_closed
- package_delivered
- motion_detected
- user_left_home
- user_returned_home

The UI and documentation must clearly identify simulated data as simulated.

---

# 20. Testing Strategy

Testing layers:

- Unit tests — test individual functions
- MCP tests — test tool inputs and outputs
- Agent tests — test tool selection and behavior
- Event tests — test event → context → decision flows
- End-to-end tests — test user request → agent → MCP → database → result → response

---

# 21. Example End-to-End Flow

Scenario:

User: "I'm leaving home for three days."

System:
1. Parse user intent.
2. Retrieve active goals.
3. Retrieve relevant upcoming events.
4. Identify potentially relevant monitors.
5. Create or propose trip context.
6. Ask for confirmation when required.
7. Record the decision.

Later:

Event: `package_delivered`

System:
1. Store event.
2. Check active monitors.
3. Retrieve trip context.
4. Agent reasons internally about relevance.
5. Determine response.
6. Create notification.
7. Record action.
8. Display event in timeline.

---

# 22. Repository Structure

```
life-os/
│
├── README.md
├── SPEC.md
├── ARCHITECTURE.md
├── AGENT_RULES.md
├── .gitignore
├── .env.example
│
├── frontend/
│
├── backend/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── agent/        ← AI agent module (inside backend)
│   ├── events/
│   ├── memory/
│   ├── database/
│   └── tests/
│
├── mcp-server/
│
├── database/
│
├── simulator/
│
├── tests/
│
└── docs/
    ├── decisions/
    ├── research/
    └── reviews/
```

**Key structural decision:** There is NO top-level `agent/` directory.
The agent is a module inside `backend/agent/`.

Do not create every directory immediately.
Directories should be created when their implementation begins.

---

# 23. Development Order

Build in this order:

1. Repository configuration
2. Backend skeleton
3. Database connection
4. Goal system
5. Event system
6. MCP server
7. MCP tools (V1 essential tools only)
8. AI agent
9. AWS Bedrock integration
10. Monitoring engine
11. Frontend dashboard
12. Event timeline
13. AI activity view
14. End-to-end integration
15. Testing
16. Demo preparation

Do not build advanced features before the core loop works.

---

# 24. Core Loop

The minimum working LIFE OS loop is:

```
USER
 ↓
AI AGENT
 ↓
CONTEXT
 ↓
MCP TOOL
 ↓
DATABASE / SIMULATOR
 ↓
RESULT
 ↓
AI REASONING
 ↓
USER
```

The minimum event-driven loop is:

```
EVENT
 ↓
MONITOR
 ↓
CONTEXT
 ↓
AI REASONING
 ↓
ACTION
 ↓
AUDIT
```

These two loops must work before adding advanced features.

---

# 25. Architecture Decision Rule

When choosing between two implementations:

Prefer the option that is:

- simpler
- more reliable
- easier to demonstrate
- easier to test
- easier to explain to judges

Do not choose technology merely because it sounds advanced.

---

# 26. Resolved Architecture Decisions

| Decision | Resolution |
|---|---|
| Agent location | Inside `backend/agent/` — no separate top-level `agent/` directory |
| `evaluate_event` | Removed from MCP tool list — internal agent reasoning step |
| Memory storage for V1 | PostgreSQL only — no vector database, no pgvector |
| V1 MCP tool count | 9 essential tools (see §7) |

---

# 27. Current Architecture Status

Frontend: PLANNED

Backend: PLANNED

Database: PLANNED

MCP Server: PLANNED

AI Agent: PLANNED

AWS Bedrock: PLANNED

Event Engine: PLANNED

Memory: PLANNED

Monitoring: PLANNED

Simulator: PLANNED

Testing: PLANNED

Production deployment: NOT STARTED
