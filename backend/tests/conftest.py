import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.services.clicks as clicks_service
from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = (
    "postgresql+psycopg2://linktrack:linktrack@localhost:5432/linktrack_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture(autouse=True)
def clean_database(monkeypatch):
    """Fresh empty tables before every test."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    # The background click recorder opens its own session, so point it at the test DB too.
    monkeypatch.setattr(clicks_service, "SessionLocal", TestingSessionLocal)
    from app.limiter import limiter
    limiter.enabled = False


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
