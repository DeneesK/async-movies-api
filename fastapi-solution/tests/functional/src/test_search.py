import datetime
import uuid
from http import HTTPStatus

import aiohttp
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
async def test_search(es_write_data, query_data, expected_answer):

    # 1. Генерируем данные для ES

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
        #'created_at': datetime.datetime.now().isoformat(),
        #'updated_at': datetime.datetime.now().isoformat(),
        #'film_work_type': 'movie'
    } for _ in range(60)]

    # 1.1 Записываем данные в ES
    bulk_query = make_bulk_query(es_data, test_settings.es_index, test_settings.es_id_field)
    await es_write_data(bulk_query)

    # 2. Запрашиваем данные из ES по API

    session = aiohttp.ClientSession()
    url = f'http://{test_settings.service_host}:8000/api/v1/films/search'
    async with session.get(url, params=query_data) as response:
        body = await response.json()
        status = response.status
        length = len(body)
    await session.close()

    # 2. Проверяем ответ

    assert status == expected_answer['status']
    assert length == expected_answer['length']
