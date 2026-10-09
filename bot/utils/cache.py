from functools import wraps
from threading import Lock

from cachetools import TTLCache


def ttl_cache(maxsize: int, ttl: int):
    """Cache truthy results of a one-argument function; misses and errors are never cached."""

    def decorator(func):
        cache = TTLCache(maxsize, ttl)
        lock = Lock()

        @wraps(func)
        def wrapper(key):
            with lock:
                value = cache.get(key)
            if value is None:
                value = func(key)
                if value:
                    with lock:
                        cache[key] = value
            return value

        def forget(key) -> None:
            with lock:
                cache.pop(key, None)

        def clear() -> None:
            with lock:
                cache.clear()

        wrapper.forget = forget
        wrapper.clear = clear
        return wrapper

    return decorator
