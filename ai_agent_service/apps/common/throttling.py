"""Rate limiting dependencies for FastAPI endpoints.

Uses Redis when configured (distributed, multi-instance safe), and falls back to
in-memory limiting for local development.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Depends, Request
from redis import Redis
from redis.exceptions import RedisError

from apps.common.authentication import require_api_key
from apps.common.exceptions import RateLimitedServiceError
from core.settings import get_settings

_SECONDS_BY_UNIT = {
    "s": 1,
    "sec": 1,
    "second": 1,
    "m": 60,
    "min": 60,
    "minute": 60,
    "h": 3600,
    "hour": 3600,
    "d": 86400,
    "day": 86400,
}


@dataclass
class ParsedRate:
    limit: int
    window_seconds: int


def parse_rate(rate: str) -> ParsedRate:
    try:
        limit_str, unit = rate.split("/", maxsplit=1)
        limit = int(limit_str)
    except ValueError as exc:
        raise ValueError(f"Invalid rate limit format: {rate}") from exc

    unit = unit.lower().strip()
    if unit not in _SECONDS_BY_UNIT:
        raise ValueError(f"Unsupported rate unit: {unit}")

    return ParsedRate(limit=limit, window_seconds=_SECONDS_BY_UNIT[unit])


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, parsed_rate: ParsedRate) -> tuple[bool, int]:
        now = time.time()

        with self._lock:
            queue = self._hits[key]
            cutoff = now - parsed_rate.window_seconds
            while queue and queue[0] <= cutoff:
                queue.popleft()

            if len(queue) >= parsed_rate.limit:
                retry_after = max(1, int(parsed_rate.window_seconds - (now - queue[0])))
                return False, retry_after

            queue.append(now)
            return True, 0


class RedisRateLimiter:
    def __init__(self, redis_url: str) -> None:
        self._client = Redis.from_url(redis_url, decode_responses=True)

    def hit(self, key: str, parsed_rate: ParsedRate) -> tuple[bool, int]:
        now_ms = int(time.time() * 1000)
        window_ms = parsed_rate.window_seconds * 1000
        cutoff_ms = now_ms - window_ms
        redis_key = f"ratelimit:{key}"
        member = f"{now_ms}-{time.time_ns()}"

        pipeline = self._client.pipeline()
        pipeline.zremrangebyscore(redis_key, 0, cutoff_ms)
        pipeline.zadd(redis_key, {member: now_ms})
        pipeline.zcard(redis_key)
        pipeline.expire(redis_key, parsed_rate.window_seconds)
        _, _, count, _ = pipeline.execute()

        if count > parsed_rate.limit:
            oldest = self._client.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                oldest_ms = int(oldest[0][1])
                retry_after = max(1, int((window_ms - (now_ms - oldest_ms)) / 1000))
            else:
                retry_after = 1
            return False, retry_after

        return True, 0


class RateLimiter:
    def __init__(self) -> None:
        self._fallback = InMemoryRateLimiter()
        settings = get_settings()
        self._redis: RedisRateLimiter | None = None
        if settings.redis_url:
            try:
                self._redis = RedisRateLimiter(settings.redis_url)
            except Exception:
                self._redis = None

    def hit(self, key: str, rate: str) -> tuple[bool, int]:
        parsed = parse_rate(rate)
        if self._redis is None:
            return self._fallback.hit(key=key, parsed_rate=parsed)

        try:
            return self._redis.hit(key=key, parsed_rate=parsed)
        except RedisError:
            return self._fallback.hit(key=key, parsed_rate=parsed)


_RATE_LIMITER = RateLimiter()


def throttle(scope: str):
    async def _enforce(request: Request, _: str = Depends(require_api_key)) -> None:
        settings = get_settings()
        rate = settings.rate_limits.get(scope, "60/min")
        request_id = getattr(request.state, "request_id", "")
        ip = request.client.host if request.client else "unknown"
        key = f"{scope}:{ip}"

        allowed, retry_after = _RATE_LIMITER.hit(key=key, rate=rate)
        if not allowed:
            raise RateLimitedServiceError(
                message=f"Too many requests. Retry after {retry_after} seconds.",
                details=[{"retry_after": retry_after, "scope": scope, "request_id": request_id}],
            )

    return _enforce
