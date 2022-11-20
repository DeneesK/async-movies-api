import json
import uuid
from http import HTTPStatus

import pytest

from ..settings import test_settings
from .common import make_bulk_query, random_string, is_sorted

ES_INDEX = 'persons'


def get_es_persons_bulk_query(query_data, es_index, es_id_field, items_count, use_random=False):
    # 1. Генерируем данные для ES
    es_data = [{
        'id': str(uuid.uuid4()),
        'name': (random_string(6) + ' ' if use_random else '') + query_data['search'],
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
async def test_search(es_write_data, redis_client, make_search_request, query_data, expected_answer):
    """We assume that the index is clean."""
    items_count = 60
    bulk_query = get_es_persons_bulk_query(query_data, ES_INDEX, test_settings.es_id_field, items_count, use_random=True)
    names = [json.loads(str_item)['name'] for str_item in bulk_query[1::2]]
    await es_write_data(bulk_query)
    # 3. Запрашиваем данные из ES по API

    page_size = expected_answer['length']
    # several queries for each pagination page:
    for page_num in range(items_count // page_size):
        query_data1 = query_data.copy()
        from_ = page_num * page_size if page_num > 0 else None
        status, body, headers = await make_search_request('/api/v1/persons/search', query_data1, expected_answer,
                                                          items_count, from_,
                                                          sorting_fields=['name.raw'])

        # 4. Проверяем ответ
        assert status == expected_answer['status']
        assert len(body) == page_size
        #for item in body:
        #    assert item['name'] in names
        #assert is_sorted(body, lambda x: x['name'])
        # 5. Let's check the cache
        redis_key = str((query_data['search'], ('name.raw',), None, from_, str(page_size)))
        print('redis_key', (query_data['search'], ('name.raw',), None, from_, str(page_size)))
        cache_data_str = await redis_client.get(redis_key)
        cache_data = json.loads(cache_data_str)
        for cache_item_str, response_item in zip(cache_data, body):
            cache_item = json.loads(cache_item_str)
            assert cache_item == response_item


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
    person_id = json.loads(bulk_query[1])['id']

    await es_write_data(bulk_query)
    # 3. Запрашиваем данные из ES по API

    page_size = expected_answer['length']
    # to replace with:
    status, body, headers = await make_id_request(f'/api/v1/persons/person/{person_id}')

    # 4. Проверяем ответ

    assert status == expected_answer['status']
    assert len(body) == page_size
    assert body['name'] == query_data['search']
