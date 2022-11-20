import json
from http import HTTPStatus

import pytest

from .common import make_bulk_query


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
async def test_film(es_write_data, redis_client, checking_id, expected_answer, make_id_request, es_data_film):

    # 1. Генерируем данные для ES

    bulk_query = make_bulk_query(es_data_film, 'movies', 'id')

    # 1.1 Записываем данные в ES

    await es_write_data(bulk_query)  # , 1, 'movies'

    # 2. Запрашиваем данные из ES по API
    status, body, _ = await make_id_request(f'/api/v1/films/film/{checking_id}')
    result = body.get('title', 'film not found')

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


@pytest.mark.parametrize(
    'expected_answer',
    [
        {'rating': 9.5}
    ]
)
@pytest.mark.asyncio
async def test_film_sort(expected_answer, make_id_request, es_data_film, es_write_data):

    bulk_query = make_bulk_query(es_data_film, 'movies', 'id')

    await es_write_data(bulk_query)

    _, body, _ = await make_id_request('/api/v1/films/search/?query=star&sort=imdb_rating',)

    result = body[0].get('imdb_rating')  # проверяем первый элмент, первым должен находится фильм с самым высоким рейтингом

    assert result == expected_answer['rating']
