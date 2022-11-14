import json
from functools import lru_cache
from typing import Hashable

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import parse_obj_as

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person
from services.cache_redis import RedisCache
from services.common import DBObjectService, Key
from services.search_elastic import ElasticSearch

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class PersonService(DBObjectService):
    async def get_by_id(self, id_: Key) -> list[Person]:
        persons = await self._persons_from_cache(id_)
        if not persons:
            persons = await self._get_persons_from_elastic(id_)
            if not persons:
                return []
            await self._put_persons_to_cache(key=id_, persons=persons)

        return persons

    async def _get_persons_from_elastic(self, id_: Key) -> list[Person]:
        try:
            doc = await self.search.get_by_id(id_)
        except NotFoundError:
            return []
        result = Person(**doc['_source'])
        return [result]

    async def get_persons_by_query(self, query: Key,
                                   from_:int=None, page_size:int=None,
                                   sort_fields:list|None=None,
                                   filter_items:list|None=None) -> list[Person]:
        """
        Метод запрашивает из ES список персон, по запросу введеному в поиске
        """
        def to_tuple(arg):
            return None if arg is None else tuple(arg)
        redis_key = hash((query, to_tuple(sort_fields), to_tuple(filter_items), from_, page_size))
        persons = await self._persons_from_cache(redis_key)
        if persons is None:
            persons = await self._get_persons_list_from_elastic(query,
                                                                from_, page_size,
                                                                sort_fields, filter_items)
            await self._put_persons_to_cache(redis_key, persons)
        if not persons:
            return []
        return persons

    async def _get_persons_list_from_elastic(self, query: str,
                                             from_:int=None, page_size:int=None,
                                             sort_fields:list|None=None,
                                             filter_items:list|None=None) -> list[Person]:

        results = await self.search.search(query, from_, page_size, sort_fields, filter_items)
        films = [Person(**r) for r in results]
        return films

    async def _persons_from_cache(self, key : Hashable) -> list[Person]|None:
        """None - значит, нет данных в кеше, пустой список - это валидное содержимое."""
        data = await self.cache.get(key)
        if data is None:
            return None

        data_dict = json.loads(data)
        dict_obj_2 = [json.loads(itm) for itm in data_dict]
        persons = parse_obj_as(list[Person], dict_obj_2)
        return persons

    async def _put_persons_to_cache(self, key: Hashable, persons: list[Person]):
        # TODO use keywords for different classes

        assert isinstance(persons, list)
        persons_dict = [person.json() for person in persons]
        await self.cache.set(key, json.dumps(persons_dict), expire=PERSON_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    cache = RedisCache(redis)
    search = ElasticSearch(elastic, 'persons')
    return PersonService(cache, search)