import json
from sqlalchemy import text

def test_outbox_event_contains_non_null_attempt_id(client, db):
    # create invoice
    r = client.post(
        "/invoices",
        json={
            "amount_cents": 2500,
            "currency": "EUR",
            "customer_ref": "cust_456"
        }
    )
    assert r.status_code == 200
    invoice_id = r.json()["invoice_id"]

    headers = {"Idempotency-Key": "22222222-2222-2222-2222-222222222222"}
    r2 = client.post(
        f"/invoices/{invoice_id}/pay",
        headers=headers,
        json={"payment_method": "mock_card"}
    )
    assert r2.status_code == 202
    attempt_id = r2.json()["attempt_id"]

    # Outbox'ta payment_attempt_created olmalı
    row = db.execute(
        text("""
            SELECT payload
            FROM outbox_events
            WHERE event_type = 'payment_attempt_created'
            ORDER BY created_at DESC
            LIMIT 1
        """)
    ).first()

    assert row is not None, "Expected outbox event payment_attempt_created"

    payload = json.loads(row[0])  # MariaDB JSON column returns dict-like via SQLAlchemy driver
    print(payload.get("invoice_id"))
    assert payload.get("invoice_id") == invoice_id
    assert payload.get("attempt_id") is not None, "attempt_id should never be null (flush must happen before enqueue)"
    assert payload.get("attempt_id") == attempt_id
