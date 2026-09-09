import time
import json
import functools
import threading
from typing import Any, Optional, Callable
from collections import OrderedDict

from backend.app.config import settings
from backend.app.utils.logger import logger

class SimpleLRUCache:
    """
    Thread-safe in-memory LRU cache with TTL expiration.
    """
    def __init__(self, capacity: int = 500, default_ttl: int = 60):
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            val, expire_time = self._cache[key]
            if time.time() > expire_time:
                del self._cache[key]
                return None
            # Move to end to mark as recently used
            self._cache.move_to_end(key)
            return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        expire_time = time.time() + ttl
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.capacity:
                # Evict oldest
                self._cache.popitem(last=False)
            self._cache[key] = (value, expire_time)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


class CacheManager:
    """
    Unified cache manager that uses Redis if configured & reachable,
    otherwise falls back to SimpleLRUCache.
    """
    def __init__(self):
        self._lru = SimpleLRUCache()
        self._redis_client = None
        self._use_redis = False
        self._init_redis()

    def _init_redis(self):
        if settings.REDIS_URL:
            try:
                import redis
                client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
                # Test ping
                client.ping()
                self._redis_client = client
                self._use_redis = True
                logger.info(f"Connected to Redis cache at {settings.REDIS_URL}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis at {settings.REDIS_URL} ({e}). Falling back to in-memory LRU cache.")
                self._redis_client = None
                self._use_redis = False

    @property
    def is_redis_active(self) -> bool:
        return self._use_redis and self._redis_client is not None

    def get(self, key: str) -> Optional[Any]:
        if self.is_redis_active:
            try:
                data = self._redis_client.get(key)
                if data is not None:
                    return json.loads(data)
                return None
            except Exception as e:
                logger.warning(f"Redis get error for {key}: {e}. Reading from LRU fallback.")
                return self._lru.get(key)
        return self._lru.get(key)

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        if self.is_redis_active:
            try:
                data = json.dumps(value)
                self._redis_client.setex(key, ttl, data)
                return
            except Exception as e:
                logger.warning(f"Redis set error for {key}: {e}. Writing to LRU fallback.")
                self._lru.set(key, value, ttl=ttl)
                return
        self._lru.set(key, value, ttl=ttl)

    def delete(self, key: str) -> None:
        if self.is_redis_active:
            try:
                self._redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        self._lru.delete(key)

    def clear(self) -> None:
        if self.is_redis_active:
            try:
                self._redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis flush error: {e}")
        self._lru.clear()


cache_manager = CacheManager()
