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
from services.common import DBObjectService, Key

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class PersonService(DBObjectService):
    async def get_by_id(self, search_string: Key) -> list[Person]:
        persons = await self._persons_from_cache(search_string)
        if not persons:
            persons = await self._get_persons_from_elastic(search_string)
            if not persons:
                return []
            await self._put_persons_to_cache(key=search_string, persons=persons)

        return persons

    async def _get_persons_from_elastic(self, search_string: Key) -> list[Person]:
        try:
            doc = await self.elastic.get('persons', search_string)
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
        body = {"query": {'bool': {'must': {"match": {"name": {"query": query}}}}},
                # an example: "sort": [{'name.raw': 'asc'}]
                }
        if sort_fields:
            body["sort"] = [{sort_field: 'asc'} for sort_field in sort_fields]
        if filter_items:
            body["query"]["bool"]["filter"] = [{'term': {"name": filter_item}} for filter_item in filter_items]
        if from_:
            body['from'] = from_
        if page_size:
            body['size'] = page_size
        try:
            result = await self.elastic.search(index='persons', body=body)
        except NotFoundError:
            return []  # None?
        films = [Person(**f['_source']) for f in result['hits']['hits']]
        return films

    async def _persons_from_cache(self, key : Hashable) -> list[Person]|None:
        """None - значит, нет данных в кеше, пустой список - это валидное содержимое."""
        data = await self.redis.get(key)
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
        await self.redis.set(key, json.dumps(persons_dict), ex=PERSON_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)