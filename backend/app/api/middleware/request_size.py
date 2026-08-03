# app/api/middleware/request_size.py
"""
Request size limiting middleware.
"""
import logging

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import http_exception_handler
from app.api.middleware.auth import is_path_exempt
from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size to prevent denial of service attacks.

    Features:
    - Configurable maximum request size
    - Applies to all requests with bodies (POST, PUT, PATCH, etc.)
    - Exempt paths for health checks and documentation
    - Clear error messages with actual size vs limit
    """

    def __init__(self, app):
        super().__init__(app)
        self.enabled = getattr(settings, 'REQUEST_SIZE_LIMIT_ENABLED', False)
        self.max_size = getattr(settings, 'REQUEST_SIZE_LIMIT_BYTES', 5 * 1024 * 1024)  # 5MB default
        self.exempt_paths = set(getattr(settings, 'REQUEST_SIZE_LIMIT_EXEMPT_PATHS', [
            "/", "/health", "/docs", "/redoc", "/openapi.json", "/debug/env"
        ]))

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Check if path is exempt
        if self._is_path_exempt(request.url.path):
            return await call_next(request)

        # For requests without content-length header, we need to read the body
        # This is less efficient but necessary for size checking
        content_length = request.headers.get("content-length")

        # If content-length is provided and exceeds limit, reject immediately
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_size:
                    logger.warning(
                        f"Request too large: {length} bytes > {self.max_size} bytes from {request.client.host if request.client else 'unknown'} "
                        f"to {request.method} {request.url.path}"
                    )
                    # Return the response directly (not raise): an HTTPException
                    # raised inside a BaseHTTPMiddleware becomes a 500 because
                    # ExceptionMiddleware sits inside the middleware stack.
                    return await http_exception_handler(
                        request,
                        HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=f"Request body too large. Maximum size allowed is {self.max_size} bytes. Received {length} bytes."
                        )
                    )
            except ValueError:
                # Invalid content-length header, fall back to reading body
                pass

        # For chunked transfers or missing content-length, we need to check the actual body
        # We'll read the body and then reconstruct the request
        body = await request.body()
        if len(body) > self.max_size:
            logger.warning(
                f"Request too large: {len(body)} bytes > {self.max_size} bytes from {request.client.host if request.client else 'unknown'} "
                f"to {request.method} {request.url.path}"
            )
            return await http_exception_handler(
                request,
                HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=f"Request body too large. Maximum size allowed is {self.max_size} bytes. Received {len(body)} bytes."
                )
            )

        # Create a new request with a receive() that serves the pre-read body
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        # Create a new request with our custom receive function
        from starlette.requests import Request
        new_request = Request(request.scope, receive)

        # The reconstructed request shares the original request's scope, so
        # request.state (backed by scope["state"]) is carried over automatically.
        # NOTE: the previous code assigned `new_request._state = request._state`,
        # but this Starlette version's _CachedRequest has no `_state` attribute,
        # which crashed every non-exempt request while size limiting was enabled.

        response = await call_next(new_request)
        return response

    def _is_path_exempt(self, path: str) -> bool:
        """Check if path is exempt from size limiting.

        Exact match only (with trailing-slash tolerance), never prefix match.
        RC9.5: the former ``path.startswith(exempt_path)`` logic meant the
        default ``"/"`` entry exempted every route, disabling enforcement.
        """
        return is_path_exempt(path, self.exempt_paths)