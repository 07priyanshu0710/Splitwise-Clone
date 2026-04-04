import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.db.session import get_db
from app.db.base_class import Base
from app.core.config import settings

TEST_DB_NAME = "splitwise_test"
SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql+asyncpg", "postgresql")
TEST_SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.rsplit('/', 1)[0] + f"/{TEST_DB_NAME}"

@pytest.fixture(scope="session")
def setup_test_db():
    default_engine = create_engine(SQLALCHEMY_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with default_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))

    engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    yield

@pytest.fixture(scope="session")
def session_engine(setup_test_db):
    engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db(session_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=session_engine)
    db = SessionLocal()

    yield db

    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def test_user_token_headers(client, db):
    uid1 = str(uuid.uuid4())[:8]
    uid2 = str(uuid.uuid4())[:8]

    email1 = f"user_{uid1}@example.com"
    email2 = f"user_{uid2}@example.com"
    pwd = "password123"

    client.post("/api/v1/auth/register", json={"email": email1, "password": pwd, "full_name": "User 1"})
    res1 = client.post("/api/v1/auth/login", data={"username": email1, "password": pwd})
    token1 = res1.json()["access_token"]
    u_res1 = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token1}"})

    client.post("/api/v1/auth/register", json={"email": email2, "password": pwd, "full_name": "User 2"})
    res2 = client.post("/api/v1/auth/login", data={"username": email2, "password": pwd})
    token2 = res2.json()["access_token"]
    u_res2 = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token2}"})

    return {
        "token1": {"Authorization": f"Bearer {token1}"},
        "token2": {"Authorization": f"Bearer {token2}"},
        "email1": email1,
        "email2": email2,
        "user1_id": u_res1.json()["id"],
        "user2_id": u_res2.json()["id"]
    }
