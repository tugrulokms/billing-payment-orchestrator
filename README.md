# Billing Demo – Invoice Payment Orchestrator

This project is a minimal backend service that demonstrates how to safely orchestrate invoice payments in a real-world payment system.

Instead of focusing on full payment provider integrations or UI, the demo models the **most critical backend challenges** in billing systems:
- idempotent payment attempts
- safe retry handling
- duplicate / out-of-order webhook processing
- transactional consistency between database state and emitted events

The goal is to showcase **backend engineering decisions**, not a production-ready payment gateway.

---

## What this service does

At a high level, the service:
1. Creates invoices that can be paid
2. Accepts payment requests in an idempotent way
3. Finalizes payments asynchronously via provider webhooks
4. Records domain events using the Outbox pattern

This mirrors how real payment systems protect against:
- double charges
- network retries
- duplicated provider callbacks
- inconsistent state vs. event publishing

---

## Core flow

1. **Create invoice**
   - An invoice is created with status `open`

2. **Pay invoice**
   - Client calls `POST /invoices/{id}/pay`
   - An `Idempotency-Key` header is required
   - A single `payment_attempt` is created even if the request is retried
   - Invoice row is locked to prevent concurrent payment attempts

3. **Provider webhook**
   - A simulated payment provider sends a webhook (`succeeded` / `failed`)
   - Webhook handling is idempotent and safe for duplicate events
   - Invoice state is updated accordingly

4. **Outbox events**
   - All important state changes are written to an outbox table
   - Events can later be published to Kafka / RabbitMQ
   - Database state and events remain consistent

---

## API overview

### Create invoice
    POST /invoices

### Pay invoice (idempotent)
    POST /invoices/{invoice_id}/pay
    Headers:
    Idempotency-Key: <uuid>

### Provider webhook (simulated)
    POST /webhooks/payment-provider

### Invoice details (debug/demo)
    GET /invoices/{invoice_id}
    Returns:
    - invoice state
    - payment attempts
    - recent outbox events

---

## Key design decisions

### Idempotency at the domain level
Idempotency is handled at the **payment attempt** level rather than at the HTTP layer.
This ensures retries never create duplicate payment attempts or double charges.

### Transaction boundaries and locking
- Invoice rows are locked during payment initiation
- Prevents multiple concurrent in-flight payment attempts for the same invoice

### Webhook idempotency
- Provider webhooks may be duplicated or arrive out of order
- Each webhook is processed safely without corrupting state

### Outbox pattern
- Domain events are written within the same database transaction
- Guarantees consistency between state changes and emitted events
- Prepares the system for Kafka / RabbitMQ integration

---

## Trade-offs & non-goals

This demo intentionally does **not** include:
- real payment provider SDKs
- authentication / authorization
- frontend or UI
- Kafka / RabbitMQ setup

These were excluded to keep the scope focused on backend correctness and clarity.
The integration points for these concerns are clearly defined.

---

## Tech stack

- **FastAPI**
- **SQLAlchemy + Alembic**
- **MariaDB**
- **Docker Compose**
- **pytest**

---

## How to run
    - make up
    - make migrate

API will be available at:
    http://localhost:8000

Swagger UI:
    http://localhost:8000/docs
    