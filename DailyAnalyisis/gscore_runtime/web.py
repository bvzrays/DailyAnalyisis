from __future__ import annotations

from contextvars import ContextVar

from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse

_current_request: ContextVar[Request | None] = ContextVar(
    "qq_daily_request",
    default=None,
)


class _QueryProxy:
    def get(self, key: str, default=None):
        current = _current_request.get()
        return current.query_params.get(key, default) if current is not None else default


class _RequestProxy:
    query = _QueryProxy()

    @property
    def headers(self):
        current = _current_request.get()
        return current.headers if current is not None else {}

    @property
    def cookies(self):
        current = _current_request.get()
        return current.cookies if current is not None else {}

    @property
    def scheme(self) -> str:
        current = _current_request.get()
        return current.url.scheme if current is not None else "http"

    async def json(self, default=None):
        current = _current_request.get()
        if current is None:
            return default
        try:
            return await current.json()
        except Exception:
            return default


request = _RequestProxy()


def json_response(data, status_code: int = 200):
    return JSONResponse(data, status_code=status_code)


def error_response(msg: str, status_code: int = 400):
    return JSONResponse({"status": "error", "message": msg}, status_code=status_code)


def stream_response(gen):
    return StreamingResponse(gen, media_type="text/event-stream")


def register_route(
    path: str,
    handler,
    methods: list[str],
    description: str = "",
    authenticator=None,
) -> None:
    from gsuid_core.webconsole.app_app import app

    normalized = path.replace("<trace_id>", "{trace_id}")
    route_path = f"/api{normalized}"
    route_name = "daily_analyisis_" + handler.__name__ + "_" + "_".join(methods)
    if any(getattr(route, "name", None) == route_name for route in app.routes):
        return

    async def endpoint(raw_request: Request, trace_id: str | None = None):
        token = _current_request.set(raw_request)
        try:
            if authenticator is not None and not authenticator.is_authenticated():
                return authenticator.unauthorized_response()
            if trace_id is None:
                return await handler()
            return await handler(trace_id)
        finally:
            _current_request.reset(token)

    app.add_api_route(
        route_path,
        endpoint,
        methods=methods,
        name=route_name,
        description=description,
    )


__all__ = ["error_response", "json_response", "request", "stream_response"]
