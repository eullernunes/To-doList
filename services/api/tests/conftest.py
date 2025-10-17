import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.models import Base, User
from app.dependencies import get_session, verify_token

TEST_DB_FD, TEST_DB_PATH = tempfile.mkstemp(suffix=".db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@pytest.fixture(scope="session", autouse=True)
def _create_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    try:
        os.close(TEST_DB_FD)
        os.remove(TEST_DB_PATH)
    except Exception:
        pass

def _get_test_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    app.dependency_overrides[get_session] = _get_test_session

    test_db = next(_get_test_session())
    user = test_db.query(User).filter(User.email == "tester@example.com").first()
    if not user:
        user = User(name="Tester", email="tester@example.com", password="hashed")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

    def _fake_verify_token():
        return user  

    app.dependency_overrides[verify_token] = _fake_verify_token

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
