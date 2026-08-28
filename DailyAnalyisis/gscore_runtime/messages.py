from __future__ import annotations

from typing import Any
from dataclasses import field, dataclass


@dataclass
class Plain:
    text: str
    type: str = "Plain"


@dataclass
class Image:
    file: str = ""
    url: str = ""
    type: str = "Image"

    @classmethod
    def fromFileSystem(cls, path: str, **_: object) -> "Image":
        return cls(file=str(path))

    @classmethod
    def fromURL(cls, url: str, **_: object) -> "Image":
        return cls(url=str(url))

    @classmethod
    def fromBase64(cls, base64: str, **_: object) -> "Image":
        return cls(url=f"base64://{base64}")


@dataclass
class Node:
    uin: str = ""
    name: str = ""
    content: list[object] = field(default_factory=list)
    type: str = "Node"


@dataclass
class Nodes:
    nodes: list[Node] = field(default_factory=list)
    type: str = "Nodes"


@dataclass
class File:
    file: str = ""
    name: str = ""


class PluginMessageEvent:
    """Base type for the GsCore event bridge."""

    message_obj: Any
    platform_meta: Any = None
    unified_msg_origin: str

    def get_group_id(self) -> str | None:
        raise NotImplementedError

    def get_sender_id(self) -> str:
        raise NotImplementedError

    def get_sender_name(self) -> str:
        raise NotImplementedError

    def get_platform_id(self) -> str:
        raise NotImplementedError

    def get_platform_name(self) -> str:
        raise NotImplementedError

    def get_self_id(self) -> str:
        raise NotImplementedError

    def should_call_llm(self, enabled: bool) -> None:
        raise NotImplementedError

    def plain_result(self, text: str) -> object:
        raise NotImplementedError

    def chain_result(self, chain: list[object]) -> object:
        raise NotImplementedError


__all__ = ["File", "Image", "Node", "Nodes", "Plain", "PluginMessageEvent"]
