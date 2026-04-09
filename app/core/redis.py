import redis
from app.core.config import settings

# Initialize redis client
redis_client = None

try:
    if settings.REDIS_URL:
        # For Upstash/Production
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
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
    print("✅ Redis connection established.")
except Exception as e:
    print(f"⚠️ Redis not available ({e}). Falling back to database-only mode.")
    redis_client = None

def get_redis():
    """Returns the redis client if available, else None."""
    return redis_client
