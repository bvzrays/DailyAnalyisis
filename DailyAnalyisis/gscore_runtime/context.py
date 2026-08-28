from __future__ import annotations

import re
import json
from types import SimpleNamespace
from collections.abc import AsyncIterator

import aiohttp

from .config import PluginPaths, PluginConfig
from .provider import LLMUsage, LLMResponse

_SVG_OPEN_TAG_RE = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_DOODLE_CLASS_RE = re.compile(
    r'''\bclass\s*=\s*(["'])[^"']*\bdoodle\b[^"']*\1''',
    re.IGNORECASE,
)
_SVG_DIMENSION_RE = re.compile(
    r'''\s(?:width|height)\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)''',
    re.IGNORECASE,
)
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_IMG_SRC_RE = re.compile(r"\bsrc\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
_UPLOADED_URL_RE = re.compile(
    r"url\(\s*(['\"])uploaded:[^)]*?\1\s*\)", re.IGNORECASE
)
_FALLBACK_IMAGE_DATA = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 80 80'%3E%3Crect width='80' height='80' rx='16' "
    "fill='%23dbeafe'/%3E%3Ccircle cx='40' cy='30' r='12' fill='%2360a5fa'/%3E"
    "%3Cpath d='M16 68c4-16 44-16 48 0' fill='%2360a5fa'/%3E%3C/svg%3E"
)


def _protect_inline_icons(html: str) -> str:
    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group(0)
        if _DOODLE_CLASS_RE.search(tag) is None:
            return tag
        without_dimensions = _SVG_DIMENSION_RE.sub("", tag)
        return without_dimensions[:-1] + ' width="100%" height="100%">'

    return _SVG_OPEN_TAG_RE.sub(replace_tag, html)


def _usage_from_entries(entries: list[object]) -> LLMUsage:
    usage = LLMUsage()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("type") != "token_usage":
            continue
        data = entry.get("data")
        if not isinstance(data, dict):
            continue
        usage.prompt_tokens += int(data.get("input_tokens", 0) or 0)
        usage.completion_tokens += int(data.get("output_tokens", 0) or 0)
    usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
    return usage


def sanitize_rendered_html(html: str) -> str:
    """为缺失的图片资源提供稳定占位图，避免渲染器直接拒绝文档。"""

    def replace_img(match: re.Match[str]) -> str:
        tag = match.group(0)
        src_match = _IMG_SRC_RE.search(tag)
        if src_match is None:
            return tag[:-1] + f' src="{_FALLBACK_IMAGE_DATA}">'
        if not src_match.group(2).strip():
            start, end = src_match.span(2)
            return tag[:start] + _FALLBACK_IMAGE_DATA + tag[end:]
        return tag

    html = _IMG_TAG_RE.sub(replace_img, html)
    return _UPLOADED_URL_RE.sub(f"url('{_FALLBACK_IMAGE_DATA}')", html)


class _Provider:
    def __init__(self, config: PluginConfig, provider_id: str = "plugin") -> None:
        self.config = config
        self.provider_id = provider_id
        self.provider_config = {}

    def meta(self):
        return SimpleNamespace(id=self.provider_id, name=self.provider_id)

    def _llm_config(self) -> dict[str, object]:
        value = self.config.get("llm", {})
        return value if isinstance(value, dict) else {}

    def _settings(self, kwargs: dict[str, object]) -> dict[str, object]:
        config = self._llm_config()
        model = str(config.get("model", "gpt-4o-mini")).strip() or "gpt-4o-mini"
        base_url = str(config.get("api_url", "https://api.openai.com/v1")).strip()
        api_key = str(config.get("api_key", "")).strip()
        temperature_value = kwargs.get("temperature", config.get("temperature", 0.7))
        try:
            temperature = max(0.0, min(2.0, float(temperature_value)))
        except (TypeError, ValueError):
            temperature = 0.7
        try:
            max_tokens = max(1, int(config.get("max_tokens", 8192)))
        except (TypeError, ValueError):
            max_tokens = 8192
        try:
            timeout = max(1, int(config.get("timeout", 120)))
        except (TypeError, ValueError):
            timeout = 120
        self.provider_config = {
            "type": "plugin_openai_compatible",
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout,
        }
        return {
            "model": model,
            "base_url": base_url.rstrip("/"),
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout,
        }

    @staticmethod
    def _content_text(value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts: list[str] = []
            for item in value:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            return "".join(parts)
        return str(value or "")

    @staticmethod
    def _response_from_payload(payload: dict[str, object]) -> LLMResponse:
        choices = payload.get("choices")
        completion_text = ""
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                completion_text = _Provider._content_text(message.get("content"))
            if not completion_text:
                completion_text = _Provider._content_text(choices[0].get("text"))
        usage_data = payload.get("usage")
        usage = LLMUsage()
        if isinstance(usage_data, dict):
            usage.prompt_tokens = int(usage_data.get("prompt_tokens", 0) or 0)
            usage.completion_tokens = int(usage_data.get("completion_tokens", 0) or 0)
            usage.total_tokens = int(
                usage_data.get("total_tokens", usage.prompt_tokens + usage.completion_tokens)
                or 0
            )
        return LLMResponse(
            role="assistant",
            completion_text=completion_text,
            usage=usage,
            raw_completion=payload,
        )

    @staticmethod
    def _error_text(status: int, body: str, api_key: str) -> str:
        safe_body = body.replace(api_key, "[REDACTED]") if api_key else body
        return f"插件 LLM 请求失败 (HTTP {status}): {safe_body[:1000]}"

    def _build_payload(self, kwargs: dict[str, object], stream: bool) -> dict[str, object]:
        settings = self._settings(kwargs)
        messages: list[dict[str, str]] = []
        system_prompt = kwargs.get("system_prompt")
        if system_prompt:
            messages.append({"role": "system", "content": str(system_prompt)})
        messages.append({"role": "user", "content": str(kwargs.get("prompt", ""))})
        payload: dict[str, object] = {
            "model": settings["model"],
            "messages": messages,
            "temperature": settings["temperature"],
            "max_tokens": settings["max_tokens"],
            "stream": stream,
        }
        response_format = kwargs.get("response_format")
        if isinstance(response_format, dict):
            payload["response_format"] = response_format
        return payload

    async def text_chat(self, **kwargs: object) -> LLMResponse:
        return await self._run(kwargs)

    async def text_chat_stream(self, **kwargs: object) -> AsyncIterator[LLMResponse]:
        settings = self._settings(kwargs)
        payload = self._build_payload(kwargs, stream=True)
        headers = {"Content-Type": "application/json"}
        if settings["api_key"]:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        timeout = aiohttp.ClientTimeout(total=int(settings["timeout"]))
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.post(
                f"{settings['base_url']}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                if response.status >= 400:
                    body = await response.text()
                    raise RuntimeError(self._error_text(response.status, body, str(settings["api_key"])))
                collected: list[str] = []
                usage = LLMUsage()
                async for raw_line in response.content:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(chunk, dict):
                        continue
                    choices = chunk.get("choices")
                    text = ""
                    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                        delta = choices[0].get("delta")
                        if isinstance(delta, dict):
                            text = self._content_text(delta.get("content"))
                    if text:
                        collected.append(text)
                        yield LLMResponse(completion_text=text, is_chunk=True)
                    usage_payload = chunk.get("usage")
                    if isinstance(usage_payload, dict):
                        usage = self._response_from_payload({"usage": usage_payload}).usage
                yield LLMResponse(
                    completion_text="".join(collected), usage=usage, is_chunk=False
                )

    async def _run(self, kwargs: dict[str, object]) -> LLMResponse:
        settings = self._settings(kwargs)
        payload = self._build_payload(kwargs, stream=False)
        headers = {"Content-Type": "application/json"}
        if settings["api_key"]:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        timeout = aiohttp.ClientTimeout(total=int(settings["timeout"]))
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.post(
                f"{settings['base_url']}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                body = await response.text()
                if response.status >= 400:
                    raise RuntimeError(
                        self._error_text(response.status, body, str(settings["api_key"]))
                    )
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError as exc:
                    raise RuntimeError("插件 LLM 返回了无效 JSON") from exc
                if not isinstance(parsed, dict):
                    raise RuntimeError("插件 LLM 返回格式不是 JSON 对象")
                return self._response_from_payload(parsed)


class _CronManager:
    @property
    def scheduler(self):
        from gsuid_core.aps import scheduler

        return scheduler


class PluginContext:
    def __init__(self, config: PluginConfig) -> None:
        self.cron_manager = _CronManager()
        self._provider = _Provider(config)
        self.persona_manager = None
        self.conversation_manager = None

    def get_provider_by_id(self, provider_id: str | None = None):
        if provider_id not in (None, self._provider.provider_id):
            return None
        return self._provider

    def get_all_providers(self):
        return [self._provider]

    async def get_current_chat_provider_id(self, umo: str | None = None) -> str:
        return self._provider.provider_id

    async def llm_generate(self, **kwargs) -> LLMResponse:
        return await self._provider.text_chat(**kwargs)

    def register_web_api(
        self,
        path,
        handler,
        methods,
        description: str = "",
    ) -> None:
        from .web import register_route

        register_route(path, handler, methods, description)


class PluginBase:
    def __init__(self, context: PluginContext, config: dict | None = None) -> None:
        self.context = context
        self._kv_path = PluginPaths.get_data_dir() / "kv_store.json"

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

    async def html_render(
        self,
        tmpl: str,
        data: dict,
        return_url: bool = True,
        options: dict | None = None,
    ):
        from gsuid_core.utils.html_render import render_html_to_bytes

        opts = options or {}
        viewport = opts.get("viewport", {}) if isinstance(opts.get("viewport"), dict) else {}
        width = float(viewport.get("width", 1200))
        image_type = str(opts.get("type", "jpeg")).lower()
        image_format = "jpeg" if image_type in {"jpg", "jpeg"} else "png"
        return await render_html_to_bytes(
            sanitize_rendered_html(_protect_inline_icons(tmpl)),
            max_width=width,
            image_format=image_format,
            jpeg_quality=int(opts.get("quality", 95)),
        )


__all__ = ["PluginBase", "PluginContext"]
