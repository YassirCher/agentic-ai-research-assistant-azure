import os
import sys

import pytest
from sqlmodel import SQLModel


TESTS_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.dirname(TESTS_DIR)

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

os.environ.setdefault("ENV", "test")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")


from app.core.upload_jobs import upload_job_store
from app.core.rate_limit import rate_limiter
from app.db.database import engine


@pytest.fixture(scope="session", autouse=True)
def init_test_database_schema():
    """Create SQLModel tables once so CI tests don't depend on app lifespan hooks."""
    SQLModel.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def reset_runtime_state():
    """Clear in-memory stores and wipe DB rows to keep tests deterministic."""
    with engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM message")
        conn.exec_driver_sql("DELETE FROM chat")

    with rate_limiter._lock:
        rate_limiter._requests.clear()

    with upload_job_store._lock:
        upload_job_store._jobs.clear()

    yield
