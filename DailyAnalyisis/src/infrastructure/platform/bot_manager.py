from __future__ import annotations

from pathlib import Path

from .gscore_adapter import GsCorePlatformAdapter


class BotManager:
    def __init__(self, config_manager) -> None:
        self.config_manager = config_manager
        self._bot_instances: dict[str, object] = {}
        self._adapters: dict[str, GsCorePlatformAdapter] = {}
        self._bot_self_ids: list[str] = []
        self._context = None
        self._plugin_instance = None

    @property
    def _data_dir(self) -> Path:
        return Path(getattr(self._plugin_instance, "plugin_data_dir", Path.cwd() / "data"))

    def set_context(self, context) -> None:
        self._context = context

    def set_plugin_instance(self, plugin_instance: object) -> None:
        self._plugin_instance = plugin_instance

    def register_gscore_event(self, bot, event):
        platform_id = str(event.WS_BOT_ID or event.real_bot_id or event.bot_id or "gscore")
        adapter = self._adapters.get(platform_id)
        if adapter is None:
            adapter = GsCorePlatformAdapter(platform_id, self._data_dir)
            self._adapters[platform_id] = adapter
        self._bot_instances[platform_id] = bot
        bot_self_id = str(event.bot_self_id or "")
        if bot_self_id and bot_self_id not in self._bot_self_ids:
            self._bot_self_ids.append(bot_self_id)
        return adapter

    async def archive_gscore_event(self, bot, event) -> None:
        adapter = self.register_gscore_event(bot, event)
        await adapter.record_event(bot, event)

    def update_from_event(self, event) -> None:
        bot = getattr(event, "gscore_bot", None)
        raw_event = getattr(event, "gscore_event", None)
        if bot is not None and raw_event is not None:
            self.register_gscore_event(bot, raw_event)

    async def initialize_from_config(self) -> None:
        return None

    async def auto_discover_bot_instances(self) -> None:
        return None

    def get_adapter(self, platform_id: str | None = None):
        if platform_id and platform_id in self._adapters:
            return self._adapters[platform_id]
        if len(self._adapters) == 1:
            return next(iter(self._adapters.values()))
        if platform_id:
            lowered = str(platform_id).lower()
            for key, adapter in self._adapters.items():
                if key.lower() == lowered:
                    return adapter
        return next(iter(self._adapters.values()), None)

    def get_adapter_platform_id(self, adapter) -> str:
        return str(getattr(adapter, "platform_id", ""))

    def get_all_adapters(self) -> dict:
        return dict(self._adapters)

    def get_platform_ids(self) -> list[str]:
        return list(self._adapters)

    def get_platform_count(self) -> int:
        return len(self._adapters)

    def get_all_bot_instances(self) -> dict:
        return dict(self._bot_instances)

    def has_bot_instance(self) -> bool:
        return bool(self._bot_instances)

    def has_bot_self_id(self) -> bool:
        return bool(self._bot_self_ids)

    def is_ready_for_auto_analysis(self) -> bool:
        return bool(self._adapters)

    def set_bot_instance(self, bot_instance, platform_id=None, platform_name=None) -> None:
        if platform_id:
            self._bot_instances[str(platform_id)] = bot_instance

    def set_bot_self_ids(self, bot_self_ids) -> None:
        values = bot_self_ids if isinstance(bot_self_ids, list) else [bot_self_ids]
        self._bot_self_ids = [str(value) for value in values if value]

    def _detect_platform_name(self, bot_instance) -> str:
        return "gscore"

    def is_plugin_enabled(self, platform_id: str, plugin_name: str) -> bool:
        return True

    def get_status_info(self) -> dict[str, object]:
        return {
            "platforms": self.get_platform_ids(),
            "bot_self_ids": self._bot_self_ids,
            "ready": self.is_ready_for_auto_analysis(),
        }


__all__ = ["BotManager"]
