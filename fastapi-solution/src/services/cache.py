from aioredis import Redis


class Cache:
    async def get(self, key):
        raise NotImplementedError()

    async def set(self, key, objects, expire=None):
        raise NotImplementedError()


class RedisCache(Cache):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key):
        return await self.redis.get(key)

    async def set(self, key, objects, expire=None):
        await self.redis.set(key, objects, ex=expire)