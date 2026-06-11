import threading
import time
import hashlib
from typing import Optional, Any
from backend.config import settings

class InMemoryCache:
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key in self._cache:
                val, expires_at = self._cache[key]
                if expires_at is None or expires_at > time.time():
                    return val
                else:
                    del self._cache[key]
            return None

    def set(self, key: str, value: str, ttl: int = None) -> None:
        with self._lock:
            expires_at = time.time() + ttl if ttl else None
            self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]

# Try connecting to Redis if URL provided
redis_client = None
if settings.redis_url:
    try:
        import redis
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        print("Connected to Redis successfully.")
    except Exception as e:
        print(f"Redis not available, falling back to In-Memory cache. Detail: {e}")
        redis_client = None

in_mem_cache = InMemoryCache()

def cache_get(key: str) -> Optional[str]:
    if redis_client:
        try:
            return redis_client.get(key)
        except Exception:
            return in_mem_cache.get(key)
    return in_mem_cache.get(key)

def cache_set(key: str, value: str, ttl: int = None) -> None:
    if redis_client:
        try:
            redis_client.set(key, value, ex=ttl)
            return
        except Exception:
            pass
    in_mem_cache.set(key, value, ttl)

def cache_delete(key: str) -> None:
    if redis_client:
        try:
            redis_client.delete(key)
            return
        except Exception:
            pass
    in_mem_cache.delete(key)

def get_query_hash(role: str, query: str) -> str:
    hasher = hashlib.sha256()
    hasher.update(f"{role}:{query}".encode('utf-8'))
    return f"query_cache:{hasher.hexdigest()}"
