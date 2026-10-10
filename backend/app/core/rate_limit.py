import time
from collections import defaultdict

from fastapi import HTTPException, status

_buckets: dict[str, list[float]] = defaultdict(list)


def enforce_rate_limit(key: str, limit: int, window_seconds: int = 60) -> None:
    if limit <= 0:
        return
    now = time.monotonic()
    bucket = _buckets[key]
    bucket[:] = [stamp for stamp in bucket if now - stamp < window_seconds]
    if len(bucket) >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
    bucket.append(now)


def reset_rate_limits() -> None:
    _buckets.clear()
