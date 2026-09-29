import asyncio, json, uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Job

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/jobs/{job_id}")
async def job_updates(websocket: WebSocket, job_id: uuid.UUID):
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()

    if not job:
        await websocket.send_json({"error": "Job not found"})
        await websocket.close(code=1008)
        return

    await websocket.send_json({
        "job_id": str(job.id),
        "status": job.status,
        "attempts": job.attempts,
        "result": job.result,
        "error": job.error,
    })

    client = Redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    channel = f"jobs:{job_id}"

    try:
        await pubsub.subscribe(channel)
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
            if message and message.get("data"):
                data = json.loads(message["data"])
                await websocket.send_json(data)
                if data.get("status") in {"completed", "failed"}:
                    break
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await client.aclose()
