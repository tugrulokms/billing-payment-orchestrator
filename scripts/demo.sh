#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
IDEMPOTENCY_KEY="${IDEMPOTENCY_KEY:-11111111-1111-1111-1111-111111111111}"

echo "==> Creating invoice"
INV_JSON=$(curl -s -X POST "$BASE_URL/invoices" \
  -H "Content-Type: application/json" \
  -d '{"amount_cents":1999,"currency":"EUR","customer_ref":"cust_demo"}')

INVOICE_ID=$(echo "$INV_JSON" | python -c 'import sys,json; print(json.load(sys.stdin)["invoice_id"])')
echo "Invoice: $INVOICE_ID"

echo "==> Paying invoice (idempotency key: $IDEMPOTENCY_KEY)"
PAY_JSON=$(curl -s -X POST "$BASE_URL/invoices/$INVOICE_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{"payment_method":"mock_card"}')

PROVIDER_PAYMENT_ID=$(echo "$PAY_JSON" | python -c 'import sys,json; print(json.load(sys.stdin)["provider_payment_id"])')
ATTEMPT_ID=$(echo "$PAY_JSON" | python -c 'import sys,json; print(json.load(sys.stdin)["attempt_id"])')
echo "Attempt: $ATTEMPT_ID"
echo "Provider payment id: $PROVIDER_PAYMENT_ID"

echo "==> Simulating provider webhook success"
curl -s -X POST "$BASE_URL/webhooks/payment-provider" \
  -H "Content-Type: application/json" \
  -d "{\"provider_payment_id\":\"$PROVIDER_PAYMENT_ID\",\"result\":\"succeeded\",\"provider_event_id\":\"evt_1\"}" >/dev/null

echo "==> Publishing outbox events"
curl -s -X POST "$BASE_URL/internal/outbox/publish?limit=50" >/dev/null

echo "==> Fetching invoice details"
curl -s "$BASE_URL/invoices/$INVOICE_ID" | python -m json.tool

echo "Demo flow completed."
