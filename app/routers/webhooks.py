from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.idempotency import payload_fingerprint
from app.core.signatures import verify_signature
from app.database import get_db
from app.models import IntegrationEvent, Job
from app.schemas.events import OrderWebhook, WebhookAccepted
from app.worker.tasks import process_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/orders", response_model=WebhookAccepted, status_code=status.HTTP_202_ACCEPTED)
async def receive_order_webhook(
    request: Request,
    payload: OrderWebhook,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_webhook_signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
):
    body = await request.body()
    if x_webhook_signature and not verify_signature(settings.webhook_secret, body, x_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload_dict = payload.model_dump()
    key = idempotency_key or payload_fingerprint("order.updated", payload_dict)

    existing = (await db.execute(
        select(IntegrationEvent).where(IntegrationEvent.idempotency_key == key)
    )).scalar_one_or_none()

    if existing:
        job = (await db.execute(select(Job).where(Job.event_id == existing.id))).scalar_one()
        return WebhookAccepted(event=existing, job=job, duplicate=True)

    event = IntegrationEvent(
        event_type="order.updated",
        idempotency_key=key,
        payload=payload_dict,
        status="queued",
    )
    db.add(event)
    await db.flush()

    job = Job(event_id=event.id, status="queued")
    db.add(job)
    await db.commit()
    await db.refresh(event)
    await db.refresh(job)

    try:
        process_event.delay(str(job.id))
    except Exception as exc:
        job.status = "dispatch_failed"
        job.error = f"Could not dispatch task: {exc}"
        event.status = "dispatch_failed"
        await db.commit()
        await db.refresh(event)
        await db.refresh(job)

    return WebhookAccepted(event=event, job=job)
