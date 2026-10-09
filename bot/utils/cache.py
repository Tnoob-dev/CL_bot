from functools import wraps

from cachetools import TTLCache


def ttl_cache(maxsize: int, ttl: int):
    """Cache truthy results of a one-argument coroutine; misses and errors are never cached."""

    def decorator(func):
        cache = TTLCache(maxsize, ttl)

        @wraps(func)
        async def wrapper(key):
            value = cache.get(key)
            if value is None:
                value = await func(key)
                if value:
                    cache[key] = value
            return value

        wrapper.forget = lambda key: cache.pop(key, None)
        wrapper.clear = cache.clear
        return wrapper

    return decorator
