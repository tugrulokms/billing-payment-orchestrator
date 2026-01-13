from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infra.db import get_db
from app.infra.models import Invoice, PaymentAttempt, OutboxEvent
from app.schemas.invoice import InvoiceCreate, InvoiceOut, InvoiceDetailOut, PaymentAttemptOut, OutboxEventSummary

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceOut)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    inv = Invoice(
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        customer_ref=payload.customer_ref,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return InvoiceOut(
        invoice_id=inv.id,
        status=inv.status,
        amount_cents=inv.amount_cents,
        currency=inv.currency,
        customer_ref=inv.customer_ref,
    )


@router.get("/{invoice_id}", response_model=InvoiceDetailOut)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="invoice_not_found")
    
    attempts = (
        db.query(PaymentAttempt)
        .filter(PaymentAttempt.invoice_id == invoice_id)
        .order_by(PaymentAttempt.created_at.desc())
        .all()
    )

    # Outbox events for this invoice (last 10)
    outbox = (
        db.query(OutboxEvent)
        .filter(
            OutboxEvent.aggregate_type == "invoice",
            OutboxEvent.aggregate_id == invoice_id
        )
        .order_by(OutboxEvent.created_at.desc())
        .limit(10)
        .all()
    )

    return InvoiceDetailOut(
        invoice_id=inv.id,
        status=inv.status,
        amount_cents=inv.amount_cents,
        currency=inv.currency,
        customer_ref=inv.customer_ref,
        attempts=[
            PaymentAttemptOut(
                attempt_id=a.id,
                status=a.status,
                idempotency_key=a.idempotency_key,
                provider_payment_id=a.provider_payment_id,
                error_code=a.error_code,
                error_message=a.error_message,
                created_at=a.created_at.isoformat(),
            )
            for a in attempts
        ],
        outbox_events=[
            OutboxEventSummary(
                id=e.id,
                event_type=e.event_type,
                aggregate_type=e.aggregate_type,
                aggregate_id=e.aggregate_id,
                created_at=e.created_at.isoformat(),
                published_at=e.published_at.isoformat()
                if e.published_at else None,
            )
            for e in outbox
        ],
    )


@router.get("", response_model=list[InvoiceOut])
def list_invoices(limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(Invoice)
        .order_by(Invoice.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [
        InvoiceOut(
            invoice_id=i.id,
            status=i.status,
            amount_cents=i.amount_cents,
            currency=i.currency,
            customer_ref=i.customer_ref,
        )
        for i in rows
    ]
