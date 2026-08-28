from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from gsuid_core.webconsole.app_app import app

WEBUI_PATH = Path(__file__).resolve().parent / "pages" / "daily-analysis"
WEBUI_ROUTE = "/daily-analyisis-gscore"


def _external_webui_enabled() -> bool:
    try:
        from .plugin_config import gsconfig

        field = gsconfig.config.get("ExternalWebUIEnabled")
        value: Any = field.data if field is not None else False
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
    except Exception:
        return False


class _ExternalWebUIGate:
    def __init__(self, application: Any) -> None:
        self.application = application

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "http" and not _external_webui_enabled():
            response = JSONResponse(
                {"status": "disabled", "message": "DailyAnalyisis 外部 WebUI 当前已关闭"},
                status_code=404,
            )
            await response(scope, receive, send)
            return
        await self.application(scope, receive, send)


if WEBUI_PATH.is_dir() and not any(getattr(route, "path", None) == WEBUI_ROUTE for route in app.routes):
    app.mount(
        WEBUI_ROUTE,
        _ExternalWebUIGate(StaticFiles(directory=WEBUI_PATH, html=True)),
        name="daily-analyisis-gscore",
    )


__all__ = ["WEBUI_PATH", "WEBUI_ROUTE"]
