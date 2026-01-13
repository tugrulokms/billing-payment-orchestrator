from sqlalchemy import text

def test_webhook_duplicate_event_id_is_idempotent(client, db):
    # create invoice
    r = client.post(
        "/invoices",
        json={
            "amount_cents": 3000,
            "currency": "EUR",
            "customer_ref": "cust_789"
        }
    )
    invoice_id = r.json()["invoice_id"]

    # pay -> get provider_payment_id
    headers = {"Idempotency-Key": "33333333-3333-3333-3333-333333333333"}
    pay = client.post(
        f"/invoices/{invoice_id}/pay",
        headers=headers,
        json={"payment_method": "mock_card"}
    )
    assert pay.status_code == 202
    provider_payment_id = pay.json()["provider_payment_id"]

    # webhook success
    evt = {
        "provider_payment_id": provider_payment_id,
        "result": "succeeded", "provider_event_id": "evt_1"
    }
    w1 = client.post("/webhooks/payment-provider", json=evt)
    assert w1.status_code == 200

    # duplicate webhook with same provider_event_id -> should be idempotent
    w2 = client.post("/webhooks/payment-provider", json=evt)
    assert w2.status_code == 200

    # invoice should be paid
    inv = client.get(f"/invoices/{invoice_id}")
    assert inv.status_code == 200
    assert inv.json()["status"] == "paid"

    data = inv.json()
    assert len(data["attempts"]) >= 1

    # ensure only one "invoice_paid" outbox event (or at least not duplicated)
    count = db.execute(
        text("""
             SELECT COUNT(*)
             FROM outbox_events
             WHERE event_type = 'invoice_paid'
             AND JSON_EXTRACT(payload,'$.invoice_id') = :iid
             """),
        {"iid": invoice_id},
    ).scalar_one()

    assert count == 1
