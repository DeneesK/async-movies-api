# import datetime
import uuid
import json
from http import HTTPStatus

# import aiohttp
import pytest

from .common import make_bulk_query
from ..settings import test_settings


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'query': 'The Star', 'page_size': 50},
                {'status': HTTPStatus.OK, 'length': 50}
        ),
        (
                {'query': 'Mashed potato', 'page_size': 50},
                {'status': HTTPStatus.NOT_FOUND, 'length': 1}
        )
    ]
)
@pytest.mark.asyncio
async def test_search(es_write_data, query_data, redis_client, make_search_request, expected_answer):

    # 1. Генерируем данные для ES
    items_count = 60
    es_data = [{
        'id': str(uuid.uuid4()),
        'imdb_rating': 8.5,
        'genre': ['Action', 'Sci-Fi'],
        'title': 'The Star',
        'description': 'New World',
        'director': ['Stan'],
        'actors_names': ['Ann', 'Bob'],
        'writers_names': ['Ben', 'Howard'],
        'actors': [
            {'id': '111', 'name': 'Ann'},
            {'id': '222', 'name': 'Bob'}
        ],
        'writers': [
            {'id': '333', 'name': 'Ben'},
            {'id': '444', 'name': 'Howard'}
        ],
    } for _ in range(items_count)]

    # 1.1 Записываем данные в ES
    bulk_query = make_bulk_query(es_data, test_settings.es_index, test_settings.es_id_field)
    await es_write_data(bulk_query)

    # 2. Запрашиваем данные из ES по API

    # session = aiohttp.ClientSession()
    # url = f'http://{test_settings.service_host}:8000/api/v1/films/search'
    # async with session.get(url, params=query_data) as response:
    page_size = expected_answer['length']
    for page_num in range(items_count // page_size):
        query_data1 = query_data.copy()
        from_ = page_num * page_size if page_num > 0 else None
        status, body, headers = await make_search_request('/api/v1/films/search', query_data1, expected_answer,
                                                          items_count, from_)

    #    body = await response.json()
    #    status = response.status
        length = len(body)
    # await session.close()

        # 2. Проверяем ответ

        assert status == expected_answer['status']
        assert length == expected_answer['length']

        # Checking the cache
        redis_key = str((query_data['query'], from_, page_size))
        cache_data_str = await redis_client.get(redis_key)
        cache_data = json.loads(cache_data_str)
        for cache_item_str, response_item in zip(cache_data, body):
            cache_item = json.loads(cache_item_str)
            assert cache_item == response_item
