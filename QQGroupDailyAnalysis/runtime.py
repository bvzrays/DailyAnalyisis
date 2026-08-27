from __future__ import annotations

import inspect

from gsuid_core.bot import Bot
from astrbot.api.star import Context
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .legacy_main import GroupDailyAnalysis
from .event_bridge import GsCoreAstrMessageEvent, send_compat_result
from .plugin_config import gsconfig, load_config


class PluginRuntime:
    def __init__(self) -> None:
        self.plugin: GroupDailyAnalysis | None = None

    async def initialize(self) -> None:
        if self.plugin is not None:
            return
        if not gsconfig.get_config("Enabled").data:
            logger.info("QQGroupDailyAnalysis is disabled by configuration")
            return
        plugin = GroupDailyAnalysis(Context(), load_config())
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
            compat_event = GsCoreAstrMessageEvent(bot, event)
            await self.plugin.auto_scheduler.record_incremental_message(compat_event)

    async def invoke(self, method_name: str, bot: Bot, event: Event, *args) -> None:
        if self.plugin is None:
            await self.initialize()
        if self.plugin is None:
            await bot.send("❌ 群日常分析插件当前已禁用")
            return
        compat_event = GsCoreAstrMessageEvent(bot, event)
        self.plugin.bot_manager.update_from_event(compat_event)
        method = getattr(self.plugin, method_name)
        result = method(compat_event, *args)
        if inspect.isasyncgen(result):
            async for item in result:
                await send_compat_result(bot, item)
        else:
            value = await result
            if value is not None:
                await send_compat_result(bot, value)


runtime = PluginRuntime()


__all__ = ["runtime"]
