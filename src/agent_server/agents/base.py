from dataclasses import dataclass, field
from typing import Callable


@dataclass
class AgentBase:
    name: str = "echo"
    on_event: Callable | None = field(default=None, init=False)

    def step(self) -> str | None:
        return None
