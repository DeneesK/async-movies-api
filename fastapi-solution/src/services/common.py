from aioredis import Redis
from elasticsearch import AsyncElasticsearch

Key = str  # An id of search phrase, to look in the cache.

class DBObjectService:
    keyword = None  # must inherit

    _template = { "query":
        { "query_string":
            { "query": None } } }

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic