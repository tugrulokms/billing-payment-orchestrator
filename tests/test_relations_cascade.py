from sqlalchemy import text

def test_deleting_invoice_cascades_payment_attempts(client, db):
    # create invoice
    r = client.post("/invoices", json={"amount_cents": 1000, "currency": "EUR"})
    invoice_id = r.json()["invoice_id"]

    # pay invoice -> creates attempt
    client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"Idempotency-Key": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
        json={"payment_method": "mock_card"},
    )

    # sanity: attempt exists
    attempt_count = db.execute(
        text("SELECT COUNT(*) FROM payment_attempts WHERE invoice_id = :iid"),
        {"iid": invoice_id},
    ).scalar_one()
    assert attempt_count == 1

    # delete invoice (direct SQL for clarity)
    db.execute(text("DELETE FROM invoices WHERE id = :iid"), {"iid": invoice_id})
    db.commit()

    # attempts should be gone
    attempt_count2 = db.execute(
        text("SELECT COUNT(*) FROM payment_attempts WHERE invoice_id = :iid"),
        {"iid": invoice_id},
    ).scalar_one()
    assert attempt_count2 == 0
