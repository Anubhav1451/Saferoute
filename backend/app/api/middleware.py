# app/api/middleware.py
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process request and time it
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log the request
        logger.info(
            f"Method: {request.method} "
            f"Path: {request.url.path} "
            f"Status: {response.status_code} "
            f"Process Time: {process_time:.3f}s "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers for protection
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # HSTS would typically be added by a reverse proxy in production
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response