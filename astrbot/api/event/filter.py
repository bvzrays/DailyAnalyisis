from __future__ import annotations

from enum import IntEnum


class PermissionType(IntEnum):
    ADMIN = 3
    MEMBER = 6


__all__ = ["PermissionType"]
