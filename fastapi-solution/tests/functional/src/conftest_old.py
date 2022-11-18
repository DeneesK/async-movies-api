import asyncio

import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
import aiohttp

from functional.settings import test_settings




@pytest_asyncio.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(hosts=test_settings.es_host)  # ! Warning - no port here, the default one used.
    yield client
    await client.close()


@pytest_asyncio.fixture
def es_write_data(es_client):
    async def inner(bulk_query: list[str]):
        print('es write data inner')
        # bulk_query = get_bulk_query_function(data, es_index, test_settings.es_id_field, items_count)
        str_query = '\n'.join(bulk_query) + '\n'

        response = await es_client.bulk(str_query, refresh=True)

        if response['errors']:
            raise Exception(f'Ошибка записи данных в Elasticsearch: {response["errors"]}')
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
def make_search_request(aiohttp_client_session):
    async def inner(url_start, query_data, expected_answer, items_count):
        """url start is the beginning of url, like '/api/v1/films/search'."""
        # aiohttp_client_session = aiohttp.ClientSession()
        url = test_settings.service_url + url_start
        page_size = expected_answer['length']
        assert page_size <= items_count
        query_data1 = {'query': query_data["search"], 'page_size': page_size}
        async with aiohttp_client_session.get(url, params=query_data1) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        # await aiohttp_client_session.close()
        return status, body, headers
    return inner


@pytest_asyncio.fixture
def make_id_request(aiohttp_client_session):
    async def inner(url_start):
        """url start is the beginning of url, like '/api/v1/films/search'."""
        # aiohttp_client_session = aiohttp.ClientSession()
        url = test_settings.service_url + url_start
        page_size = 1
        query_data1 = {}
        async with aiohttp_client_session.get(url, params=query_data1) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        # await aiohttp_client_session.close()
        return status, body, headers
    return inner