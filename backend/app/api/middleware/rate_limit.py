# app/api/middleware/rate_limit.py
"""
Rate limiting middleware using token bucket algorithm.
"""
import logging
import time
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions import http_exception_handler
from app.api.middleware.auth import is_path_exempt
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware.

    Features:
    - Configurable requests per minute and burst capacity
    - Per-method rate limiting (separate counters for GET, POST, etc.)
    - Exempt paths (health checks, docs, etc.)
    - Client identification by IP address
    """

    def __init__(self, app):
        super().__init__(app)
        self.enabled = getattr(settings, 'RATE_LIMIT_ENABLED', False)
        self.requests_per_minute = getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 60)
        self.burst = getattr(settings, 'RATE_LIMIT_BURST', 10)
        self.per_method = getattr(settings, 'RATE_LIMIT_PER_METHOD', True)
        self.exempt_paths = set(getattr(settings, 'RATE_LIMIT_EXEMPT_PATHS', [
            "/", "/health", "/docs", "/redoc", "/openapi.json", "/debug/env"
        ]))
        # SEC-15: cap the in-memory bucket dict so a flood of spoofed client
        # keys (e.g. via X-Forwarded-For) cannot grow memory without bound.
        self.max_clients = getattr(settings, 'RATE_LIMIT_MAX_CLIENTS', 10000)

        # Token buckets: {client_key: (tokens, last_update_time)}
        self.buckets: Dict[str, Tuple[float, float]] = {}

        # Refill rate: tokens per second
        self.refill_rate = self.requests_per_minute / 60.0

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Check if path is exempt
        if self._is_path_exempt(request.url.path):
            return await call_next(request)

        # Get client identifier
        client_key = self._get_client_key(request)

        # Check rate limit
        if not self._allow_request(client_key):
            logger.warning(
                f"Rate limit exceeded for client {client_key} on {request.method} {request.url.path}"
            )
            # Return the error response directly instead of raising: an
            # HTTPException raised inside a BaseHTTPMiddleware bypasses the
            # ExceptionMiddleware and is turned into a 500 by
            # ServerErrorMiddleware, so a raised 429 never reaches the client.
            return await http_exception_handler(
                request,
                HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + 60))
                    }
                )
            )

        # Add rate limit headers to response
        response = await call_next(request)
        remaining, reset_time = self._get_remaining_quota(client_key)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(remaining))
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))

        return response

    def _is_path_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting.

        Exact match only (with trailing-slash tolerance), never prefix match.
        RC9.5: the former ``path.startswith(exempt_path)`` logic meant the
        default ``"/"`` entry exempted every route, disabling enforcement.
        """
        return is_path_exempt(path, self.exempt_paths)

    def _get_client_key(self, request: Request) -> str:
        """Generate client key for rate limiting."""
        # Use X-Forwarded-For if behind trusted proxy, otherwise use direct client
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for and getattr(settings, 'TRUSTED_PROXY_ENABLED', False):
            # Take the first IP in the forwarded-for list (original client)
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Include method in key if per-method limiting is enabled
        if self.per_method:
            return f"{client_ip}:{request.method}"
        return client_ip

    def _allow_request(self, client_key: str) -> bool:
        """Check if request is allowed based on token bucket algorithm."""
        now = time.time()

        # Enforce the bucket-dict bound before inserting a new client key.
        # Only runs when a brand-new key would push the dict past the cap and
        # evicts the idle client (fully refilled, last seen longest ago), so
        # active clients' quotas are unaffected.
        if client_key not in self.buckets and len(self.buckets) >= self.max_clients:
            self._evict_idle_client(now)

        tokens, last_update = self.buckets.get(client_key, (self.burst, now))

        # Add tokens based on time passed
        time_passed = now - last_update
        tokens = min(self.burst, tokens + (time_passed * self.refill_rate))

        # Check if request can be served
        if tokens >= 1:
            tokens -= 1
            self.buckets[client_key] = (tokens, now)
            return True
        else:
            # Not enough tokens, update timestamp anyway
            self.buckets[client_key] = (tokens, now)
            return False

    def _evict_idle_client(self, now: float) -> None:
        """Evict one idle client to keep the bucket dict bounded.

        Prefer a client whose bucket has fully refilled (tokens == burst, i.e.
        they have not consumed for at least one full refill window). If no such
        client exists, fall back to the single least-recently-active client.
        """
        idle = None
        idle_seen = None
        for key, (tokens, last_update) in self.buckets.items():
            if tokens >= self.burst:
                if idle_seen is None or last_update < idle_seen:
                    idle = key
                    idle_seen = last_update
        if idle is not None:
            del self.buckets[idle]
            return
        # No fully-refilled client: drop the single least-recently-active one.
        oldest = None
        oldest_seen = None
        for key, (_, last_update) in self.buckets.items():
            if oldest_seen is None or last_update < oldest_seen:
                oldest = key
                oldest_seen = last_update
        if oldest is not None:
            del self.buckets[oldest]

    def _get_remaining_quota(self, client_key: str) -> tuple[float, float]:
        """Get remaining tokens and reset time for client."""
        now = time.time()
        tokens, last_update = self.buckets.get(client_key, (self.burst, now))

        # Add tokens based on time passed
        time_passed = now - last_update
        tokens = min(self.burst, tokens + (time_passed * self.refill_rate))

        # Calculate time until bucket is full (or until we have at least 1 token)
        if tokens >= 1:
            # We have tokens available now
            return tokens, now
        else:
            # Calculate time to get 1 token
            time_to_wait = (1 - tokens) / self.refill_rate
            return 0, now + time_to_wait