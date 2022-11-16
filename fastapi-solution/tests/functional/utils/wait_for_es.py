import time

from elasticsearch import Elasticsearch

from settings import test_settings


if __name__ == '__main__':
    es_client = Elasticsearch(hosts=test_settings.es_host, validate_cert=False, use_ssl=False)
    while True:
        if es_client.ping():
            es_client.close()
            break
        time.sleep(1)