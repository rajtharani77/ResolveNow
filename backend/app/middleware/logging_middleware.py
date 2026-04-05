"""
Request / Response logging middleware.

Logs every inbound HTTP request and its outgoing response including:
  - method, path, query string
  - client IP
  - response status code
  - elapsed time in milliseconds
  - request body for mutating methods (POST / PUT / PATCH) – truncated to
    2 000 chars to avoid flooding logs with large file uploads.

Sensitive paths (login, register, refresh) have their bodies redacted so
passwords and tokens are never written to disk.
"""

import time
import json
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logger import get_logger

logger = get_logger("middleware.request")

# Paths whose request bodies should be redacted in logs
_REDACT_PATHS = {"/auth/login", "/auth/register", "/auth/refresh", "/auth/logout", "/auth/login-oauth"}
_BODY_METHODS = {"POST", "PUT", "PATCH"}
_MAX_BODY_LOG_CHARS = 2_000


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # ── log request ───────────────────────────────────────────────────
        path = request.url.path
        query = f"?{request.url.query}" if request.url.query else ""
        client_ip = self._get_client_ip(request)

        body_snippet = ""
        if request.method in _BODY_METHODS:
            body_snippet = await self._get_body_snippet(request, path)

        logger.info(
            "→ %s %s%s | ip=%s%s",
            request.method,
            path,
            query,
            client_ip,
            f" | body={body_snippet}" if body_snippet else "",
        )

        # ── call handler ──────────────────────────────────────────────────
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1_000
            logger.error(
                "✗ %s %s%s | UNHANDLED EXCEPTION | %.1f ms | error=%s",
                request.method,
                path,
                query,
                elapsed_ms,
                repr(exc),
                exc_info=True,
            )
            raise

        # ── log response ──────────────────────────────────────────────────
        elapsed_ms = (time.perf_counter() - start_time) * 1_000
        level = logger.warning if response.status_code >= 400 else logger.info
        level(
            "← %s %s%s | %d | %.1f ms",
            request.method,
            path,
            query,
            response.status_code,
            elapsed_ms,
        )

        return response

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    @staticmethod
    async def _get_body_snippet(request: Request, path: str) -> str:
        # Redact sensitive paths entirely
        for sensitive in _REDACT_PATHS:
            if path.endswith(sensitive):
                return "[REDACTED]"

        # Skip multipart (file uploads) – too large and binary
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            return "[multipart/skipped]"

        try:
            raw = await request.body()
            if not raw:
                return ""
            text = raw.decode("utf-8", errors="replace")
            if len(text) > _MAX_BODY_LOG_CHARS:
                text = text[:_MAX_BODY_LOG_CHARS] + "…[truncated]"
            return text
        except Exception:
            return "[unreadable]"