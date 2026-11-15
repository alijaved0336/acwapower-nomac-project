from django.core.cache import cache


def set_cache(key, value, timeout=300):
    """
    Cache data with key and expiration time.
    """
    cache.set(key, value, timeout)


def get_cache(key):
    """
    Retrieve data from cache by key.
    """
    return cache.get(key)


def cache_query(query_key, fetch_func, timeout=300):
    """
    Cache query result if not already cached.
    """
    data = cache.get(query_key)
    if data is None:
        data = fetch_func()
        cache.set(query_key, data, timeout)
    return data
