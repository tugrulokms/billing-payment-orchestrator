from pydantic import BaseModel, Field
from typing import Optional, Literal


class PayInvoiceRequest(BaseModel):
    payment_method: str = "mock_card"


class PayInvoiceResponse(BaseModel):
    attempt_id: str
    status: str
    provider_payment_id: str


class ProviderWebhookRequest(BaseModel):
    provider_payment_id: str
    result: Literal["succeeded", "failed"]
    provider_event_id: str = Field(default_factory=lambda: "evt_mock")
    error_code: Optional[str] = None
    error_message: Optional[str] = None
