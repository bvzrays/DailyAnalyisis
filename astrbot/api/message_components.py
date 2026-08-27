from __future__ import annotations

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


__all__ = ["Image", "Node", "Nodes", "Plain"]
