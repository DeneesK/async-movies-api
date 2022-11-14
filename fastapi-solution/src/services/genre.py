import json
from functools import lru_cache
from typing import Hashable

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import parse_obj_as

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre
from services.cache_redis import RedisCache
from services.common import DBObjectService, Key
from services.search_elastic import ElasticSearch

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService(DBObjectService):
    async def get_by_id(self, id_: Key) -> list[Genre]:
        genres = await self._genres_from_cache(id_)
        if not genres:
            genres = await self._get_genres_from_elastic(id_)
            if not genres:
                return []
            await self._put_genres_to_cache(key=id_, genres=genres)

        return genres

    async def _get_genres_from_elastic(self, id_: Key) -> list[Genre]:
        try:
            doc = await self.search.get_by_id(id_)
        except NotFoundError:
            return []
        result = Genre(**doc['_source'])
        return [result]

    async def get_genres_by_query(self, query: Key,
                                  from_:int=None, page_size:int=None,
                                  sort_fields:list|None=None,
                                  filter_items: list | None = None) -> list[Genre]:
        """
        Метод запрашивает из ES список персон, по запросу введеному в поиске
        """
        def to_tuple(arg):
            return None if arg is None else tuple(arg)
        redis_key = hash((query, to_tuple(sort_fields), to_tuple(filter_items), from_, page_size))
        genres = await self._genres_from_cache(redis_key)
        if genres is None:
            genres = await self._get_genres_list_from_elastic(query,
                                                              from_, page_size,
                                                              sort_fields, filter_items)
            await self._put_genres_to_cache(redis_key, genres)
        if not genres:
            return []
        return genres

    async def _get_genres_list_from_elastic(self, query: str,
                                            from_:int=None, page_size:int=None,
                                            sort_fields:list|None=None,
                                            filter_items: list | None = None
                                            ) -> list[Genre]:

        results = await self.search.search(query, from_, page_size, sort_fields, filter_items)

        films = [Genre(**r) for r in results]
        return films

    async def _genres_from_cache(self, key : Hashable) -> list[Genre]|None:
        """None - значит, нет данных, пустой список - валидное содержимое."""
        data = await self.cache.get(key)
        if data is None:
            return None

        data_dict = json.loads(data)
        dict_obj_2 = [json.loads(itm) for itm in data_dict]
        persons = parse_obj_as(list[Genre], dict_obj_2)
        return persons

    async def _put_genres_to_cache(self, key: Hashable, genres: list[Genre]):
        # TODO use keywords for different classes

        assert isinstance(genres, list)
        genres_dict = [genre.json() for genre in genres]
        await self.cache.set(key, json.dumps(genres_dict), expire=GENRE_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    cache = RedisCache(redis)
    search = ElasticSearch(elastic, 'genres')
    return GenreService(cache, search)