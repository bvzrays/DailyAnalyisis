from __future__ import annotations

import json
from pathlib import Path

import aiofiles
from PIL import Image

from gsuid_core.sv import get_plugin_available_prefix
from gsuid_core.help.model import PluginHelp
from gsuid_core.help.utils import register_help
from gsuid_core.help.draw_new_plugin_help import get_new_help

from ..src.shared.constants import PLUGIN_NAME, PLUGIN_VERSION

HELP_DATA = Path(__file__).parent / "help.json"
PLUGIN_ICON = Path(__file__).parent.parent.parent / "ICON.png"


async def get_help_data() -> dict[str, PluginHelp]:
    async with aiofiles.open(HELP_DATA, "rb") as file:
        return json.loads(await file.read())


async def get_help(pm: int = 6) -> bytes:
    with Image.open(PLUGIN_ICON) as icon:
        return await get_new_help(
            plugin_name=PLUGIN_NAME,
            plugin_info={f"v{PLUGIN_VERSION}": ""},
            plugin_icon=icon.copy(),
            plugin_help=await get_help_data(),
            plugin_prefix=get_plugin_available_prefix(PLUGIN_NAME),
            banner_sub_text="群聊分析 · 可视化报告 · 每日群漫画",
            help_mode="dark",
            pm=pm,
            enable_cache=True,
        )


def register_help_entry() -> None:
    with Image.open(PLUGIN_ICON) as icon:
        register_help(
            PLUGIN_NAME,
            f"{get_plugin_available_prefix(PLUGIN_NAME)}帮助",
            icon.copy(),
        )


__all__ = ["get_help", "get_help_data", "register_help_entry"]
