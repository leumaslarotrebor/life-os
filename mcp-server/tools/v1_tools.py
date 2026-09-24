"""
LIFE OS — V1 MCP Tools.

Implements the 9 essential V1 tools defined in ARCHITECTURE.md §7.

ARCHITECTURAL DECISION:
  create_notification stores a row in the `actions` table with
  action_type="notification".  A dedicated `notifications` table is not
  created in this milestone; the existing audit-log model is sufficient
  for V1 and avoids unnecessary schema complexity.

Database access:
  Every tool creates its own session via SessionLocal and closes it in a
  finally block.  Sessions are never shared across tool calls.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

# The mcp-server shares the backend's database and model packages.
# The repo root must be on sys.path (set in server.py before importing here).
from backend.database.connection import SessionLocal
from backend.models.action import Action, ActionStatus
from backend.models.event import Event
from backend.models.goal import Goal, GoalStatus
from backend.models.monitor import Monitor, MonitorStatus

# ── helpers ──────────────────────────────────────────────────────────────────


def _goal_to_dict(g: Goal) -> dict[str, Any]:
    return {
        "id": g.id,
        "title": g.title,
        "description": g.description,
        "status": g.status.value,
        "priority": g.priority,
        "deadline": g.deadline.isoformat() if g.deadline else None,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }


def _monitor_to_dict(m: Monitor) -> dict[str, Any]:
    return {
        "id": m.id,
        "name": m.name,
        "description": m.description,
        "condition": m.condition,
        "related_goal": m.related_goal,
        "status": m.status.value,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _event_to_dict(e: Event) -> dict[str, Any]:
    payload = None
    if e.payload:
        try:
            payload = json.loads(e.payload)
        except (json.JSONDecodeError, TypeError):
            payload = e.payload
    return {
        "id": e.id,
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        "source": e.source,
        "event_type": e.event_type,
        "payload": payload,
        "importance": e.importance,
        "processed": e.processed,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _action_to_dict(a: Action) -> dict[str, Any]:
    return {
        "id": a.id,
        "action_type": a.action_type,
        "description": a.description,
        "status": a.status.value,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


# ── Tool 1: get_current_context ───────────────────────────────────────────────


def get_current_context() -> dict[str, Any]:
    """
    Return a compact snapshot of the current LIFE OS context:
    active goals, active monitors, and the 10 most recent events.

    The AI agent calls this at the start of each reasoning cycle.
    """
    db = SessionLocal()
    try:
        goals = db.query(Goal).filter(Goal.status == GoalStatus.active).all()
        monitors = (
            db.query(Monitor).filter(Monitor.status == MonitorStatus.active).all()
        )
        events = (
            db.query(Event)
            .order_by(Event.timestamp.desc())
            .limit(10)
            .all()
        )
        return {
            "active_goals": [_goal_to_dict(g) for g in goals],
            "active_monitors": [_monitor_to_dict(m) for m in monitors],
            "recent_events": [_event_to_dict(e) for e in events],
        }
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Database error retrieving context: {exc}") from exc
    finally:
        db.close()


# ── Tool 2: list_goals ────────────────────────────────────────────────────────


def list_goals(status: str = "active") -> dict[str, Any]:
    """
    Return goals filtered by status.

    Parameters:
        status: one of active | paused | completed | cancelled  (default: active)
    """
    valid_statuses = {s.value for s in GoalStatus}
    if status not in valid_statuses:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {sorted(valid_statuses)}"
        )
    db = SessionLocal()
    try:
        goals = db.query(Goal).filter(Goal.status == GoalStatus(status)).all()
        return {"goals": [_goal_to_dict(g) for g in goals], "count": len(goals)}
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Database error listing goals: {exc}") from exc
    finally:
        db.close()


# ── Tool 3: create_goal ───────────────────────────────────────────────────────


def create_goal(
    title: str,
    description: str | None = None,
    priority: str | None = None,
    deadline: str | None = None,
) -> dict[str, Any]:
    """
    Create a new active goal.

    Parameters:
        title:       Required. Short goal description.
        description: Optional longer context.
        priority:    Optional. Suggested values: low | medium | high.
        deadline:    Optional ISO-8601 datetime string, e.g. '2026-10-01T09:00:00Z'.
    """
    if not title or not title.strip():
        raise ValueError("title is required and cannot be empty")

    deadline_dt: datetime | None = None
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(
                f"deadline must be an ISO-8601 datetime string, got: {deadline!r}"
            )

    db = SessionLocal()
    try:
        goal = Goal(
            title=title.strip(),
            description=description,
            status=GoalStatus.active,
            priority=priority,
            deadline=deadline_dt,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return {"goal": _goal_to_dict(goal)}
    except SQLAlchemyError as exc:
        db.rollback()
        raise RuntimeError(f"Database error creating goal: {exc}") from exc
    finally:
        db.close()


# ── Tool 4: create_monitor ────────────────────────────────────────────────────


def create_monitor(
    name: str,
    description: str | None = None,
    condition: str | None = None,
    related_goal: int | None = None,
) -> dict[str, Any]:
    """
    Create an active monitor.

    Parameters:
        name:         Required. Short name for what is being monitored.
        description:  Optional context about why this matters.
        condition:    Optional plain-text trigger condition, e.g.
                      'package_delivered AND user_away'.
        related_goal: Optional ID of an existing goal this monitor relates to.
    """
    if not name or not name.strip():
        raise ValueError("name is required and cannot be empty")

    db = SessionLocal()
    try:
        monitor = Monitor(
            name=name.strip(),
            description=description,
            condition=condition,
            related_goal=related_goal,
            status=MonitorStatus.active,
        )
        db.add(monitor)
        db.commit()
        db.refresh(monitor)
        return {"monitor": _monitor_to_dict(monitor)}
    except SQLAlchemyError as exc:
        db.rollback()
        raise RuntimeError(f"Database error creating monitor: {exc}") from exc
    finally:
        db.close()


# ── Tool 5: list_monitors ─────────────────────────────────────────────────────


def list_monitors() -> dict[str, Any]:
    """
    Return all active monitors.

    Returns enough information for the AI agent to understand what each
    monitor is watching and why.
    """
    db = SessionLocal()
    try:
        monitors = (
            db.query(Monitor).filter(Monitor.status == MonitorStatus.active).all()
        )
        return {
            "monitors": [_monitor_to_dict(m) for m in monitors],
            "count": len(monitors),
        }
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Database error listing monitors: {exc}") from exc
    finally:
        db.close()


# ── Tool 6: record_event ──────────────────────────────────────────────────────


def record_event(
    source: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    importance: str | None = None,
) -> dict[str, Any]:
    """
    Store an incoming event.

    This tool does NOT perform AI reasoning or decide whether the event is
    relevant.  Relevance evaluation is an internal agent reasoning step.

    Parameters:
        source:      Required. Origin of the event, e.g. 'home_simulator'.
        event_type:  Required. Event category, e.g. 'package_delivered'.
        payload:     Optional structured event data (dict).
        importance:  Optional hint: low | medium | high.
    """
    if not source or not source.strip():
        raise ValueError("source is required and cannot be empty")
    if not event_type or not event_type.strip():
        raise ValueError("event_type is required and cannot be empty")

    db = SessionLocal()
    try:
        event = Event(
            timestamp=datetime.now(timezone.utc),
            source=source.strip(),
            event_type=event_type.strip(),
            payload=json.dumps(payload) if payload is not None else None,
            importance=importance,
            processed=False,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return {"event": _event_to_dict(event)}
    except SQLAlchemyError as exc:
        db.rollback()
        raise RuntimeError(f"Database error recording event: {exc}") from exc
    finally:
        db.close()


# ── Tool 7: get_recent_events ─────────────────────────────────────────────────


def get_recent_events(limit: int = 10) -> dict[str, Any]:
    """
    Return recent events, newest first.

    Parameters:
        limit: Maximum number of events to return (default 10, max 50).
    """
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    limit = min(limit, 50)  # hard cap — never return an unbounded result set

    db = SessionLocal()
    try:
        events = (
            db.query(Event)
            .order_by(Event.timestamp.desc())
            .limit(limit)
            .all()
        )
        return {"events": [_event_to_dict(e) for e in events], "count": len(events)}
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Database error retrieving events: {exc}") from exc
    finally:
        db.close()


# ── Tool 8: create_notification ───────────────────────────────────────────────


def create_notification(message: str, context: str | None = None) -> dict[str, Any]:
    """
    Create a notification that should be presented to the user.

    ARCHITECTURAL DECISION: Notifications are stored in the `actions` table
    with action_type="notification".  A dedicated notifications table is not
    created in V1; the existing audit-log model is sufficient and avoids
    unnecessary schema complexity.

    Parameters:
        message: Required. The notification text for the user.
        context: Optional. Extra context about why the notification was created.
    """
    if not message or not message.strip():
        raise ValueError("message is required and cannot be empty")

    description = message.strip()
    if context:
        description = f"{description}\n\nContext: {context.strip()}"

    db = SessionLocal()
    try:
        action = Action(
            action_type="notification",
            description=description,
            status=ActionStatus.completed,
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return {
            "notification": {
                "id": action.id,
                "message": message.strip(),
                "context": context,
                "created_at": action.created_at.isoformat() if action.created_at else None,
            }
        }
    except SQLAlchemyError as exc:
        db.rollback()
        raise RuntimeError(f"Database error creating notification: {exc}") from exc
    finally:
        db.close()


# ── Tool 9: record_action ─────────────────────────────────────────────────────


def record_action(
    action_type: str,
    description: str | None = None,
    status: str = "completed",
) -> dict[str, Any]:
    """
    Record an important LIFE OS agent action in the audit log.

    Parameters:
        action_type:  Required. Short label, e.g. 'create_monitor', 'trip_activated'.
        description:  Optional. Plain-text explanation of what happened.
        status:       One of completed | pending | failed  (default: completed).
    """
    if not action_type or not action_type.strip():
        raise ValueError("action_type is required and cannot be empty")

    valid_statuses = {s.value for s in ActionStatus}
    if status not in valid_statuses:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {sorted(valid_statuses)}"
        )

    db = SessionLocal()
    try:
        action = Action(
            action_type=action_type.strip(),
            description=description,
            status=ActionStatus(status),
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return {"action": _action_to_dict(action)}
    except SQLAlchemyError as exc:
        db.rollback()
        raise RuntimeError(f"Database error recording action: {exc}") from exc
    finally:
        db.close()
