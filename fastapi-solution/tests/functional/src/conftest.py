import datetime
import uuid
import json
import asyncio

import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
import aiohttp

from functional.settings import test_settings


def get_es_films_bulk_query(query_data, es_index, es_id_field, items_count):
    # 1. Генерируем данные для ES
    es_data = [{
        'id': str(uuid.uuid4()),
        'imdb_rating': 8.5,
        'genre': ['Action', 'Sci-Fi'],
        'title': query_data['search'],
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
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat(),
        'film_work_type': 'movie'
    } for _ in range(items_count)]
    return make_bulk_query(es_data, es_index, es_id_field)


def get_es_persons_bulk_query(query_data, es_index, es_id_field, items_count):
    # 1. Генерируем данные для ES
    es_data = [{
        'id': str(uuid.uuid4()),
        'name': query_data['search'],
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat(),
    } for _ in range(items_count)]
    return make_bulk_query(es_data, es_index, es_id_field)


def make_bulk_query(es_data, es_index, es_id_field):
    bulk_query = []
    for row in es_data:
        bulk_query.extend([
            json.dumps({'index': {'_index': es_index, '_id': row[es_id_field]}}),
            json.dumps(row)
        ])

    return bulk_query


@pytest.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(hosts=test_settings.es_host)  # ! Warning - no port here, the default one used.
    yield client
    await client.close()


@pytest.fixture
def es_write_data(request, es_client):
    async def inner(data: list[dict], items_count, es_index):
        get_bulk_query_function = request.param
        bulk_query = get_bulk_query_function(data, es_index, test_settings.es_id_field, items_count)
        str_query = '\n'.join(bulk_query) + '\n'

        response = await es_client.bulk(str_query, refresh=True)

        if response['errors']:
            raise Exception('Ошибка записи данных в Elasticsearch')
    return inner


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope='session')
async def aiohttp_client_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture
def make_get_request(aiohttp_client_session):
    async def inner(url_start, query_data, expected_answer, items_count):
        """url start is the beginning of url, like '/api/v1/films/search'."""
        # aiohttp_client_session = aiohttp.ClientSession()
        url = test_settings.service_url + url_start
        page_size = expected_answer['length']
        assert page_size <= items_count
        # query_data = {'search': 'The Star'}  # the original option
        query_data1 = {'query': query_data['search'], 'page_size': page_size}
        async with aiohttp_client_session.get(url, params=query_data1) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        # await aiohttp_client_session.close()
        return status, body, headers
    return inner
