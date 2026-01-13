import pytest

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.infra.models import PaymentAttempt

def test_unique_invoice_idempotency_constraint_enforced(db):
    invoice_id = "00000000-0000-0000-0000-000000000001"

    # Create invoice row directly
    db.execute(
        text(
            "INSERT INTO invoices (id, status, amount_cents, currency, created_at, updated_at) "
            "VALUES (:id, 'open', 1000, 'EUR', NOW(), NOW())"
        ),
        {"id": invoice_id},
    )
    db.commit()

    a1 = PaymentAttempt(
        invoice_id=invoice_id,
        idempotency_key="same-key",
        status="requires_action",
        provider_payment_id="pp_unique_1",
    )
    db.add(a1)
    db.commit()

    a2 = PaymentAttempt(
        invoice_id=invoice_id,
        idempotency_key="same-key",
        status="requires_action",
        provider_payment_id="pp_unique_2",
    )
    db.add(a2)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()
