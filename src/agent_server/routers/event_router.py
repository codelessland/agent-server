from uuid import UUID

from fastapi import APIRouter, Depends

from ..dependencies import get_event_service
from ..event_service import EventService
from ..models import Event, EventSource, SendMessageRequest

router = APIRouter(
    prefix="/api/conversations/{conversation_id}/events", tags=["Events"]
)


@router.post("")
async def send_message(
    request: SendMessageRequest,
    event_service: EventService = Depends(get_event_service),
) -> dict:
    await event_service.send_message(request.content, run=True)
    return {"success": True}


@router.get("")
async def get_events(
    event_service: EventService = Depends(get_event_service),
) -> list[dict]:
    events = await event_service.get_events()
    return [e.model_dump() for e in events]
