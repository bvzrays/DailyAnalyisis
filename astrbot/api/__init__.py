from __future__ import annotations

from collections.abc import Callable

from gsuid_core.logger import logger


class AstrBotConfig(dict):
    """Dict-compatible configuration with a persistence callback."""

    def __init__(self, *args, save_callback: Callable[[dict], None] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._save_callback = save_callback

    def save_config(self) -> None:
        if self._save_callback is not None:
            self._save_callback(dict(self))


__all__ = ["AstrBotConfig", "logger"]
