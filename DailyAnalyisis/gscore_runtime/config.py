from __future__ import annotations

from pathlib import Path
from collections.abc import Callable


class PluginConfig(dict):
    """Dictionary configuration that persists through a callback."""

    def __init__(
        self,
        *args,
        save_callback: Callable[[dict], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._save_callback = save_callback

    def save_config(self) -> None:
        if self._save_callback is not None:
            self._save_callback(dict(self))


class PluginPaths:
    _data_dir: Path = Path.cwd() / "data" / "DailyAnalyisis"

    @classmethod
    def set_data_dir(cls, path: Path) -> None:
        cls._data_dir = path
        cls._data_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_data_dir(cls, plugin_name: str = "") -> Path:
        cls._data_dir.mkdir(parents=True, exist_ok=True)
        return cls._data_dir


__all__ = ["PluginConfig", "PluginPaths"]
