import json
import uuid
import datetime
from http import HTTPStatus

import pytest

from ..settings import test_settings
from .common import make_bulk_query

ES_INDEX = 'persons'


def get_es_persons_bulk_query(query_data, es_index, es_id_field, items_count):
    # 1. Генерируем данные для ES
    es_data = [{
        'id': str(uuid.uuid4()),
        'name': query_data['search'],
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat(),
    } for _ in range(items_count)]
    return make_bulk_query(es_data, es_index, es_id_field)


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'search': 'John Smith'},
                {'status': HTTPStatus.OK, 'length': 50}
        ),
        (
                {'search': 'William Shakespear'},
                {'status': HTTPStatus.OK, 'length': 1}  # 1 - because one item with "not found"
        )
    ]
)
# @pytest.mark.parametrize('es_write_data', [get_es_persons_bulk_query], indirect=True)
@pytest.mark.asyncio
async def test_search(es_write_data, make_search_request, query_data, expected_answer):
    items_count = 60
    bulk_query = get_es_persons_bulk_query(query_data, ES_INDEX, test_settings.es_id_field, items_count)

    await es_write_data(bulk_query)
    # 3. Запрашиваем данные из ES по API

    page_size = expected_answer['length']
    # to replace with:
    status, body, headers = await make_search_request('/api/v1/persons/search', query_data, expected_answer, items_count)

    # 4. Проверяем ответ

    assert status == expected_answer['status']
    assert len(body) == page_size


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'search': 'John Smith'},
                {'status': 200, 'length': 2}
        )
    ]
)
@pytest.mark.asyncio
async def test_by_id(es_write_data, make_id_request, query_data, expected_answer):
    items_count = 1
    bulk_query = get_es_persons_bulk_query(query_data, ES_INDEX, test_settings.es_id_field, items_count)
    person_id = json.loads(bulk_query[0])['index']['_id']
    print(f'got person id {person_id}')
    await es_write_data(bulk_query)
    # 3. Запрашиваем данные из ES по API

    page_size = expected_answer['length']
    # to replace with:
    status, body, headers = await make_id_request(f'/api/v1/persons/person/{person_id}')

    # 4. Проверяем ответ

    assert status == expected_answer['status']
    assert len(body) == page_size
    assert body['name'] == query_data['search']
