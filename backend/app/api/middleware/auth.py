# app/api/middleware/auth.py
"""
Authentication middleware for API key validation.
"""
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import http_exception_handler
from app.core.config import settings


def extract_api_key(headers) -> Optional[str]:
    """Extract an API key from a headers mapping (case-insensitive).

    Supports two authentication methods:
    1. Header: X-API-KEY: <api_key>
    2. Authorization: Bearer <api_key>

    Shared by AuthMiddleware (HTTP requests) and the WebSocket endpoints so the
    validation logic lives in exactly one place.
    """
    api_key = headers.get("X-API-KEY")
    if api_key:
        return api_key

    authorization = headers.get("Authorization")
    if authorization:
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() == "bearer":
            return param

    return None


def is_valid_api_key(api_key: Optional[str], valid_keys) -> bool:
    """Return True if api_key is present and contained in valid_keys."""
    if not api_key or not valid_keys:
        return False
    return api_key in valid_keys


def is_path_exempt(path: str, exempt_paths) -> bool:
    """Exact-path matching (with trailing-slash tolerance), never prefix matching.

    An exempt entry of ``"/"`` may only exempt the literal root path, and
    ``"/health"`` must not exempt ``"/health-evil"``. RC9.5: replaces the former
    ``path.startswith(exempt_path)`` logic, under which the default ``"/"`` entry
    exempted every route and neutralized auth / rate limiting / request-size /
    timeout enforcement.
    """
    normalized = path.rstrip("/") or "/"
    for exempt_path in exempt_paths:
        if normalized == (exempt_path.rstrip("/") or "/"):
            return True
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate API keys for protected endpoints.

    Supports two authentication methods:
    1. Header: X-API-KEY: <api_key>
    2. Authorization: Bearer <api_key>

    Certain endpoints can be excluded from authentication (health checks, etc.)
    """

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/debug/env"
        ]
        self.api_key_required = getattr(settings, 'API_KEY_REQUIRED', False)
        self.valid_api_keys = set(getattr(settings, 'API_KEYS', []))

    async def dispatch(self, request: Request, call_next):
        # Skip authentication if not required or if path is excluded
        if not self.api_key_required or self._is_path_excluded(request.url.path):
            return await call_next(request)

        # Allow CORS preflight OPTIONS through: the CORSMiddleware sits inside
        # this middleware and is responsible for enforcing the origin allowlist
        # on preflight requests. Requiring an API key on preflight would return
        # 401 and break browser clients before CORS could respond.
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract API key from request
        api_key = self._extract_api_key(request)

        # Validate API key
        if not self._is_valid_api_key(api_key):
            return await http_exception_handler(
                request,
                HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or missing API key",
                    headers={"WWW-Authenticate": "ApiKey"}
                )
            )

        # Add authenticated user info to request state (for downstream use)
        request.state.authenticated = True
        request.state.api_key = api_key

        response = await call_next(request)
        return response

    def _is_path_excluded(self, path: str) -> bool:
        """Check if the path should be excluded from authentication."""
        return is_path_exempt(path, self.exclude_paths)

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers."""
        return extract_api_key(request.headers)

    def _is_valid_api_key(self, api_key: Optional[str]) -> bool:
        """Validate the API key against the list of valid keys."""
        return is_valid_api_key(api_key, self.valid_api_keys)