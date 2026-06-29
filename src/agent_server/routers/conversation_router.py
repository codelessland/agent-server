from uuid import UUID

from fastapi import APIRouter, Depends, Request

from ..dependencies import get_event_service
from ..event_service import EventService
from ..models import StartConversationRequest

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.post("")
def create_conversation(
    request: StartConversationRequest,
    req: Request,
) -> dict:
    from ..event_service import EventService

    svc = EventService()
    svc.conversation.agent.name = request.agent_config.get("name", "echo")
    services: dict[UUID, EventService] = getattr(req.app.state, "event_services", {})
    services[svc.conversation.id] = svc
    req.app.state.event_services = services
    return {"id": str(svc.conversation.id)}


@router.post("/{conversation_id}/run")
async def run_conversation(
    conversation_id: UUID,
    event_service: EventService = Depends(get_event_service),
) -> dict:
    await event_service.run()
    return {"status": "started"}


@router.post("/{conversation_id}/pause")
async def pause_conversation(
    conversation_id: UUID,
    event_service: EventService = Depends(get_event_service),
) -> dict:
    await event_service.pause()
    return {"status": "paused"}


@router.get("")
def list_conversations(req: Request) -> list[str]:
    services: dict[UUID, EventService] = getattr(req.app.state, "event_services", {})
    return [str(svc.conversation.id) for svc in services.values()]


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: UUID,
    event_service: EventService = Depends(get_event_service),
) -> dict:
    return {
        "id": str(event_service.conversation.id),
        "status": event_service.conversation.state.status.value,
    }
