import os
from collections.abc import Generator

import app.models  # noqa: F401
import pytest
from app.api.deps import get_db
from app.core.config import ApplicationSettings, settings
from app.db.base import Base
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["APP_ENV"] = "test"
settings.APP_ENV = "test"

# In-memory SQLite engine using StaticPool for isolated unit testing
TEST_SQLITE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Create all database schema objects in memory for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a fresh transaction for each test that rolls back upon completion."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def mock_redis_for_unit_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Redis client calls during unit tests to prevent network connection attempts."""
    monkeypatch.setattr("app.core.rate_limit.is_login_rate_limited", lambda identifier: False)
    monkeypatch.setattr("app.core.rate_limit.record_failed_login_attempt", lambda identifier: None)
    monkeypatch.setattr("app.core.rate_limit.clear_failed_login_attempts", lambda identifier: None)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient with the isolated database session dependency."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings() -> ApplicationSettings:
    """Provide settings configured for test environment."""
    return ApplicationSettings(
        APP_ENV="test",
        DEBUG=False,
        POSTGRES_DB="metasphere_test",
        POSTGRES_PASSWORD="test_password_123",
        CORS_ORIGINS=["http://testserver"],
    )
