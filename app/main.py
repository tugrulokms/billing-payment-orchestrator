from fastapi import FastAPI
from sqlalchemy import text

from app.infra.db import engine
from app.api.invoices import router as invoices_router
from app.api.payments import router as payments_router

app = FastAPI(title="Billing Demo - Payment Orchestrator")
app.include_router(invoices_router)
app.include_router(payments_router)


@app.get("/health")
def health():
    # DB connectivity check
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
