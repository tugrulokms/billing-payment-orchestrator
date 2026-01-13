from datetime import datetime
from sqlalchemy.orm import Session
from app.infra.models import OutboxEvent


def enqueue_event(db: Session, event_type: str, aggregate_type: str, aggregate_id: str, payload: dict) -> OutboxEvent:
    evt = OutboxEvent(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
    )
    db.add(evt)
    return evt


def publish_pending(db: Session, limit: int = 50) -> int:
    # In a real system, this is where we'd publish to Kafka/RabbitMQ.
    # Here we mark events as published.
    pending = (
        db.query(OutboxEvent)
        .filter(OutboxEvent.published_at.is_(None))
        .order_by(OutboxEvent.created_at.asc())
        .limit(limit)
        .all()
    )
    now = datetime.datetime.now()
    for evt in pending:
        evt.published_at = now
    return len(pending)
