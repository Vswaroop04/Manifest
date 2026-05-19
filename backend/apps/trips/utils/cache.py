import logging
from typing import TypeVar, Callable
from django.core.cache import cache

logger = logging.getLogger("app")

T = TypeVar("T")


def cached_or_calculate(key: str, build: Callable[[], T], ttl: int) -> T:
    try:
        value: T | None = cache.get(key)
        if value is not None:
            return value
    except Exception as exc:
        logger.warning("Cache read failed, skipping cache", extra={"key": key, "error": str(exc)})
        return build()

    value = build()

    try:
        cache.set(key, value, ttl)
    except Exception as exc:
        logger.warning("Cache write failed", extra={"key": key, "error": str(exc)})

    return value
