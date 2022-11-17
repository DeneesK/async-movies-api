import json
import pytest

# from elasticsearch import AsyncElasticsearch

from functional.settings import test_settings

#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.
from functional.src.conftest import get_es_persons_bulk_query


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'search': 'John Smith'},
                {'status': 200, 'length': 50}
        ),
        (
                {'search': 'William Shakespear'},
                {'status': 200, 'length': 1}  # 1 - because one item with "not found"
        )
    ]
)
# @pytest.mark.parametrize('es_write_data', [get_es_persons_bulk_query], indirect=True)
@pytest.mark.asyncio
async def test_search(es_write_data, make_get_request, query_data, expected_answer):
    items_count = 60
    bulk_query = get_es_persons_bulk_query(query_data, test_settings.es_index, test_settings.es_id_field, items_count)

    es_write_data(bulk_query, items_count, 'persons')
    # 3. Запрашиваем данные из ES по API

    page_size = expected_answer['length']
    # to replace with:
    status, body, headers = await make_get_request('/api/v1/persons/search', query_data, expected_answer, items_count)

    # 4. Проверяем ответ

    assert status == expected_answer['status']
    assert len(body) == page_size

@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'search': 'John Smith'},
                {'status': 200, 'length': 1}
        )
    ]
)
@pytest.mark.asyncio
async def test_by_id(es_write_data, make_get_request, query_data, expected_answer):
    items_count = 1
    bulk_query = get_es_persons_bulk_query(query_data, test_settings.es_index, test_settings.es_id_field, items_count)
    person_id = json.loads(bulk_query[0])['index']['_id']
    es_write_data(bulk_query, items_count, 'persons')
    # 3. Запрашиваем данные из ES по API

    page_size = expected_answer['length']
    getting_query_data = {}
    # to replace with:
    status, body, headers = await make_get_request(f'/api/v1/persons/person/{person_id}', getting_query_data, expected_answer, items_count)

    # 4. Проверяем ответ

    assert status == expected_answer['status']
    assert len(body) == page_size
    assert body['name'] == query_data['search']
