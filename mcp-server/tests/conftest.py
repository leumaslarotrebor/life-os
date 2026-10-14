"""
Pytest configuration for MCP server tests.

Patches backend.database.connection to use a disposable SQLite file so that
all SessionLocal connections share the same physical database within the
test session. This avoids the shared-memory isolation issue with :memory:.

The temporary database file is cleaned up after the session.
"""

import os
import sys
from pathlib import Path

# ── Path bootstrap ────────────────────────────────────────────────────────────
_MCP_SERVER_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _MCP_SERVER_DIR.parent

for _p in [str(_REPO_ROOT), str(_MCP_SERVER_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Temp database file ────────────────────────────────────────────────────────
import uuid

_TEST_DB_PATH = f"/tmp/lifeos_test_{uuid.uuid4().hex}.db"
TEST_DATABASE_URL = f"sqlite:///{_TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# ── Import and patch the connection module ────────────────────────────────────
# Import order matters: backend.database.connection reads DATABASE_URL at
# module level. We import it here (after setting the env var) and also patch
# the engine/SessionLocal singletons in-place so that tool functions that
# import SessionLocal from this module at their own import time also get the
# test engine.

import backend.database.connection as _conn  # noqa: E402
import backend.models  # noqa: E402, F401  (registers models on Base.metadata)

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

_test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Patch the module-level singletons so any subsequent import of SessionLocal
# from backend.database.connection resolves to the test engine.
_conn.engine = _test_engine
_conn.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# Create all tables.
_conn.Base.metadata.create_all(bind=_test_engine)

import atexit as _atexit


def _cleanup():
    try:
        os.unlink(_TEST_DB_PATH)
    except OSError:
        pass


_atexit.register(_cleanup)
