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

HELP_DIR = Path(__file__).parent
HELP_DATA = HELP_DIR / "help.json"
ICON_PATH = HELP_DIR / "icon_path"
TEXT_PATH = HELP_DIR / "texture2d"
PLUGIN_ICON = HELP_DIR.parent.parent / "ICON.png"

# 框架分类条文案画在 100px 高的素材中线；插件原图为 200px，需先压到该尺寸。
CAG_BG_SIZE = (1545, 100)


def _load_image(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    with Image.open(path) as img:
        image = img.convert("RGBA")
        if size is not None and image.size != size:
            image = image.resize(size, Image.Resampling.LANCZOS)
        return image


def _plugin_prefix() -> str:
    try:
        prefix = get_plugin_available_prefix(PLUGIN_NAME)
    except ValueError:
        prefix = ""
    return prefix or "day"


async def get_help_data() -> dict[str, PluginHelp]:
    async with aiofiles.open(HELP_DATA, "rb") as file:
        return json.loads(await file.read())


async def get_help(pm: int = 6, enable_cache: bool = True) -> bytes:
    return await get_new_help(
        plugin_name=PLUGIN_NAME,
        plugin_info={f"v{PLUGIN_VERSION}": ""},
        plugin_icon=_load_image(PLUGIN_ICON),
        plugin_icon_size=160,
        plugin_help=await get_help_data(),
        plugin_prefix=_plugin_prefix(),
        help_mode="light",
        banner_bg=_load_image(TEXT_PATH / "banner_bg.jpg"),
        banner_sub_text="群聊分析 · 可视化报告 · 每日群漫画",
        help_bg=_load_image(TEXT_PATH / "bg.jpg"),
        cag_bg=_load_image(TEXT_PATH / "cag_bg.png", CAG_BG_SIZE),
        cag_title_color=(22, 72, 150),
        cag_sub_color=(55, 115, 185),
        item_bg=_load_image(TEXT_PATH / "item.png"),
        icon_path=ICON_PATH,
        pm=pm,
        enable_cache=enable_cache,
    )


def register_help_entry() -> None:
    register_help(
        PLUGIN_NAME,
        f"{_plugin_prefix()}帮助",
        _load_image(PLUGIN_ICON),
    )


__all__ = ["get_help", "get_help_data", "register_help_entry"]
