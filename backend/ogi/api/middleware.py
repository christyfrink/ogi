"""API key authentication middleware for no-Supabase deployments.

All requests except /health must carry:
    Authorization: Bearer <OGI_LOCAL_API_KEY>

The key is set by the frontend nginx proxy automatically. External clients
(e.g. MCP servers) must include the header explicitly.

Uses hmac.compare_digest for constant-time comparison to prevent timing attacks.

Implemented as a pure ASGI middleware (not BaseHTTPMiddleware) to avoid the
known BaseHTTPMiddleware/anyio incompatibility with async SQLAlchemy sessions.
"""
import hmac
import json

from starlette.types import ASGIApp, Receive, Scope, Send

from ogi.config import settings

_EXEMPT_PATHS = frozenset({"/health"})
_UNAUTHORIZED_BODY = json.dumps({"detail": "Unauthorized"}).encode()


class ApiKeyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        if path in _EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return

        # Extract Authorization header from scope headers
        headers = dict(scope.get("headers", []))
        auth = headers.get(b"authorization", b"").decode("latin-1")

        if not auth.startswith("Bearer "):
            await self._send_401(send)
            return

        token = auth.removeprefix("Bearer ")

        if not hmac.compare_digest(token.encode("utf-8"), settings.local_api_key.encode("utf-8")):
            await self._send_401(send)
            return

        await self.app(scope, receive, send)

    @staticmethod
    async def _send_401(send: Send) -> None:
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(_UNAUTHORIZED_BODY)).encode()),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": _UNAUTHORIZED_BODY,
            "more_body": False,
        })
