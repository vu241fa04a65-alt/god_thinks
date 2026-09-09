import time
from typing import Dict, List
from backend.app.utils.logger import logger


class InMemoryLoginRateLimiter:
    """
    Simple thread-safe in-memory rate limiter for tracking login attempts
    and mitigating brute-force attacks.
    """
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        # key (IP or username) -> list of failure timestamps
        self._failures: Dict[str, List[float]] = {}

    def _cleanup_expired(self, key: str, now: float):
        if key in self._failures:
            self._failures[key] = [
                ts for ts in self._failures[key] if now - ts < self.window_seconds
            ]
            if not self._failures[key]:
                del self._failures[key]

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        self._cleanup_expired(key, now)
        attempts = len(self._failures.get(key, []))
        if attempts >= self.max_attempts:
            logger.warning(
                f"[RateLimiter] Rate limit exceeded for key='{key}' ({attempts}/{self.max_attempts} attempts in {self.window_seconds}s)"
            )
            return True
        return False

    def record_failure(self, key: str, username: str = None, client_ip: str = None):
        now = time.time()
        self._cleanup_expired(key, now)
        if key not in self._failures:
            self._failures[key] = []
        self._failures[key].append(now)
        count = len(self._failures[key])
        logger.warning(
            f"[Auth Security] Failed login attempt #{count} for target='{username or key}' from IP='{client_ip or 'unknown'}'"
        )

    def record_success(self, key: str):
        if key in self._failures:
            del self._failures[key]

    def get_rate_limit_headers(self, key: str):
        """
        Returns (limit, remaining, reset_seconds) for rate limit response headers.
        """
        now = time.time()
        self._cleanup_expired(key, now)
        attempts = len(self._failures.get(key, []))
        remaining = max(0, self.max_attempts - attempts)
        if attempts > 0:
            oldest = self._failures[key][0]
            reset_in = max(1, int(self.window_seconds - (now - oldest)))
        else:
            reset_in = self.window_seconds
        return self.max_attempts, remaining, reset_in


login_limiter = InMemoryLoginRateLimiter(max_attempts=5, window_seconds=300)
