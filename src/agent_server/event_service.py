import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from uuid import UUID

from .conversation import Conversation
from .models import ConversationStatus, Event
from .pub_sub import PubSub, Subscriber

logger = logging.getLogger(__name__)


@dataclass
class EventService:
    conversation: Conversation = field(default_factory=Conversation)
    _pubsub: PubSub = field(default_factory=PubSub)
    _run_task: asyncio.Task | None = field(default=None, init=False)
    _run_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self):
        self.conversation._pubsub = self._pubsub

    async def send_message(self, text: str, run: bool = False) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.conversation.send_message, text)
        if run:
            await self.run()

    async def run(self) -> None:
        if not self.conversation:
            raise ValueError("inactive_service")
        async with self._run_lock:
            if self.conversation.state.status == ConversationStatus.RUNNING:
                raise ValueError("conversation_already_running")
            self._run_task = asyncio.create_task(self._run_and_publish())

    async def _run_and_publish(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self.conversation.run)
        except Exception:
            logger.exception("Run failed")
            self.conversation.state.status = ConversationStatus.ERROR
        finally:
            self._run_task = None
            await self._publish_state_update()

    async def pause(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.conversation.pause)
        await self._publish_state_update()

    async def subscribe(self, subscriber: Subscriber) -> UUID:
        return self._pubsub.subscribe(subscriber)

    def unsubscribe(self, sid: UUID) -> bool:
        return self._pubsub.unsubscribe(sid)

    async def get_events(self) -> list[Event]:
        return list(self.conversation.state.events)

    async def _publish_state_update(self) -> None:
        event = Event(
            content=f"status:{self.conversation.state.status.value}",
        )
        await self._pubsub.publish(event)

    async def close(self) -> None:
        if self._run_task and not self._run_task.done():
            self._run_task.cancel()
            with suppress(asyncio.CancelledError):
                await asyncio.wait_for(self._run_task, timeout=5.0)


from contextlib import suppress
