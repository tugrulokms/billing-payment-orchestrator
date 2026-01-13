from pydantic import BaseModel, Field
from typing import Optional, List, Any


class InvoiceCreate(BaseModel):
    amount_cents: int = Field(gt=0)
    currency: str = "EUR"
    customer_ref: Optional[str] = None


class InvoiceOut(BaseModel):
    invoice_id: str
    status: str
    amount_cents: int
    currency: str
    customer_ref: Optional[str] = None


class PaymentAttemptOut(BaseModel):
    attempt_id: str
    status: str
    idempotency_key: str
    provider_payment_id: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str


class OutboxEventSummary(BaseModel):
    id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    created_at: str
    published_at: Optional[str] = None


class InvoiceDetailOut(BaseModel):
    invoice_id: str
    status: str
    amount_cents: int
    currency: str
    customer_ref: Optional[str] = None

    attempts: List[PaymentAttemptOut]
    outbox_events: List[OutboxEventSummary]
