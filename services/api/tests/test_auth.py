from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base
from app.dependencies import get_session

def test_create_account_and_login(tmp_path):
    db_path = tmp_path / "auth.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def _get_sess():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_session] = _get_sess

    client = TestClient(app)

    r = client.post("/auth/create_account", json={
        "name": "Dev",
        "email": "dev@example.com",
        "password": "123"
    })
    assert r.status_code in (200, 201), r.text

    r2 = client.post("/auth/login", json={
        "email": "dev@example.com",
        "password": "123"
    })
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert "access_token" in data and data["token_type"].lower() == "bearer"

    app.dependency_overrides.clear()
