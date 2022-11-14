from aioredis import Redis

from services.cache import Cache


class RedisCache(Cache):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key):
        return await self.redis.get(key)

    async def set(self, key, objects, expire=None):
        await self.redis.set(key, objects, ex=expire)