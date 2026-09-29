import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class OrderWebhook(BaseModel):
    order_id: str = Field(min_length=1, max_length=100)
    status: str = Field(min_length=1, max_length=50)
    amount: float = Field(ge=0)
    currency: str = Field(default="KZT", min_length=3, max_length=3)
    customer_id: str | None = Field(default=None, max_length=100)

class EventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    idempotency_key: str
    payload: dict
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class JobResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    status: str
    attempts: int
    result: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WebhookAccepted(BaseModel):
    event: EventResponse
    job: JobResponse
    duplicate: bool = False
