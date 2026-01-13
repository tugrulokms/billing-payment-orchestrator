import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON

from app.infra.db import Base

InvoiceStatus = Enum("open", "paid", "void", name="invoice_status")
PaymentAttemptStatus = Enum(
    "requires_action",
    "succeeded",
    "failed",
    name="payment_attempt_status"
)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    status: Mapped[str] = mapped_column(
        InvoiceStatus,
        nullable=False,
        default="open"
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="EUR")
    customer_ref: Mapped[str] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    attempts: Mapped[list["PaymentAttempt"]] = relationship(
        back_populates="invoice",
        cascade="all,delete-orphan"
    )


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "invoices.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
            PaymentAttemptStatus,
            nullable=False,
            default="requires_action"
    )

    # Client retries safety
    idempotency_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )

    # Provider references (webhook uses these)
    provider_payment_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_event_id_last: Mapped[str] = mapped_column(String(64), nullable=True)

    error_code: Mapped[str] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.utcnow
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="attempts")

    __table_args__ = (
        UniqueConstraint("invoice_id", "idempotency_key", name="uq_invoice_idemkey"),
        UniqueConstraint("provider_payment_id", name="uq_provider_payment_id"),
        Index("ix_attempt_invoice", "invoice_id"),
        Index("ix_attempt_status", "status"),
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_outbox_published_at", "published_at"),
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
        Index("ix_outbox_event_type", "event_type"),
    )
