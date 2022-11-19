import backoff
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError 

from settings import test_settings
from config import BACKOFF_CONFIG


@backoff.on_exception(backoff.expo, **BACKOFF_CONFIG)
def es_client_ping():
    es_client = Elasticsearch(hosts=test_settings.es_host, validate_cert=False, use_ssl=False)
    if es_client.ping():
        return True
    raise ConnectionError


if __name__ == '__main__':
    es_client_ping()