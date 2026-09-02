import redis
from app.core.config import settings

# Initialize redis client
redis_client = None

BALANCE_CACHE_PATTERNS = ("user_balances:*", "group_balances:*")


def clear_balance_cache(client) -> int:
    """Remove balance entries that may have survived a Redis outage."""
    deleted = 0
    for pattern in BALANCE_CACHE_PATTERNS:
        keys = list(client.scan_iter(match=pattern, count=100))
        if keys:
            deleted += client.delete(*keys)
    return deleted

try:
    if settings.REDIS_URL:
        # For Upstash/Production - Clean the URL to handle trailing spaces or quotes from dashboard copy-pastes
        url = settings.REDIS_URL.strip().strip('"').strip("'")
        redis_client = redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_timeout=2.0, # Don't block the app for too long
            retry_on_timeout=True
        )
    else:
        # Fallback for local dev
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_timeout=2.0
        )
    # Ping to verify connection immediately
    redis_client.ping()
    cleared_keys = clear_balance_cache(redis_client)
    print(f"✅ Redis connection established. Cleared {cleared_keys} stale balance cache entries.")
except Exception as e:
    print(f"⚠️ Redis not available ({e}). Falling back to database-only mode.")
    redis_client = None

def get_redis():
    """Returns the redis client if available, else None."""
    return redis_client
