import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..event_service import EventService
from ..models import Event
from ..pub_sub import Subscriber

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sockets", tags=["WebSockets"])


@router.websocket("/conversations/{conversation_id}/events")
async def events_socket(conversation_id: UUID, ws: WebSocket):
    await ws.accept()

    from fastapi import Request
    from fastapi.routing import APIRouter as _AR

    request: Request = ws.scope.get("ASGI").__self__.scope.get("app").state
    services: dict[UUID, EventService] = getattr(request, "event_services", {})
    svc = services.get(conversation_id)
    if svc is None:
        await ws.close(code=4004, reason="Conversation not found")
        return

    async def subscriber(event: Event) -> None:
        try:
            await ws.send_json(event.model_dump())
        except Exception:
            pass

    sid = svc.subscribe(subscriber)

    try:
        while True:
            data = await ws.receive_json()
            if isinstance(data, dict) and data.get("type") == "auth":
                continue
            content = data.get("content", "") if isinstance(data, dict) else str(data)
            await svc.send_message(content, run=True)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", conversation_id)
    except Exception:
        logger.exception("WebSocket error")
    finally:
        svc.unsubscribe(sid)
