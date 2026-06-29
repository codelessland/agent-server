from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from .event_service import EventService


def get_event_service(
    conversation_id: UUID,
    request: Request,
) -> EventService:
    services: dict[UUID, EventService] = getattr(
        request.app.state, "event_services", {}
    )
    service = services.get(conversation_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return service
