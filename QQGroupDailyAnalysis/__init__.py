from __future__ import annotations

from gsuid_core.sv import SV, Plugins
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.server import on_core_start, on_core_shutdown

from . import webui_static as webui_static
from .runtime import runtime

Plugins(
    name="QQGroupDailyAnalysis",
    allow_empty_prefix=True,
    alias=["群日常分析", "群分析总结"],
)

archive_sv = SV("群日常分析消息归档", pm=6, area="GROUP", priority=10)
admin_sv = SV("群日常分析管理命令", pm=3, area="GROUP", priority=5)


def _parse_days(text: str) -> int | None:
    value = str(text or "").strip().split(maxsplit=1)[0] if str(text or "").strip() else ""
    if not value:
        return None
    try:
        return max(1, min(int(value), 365))
    except ValueError:
        return None


@on_core_start
async def initialize_qq_group_daily_analysis() -> None:
    await runtime.initialize()


@on_core_shutdown
async def shutdown_qq_group_daily_analysis() -> None:
    await runtime.shutdown()


@archive_sv.on_message(unique_id="qq_group_daily_analysis_archive", block=False)
async def archive_group_message(bot: Bot, event: Event) -> None:
    await runtime.archive(bot, event)


@admin_sv.on_command(("群分析", "group_analysis"), block=True)
async def analyze_group_daily(bot: Bot, event: Event) -> None:
    await runtime.invoke("analyze_group_daily", bot, event, _parse_days(event.text))


@admin_sv.on_command(("群漫画", "group_comic", "daily_comic"), block=True)
async def generate_group_comic(bot: Bot, event: Event) -> None:
    await runtime.invoke("generate_group_comic", bot, event, _parse_days(event.text))


@admin_sv.on_command(("设置格式", "set_format"), block=True)
async def set_output_format(bot: Bot, event: Event) -> None:
    await runtime.invoke("set_output_format", bot, event, event.text.strip())


@admin_sv.on_command(("设置模板", "set_template"), block=True)
async def set_report_template(bot: Bot, event: Event) -> None:
    await runtime.invoke("set_report_template", bot, event, event.text.strip())


@admin_sv.on_command(("查看模板", "view_templates"), block=True)
async def view_templates(bot: Bot, event: Event) -> None:
    await runtime.invoke("view_templates", bot, event)


@admin_sv.on_command(("分析设置", "analysis_settings"), block=True)
async def analysis_settings(bot: Bot, event: Event) -> None:
    await runtime.invoke("analysis_settings", bot, event, event.text.strip() or "status")


@admin_sv.on_command(("增量状态", "incremental_status"), block=True)
async def incremental_status(bot: Bot, event: Event) -> None:
    await runtime.invoke("incremental_status", bot, event)


__all__ = [
    "analysis_settings",
    "analyze_group_daily",
    "archive_group_message",
    "generate_group_comic",
    "incremental_status",
    "set_output_format",
    "set_report_template",
    "view_templates",
]
