# Starting with TSTTCPW

from dataclasses import dataclass
from typing import Protocol


@dataclass
class DataEvent:
    event_type: str
    event_data: object


class AgentContext(Protocol):
    """Protocol for agent contexts. Different context implementations
    might be used for testing or distributed operations."""

    def notify(self, event: DataEvent) -> None:
        ...

    def log(self, level: int, message: str) -> None:
        ...


class DataAgent(Protocol):
    """Protocol for a data agent."""

    def handle_event(self, event: DataEvent) -> None:
        ...
