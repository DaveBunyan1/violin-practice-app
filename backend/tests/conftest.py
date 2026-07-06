import queue

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database.connection import Base, get_db
from app.main import app
from app.pipeline.ingestion import AudioIngestionStream
from tests.utils.audio_harness import AudioStreamTestHarness
from app.core.config import settings

engine = create_engine(
    settings.TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },  # Required for SQLite async thread handling
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Lifecycle Hook: Automatically builds the entire database schema from scratch
    before any tests run, and drops it completely when the test suite finished.
    """
    Base.metadata.create_all(bind=engine)
    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """
    Provides a clean, isolated database transaction for a single test case,
    then rolls back changes so tests don't leak state into each other.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session):
    """
    Overrides the production database dependency in FastAPI with our
    isolated testing session, returning a TestClient ready for endpoint testing.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up dependency overrides after the test finishes
    app.dependency_overrides.clear()


@pytest.fixture
def audio_harness():
    """Provides an isolated ingestion stream and a mock harness for feeding data."""
    test_queue = queue.Queue()
    stream = AudioIngestionStream(inbound_queue=test_queue)
    harness = AudioStreamTestHarness(stream)

    # Return both so your tests can feed data via harness AND inspect output via stream.inbound_queue
    return harness, stream
