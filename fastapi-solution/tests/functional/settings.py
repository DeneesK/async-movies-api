from pydantic import BaseSettings, Field


class TestSettings(BaseSettings):
    es_host: str = Field(..., env='ELASTIC_HOST')
    es_index: str = Field('movies')
    es_id_field: str = Field('id')
    es_index_mapping: dict = {}

    redis_host: str = Field(..., env='REDIS_HOST')
    service_host: str = Field(..., env='SERVICE_HOST')

    @property
    def service_url(self):
        return f'http://{self.service_host}:8000'


test_settings = TestSettings()
