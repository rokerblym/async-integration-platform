import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import IntegrationEvent
from app.schemas.events import EventResponse

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    event = (await db.execute(
        select(IntegrationEvent).where(IntegrationEvent.id == event_id)
    )).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
