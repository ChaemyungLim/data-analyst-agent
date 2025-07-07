import redis
from redis.asyncio import Redis
from .config import REDIS_CONFIG

redis_client = redis.Redis(**REDIS_CONFIG)
async_redis_client = redis.asyncio.Redis(**REDIS_CONFIG)