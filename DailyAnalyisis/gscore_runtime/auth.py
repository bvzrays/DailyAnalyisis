from __future__ import annotations

import hmac
import time
import hashlib
import secrets
from typing import Any
from collections.abc import Callable

from .web import request, json_response, error_response


class WebUIAuthenticator:
    cookie_name = "daily_analyisis_session"
    session_ttl = 7 * 24 * 60 * 60
    password_iterations = 310_000

    def __init__(
        self,
        config: Any,
        password_reader: Callable[[], str | None] | None = None,
        enabled_reader: Callable[[], bool | None] | None = None,
    ) -> None:
        self.config = config
        self.password_reader = password_reader
        self.enabled_reader = enabled_reader
        self._sessions: dict[str, float] = {}
        self._observed_password_hash: str | None = None

    def _section(self) -> dict[str, Any]:
        section = self.config.get("webui")
        if isinstance(section, dict):
            return section
        section = {}
        self.config["webui"] = section
        return section

    @staticmethod
    def _as_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        if value is None:
            return default
        return bool(value)

    @property
    def enabled(self) -> bool:
        if self.enabled_reader is not None:
            try:
                current = self.enabled_reader()
            except Exception:
                current = None
            if current is not None:
                return self._as_bool(current)
        return self._as_bool(self._section().get("external_enabled", False))

    def _password_hash(self) -> str:
        if self.password_reader is not None:
            try:
                current = self.password_reader()
            except Exception:
                current = None
            if current is not None:
                value = str(current).strip()
            else:
                value = str(self._section().get("password", "")).strip()
        else:
            value = str(self._section().get("password", "")).strip()
        if value and not value.startswith("pbkdf2_sha256$"):
            value = self.hash_password(value)
            self._section()["password"] = value
            save_config = getattr(self.config, "save_config", None)
            if callable(save_config):
                save_config()
        if (
            self._observed_password_hash is not None
            and value != self._observed_password_hash
        ):
            self._sessions.clear()
        self._observed_password_hash = value
        return value

    @property
    def configured(self) -> bool:
        return self._password_hash().startswith("pbkdf2_sha256$")

    @classmethod
    def hash_password(cls, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls.password_iterations,
        )
        return "pbkdf2_sha256${}${}${}".format(
            cls.password_iterations,
            salt.hex(),
            digest.hex(),
        )

    @classmethod
    def _verify_password(cls, password: str, encoded: str) -> bool:
        try:
            scheme, iterations, salt_hex, digest_hex = encoded.split("$", 3)
            if scheme != "pbkdf2_sha256":
                return False
            expected = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iterations),
            ).hex()
            return hmac.compare_digest(expected, digest_hex)
        except (TypeError, ValueError):
            return False

    def set_password(self, password: str) -> None:
        self._section()["password"] = self.hash_password(password)
        save_config = getattr(self.config, "save_config", None)
        if callable(save_config):
            save_config()
        self._password_hash()

    def _purge_sessions(self) -> None:
        now = time.time()
        expired = [token for token, expires_at in self._sessions.items() if expires_at <= now]
        for token in expired:
            self._sessions.pop(token, None)

    def is_authenticated(self) -> bool:
        if not self.enabled or not self.configured:
            return False
        self._purge_sessions()
        token = request.cookies.get(self.cookie_name, "")
        return bool(token and token in self._sessions)

    def status_response(self):
        if not self.enabled:
            return error_response("DailyAnalyisis 外部 WebUI 当前已关闭", status_code=404)
        return json_response(
            {
                "status": "ok",
                "data": {
                    "configured": self.configured,
                    "authenticated": self.is_authenticated(),
                },
            }
        )

    def unauthorized_response(self):
        if not self.enabled:
            return error_response("DailyAnalyisis 外部 WebUI 当前已关闭", status_code=404)
        return json_response(
            {
                "status": "auth_required",
                "message": "WebUI 尚未设置密码" if not self.configured else "WebUI 需要登录",
                "data": {
                    "configured": self.configured,
                    "authenticated": False,
                },
            },
            status_code=428 if not self.configured else 401,
        )

    def _session_response(self, message: str):
        token = secrets.token_urlsafe(32)
        self._purge_sessions()
        self._sessions[token] = time.time() + self.session_ttl
        response = json_response(
            {
                "status": "ok",
                "message": message,
                "data": {"configured": True, "authenticated": True},
            }
        )
        response.set_cookie(
            self.cookie_name,
            token,
            max_age=self.session_ttl,
            httponly=True,
            samesite="lax",
            secure=request.scheme == "https",
            path="/",
        )
        return response

    def setup(self, password: str, confirmation: str):
        if not self.enabled:
            return error_response("DailyAnalyisis 外部 WebUI 当前已关闭", status_code=404)
        if self.configured:
            return error_response("WebUI 密码已经设置，请使用登录接口", status_code=409)
        if len(password) < 8:
            return error_response("密码至少需要 8 个字符", status_code=400)
        if password != confirmation:
            return error_response("两次输入的密码不一致", status_code=400)
        self.set_password(password)
        return self._session_response("WebUI 密码设置成功")

    def login(self, password: str):
        if not self.enabled:
            return error_response("DailyAnalyisis 外部 WebUI 当前已关闭", status_code=404)
        if not self.configured:
            return error_response("请先设置 WebUI 密码", status_code=428)
        if not self._verify_password(password, self._password_hash()):
            return error_response("WebUI 密码错误", status_code=401)
        return self._session_response("WebUI 登录成功")

    def logout(self):
        if not self.enabled:
            return error_response("DailyAnalyisis 外部 WebUI 当前已关闭", status_code=404)
        token = request.cookies.get(self.cookie_name, "")
        self._sessions.pop(token, None)
        response = json_response({"status": "ok", "message": "WebUI 已退出登录"})
        response.delete_cookie(self.cookie_name, path="/")
        return response
