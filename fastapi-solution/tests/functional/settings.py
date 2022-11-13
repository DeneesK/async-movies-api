import os

from pydantic import BaseSettings, Field


class TestSettings(BaseSettings):
    es_host: str = Field(os.environ.get('ELASTIC_HOST', 'http://127.0.0.1:9200'))
    es_index: str = Field('movies')
    es_id_field: str = Field('id')
    es_index_mapping: dict = {}

    redis_host: str = Field(os.environ.get('REDIS_HOST', 'http://127.0.0.1:6372'))
    service_host: str = Field(os.environ.get('SERVICE_HOST', 'http://127.0.0.1:8000'))
 

test_settings = TestSettings()