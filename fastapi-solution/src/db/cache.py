
class Cache:
    async def get(self, key):
        raise NotImplementedError()

    async def set(self, key, objects, expire=None):
        raise NotImplementedError()


