import logging
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .agents.base import AgentBase
from .models import ConversationState, ConversationStatus, Event, EventSource
from .pub_sub import PubSub

logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    id: UUID = field(default_factory=uuid4)
    state: ConversationState = field(default_factory=ConversationState)
    agent: AgentBase = field(default_factory=AgentBase)
    _pubsub: PubSub = field(default_factory=PubSub)

    def send_message(self, text: str) -> None:
        event = Event(content=text, source=EventSource.USER)
        self._state_safe_append(event)
        logger.info("User: %s", text)

    def run(self) -> None:
        if self.state.status == ConversationStatus.RUNNING:
            logger.warning("Already running")
            return
        self.state.status = ConversationStatus.RUNNING
        self._publish_state()

        try:
            while self.state.status == ConversationStatus.RUNNING:
                output = self.agent.step()
                if output:
                    event = Event(content=output, source=EventSource.AGENT)
                    self._state_safe_append(event)
                    logger.info("Agent: %s", output)
                else:
                    self.state.status = ConversationStatus.FINISHED
                    break
        except Exception:
            logger.exception("Run failed")
            self.state.status = ConversationStatus.ERROR

        self._publish_state()

    def pause(self) -> None:
        if self.state.status == ConversationStatus.RUNNING:
            self.state.status = ConversationStatus.PAUSED
            self._publish_state()

    def _state_safe_append(self, event: Event) -> None:
        self.state.events.append(event)
        asyncio_run(self._pubsub.publish(event))

    def _publish_state(self) -> None:
        event = Event(
            content=f"status:{self.state.status.value}",
            source=EventSource.SYSTEM,
        )
        asyncio_run(self._pubsub.publish(event))


def asyncio_run(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, loop)
            return
    except RuntimeError:
        pass
    asyncio.run(coro)
