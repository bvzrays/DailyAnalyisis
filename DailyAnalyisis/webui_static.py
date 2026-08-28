from __future__ import annotations

from pathlib import Path

from fastapi.staticfiles import StaticFiles

from gsuid_core.webconsole.app_app import app

WEBUI_PATH = Path(__file__).resolve().parent / "pages" / "daily-analysis"
WEBUI_ROUTE = "/daily-analyisis-gscore"

if WEBUI_PATH.is_dir() and not any(getattr(route, "path", None) == WEBUI_ROUTE for route in app.routes):
    app.mount(
        WEBUI_ROUTE,
        StaticFiles(directory=WEBUI_PATH, html=True),
        name="daily-analyisis-gscore",
    )


__all__ = ["WEBUI_PATH", "WEBUI_ROUTE"]
