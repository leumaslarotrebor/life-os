"""
Database tests for LIFE OS — Milestone 2.

Uses an in-memory SQLite database so no external credentials are required.
These tests verify the schema, models, and basic insert/retrieve operations.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base
from backend.models import Action, Event, Goal, Memory, Monitor
from backend.models.goal import GoalStatus
from backend.models.monitor import MonitorStatus
from backend.models.action import ActionStatus
from backend.models.memory import MemoryType

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def db_engine():
    """Create a fresh in-memory SQLite engine with all tables for the test module."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Yield a database session and roll back after each test for isolation."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ── 1. Connection ──────────────────────────────────────────────────────────────

def test_database_connection(db_engine):
    """Database connection works and responds to a simple query."""
    with db_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


# ── 2. Tables exist ────────────────────────────────────────────────────────────

def test_all_tables_created(db_engine):
    """All five required tables exist after Base.metadata.create_all."""
    inspector = inspect(db_engine)
    tables = set(inspector.get_table_names())
    required = {"goals", "monitors", "events", "actions", "memories"}
    assert required.issubset(tables), f"Missing tables: {required - tables}"


# ── 3. Goal ────────────────────────────────────────────────────────────────────

def test_goal_insert_and_retrieve(db_session):
    """A goal can be inserted and retrieved with correct field values."""
    goal = Goal(
        title="Prepare for interview",
        description="Python, SQL, and system design.",
        status=GoalStatus.active,
        priority="high",
        deadline=datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc),
    )
    db_session.add(goal)
    db_session.flush()

    retrieved = db_session.query(Goal).filter_by(title="Prepare for interview").first()
    assert retrieved is not None
    assert retrieved.status == GoalStatus.active
    assert retrieved.priority == "high"
    assert retrieved.id is not None


# ── 4. Monitor ─────────────────────────────────────────────────────────────────

def test_monitor_insert(db_session):
    """A monitor can be inserted successfully."""
    monitor = Monitor(
        name="Package delivery",
        description="Watch for package while user is away.",
        condition="package_delivered AND user_away",
        status=MonitorStatus.active,
    )
    db_session.add(monitor)
    db_session.flush()

    retrieved = db_session.query(Monitor).filter_by(name="Package delivery").first()
    assert retrieved is not None
    assert retrieved.status == MonitorStatus.active


# ── 5. Event ───────────────────────────────────────────────────────────────────

def test_event_insert(db_session):
    """An event can be inserted successfully."""
    import json

    event = Event(
        timestamp=datetime.now(timezone.utc),
        source="home_simulator",
        event_type="package_delivered",
        payload=json.dumps({"carrier": "FedEx", "location": "front_door"}),
        importance="medium",
        processed=False,
    )
    db_session.add(event)
    db_session.flush()

    retrieved = db_session.query(Event).filter_by(event_type="package_delivered").first()
    assert retrieved is not None
    assert retrieved.source == "home_simulator"
    assert retrieved.processed is False


# ── 6. Action ──────────────────────────────────────────────────────────────────

def test_action_insert(db_session):
    """An action (audit log entry) can be inserted successfully."""
    action = Action(
        action_type="create_notification",
        description="Notified user about package delivery.",
        status=ActionStatus.completed,
    )
    db_session.add(action)
    db_session.flush()

    retrieved = db_session.query(Action).filter_by(action_type="create_notification").first()
    assert retrieved is not None
    assert retrieved.status == ActionStatus.completed


# ── 7. Memory ──────────────────────────────────────────────────────────────────

def test_memory_insert(db_session):
    """A memory row can be inserted successfully."""
    memory = Memory(
        memory_type=MemoryType.short_term,
        content="User is away from home for three days.",
    )
    db_session.add(memory)
    db_session.flush()

    retrieved = db_session.query(Memory).filter_by(
        memory_type=MemoryType.short_term
    ).first()
    assert retrieved is not None
    assert "three days" in retrieved.content
