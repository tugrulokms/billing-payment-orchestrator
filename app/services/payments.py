import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.infra.models import Invoice, PaymentAttempt
from app.services.outbox import enqueue_event


def _provider_payment_id() -> str:
    return f"pp_{uuid.uuid4().hex[:18]}"


def pay_invoice(db: Session, invoice_id: str, idempotency_key: str) -> PaymentAttempt:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="idempotency_key_required")

    # Row-lock invoice to avoid concurrent pay attempts for the same invoice
    invoice = db.execute(
        select(Invoice).where(Invoice.id == invoice_id).with_for_update()
    ).scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="invoice_not_found")

    if invoice.status == "paid":
        raise HTTPException(status_code=409, detail="invoice_already_paid")

    # Idempotency: if same key already used for this invoice, return same attempt
    existing = db.query(PaymentAttempt).filter(
        PaymentAttempt.invoice_id == invoice_id,
        PaymentAttempt.idempotency_key == idempotency_key,
    ).one_or_none()
    if existing:
        return existing

    # If there is a pending attempt, you can choose either to block or return it.
    pending = db.query(PaymentAttempt).filter(
        PaymentAttempt.invoice_id == invoice_id,
        PaymentAttempt.status == "requires_action",
    ).order_by(PaymentAttempt.created_at.desc()).first()
    if pending:
        # conservative behavior to avoid multiple in-flight provider payments
        raise HTTPException(
            status_code=409,
            detail="invoice_has_pending_attempt"
        )

    attempt = PaymentAttempt(
        invoice_id=invoice_id,
        idempotency_key=idempotency_key,
        status="requires_action",
        provider_payment_id=_provider_payment_id(),
    )
    db.add(attempt)

    # Ensure attempt.id is generated BEFORE writing outbox payload
    db.flush()

    enqueue_event(
        db,
        event_type="payment_attempt_created",
        aggregate_type="invoice",
        aggregate_id=invoice_id,
        payload={
            "invoice_id": invoice_id,
            "attempt_id": attempt.id,  # note: will be populated after flush
            "provider_payment_id": attempt.provider_payment_id,
            "amount_cents": invoice.amount_cents,
            "currency": invoice.currency,
        },
    )

    return attempt


def handle_provider_webhook(
    db: Session,
    provider_payment_id: str,
    result: str,
    provider_event_id: str,
    error_code: str | None,
    error_message: str | None,
):
    # Idempotent webhook handling:
    attempt = db.query(PaymentAttempt).filter(
        PaymentAttempt.provider_payment_id == provider_payment_id
    ).one_or_none()

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="attempt_not_found_for_provider_payment_id"
        )

    # If we already processed this provider event id, ignore
    if attempt.provider_event_id_last == provider_event_id:
        return attempt

    # If already terminal, ignore (idempotency for duplicates/out-of-order)
    if attempt.status in ("succeeded", "failed"):
        attempt.provider_event_id_last = provider_event_id
        return attempt

    invoice = db.get(Invoice, attempt.invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="invoice_not_found")

    if result == "succeeded":
        attempt.status = "succeeded"
        invoice.status = "paid"

        enqueue_event(
            db,
            event_type="payment_attempt_succeeded",
            aggregate_type="invoice",
            aggregate_id=invoice.id,
            payload={
                "invoice_id": invoice.id,
                "attempt_id": attempt.id,
                "provider_payment_id": provider_payment_id
            },
        )
        enqueue_event(
            db,
            event_type="invoice_paid",
            aggregate_type="invoice",
            aggregate_id=invoice.id,
            payload={
                "invoice_id": invoice.id,
                "amount_cents": invoice.amount_cents,
                "currency": invoice.currency
            },
        )
    else:
        attempt.status = "failed"
        attempt.error_code = error_code
        attempt.error_message = error_message

        enqueue_event(
            db,
            event_type="payment_attempt_failed",
            aggregate_type="invoice",
            aggregate_id=invoice.id,
            payload={
                "invoice_id": invoice.id,
                "attempt_id": attempt.id,
                "provider_payment_id": provider_payment_id,
                "error_code": error_code,
            },
        )

    attempt.provider_event_id_last = provider_event_id
    return attempt
