import json
from functools import lru_cache
from typing import Optional, Hashable

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import parse_obj_as

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from db.cache_redis import RedisCache
from services.common import DBObjectService
from db.search_elastic import ElasticSearch

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


# FilmService содержит бизнес-логику по работе с фильмами. 
# Никакой магии тут нет. Обычный класс с обычными методами. 
# Этот класс ничего не знает про DI — максимально сильный и независимый.
class FilmService(DBObjectService):
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await self._films_from_cache(film_id)
        if not film:
            film = await self._find_film(film_id)
            if not film:
                return None
            await self._put_films_to_cache(key=film.id, films=film)

        return film

    async def _find_film(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.search.get_by_id(film_id)
        except NotFoundError:
            return None
        return Film(**doc['_source'])

    async def get_films_by_query(self, query: str, from_: int=None, page_size:int=None) -> list:
        """
        Метод запрашивает из ES список фильмов, по запросу введеному в поиске
        """
        redis_key = hash((query, from_, page_size))
        films = await self._films_from_cache(redis_key)
        if not films:
            films = await self._search_films(query, from_, page_size)
            if not films:
                films = []
            await self._put_films_to_cache(key=redis_key, films=films)
        return films

    async def _search_films(self, query: str, from_:int=None,
                            page_size:int=None) -> list:
        results = await self.search.search(query, from_, page_size)
        films = [Film(**r) for r in results]
        return films

    async def _films_from_cache(self, key: Hashable) -> Optional[Film] | list:
        # noinspection PyTypeChecker
        data = await self.cache.get(key)
        if not data:
            return None

        data_dict=json.loads(data)
        if isinstance(data_dict, list):
            dict_obj_2 = [json.loads(itm) for itm in data_dict]
            films = parse_obj_as(list[Film], dict_obj_2)
            return films
        else:
            film = Film.parse_raw(data)
            return film

    async def _put_films_to_cache(self, key: Hashable, films: Film | list):
        if isinstance(films, list):
            films = [f.json() for f in films if f]
            # noinspection PyTypeChecker
            await self.cache.set(key, json.dumps(films), expire=FILM_CACHE_EXPIRE_IN_SECONDS)
        else:    
            # noinspection PyTypeChecker
            await self.cache.set(key, films.json(), expire=FILM_CACHE_EXPIRE_IN_SECONDS)

@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    cache = RedisCache(redis)
    search = ElasticSearch(elastic, 'movies')
    return FilmService(cache, search)
