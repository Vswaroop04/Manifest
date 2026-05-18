import logging
from typing import TypeVar, Callable
from django.core.cache import cache

logger = logging.getLogger("app")

T = TypeVar("T")


def cached_or_calculate(key: str, build: Callable[[], T], ttl: int) -> T:
    value: T | None = cache.get(key)
    if value is not None:
        return value
    value = build()
    cache.set(key, value, ttl)
    return value
