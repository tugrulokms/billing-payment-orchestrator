from sqlalchemy import text

def test_pay_same_idempotency_key_returns_same_attempt(client, db):
    # create invoice
    r = client.post(
        "/invoices",
        json={
            "amount_cents": 1999,
            "currency": "EUR",
            "customer_ref": "cust_123"
        }
    )
    assert r.status_code == 200
    invoice_id = r.json()["invoice_id"]

    headers = {"Idempotency-Key": "11111111-1111-1111-1111-111111111111"}

    r1 = client.post(
        f"/invoices/{invoice_id}/pay",
        headers=headers,
        json={
            "payment_method": "mock_card"
        }
    )
    assert r1.status_code == 202
    a1 = r1.json()["attempt_id"]

    r2 = client.post(
        f"/invoices/{invoice_id}/pay",
        headers=headers,
        json={
            "payment_method": "mock_card"
        }
    )
    assert r2.status_code == 202
    a2 = r2.json()["attempt_id"]

    assert a1 == a2

    # ensure only one row exists in payment_attempts
    count = db.execute(text("SELECT COUNT(*) FROM payment_attempts")).scalar_one()
    assert count == 1
