"""API key authentication middleware for no-Supabase deployments.

All requests except /health must carry:
    Authorization: Bearer <OGI_LOCAL_API_KEY>

The key is set by the frontend nginx proxy automatically. External clients
(e.g. MCP servers) must include the header explicitly.

Uses hmac.compare_digest for constant-time comparison to prevent timing attacks.
"""
import hmac

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from ogi.config import settings

_EXEMPT_PATHS = frozenset({"/health"})
_UNAUTHORIZED = {"detail": "Unauthorized"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(_UNAUTHORIZED, status_code=401)

        token = auth.removeprefix("Bearer ")
        expected = settings.local_api_key or ""

        if not hmac.compare_digest(token.encode("utf-8"), expected.encode("utf-8")):
            return JSONResponse(_UNAUTHORIZED, status_code=401)

        return await call_next(request)
