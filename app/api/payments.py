from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.infra.db import get_db
from app.schemas.payment import PayInvoiceRequest, PayInvoiceResponse, ProviderWebhookRequest
from app.services.payments import pay_invoice, handle_provider_webhook
from app.services.outbox import publish_pending

router = APIRouter(tags=["payments"])


@router.post("/invoices/{invoice_id}/pay", response_model=PayInvoiceResponse, status_code=202)
def pay(invoice_id: str, payload: PayInvoiceRequest, db: Session = Depends(get_db), idempotency_key: str = Header(default="")):
    # Use-case + transaction boundary in the endpoint
    attempt = pay_invoice(
        db,
        invoice_id=invoice_id,
        idempotency_key=idempotency_key
    )

    # Ensure attempt.id exists for event payloads that may rely on it
    # db.flush()

    db.commit()
    db.refresh(attempt)

    return PayInvoiceResponse(
        attempt_id=attempt.id,
        status=attempt.status,
        provider_payment_id=attempt.provider_payment_id,
    )


@router.post("/webhooks/payment-provider")
def webhook(payload: ProviderWebhookRequest, db: Session = Depends(get_db)):
    attempt = handle_provider_webhook(
        db,
        provider_payment_id=payload.provider_payment_id,
        result=payload.result,
        provider_event_id=payload.provider_event_id,
        error_code=payload.error_code,
        error_message=payload.error_message,
    )
    db.commit()
    return {
        "status": "ok",
        "attempt_id": attempt.id,
        "attempt_status": attempt.status
    }


@router.post("/internal/outbox/publish")
def publish_outbox(limit: int = 50, db: Session = Depends(get_db)):
    count = publish_pending(db, limit=limit)
    db.commit()
    return {"published": count}
