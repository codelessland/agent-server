import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

Subscriber = Callable[["Event"], None]


@dataclass
class PubSub:
    _subscribers: dict[UUID, Subscriber] = field(default_factory=dict)

    def subscribe(self, subscriber: Subscriber) -> UUID:
        sid = uuid4()
        self._subscribers[sid] = subscriber
        return sid

    def unsubscribe(self, sid: UUID) -> bool:
        return self._subscribers.pop(sid, None) is not None

    async def publish(self, event: "Event") -> None:
        subs = list(self._subscribers.items())
        if not subs:
            return
        await asyncio.gather(
            *[self._safe_notify(sid, sub, event) for sid, sub in subs]
        )

    async def _safe_notify(
        self, sid: UUID, subscriber: Subscriber, event: "Event"
    ) -> None:
        try:
            await subscriber(event)
        except Exception:
            logger.exception("Subscriber %s raised", sid)
