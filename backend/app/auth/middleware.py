from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from backend.app.utils.logger import logger
from backend.app.auth.limiter import login_limiter


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
                from fastapi.responses import JSONResponse
                from backend.app.routes import error_envelope
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
