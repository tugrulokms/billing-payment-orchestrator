from sqlalchemy import text

def test_webhook_success_updates_invoice_and_writes_outbox(client, db):
    # create invoice
    inv = client.post("/invoices", json={"amount_cents": 1999, "currency": "EUR"}).json()
    invoice_id = inv["invoice_id"]

    # pay -> get provider_payment_id
    pay = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"Idempotency-Key": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"},
        json={"payment_method": "mock_card"},
    ).json()
    pp_id = pay["provider_payment_id"]

    # webhook success
    r = client.post("/webhooks/payment-provider", json={
        "provider_payment_id": pp_id,
        "result": "succeeded",
        "provider_event_id": "evt_atomic_1",
    })
    assert r.status_code == 200

    # invoice status paid
    inv_detail = client.get(f"/invoices/{invoice_id}").json()
    assert inv_detail["status"] == "paid"

    # outbox has invoice_paid exactly once
    cnt = db.execute(
        text("SELECT COUNT(*) FROM outbox_events WHERE event_type='invoice_paid' AND aggregate_id=:iid"),
        {"iid": invoice_id},
    ).scalar_one()
    assert cnt == 1
