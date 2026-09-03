"""
Pytest configuration for Worker Risk Engine.
Sets up an isolated SQLite database fixture for testing so tests run offline
without requiring a live Supabase connection.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as db_module
from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_risk_scores.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Rebind database engine for all tests
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override FastAPI dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    if os.path.exists("./test_risk_scores.db"):
        try:
            os.remove("./test_risk_scores.db")
        except Exception:
            pass
