from uid import Uid
from dataclasses import dataclass
from fastapi import WebSocket

@dataclass
class LogListener:
    socket: WebSocket
    machine: Uid | None
    tags: list[str]