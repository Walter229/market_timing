import diskcache as dc
import hashlib
import json

# Create a cache object (e.g., for a specific directory)
cache = dc.Cache("cache")

def hash_dict(d):
    """Generates a hash for a dictionary to use as a cache key."""
    dict_str = json.dumps(d, sort_keys=True)  # Convert dictionary to a sorted JSON string
    return hashlib.md5(dict_str.encode()).hexdigest()  # Return an MD5 hash of the string

def disk_cached_write(func):
    """Decorator to cache function results on disk based on the input dictionary."""
    def wrapper(*args, **kwargs):
        # Convert args to a key using a hash
        if args or kwargs:
            # Create a cache key from the args and kwargs (which could include the dict)
            cache_key = hash_dict({"args": args, "kwargs": kwargs})
        else:
            cache_key = func.__name__  # If no args, use function name as a fallback

        # Try to retrieve the result from the cache
        if cache_key in cache:
            return cache[cache_key]

        # If not cached, call the function and store the result
        result = func(*args, **kwargs)
        cache[cache_key] = result
        return result
    return wrapper
    
def disk_cached(func):
    """Decorator to cache function results on disk based on the input dictionary."""
    def wrapper(*args, **kwargs):
        # Convert args to a key using a hash
        if args or kwargs:
            # Create a cache key from the args and kwargs (which could include the dict)
            cache_key = hash_dict({"args": args, "kwargs": kwargs})
        else:
            cache_key = func.__name__  # If no args, use function name as a fallback

        # Try to retrieve the result from the cache
        if cache_key in cache:
            return cache[cache_key]

        # If not cached, call the function
        result = func(*args, **kwargs)
        return result
    
    return wrapper