import os

from pydantic import BaseSettings, Field


class TestSettings(BaseSettings):
    es_host: str = Field(os.environ.get('ELASTIC_HOST'))
    es_index: str = Field('movies')
    es_id_field: str = Field('id')
    es_index_mapping: dict = {}

    redis_host: str = Field(os.environ.get('REDIS_HOST'))
    service_host: str = Field(os.environ.get('SERVICE_HOST'))


test_settings = TestSettings()
