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

class UpstashRESTClient:
    def __init__(self, hostname: str, token: str):
        self.base_url = f"https://{hostname}"
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _run_cmd(self, cmd: list) -> Any:
        import urllib.request
        import json
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(cmd).encode('utf-8'),
            headers=self.headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.getcode() == 200:
                res = json.loads(response.read().decode('utf-8'))
                return res.get("result")
            else:
                raise Exception(f"HTTP Status {response.getcode()}")

    def ping(self) -> bool:
        try:
            return self._run_cmd(["PING"]) == "PONG"
        except Exception:
            return False

    def get(self, key: str) -> Optional[str]:
        # Return string key value, similar to redis-py
        val = self._run_cmd(["GET", key])
        return val

    def set(self, key: str, value: str, ex: int = None) -> None:
        cmd = ["SET", key, value]
        if ex is not None:
            cmd.extend(["EX", str(ex)])
        self._run_cmd(cmd)

    def delete(self, key: str) -> None:
        self._run_cmd(["DEL", key])

# Try connecting to Redis if URL provided
redis_client = None
if settings.redis_url:
    # 1. Try TCP Connection first
    try:
        import redis
        redis_client = redis.from_url(
            settings.redis_url, 
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0
        )
        redis_client.ping()
        print("Connected to Redis via TCP successfully.")
    except Exception as e_tcp:
        print(f"Redis TCP connection failed: {e_tcp}. Attempting REST fallback...")
        redis_client = None
        
        # 2. Try Upstash REST fallback if host is upstash
        from urllib.parse import urlparse
        try:
            parsed = urlparse(settings.redis_url)
            hostname = parsed.hostname
            password = parsed.password
            if hostname and ("upstash.io" in hostname or "upstash" in hostname):
                rest_client = UpstashRESTClient(hostname, password)
                if rest_client.ping():
                    redis_client = rest_client
                    print("Connected to Upstash Redis via REST API successfully.")
                else:
                    print("Upstash REST ping did not return PONG.")
            else:
                print("Not an Upstash host, skipping REST API fallback.")
        except Exception as e_rest:
            print(f"Upstash REST fallback failed: {e_rest}")
            redis_client = None

if redis_client is None:
    print("Redis not available, falling back to In-Memory cache.")

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

