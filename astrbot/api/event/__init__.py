from __future__ import annotations

from enum import Enum
from dataclasses import field, dataclass


class EventMessageType(Enum):
    GROUP_MESSAGE = "group"


class PlatformAdapterType(Enum):
    TELEGRAM = 1
    QQOFFICIAL = 2
    QQOFFICIAL_WEBHOOK = 4

    def __or__(self, other: "PlatformAdapterType") -> int:
        return self.value | other.value


def _decorator(*args, **kwargs):
    def wrap(func):
        return func

    return wrap


class _Filter:
    EventMessageType = EventMessageType
    PlatformAdapterType = PlatformAdapterType
    command = staticmethod(_decorator)
    permission_type = staticmethod(_decorator)
    event_message_type = staticmethod(_decorator)
    platform_adapter_type = staticmethod(_decorator)
    on_platform_loaded = staticmethod(_decorator)


filter = _Filter()


@dataclass
class MessageChain:
    chain: list[object] = field(default_factory=list)

    def __iter__(self):
        return iter(self.chain)


class AstrMessageEvent:
    """Runtime-populated event facade; concrete behavior lives in the plugin host."""


__all__ = ["AstrMessageEvent", "MessageChain", "filter"]
