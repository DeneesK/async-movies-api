# import datetime
# import uuid
import json
from http import HTTPStatus

import aiohttp
import pytest


from ..settings import test_settings
from .common import make_bulk_query


# def get_es_films_bulk_query(query_data, es_index, es_id_field, items_count):
#     # 1. Генерируем данные для ES
#     es_data = [{
#         'id': str(uuid.uuid4()),
#         'imdb_rating': 8.5,
#         'genre': ['Action', 'Sci-Fi'],
#         'title': query_data['search'],
#         'description': 'New World',
#         'director': ['Stan'],
#         'actors_names': ['Ann', 'Bob'],
#         'writers_names': ['Ben', 'Howard'],
#         'actors': [
#             {'id': '111', 'name': 'Ann'},
#             {'id': '222', 'name': 'Bob'}
#         ],
#         'writers': [
#             {'id': '333', 'name': 'Ben'},
#             {'id': '444', 'name': 'Howard'}
#         ],
#         'created_at': datetime.datetime.now().isoformat(),
#         'updated_at': datetime.datetime.now().isoformat(),
#         'film_work_type': 'movie'
#     } for _ in range(items_count)]
#     return make_bulk_query(es_data, es_index, es_id_field)


@pytest.mark.parametrize(
    'checking_id, expected_answer',
    [
        (
                '7e0ad51a-332f-4ff0-b8b9-9b5308836cb1',
                {'status': HTTPStatus.OK, 'result': 'The Star'}
        ),
        (
                '1111111111',
                {'status': HTTPStatus.NOT_FOUND, 'result': 'film not found'}
        )
    ]
)
@pytest.mark.asyncio
async def test_film(es_write_data, redis_client, checking_id, expected_answer):

    # 1. Генерируем данные для ES
    film_id = '7e0ad51a-332f-4ff0-b8b9-9b5308836cb1'
    es_data = [{
        'id': film_id,
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
    }]
    bulk_query = make_bulk_query(es_data, 'movies', 'id')
    # 1.1 Записываем данные в ES

    await es_write_data(bulk_query)  # , 1, 'movies'

    # 2. Запрашиваем данные из ES по API

    session = aiohttp.ClientSession()
    url = f'http://{test_settings.service_host}:8000/api/v1/films/film/{checking_id}'
    async with session.get(url) as response:
        body = await response.json()
        status = response.status
        result = body.get('title', 'film not found')
    await session.close()

    # 2. Проверяем ответ

    assert status == expected_answer['status']
    assert result == expected_answer['result']

    # Checking the cache.
    cache_data_str = await redis_client.get(checking_id)
    if expected_answer['status'] == HTTPStatus.OK:
        cache_data = json.loads(cache_data_str)
        assert cache_data == body
    else:
        assert cache_data_str is None
