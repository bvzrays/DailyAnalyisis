from __future__ import annotations

import inspect

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .plugin import GroupDailyAnalysis
from .event_bridge import GsCoreMessageEvent, send_plugin_result
from .plugin_config import gsconfig, load_config
from .gscore_runtime import PluginContext


class PluginRuntime:
    def __init__(self) -> None:
        self.plugin: GroupDailyAnalysis | None = None

    async def initialize(self) -> None:
        if self.plugin is not None:
            return
        if not gsconfig.get_config("Enabled").data:
            logger.info("QQGroupDailyAnalysis is disabled by configuration")
            return
        config = load_config()
        plugin = GroupDailyAnalysis(PluginContext(config), config)
        self.plugin = plugin
        await plugin.initialize()

    async def shutdown(self) -> None:
        plugin = self.plugin
        self.plugin = None
        if plugin is not None:
            await plugin.terminate()

    async def archive(self, bot: Bot, event: Event) -> None:
        if self.plugin is None:
            await self.initialize()
        if self.plugin is None:
            return
        await self.plugin.bot_manager.archive_gscore_event(bot, event)
        if self.plugin.auto_scheduler:
            plugin_event = GsCoreMessageEvent(bot, event)
            await self.plugin.auto_scheduler.record_incremental_message(plugin_event)

    async def invoke(self, method_name: str, bot: Bot, event: Event, *args) -> None:
        if self.plugin is None:
            await self.initialize()
        if self.plugin is None:
            await bot.send("❌ 群日常分析插件当前已禁用")
            return
        plugin_event = GsCoreMessageEvent(bot, event)
        self.plugin.bot_manager.update_from_event(plugin_event)
        method = getattr(self.plugin, method_name)
        result = method(plugin_event, *args)
        if inspect.isasyncgen(result):
            async for item in result:
                await send_plugin_result(bot, item)
        else:
            value = await result
            if value is not None:
                await send_plugin_result(bot, value)


runtime = PluginRuntime()


__all__ = ["runtime"]
