# app/api/middleware/timeout.py
"""
Request timeout middleware.
"""
import asyncio
import logging

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import http_exception_handler
from app.api.middleware.auth import is_path_exempt
from app.core.config import settings

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts to prevent hanging connections.

    Features:
    - Configurable timeout duration
    - Applies to all requests
    - Proper timeout error responses
    - Exempt paths for health checks (optional)
    """

    def __init__(self, app):
        super().__init__(app)
        self.enabled = getattr(settings, 'REQUEST_TIMEOUT_ENABLED', False)
        self.timeout_seconds = getattr(settings, 'REQUEST_TIMEOUT_SECONDS', 30)
        self.exempt_paths = set(getattr(settings, 'REQUEST_TIMEOUT_EXEMPT_PATHS', [
            "/", "/health", "/docs", "/redoc", "/openapi.json", "/debug/env"
        ]))

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Check if path is exempt
        if self._is_path_exempt(request.url.path):
            return await call_next(request)

        try:
            # Apply timeout to the request processing
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout after {self.timeout_seconds}s for {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            # Return the response directly (not raise): an HTTPException raised
            # inside a BaseHTTPMiddleware becomes a 500 because
            # ExceptionMiddleware sits inside the middleware stack.
            return await http_exception_handler(
                request,
                HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail=f"Request timed out after {self.timeout_seconds} seconds"
                )
            )

    def _is_path_exempt(self, path: str) -> bool:
        """Check if path is exempt from timeout.

        Exact match only (with trailing-slash tolerance), never prefix match.
        RC9.5: the former ``path.startswith(exempt_path)`` logic meant the
        default ``"/"`` entry exempted every route, disabling enforcement.
        """
        return is_path_exempt(path, self.exempt_paths)