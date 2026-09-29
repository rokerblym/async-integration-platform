from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.webhooks import router as webhooks_router
from app.routers.jobs import router as jobs_router
from app.routers.events import router as events_router
from app.routers.ws import router as ws_router

app = FastAPI(
    title="Async Integration Platform",
    version="1.0.0",
    description="Event-driven backend with idempotent webhooks, PostgreSQL, Celery/Redis, retries and WebSockets.",
)
app.include_router(health_router)
app.include_router(webhooks_router)
app.include_router(jobs_router)
app.include_router(events_router)
app.include_router(ws_router)
