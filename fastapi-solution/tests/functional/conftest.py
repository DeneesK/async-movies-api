import json

import pytest
import pytest_asyncio
import aiohttp
from elasticsearch import AsyncElasticsearch
from aioredis import Redis

from .settings import test_settings
from .es_schemes import person_index_body, genre_index_body, filmwork_index_body


@pytest_asyncio.fixture
async def es_client():
    client = AsyncElasticsearch(hosts=test_settings.es_host, 
                                validate_cert=False, 
                                use_ssl=False)
    # create the schemas:
    if await client.indices.exists('movies'):
        await client.indices.delete('movies')
    await client.indices.create('movies', filmwork_index_body)

    if await client.indices.exists('persons'):
        await client.indices.delete('persons')
    await client.indices.create('persons', person_index_body)

    if await client.indices.exists('genres'):
        await client.indices.delete('genres')
    await client.indices.create('genres', genre_index_body)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def redis_client():
    client = Redis(host=test_settings.redis_host)
    await client.flushdb()
    yield client
    await client.close()


def get_es_bulk_query(es_data: list[dict], es_index: str, es_id_field: str):
    bulk_query = []
    for row in es_data:
        bulk_query.extend([
            json.dumps({'index': {'_index': es_index, '_id': row[es_id_field]}}),
            json.dumps(row)
        ])
    return bulk_query


@pytest.fixture
def es_write_data(es_client):
    async def inner(bulk_query: list[str]):
        # bulk_query = get_es_bulk_query(es_data, test_settings.es_index, test_settings.es_id_field)

        str_query = '\n'.join(bulk_query) + '\n'

        response = await es_client.bulk(str_query, refresh=True)

        if response['errors']:
            msg = 'Ошибка записи данных в Elasticsearch'
            if len(response['items'])>0:
                msg += str(response['items'][0]['index'])
            raise Exception(msg)

    return inner


@pytest_asyncio.fixture  # (scope='session') session - doesn't work,
# ScopeMismatch: You tried to access the function scoped fixture event_loop with a session scoped request object,
# involved factories:
async def aiohttp_client_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture
def make_search_request(aiohttp_client_session):
    async def inner(url_start, query_data, expected_answer, items_count, from_=None,
                    sorting_fields=None):
        """url start is the beginning of url, like '/api/v1/films/search'."""
        url = test_settings.service_url + url_start
        page_size = expected_answer['length']
        assert page_size <= items_count
        query_data1 = {'query': query_data["query"], 'page_size': page_size}
        if from_:
            query_data1['from_'] = from_
        if sorting_fields:
            query_data1['sort'] = sorting_fields
        async with aiohttp_client_session.get(url, params=query_data1) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        return status, body, headers
    return inner


@pytest_asyncio.fixture
def make_id_request(aiohttp_client_session):
    async def inner(url_start):
        """url start is the beginning of url, like '/api/v1/films/search'."""
        url = test_settings.service_url + url_start
        query_data1 = {}
        async with aiohttp_client_session.get(url, params=query_data1) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        return status, body, headers
    return inner
