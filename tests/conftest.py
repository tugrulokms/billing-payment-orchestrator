import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import app
from app.infra.db import SessionLocal


@pytest.fixture()
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session):
    # Her test öncesi tabloları temizle (sıra önemli)
    db.execute(text("DELETE FROM outbox_events"))
    db.execute(text("DELETE FROM payment_attempts"))
    db.execute(text("DELETE FROM invoices"))
    db.commit()

    with TestClient(app) as c:
        yield c
