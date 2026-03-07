"""
Centralised Redis client with an in-memory fallback.

When Redis is reachable the real redis.Redis client is returned.
When Redis is not running (ConnectionError / ResponseError) a thread-safe
FallbackRedis object that mirrors the subset of commands used in this project
is returned instead.  Data is kept only in process memory and is lost on
restart, but all API endpoints continue to work without Redis.
"""

import fnmatch
import logging
import math
import os
import time
from threading import Lock

logger = logging.getLogger(__name__)

import redis as redis_lib

_client = None
_client_lock = Lock()


# ---------------------------------------------------------------------------
# In-memory fallback
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2.0 * R * math.asin(math.sqrt(a))


class FallbackRedis:
    """Thread-safe in-memory substitute for the Redis commands used here."""

    def __init__(self):
        self._strings: dict = {}   # key -> (value, expire_at|None)
        self._sets: dict = {}      # key -> set
        self._geo: dict = {}       # key -> {member: (lon, lat)}
        self._hashes: dict = {}    # key -> {field: value}
        self._lock = Lock()

    # ---- helpers -----------------------------------------------------------

    def _str_alive(self, key: str):
        """Return stored value if key exists and is not expired, else None."""
        item = self._strings.get(key)
        if item is None:
            return None
        val, exp = item
        if exp is not None and time.time() > exp:
            del self._strings[key]
            return None
        return val

    # ---- string commands ---------------------------------------------------

    def get(self, key: str):
        with self._lock:
            return self._str_alive(key)

    def set(self, key: str, value, nx: bool = False, ex=None):
        with self._lock:
            if nx and self._str_alive(key) is not None:
                return None          # key exists, NX prevents overwrite
            exp = time.time() + ex if ex else None
            self._strings[key] = (value, exp)
            return True

    def setex(self, key: str, ttl: int, value):
        with self._lock:
            self._strings[key] = (value, time.time() + ttl)

    def delete(self, *keys: str):
        with self._lock:
            for k in keys:
                self._strings.pop(k, None)
                self._sets.pop(k, None)
                self._geo.pop(k, None)
                self._hashes.pop(k, None)

    def keys(self, pattern: str = "*"):
        with self._lock:
            all_keys = set(self._strings) | set(self._sets) | set(self._geo) | set(self._hashes)
            return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    # ---- set commands ------------------------------------------------------

    def sadd(self, key: str, *values):
        with self._lock:
            self._sets.setdefault(key, set()).update(values)

    def smembers(self, key: str):
        with self._lock:
            return self._sets.get(key, set()).copy()

    # ---- geo commands ------------------------------------------------------

    def geoadd(self, key: str, *args):
        """Accept redis-py style: geoadd(key, (lon, lat, member))."""
        with self._lock:
            geo = self._geo.setdefault(key, {})
            for item in args:
                if isinstance(item, (list, tuple)) and len(item) == 3:
                    lon, lat, member = item
                    geo[member] = (float(lon), float(lat))

    def georadius(self, key: str, lon: float, lat: float, radius: float, unit: str = "km"):
        with self._lock:
            geo = self._geo.get(key, {})
            results = []
            for member, (m_lon, m_lat) in geo.items():
                dist_km = _haversine_km(lat, lon, m_lat, m_lon)
                dist = {"km": dist_km, "m": dist_km * 1000, "mi": dist_km * 0.621371}.get(unit, dist_km)
                if dist <= radius:
                    results.append(member)
            return results

    # ---- hash commands -----------------------------------------------------

    def hset(self, key: str, field: str, value):
        with self._lock:
            self._hashes.setdefault(key, {})[field] = value

    def hget(self, key: str, field: str):
        with self._lock:
            return self._hashes.get(key, {}).get(field)

    # ---- counter commands --------------------------------------------------

    def incr(self, key: str) -> int:
        with self._lock:
            val = self._str_alive(key)
            n = int(val) + 1 if val is not None else 1
            self._strings[key] = (str(n), None)
            return n

    def decr(self, key: str) -> int:
        with self._lock:
            val = self._str_alive(key)
            n = int(val) - 1 if val is not None else -1
            self._strings[key] = (str(n), None)
            return n

    # ---- misc --------------------------------------------------------------

    def ping(self):
        return True


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

def get_redis():
    """Return a live Redis client or a FallbackRedis if Redis is unreachable."""
    global _client
    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            candidate = redis_lib.Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=2,
            )
            candidate.ping()
            _client = candidate
            logger.info("Connected to Redis | url=%s", url)
        except Exception:
            logger.warning(
                "Redis is unavailable — using in-memory fallback. "
                "Data will not persist across restarts. "
                "Start Redis on localhost:6379 for full persistence."
            )
            _client = FallbackRedis()
            logger.info("FallbackRedis (in-memory) initialised")

        return _client
