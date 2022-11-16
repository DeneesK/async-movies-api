import json
import datetime
import uuid

import pytest
from elasticsearch import AsyncElasticsearch

from .settings import test_settings


@pytest.fixture
async def es_client():
    client = AsyncElasticsearch(hosts=test_settings.es_host, 
                                validate_cert=False, 
                                use_ssl=False)
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
    async def inner(es_data: list[dict]):
        bulk_query = get_es_bulk_query(es_data, test_settings.es_index, test_settings.es_id_field)

        str_query = '\n'.join(bulk_query) + '\n'

        response = await es_client.bulk(str_query, refresh=True)

        if response['errors']:
            raise Exception('Ошибка записи данных в Elasticsearch')

    return inner
