from __future__ import annotations

import json
from types import SimpleNamespace
from pathlib import Path

from astrbot.api.provider import Usage, LLMResponse


class StarTools:
    _data_dir: Path = Path.cwd() / "data" / "QQGroupDailyAnalysis"

    @classmethod
    def set_data_dir(cls, path: Path) -> None:
        cls._data_dir = path
        cls._data_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_data_dir(cls, plugin_name: str) -> Path:
        cls._data_dir.mkdir(parents=True, exist_ok=True)
        return cls._data_dir


class _Provider:
    def __init__(self, provider_id: str = "gscore") -> None:
        self.provider_id = provider_id
        self.provider_config = {"type": "gscore", "model": provider_id}

    def meta(self):
        return SimpleNamespace(id=self.provider_id, name=self.provider_id)

    async def text_chat(self, **kwargs) -> LLMResponse:
        return await self._run(kwargs)

    async def text_chat_stream(self, **kwargs):
        yield await self._run(kwargs)

    async def _run(self, kwargs: dict) -> LLMResponse:
        from gsuid_core.ai_core.gs_agent import GsCoreAIAgent

        prompt = str(kwargs.get("prompt", ""))
        system_prompt = kwargs.get("system_prompt")
        agent = GsCoreAIAgent(
            system_prompt=str(system_prompt) if system_prompt else None,
            create_by="QQGroupDailyAnalysis",
            task_level="high",
            dynamic_tools=False,
        )
        result = await agent.run(
            prompt,
            return_mode="return",
            tools=[],
            suppress_intermediate_text=True,
        )
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        return LLMResponse(role="assistant", completion_text=text, usage=Usage())


class _CronManager:
    @property
    def scheduler(self):
        from gsuid_core.aps import scheduler

        return scheduler


class Context:
    def __init__(self) -> None:
        self.cron_manager = _CronManager()
        self._provider = _Provider()
        self.persona_manager = None
        self.conversation_manager = None

    def get_provider_by_id(self, provider_id: str | None = None):
        return self._provider

    def get_all_providers(self):
        return [self._provider]

    async def get_current_chat_provider_id(self, umo: str | None = None) -> str:
        return self._provider.provider_id

    async def llm_generate(self, **kwargs) -> LLMResponse:
        return await self._provider.text_chat(**kwargs)

    def register_web_api(self, path, handler, methods, description="") -> None:
        from astrbot.api.web import register_route

        register_route(path, handler, methods, description)


class Star:
    def __init__(self, context: Context, config: dict | None = None) -> None:
        self.context = context
        self._kv_path = StarTools.get_data_dir("") / "kv_store.json"

    async def put_kv_data(self, key: str, value: object) -> None:
        data = self._read_kv()
        data[key] = value
        temp = self._kv_path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self._kv_path)

    async def get_kv_data(self, key: str, default=None):
        return self._read_kv().get(key, default)

    def _read_kv(self) -> dict:
        try:
            data = json.loads(self._kv_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    async def html_render(self, tmpl: str, data: dict, return_url=True, options: dict | None = None):
        from gsuid_core.utils.html_render import render_html_to_bytes

        opts = options or {}
        viewport = opts.get("viewport", {}) if isinstance(opts.get("viewport"), dict) else {}
        width = float(viewport.get("width", 1200))
        image_type = str(opts.get("type", "jpeg")).lower()
        image_format = "jpeg" if image_type in {"jpg", "jpeg"} else "png"
        return await render_html_to_bytes(
            tmpl,
            max_width=width,
            image_format=image_format,
            jpeg_quality=int(opts.get("quality", 95)),
        )


__all__ = ["Context", "Star", "StarTools"]
