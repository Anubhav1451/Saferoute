# app/api/middleware/__init__.py
"""Middleware package."""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses with slow request detection"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process request and time it
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Check if this is a slow request
        from app.core.config import settings
        slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1.0)
        slow_log_enabled = getattr(settings, 'SLOW_REQUEST_LOG_ENABLED', True)

        if slow_log_enabled and process_time > slow_threshold:
            logger.warning(
                f"SLOW REQUEST: {request.method} {request.url.path} took {process_time:.3f}s "
                f"(threshold: {slow_threshold}s) from {request.client.host if request.client else 'unknown'}"
            )
        else:
            # Log the request normally
            logger.info(
                f"Method: {request.method} "
                f"Path: {request.url.path} "
                f"Status: {response.status_code} "
                f"Process Time: {process_time:.3f}s "
                f"Client: {request.client.host if request.client else 'unknown'}"
            )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers with trusted proxy support"""

    # SEC-16 (T7): Swagger UI / ReDoc inject inline <script>/<style> and rely
    # on eval, so the strict default CSP breaks them. Docs are only served in
    # development (DEBUG=true); when docs are enabled this relaxed policy is
    # applied to the /docs and /redoc paths only. Every other response keeps
    # the strict policy.
    SWAGGER_CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )

    def __init__(self, app):
        super().__init__(app)
        from app.core.config import settings
        self.enabled = getattr(settings, 'SECURITY_HEADERS_ENABLED', True)
        self.hsts_max_age = getattr(settings, 'STRICT_TRANSPORT_SECURITY_MAX_AGE', 31536000)
        self.csp_policy = getattr(settings, 'CONTENT_SECURITY_POLICY', "default-src 'self'")
        self.docs_enabled = getattr(settings, 'DEBUG', False)
        self.trusted_proxy_enabled = getattr(settings, 'TRUSTED_PROXY_ENABLED', False)
        self.trusted_proxy_count = getattr(settings, 'TRUSTED_PROXY_COUNT', 1)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        if not self.enabled:
            return response

        # Security headers for protection.
        # SEC-16 (T7): X-XSS-Protection removed (deprecated and ineffective in
        # modern browsers — can even introduce sanitizer vulnerabilities).
        # Referrer-Policy set once (previously duplicated with conflicting
        # values).
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS - only add if we're using HTTPS (check via forwarded headers if behind proxy)
        scheme = self._get_request_scheme(request)
        if scheme == "https":
            response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains"

        # Content Security Policy: keep the strict policy everywhere, relax it
        # only for Swagger UI / ReDoc paths when docs are enabled (dev).
        path = request.url.path
        if self.docs_enabled and (
            path == "/docs" or path.startswith("/docs/")
            or path == "/redoc" or path.startswith("/redoc/")
        ):
            response.headers["Content-Security-Policy"] = self.SWAGGER_CSP
        else:
            response.headers["Content-Security-Policy"] = self.csp_policy

        # Additional security headers
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        return response

    def _get_request_scheme(self, request: Request) -> str:
        """Get the request scheme, considering forwarded headers if behind trusted proxy."""
        if not self.trusted_proxy_enabled:
            return request.url.scheme

        # Check forwarded headers for original scheme
        # X-Forwarded-Proto: https,http
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto:
            # Take the first protocol in the list (closest to client)
            proto = forwarded_proto.split(",")[0].strip()
            if proto in ["http", "https"]:
                return proto

        # Fallback to X-Forwarded-Ssl
        forwarded_ssl = request.headers.get("x-forwarded-ssl")
        if forwarded_ssl and forwarded_ssl.lower() in ["on", "1"]:
            return "https"

        # Default to current scheme
        return request.url.scheme