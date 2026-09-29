import json, uuid
import httpx, redis
from celery import Task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config import settings
from app.models import IntegrationEvent, Job
from app.worker.celery_app import celery_app

sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)

def publish(job_id: str, payload: dict) -> None:
    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        client.publish(f"jobs:{job_id}", json.dumps(payload, default=str))
    finally:
        client.close()

def set_state(session: Session, job: Job, event: IntegrationEvent, status: str, *, result=None, error=None):
    job.status = status
    event.status = status
    job.result = result
    job.error = error
    session.commit()
    session.refresh(job)
    publish(str(job.id), {
        "job_id": str(job.id),
        "status": job.status,
        "attempts": job.attempts,
        "result": job.result,
        "error": job.error,
    })

@celery_app.task(bind=True, max_retries=3)
def process_event(self: Task, job_id: str):
    job_uuid = uuid.UUID(job_id)
    with Session(sync_engine) as session:
        job = session.scalar(select(Job).where(Job.id == job_uuid))
        if not job:
            return {"error": "job_not_found"}
        event = session.scalar(select(IntegrationEvent).where(IntegrationEvent.id == job.event_id))
        if not event:
            return {"error": "event_not_found"}

        job.attempts += 1
        set_state(session, job, event, "processing")

        try:
            if settings.downstream_url:
                with httpx.Client(timeout=8.0) as client:
                    response = client.post(settings.downstream_url, json={
                        "event_id": str(event.id),
                        "type": event.event_type,
                        "payload": event.payload,
                    })
                    response.raise_for_status()
                    downstream_result = {
                        "status_code": response.status_code,
                        "body": response.text[:1000],
                    }
            else:
                downstream_result = {
                    "mode": "demo",
                    "message": "Event processed without external downstream service",
                    "order_id": event.payload.get("order_id"),
                }

            set_state(session, job, event, "completed", result=downstream_result)
            return downstream_result

        except httpx.HTTPError as exc:
            if self.request.retries < self.max_retries:
                set_state(session, job, event, "retrying", error=str(exc))
                raise self.retry(exc=exc, countdown=min(2 ** (self.request.retries + 1), 30))
            set_state(session, job, event, "failed", error=str(exc))
            raise
