from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Config:
    session_api_keys: set[str] = field(default_factory=set)
    host: str = "127.0.0.1"
    port: int = 8000
