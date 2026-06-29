from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ConversationStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    ERROR = "error"


class EventSource(StrEnum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class Event:
    id: str = field(default_factory=lambda: uuid4().hex)
    source: EventSource = EventSource.SYSTEM
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    content: str = ""

    def model_dump(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "timestamp": self.timestamp,
            "content": self.content,
        }


@dataclass
class ConversationState:
    status: ConversationStatus = ConversationStatus.IDLE
    events: list[Event] = field(default_factory=list)


@dataclass
class Conversation:
    id: UUID
    state: ConversationState = field(default_factory=ConversationState)
    agent_config: dict = field(default_factory=dict)


@dataclass
class SendMessageRequest:
    content: str


@dataclass
class StartConversationRequest:
    agent_config: dict = field(default_factory=dict)
