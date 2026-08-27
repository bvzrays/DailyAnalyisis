from __future__ import annotations

from dataclasses import dataclass


@dataclass
class File:
    file: str = ""
    name: str = ""


__all__ = ["File"]
