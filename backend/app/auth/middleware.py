import time
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from backend.app.config import settings
from backend.app.utils.logger import logger
from backend.app.auth.limiter import login_limiter
from backend.app.routes import error_envelope


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enforces HTTPS in production, injects HSTS, and attaches defensive HTTP headers.
    """
    async def dispatch(self, request: Request, call_next):
        is_prod = settings.ENVIRONMENT.lower() == "production"

        # 1. Enforce HTTPS in production or if explicitly configured
        if is_prod or settings.ENFORCE_HTTPS:
            forwarded_proto = request.headers.get("x-forwarded-proto", "")
            if request.url.scheme != "https" and forwarded_proto != "https":
                # Redirect insecure HTTP requests to HTTPS
                https_url = request.url.replace(scheme="https")
                logger.info(f"[HTTPS Enforcement] Redirecting insecure request to: {https_url}")
                return RedirectResponse(url=str(https_url), status_code=301)

        response = await call_next(request)

        # 2. Strict-Transport-Security (HSTS)
        if is_prod or settings.ENFORCE_HTTPS:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # 3. Defensive Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"

        return response


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket / sliding window rate limiting per client IP to mitigate DoS and credential stuffing.
    """
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._ip_history: Dict[str, List[float]] = {}

    def _cleanup_and_check(self, client_ip: str, limit: int) -> bool:
        now = time.time()
        if client_ip not in self._ip_history:
            self._ip_history[client_ip] = []

        # Retain timestamps within the active 60s sliding window
        self._ip_history[client_ip] = [
            ts for ts in self._ip_history[client_ip] if now - ts < self.window_seconds
        ]

        if len(self._ip_history[client_ip]) >= limit:
            return False

        self._ip_history[client_ip].append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Health probes and Prometheus scrape endpoints are exempted from rate limits
        if path in ("/health", "/ready", "/metrics", "/api/v1/health", "/api/v1/ready", "/api/v1/metrics"):
            return await call_next(request)

        # Stricter limit for resource-intensive file uploads
        effective_limit = 20 if path.endswith("/reports/upload") else self.requests_per_minute

        if not self._cleanup_and_check(client_ip, effective_limit):
            logger.warning(f"[RateLimit] Client IP='{client_ip}' exceeded rate limit on {request.method} {path}")
            response = JSONResponse(
                status_code=429,
                content=error_envelope(
                    message=f"Too many requests. Rate limit is {effective_limit} requests/minute. Please slow down.",
                    code=429
                )
            )
            response.headers["Retry-After"] = "60"
            return response

        response = await call_next(request)
        return response


class AuthAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log failed authentication attempts (401/403) and monitor login rate limits.
    """
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # If it's a login route, verify IP rate limit before proceeding
        if path.endswith("/auth/login") and request.method == "POST":
            if login_limiter.is_rate_limited(client_ip):
                logger.warning(f"[RateLimit Intercept] Blocked login attempt from IP='{client_ip}'")
                return JSONResponse(
                    status_code=429,
                    content=error_envelope(
                        message="Too many failed login attempts. Please try again after 5 minutes.",
                        code=429
                    )
                )

        response = await call_next(request)

        # Inject standardized rate limit headers
        limit_val, remaining_val, reset_val = login_limiter.get_rate_limit_headers(client_ip)
        response.headers["X-RateLimit-Limit"] = str(limit_val)
        response.headers["X-RateLimit-Remaining"] = str(remaining_val)
        response.headers["X-RateLimit-Reset"] = str(reset_val)

        # Audit log failed authentication and authorization events
        if response.status_code in (401, 403):
            logger.warning(
                f"[Auth Audit] Unauthorized access (HTTP {response.status_code}) on {request.method} {path} from IP='{client_ip}'"
            )

        return response
